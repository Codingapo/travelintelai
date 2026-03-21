from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agency_id: str
    booking_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    customer_email_type: Optional[str] = None
    customer_age: Optional[int] = None
    destination: str
    departure_date: str
    return_date: str
    currency: str
    amount: float
    booking_status: str
    channel: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    recommendations: Optional[str] = None
    travel_insights: Optional[str] = None
    destination_intelligence: Optional[str] = None
    news_alerts: Optional[str] = None
    processing_status: str = "pending"


class Agency(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)
    hashed_password: str
    api_key: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EventLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str
    event_type: str
    agency_name: str
    booking_id: Optional[str] = None
    status: str
    payload_json: str
    received_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessingJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str
    job_type: str
    status: str
    attempt_count: int = 0
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None


class EmailLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: Optional[str] = None
    agency_name: str
    recipient_email: str
    recipient_type: str
    subject: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
