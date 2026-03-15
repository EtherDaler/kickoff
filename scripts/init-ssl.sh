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

# Убеждаемся что порт 80 свободен (останавливаем Docker если запущен)
echo "⏹  Stopping any running containers on port 80..."
docker compose down 2>/dev/null || true

# Получаем сертификат (standalone — certbot сам поднимет временный веб-сервер)
echo "🔐 Requesting SSL certificate for $DOMAIN..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"

echo ""
echo "✅ Certificate obtained!"
echo "   Location: /etc/letsencrypt/live/$DOMAIN/"
echo ""

# Настраиваем автообновление через cron
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    echo "⏰ Setting up auto-renewal cron job..."
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && docker compose -f $(pwd)/docker-compose.yml restart nginx") | crontab -
    echo "✅ Cron job added (runs daily at 3:00 AM)"
fi

echo ""
echo "🚀 Now run: docker compose up --build -d"
