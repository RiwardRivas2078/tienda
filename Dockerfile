FROM python:3.11-slim

# Instalamos unzip (necesario para Reflex) y limpiamos la caché
RUN apt-get update && apt-get install -y unzip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN reflex init

EXPOSE 10000

CMD ["reflex", "run", "--env", "prod", "--backend-port", "10000", "--frontend-port", "10000"]