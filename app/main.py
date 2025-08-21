
# старт
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import earnings_router, currency_router
from fastapi import FastAPI, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from decimal import Decimal

from app.database import get_db
from app.models.earnings import ProxyEarning
from app.models.currency import CurrencyRate

# Создаем FastAPI приложение
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="API для отслеживания статистики заработка ботов через прокси",
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(earnings_router)
app.include_router(currency_router)


@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "Proxy Stats API",
        "version": settings.version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}


@app.get("/currencies", response_model=Dict[str, float])
async def get_currency_rates(
    db: AsyncSession = Depends(get_db)
):
    """Получение курсов валют (упрощенный endpoint для совместимости)"""
    try:
        # Получаем курсы из БД через SQLAlchemy
        result = await db.execute(select(CurrencyRate))
        rates_records = result.scalars().all()
        
        if not rates_records:
            return {}
        
        # Формируем словарь курсов
        rates = {}
        for record in rates_records:
            rates[record.symbol] = float(record.price)
        
        return rates
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения курсов: {str(e)}")


@app.get("/bot/submit")
async def submit_bot_data(
    proxy_address: str = Query(..., description="Прокси адрес с портом (IP:PORT)"),
    bot_name: str = Query(..., description="Имя бота"),
    earnings: float = Query(..., description="Заработанная сумма"),
    session_id: Optional[str] = Query(None, description="ID сессии бота"),
    asn: Optional[int] = Query(None, description="ASN прокси"),
    asn_org: Optional[str] = Query(None, description="Организация ASN"),
    db: AsyncSession = Depends(get_db)
):
    """
    Бот подает данные о заработке через конкретный прокси
    """
    try:
        # Парсим IP и порт из proxy_address
        if ":" not in proxy_address:
            raise HTTPException(status_code=400, detail="Неверный формат адреса прокси. Используйте IP:PORT")
        
        proxy_ip, proxy_port_str = proxy_address.split(":", 1)
        try:
            proxy_port = int(proxy_port_str)
            if not (1 <= proxy_port <= 65535):
                raise ValueError()
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный порт прокси")
        
        # Создаем уникальный ключ для записи
        unique_key = f"{bot_name}_{proxy_address}_{session_id or 'no_session'}_{datetime.now().isoformat()}"
        
        # Создаем запись о заработке через SQLAlchemy
        earning_record = ProxyEarning(
            proxy_ip=proxy_ip,
            proxy_port=proxy_port,
            proxy_key=proxy_address,  # Используем полный адрес как ключ
            server_id="default",  # Можно сделать настраиваемым
            bot_id=bot_name,  # Используем имя бота как ID
            bot_name=bot_name,
            faucet_name="manual_submit",  # Можно сделать настраиваемым
            faucet_url=None,
            reward_amount=Decimal(str(earnings)),
            reward_currency="BTC",  # Можно сделать настраиваемым
            unique_key=unique_key,
            success=True,
            error_message=None,
            event_timestamp=datetime.now(timezone.utc),
            extra_data=f"session_id={session_id}, asn={asn}, asn_org={asn_org}" if any([session_id, asn, asn_org]) else None
        )
        
        db.add(earning_record)
        await db.commit()
        await db.refresh(earning_record)
        
        return {
            "message": "Данные о заработке успешно сохранены",
            "earning_id": earning_record.id,
            "proxy_address": proxy_address,
            "bot_name": bot_name,
            "amount": earnings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения данных: {str(e)}")


@app.get("/stats/summary")
async def get_stats_summary(
    db: AsyncSession = Depends(get_db)
):
    """Получение сводной статистики"""
    try:
        # Общее количество записей
        total_result = await db.execute(select(func.count(ProxyEarning.id)))
        total_earnings = total_result.scalar()
        
        # Общая сумма заработка
        total_amount_result = await db.execute(
            select(func.sum(ProxyEarning.reward_amount))
        )
        total_amount = total_amount_result.scalar() or Decimal('0')
        
        # Количество уникальных ботов
        unique_bots_result = await db.execute(
            select(func.count(func.distinct(ProxyEarning.bot_name)))
        )
        unique_bots = unique_bots_result.scalar()
        
        # Количество уникальных прокси
        unique_proxies_result = await db.execute(
            select(func.count(func.distinct(ProxyEarning.proxy_key)))
        )
        unique_proxies = unique_proxies_result.scalar()
        
        return {
            "total_earnings": total_earnings,
            "total_amount": float(total_amount),
            "unique_bots": unique_bots,
            "unique_proxies": unique_proxies,
            "last_updated": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")


@app.get("/stats/daily")
async def get_daily_stats(
    days: int = Query(7, ge=1, le=30, description="Количество дней"),
    db: AsyncSession = Depends(get_db)
):
    """Получение ежедневной статистики"""
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Группируем по дням
        daily_stats_result = await db.execute(
            select(
                func.date(ProxyEarning.event_timestamp).label('date'),
                func.count(ProxyEarning.id).label('count'),
                func.sum(ProxyEarning.reward_amount).label('total_amount')
            )
            .where(ProxyEarning.event_timestamp >= start_date)
            .group_by(func.date(ProxyEarning.event_timestamp))
            .order_by(func.date(ProxyEarning.event_timestamp))
        )
        
        daily_stats = []
        for row in daily_stats_result:
            daily_stats.append({
                "date": row.date.isoformat(),
                "count": row.count,
                "total_amount": float(row.total_amount) if row.total_amount else 0.0
            })
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_stats": daily_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения ежедневной статистики: {str(e)}")
