# Tasks: LLM Curation Pipeline

## Phase 1: Thumbnail Generator
> Создание оптимизированных thumbnails для эффективной отправки в LLM

- [ ] **1.1** Создать структуру модуля `src/curation/` с `__init__.py`
- [ ] **1.2** Реализовать `ThumbnailGenerator` в `src/curation/thumbnail.py`
  - Resize с сохранением aspect ratio (max 512x512)
  - JPEG compression (quality 60)
  - Base64 encoding для API
- [ ] **1.3** Написать unit-тесты для ThumbnailGenerator
  - Тест: выходной размер ≤ 512x512
  - Тест: выходной файл ≤ 50KB
  - Тест: различные форматы входа (jpg, png, webp)
- [ ] **1.4** Добавить Pillow в зависимости проекта

---

## Phase 2: LLM Scoring
> Интеграция с Groq Vision API для оценки изображений

- [ ] **2.1** Создать `src/curation/models.py` с Pydantic моделями
  - `ImageScore`: wow_factor, engagement, tiktok_fit, is_explicit, reasoning
  - `CurationConfig`: threshold, max_size, quality, dry_run
- [ ] **2.2** Разработать scoring prompt (`src/curation/prompts.py`)
  - Чёткие критерии для каждой метрики
  - JSON output format
  - Explicit content detection
- [ ] **2.3** Реализовать `ImageScorer` в `src/curation/scorer.py`
  - Интеграция с Groq через langchain-groq
  - Async методы для scoring
  - Парсинг JSON ответа
- [ ] **2.4** Написать тесты для ImageScorer
  - Mock API responses
  - Тест парсинга JSON
  - Тест explicit detection

---

## Phase 3: Curation Logic
> Логика принятия решений и перемещения файлов

- [ ] **3.1** Реализовать `CurationPipeline` в `src/curation/pipeline.py`
  - Поиск изображений в папке
  - Threshold-based filtering
  - Перемещение в `data/curated/`
- [ ] **3.2** Добавить структуру `data/curated/` в проект
- [ ] **3.3** Реализовать dry-run режим
- [ ] **3.4** Добавить reporting/logging
  - Результат по каждому изображению
  - Итоговая статистика
- [ ] **3.5** Написать integration тесты
  - End-to-end с mock API
  - Проверка перемещения файлов

---

## Phase 4: CLI & Integration
> CLI интерфейс и интеграция с проектом

- [ ] **4.1** Создать CLI в `src/curation/cli.py` с командами:
  - `curate <path>` — курация папки
  - `curate-all` — курация всего incoming
  - `stats` — статистика
- [ ] **4.2** Добавить entry point в `pyproject.toml`
- [ ] **4.3** Добавить документацию в README или docs/
- [ ] **4.4** Финальное тестирование на реальных данных

---

## Dependencies

| Package | Purpose | Status |
|---------|---------|--------|
| `Pillow` | Image processing | Needs install |
| `langchain-groq` | Groq API | Already in project |
| `typer` | CLI | Needs install |
| `pydantic` | Data models | Already in project |

---

## Verification Checklist

```bash
# Unit tests
pytest tests/test_thumbnail.py -v
pytest tests/test_scorer.py -v

# Integration test
pytest tests/test_curation_pipeline.py -v

# Manual test on real data
python -m src.curation curate data/incoming/CCumpot/2026-01-22_07-01-58/ --dry-run

# Verify curated output
ls -la data/curated/
```

---

## Acceptance Criteria

1. ✅ Thumbnails генерируются корректно (≤50KB, ≤512x512)
2. ✅ LLM возвращает структурированные оценки
3. ✅ Explicit контент определяется и reject'ется
4. ✅ Изображения с score ≥ threshold перемещаются в `data/curated/`
5. ✅ CLI работает с dry-run и threshold параметрами
6. ✅ Все тесты проходят
