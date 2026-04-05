# Pearl Translation Service 🤖📄

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![aiogram](https://img.shields.io/badge/aiogram-3.x-blueviolet.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![Gemini](https://img.shields.io/badge/Google%20Gemini-AI-orange.svg)
![Loguru](https://img.shields.io/badge/Loguru-logging-brightgreen.svg)
![Pytest](https://img.shields.io/badge/pytest-passing-success.svg)

**Pearl Translation Service** — современный многофункциональный Telegram-бот и Backend-сервис для умного перевода и оцифровки личных и бизнес-документов с использованием ИИ **Google Gemini**.

В основе архитектуры лежит связка `aiogram 3` для взаимодействия с пользователем и `FastAPI` для REST API, работающие внутри единого асинхронного event loop. Проект построен на принципах **Dependency Injection**, **Lazy Initialization** и **Graceful Shutdown**, что гарантирует стабильную работу в продакшен-среде.

Бот принимает фотографии документов (поддерживается многостраничность), интеллектуально извлекает и переводит данные строго по сгенерированной **JSON Schema**, позволяет пользователю вносить правки через продвинутое inline-меню (с поддержкой таблиц и вложенностей), а затем возвращает готовый переведенный документ в формате Word (`.docx`), сгенерированный по заранее заготовленному шаблону.

---

## ✨ Основные возможности

### Для пользователей

1. **Многостраничное распознавание и агрегация**
   Бот поддерживает состояние ожидания (FSM) для загрузки **нескольких фотографий одновременно** (например, обе стороны ID-карты, многостраничный паспорт или договор). Бот не начинает анализ до нажатия кнопки «Начать распознавание», что позволяет ИИ собрать весь контекст со всех страниц и объединить данные для максимально точного заполнения полей.

2. **Строгое извлечение данных (Strict JSON Schema + Gemini 2.5)**
   Для анализа изображений используется multimodal модель Google Gemini, запрос к которой происходит через **Strict JSON Schema**. ИИ не просто считывает текст (как классический OCR), а *понимает* контекст: находит нужные поля (имя, фамилия, таблицы из инвойсов), переводит их и возвращает ответ в **строго валидированном JSON формате**, полностью исключая галлюцинации ключей или потерю данных.

3. **Выбор модели распознавания**
   Пользователь может выбрать между **Flash** (быстрое распознавание) и **Pro** (точное распознавание) моделями Gemini в зависимости от сложности документа.

4. **Сложные структуры данных: Таблицы и Вложенность**
   Бот поддерживает не просто плоские ключи, но и сложную структуру документа. Вы можете распознавать целые **табличные данные** (например, списки товаров с ценами) и вложенные свойства. Для Telegram-интерфейса реализовано удобное Summary-отображение таблиц с пагинацией и интерфейсом построчного редактирования.

5. **Продвинутая интерактивная валидация данных (Богатый UI)**
   После успешного извлечения данных пользователю не отправляется сразу готовый файл. Бот предоставляет удобное inline-меню со следующими возможностями:
   - **Поэкранная проверка:** Каждое поле отображается как кнопка. Нажали на кнопку — ввели исправленный вариант текстом.
   - **Табличный UI:** Просмотр и редактирование отдельных строк сложных таблиц прямо из чата.
   - **Режим Raw JSON:** Для сложных случаев опытный пользователь может нажать «Редактировать всё (JSON)» и прислать боту сырой исправленный JSON объект для моментального обновления всего документа целиком.

6. **Умные инструкции (Smart UX)**
   При загрузке бот предлагает советы по правильной съемке документов (освещение, фокус, отсутствие бликов), снижая вероятность ошибок со стороны AI.

7. **Мгновенная генерация `.docx`**
   Автоматическая подстановка финально утвержденных данных (и даже целых таблиц) в готовые Word-шаблоны посредством библиотеки `docxtpl` (на базе синтаксиса Jinja2: `{{ var_name }}`, `{% for row in table %}`). Бот мгновенно генерирует файл и отправляет его обратно в чат.

### Для администраторов

8. **Генерация полей ИИ и переводы (No-Code)**
   При добавлении нового типа документа прямо из Telegram, администратор вводит только русские названия полей. Бот автоматически отправляет их в Gemini для подбора оптимальных английских ключей (keys), обеспечивая No-Code подход для расширения системы.

9. **Полное управление шаблонами из Telegram**
   Администраторы могут добавлять, удалять, редактировать шаблоны, загружать/заменять `.docx` файлы для каждого языка — всё из интерфейса бота.

---

## 🏗 Архитектура

### Принципы

| Принцип | Реализация |
|---|---|
| **Dependency Injection** | Легковесный DI-контейнер (`Container`) с `register()` и `register_lazy()` |
| **Lazy Initialization** | Тяжёлые клиенты (Gemini) создаются при первом обращении, а не при старте |
| **Graceful Shutdown** | Упорядоченное закрытие ресурсов при остановке (в обратном порядке регистрации) |
| **Async First** | Все сетевые операции через `async/await` (aiogram, FastAPI, Gemini SDK) |
| **Strict Typing** | Pydantic Settings для конфигурации, Type Hints во всех модулях |
| **Plug-and-Play** | Новый сервис = 1 строка в `app.py`, новый роутер = 1 файл в `routers/` |

### Инженерный слой — `libs/`

Папка `libs/` содержит переиспользуемые обёртки над библиотеками, независимые от бизнес-логики:

| Модуль | Назначение | Подключение |
|---|---|---|
| `libs/utils/logger.py` | Loguru-конфигурация с InterceptHandler | Вызывается в `app.py → setup_logging()` |

> **Принцип**: каждый модуль `libs/` — self-contained, принимает конфигурацию из `app.config`, обрабатывает свои ошибки и может быть отключен комментированием одной строки.

### DI-контейнер

```python
# Немедленная регистрация (лёгкие сервисы)
container.register("docx_service", DocxService())

# Ленивая регистрация (тяжёлые клиенты)
container.register_lazy("gemini_service", lambda: GeminiTranslationService(api_key=settings.GEMINI_API_KEY))

# Доступ через __getattr__
service = container.gemini_service      # lazy init при первом вызове
service = container.get("gemini_service")  # классический вариант тоже работает

# Graceful shutdown (в обратном порядке регистрации)
await container.shutdown()
```

---

## 🛠 Стек технологий

| Категория | Библиотеки |
|---|---|
| **Core** | Python 3.12+, asyncio |
| **Telegram** | [aiogram 3.x](https://docs.aiogram.dev/) — FSM, Inline-клавиатуры, Media Groups |
| **AI** | [Google Gemini](https://ai.google.dev/) (`google-generativeai`) — Multimodal OCR + Structured Outputs |
| **API** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn — REST API, Healthcheck |
| **Документы** | [docxtpl](https://docxtpl.readthedocs.io/) — Jinja2-шаблонизация Word |
| **Логирование** | [Loguru](https://loguru.readthedocs.io/) — цветной вывод, ротация, JSON-режим |
| **Конфигурация** | [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) + python-dotenv |
| **Тестирование** | pytest + pytest-asyncio + pytest-cov |
| **Линтер** | [Ruff](https://docs.astral.sh/ruff/) — проверка и форматирование кода |
| **Утилиты** | Pillow (работа с изображениями) |

---

## 📂 Структура проекта

```text
pearl_translation_service/
├── app/                          # Ядро приложения
│   ├── api/                      # FastAPI компоненты
│   │   ├── dependencies.py       # DI-зависимости для Depends()
│   │   ├── routers/
│   │   │   └── example.py        # Пример API роутера (/ping)
│   │   └── server.py             # Инициализация FastAPI + Uvicorn
│   ├── telegram/                 # Aiogram компоненты
│   │   ├── routers/
│   │   │   ├── translator.py     # Основной workflow: фото → валидация → .docx
│   │   │   ├── admin_docs.py     # Добавление шаблонов (AI анализ + генерация полей)
│   │   │   └── admin_manage.py   # Управление шаблонами (просмотр, переименование, удаление)
│   │   ├── keyboards/            # Клавиатуры (ReplyKeyboard, InlineKeyboard)
│   │   ├── states/               # FSM состояния
│   │   ├── views/                # Генерация текстовых представлений
│   │   └── bot.py                # Инициализация Dispatcher и Bot
│   ├── services/                 # Бизнес-логика
│   │   ├── gemini_service.py     # AI-провайдер: OCR + Schema-based extraction + Field Translation
│   │   ├── document_manager.py   # Управление конфигурацией документов и генерация JSON Schema
│   │   ├── docx_service.py       # Рендеринг .docx шаблонов (docxtpl + XML sanitization)
│   │   └── file_manager_service.py  # Скачивание фото, временные файлы, cleanup
│   ├── app.py                    # Оркестратор: logging → services → telegram + API → shutdown
│   ├── config.py                 # Единая конфигурация (Pydantic Settings из .env)
│   └── container.py              # DI-контейнер (register, register_lazy, __getattr__, shutdown)
├── libs/                         # ⚡ Инженерный слой (переиспользуемые обёртки)
│   └── utils/
│       └── logger.py             # Loguru конфигурация + InterceptHandler для stdlib logging
├── tests/                        # Тесты (pytest)
│   ├── conftest.py               # Глобальные фикстуры (container, mock_gemini_service)
│   └── test_gemini_service.py    # Тесты GeminiTranslationService (мок API)
├── templates/                    # Хранилище .docx шаблонов ({{ field_name }})
├── temp/                         # Временные файлы (фото, сгенерированные документы)
├── documents.json                # Конфигурация типов документов, полей и локализаций
├── main.py                       # Точка входа
├── Makefile                      # Команды разработки (run, test, lint, format, clean)
├── Procfile                      # Конфигурация для деплоя (Railway, Heroku)
├── nixpacks.toml                 # Конфигурация для Nixpacks (Railway)
├── requirements.txt              # Зависимости Python
├── .env                          # Секретные ключи и настройки окружения
└── .gitignore                    # Игнорируемые файлы
```

---

## 🚀 Установка и запуск

### 1. Подготовка системы

Убедитесь, что установлен **Python 3.12** или новее.

```bash
git clone <url-вашего-репозитория>
cd pearl_translation_service
```

### 2. Виртуальное окружение и зависимости

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Установка зависимостей
make install
# или вручную:
pip install -r requirements.txt
```

### 3. Настройка окружения `.env`

Создайте файл `.env` в корне проекта:

```env
# ── Telegram ──────────────────────────────────────────────────────
BOT_TOKEN=1234567890:ААBВСС...          # Токен от @BotFather
ADMIN_IDS=123456789,987654321            # Telegram ID администраторов

# ── AI / Gemini ───────────────────────────────────────────────────
GEMINI_API_KEY=AIzaSy...                 # API ключ из Google AI Studio

# ── Компоненты ────────────────────────────────────────────────────
RUN_TELEGRAM=true                        # Запускать Telegram-бота
RUN_API=true                             # Запускать FastAPI сервер

# ── Сетевые настройки ─────────────────────────────────────────────
API_HOST=0.0.0.0
PORT=8000

# ── Логирование ───────────────────────────────────────────────────
LOG_LEVEL=INFO                           # DEBUG, INFO, WARNING, ERROR
LOG_FILE=                                # Путь к файлу логов (пусто = только консоль)
LOG_JSON=false                           # JSON-формат для продакшена
```

### 4. Запуск

```bash
# Через Makefile:
make run

# Или напрямую:
python main.py
```

При успешном запуске в консоли появится цветной вывод Loguru:

```
2026-04-06 01:30:00 | INFO     | libs.utils.logger:setup_logger:89 — Логирование настроено (level=INFO, file=—, json=False)
2026-04-06 01:30:00 | INFO     | app.app:setup_services:35 — Setting up services...
2026-04-06 01:30:00 | INFO     | app.app:setup_telegram:47 — Starting Telegram Bot...
```

---

## ⚙️ Конфигурация (.env)

| Переменная | Описание | По умолчанию |
|---|---|---|
| `BOT_TOKEN` | Токен Telegram бота (обязательный) | — |
| `ADMIN_IDS` | Telegram ID администраторов (через запятую) | `[]` |
| `GEMINI_API_KEY` | API ключ Google Gemini | `""` |
| `GEMINI_API_KEY2` | Запасной API ключ Gemini | `""` |
| `API_HOST` | Хост API сервера | `0.0.0.0` |
| `PORT` | Порт API сервера | `8000` |
| `RUN_TELEGRAM` | Запускать Telegram-бота | `true` |
| `RUN_API` | Запускать FastAPI сервер | `true` |
| `RUN_WEBAPP` | Запускать WebApp | `false` |
| `WEBAPP_PORT` | Порт WebApp | `8001` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `LOG_FILE` | Путь к файлу логов | `None` |
| `LOG_JSON` | JSON-формат логов | `false` |

---

## 📋 Makefile — Команды разработки

| Команда | Описание |
|---|---|
| `make run` | Запустить приложение (`python main.py`) |
| `make test` | Запустить тесты (`pytest -v`) |
| `make test-cov` | Тесты с покрытием (`pytest --cov`) |
| `make lint` | Проверка линтером (`ruff check .`) |
| `make format` | Форматирование кода (`ruff format .`) |
| `make install` | Установить зависимости (`pip install -r requirements.txt`) |
| `make clean` | Удалить `__pycache__`, `.pytest_cache`, очистить `temp/` |

---

## 📝 Руководство пользователя

### 👤 Основной Workflow (Пользователь)

1. Отправьте `/start` — бот предложит удобное меню навигации.
2. Нажмите **«📄 Перевод документа»** — ознакомьтесь с инструкциями по фото (для лучшего качества).
3. Загрузите **одно или несколько фото** документа. Нажмите одну из кнопок распознавания:
   - **⚡ Быстрое распознавание (Flash)** — для простых документов
   - **🧠 Точное распознавание (Pro)** — для сложных или слабочитаемых
4. Выберите **тип документа** (Паспорт, Свидетельство, ID-карта и т.д.)
5. Выберите **язык перевода** (Русский или Английский)
6. AI проведёт обработку с использованием жёсткой JSON Schema
7. **Валидация данных:**
   - Простые поля — редактируйте нажатием кнопки ✏️
   - Таблицы — пагинация и построчное редактирование 📊
   - Режим Raw JSON — для опытных пользователей ⚙️
8. Нажмите **«✅ Подтвердить и создать»** — бот мгновенно сгенерирует и отправит `.docx` файл

### 👑 Workflow для Администраторов

1. Нажмите **«➕ Добавить шаблон»** в главном меню
2. Отправьте фото документа (одну или несколько страниц)
3. Выберите модель анализа (Flash / Pro) — AI определит структуру автоматически:
   - Название документа
   - Все поля с `keyword` (snake_case), `ru_name`, `en_name`
4. Проверьте результат и при необходимости:
   - Отредактируйте поля ✏️
   - Измените название 🏷
5. Укажите эмодзи для кнопки (📄, 💍 и т.д.)
6. Загрузите `.docx` шаблоны для RU и EN (или `skip` для пропуска)
7. Готово! — шаблон сразу доступен пользователям

**Управление шаблонами** (кнопка **«🗂 Мои шаблоны»**):
- Просмотр полей и ключей
- Скачивание текущих `.docx` шаблонов
- Замена шаблонов (RU/EN)
- Переименование
- Удаление

---

## ⚙️ Устройство `documents.json`

Файл `documents.json` — ядро типизации системы. Он определяет:

### Структура

```json
{
    "document_types": {
        "zagranpasport": {
            "name": "Загранпаспорт",
            "emoji": "🇺🇿"
        }
    },
    "configs": {
        "zagranpasport": {
            "fields": {
                "surname": {
                    "type": "string",
                    "ui_mapping": {
                        "ru": "Фамилия",
                        "en": "Surname"
                    }
                }
            },
            "tables": {
                "items": {
                    "description": "Список позиций",
                    "items": {
                        "item_name": { "type": "string" },
                        "quantity": { "type": "string" }
                    }
                }
            }
        }
    }
}
```

### Как это работает

1. **`document_types`** — реестр типов документов (имя + эмодзи для кнопок)
2. **`configs`** — для каждого типа:
   - `fields` — плоские поля (ключ → тип + локализация)
   - `tables` — табличные поля (массивы объектов)
3. Из `configs` автоматически генерируется **JSON Schema**, которая отправляется в Gemini для строгого извлечения данных
4. `ui_mapping` используется для локализации имён полей в интерфейсе бота

> **Гарантия**: благодаря строгому JSON Schema, Gemini всегда возвращает данные с ожидаемыми ключами, что исключает ошибки при рендеринге `.docx` шаблонов.

### Шаблоны `.docx`

Шаблоны Word используют Jinja2-синтаксис `docxtpl`:

```
Фамилия: {{ surname }}
Имя: {{ given_names }}
Дата рождения: {{ date_of_birth }}

{% for row in items %}
{{ row.item_name }} — {{ row.quantity }}
{% endfor %}
```

Файлы шаблонов хранятся в `templates/` с именованием: `{DOC_ID}_TEMPLATE_{LANG}.docx`

Например:
- `ZAGRANPASPORT_TEMPLATE_RU.docx`
- `ZAGRANPASPORT_TEMPLATE_EN.docx`

---

## 🧪 Тестирование

Проект использует **pytest** с поддержкой asyncio.

### Запуск тестов

```bash
# Все тесты
make test

# С покрытием
make test-cov

# Конкретный файл
pytest tests/test_gemini_service.py -v
```

### Фикстуры (`tests/conftest.py`)

| Фикстура | Описание |
|---|---|
| `container` | Чистый DI-контейнер |
| `mock_gemini_service` | GeminiTranslationService с замоканным API |
| `container_with_services` | Контейнер со всеми сервисами (моки) |

### Что тестируется

- **GeminiTranslationService** — мокирование `google-generativeai` ответов (тесты без API-трат)
- **JSON Schema** — валидация структуры `documents.json`
- **DocxService** — генерация документов с санитизацией XML
- **Container** — lazy init, shutdown, attribute access

---

## 🔧 Логирование (Loguru)

Проект использует **Loguru** как единый логгер, перехватывающий все `logging` вызовы из библиотек (aiogram, uvicorn, Google SDK).

### Режимы

| Режим | Настройка `.env` | Описание |
|---|---|---|
| **Консоль (dev)** | `LOG_JSON=false` | Цветной вывод с форматированием |
| **JSON (prod)** | `LOG_JSON=true` | Структурированные JSON-логи |
| **Файл** | `LOG_FILE=logs/app.log` | + ротация 10 MB, хранение 7 дней, zip-сжатие |

### Пример вывода

```
2026-04-06 01:30:00 | INFO     | app.app:run:75 — Setting up services...
2026-04-06 01:30:00 | INFO     | app.container:get:54 — Lazy init: создание сервиса 'gemini_service'
2026-04-06 01:30:01 | INFO     | app.app:setup_telegram:47 — Starting Telegram Bot...
```

---

## 🚀 Деплой

### Railway / Render

Проект готов к деплою на Railway/Render через `Procfile`:

```
web: python main.py
```

Настройте переменные окружения в панели управления хостинга (те же, что в `.env`).

### Docker (опционально)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

---

## 🤝 Разработка

### Добавление нового сервиса

1. Создайте класс в `app/services/my_service.py`
2. Зарегистрируйте в `app/app.py → setup_services()`:
   ```python
   # Лёгкий сервис — сразу
   self.container.register("my_service", MyService())
   
   # Тяжёлый сервис — лениво
   self.container.register_lazy("my_service", lambda: MyService(api_key=settings.KEY))
   ```
3. Используйте в хендлерах:
   ```python
   service = container.my_service  # или container.get("my_service")
   ```

### Добавление Telegram-роутера

1. Создайте роутер в `app/telegram/routers/my_router.py`
2. Подключите в `app/telegram/bot.py`:
   ```python
   from app.telegram.routers import my_router
   my_router.setup_router(container)
   dp.include_router(my_router.router)
   ```

### Добавление API-роутера

1. Создайте роутер в `app/api/routers/my_router.py`
2. Используйте `Depends` для инъекции контейнера:
   ```python
   from fastapi import APIRouter, Depends
   from app.api.dependencies import get_container
   from app.container import Container

   router = APIRouter()

   @router.get("/my-endpoint")
   async def my_endpoint(container: Container = Depends(get_container)):
       service = container.my_service
       return {"result": "ok"}
   ```
3. Подключите в `app/api/server.py`:
   ```python
   from app.api.routers import my_router
   app.include_router(my_router.router)
   ```

### Добавление модуля в `libs/`

1. Создайте файл в `libs/utils/my_module.py` (или `libs/category/my_module.py`)
2. Следуйте принципам:
   - **Self-Contained** — модуль обрабатывает свои ошибки
   - **Lazy Init** — тяжёлые клиенты создаются при первом вызове
   - **Config из `app.config`** — не хардкодите значения
3. Зарегистрируйте в `app/app.py`:
   ```python
   self.container.register_lazy("my_module", lambda: MyModule(url=settings.MY_URL))
   ```

### Code Style

```bash
# Проверка
make lint

# Авто-форматирование
make format
```

---

## 📄 Лицензия

Проприетарный проект. Все права защищены.
