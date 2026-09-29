# Dockerfile for the phone-first AI Trading Agent
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    AGENT_MODE=paper \
    DEFAULT_LANGUAGE=hi \
    LIVE_MODE_ENABLED=false

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY app.py ./app.py
COPY src ./src
COPY examples ./examples

EXPOSE 8000

CMD ["python", "app.py"]
