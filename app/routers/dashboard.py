from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.database import get_session
from app.models import Agency, Booking, EventLog, EmailLog

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)


@router.get("/api-docs", response_class=HTMLResponse)
async def api_docs(request: Request, session: Session = Depends(get_session)):
    agency_id = request.session.get("agency_id")
    if agency_id:
        agency = session.get(Agency, agency_id)
        if agency:
            request.session["agency_api_key"] = agency.api_key
    return templates.TemplateResponse("api_docs.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def agency_dashboard(request: Request, session: Session = Depends(get_session)):
    agency_id = request.session.get("agency_id")
    if not agency_id:
        return RedirectResponse("/login", status_code=302)

    agency = session.get(Agency, agency_id)
    if not agency:
        request.session.clear()
        return RedirectResponse("/login", status_code=302)

    bookings = session.exec(
        select(Booking).where(Booking.agency_id == str(agency.id)).order_by(Booking.created_at.desc())
    ).all()
    events = session.exec(
        select(EventLog).where(EventLog.agency_name == agency.name).order_by(EventLog.received_at.desc())
    ).all()
    emails = session.exec(
        select(EmailLog).where(EmailLog.agency_name == agency.name).order_by(EmailLog.created_at.desc())
    ).all()

    total_revenue = sum(b.amount for b in bookings)
    confirmed = [b for b in bookings if b.booking_status == "confirmed"]
    destinations = list(set(b.destination for b in bookings))

    return templates.TemplateResponse("agency_dashboard.html", {
        "request": request,
        "agency": agency,
        "bookings": bookings[:8],
        "total_bookings": len(bookings),
        "total_revenue": total_revenue,
        "confirmed_count": len(confirmed),
        "destinations": destinations,
        "recent_events": events[:5],
        "recent_emails": emails[:5],
        "success": request.session.pop("flash_success", None),
        "error": request.session.pop("flash_error", None),
    })
