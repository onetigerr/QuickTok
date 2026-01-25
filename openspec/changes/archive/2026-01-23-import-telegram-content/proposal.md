# Change: Import Content from Telegram Channels

## Why
Нужен модуль для автоматизированного скачивания контента (фото/видео) из Telegram-каналов. Это расширяет источники контента для QuickTok помимо Douyin.

## What Changes
- Создать универсальный Telegram-клиент на базе **Telethon** для подключения и итерации по истории канала.
- Реализовать систему адаптеров для нормализации метаданных под конкретные каналы.
- Первый адаптер: **CCumpot** — парсинг имени модели из caption.
- Хранить метаданные в SQLite для дедупликации и учёта.
- CLI: `python run_import.py --channel <name> [--limit N]`

## Impact
- **New Capability**: `telegram-client` — универсальный клиент для Telegram.
- **New Capability**: `content-adapter` — система адаптеров для каналов.
- **New Files**:
    - `src/telegram/client.py` — TelegramClientWrapper
    - `src/telegram/adapters/base.py` — BaseAdapter
    - `src/telegram/adapters/ccumpot.py` — CCumpotAdapter
    - `src/telegram/models.py` — Pydantic модели (ImportedPost)
    - `src/telegram/database.py` — SQLite repository
    - `run_import.py` — CLI entrypoint

## Key Decisions
1. **Session files**: Используем готовые `.session` файлы из `data/sessions/`.
2. **Порядок скачивания**: От новых к старым, без лимита по глубине.
3. **Batch size**: Пагинация по N постов (настраивается).
4. **Ошибки**: Логируем и пропускаем, при 3 ошибках подряд — остановка.
5. **Фильтрация рекламы**: Не реализуем (игнорируем).
