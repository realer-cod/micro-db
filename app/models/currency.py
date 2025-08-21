from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class CurrencyRate(Base):
    """Модель для курсов валют"""
    __tablename__ = "currency_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, unique=True, index=True)
    price = Column(Numeric(20, 8), nullable=False)
    last_updated = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<CurrencyRate(symbol={self.symbol}, price={self.price}, updated={self.last_updated})>"
