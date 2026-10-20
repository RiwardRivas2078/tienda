FROM python:3.11-slim

# 1. Instalamos Node.js, npm, unzip, Caddy y certificados
RUN apt-get update && apt-get install -y nodejs npm unzip caddy ca-certificates && rm -rf /var/lib/apt/lists/*

# 2. Instalamos Bun manualmente para evitar fallos de SSL
RUN npm install -g bun

WORKDIR /app

# 3. Copiamos e instalamos dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiamos el resto del proyecto
COPY . .

# 5. Forzamos el uso de npm y desactivamos verificación SSL
ENV REFLEX_USE_NPM=1
ENV SSL_NO_VERIFY=1
ENV NODE_TLS_REJECT_UNAUTHORIZED=0

# 6. Inicializamos Reflex y construimos el frontend
RUN reflex init --template blank
RUN reflex export --frontend-only --no-zip && mv .web/_static/* /srv/ && rm -rf .web

# 7. Configuración de Caddy con soporte explícito para WebSockets
RUN cat > Caddyfile <<EOF
:{\$PORT} {
    encode gzip
    
    # Proxy para WebSockets (eventos en tiempo real)
    reverse_proxy /_event/* localhost:8000 {
        transport http {
            read_timeout 300s
        }
    }
    
    # Proxy para otras rutas del backend
    reverse_proxy /ping localhost:8000
    reverse_proxy /_upload/* localhost:8000

    # Servir el frontend estático
    root * /srv
    try_files {path} {path}/ /404.html
    file_server
}
EOF

EXPOSE 10000
CMD ["sh", "-c", "caddy start && reflex run --env prod --backend-only"]