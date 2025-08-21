from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Dict

class CurrencyRateCreate(BaseModel):
    """Схема для создания курса валюты"""
    symbol: str = Field(..., max_length=10, description="Символ валюты")
    price: Decimal = Field(..., gt=0, description="Курс валюты")

class CurrencyRateResponse(BaseModel):
    """Схема ответа с курсом валюты"""
    id: int
    symbol: str
    price: Decimal
    last_updated: datetime
    
    class Config:
        from_attributes = True

class CurrencyRatesResponse(BaseModel):
    """Схема ответа с курсами валют"""
    rates: Dict[str, float]
    last_updated: datetime | None


class FetchResponse(BaseModel):
    """Схема ответа для эндпоинта по загрузке курсов."""
    message: str
    count: int