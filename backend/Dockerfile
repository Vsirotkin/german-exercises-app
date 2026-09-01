FROM python:3.12-slim

# Копируем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Обновляем системные пакеты для закрытия CVE в OpenSSL и util-linux
# и удаляем кэш apt для уменьшения размера образа
RUN apt-get update && apt-get upgrade -y && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Создаем пользователя с UID 1000 (как у твоего пользователя vik на хосте)
RUN useradd -u 1000 -m -s /bin/bash appuser

WORKDIR /app

# Делаем пользователя владельцем рабочей папки
RUN chown -R appuser:appuser /app

# Переключаемся на non-root пользователя
USER appuser

# Настраиваем окружение для uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV HOME=/home/appuser

# Копируем зависимости и устанавливаем их
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Очищаем кэш uv для уменьшения размера образа
RUN rm -rf $HOME/.cache/uv

# Копируем исходный код с правильными правами
COPY --chown=appuser:appuser . .

EXPOSE 8000

CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
