from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import earnings

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
app.include_router(earnings.router, prefix="/api/v1")


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
    return {"status": "healthy", "service": "proxy-stats-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
