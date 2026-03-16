#!/bin/bash
# Скрипт первичного получения SSL сертификата от Let's Encrypt
# Запускать ОДИН РАЗ на VPS до docker compose up
#
# Использование: sudo bash scripts/init-ssl.sh k1ckoff.duckdns.org your@email.com

set -e

DOMAIN=${1:-"k1ckoff.duckdns.org"}
EMAIL=${2:-"admin@example.com"}

echo "========================================"
echo "  SSL Certificate Init for $DOMAIN"
echo "========================================"

# Проверяем что certbot установлен
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    apt-get update -qq
    apt-get install -y certbot
fi

echo "⏹  Freeing port 80..."

# Останавливаем все Docker-контейнеры
docker compose down 2>/dev/null || true
docker stop $(docker ps -q) 2>/dev/null || true

# Останавливаем системный nginx/apache если есть
systemctl stop nginx 2>/dev/null || true
systemctl stop apache2 2>/dev/null || true

# Убиваем любой процесс на порту 80
fuser -k 80/tcp 2>/dev/null || true

# Ждём секунду чтобы порт освободился
sleep 2

# Проверяем что порт 80 свободен
if ss -tlnp | grep -q ':80 '; then
    echo "❌ Port 80 is still in use!"
    ss -tlnp | grep ':80'
    echo "Kill the process manually and re-run the script."
    exit 1
fi

echo "✅ Port 80 is free"

# Получаем сертификат
echo "🔐 Requesting SSL certificate for $DOMAIN..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"

echo ""
echo "✅ Certificate obtained!"
echo "   Cert: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "   Key:  /etc/letsencrypt/live/$DOMAIN/privkey.pem"
echo ""

# Настраиваем автообновление через cron
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    COMPOSE_DIR=$(pwd)
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && docker compose -f $COMPOSE_DIR/docker-compose.yml restart nginx") | crontab -
    echo "✅ Auto-renewal cron job added (daily at 3:00 AM)"
fi

echo ""
echo "🚀 Now run: docker compose up --build -d"
