version: '3.8'

services:
  # البوت الرئيسي
  whale-bot:
    build: .
    container_name: whale_bot
    ports:
      - "${PORT:-5000}:5000"
    environment:
      - LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN}
      - LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET}
      - GEMINI_API_KEY_1=${GEMINI_API_KEY_1}
      - GEMINI_API_KEY_2=${GEMINI_API_KEY_2}
      - GEMINI_API_KEY_3=${GEMINI_API_KEY_3}
      - USE_POSTGRES=true
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=whale_bot
      - POSTGRES_USER=whale_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-whale_password}
      - USE_REDIS=true
      - REDIS_HOST=redis
      - ENABLE_MONITORING=true
      - ENABLE_BACKUP=true
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - whale_network

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: whale_postgres
    environment:
      - POSTGRES_DB=whale_bot
      - POSTGRES_USER=whale_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-whale_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - whale_network

  # Redis
  redis:
    image: redis:7-alpine
    container_name: whale_redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - whale_network

  # Prometheus للمراقبة
  prometheus:
    image: prom/prometheus:latest
    container_name: whale_prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: unless-stopped
    networks:
      - whale_network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:

networks:
  whale_network:
    driver: bridge
