FROM python:3.11-slim

# 1. Instalamos Node.js, npm, unzip y Caddy (servidor web para producción)
RUN apt-get update && apt-get install -y nodejs npm unzip caddy && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copiamos e instalamos las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copiamos el resto del proyecto
COPY . .

# 4. Forzamos a Reflex a usar npm y configuramos el registro para evitar errores de certificado
ENV REFLEX_USE_NPM=1
ENV NPM_CONFIG_REGISTRY=https://registry.npmjs.org/
ENV NODE_TLS_REJECT_UNAUTHORIZED=0

# 5. Inicializamos Reflex y construimos el frontend
RUN reflex init --template blank
RUN reflex export --frontend-only --no-zip && mv .web/_static/* /srv/ && rm -rf .web

# 6. Configuramos Caddy como proxy inverso para servir el frontend y redirigir al backend
RUN cat > Caddyfile <<EOF
:{\$PORT} {
    encode gzip
    @backend_routes path /_event/* /ping /_upload /_upload/*
    handle @backend_routes {
        reverse_proxy localhost:8000
    }
    root * /srv
    route {
        try_files {path} {path}/ /404.html
        file_server
    }
}
EOF

# 7. Exponemos el puerto que Render espera (10000)
EXPOSE 10000

# 8. Comando de inicio: Caddy sirve el frontend y el backend corre en segundo plano
CMD ["sh", "-c", "caddy start && reflex run --env prod --backend-only"]