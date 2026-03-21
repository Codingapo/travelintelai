from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import get_session
from app.models import EventLog, ProcessingJob, EmailLog

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"))


@router.get("/", response_class=HTMLResponse)
async def list_events(request: Request, session: Session = Depends(get_session)):
    events = session.exec(select(EventLog).order_by(EventLog.received_at.desc())).all()
    jobs = session.exec(select(ProcessingJob).order_by(ProcessingJob.created_at.desc())).all()
    emails = session.exec(select(EmailLog).order_by(EmailLog.created_at.desc())).all()

    return templates.TemplateResponse("events.html", {
        "request": request,
        "events": events,
        "jobs": jobs,
        "emails": emails,
        "total_events": len(events),
        "total_jobs": len(jobs),
        "completed_jobs": len([j for j in jobs if j.status == "completed"]),
        "failed_jobs": len([j for j in jobs if j.status == "failed"]),
    })
