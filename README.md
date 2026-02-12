# Minimalistic Backend Template

Чистый, асинхронный шаблон backend-приложения на Python 3.12+, объединяющий Telegram-бота (aiogram 3.x) и API (FastAPI). 
Без сложной архитектуры, без лишних абстракций.

## Особенности

- **Асинхронность**: Полная поддержка `asyncio`.
- **Гибкость**: Запуск только бота, только API или обоих сервисов одновременно.
- **Простота**: Отсутствие сложного Dependency Injection, Event Bus и прочей "магии".
- **Конфигурация**: Переменные окружения через `.env` (Pydantic Settings).
- **Структура**: Понятное разделение на слои (routers, services, app core).

## Структура проекта

```
project/
├── app/
│   ├── api/            # FastAPI компоненты
│   ├── telegram/       # Aiogram компоненты
│   ├── services/       # Бизнес-логика
│   ├── app.py          # Точка сборки (Orchestrator)
│   ├── config.py       # Настройки
│   └── container.py    # Простой DI-контейнер
├── main.py             # Точка входа
├── .env                # Конфигурация
└── requirements.txt    # Зависимости
```

## Установка и запуск

1. **Клонируйте репозиторий** (или используйте как шаблон).

2. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Настройте окружение**:
   Создайте файл `.env` в корне проекта (или используйте существующий):
   ```env
   BOT_TOKEN=your_telegram_bot_token
   API_HOST=0.0.0.0
   API_PORT=8000
   RUN_TELEGRAM=true
   RUN_API=true
   ```

4. **Запустите приложение**:
   ```bash
   python main.py
   ```

## Конфигурация (.env)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram бота | Required |
| `API_HOST` | Хост для API сервера | `0.0.0.0` |
| `API_PORT` | Порт для API сервера | `8000` |
| `RUN_TELEGRAM` | Запускать ли бота | `true` |
| `RUN_API` | Запускать ли API | `true` |

## Использование

### Добавление сервиса
1. Создайте класс сервиса в `app/services/`.
2. Зарегистрируйте его в `app/app.py` -> `setup_services()`:
   ```python
   self.container.register("my_service", MyService())
   ```

### Добавление роутера (Telegram)
1. Создайте роутер в `app/telegram/routers/`.
2. Подключите его в `app/telegram/bot.py`.

### Добавление роутера (API)
1. Создайте роутер в `app/api/routers/`.
2. Подключите его в `app/api/server.py`.

## Стек технологий

- Python 3.12+
- aiogram 3.x
- FastAPI
- Uvicorn
- Pydantic Settings
