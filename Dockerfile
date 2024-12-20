FROM python:3.9-alpine

WORKDIR /app

COPY requirements.txt .

# ติดตั้ง dependencies ที่จำเป็น
RUN apk add --no-cache \
    postgresql-dev \
    python3-dev \
    gcc \
    musl-dev

RUN pip install -r requirements.txt

COPY . .

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]