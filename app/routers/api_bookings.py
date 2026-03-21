"""
routers/api_bookings.py
-----------------------
Public REST API consumed by external agency clients (e.g. APO Agency).
All endpoints require a valid X-API-Key header.
Data is always scoped to the authenticated agency — agencies cannot
read or modify each other's bookings.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
import uuid

from app.database import get_session
from app.models import Booking, Agency
from app.api_auth import require_api_key
from services.intelligence import generate_intelligence

router = APIRouter(prefix="/api/v1", tags=["Public API — Bookings"])


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    customer_name: str
    customer_email: str
    customer_id: str
    customer_age: Optional[int] = None
    customer_email_type: Optional[str] = None
    destination: str
    departure_date: str          # YYYY-MM-DD
    return_date: str             # YYYY-MM-DD
    currency: str = "ZAR"
    amount: float
    booking_status: str = "confirmed"
    channel: Optional[str] = None
    source: Optional[str] = None

    @field_validator("departure_date", "return_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("booking_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"confirmed", "pending", "cancelled"}
        if v.lower() not in allowed:
            raise ValueError(f"booking_status must be one of: {allowed}")
        return v.lower()


class BookingRead(BaseModel):
    id: int
    booking_id: str
    agency_id: str
    customer_name: str
    customer_email: str
    customer_id: str
    customer_age: Optional[int]
    customer_email_type: Optional[str]
    destination: str
    departure_date: str
    return_date: str
    currency: str
    amount: float
    booking_status: str
    channel: Optional[str]
    source: Optional[str]
    created_at: datetime
    recommendations: Optional[str] = None
    travel_insights: Optional[str] = None
    destination_intelligence: Optional[str] = None
    news_alerts: Optional[str] = None
    processing_status: str = "pending"

    model_config = {"from_attributes": True}


class BookingStatusUpdate(BaseModel):
    booking_status: str

    @field_validator("booking_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"confirmed", "pending", "cancelled"}
        if v.lower() not in allowed:
            raise ValueError(f"booking_status must be one of: {allowed}")
        return v.lower()


class AgencyProfile(BaseModel):
    id: int
    name: str
    email: str
    api_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Agency profile ────────────────────────────────────────────────────────────

@router.get(
    "/agency/me",
    response_model=AgencyProfile,
    summary="Get authenticated agency profile",
)
async def get_agency_profile(
    agency: Agency = Depends(require_api_key),
):
    """Return the profile of the agency identified by the API key."""
    return agency


# ── Create booking ────────────────────────────────────────────────────────────

@router.post(
    "/bookings",
    response_model=BookingRead,
    status_code=201,
    summary="Create a new booking",
)
async def create_booking(
    payload: BookingCreate,
    agency: Agency = Depends(require_api_key),
    session: Session = Depends(get_session),
):
    """
    Create a booking on behalf of the authenticated agency.
    The `agency_id` is automatically set from the API key — it cannot
    be overridden by the caller.
    """
    # Validate date order
    dep = datetime.strptime(payload.departure_date, "%Y-%m-%d")
    ret = datetime.strptime(payload.return_date, "%Y-%m-%d")
    if ret < dep:
        raise HTTPException(
            status_code=422,
            detail="return_date must be on or after departure_date",
        )

    # Generate intelligence for the booking
    intel = generate_intelligence(payload.dict())
    
    booking = Booking(
        booking_id=f"BK-{uuid.uuid4().hex[:8].upper()}",
        agency_id=str(agency.id),
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        customer_id=payload.customer_id,
        customer_age=payload.customer_age,
        customer_email_type=payload.customer_email_type,
        destination=payload.destination,
        departure_date=payload.departure_date,
        return_date=payload.return_date,
        currency=payload.currency,
        amount=payload.amount,
        booking_status=payload.booking_status,
        channel=payload.channel,
        source=payload.source,
        processing_status=intel["processing_status"],
        recommendations=intel["recommendations"],
        travel_insights=intel["travel_insights"],
        destination_intelligence=intel["destination_intelligence"],
        news_alerts=intel["news_alerts"]
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


# ── List bookings ─────────────────────────────────────────────────────────────

@router.get(
    "/bookings",
    response_model=List[BookingRead],
    summary="List all bookings for this agency",
)
async def list_bookings(
    status: Optional[str] = Query(None, description="Filter by status: confirmed | pending | cancelled"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    agency: Agency = Depends(require_api_key),
    session: Session = Depends(get_session),
):
    """
    Return all bookings belonging to the authenticated agency.
    Supports optional filtering by status and pagination.
    """
    query = select(Booking).where(Booking.agency_id == str(agency.id))
    if status:
        query = query.where(Booking.booking_status == status.lower())
    query = query.order_by(Booking.created_at.desc()).offset(offset).limit(limit)
    return session.exec(query).all()


# ── Get single booking ────────────────────────────────────────────────────────

@router.get(
    "/bookings/{booking_id}",
    response_model=BookingRead,
    summary="Get a single booking by booking_id string",
)
async def get_booking(
    booking_id: str,
    agency: Agency = Depends(require_api_key),
    session: Session = Depends(get_session),
):
    """
    Retrieve a single booking by its `booking_id` (e.g. BK-A1B2C3D4).
    Returns 404 if not found, 403 if it belongs to a different agency.
    """
    booking = session.exec(
        select(Booking).where(Booking.booking_id == booking_id)
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.agency_id != str(agency.id):
        raise HTTPException(status_code=403, detail="Access denied")
    return booking


# ── Update booking status ─────────────────────────────────────────────────────

@router.patch(
    "/bookings/{booking_id}/status",
    response_model=BookingRead,
    summary="Update the status of a booking",
)
async def update_booking_status(
    booking_id: str,
    payload: BookingStatusUpdate,
    agency: Agency = Depends(require_api_key),
    session: Session = Depends(get_session),
):
    """
    Update the `booking_status` of a booking owned by this agency.
    Allowed values: `confirmed`, `pending`, `cancelled`.
    """
    booking = session.exec(
        select(Booking).where(Booking.booking_id == booking_id)
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.agency_id != str(agency.id):
        raise HTTPException(status_code=403, detail="Access denied")
    booking.booking_status = payload.booking_status
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


# ── Delete booking ────────────────────────────────────────────────────────────

@router.delete(
    "/bookings/{booking_id}",
    status_code=204,
    summary="Delete a booking",
)
async def delete_booking(
    booking_id: str,
    agency: Agency = Depends(require_api_key),
    session: Session = Depends(get_session),
):
    """
    Permanently delete a booking owned by this agency.
    Returns 204 No Content on success.
    """
    booking = session.exec(
        select(Booking).where(Booking.booking_id == booking_id)
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.agency_id != str(agency.id):
        raise HTTPException(status_code=403, detail="Access denied")
    session.delete(booking)
    session.commit()
