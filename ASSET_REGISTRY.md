# Реестр ассетов и происхождения

0.44, 18.10.2026: `game25d/scripts/environment_kit.gd` — собственный процедурный
набор настоящих 3D-мешей: деревья, кусты, трава MultiMesh, ограды, будка,
машина, ёмкость, окна и детали больницы. `foliage.gdshader` и
`path_ground.gdshader` — собственные ветер/материалы. Внешние ассеты не
загружались. Персонажные GLB не менялись; новый набор не означает их приёмки.
Происхождение/границы: game25d/PROVENANCE.md, design/progress-v044.md.

Хеши текущих GLB 0.38: `release/motion-v038/verification.json`.
Исходная инвентаризация до ретаргета сохранена в
`release/capability-audit/asset-inventory.json` как историческое доказательство.
Источник лицензий: `game25d/LICENSES.txt`, `PROVENANCE.md`, оригинальные файлы
паков. Запись в реестре не означает финальную художественную приёмку.

| Ресурс | Реальный путь | Происхождение / статус |
|---|---|---|
| Артём | `game25d/assets/characters/motion-v38/worker.glb` | Прежний Man/одежда + ретаргет UAL; baseline worker.glb сохранён |
| Путевые | `game25d/assets/characters/motion-v38/wraith.glb` | Прежний Man/капюшон + ретаргет UAL; три масштаба, исходный wraith.glb сохранён |
| Михаил | `game25d/assets/characters/patient.glb` | Базовая адаптация Man, временный образ |
| Проп-модуль | `game25d/assets/props/beveled-box.glb` | Собственная Blender-геометрия; не готовый персонаж |
| Выходной привод / звонок / дверь 0.39 | `game25d/scripts/chapter1_exit.gd` | Собственная процедурная геометрия для blockout; движется в реальном 3D, финальный environment art и контакт рук не приняты |
| Транспортные носилки | `game25d/scripts/expedition.gd`, build_cart | Собственная геометрия Godot и CharacterBody3D, без отдельного фиктивного GLB |
| Контактный IK | `game25d/scripts/carry_ik.gd` | Собственный двухкостный solver, существующий Man-скелет |
| Пол новой вылазки | `game25d/shaders/expedition_floor.gdshader` | Собственный spatial shader, метрические швы плитки |
| Исходный Man | `source_25d/quaternius/Man-CC0.glb` | https://poly.pizza/m/HMnuH5geEG, 11 исходных клипов |
| UAL Standard | `source_25d/ual-standard` | https://quaternius.itch.io/universal-animation-library, 43 CC0-клипа; часть перенесена в 0.38, не все приняты |
| Base Characters Standard | `source_25d/base-characters-standard` | https://quaternius.itch.io/universal-base-characters, только Superhero Male/Female в бесплатном паке; не выбраны |
| Kenney Survivors | `source_25d/kenney-survivors` | Сравнение, не используется в сборке |
| Kenney Impact Sounds | `game25d/assets/audio/*.ogg` | CC0, оригинал лицензии `Kenney-CC0.txt` |
| Старые 2D-люди | `assets/characters` | Imagegen и прежняя обработка; `assets/PROVENANCE.md`, prompts в design; legacy |
| Референсы игр | `design/references/*.jpg` | Рекламные изображения для анализа; исключены из экспорта |

## Известные проблемы источников

- Некоторые старые загрузки вернули HTML вместо моделей; они в
  `source_25d/rejected-downloads`, не использовать как GLB или лицензии.
- В glTF Base Characters ссылки на `T_Hair_1_Normal_png.png` и
  `T_Eye_Normal_png.png` не совпадают с реальными именами. Исправление URI нужно
  делать в рабочей копии с сохранением оригинала; пак ещё не принят.
- Доступность CC0-пака не является утверждением подходящей анатомии/стиля.

## Новая запись

0.46-dev: собственные Godot-меши в `scripts/hospital_reception.gd`: вагонные
сиденья/ввод/вещи/настенные светильники, койки/одеяла/шкаф/ширма и сумка.
Существующий patient.glb поставлен как Михаил в вагоне, не как четыре новых
утверждённых персонажа. Новых сторонних ассетов нет; финальный интерьер и
постановка/внешность остальных людей не приняты. GPU-материалы — reception-v046.

0.37: больничный blockout и механизм стрелки — собственная геометрия Godot
в `scripts/hospital.gd`, без новых персонажей/покупных моделей. Используются
те же worker/wraith GLB и floor shader; новая внешность не утверждалась.
Простой диск с рукояткой и стрелочные рельсы — проверка логики/читаемости,
не финальный производственный арт механизма. Финальные позы совместной
работы и контакт рук с лебёдкой ещё не созданы.

ID, версия, source URL/путь, автор/лицензия, hash, формат, размеры/единицы,
скелет/bind pose, материалы/текстуры, клипы, варианты/зависимости, master/reference,
approval status, используется ли и где, render evidence, дефекты.
Сгенерированные проектные изображения копировать в workspace, хранить prompt,
references и выбранную версию; не ссылаться только на временную папку генератора.
