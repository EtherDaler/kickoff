# ⚽ Football Bot — Полная инструкция деплоя на VPS

## Требования к VPS
- Ubuntu 22.04 / Debian 12
- Минимум 1 CPU, 1 GB RAM
- Открытые порты: **80**, **443**
- Docker + Docker Compose установлены

---

## Шаг 1: Настройка DuckDNS

1. Зайди на https://www.duckdns.org
2. Убедись что домен `k1ckoff` создан и его IP указывает на **IP твоего VPS**
3. Проверь: `ping k1ckoff.duckdns.org` — должен вернуть IP твоего VPS

---

## Шаг 2: Установка Docker на VPS

```bash
ssh root@<IP_VPS>

curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin

# Проверь
docker --version
docker compose version
```

---

## Шаг 3: Загрузка кода на VPS

**Вариант A: через git**
```bash
git init && git add . && git commit -m "init"
# Создай репо на GitHub, затем на VPS:
git clone https://github.com/ВАШ_ЮЗЕР/football_bot.git
cd football_bot
```

**Вариант B: через scp (прямая копия)**
```bash
# На локальной машине:
scp -r /Users/dalerkhodzhimatov/Desktop/projects/football_bot root@<IP_VPS>:/opt/
ssh root@<IP_VPS>
cd /opt/football_bot
```

---

## Шаг 4: Получение SSL сертификата (ОБЯЗАТЕЛЬНО — без HTTPS Telegram не работает)

```bash
cd /opt/football_bot
chmod +x scripts/init-ssl.sh
sudo bash scripts/init-ssl.sh k1ckoff.duckdns.org твой@email.com
```

Скрипт:
- Установит certbot
- Остановит контейнеры на порту 80 (если были)
- Получит бесплатный SSL сертификат от Let's Encrypt
- Настроит автообновление через cron

---

## Шаг 5: Настройка BotFather

1. Открой @BotFather в Telegram
2. Найди своего бота → **Bot Settings** → **Menu Button** → **Configure menu button**
3. URL: `https://k1ckoff.duckdns.org`
4. Или создай Web App: `/newapp` → укажи URL `https://k1ckoff.duckdns.org`

---

## Шаг 6: Запуск проекта

```bash
cd /opt/football_bot
docker compose up --build -d
```

Проверь что всё запустилось:
```bash
docker compose ps
docker compose logs -f
```

---

## Проверка работы

| URL | Что должно быть |
|-----|-----------------|
| `https://k1ckoff.duckdns.org` | Mini App (Vue 3) |
| `https://k1ckoff.duckdns.org/api/docs` | Swagger API |
| `https://k1ckoff.duckdns.org/api/health` | `{"status":"ok"}` |
| Telegram → бот | Отвечает на /start |

---

## Полезные команды на VPS

```bash
# Посмотреть логи всех сервисов
docker compose logs -f

# Посмотреть логи конкретного сервиса
docker compose logs -f backend
docker compose logs -f bot
docker compose logs -f nginx

# Перезапустить один сервис
docker compose restart backend

# Остановить всё
docker compose down

# Обновить код и пересобрать
git pull
docker compose up --build -d

# Посмотреть базу данных
docker compose exec postgres psql -U kickoff -d kickoff
```

---

## Если что-то пошло не так

**nginx не стартует:**
```bash
docker compose logs nginx
# Чаще всего: нет SSL сертификата
# Решение: повтори шаг 4
```

**backend 500 ошибки:**
```bash
docker compose logs backend
# Смотри трейсбек, обычно это миграции или переменные окружения
```

**Бот не отвечает:**
```bash
docker compose logs bot
# Убедись что BOT_TOKEN правильный
```

**SSL сертификат истёк (через 90 дней):**
```bash
certbot renew
docker compose restart nginx
```

---

## Локальная разработка (без VPS)

```bash
# Терминал 1: Backend + DB + Bot
docker compose -f docker-compose.yml -f docker-compose.dev.yml up postgres backend bot --build

# Терминал 2: Frontend с hot-reload
cd frontend && npm run dev
# Открыть: http://localhost:5173
```

API документация: http://localhost:8000/docs
