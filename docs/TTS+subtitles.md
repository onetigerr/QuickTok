Это финальный flow-спек для модуля: вход только **испанский текст + вертикальное видео**, выход — видео с TTS-аудио и прожжёнными субтитрами в одну строку с “заливкой” по словам (karaoke). Подсветку строим строго по word-boundary таймингам, где есть `audioOffset` и `duration`. [learn.microsoft](https://learn.microsoft.com/en-us/javascript/api/microsoft-cognitiveservices-speech-sdk/speechsynthesiswordboundaryeventargs?view=azure-node-latest)

## Вход и выход
Входные файлы: `script_es.txt` (текст) и `bg.mp4` (вертикальный фон 9:16).  
Выходные файлы: `voice.*` (аудио), `subs.ass` (субтитры с подсветкой), `final.mp4` (финальный ролик с прожжёнными субтитрами). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/103935153/24686f7f-ab9a-482e-961c-bc4772fed78b/image.jpg)

## Нормализация текста
Приводите текст к стабильному виду до TTS: пробелы, переносы строк, кавычки/тире, удаление “ломающих” символов, и фиксируете правило для чисел/аббревиатур (иначе TTS может дать неожиданные паузы и произношение).  
Одновременно задаёте правило токенизации для субтитров: что считается “словом”, а что — пунктуацией (пунктуацию вы решили **не подсвечивать**).

## Синтез речи и тайминги
Синтезируете речь Edge TTS из нормализованного текста и сохраняете аудио `voice.*`.  
Во время синтеза (или сразу после) сохраняете word-boundary события по словам как минимум с `audioOffset` (старт) и `duration` (длительность) — это и есть источник истины для подсветки. [learn.microsoft](https://learn.microsoft.com/en-us/javascript/api/microsoft-cognitiveservices-speech-sdk/speechsynthesiswordboundaryeventargs?view=azure-node-latest)

## Сегментация под одну строку
Из потока слов с таймингами формируете субтитр-ивенты так, чтобы на экране всегда была **одна строка** (двух строк быть не должно).  
Правило разбиения: если фраза не помещается, вы не переносите её на 2 строки, а создаёте следующий ивент (то есть показываете текст последовательно “порциями”).

## Генерация ASS с “заливкой”
Формируете `subs.ass` в формате ASS, потому что он поддерживает karaoke-теги для прогрессивной заливки по времени (включая варианты `\K`/`\kf`).   
Каждый субтитр-ивент — это одна строка текста, где перед каждым словом стоит karaoke-тег с длительностью слова (длительность берёте из `duration`, приведённой к сотым долям секунды, как требуется в ASS karaoke). [learn.microsoft](https://learn.microsoft.com/en-us/javascript/api/microsoft-cognitiveservices-speech-sdk/speechsynthesiswordboundaryeventargs?view=azure-node-latest)
Пунктуацию делаете отдельными токенами без заливки (например, нулевая длительность или отдельное отображение без karaoke-эффекта), чтобы запятые/точки не “прокрашивались”. 

## Политика длительности (аудио vs видео)
Длину заранее знать не нужно: сначала синтезируете аудио, и его длительность становится целевой длительностью ролика.  
Дальше приводите `bg.mp4` к этой длительности: если фон длиннее — обрезаете до длины аудио; если короче — зацикливаете фон до нужной длины (или повторяете/замораживаете последний кадр — это тоже допустимая политика, если нужен более “спокойный” визуал).

## Финальная сборка и прожиг
Собираете `final.mp4`: подставляете `voice.*` как аудиодорожку и прожигаете `subs.ass` прямо в картинку видео (hard/burn-in subtitles) через FFmpeg/libass. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/103935153/24686f7f-ab9a-482e-961c-bc4772fed78b/image.jpg)
Именно “burn-in” нужен, чтобы подсветка и субтитры гарантированно отображались везде как часть изображения, а не как отдельная дорожка. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/103935153/24686f7f-ab9a-482e-961c-bc4772fed78b/image.jpg)

## Как оформить модуль (контракт)
Модуль принимает `script_es.txt`, `bg.mp4`, Путь вывода. Возвращает true-false, сохраняет `final.mp4` плюс (опционально) артефакты для отладки: `voice.*`, `word_boundaries.json`, `subs.ass`.  
На уровне логирования держите ключевые метрики: длительность аудио, длительность видео до/после приведения, число слов, число субтитр-ивентов, и процент слов без тайминга (если вдруг TTS вернул неполные события). [learn.microsoft](https://learn.microsoft.com/en-us/javascript/api/microsoft-cognitiveservices-speech-sdk/speechsynthesiswordboundaryeventargs?view=azure-node-latest)