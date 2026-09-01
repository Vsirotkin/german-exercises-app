.PHONY: install run migrate makemigrations shell test createsuperuser clean lint format

# Установка зависимостей из pyproject.toml
install:
	uv sync

# Запуск сервера разработки
run:
	uv run python manage.py runserver

# Применение миграций к базе данных
migrate:
	uv run python manage.py migrate

# Создание новых файлов миграций после изменений в моделях
makemigrations:
	uv run python manage.py makemigrations

# Открытие интерактивной оболочки Django Shell
shell:
	uv run python manage.py shell

# Запуск тестов
test:
	uv run python manage.py test

# Создание суперпользователя (интерактивно)
createsuperuser:
	uv run python manage.py createsuperuser

# Очистка кэша, временных файлов и базы данных SQLite
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.sqlite3" -delete
	rm -rf staticfiles

# Линтинг кода (если подключите flake8 или ruff в будущем)
lint:
	@echo "Linting not configured yet."

# Форматирование кода (если подключите black или ruff в будущем)
format:
	@echo "Formatting not configured yet."


seed:
	uv run python manage.py seed_data


# Помощь по доступным командам
help:
	@echo "Доступные команды:"
	@echo "  make install          - Установить зависимости (uv sync)"
	@echo "  make run              - Запустить сервер разработки"
	@echo "  make migrate          - Применить миграции"
	@echo "  make makemigrations   - Создать новые миграции"
	@echo "  make shell            - Открыть Django Shell"
	@echo "  make test             - Запустить тесты"
	@echo "  make createsuperuser  - Создать администратора"
	@echo "  make clean            - Очистить кэш и БД"
	@echo "  make seed             - Наполнить БД тестовыми данными (упражнения, темы)"
	@echo "----------------------------------------"