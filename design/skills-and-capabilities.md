# Skills и инструменты разработки игры

Срез: 17 октября 2026. Установлены 15 локальных специализированных skills и
два официальных браузерных skill. Это инструкции и рабочие процедуры, а не
обученные модели или автоматически работающая команда специалистов.

## Реальные инструменты

| Capability | Проверенный путь / статус | Область применения |
|---|---|---|
| imagegen | `.codex/skills/.system/imagegen`, встроенный `image_gen` доступен | Концепты, референсы, растровые ассеты; генерации в рамках этой настройки не было |
| skill-creator | `.codex/skills/.system/skill-creator` | Созданы SKILL.md и agents/openai.yaml, выполнен quick_validate |
| 2d-games | `.codex/skills/2d-games` | Общие основы; не заменяет специальный пайплайн |
| Blender 5.1.1 / bpy | `C:/Program Files/Blender Foundation/Blender 5.1/blender.exe` | Нативные меши, skin/rig, материалы, камеры, свет и рендер |
| Godot 4.7.2 | `tools/vendor/godot-4.7.2/` | Основной движок игры, реальный Forward+ и захват GPU-кадров |
| Playwright 1.64.1 | `tools/visual-qa/node_modules/playwright` | Браузерные отчёты и web/Electron, не управление нативным окном Godot |
| @playwright/cli 0.1.22 | `tools/visual-qa/node_modules/.bin/playwright-cli.cmd` | CLI автоматизации; Windows-адаптер `tools/visual-qa/playwright_cli.ps1` |
| playwright-interactive | `.codex/skills/playwright-interactive` | Постоянная сессия через доступный node_repl; проверен createRequire |
| Chromium | Playwright browser v1248, Chrome for Testing 156.0.8078.4 | Установлен официальным `playwright install chromium` |
| Python 3.12.10 / Node 24.14.0 / FFmpeg | Системные команды | Скрипты ресурсов, браузерный QA, видео |
| MCP Blender/Godot/Playwright | Не обнаружены среди доступных tools; поиск плагинов вернул пустой список | Не объявлены подключёнными; прямые CLI/API уже работают |
| Three.js / React Three Fiber | Не установлены в проект | Не соответствуют текущему нативному стеку; перенос не нужен |

Зависимости npm закреплены точными версиями и package-lock.json в tools/visual-qa.
Установка выполнена с --ignore-scripts; браузер загружен отдельной официальной
командой. Секреты и внешние серверы MCP для этого не требуются.

## Специализированные skills

Для каждого строка ниже содержит путь. Триггеры — в YAML description;
необходимые инструменты — Tools; процедура — Procedure; критерии — Acceptance.
Копии исходников хранятся в tools/skill_sources; установщик — tools/setup_game_skills.py.
Новые skills появятся в автоматическом каталоге следующего хода/сессии; в этом
ходе файлы прочитаны и процедуры применены напрямую.

| Skill / файл | Назначение |
|---|---|
| [character-design](C:/Users/koall/.codex/skills/character-design/SKILL.md) | Character proportions and reference specifications |
| [character-consistency](C:/Users/koall/.codex/skills/character-consistency/SKILL.md) | Preserve identity across views and animation frames |
| [2d-sprite-pipeline](C:/Users/koall/.codex/skills/2d-sprite-pipeline/SKILL.md) | Sprites, pivots, atlases and frame sequence checks |
| [2-5d-character-pipeline](C:/Users/koall/.codex/skills/2-5d-character-pipeline/SKILL.md) | Camera, depth, scale and character scene integration |
| [character-rigging-animation](C:/Users/koall/.codex/skills/character-rigging-animation/SKILL.md) | Skeletons, skinning, retargeting and contact controls |
| [character-animation](C:/Users/koall/.codex/skills/character-animation/SKILL.md) | Readable motion, transitions and secondary animation |
| [level-design](C:/Users/koall/.codex/skills/level-design/SKILL.md) | Playable routes, encounter pacing and traversal checks |
| [environment-design](C:/Users/koall/.codex/skills/environment-design/SKILL.md) | Cohesive spaces, materials, lighting and readable depth |
| [narrative-design](C:/Users/koall/.codex/skills/narrative-design/SKILL.md) | Character arcs and story delivered through player actions |
| [cinematic-direction](C:/Users/koall/.codex/skills/cinematic-direction/SKILL.md) | Shots, gestures, sound cues and gameplay handoffs |
| [gameplay-design](C:/Users/koall/.codex/skills/gameplay-design/SKILL.md) | Mechanics, world states, combat and quest integration |
| [game-feel](C:/Users/koall/.codex/skills/game-feel/SKILL.md) | Responsive controls, stable motion and readable feedback |
| [visual-qa](C:/Users/koall/.codex/skills/visual-qa/SKILL.md) | Real render evidence, animation review and visual regressions |
| [narrative-qa](C:/Users/koall/.codex/skills/narrative-qa/SKILL.md) | Canon, event prerequisites and quest branch verification |
| [art-direction](C:/Users/koall/.codex/skills/art-direction/SKILL.md) | Shared style bible and cross-asset visual coherence |

## Совместный процесс

1. art-direction + gameplay-design + narrative-design: установить факты, стиль,
   игровой конфликт и версии спецификаций в семи корневых документах.
2. character-design + character-consistency: мастер-образ, инварианты и ракурсы;
   новые детали внешности отделить от согласованного. Не принимать pack автоматически.
3. level-design: route graph и blockout, обычный проход и коллизии до декораций.
4. character-rigging-animation + character-animation: bind pose, хват/контакты,
   каденс, состояния и временные переходы; 2d-sprite-pipeline — только для 2D-экспорта.
5. 2-5d-character-pipeline + environment-design: единые камера, масштаб, глубина,
   материалы, свет и перекрытия. cinematic-direction — постановка конкретного beat.
6. game-feel: управление/обратная связь по воспроизводимой проблеме.
7. visual-qa + narrative-qa: реальные кадры и движение, взаимодействия, события,
   ветки и регрессии. Исправление → повтор того же случая → честный статус.

## Малые применения на существующем проекте

| Группа skills | Применение и реальный результат |
|---|---|
| character-design, character-consistency, art-direction | Инвентаризация трёх GLB, baseline Артёма и NPC, восемь направлений, нейтральный и игровой свет. Финальный образ не принят |
| character-rigging-animation, character-animation, game-feel | Аудит старого хвата выявил инструмент у запястья. Отдельная версия правит хват; motion требует видео и повторной проверки |
| 2d-sprite-pipeline | Метаданные существующего 2D PNG и alpha проверяются helper; новый атлас и анимация не создавались |
| 2-5d-character-pipeline, environment-design | Реальная сцена Forward+, размеры кадров, occlusion/camera в regression fixtures; серые лужи и темнота остаются замечаниями |
| level-design, gameplay-design | Сверены реальные mission 0→1→2 и 25 игровых проверок. Полная эвакуация/длинный уровень отсутствуют |
| narrative-design, narrative-qa | Сверены канон, возрастная хронология, радиоприсутствие Нины и ограничение новой сцены. Остальные ветки не заявлены проверенными |
| cinematic-direction | Проверка текущих radio-beats: это текст на экране, не поставленная кат-сцена; озвучка/lip-sync не подтверждены |
| visual-qa | Новый нативный GPU-capture, Blender-рендер и браузерный отчёт; разделены корректность захвата и качество арта |

Это ограниченная практическая проверка процедур, не полная квалификация каждого
skill на всех игровых жанрах и не независимая человеческая приёмка.

## Повторяемые команды

```powershell
python tools/setup_game_skills.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/run_capability_native_qa.ps1
python tools/build_game_review.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/visual-qa/playwright_cli.ps1 --help
```

Native QA создаёт диагностические кадры, запускает сцену и 25 проверок;
это не прохождение человеком. Перед следующей арт-правкой записывать новый
output/version, чтобы не выдавать старые кадры за проверку изменённого ассета.
Пример постоянной браузерной сессии — tools/visual-qa/interactive-bootstrap.cjs.
Прямой import('playwright') в этом node_repl дал ошибку загрузчика default export;
createRequire из node:module проверен запуском Chromium и кликом.

## Официальные источники

- Skills: https://github.com/openai/skills/tree/main/skills/.curated/playwright
  и https://github.com/openai/skills/tree/main/skills/.curated/playwright-interactive
- Playwright: https://playwright.dev/docs/intro и https://playwright.dev/docs/browsers
- CLI: https://github.com/microsoft/playwright-cli
- bpy: https://github.com/blender/blender/blob/main/doc/python_api/rst/info_quickstart.rst
  и https://developer.blender.org/docs/handbook/building_blender/python_module/
- Godot: https://docs.godotengine.org/en/stable/tutorials/animation/animation_tree.html
  и https://docs.godotengine.org/en/stable/classes/class_camera3d.html

Основной сайт docs.blender.org при проверке через web-tool вернул ошибку доступа;
существование API сверено с официальным репозиторием Blender и реальным bpy 5.1.1.
Отдельный pip-пакет bpy не установлен: используется Python внутри Blender.
