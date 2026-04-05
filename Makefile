.PHONY: run test test-cov lint format install clean help

# ── Основные команды ──────────────────────────────────────────────

run:  ## Запустить приложение
	python main.py

test:  ## Запустить тесты
	pytest -v

test-cov:  ## Тесты с покрытием
	pytest --cov=app --cov=libs --cov-report=term-missing -v

lint:  ## Проверка линтером (ruff)
	ruff check .

format:  ## Форматирование кода (ruff)
	ruff format .

install:  ## Установить зависимости
	pip install -r requirements.txt

clean:  ## Удалить кэши и временные файлы
	@echo Cleaning...
	@if exist __pycache__ rd /s /q __pycache__
	@if exist .pytest_cache rd /s /q .pytest_cache
	@if exist temp rd /s /q temp && mkdir temp
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
	@echo Done.

help:  ## Показать доступные команды
	@echo Available commands:
	@echo   make run       - Start the application
	@echo   make test      - Run tests
	@echo   make test-cov  - Run tests with coverage
	@echo   make lint      - Check code with ruff
	@echo   make format    - Format code with ruff
	@echo   make install   - Install dependencies
	@echo   make clean     - Remove caches and temp files
