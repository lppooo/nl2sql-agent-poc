FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY requirements-postgres.txt .
RUN pip install --no-cache-dir -r requirements-postgres.txt

COPY . .

EXPOSE 8000 8501
