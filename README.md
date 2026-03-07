# Private Law Library — Telegram Content Bot

Минимальный production-ready контент-движок и микро-CMS для Telegram-канала **Private Law Library**.

## Что делает проект

Бот автоматически публикует регулярные рубрики:

1. **Roman Law Today** (полностью dataset-driven)
2. **Аргумент дня** (dataset + опционально LLM)

Ключевой принцип: система работает стабильно даже без OpenAI API.

---

## Структура проекта

```text
pll_content_bot/
  app/
    main.py
    config.py
    logger.py
    db/
      database.py
      models.py
      queries.py
    scheduler/
      scheduler.py
      jobs.py
    bot/
      bot.py
      handlers.py
      publisher.py
      moderation.py
    rubrics/
      base_rubric.py
      roman_law_today.py
      argument_of_the_day.py
    services/
      dataset_loader.py
      openai_client.py
    formatters/
      telegram_formatter.py
    data/
      roman_posts.csv
      argument_topics.csv
  .env.example
  requirements.txt
```

---

## Установка

```bash
cd pll_content_bot
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Заполните `.env` реальными значениями.

---

## Конфигурация `.env`

- `BOT_TOKEN` — токен Telegram-бота
- `CHANNEL_ID` — ID канала (`@channel_name` или numeric id)
- `ADMIN_CHAT_ID` — chat id администратора для модерации/команд
- `AUTO_PUBLISH` — стартовое значение `true/false`
- `SQLITE_PATH` — путь к SQLite БД
- `OPENAI_API_KEY` — опционально; если пусто, LLM отключен
- `ROMAN_POST_HOUR` — час публикации Roman Law Today
- `ARGUMENT_POST_HOUR` — час публикации Аргумент дня

> `.env` задает **стартовые значения**. Для ежедневной работы часть параметров управляется через runtime-настройки в SQLite.

---

## Runtime-настройки (SQLite)

Таблица `runtime_settings` хранит параметры, которые можно менять без правки `.env`:

- `auto_publish` — главный переключатель автопубликации во время работы бота.

На старте бота значение инициализируется из `.env`, если ключа еще нет в БД.

---

## Запуск

```bash
cd pll_content_bot
python -m app.main
```

После запуска:
- стартует polling Telegram-бота;
- создается/инициализируется SQLite;
- поднимается APScheduler с ежедневными задачами.

---

## Редакционный workflow

### Статусы контента
`draft → ready → scheduled → published → archived`

В MVP используются ключевые переходы:
- при `auto_publish=true`: сразу `published`
- при `auto_publish=false`: `draft` в админ-чат, затем ручная модерация

### Модерация
Когда `auto_publish=false`, админ получает черновик с inline-кнопками:
- **Publish** — публикует в канал
- **Regenerate** — перегенерирует текст (актуально для «Аргумент дня»)
- **Skip** — архивирует/пропускает элемент

---

## Админ-команды

Все команды ниже — **только для `ADMIN_CHAT_ID`**.

- `/help_admin` — список админ-команд. OpenAI не нужен.
- `/status` — текущий статус: auto publish, OpenAI, scheduler, расписание, путь к БД, размеры dataset и остатки, режим модерации. OpenAI не нужен.
- `/health` — health-check (SQLite, datasets, scheduler, OpenAI ON/OFF). OpenAI не нужен.
- `/stats` — статистика: опубликовано по рубрикам, пропуски, черновики, архив. OpenAI не нужен.
- `/test_roman` — создать и отправить администратору тестовый черновик Roman Law Today. OpenAI не нужен.
- `/test_argument` — создать и отправить администратору тестовый черновик Аргумент дня. OpenAI нужен только для генерации аргументов (иначе будет fallback с вопросом).
- `/publish_roman` — немедленно обработать следующий Roman item (в канал или в модерацию в зависимости от `auto_publish`). OpenAI не нужен.
- `/publish_argument` — немедленно обработать следующий Argument item (в канал или в модерацию по `auto_publish`). OpenAI опционален.
- `/next_roman` — показать следующий Roman item (reference/latin/id). OpenAI не нужен.
- `/next_argument` — показать следующий Argument topic/id. OpenAI не нужен.
- `/skip_roman` — пометить следующий Roman item как пропущенный. OpenAI не нужен.
- `/skip_argument` — пометить следующий Argument topic как пропущенный. OpenAI не нужен.
- `/autopublish_on` — включить runtime `auto_publish=true`.
- `/autopublish_off` — выключить runtime `auto_publish=false`.
- `/scheduler_status` — показать зарегистрированные job’ы и `next_run_time`.

---

## Данные и рубрики

### Roman Law Today
Источник: `app/data/roman_posts.csv`

Поля:
- `reference`
- `latin`
- `translation`
- `explanation`
- `modern`

### Аргумент дня
Источник: `app/data/argument_topics.csv`

Поле:
- `topic`

Если `OPENAI_API_KEY` не задан, пост публикуется только с вопросом.

---

## SQLite: что хранится

### `content_items`
- id
- rubric_type
- source_item_id
- formatted_text
- status
- created_at
- published_at
- tags

### `dataset_usage`
- rubric_type
- source_item_id
- used_at
- status

### `runtime_settings`
- key
- value
- updated_at

---

## Как добавить новый контент

1. Дополнить CSV в `app/data/`.
2. Перезапуск не обязателен: рубрики читают CSV при генерации.

## Как добавить новую рубрику

1. Создать модуль в `app/rubrics/` с реализацией `BaseRubric`:
   - `load_next_item()`
   - `render_post()`
   - `mark_published()`
   - `peek_next_item()`
   - `mark_skipped()`
2. Добавить rubric в `app/main.py`.
3. Добавить job в `app/scheduler/scheduler.py`.
