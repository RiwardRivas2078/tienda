FROM python:3.11-slim

# Instalamos las herramientas necesarias
RUN apt-get update && apt-get install -y nodejs npm unzip caddy ca-certificates && rm -rf /var/lib/apt/lists/*

# Instalamos Bun manualmente para evitar fallos de SSL
RUN npm install -g bun

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV REFLEX_USE_NPM=1
ENV SSL_NO_VERIFY=1
ENV NODE_TLS_REJECT_UNAUTHORIZED=0

RUN reflex init --template blank
RUN reflex export --frontend-only --no-zip && mv .web/_static/* /srv/ && rm -rf .web

# CONFIGURACIÓN DE CADDY PARA PERMITIR WEBSOCKETS (La clave del arreglo)
RUN cat > Caddyfile <<EOF
:{\$PORT} {
    encode gzip
    
    # Permitir conexiones en tiempo real (Websockets)
    @ws {
        header Connection *Upgrade*
        header Upgrade    websocket
    }
    reverse_proxy @ws localhost:8000
    
    # Rutas del backend de Python
    reverse_proxy /_event* localhost:8000
    reverse_proxy /ping localhost:8000
    reverse_proxy /_upload* localhost:8000

    # Servir el Frontend
    root * /srv
    try_files {path} {path}/ /404.html
    file_server
}
EOF

EXPOSE 10000

CMD ["sh", "-c", "caddy start && reflex run --env prod --backend-only"]