FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
COPY run.py .
COPY satisfactory/ ./satisfactory/

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD test -f /app/logs/FactoryGame.log

CMD ["python", "run.py"]
