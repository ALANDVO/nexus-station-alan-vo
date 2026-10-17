FROM node:24-alpine AS base
WORKDIR /app
RUN addgroup -S app && adduser -S -G app app

FROM base AS deps
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --omit=dev

FROM base AS build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM base AS runtime
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY frontend/package.json ./

RUN chown -R app:app /app
USER app

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q --spider http://localhost:80/ || exit 1

CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "80"]