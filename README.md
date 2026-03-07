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
- `ADMIN_CHAT_ID` — chat id администратора для модерации
- `AUTO_PUBLISH` — `true/false`
- `SQLITE_PATH` — путь к SQLite БД
- `OPENAI_API_KEY` — опционально; если пусто, LLM отключен
- `ROMAN_POST_HOUR` — час публикации Roman Law Today
- `ARGUMENT_POST_HOUR` — час публикации Аргумент дня

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
- при `AUTO_PUBLISH=true`: сразу `published`
- при `AUTO_PUBLISH=false`: `draft` в админ-чат, затем ручная модерация

### Модерация
Когда `AUTO_PUBLISH=false`, админ получает черновик с inline-кнопками:
- **Publish** — публикует в канал
- **Regenerate** — перегенерирует текст (актуально для «Аргумент дня»)
- **Skip** — архивирует/пропускает элемент

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

Повтор dataset-элементов избегается, пока не исчерпается пул.

---

## Как добавить новый контент

1. Дополнить CSV в `app/data/`.
2. Перезапуск не обязателен: рубрики читают CSV при генерации.

## Как добавить новую рубрику

1. Создать модуль в `app/rubrics/` с реализацией `BaseRubric`:
   - `load_next_item()`
   - `render_post()`
   - `mark_published()`
2. Добавить rubric в `app/main.py`.
3. Добавить job в `app/scheduler/scheduler.py`.

---

## Примечания по надежности MVP

- Без OpenAI проект работает полноценно.
- Ошибки OpenAI не ломают pipeline: автоматически включается fallback.
- История публикаций и использование dataset фиксируются в SQLite.
