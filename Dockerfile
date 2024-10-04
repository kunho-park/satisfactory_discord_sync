FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
COPY run.py .
COPY satisfactory/ ./satisfactory/

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["python", "run.py"]
