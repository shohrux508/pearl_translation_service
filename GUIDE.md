# Путеводитель по шаблону (Developer Guide)

Этот документ поможет вам разобраться в архитектуре шаблона, добавить новый функционал и поддерживать чистоту кода.

## 📋 Обзор архитектуры

Шаблон построен на **принципе модульности** и **отсутствия магии**.
Вся логика собирается в классе `App` (файл `app/app.py`), который управляет запуском компонентов (Telegram бот, API сервер).

### Основные компоненты

1.  **`app/app.py` (Orchestrator)**:
    *   Инициализирует DI-контейнер (`Container`).
    *   Регистрирует сервисы (бизнес-логику).
    *   Запускает Telegram бота и API сервер в едином `asyncio` цикле.

2.  **`app/container.py` (Simple DI)**:
    *   Прострой реестр зависимостей.
    *   Позволяет получать сервисы в любом месте (в роутерах, хендлерах) без глобальных переменных.

3.  **`app/config.py` (Settings)**:
    *   Использует `pydantic-settings` для загрузки переменных окружения из `.env`.
    *   Все настройки типизированы.

---

## 🚀 Как начать работу

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка окружения
Скопируйте пример `.env` (если есть) или создайте свой:
```env
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
API_HOST=0.0.0.0
API_PORT=8000
RUN_TELEGRAM=true  # или false, если нужен только API
RUN_API=true       # или false, если нужен только Бот
```

### 3. Запуск
```bash
python main.py
```

---

## 🛠 Руководство по разработке

### Добавление новой бизнес-логики (Сервис)

Вся сложная логика должна жить в сервисах, а не в хендлерах.

1.  Создайте файл `app/services/my_service.py`:
    ```python
    class MyService:
        def hello(self) -> str:
            return "Hello from Service!"
    ```
2.  Зарегистрируйте сервис в `app/app.py`:
    ```python
    # В методе setup_services
    from app.services.my_service import MyService
    
    self.container.register("my_service", MyService())
    ```

### Добавление API эндпоинта (FastAPI)

1.  Создайте роутер `app/api/routers/users.py`:
    ```python
    from fastapi import APIRouter, Depends
    from app.container import Container
    
    router = APIRouter(prefix="/users", tags=["Users"])
    
    # Пример получения контейнера (зависит от реализации get_container в api/server.py)
    # Если вы передаете container через app.state, то можно так:
    
    @router.get("/")
    async def get_users():
        return {"users": []}
    ```
2.  Подключите роутер в `app/api/server.py`:
    ```python
    from app.api.routers import users
    
    def start_api(container):
        app = FastAPI()
        app.include_router(users.router)
        # ...
    ```

### Добавление команды бота (Aiogram)

1.  Создайте роутер `app/telegram/routers/menu.py`:
    ```python
    from aiogram import Router, types
    from aiogram.filters import Command
    
    router = Router()
    
    @router.message(Command("menu"))
    async def cmd_menu(message: types.Message):
        await message.answer("Меню")
    ```
2.  Подключите роутер в `app/telegram/bot.py`:
    ```python
    from app.telegram.routers import menu
    
    async def start_telegram(container):
        dp = Dispatcher()
        dp.include_router(menu.router)
        # ...
    ```

### Использование сервисов в хендлерах

Чтобы использовать сервис внутри хендлера (API или Бота), вам нужен доступ к `container`.

**Для Aiogram:**
Обычно контейнер передается через middleware или workflow data. В этом шаблоне простейший вариант — передать `container` при создании бота в `bot.py` и использовать его.
*Рекомендуется:* Настроить Middleware для внедрения зависимостей в хендлеры.

**Для FastAPI:**
Используйте `Request.app.state.container` или `Depends`.

---

## 🧪 Тестирование

Проект настроен для использования `pytest`.

1.  Создайте папку `tests/`.
2.  Создайте тест `tests/test_service.py`:
    ```python
    from app.services.example_service import ExampleService
    
    def test_example_service():
        service = ExampleService()
        assert service.process() == "result"
    ```
3.  Запустите тесты:
    ```bash
    pytest
    ```

## ⚠️ Частые вопросы

**В: Как запустить только бота?**
О: Установите `RUN_API=false` в `.env`.

**В: Почему `main.py` такой пустой?**
О: `main.py` — это только точка входа. Вся инициализация происходит в `app/app.py`, чтобы код был чище и тестируемым.
