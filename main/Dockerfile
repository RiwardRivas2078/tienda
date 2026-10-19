FROM python:3.11-slim
WORKDIR /app
RUN apt-get update -y && apt-get install -y caddy && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN reflex init
RUN reflex export --frontend-only --no-zip && mv .web/_static/* /srv/ && rm -rf .web
ENV PORT=10000
EXPOSE 10000
CMD ["sh", "-c", "caddy start && reflex run --env prod --backend-only"]
