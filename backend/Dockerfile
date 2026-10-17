FROM python:3.12-slim AS base
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app

FROM base AS deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM base AS runtime
COPY --from=deps /root/.local /home/app/.local
ENV PATH="/home/app/.local/bin:$PATH"
COPY backend/app ./app
COPY backend/requirements.txt .

RUN chown -R app:app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import httpx; r=httpx.get('http://localhost:8000/api/v1/healthz', timeout=3); assert r.status_code==200" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]