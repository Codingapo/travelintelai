from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import os, sys, uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import get_session
from app.models import Booking

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"))


# ── List all bookings ────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def list_bookings(request: Request, session: Session = Depends(get_session)):
    bookings = session.exec(select(Booking).order_by(Booking.created_at.desc())).all()
    return templates.TemplateResponse("bookings.html", {
        "request": request,
        "bookings": bookings,
        "total": len(bookings),
    })


# ── Show create booking form ─────────────────────────────────────────────────
@router.get("/create", response_class=HTMLResponse)
async def create_booking_form(request: Request, session: Session = Depends(get_session)):
    recent = session.exec(select(Booking).order_by(Booking.created_at.desc()).limit(5)).all()
    return templates.TemplateResponse("create_booking.html", {
        "request": request,
        "recent_bookings": recent,
        "form": None,
        "error": None,
    })


# ── Submit create booking ────────────────────────────────────────────────────
@router.post("/create", response_class=HTMLResponse)
async def create_booking_submit(
    request: Request,
    session: Session = Depends(get_session),
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    customer_id: str = Form(...),
    customer_age: str = Form(""),
    customer_email_type: str = Form(""),
    agency_id: str = Form(...),
    destination: str = Form(...),
    departure_date: str = Form(...),
    return_date: str = Form(...),
    channel: str = Form(""),
    source: str = Form(""),
    currency: str = Form("ZAR"),
    amount: float = Form(...),
    booking_status: str = Form("confirmed"),
):
    # Validate dates
    try:
        dep = datetime.strptime(departure_date, "%Y-%m-%d")
        ret = datetime.strptime(return_date, "%Y-%m-%d")
        if ret < dep:
            raise ValueError("Return date must be after departure date")
    except ValueError as e:
        recent = session.exec(select(Booking).order_by(Booking.created_at.desc()).limit(5)).all()
        return templates.TemplateResponse("create_booking.html", {
            "request": request,
            "recent_bookings": recent,
            "error": str(e),
            "form": {
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_id": customer_id,
                "customer_age": customer_age,
                "customer_email_type": customer_email_type,
                "agency_id": agency_id,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "channel": channel,
                "source": source,
                "currency": currency,
                "amount": amount,
                "booking_status": booking_status,
            },
        })

    booking = Booking(
        booking_id=f"BK-{uuid.uuid4().hex[:8].upper()}",
        agency_id=agency_id,
        customer_id=customer_id,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_email_type=customer_email_type or None,
        customer_age=int(customer_age) if customer_age else None,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        currency=currency,
        amount=amount,
        booking_status=booking_status,
        channel=channel or None,
        source=source or None,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)

    return RedirectResponse(url=f"/bookings/{booking.id}?created=1", status_code=303)


# ── Booking detail ───────────────────────────────────────────────────────────
@router.get("/{booking_id}", response_class=HTMLResponse)
async def booking_detail(request: Request, booking_id: int, created: str = "", session: Session = Depends(get_session)):
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return templates.TemplateResponse("booking_detail.html", {
        "request": request,
        "booking": booking,
        "just_created": created == "1",
    })


# ── Update booking status ────────────────────────────────────────────────────
@router.post("/{booking_id}/status", response_class=HTMLResponse)
async def update_booking_status(
    request: Request,
    booking_id: int,
    booking_status: str = Form(...),
    session: Session = Depends(get_session),
):
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.booking_status = booking_status
    session.add(booking)
    session.commit()
    return RedirectResponse(url=f"/bookings/{booking_id}?updated=1", status_code=303)


# ── Delete booking ───────────────────────────────────────────────────────────
@router.post("/{booking_id}/delete", response_class=HTMLResponse)
async def delete_booking(
    request: Request,
    booking_id: int,
    session: Session = Depends(get_session),
):
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    session.delete(booking)
    session.commit()
    return RedirectResponse(url="/bookings/?deleted=1", status_code=303)
