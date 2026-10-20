FROM python:3.11-slim

# Instalamos Node.js, npm, unzip, Caddy y certificados
RUN apt-get update && apt-get install -y nodejs npm unzip caddy ca-certificates && rm -rf /var/lib/apt/lists/*

# Instalamos Bun manualmente para evitar fallos de SSL
RUN npm install -g bun

WORKDIR /app

# Copiamos e instalamos dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

# Forzamos el uso de npm y desactivamos verificación SSL
ENV REFLEX_USE_NPM=1
ENV SSL_NO_VERIFY=1
ENV NODE_TLS_REJECT_UNAUTHORIZED=0

# Inicializamos Reflex y construimos el frontend
RUN reflex init --template blank
RUN reflex export --frontend-only --no-zip && mv .web/_static/* /srv/ && rm -rf .web

# CONFIGURACIÓN DE CADDY CORREGIDA (basada en el ejemplo oficial de Reflex)
RUN cat > Caddyfile <<EOF
:{\$PORT} {
    encode gzip

    # Matcher para todas las rutas del backend (WebSocket, uploads, ping)
    @backend_routes path /_event/* /ping /_upload /_upload/*
    
    # Redirigir esas rutas al backend de Reflex en el puerto 8000
    handle @backend_routes {
        reverse_proxy localhost:8000
    }

    # Servir el frontend estático
    root * /srv
    route {
        try_files {path} {path}/ /404.html
        file_server
    }
}
EOF

# Señal para detener el backend correctamente
STOPSIGNAL SIGKILL

EXPOSE 10000
CMD ["sh", "-c", "caddy start && reflex run --env prod --backend-only"]