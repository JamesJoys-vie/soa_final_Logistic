FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY init.sql .
COPY app ./app
EXPOSE 8003
# python:3.12-slim has no curl
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health', timeout=2)"
# One worker: APScheduler runs in-process and SQLite allows one writer at a time.
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8003", "--workers", "1"]
