from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict
from datetime import datetime, timezone
import requests
import logging

from app.database import get_db
from app.models.currency import CurrencyRate
from app.schemas.currency import CurrencyRateCreate, CurrencyRateResponse, CurrencyRatesResponse, FetchResponse
from app.config import settings

# Настройка логирования
logger = logging.getLogger(__name__)

# Создание роутера
router = APIRouter(prefix="/currency", tags=["currency"])

# Константы для API
CRYPTOCOMPARE_URL = "https://min-api.cryptocompare.com/data/pricemulti"
FROM_SYMBOL = "BTC"
TO_SYMBOLS = "BCH,DOGE,LTC,USDT,FEY,DGB,DASH,TRX,ZEC,ETH,BNB,SOL,XRP,MATIC,ADA,TON,XLM,XMR,USDC,TARA,TRUMP,PEPE"

@router.get("/rates", response_model=CurrencyRatesResponse)
async def get_currency_rates(db: AsyncSession = Depends(get_db)):
    """Получение курсов валют из базы данных"""
    try:
        # Получаем все курсы из БД
        result = await db.execute(select(CurrencyRate))
        rates_records = result.scalars().all()
        
        if not rates_records:
            return CurrencyRatesResponse(rates={}, last_updated=None)
        
        # Формируем словарь курсов
        rates = {}
        oldest_update = None
        
        for record in rates_records:
            rates[record.symbol] = float(record.price)
            if oldest_update is None or record.last_updated < oldest_update:
                oldest_update = record.last_updated
        
        # Приводим время к UTC
        if oldest_update:
            oldest_update = oldest_update.astimezone(timezone.utc)
        
        logger.info(f"Из БД загружено {len(rates)} курсов. Самое старое обновление: {oldest_update}")
        
        return CurrencyRatesResponse(rates=rates, last_updated=oldest_update)
        
    except Exception as e:
        logger.error(f"Ошибка при получении курсов из БД: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения курсов: {str(e)}")

@router.post("/fetch", response_model=FetchResponse)
async def fetch_and_store_rates(db: AsyncSession = Depends(get_db)):
    """Получение курсов с API и сохранение в БД"""
    try:
        # Получаем курсы с API
        params = {
            'fsyms': FROM_SYMBOL,
            'tsyms': TO_SYMBOLS,
            'api_key': settings.CRYPTOCOMPARE_API_KEY
        }
        
        response = requests.get(CRYPTOCOMPARE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if FROM_SYMBOL not in data:
            raise HTTPException(status_code=500, detail="Неверный ответ от API")
        
        rates = data[FROM_SYMBOL]
        
        # Сохраняем курсы в БД
        for symbol, price in rates.items():
            if price and price > 0:
                # Проверяем существование записи
                existing = await db.execute(
                    select(CurrencyRate).where(CurrencyRate.symbol == symbol)
                )
                existing_rate = existing.scalar_one_or_none()
                
                if existing_rate:
                    # Обновляем существующий курс
                    existing_rate.price = price
                    existing_rate.last_updated = func.now()
                else:
                    # Создаем новый курс
                    new_rate = CurrencyRate(symbol=symbol, price=price)
                    db.add(new_rate)
        
        await db.commit()
        logger.info(f"Успешно обновлено/вставлено {len(rates)} курсов в БД")
        
        return {"message": f"Обновлено {len(rates)} курсов валют", "count": len(rates)}
        
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка API: {str(e)}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при сохранении курсов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")

@router.get("/", response_model=List[CurrencyRateResponse])
async def get_all_currency_rates(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получение всех курсов валют с пагинацией"""
    result = await db.execute(
        select(CurrencyRate).offset(skip).limit(limit)
    )
    rates = result.scalars().all()
    return rates

@router.get("/{symbol}", response_model=CurrencyRateResponse)
async def get_currency_rate(symbol: str, db: AsyncSession = Depends(get_db)):
    """Получение курса валюты по символу"""
    result = await db.execute(
        select(CurrencyRate).where(CurrencyRate.symbol == symbol.upper())
    )
    rate = result.scalar_one_or_none()
    
    if not rate:
        raise HTTPException(status_code=404, detail="Курс валюты не найден")
    
    return rate
