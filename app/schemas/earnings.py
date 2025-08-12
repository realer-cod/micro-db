from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional


class EarningCreate(BaseModel):
    """Схема для создания записи о заработке"""
    proxy_ip: str = Field(..., description="IP адрес прокси")
    proxy_port: int = Field(..., ge=1, le=65535, description="Порт прокси")
    server_id: str = Field(..., max_length=50, description="ID сервера")
    bot_id: str = Field(..., max_length=50, description="ID бота")
    bot_name: str = Field(..., max_length=100, description="Название бота")  # ✅ НОВОЕ
    faucet_name: str = Field(..., max_length=100, description="Название крана")
    faucet_url: Optional[str] = Field(None, max_length=255, description="URL крана")
    reward_amount: Decimal = Field(..., gt=0, description="Сумма заработка")
    reward_currency: str = Field(..., max_length=10, description="Валюта заработка")
    event_timestamp: Optional[datetime] = Field(None, description="Время события")
    success: bool = Field(True, description="Успешность операции")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    extra_data: Optional[str] = Field(None, description="Дополнительные данные (JSON)")

    @validator('bot_name')  # ✅ НОВОЕ: Валидация названия бота
    def validate_bot_name(cls, v):
        if not v.strip():
            raise ValueError('Название бота не может быть пустым')
        return v.strip()

    # ... остальные валидаторы остаются те же


class EarningResponse(BaseModel):
    """Схема ответа с информацией о записи"""
    id: int
    proxy_key: str
    server_id: str
    bot_id: str
    bot_name: str  # ✅ НОВОЕ
    faucet_name: str
    reward_amount: Decimal
    reward_currency: str
    success: bool
    event_timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True
