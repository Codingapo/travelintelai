from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import get_session
from app.models import Agency, Booking

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"))


@router.get("/", response_class=HTMLResponse)
async def list_agencies(request: Request, session: Session = Depends(get_session)):
    agencies = session.exec(select(Agency)).all()
    agency_stats = []
    for agency in agencies:
        bookings = session.exec(select(Booking).where(Booking.agency_id == agency.name)).all()
        agency_stats.append({
            "agency": agency,
            "total_bookings": len(bookings),
            "total_revenue": sum(b.amount for b in bookings),
            "confirmed": len([b for b in bookings if b.booking_status == "confirmed"]),
        })

    return templates.TemplateResponse("agencies.html", {
        "request": request,
        "agency_stats": agency_stats,
        "total_agencies": len(agencies),
    })
