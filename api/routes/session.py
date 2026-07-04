from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from database.models import ChatSession

router = APIRouter()

@router.post("/new")
async def create_session(db: AsyncSession = Depends(get_db)):
    """Creates and returns a new unique session_id."""
    new_session = ChatSession()
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return {"session_id": new_session.session_id}