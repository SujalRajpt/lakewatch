from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/dbtest")
async def db_test(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"database": result.scalar()}
