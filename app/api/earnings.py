from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.earnings import ProxyEarning
from app.schemas.earnings import EarningCreate, EarningResponse

# Создание роутера
router = APIRouter(prefix="/earnings", tags=["earnings"])


@router.post("/", response_model=EarningResponse)
async def create_earning(
    earning: EarningCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание новой записи заработка"""
    try:
        # Создание новой записи
        db_earning = ProxyEarning(**earning.dict())
        db.add(db_earning)
        await db.commit()
        await db.refresh(db_earning)
        
        return db_earning
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating earning: {str(e)}")


@router.get("/", response_model=List[EarningResponse])
async def get_earnings(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получение списка записей заработка"""
    result = await db.execute(
        select(ProxyEarning).offset(skip).limit(limit)
    )
    earnings = result.scalars().all()
    return earnings


@router.get("/{earning_id}", response_model=EarningResponse)
async def get_earning(
    earning_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение записи заработка по ID"""
    result = await db.execute(
        select(ProxyEarning).where(ProxyEarning.id == earning_id)
    )
    earning = result.scalar_one_or_none()
    
    if not earning:
        raise HTTPException(status_code=404, detail="Earning not found")
    
    return earning


@router.get("/proxy/{proxy_key}", response_model=List[EarningResponse])
async def get_earnings_by_proxy(
    proxy_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Получение записей заработка по ключу прокси"""
    result = await db.execute(
        select(ProxyEarning).where(ProxyEarning.proxy_key == proxy_key)
    )
    earnings = result.scalars().all()
    return earnings


@router.get("/bot/{bot_name}", response_model=List[EarningResponse])
async def get_earnings_by_bot(
    bot_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Получение записей заработка по имени бота"""
    result = await db.execute(
        select(ProxyEarning).where(ProxyEarning.bot_name == bot_name)
    )
    earnings = result.scalars().all()
    return earnings
