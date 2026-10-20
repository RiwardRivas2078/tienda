FROM python:3.11-slim

# 1. Instalamos Node.js, npm, unzip, Caddy y certificados SSL actualizados
RUN apt-get update && apt-get install -y nodejs npm unzip caddy ca-certificates && rm -rf /var/lib/apt/lists/*

# 2. Instalamos Bun manualmente usando npm para evitar la descarga directa desde GitHub
RUN npm install -g bun

WORKDIR /app

# 3. Copiamos e instalamos las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiamos el resto del proyecto
COPY . .

# 5. Forzamos el uso de npm y desactivamos la verificación SSL (por si acaso)
ENV REFLEX_USE_NPM=1
ENV SSL_NO_VERIFY=1
ENV NODE_TLS_REJECT_UNAUTHORIZED=0

# 6. Inicializamos Reflex (ahora encontrará Bun ya instalado)
RUN reflex init --template blank

# 7. Construimos el frontend y lo movemos a la carpeta que servirá Caddy
RUN reflex export --frontend-only --no-zip && mv .web/_static/* /srv/ && rm -rf .web

# 8. Configuramos Caddy como proxy inverso
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

# 9. Exponemos el puerto que Render espera
EXPOSE 10000

# 10. Comando de inicio: Caddy sirve el frontend y el backend corre en segundo plano
CMD ["sh", "-c", "caddy start && reflex run --env prod --backend-only"]