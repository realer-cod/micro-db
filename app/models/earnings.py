from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base


class ProxyEarning(Base):
    """Модель для записи заработка через прокси"""
    __tablename__ = "proxy_earnings"

    id = Column(Integer, primary_key=True, index=True)
    
    # Информация о прокси
    proxy_ip = Column(String(45), nullable=False, index=True)
    proxy_port = Column(Integer, nullable=False)
    proxy_key = Column(String(100), nullable=False, index=True)  # ip:port
    
    # Информация о сервере и боте
    server_id = Column(String(50), nullable=False, index=True)
    bot_id = Column(String(50), nullable=False)
    bot_name = Column(String(100), nullable=False, index=True)  # ✅ НОВОЕ: Название бота
    
    # Информация о заработке
    faucet_name = Column(String(100), nullable=False)
    faucet_url = Column(String(255), nullable=True)
    
    # Сумма заработка
    reward_amount = Column(Numeric(20, 8), nullable=False)
    reward_currency = Column(String(10), nullable=False)
    
    # Метаданные
    unique_key = Column(String(64), nullable=False, unique=True, index=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Временные метки
    event_timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Дополнительные данные
    metadata = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ProxyEarning(bot={self.bot_name}, proxy={self.proxy_key}, amount={self.reward_amount} {self.reward_currency})>"
