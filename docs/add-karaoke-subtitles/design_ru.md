# Дизайн: Модуль караоке-субтитров

## Контекст

QuickTok должен создавать TikTok-ready видео с синхронизированным TTS-аудио и караоке-субтитрами. Модуль должен быть независим от существующего роудмапа VideoCreator, позволяя параллельную разработку и гибкую композицию в будущих пайплайнах.

### Заинтересованные стороны
- Контент-креаторы, использующие QuickTok для создания TikTok-видео
- Разработчики, расширяющие пайплайн создания видео

### Ограничения
- Использовать Edge TTS (бесплатный, качественный, поддерживает события word-boundary)
- Создавать вертикальное видео формата 9:16
- Субтитры должны быть прожжёнными (burn-in), а не отдельным треком — для универсальной совместимости
- Поддержка нескольких языков (основной — испанский, но настраиваемо)

---

## Цели / Не-цели

### Цели
- Создать автономный переиспользуемый модуль для TTS + караоке-субтитров
- Обеспечить точную синхронизацию слов через события word-boundary Edge TTS
- Поддержать настраиваемую стилизацию через конфигурацию
- Реализовать надёжную сборку видео через FFmpeg/libass
- Хранить промежуточные артефакты для отладки и переиспользования

### Не-цели
- Интеграция с существующим VideoCreator в рамках этого изменения
- Генерация скриптов через LLM
- Пакетная обработка (задокументирована для будущего)
- Микширование музыки или несколько аудиодорожек
- Автоматическая генерация фонов из изображений

---

## Обзор архитектуры

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Модуль караоке-субтитров                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│   │    Вход      │    │   Хранение   │    │        Выход         │  │
│   │              │    │              │    │                      │  │
│   │ script.txt   │    │ data/audio/  │    │ final.mp4            │  │
│   │ bg.mp4       │    │   {hash}/    │    │ (с прожжёнными ASS)  │  │
│   │ config.json  │    │              │    │                      │  │
│   └──────┬───────┘    └──────────────┘    └──────────────────────┘  │
│          │                    ▲                      ▲               │
│          ▼                    │                      │               │
│   ┌──────────────┐            │                      │               │
│   │ Нормализатор │            │                      │               │
│   │    текста    │────────────┤                      │               │
│   └──────┬───────┘            │                      │               │
│          │                    │                      │               │
│          ▼                    │                      │               │
│   ┌──────────────┐            │                      │               │
│   │  TTS-движок  │────────────┤                      │               │
│   │  (Edge TTS)  │  voice.mp3 │                      │               │
│   │              │  boundaries│                      │               │
│   └──────┬───────┘            │                      │               │
│          │                    │                      │               │
│          ▼                    │                      │               │
│   ┌──────────────┐            │                      │               │
│   │  Сегментатор │            │                      │               │
│   │ (разбиение)  │            │                      │               │
│   └──────┬───────┘            │                      │               │
│          │                    │                      │               │
│          ▼                    │                      │               │
│   ┌──────────────┐            │                      │               │
│   │     ASS      │────────────┘                      │               │
│   │  Генератор   │  subs.ass                         │               │
│   └──────┬───────┘                                   │               │
│          │                                           │               │
│          ▼                                           │               │
│   ┌──────────────┐                                   │               │
│   │   Караоке    │───────────────────────────────────┘               │
│   │  Рендерер    │                                                   │
│   │   (FFmpeg)   │                                                   │
│   └──────────────┘                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Дизайн компонентов

### 1. Нормализатор текста (`normalizer.py`)

**Назначение**: Подготовка входного текста для стабильного синтеза TTS.

```python
@dataclass
class NormalizationConfig:
    collapse_whitespace: bool = True
    normalize_quotes: bool = True      # Умные кавычки → стандартные
    normalize_dashes: bool = True      # Em/en тире → дефис
    strip_control_chars: bool = True   # Удаление непечатаемых символов
    number_format: str = "spoken"      # "spoken" | "digits"

class TextNormalizer:
    def __init__(self, config: NormalizationConfig = None):
        self.config = config or NormalizationConfig()
    
    def normalize(self, text: str) -> str:
        """Нормализует текст для синтеза TTS."""
        
    def tokenize(self, text: str) -> List[Token]:
        """Разбивает текст на слова и пунктуацию."""
```

**Типы токенов**:
- `WORD`: Текст, который озвучивается и подсвечивается
- `PUNCTUATION`: Отображается, но не подсвечивается
- `WHITESPACE`: Не отображается в субтитрах

---

### 2. TTS-движок (`tts_engine.py`)

**Назначение**: Синтез речи и захват таймингов слов.

```python
@dataclass
class WordBoundary:
    text: str
    audio_offset_ms: int    # Время начала в миллисекундах
    duration_ms: int        # Длительность в миллисекундах
    
@dataclass
class TTSResult:
    audio_path: Path
    word_boundaries: List[WordBoundary]
    total_duration_ms: int

class TTSEngine:
    def __init__(
        self,
        language: str = "es-ES",
        voice: str = "es-ES-ElviraNeural",
        rate: str = "+0%",
        volume: str = "+0%"
    ):
        pass
        
    async def synthesize(
        self, 
        text: str, 
        output_path: Path
    ) -> TTSResult:
        """Синтезирует речь с захватом таймингов слов."""
```

**Интеграция Edge TTS**:
- Использует `edge_tts.Communicate` для синтеза
- Подписывается на события `WordBoundary` для данных о времени
- Сохраняет `audioOffset` (в единицах 100 наносекунд) и `duration` для каждого слова

**Интерполяция таймингов**:
Если для некоторых слов нет данных:
1. Рассчитать среднюю длительность слова из имеющихся данных
2. Распределить пропущенные слова пропорционально между известными границами
3. Записать предупреждение с процентом интерполированных слов

---

### 3. Сегментатор субтитров (`segmenter.py`)

**Назначение**: Разбиение потока слов на события субтитров (одна строка на событие).

```python
@dataclass
class SegmentationConfig:
    max_chars_per_line: int = 40      # Максимум символов на строку
    min_words_per_segment: int = 2    # Минимум слов до переноса
    max_words_per_segment: int = 8    # Максимум слов на сегмент

@dataclass
class SubtitleEvent:
    start_time_ms: int
    end_time_ms: int
    words: List[WordBoundary]

class SubtitleSegmenter:
    def __init__(self, config: SegmentationConfig = None):
        self.config = config or SegmentationConfig()
        
    def segment(
        self, 
        word_boundaries: List[WordBoundary]
    ) -> List[SubtitleEvent]:
        """Сегментирует слова в события для однострочного отображения."""
```

**Правила сегментации**:
1. Никогда не превышать `max_chars_per_line` символов на строку
2. Предпочитать разбиение у знаков препинания (запятая, точка)
3. Если нет пунктуации — разбивать на `max_words_per_segment`
4. Каждый сегмент начинается, когда заканчивается предыдущий (без наложения)

---

### 4. Генератор ASS (`ass_generator.py`)

**Назначение**: Создание ASS-файла с караоке-эффектами.

```python
@dataclass
class SubtitleStyle:
    font_name: str = "Arial"
    font_size: int = 48
    primary_color: str = "&H00FFFFFF"    # Белый (неподсвеченный)
    secondary_color: str = "&H0000FFFF"  # Жёлтый (подсветка/караоке)
    outline_color: str = "&H00000000"    # Чёрная обводка
    back_color: str = "&H80000000"       # Полупрозрачный фон
    outline_width: float = 2.0
    shadow_depth: float = 1.0
    alignment: int = 2                    # По центру снизу
    margin_v: int = 60                    # Отступ от низа
    margin_l: int = 40
    margin_r: int = 40

class ASSGenerator:
    def __init__(self, style: SubtitleStyle = None):
        self.style = style or SubtitleStyle()
        
    def generate(
        self,
        events: List[SubtitleEvent],
        output_path: Path,
        video_width: int = 1080,
        video_height: int = 1920
    ) -> Path:
        """Генерирует ASS-файл с караоке-тегами."""
```

**Формат ASS караоке**:
```
Dialogue: 0,0:00:00.00,0:00:02.50,Default,,0,0,0,,{\kf80}Hola {\kf60}mundo {\kf100}amigos
```

- `\kf` = эффект заливки (прогрессивная подсветка)
- Длительность в сотых долях секунды
- Пунктуация получает `{\kf0}` (нулевая длительность, без подсветки)

---

### 5. Караоке Рендерер (`renderer.py`)

**Назначение**: Сборка финального видео с аудио и прожжёнными субтитрами.

> [!NOTE]
> Хотя этот компонент в данный момент является частью модуля субтитров, он реализует общую логику обработки видео (кроп, зацикливание, слияние), которая в будущем может быть вынесена в общую утилиту `src/video/`.

```python
@dataclass
class RendererConfig:
    target_width: int = 1080
    target_height: int = 1920
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = 23                     # Качество (меньше = лучше)
    preset: str = "medium"

class KaraokeRenderer:
    def __init__(self, config: RendererConfig = None):
        self.config = config or RendererConfig()
        
    def render_video(
        self,
        background_video: Path,
        audio: Path,
        subtitles: Path,
        output: Path,
        target_duration_ms: int
    ) -> Path:
        """Собирает видео с аудио и прожжёнными субтитрами."""
```

**Пайплайн обработки видео**:
1. **Зондирование** фонового видео (длительность и размеры)
2. **Кроп** до 9:16, если aspect ratio отличается (центральный кроп)
3. **Зацикливание/Обрезка** под длительность аудио:
   - Если короче: зациклить (`-stream_loop -1`)
   - Если длиннее: обрезать
4. **Прожиг субтитров** через фильтр `subtitles` (libass)
5. **Микширование аудио** с видео
6. **Кодирование** в выходной файл

**Структура FFmpeg-команды**:
```bash
ffmpeg -stream_loop -1 -i bg.mp4 -i voice.mp3 \
  -vf "crop=ih*9/16:ih,scale=1080:1920,subtitles=subs.ass" \
  -c:v libx264 -c:a aac -shortest \
  -t {audio_duration} final.mp4
```

---

### 6. Менеджер хранения (`storage.py`)

**Назначение**: Управление хранением артефактов с хэшированием контента.

```python
class StorageManager:
    def __init__(self, base_dir: Path = Path("data/audio")):
        self.base_dir = base_dir
        
    def get_content_hash(self, text: str) -> str:
        """Генерирует SHA-256 хэш (первые 12 символов) нормализованного текста."""
        
    def get_artifact_dir(self, text: str) -> Path:
        """Получает или создаёт директорию для артефактов текста."""
        
    def save_metadata(
        self, 
        artifact_dir: Path, 
        config: dict,
        stats: dict
    ) -> Path:
        """Сохраняет метаданные генерации для воспроизводимости."""
```

**Структура директории**:
```
data/audio/
└── a1b2c3d4e5f6/          # Первые 12 символов SHA-256
    ├── voice.mp3          # Синтезированное аудио
    ├── word_boundaries.json
    ├── subs.ass
    └── metadata.json      # Конфигурация + статистика
```

---

### 7. Основной пайплайн (`pipeline.py`)

**Назначение**: Оркестрация полного процесса генерации.

```python
@dataclass
class KaraokeConfig:
    language: str = "es-ES"
    voice: str = "es-ES-ElviraNeural"
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    segmentation: SegmentationConfig = field(default_factory=SegmentationConfig)
    style: SubtitleStyle = field(default_factory=SubtitleStyle)
    renderer: RendererConfig = field(default_factory=RendererConfig)

@dataclass
class KaraokeResult:
    success: bool
    output_path: Optional[Path]
    artifact_dir: Path
    audio_duration_ms: int
    word_count: int
    segment_count: int
    interpolated_words_pct: float
    error: Optional[str] = None

class KaraokePipeline:
    def __init__(self, config: KaraokeConfig = None):
        self.config = config or KaraokeConfig()
        
    async def create(
        self,
        script_path: Path,
        background_video: Path,
        output_path: Path
    ) -> KaraokeResult:
        """Выполняет полный пайплайн: текст → TTS → ASS → видео."""
```

**Шаги пайплайна**:
1. Читать и нормализовать текст скрипта
2. Проверить/создать директорию артефактов по хэшу текста
3. Синтезировать TTS с таймингами (или переиспользовать кэш)
4. Сегментировать слова в события субтитров
5. Сгенерировать ASS-файл с караоке-тегами
6. Отрендерить финальное видео через KaraokeRenderer
7. Сохранить метаданные и вернуть результат

---

### 8. CLI (`__main__.py`)

```python
# python -m src.subtitles --script script.txt --bg bg.mp4 --output final.mp4

@app.command()
def create(
    script: Path = typer.Option(..., "--script", "-s", help="Путь к файлу с текстом"),
    bg: Path = typer.Option(..., "--bg", "-b", help="Путь к фоновому видео"),
    output: Path = typer.Option(None, "--output", "-o", help="Путь к выходному видео"),
    lang: str = typer.Option("es-ES", "--lang", "-l", help="Код языка TTS"),
    voice: str = typer.Option(None, "--voice", "-v", help="Имя голоса TTS"),
    style_config: Path = typer.Option(None, "--style-config", help="JSON конфигурация стилей"),
    debug: bool = typer.Option(False, "--debug", help="Сохранять промежуточные файлы")
):
    """Создаёт видео с TTS-аудио и караоке-субтитрами."""
```

---

## Принятые решения

### D1: Хэширование артефактов по контенту
**Решение**: Использовать SHA-256 хэш нормализованного текста для именования директорий.
**Обоснование**: 
- Включает кэширование: тот же текст = то же аудио (без повторного синтеза)
- Устойчив к коллизиям для практических целей
- 12 символов дают 48 бит уникальности

### D2: Формат ASS для субтитров
**Решение**: Использовать исключительно формат ASS (Advanced SubStation Alpha).
**Обоснование**:
- Нативная поддержка караоке-тегов (`\k`, `\kf`, `\ko`)
- Богатые возможности стилизации
- Отличная поддержка FFmpeg/libass
- Индустриальный стандарт для караоке-приложений

### D3: Edge TTS для синтеза речи
**Решение**: Использовать Edge TTS как основной TTS-движок.
**Обоснование**:
- Бесплатный уровень с высоким качеством
- Поддержка событий word-boundary через SSML
- Мультиязычная поддержка
- Не требует API-ключа

### D4: Центральный кроп для aspect ratio
**Решение**: Кропать фоновое видео до 9:16 по центру.
**Обоснование**:
- Сохраняет качество (без растяжения)
- Центральное кадрирование обычно захватывает важный контент
- Простое, предсказуемое поведение

### D5: Независимый модуль со специализированным рендерером
**Решение**: Создать как автономный модуль. Использовать `KaraokeRenderer` для сборки видео.
**Обоснование**:
- Название `KaraokeRenderer` чётко описывает его назначение внутри этого модуля.
- Общие операции с видео (зацикливание, кроп) инкапсулированы, но могут быть вынесены в `src/utils/` позже, если появится централизованная утилита.
- Позволяет избежать использования слишком общего названия "Composer".

---

## Риски / Компромиссы

| Риск | Смягчение |
|------|-----------|
| Изменения API Edge TTS | Абстрактный TTS-интерфейс; можно заменить реализацию |
| Отсутствие таймингов слов | Резервная интерполяция с логированием предупреждений |
| FFmpeg не установлен | Понятное сообщение об ошибке с инструкцией установки |
| Большие текстовые файлы | Разумные лимиты (напр., 5000 символов) с предупреждением |
| Не-UTF8 кодировка | Принудительное UTF-8 при чтении |

---

## Открытые вопросы

1. **Пресеты голосов**: Стоит ли включить готовые конфигурации (напр., `spanish_female`, `english_male`)?
2. **Индикация прогресса**: Показывать прогресс-бар в CLI для длинных генераций?
3. **Режим превью**: Генерировать превью субтитров без полного кодирования видео?

---

## Будущие расширения (вне скоупа)

- **Пакетный режим**: Обработка нескольких скриптов из директории
- **Интеграция с LLM**: Генерация скриптов из промптов
- **Микширование музыки**: Добавление фоновой музыки
- **Пресеты стилей**: Встроенные визуальные темы (neon, minimal, bold)
- **Авто-фоны**: Генерация видео из изображений через VideoCreator
