# TG VOE Bot

## Короткий опис

Цей бот збирає та парсить графіки відключень з сайту VOE (voe.com.ua/disconnection/detailed), рендерить їх у вигляді зображень і надсилає користувачам Telegram. Підтримуються підписки на зміни графіків на сьогодні та на завтра.

Бот працює за @tg_voe_bot

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

## Швидкий старт через docker-compose

1. Клонувати репозиторій

    ```
    git clone https://github.com/MarKisses/tg-voe-bot.git
    cd tg-voe-bot
   ```

2. Налаштувати змінні оточення

Помістіть копію .env у кореневу папку або налаштуйте змінні в оточенні. Основні змінні:

- BOT_TOKEN — токен Telegram бота
- BOT_MODE — polling або webhook (polling локально, webhook для VPS/хостингу)
- ADMIN_ID — id адміністратора (поки немає функціоналу)
- REDIS - налаштування підключення до Redis
- FLARE - налаштування FlareSolverr
    - FLARE__OPERATING_MODE — cookie або proxy (використовувати як cookie-getter або проксі)
    - FLARE__SESSION — назва сесії (якщо proxy режим, щоб всі запити йшли через одну сесію)
    - FLARE__URL - URL FlareSolverr (за замовчуванням http://flaresolverr:8191)
- NOTIFICATION__INTERVAL — інтервал перевірки змін у секундах (за замовчуванням 900 - 15 хв)


3. Запуск long-polling бота

    ```
    docker-compose up --build
    ```

## Використання webhook (напр. для VPS)

Для використання webhook режиму є 3 варіанти:

1. Оренда VPS з білим IP (щоб Telegram міг достукатись до бота)
    - Генерація SSL сертифікату (Self-signed certificate). Детальніше [тут](https://core.telegram.org/bots/self-signed).
    - Налаштування змінних оточення:
        - BOT_MODE=webhook
        - WEBHOOK__URL=ip_of_your_vps
        - WEBHOOK__PORT=8443 (телеграм підтримує лише 443, 80, 88, 8443)
        - WEBHOOK__PATH=/webhook (будь-який шлях)
        - WEBHOOK__SECRET_TOKEN=my-secret-token (секретний токен, щоб переконатися, що запити йдуть від Telegram.)
        - WEBHOOK__SSL_CERT_PATH=шлях_до_сертифікату.pem
        - WEBHOOK__SSL_KEY_PATH=шлях_до_ключа.pem
    - Запуск бота через docker-compose
    ```
    docker-compose up --build
    ```

2. Використання reverse proxy (nginx, cloudflare tunnel тощо)
    - В розробці

3. Ngrok
    - В розробці


## Пояснення компонентів

- app/bot — логіка aiogram: handlers, menus, keyboards
- app/storage — зберігання у Redis (addresses, subscriptions, кеш графіків)
- app/services/fetcher.py — фетчер до ендпоінтів VOE (з fallback на FlareSolverr)
- app/services/parser.py — парсер.
- app/services/renderer.py — PIL рендеринг графіків у PNG.
- app/services/notification_worker.py — перевірка змін графіків та надсилання нотифікацій.

## Підписки та нотифікації

- Користувач може підписатися на зміни на сьогодні або на завтра для будь-якої збереженої адреси.
- Сервер періодично (15 хв.) перевіряє оновлення та надсилає повідомлення тим, у кого змінився хеш графіка.

## Тестовий mock endpoint
У репозиторії є мок-сервер для локальної розробки (mock_endpoint). Запустіть його, якщо хочете тестувати без доступу до реального VOE:

```
    cd mock_endpoint
    python main.py
```

Поки в розробці, як і написання повноцінних тестів.

## Логи та налагодження

- Налаштування логування знаходиться в app/logger.py
- Для зручності кольорового виводу логів використовується кастомний форматер

