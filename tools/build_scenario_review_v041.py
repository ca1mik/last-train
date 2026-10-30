"""Build a standalone planning document and actor reading sheet, not game maps."""
import csv,json,html,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
layout=json.loads((ROOT/'design/review/chapter1-layout-v041.json').read_text(encoding='utf-8'))
with (ROOT/'design/voice/chapter1-dialogue-v041.tsv').open(encoding='utf-8',newline='') as source:
    lines=list(csv.DictReader(source,delimiter='\t'))
assert len(lines)==len({row['line_id'] for row in lines})
assert all(row['audio_status']=='not_recorded' and row['text'].strip() for row in lines)
scenes=list(dict.fromkeys(row['scene_id'] for row in lines))
for level in layout['levels']:
    nodes={r['id'] for r in level['rooms']}
    assert len(nodes)==len(level['rooms'])
    assert all(a in nodes and b in nodes for a,b,_ in level['links'])
    assert all(s in scenes for s in level['scenes'])
    # The written topology must connect every displayed room to its entry.
    reached={level['rooms'][0]['id']}
    while True:
        expanded=reached|{b for a,b,_ in level['links'] if a in reached}|{a for a,b,_ in level['links'] if b in reached}
        if expanded==reached:break
        reached=expanded
    assert reached==nodes,(level['id'],nodes-reached)
scene_titles={
    'P01_DOOR':'Пролог · Дверь', 'P01_TEA':'Пролог · Два стакана',
    'P01_JOB':'Пролог · Обследование', 'P01_FAMILY':'Пролог · Не через меня',
    'P02_BRAKE':'Пролог · Проверка тормозов', 'P02_HINT':'Подсказка · Проверка',
    'P03_LOOP':'Пролог · Один и тот же столб', 'P04_LAND':'Пролог · Безопасный сход',
    'C1_MEET':'Фонарь Лиды', 'C1_ENTRY':'Поперечная дверь', 'C1_TICKET':'Билет на сегодня',
    'C1_SOUND':'Реле за стеклом', 'C1_BELL':'Другой коридор',
    'C1_SOUND_HINT':'Подсказки · Реакция на звук', 'C1_SHORTCUT':'Низкая калитка',
    'C1_DUTY':'Дежурный слышит', 'C1_METHOD':'Два способа', 'C1_MANUAL':'Стопор',
    'C1_POWER':'Генератор и релейная', 'C1_OPEN':'Аптека открыта',
    'C1_NOTE':'Записка дежурного', 'C1_METHOD_HINT':'Подсказки · Привод',
    'C1_PATIENT':'Михаил', 'C1_PATH':'Подготовить выход', 'C1_REQUEST':'Адрес мастерской',
    'C1_LIFT':'Не отпускайте', 'C1_RETURN':'Изменившийся путь', 'C1_BOLT':'Служебная калитка',
    'C1_BOARD':'Михаил в вагоне', 'C1_EXIT':'Выходной двор', 'C1_DOOR':'Открыть самому',
    'C1_TEA':'Вагон · Платформу помню', 'C1_WHY':'Вагон · Почему позвала',
    'C1_RECORD':'Вагон · Короткий фрагмент', 'C1_ROUTE':'Вагон · Следующая остановка',
    'C1_LATER':'Вагон · Поговорим позже', 'C1_BAG':'Вагон · Старая сумка',
    'C1_REQUEST_END':'Вагон · Адрес записали', 'C1_EXIT_WAGON':'Вернуться к пульту',
    'C1_DEPART':'Отправление'
}
assert set(scene_titles)==set(scenes)
data={'layout':layout,'lines':lines,'scene_titles':scene_titles,'meta':{'lines':len(lines),'scenes':len(scenes),'words':sum(len(r['text'].split()) for r in lines)}}

TEMPLATE=r'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:,"><title>Последний рейс — первая глава / сценарный план 0.41</title>
<style>
:root{color-scheme:dark;--bg:#101c21;--panel:#17262d;--edge:#32464d;--text:#e1e6df;--dim:#a9bbb9;--amber:#e8bb71;--mint:#8bc4b0;--blue:#7eafcf;--red:#d58e84}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 'Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--text)}
header{padding:28px 36px 22px;border-bottom:1px solid var(--edge);display:flex;gap:30px;align-items:end;justify-content:space-between}
.eyebrow{font-size:11px;font-weight:650;letter-spacing:2px;color:var(--mint);text-transform:uppercase}h1{font:400 34px/1.2 Georgia,serif;margin:8px 0}header p{margin:6px 0 0;color:var(--dim);max-width:790px}.badge{color:var(--amber);border:1px solid #6b6049;padding:7px 12px;border-radius:5px;white-space:nowrap;font-size:12px}
.workspace{display:grid;grid-template-columns:240px minmax(450px,1fr) 330px;min-height:640px}.levels{padding:26px 20px;border-right:1px solid var(--edge)}.levels h2{font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:var(--dim);margin:0 0 18px}
button{font:inherit;cursor:pointer;color:inherit}button:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid var(--amber);outline-offset:3px}.level{display:block;width:100%;text-align:left;border:1px solid transparent;background:transparent;border-radius:6px;padding:12px 11px;margin:0 0 9px}.level[aria-selected=true]{border-color:#6d6046;background:#302f28}.level:hover{background:#23343a}.level .n{font-size:12px;color:var(--amber);letter-spacing:1px}.level strong{display:block;font-size:15px;font-weight:550;margin:3px 0}.level small{color:var(--dim);font-size:11px}.nav-note{font-size:12px;color:var(--dim);margin-top:24px;border-top:1px solid var(--edge);padding-top:17px}
.map-section{padding:25px 27px 18px;min-width:0}.map-head{display:flex;align-items:baseline;justify-content:space-between;gap:10px}h2{margin:0;font-size:23px;font-weight:500}.target{color:var(--amber);font-size:12px;white-space:nowrap}.verb{margin:7px 0 15px;color:var(--dim);font-size:14px}.toolbar{display:flex;gap:20px;align-items:center;flex-wrap:wrap;font-size:12px;color:var(--dim)}.toolbar label{display:flex;gap:7px;align-items:center;cursor:pointer}input{accent-color:var(--mint)}
.map-box{margin-top:17px;border:1px solid var(--edge);border-radius:7px;background:#132229;overflow:hidden}svg{display:block;width:100%;height:auto;min-height:300px}.room{cursor:pointer;outline:none}.room rect{stroke:#5a7479;stroke-width:1.4;fill:#21373d;transition:fill .15s}.room:hover rect,.room:focus-visible rect{fill:#2d4950;stroke:var(--amber);stroke-width:2}.room.selected rect{fill:#3c3d30;stroke:var(--amber);stroke-width:2.5}.room text{pointer-events:none;fill:var(--text);font:16px 'Segoe UI',sans-serif}.room .kind{font-size:10px;letter-spacing:1px;fill:var(--dim)}.room[data-type=secret] rect{stroke:var(--mint);stroke-dasharray:5 4}.room[data-type=safe] rect{fill:#234039;stroke:#6f9d89}.room[data-type=blocked] rect{fill:#362c2c;stroke:var(--red)}.room[data-type=goal] rect{stroke:var(--amber)}
.legend{display:flex;gap:15px;flex-wrap:wrap;font-size:11px;color:var(--dim);padding:11px 14px;border-top:1px solid var(--edge)}.legend i{display:inline-block;width:23px;height:2px;margin-right:6px;vertical-align:middle}.scope{font-size:11px;color:var(--dim);margin:11px 0 0}.detail{padding:27px 24px;border-left:1px solid var(--edge);background:#142229}.detail h3{font-weight:500;font-size:19px;margin:8px 0 10px}.detail p{font-size:13px;color:var(--dim);margin:0 0 15px}.detail dl{margin:0}.detail dt{font-size:11px;letter-spacing:.8px;color:var(--mint);text-transform:uppercase;margin:17px 0 5px}.detail dd{margin:0;font-size:13px;color:var(--text)}.reset{margin-top:18px;border:1px solid var(--edge);background:transparent;border-radius:4px;padding:7px 10px;font-size:12px;color:var(--dim)}
.reading{padding:26px 36px 38px;border-top:1px solid var(--edge);background:#132128}.reading-head{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}.reading h2{font-size:22px}.reading label{font-size:12px;color:var(--dim)}select{margin-left:8px;max-width:390px;background:#1b3037;color:var(--text);border:1px solid #58717a;border-radius:4px;padding:8px;font:inherit}.reading-note{color:var(--dim);font-size:12px}.dialogues{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 24px;max-width:1420px;margin-top:18px}.line{border-left:2px solid #456469;background:#192d33;padding:11px 16px;min-width:0}.line header{display:flex;align-items:center;gap:12px;border:0;margin:0;padding:0;justify-content:space-between;font-size:11px;color:var(--mint)}.line .cond{color:var(--amber);font-size:10px}.line blockquote{margin:6px 0;font-size:17px;line-height:1.45}.line p{font-size:11px;color:var(--dim);margin:3px 0}.line code{font-size:10px;color:#8ba6aa;overflow-wrap:anywhere}footer{padding:18px 36px;color:var(--dim);font-size:11px;border-top:1px solid var(--edge)}a{color:var(--mint)}
@media(min-width:1800px){.workspace{grid-template-columns:270px minmax(450px,1fr) 380px}.detail dd,.detail p{font-size:14px}}
@media(max-width:1150px){.workspace{grid-template-columns:210px minmax(0,1fr)}.detail{grid-column:1/-1;border-top:1px solid var(--edge);border-left:0;display:grid;grid-template-columns:1fr 2fr;gap:15px}.detail dl{display:grid;grid-template-columns:1fr 1fr;gap:0 24px}.detail dt{grid-column:1/-1}.map-section{padding:22px 20px}header{padding:22px}.reading{padding:24px 22px}.badge{font-size:11px}}
@media(max-width:720px){.map-box{overflow-x:auto}svg{min-width:760px;min-height:437px}header{display:block}h1{font-size:27px}.badge{display:inline-block;margin-top:15px}.workspace{display:block}.levels{padding:16px;border-right:0;border-bottom:1px solid var(--edge)}.levels h2,.nav-note{display:none}.level{display:inline-block;width:calc(50% - 5px);vertical-align:top}.map-head{display:block}h2{font-size:21px}.target{display:block;margin:5px 0}.detail{display:block;padding:22px}.detail dl{display:block}.dialogues{grid-template-columns:1fr}.reading-head{display:block}.reading-head label{display:block;margin-top:15px}select{display:block;margin:6px 0 0;max-width:100%;width:100%}footer{padding:18px 22px}}
@media print{body{background:white;color:#111}header,.levels,.toolbar,.badge,footer{display:none}.workspace{display:block}.detail,.map-box,.reading,.line{background:white;color:#111}.room text{fill:#111}.room rect{fill:#eee!important}.scope,.detail p,.reading-note,.line p{color:#333}.dialogues{display:block}.line{break-inside:avoid;margin:8px 0}}
</style></head><body>
<header><div><div class="eyebrow">Последний рейс / сценарная мастерская</div><h1>До следующей станции</h1><p>Пять уровней первой главы: путь к человеку, изменившееся возвращение и личная помощь у двери.</p></div><div class="badge">0.41 · проектирование</div></header>
<main><div class="workspace"><nav class="levels" aria-label="Уровни первой главы"><h2>Пять уровней</h2><div id="level-list" role="tablist" aria-label="Выбрать уровень"></div><p class="nav-note">Пролог и разговоры в вагоне доступны в читке ниже. 42 минуты для пяти уровней — целевой бюджет, не измеренное прохождение.</p></nav>
<section class="map-section" aria-label="Схема маршрутов"><div class="map-head"><h2 id="map-title"></h2><span class="target" id="target"></span></div><p class="verb" id="verb"></p><div class="toolbar"><label><input type="checkbox" id="show-return" checked>Обратный путь</label><label><input type="checkbox" id="show-secrets" checked>Секреты</label><span>Выберите пространство на схеме</span></div><div class="map-box"><svg id="map" viewBox="0 0 1010 580" role="group" aria-label="Топологическая схема"></svg><div class="legend"><span><i style="background:#e8bb71"></i>Основной путь</span><span><i style="background:#7eafcf"></i>Альтернатива</span><span><i style="background:#a8bbb4"></i>Возвращение</span><span><i style="background:#8bc4b0"></i>Секрет</span><span><i style="background:#d58e84"></i>Закрытый путь</span></div></div><p class="scope">Связи пространств, без метрического масштаба. Проходимость, ширины и длительность проверяются позже в blockout.</p></section>
<aside class="detail" aria-live="polite"><div><div class="eyebrow" id="detail-kind">Задача уровня</div><h3 id="detail-title"></h3><p id="detail-text"></p><button class="reset" id="reset-detail">Обзор уровня</button></div><dl><dt>Что меняется</dt><dd id="change"></dd><dt>Выбор игрока</dt><dd id="choice"></dd><dt>На что обратить внимание</dt><dd id="risk"></dd><dt>Контрольная точка</dt><dd id="checkpoint"></dd></dl></aside></div>
<section class="reading" aria-label="Читка сценария"><div class="reading-head"><div><div class="eyebrow">Актёрский текст</div><h2>Реплики и обстоятельства</h2></div><label>Сцена<select id="scene-select" aria-label="Сцена для читки"></select></label></div><p class="reading-note" id="reading-note"></p><div class="dialogues" id="dialogues"></div></section></main>
<footer>Сценарная стадия. Игра остаётся 0.39; новые карты не добавлены. Все строки ожидают живой актёрской записи. <a href="../chapter1-production-v041.md">Постановка и контракт событий</a> · <a href="../voice/chapter1-reading-v041.md">Полная читка</a></footer>
<script id="data" type="application/json">__DATA__</script>
<script>
'use strict';const D=JSON.parse(document.getElementById('data').textContent);let selected=0,roomId=null;const E=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const kinds={safe:'Защищённая точка',story:'Сюжет и наблюдение',combat:'Угроза / выбор',route:'Вариант маршрута',puzzle:'Предметная задача',goal:'Изменение мира',secret:'Необязательное открытие',blocked:'Изменившийся путь'};const colors={main:'#e8bb71',alternate:'#7eafcf',return:'#a8bbb4',secret:'#8bc4b0',blocked:'#d58e84'};
function splitLabel(label,width){if(label.length<Math.floor((width-26)/8))return [label];const words=label.split(' ');let a='',b='';for(const w of words){if(a.length<Math.ceil(label.length/2))a+=(a?' ':'')+w;else b+=(b?' ':'')+w}return [a,b].filter(Boolean)}
function boundary(r,other){const cx=r.x+r.w/2,cy=r.y+r.h/2,dx=other.x+other.w/2-cx,dy=other.y+other.h/2-cy,t=Math.min((r.w/2+4)/Math.max(.001,Math.abs(dx)),(r.h/2+4)/Math.max(.001,Math.abs(dy)));return [cx+dx*t,cy+dy*t]}
function drawMap(){const L=D.layout.levels[selected],showReturn=E('show-return').checked,showSecrets=E('show-secrets').checked;let svg='<defs><pattern id="grid" width="35" height="35" patternUnits="userSpaceOnUse"><path d="M 35 0 L 0 0 0 35" fill="none" stroke="#294047" stroke-width=".6"/></pattern></defs><rect width="1010" height="580" fill="url(#grid)"/>';svg=svg.replace('</defs>',Object.entries(colors).map(([k,c])=>`<marker id="arrow-${k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="${c}"/></marker>`).join('')+'</defs>');
for(const [a,b,kind] of L.links){if(kind==='return'&&!showReturn||kind==='secret'&&!showSecrets)continue;const A=L.rooms.find(r=>r.id===a),B=L.rooms.find(r=>r.id===b),p=boundary(A,B),q=boundary(B,A);svg+=`<path d="M${p} L${q}" fill="none" stroke="${colors[kind]}" stroke-width="2.5" marker-end="url(#arrow-${kind})" stroke-dasharray="${kind==='main'?'none':kind==='blocked'?'6 7':'8 6'}" opacity=".85"/>`}
for(const r of L.rooms){if(r.type==='secret'&&!showSecrets)continue;const label=splitLabel(r.name,r.w);svg+=`<g class="room${r.id===roomId?' selected':''}" data-id="${r.id}" data-type="${r.type}" role="button" tabindex="0" aria-label="${esc(r.name)}"><title>${esc(r.text)}</title><rect x="${r.x}" y="${r.y}" width="${r.w}" height="${r.h}" rx="5"/><text class="kind" x="${r.x+13}" y="${r.y+22}">${esc(kinds[r.type].toUpperCase())}</text>${label.map((t,i)=>`<text x="${r.x+13}" y="${r.y+52+i*23}">${esc(t)}</text>`).join('')}</g>`}E('map').innerHTML=svg;
for(const g of E('map').querySelectorAll('.room')){const choose=()=>{roomId=g.dataset.id;renderDetail();drawMap();E('map').querySelector(`[data-id="${roomId}"]`).focus()};g.addEventListener('click',choose);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose()}})}}
function renderDetail(){const L=D.layout.levels[selected],r=L.rooms.find(r=>r.id===roomId);E('detail-kind').textContent=r?kinds[r.type]:'Задача уровня';E('detail-title').textContent=r?r.name:L.verb;E('detail-text').textContent=r?r.text:L.entry;for(const key of ['change','choice','risk','checkpoint'])E(key).textContent=L[key]}
function renderScene(){const id=E('scene-select').value,lines=D.lines.filter(r=>r.scene_id===id);E('dialogues').innerHTML=lines.map(r=>`<article class="line"><header><strong>${esc(r.subtitle_name)}</strong><span class="cond">${esc(r.branch)}</span></header><blockquote>${esc(r.text)}</blockquote><p>${esc(r.cue)} · ${esc(r.direction)}</p><code>${esc(r.line_id)} · ${esc(r.channel)} · not_recorded</code></article>`).join('');E('reading-note').textContent=`${D.meta.lines} строк / ${D.meta.scenes} сцен во всём листе. Здесь ${lines.length} строк; условия веток не означают, что все варианты звучат подряд. Записей актёров пока нет.`}
function sceneOptions(){const L=D.layout.levels[selected],all=[...new Set(D.lines.map(r=>r.scene_id))],first=L.scenes,other=all.filter(id=>!first.includes(id));E('scene-select').innerHTML='<optgroup label="Этот уровень">'+first.map(id=>`<option value="${id}">${esc(D.scene_titles[id])}</option>`).join('')+'</optgroup><optgroup label="Пролог и остальные сцены">'+other.map(id=>`<option value="${id}">${esc(D.scene_titles[id])}</option>`).join('')+'</optgroup>';renderScene()}
function setLevel(index){selected=index;roomId=null;const L=D.layout.levels[index];E('map-title').textContent=L.id+'. '+L.title;E('target').textContent=L.minutes+' мин · целевой бюджет';E('verb').textContent=L.verb;for(const b of document.querySelectorAll('.level'))b.setAttribute('aria-selected',String(Number(b.dataset.index)===index));renderDetail();drawMap();sceneOptions()}
E('level-list').innerHTML=D.layout.levels.map((L,i)=>`<button class="level" role="tab" data-index="${i}" aria-selected="false"><span class="n">УРОВЕНЬ ${L.id}</span><strong>${esc(L.title)}</strong><small>${L.minutes} минут · цель</small></button>`).join('');for(const b of document.querySelectorAll('.level'))b.addEventListener('click',()=>setLevel(Number(b.dataset.index)));E('show-return').addEventListener('change',drawMap);E('show-secrets').addEventListener('change',drawMap);E('reset-detail').addEventListener('click',()=>{roomId=null;renderDetail();drawMap()});E('scene-select').addEventListener('change',renderScene);setLevel(0);
</script></body></html>'''
target=ROOT/'design/review/chapter1-v041.html'
target.write_text(TEMPLATE.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')),encoding='utf-8')
reading=['# Первая глава — актёрская читка 0.41','',
         'Редакторский текст для будущей живой записи. Не записано и не интегрировано в Godot.',
         'Условия веток читаются отдельно. Молчаливый выход — сценическое действие без фиктивного звукового файла.',
         f'В листе {len(lines)} строк, {len(scenes)} сцен. Источник: chapter1-dialogue-v041.tsv.',
         'Пролог и сцена за чаем проходят на стоянке; команда следующего отправления — после возвращения к пульту.','']
for scene,group in itertools.groupby(lines,key=lambda r:r['scene_id']):
    reading += [f'## {scene_titles[scene]}',f'Сцена `{scene}`.','']
    for row in group:
        reading += [f"**{row['subtitle_name']}** · `{row['line_id']}` · {row['branch']}",
                    f"*{row['cue']}. {row['direction']}.*",'',row['text'],'']
(ROOT/'design/voice/chapter1-reading-v041.md').write_text('\n'.join(reading)+'\n',encoding='utf-8')
print(json.dumps({'levels':len(layout['levels']),'lines':len(lines),'scenes':len(scenes),'words':data['meta']['words'],'status':'planning artifacts only; voice not recorded'}))
