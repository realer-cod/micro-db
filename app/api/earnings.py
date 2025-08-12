@router.get("/record", response_model=dict)
async def record_earning(
    proxy_ip: str = Query(..., description="IP адрес прокси"),
    proxy_port: int = Query(..., description="Порт прокси"),
    server_id: str = Query(..., description="ID сервера"),
    bot_id: str = Query(..., description="ID бота"),
    bot_name: str = Query(..., description="Название бота"),  # ✅ НОВОЕ
    faucet_name: str = Query(..., description="Название крана"),
    reward_amount: float = Query(..., description="Сумма заработка"),
    reward_currency: str = Query("USD", description="Валюта заработка"),
    faucet_url: Optional[str] = Query(None, description="URL крана"),
    success: bool = Query(True, description="Успешность операции"),
    error_message: Optional[str] = Query(None, description="Сообщение об ошибке"),
    db: AsyncSession = Depends(get_db)
):
    """
    GET endpoint для записи заработка бота через прокси
    
    Пример:
    GET /earnings/record?proxy_ip=1.2.3.4&proxy_port=8080&server_id=srv1&bot_id=bot1&bot_name=TestBot&faucet_name=testfaucet&reward_amount=0.001
    """
    try:
        # Формируем ключ прокси
        proxy_key = f"{proxy_ip}:{proxy_port}"
        
        # Текущее время как время события
        event_timestamp = datetime.now(timezone.utc)
        
        # Генерируем уникальный ключ (теперь включает bot_name)
        unique_key = generate_unique_key(proxy_key, event_timestamp, faucet_name, str(reward_amount))
        
        # Проверяем дубликаты
        stmt = select(ProxyEarning).where(ProxyEarning.unique_key == unique_key)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            return {
                "status": "duplicate",
                "message": "Запись уже существует",
                "earning_id": existing.id
            }
        
        # Создаем новую запись
        earning = ProxyEarning(
            proxy_ip=proxy_ip,
            proxy_port=proxy_port,
            proxy_key=proxy_key,
            server_id=server_id,
            bot_id=bot_id,
            bot_name=bot_name.strip(),  # ✅ НОВОЕ
            faucet_name=faucet_name,
            faucet_url=faucet_url,
            reward_amount=reward_amount,
            reward_currency=reward_currency.upper(),
            unique_key=unique_key,
            success=success,
            error_message=error_message,
            event_timestamp=event_timestamp
        )
        
        db.add(earning)
        await db.commit()
        await db.refresh(earning)
        
        return {
            "status": "success",
            "message": "Заработок записан",
            "earning_id": earning.id,
            "bot_name": bot_name,  # ✅ НОВОЕ: Возвращаем имя бота
            "proxy_key": proxy_key,
            "amount": f"{reward_amount} {reward_currency}",
            "timestamp": event_timestamp.isoformat()
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка записи в БД: {str(e)}")


# ✅ НОВОЕ: Добавляем endpoint для фильтрации по названию бота
@router.get("/list", response_model=List[EarningResponse])
async def list_earnings(
    limit: int = Query(100, le=1000, description="Количество записей"),
    offset: int = Query(0, ge=0, description="Смещение"),
    proxy_key: Optional[str] = Query(None, description="Фильтр по прокси"),
    server_id: Optional[str] = Query(None, description="Фильтр по серверу"),
    bot_name: Optional[str] = Query(None, description="Фильтр по названию бота"),  # ✅ НОВОЕ
    db: AsyncSession = Depends(get_db)
):
    """Получить список заработков с фильтрацией"""
    stmt = select(ProxyEarning).order_by(ProxyEarning.created_at.desc())
    
    # Применяем фильтры
    if proxy_key:
        stmt = stmt.where(ProxyEarning.proxy_key == proxy_key)
    if server_id:
        stmt = stmt.where(ProxyEarning.server_id == server_id)
    if bot_name:  # ✅ НОВОЕ: Фильтр по названию бота
        stmt = stmt.where(ProxyEarning.bot_name.ilike(f"%{bot_name}%"))
    
    # Применяем пагинацию
    stmt = stmt.limit(limit).offset(offset)
    
    result = await db.execute(stmt)
    earnings = result.scalars().all()
    
    return earnings
