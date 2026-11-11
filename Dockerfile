# Pin a specific minor for reproducibility; pin by @sha256 digest in prod.
FROM python:3.12.7-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Run as non-root (Cloud Run best practice).
RUN useradd -m -u 10001 appuser && chown -R appuser /app
USER appuser
# Cloud Run injects $PORT (default 8080). --preload shares memory across workers.
CMD exec gunicorn --bind :${PORT:-8080} --workers 2 --threads 4 --timeout 180 --preload app:app
