# ⚽ Football Bot — Local Development Guide

## Что нужно установить

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — для PostgreSQL, бэкенда и бота
- [Node.js 20+](https://nodejs.org/) — для фронтенда (npm run dev)
- (опционально) Python 3.12+ — если хочешь запускать бэкенд/бот без Docker

---

## Быстрый старт (рекомендуется)

### Шаг 1: Подготовь `.env`

Файл `.env` уже заполнен. Убедись что:
- `BOT_TOKEN` — твой токен от @BotFather ✅
- `VITE_API_URL=http://localhost:8000` ✅

### Шаг 2: Запусти PostgreSQL + Backend + Bot через Docker

```bash
cd football_bot

docker compose -f docker-compose.yml -f docker-compose.dev.yml up postgres backend bot --build
```

Это запустит:
- 🗄 **PostgreSQL** → localhost:5432
- 🔌 **FastAPI Backend** → http://localhost:8000 (hot-reload)
- 🤖 **Telegram Bot** → подключится к Telegram автоматически

### Шаг 3: Запусти Frontend отдельно (hot-reload)

В **новом терминале**:

```bash
cd football_bot/frontend
npm install        # один раз
npm run dev
```

Открой в браузере: **http://localhost:5173**

> 🛠 Откроется в **Dev Mode** — жёлтая полоска сверху.
> Авторизация происходит автоматически с тестовым пользователем (без Telegram).

---

## Что и где тестировать

| Компонент | URL | Описание |
|-----------|-----|----------|
| **Mini App** | http://localhost:5173 | Vue 3 приложение, dev-mode |
| **API Docs** | http://localhost:8000/docs | Swagger UI — все эндпоинты |
| **API ReDoc** | http://localhost:8000/redoc | Альтернативная документация |
| **Telegram Bot** | @твой_бот в Telegram | Работает при запущенном Docker |
| **PostgreSQL** | localhost:5432 | Подключись через DBeaver/TablePlus |

---

## Тестирование API через Swagger

Открой http://localhost:8000/docs

Для запросов от имени тестового пользователя добавь заголовок:
```
X-Bot-Auth: 999999999
```

В Swagger нажми **Authorize** → введи имя `X-Bot-Auth`, значение `999999999`.

---

## Полный запуск через Docker (как на продакшне)

```bash
docker compose up --build -d
```

Откроет всё на порту 80 (nginx проксирует всё).

---

## Структура проекта

```
football_bot/
├── .env                    ← переменные окружения
├── docker-compose.yml      ← продакшн
├── docker-compose.dev.yml  ← dev (без frontend/nginx контейнеров)
├── backend/                ← FastAPI + SQLAlchemy + PostgreSQL
│   └── app/
│       ├── models/         (user, match, participant, stats, payment)
│       ├── schemas/        (Pydantic)
│       ├── routers/        (auth, users, matches)
│       └── services/       (telegram_auth, file_upload)
├── bot/                    ← aiogram 3
│   └── bot/
│       ├── handlers/       (start, profile, matches, friends)
│       ├── keyboards/      (reply + inline)
│       ├── states/         (FSM)
│       └── api/            (HTTP клиент к backend)
├── frontend/               ← Vue 3 Mini App
│   ├── .env.local          ← локальные переменные для npm run dev
│   └── src/
│       ├── views/          (Profile, Matches, MatchDetail, CreateMatch, Friends, SubmitStats)
│       ├── components/     (BottomNav, MatchCard)
│       ├── stores/         (Pinia: auth, matches)
│       └── api/            (Axios)
└── nginx/                  ← nginx конфиг для продакшна
```

---

## Возможные проблемы

**Backend не стартует — ошибка БД**
```bash
docker compose logs backend
# Подожди пока postgres будет ready, или перезапусти:
docker compose restart backend
```

**CORS ошибка в браузере**
Убедись что в `.env` есть:
```
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:80,...
```
И перезапусти backend: `docker compose restart backend`

**Бот не отвечает**
```bash
docker compose logs bot
# Убедись что BOT_TOKEN правильный
```

**Хочу второго тестового пользователя**
Измени в `frontend/src/stores/auth.js`:
```js
const DEV_USER = { telegram_id: 999999998, username: 'dev_user2', first_name: 'Dev2', last_name: 'User' }
```
Открой в другом браузере/incognito.
