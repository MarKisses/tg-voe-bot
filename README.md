# TG VOE Bot

## Короткий опис

Цей бот збирає та парсить графіки відключень з сайту VOE (voe.com.ua/disconnection/detailed), рендерить їх у вигляді зображень і надсилає користувачам Telegram. Підтримуються підписки на зміни графіків на сьогодні та на завтра.

Ключові можливості

- Пошук адрес (місто, вулиця, будинок)
- Збереження адрес користувача
- Автооновлення графіків (періодично, за замовчуванням ~15 хв)
- Підписки на зміни графіків (today / tomorrow)
- Рендер графіків у PNG

Технічний стек

- Python 3.10+
- aiogram (Telegram bot)
- redis (для збереження адрес, підписок? хешів, telegram FSM, service message)
- Pillow (рендер зображень)
- FlareSolverr (для обходу Cloudflare)

## Швидкий старт Docker

1. Клонувати репозиторій

   git clone <repo>
   cd new-voe-bot

2. Налаштувати змінні оточення

Помістіть копію .env у кореневу папку або налаштуйте змінні в оточенні. Основні змінні:

- BOT_TOKEN — токен Telegram бота
- BOT_MODE — polling або webhook
- ADMIN_ID — id адміністратора (опціонально)
- REDIS**HOST, REDIS**PORT, REDIS**DB, REDIS**USERNAME, REDIS\_\_PASSWORD
- FLARE**OPERATING_MODE, FLARE**SESSION, FLARE\_\_URL (для FlareSolverr)
- FETCHER\_\_BASE_URL — базовий URL для перегляду графіків
- NOTIFICATION\_\_INTERVAL — інтервал перевірки змін у секундах (за замовчуванням 900)
- WEBHOOK**URL, WEBHOOK**PORT, WEBHOOK**PATH, WEBHOOK**SECRET_TOKEN, WEBHOOK\_\_SSL_CERT/KEY

4. Запуск локально (polling)

   cd app
   python main.py

При webhook режимі потрібно забезпечити дійсний SSL сертифікат та коректні змінні для webhook.

## Docker

В проєкті є docker-compose з сервісом flaresolver (якщо потрібно). Щоб підняти контейнер бота через Compose, налаштуйте .env і запустіть:

    docker-compose up --build

## Пояснення компонентів

- app/services/fetcher.py — робить HTTP-запити до VOE (через FlareSolverr або проксі)
- app/services/parser.py — парсить HTML і будує модель графіку
- app/services/renderer.py — генерує PNG з графіком
- app/services/notification_worker.py — періодично перевіряє адреси й надсилає повідомлення підписникам
- app/storage — зберігання у Redis (addresses, subscriptions, кеш графіків)
- app/bot — логіка aiogram: handlers, menus, keyboards

## Підписки та нотифікації

- Користувач може підписатися на зміни на сьогодні або на завтра для будь-якої збереженої адреси.
- Сервер періодично (NOTIFICATION\_\_INTERVAL) перевіряє оновлення та надсилає повідомлення тим, у кого змінився хеш графіка.

## Тестовий mock endpoint

У репозиторії є мок-сервер для локальної розробки (mock_endpoint). Запустіть його, якщо хочете тестувати без доступу до реального VOE:

    python mock_endpoint/main.py

## Логи та налагодження

- Налаштування логування знаходиться в app/logger.py
- Для зручності кольорового виводу логів використовується кастомний форматер

