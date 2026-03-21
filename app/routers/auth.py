from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from passlib.context import CryptContext
import secrets, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.database import get_session
from app.models import Agency

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Landing page (public home) ────────────────────────────────
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


# ── Register ──────────────────────────────────────────────────
@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    if request.session.get("agency_id"):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("register.html", {
        "request": request,
        "error": request.session.pop("flash_error", None),
    })


@router.post("/register")
async def register_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm: str = Form(...),
    session: Session = Depends(get_session),
):
    if password != confirm:
        request.session["flash_error"] = "Passwords do not match."
        return RedirectResponse("/register", status_code=302)
    if len(password) < 6:
        request.session["flash_error"] = "Password must be at least 6 characters."
        return RedirectResponse("/register", status_code=302)
    existing = session.exec(select(Agency).where(Agency.email == email)).first()
    if existing:
        request.session["flash_error"] = "An agency with that email already exists."
        return RedirectResponse("/register", status_code=302)
    agency = Agency(
        name=name,
        email=email,
        hashed_password=pwd_ctx.hash(password),
        api_key=secrets.token_hex(24),
    )
    session.add(agency)
    session.commit()
    session.refresh(agency)
    request.session["agency_id"] = agency.id
    request.session["agency_name"] = agency.name
    return RedirectResponse("/dashboard", status_code=302)


# ── Login ─────────────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if request.session.get("agency_id"):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": request.session.pop("flash_error", None),
    })


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    agency = session.exec(select(Agency).where(Agency.email == email)).first()
    if not agency or not pwd_ctx.verify(password, agency.hashed_password):
        request.session["flash_error"] = "Invalid email or password."
        return RedirectResponse("/login", status_code=302)
    request.session["agency_id"] = agency.id
    request.session["agency_name"] = agency.name
    return RedirectResponse("/dashboard", status_code=302)


# ── Logout ────────────────────────────────────────────────────
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
