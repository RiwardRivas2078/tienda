FROM python:3.11-slim

# Instalamos Node.js, npm y unzip (para que Reflex use npm en lugar de Bun)
RUN apt-get update && apt-get install -y nodejs npm unzip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Forzamos a Reflex a usar npm en lugar de Bun
ENV REFLEX_USE_NPM=1

RUN reflex init

EXPOSE 10000

CMD ["reflex", "run", "--env", "prod", "--backend-port", "10000", "--frontend-port", "10000"]