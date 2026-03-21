"""
api_auth.py
-----------
Shared dependency for API key authentication.
Any external client (e.g. APO Agency) must pass its API key in the
X-API-Key header.  The key is validated against the Agency table and
the resolved Agency object is returned so routes can scope data to it.
"""

from fastapi import Header, HTTPException, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import Agency


async def require_api_key(
    x_api_key: str = Header(..., description="Agency API key issued by TravelIntel"),
    session: Session = Depends(get_session),
) -> Agency:
    """
    Validate the X-API-Key header and return the matching Agency.
    Raises HTTP 401 if the key is missing or invalid.
    """
    agency = session.exec(
        select(Agency).where(Agency.api_key == x_api_key)
    ).first()
    if not agency:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. "
                   "Register at TravelIntel to obtain your key.",
        )
    return agency
