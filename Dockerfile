FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.in ./
RUN pip install --no-cache-dir -r requirements.in

COPY . .

EXPOSE 8002

CMD ["uvicorn", "src.interface.http.main:app", "--host", "0.0.0.0", "--port", "8002"]
