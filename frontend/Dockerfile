FROM node:20-alpine

WORKDIR /app

# Обновляем системные пакеты для закрытия CVE в OpenSSL
RUN apk update && apk upgrade --no-cache

# Обновляем npm до последней версии для закрытия CVE в его зависимостях
RUN npm install -g npm@latest

# Копируем файлы зависимостей
COPY package.json package-lock.json ./

# Устанавливаем зависимости (пока от root)
RUN npm install

# Копируем исходный код
COPY . .

# Передаем права на всю папку приложения встроенному пользователю node (UID 1000)
RUN chown -R node:node /app

# Переключаемся на non-root пользователя
USER node

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
