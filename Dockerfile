FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "src/main.py"]