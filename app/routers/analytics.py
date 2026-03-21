from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import get_session
from app.models import Booking
from services.anomaly_detection import AnomalyDetector
from services.clustering_model import CustomerSegmenter
from services.forecasting_model import DemandForecaster

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"))


def bookings_to_df(bookings):
    return pd.DataFrame([{
        "booking_date": b.created_at,
        "revenue": b.amount,
        "age": b.customer_age or 30,
        "spending": b.amount,
        "destination": b.destination,
        "status": b.booking_status,
        "channel": b.channel or "direct",
    } for b in bookings])


@router.get("/", response_class=HTMLResponse)
async def analytics_dashboard(request: Request, session: Session = Depends(get_session)):
    bookings = session.exec(select(Booking)).all()

    anomalies = []
    forecast = []
    segments = []
    revenue_by_dest = {}
    revenue_by_status = {}
    monthly_revenue = {}

    if bookings:
        df = bookings_to_df(bookings)

        # Anomaly detection
        try:
            detector = AnomalyDetector(df.copy())
            anomalies = detector.detect_anomalies()
        except Exception as e:
            anomalies = []

        # Demand forecasting
        try:
            forecaster = DemandForecaster(df.copy())
            forecast = forecaster.train_and_predict(days_to_forecast=14)
        except Exception as e:
            forecast = []

        # Customer segmentation
        try:
            segmenter = CustomerSegmenter(df.copy())
            segments_raw = segmenter.segment_customers()
            # Count by segment
            seg_counts = {}
            for s in segments_raw:
                name = s.get("segment_name", "Unknown")
                seg_counts[name] = seg_counts.get(name, 0) + 1
            segments = [{"name": k, "count": v} for k, v in seg_counts.items()]
        except Exception as e:
            segments = []

        # Revenue by destination
        for b in bookings:
            revenue_by_dest[b.destination] = revenue_by_dest.get(b.destination, 0) + b.amount

        # Revenue by status
        for b in bookings:
            revenue_by_status[b.booking_status] = revenue_by_status.get(b.booking_status, 0) + b.amount

        # Monthly revenue
        for b in bookings:
            month_key = b.created_at.strftime("%Y-%m") if hasattr(b.created_at, 'strftime') else str(b.created_at)[:7]
            monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + b.amount

    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "anomalies": anomalies,
        "forecast": forecast[:7],  # Show 7 days
        "segments": segments,
        "revenue_by_dest": revenue_by_dest,
        "revenue_by_status": revenue_by_status,
        "monthly_revenue": dict(sorted(monthly_revenue.items())),
        "total_bookings": len(bookings),
        "total_revenue": sum(b.amount for b in bookings),
    })
