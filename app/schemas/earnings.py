from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional

class EarningCreate(BaseModel):
    """Схема для создания записи о заработке"""
    proxy_ip: str = Field(..., description="IP адрес прокси")
    proxy_port: int = Field(..., ge=1, le=65535, description="Порт прокси")
    proxy_key: str = Field(..., max_length=100, description="Ключ прокси")  # ✅ ДОБАВЛЕНО
    server_id: str = Field(..., max_length=50, description="ID сервера")
    bot_id: str = Field(..., max_length=50, description="ID бота")
    bot_name: str = Field(..., max_length=100, description="Название бота")
    faucet_name: str = Field(..., max_length=100, description="Название крана")
    faucet_url: Optional[str] = Field(None, max_length=255, description="URL крана")
    reward_amount: Decimal = Field(..., gt=0, description="Сумма заработка")
    reward_currency: str = Field(..., max_length=10, description="Валюта заработка")
    unique_key: str = Field(..., max_length=64, description="Уникальный ключ записи")  # ✅ ДОБАВЛЕНО
    success: bool = Field(True, description="Успешность операции")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    event_timestamp: datetime = Field(..., description="Время события")  # ✅ Обязательное поле
    extra_data: Optional[str] = Field(None, description="Дополнительные данные (JSON)")

    @validator('bot_name')  # ✅ Исправлено: обычный underscore
    def validate_bot_name(cls, v):
        if not v.strip():
            raise ValueError('Название бота не может быть пустым')
        return v.strip()

class EarningResponse(BaseModel):
    """Схема ответа с информацией о записи"""
    id: int
    proxy_ip: str
    proxy_port: int
    proxy_key: str
    server_id: str
    bot_id: str
    bot_name: str
    faucet_name: str
    faucet_url: Optional[str]
    reward_amount: Decimal
    reward_currency: str
    unique_key: str
    success: bool
    error_message: Optional[str]
    event_timestamp: datetime
    created_at: datetime
    extra_data: Optional[str]
    
    class Config:
        from_attributes = True  # ✅ Исправлено: обычный underscore
