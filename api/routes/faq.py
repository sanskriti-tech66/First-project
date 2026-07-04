from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.db import get_db
from database.models import FAQ
from core.faq_matcher import invalidate_faq_cache

router = APIRouter()

class FAQCreate(BaseModel):
    question: str
    answer: str

@router.get("/")
async def list_faqs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FAQ))
    return result.scalars().all()

@router.post("/")
async def add_faq(faq: FAQCreate, db: AsyncSession = Depends(get_db)):
    new_faq = FAQ(question=faq.question, answer=faq.answer)
    db.add(new_faq)
    await db.commit()
    await db.refresh(new_faq)
    invalidate_faq_cache()
    return new_faq

@router.delete("/{faq_id}")
async def delete_faq(faq_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FAQ).where(FAQ.id == faq_id))
    faq = result.scalar_one_or_none()
    
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
        
    await db.delete(faq)
    await db.commit()
    invalidate_faq_cache()
    return {"status": "deleted", "id": faq_id}
