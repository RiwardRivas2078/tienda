FROM python:3.11.4-slim

WORKDIR /app

COPY requirements.txt .

# Forzamos la instalación de las dependencias
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Inicializa y construye la app de Reflex
RUN reflex init
RUN reflex export --frontend-only --no-zip && mv .web/_static/* /srv/ && rm -rf .web

# Comando de inicio para producción
CMD ["reflex", "run", "--env", "prod", "--backend-port", "10000", "--frontend-port", "10000"]