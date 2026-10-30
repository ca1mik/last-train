"""Build review navigation from actual render artifacts and installed skill metadata."""
import html
import json
import re
from pathlib import Path
from setup_game_skills import SPECS, ROOT, SKILLS

OUT = ROOT / 'release' / 'capability-audit'
OUT.mkdir(parents=True, exist_ok=True)
DOCS = ['GAME_DESIGN_DOCUMENT.md','NARRATIVE_BIBLE.md','ART_STYLE_GUIDE.md',
        'CHARACTER_BIBLE.md','LEVEL_DESIGN_GUIDE.md','ANIMATION_GUIDE.md','ASSET_REGISTRY.md']

index = '''# Skills и инструменты разработки игры

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
'''
for name, (description, display, short, body) in SPECS.items():
    index += f'| [{name}]({(SKILLS/name/"SKILL.md").as_posix()}) | {short} |\n'
index += '''
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
'''
(ROOT/'design/skills-and-capabilities.md').write_text(index, encoding='utf-8')

pose_prefix = 'final/poses' if (OUT/'final/poses/manifest.json').is_file() else 'poses'
poses = OUT/pose_prefix
manifest = json.loads((poses/'manifest.json').read_text(encoding='utf-8'))
options = ''.join(f'<option value="{i}">{html.escape(c["state"])} / sample {c["sample"]} / {c["heading_degrees"]}°</option>' for i,c in enumerate(manifest['cases']))
page = '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Последний рейс — визуальный аудит</title>
<link rel="icon" href="data:,"><style>body{margin:0;background:#172125;color:#e3e6e1;font:16px system-ui}main{max-width:1400px;margin:auto;padding:24px}h1{font-size:27px}p{line-height:1.55}.notice{border-left:4px solid #d2aa69;padding:12px 16px;background:#243035}select,button{padding:10px;font:inherit;background:#33444a;color:white;border:1px solid #789096;margin:5px}img{display:block;width:100%;height:auto;background:#414d50}figure{margin:20px 0}figcaption{padding:8px}a{color:#e1bf82}video{width:100%}</style>
<main><h1>Последний рейс — визуальный аудит</h1><p class="notice">Проверка среды и текущих ассетов. Художественное качество игры ещё не принято. Галерея — постановочные позы: корни в walk/run неподвижны; она не доказывает качество движения по полу.</p>
<label for="pose">Поза и направление</label><select id="pose">OPTIONS</select><button id="next">Следующий кадр</button><button id="reset">Начальный кадр</button>
<figure><img id="pose-image" alt="Реальные персонажи Godot: Артём и три варианта противника"><figcaption id="pose-caption"></figcaption></figure>
<h2>Сцена в игровом ракурсе</h2><img src="scene/scene-25d.png" alt="Реальный игровой рендер станции">
<h2>Нейтральный Blender-рендер исходной модели</h2><img src="blender/worker-rest-000.png" alt="Исходный Артём в Blender" style="max-width:640px"><p>Старый хват здесь оставлен как доказательство дефекта: предмет у запястья, открытая кисть. Версия исправления проверяется отдельно.</p>
<h2>Исправленный хват: 0.35</h2><p>Рукоять перенесена к ладони, поза пальцев запечена, размер кисти скорректирован. Угловатая топология манжеты/кисти ещё требует доводки.</p><img src="grip-idle-8views.jpg" alt="Исправленный хват в восьми ракурсах покоя"><img src="grip-attack-8views.jpg" alt="Исправленный хват в восьми ракурсах удара">
<h2>Движение</h2><p><a href="motion.mp4">Новая запись движения</a>. Изолированная автоматическая сцена, не человеческое прохождение.</p>
<h2>Открытые замечания</h2><ul><li>Хват и деформация кисти требуют отдельной проверки крупным планом.</li><li>Ноги Артёма в исходной модели выглядят открытыми ниже коротких штанин, что расходится с описанием рабочих брюк.</li><li>Базовый бег, уклонение и падение ещё требуют доводки.</li><li>Серые лужи, регулярность окружения и низкая читаемость тёмных фигур.</li><li>Полноценной эвакуации и длительного уровня пока нет.</li></ul>
<p><a href="../../design/skills-and-capabilities.md">Инструменты и 15 skills</a> · <a href="../../CHARACTER_BIBLE.md">Спецификация персонажей</a></p></main>
<script>const cases=CASES;const select=document.querySelector('#pose');function show(){let c=cases[Number(select.value)];document.querySelector('#pose-image').src='poses/'+c.file;document.querySelector('#pose-caption').textContent=c.state+' · '+c.heading_degrees+'° · '+c.width+'×'+c.height+' · fixture';}select.onchange=show;document.querySelector('#next').onclick=()=>{select.value=(Number(select.value)+1)%cases.length;show()};document.querySelector('#reset').onclick=()=>{select.value=0;show()};show();</script></html>'''
page=page.replace('OPTIONS', options).replace('CASES', json.dumps(manifest['cases']))
page=page.replace(".src='poses/'", ".src='"+pose_prefix+"/'")
if (OUT/'final/scene/scene-25d.png').is_file():
    page=page.replace('src="scene/scene-25d.png"','src="final/scene/scene-25d.png"')
(OUT/'review.html').write_text(page, encoding='utf-8')

source=(ROOT/'game25d/scripts/main.gd').read_text(encoding='utf-8')
trace={'mission_assignments':sorted(set(re.findall(r'mission\s*(?:=|:=)\s*(\d+)',source))),
       'visible_completion_lines':[line.strip() for line in source.splitlines() if 'Михаил найден' in line],
       'limits':'Static event inventory only. Full scenario branches, save/load and human playtest not verified.',
       'docs_present':{name:(ROOT/name).is_file() for name in DOCS}}
(OUT/'scenario-inventory.json').write_text(json.dumps(trace,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'skills_index':15, 'pose_cases':len(manifest['cases']), 'documents':trace['docs_present']},ensure_ascii=False))
