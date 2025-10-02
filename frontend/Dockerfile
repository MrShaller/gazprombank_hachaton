# Базовый образ с Node.js 18 (лёгкий Alpine)
FROM node:18-alpine AS base

# ---------- DEPS ----------
FROM base AS deps
RUN apk add --no-cache libc6-compat

# Устанавливаем рабочую директорию
WORKDIR /app
# Копируем package.json и package-lock.json для установки зависимостей
COPY package.json package-lock.json* ./
# Устанавливаем зависимости (npm ci быстрее и чище, чем npm install)
RUN npm ci   

# ---------- BUILD ----------
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED 1
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build
# ---------- RUNNER ----------
# Минимальный финальный образ для запуска
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Создаём непривилегированного пользователя (для безопасности)
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Копируем только нужные файлы из builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Запускаем под пользователем nextjs, а не root
USER nextjs

# Открываем порт 3000
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Команда запуска Next.js standalone (создаётся на этапе build)
CMD ["node", "server.js"]
