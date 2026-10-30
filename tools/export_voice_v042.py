"""Export authored reading sheets; this is not a game narrative interpreter.

No audio generation, engine changes, playback, or runtime branch validation.
Run from any directory with Python's standard library.
"""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOICE = ROOT / 'design' / 'voice'
SOURCE = VOICE / 'chapters2-5-reading-v042.md'
PREVIOUS = VOICE / 'chapter1-dialogue-v041.tsv'
FIELDS = ['line_id', 'scene_id', 'speaker', 'subtitle_name', 'channel',
          'branch', 'cue', 'direction', 'text', 'audio_status']
ROLES = {'Артём': 'artem', 'Нина': 'nina', 'Лида': 'lida', 'Павел': 'pavel',
         'Валентина': 'valentina', 'Михаил': 'mikhail', 'Раиса': 'raisa',
         'Голос платформы 1': 'platform-1', 'Голос платформы 2': 'platform-2'}
META = {'Условие': 'branch', 'Место': 'cue', 'Канал': 'channel', 'Подача': 'direction'}


def export():
    scenes, rows, scene = [], [], None
    for number, raw in enumerate(SOURCE.read_text(encoding='utf-8').splitlines(), 1):
        line = raw.strip()
        if line.startswith('## '):
            match = re.fullmatch(r'## ([A-Z0-9_]+) — (.+)', line)
            if not match:
                raise ValueError(f'Invalid scene heading at {number}')
            scene = {'scene_id': match[1], 'title': match[2], 'line_ids': []}
            scenes.append(scene)
            continue
        if not scene or not line:
            continue
        prefix, colon, value = line.partition(': ')
        if colon and prefix in META:
            key = META[prefix]
            if key in scene or not value:
                raise ValueError(f'Duplicate/empty metadata at {number}')
            scene[key] = value
        elif colon and prefix in ROLES:
            if not all(key in scene for key in META.values()) or not value:
                raise ValueError(f'Missing metadata/text at {number}')
            ident = f"{scene['scene_id']}_{len(scene['line_ids']) + 1:03}"
            row = {key: scene[key] for key in META.values()}
            subtitle = prefix + ' (запись, 1998)' if scene['channel'] == 'tape_1998' else prefix
            row.update(line_id=ident, scene_id=scene['scene_id'], speaker=prefix,
                       subtitle_name=subtitle, text=value, audio_status='not_recorded')
            rows.append(row)
            scene['line_ids'].append(ident)
        else:
            raise ValueError(f'Unrecognized authoring line {number}: {line}')
    if not scenes or any(not s['line_ids'] for s in scenes):
        raise ValueError('Empty reading scene')
    with PREVIOUS.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream, delimiter='\t')
        if reader.fieldnames != FIELDS:
            raise ValueError('Chapter 1 schema changed; review before exporting')
        previous = list(reader)
    all_rows = previous + rows
    ids = [r['line_id'] for r in all_rows]
    scene_ids = [s['scene_id'] for s in scenes]
    if len(ids) != len(set(ids)) or len(scene_ids) != len(set(scene_ids)):
        raise ValueError('Duplicate line/scene IDs')
    if any(r['speaker'] not in ROLES or r['audio_status'] != 'not_recorded' for r in all_rows):
        raise ValueError('Review role/audio status before export')
    for row in all_rows:
        if any(not row.get(key) or '\t' in row[key] or '\n' in row[key] for key in FIELDS):
            raise ValueError(f"Invalid TSV fields: {row['line_id']}")

    output = VOICE / 'chapters2-5-dialogue-v042.tsv'
    with output.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, FIELDS, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    # Role sheets retain all partner replies as context; only this role is selected for recording.
    actors = VOICE / 'actors-v042'
    actors.mkdir(exist_ok=True)
    scene_lookup = {s['scene_id']: s for s in scenes}
    for name, slug in ROLES.items():
        owned = [r for r in all_rows if r['speaker'] == name]
        selected = list(dict.fromkeys(r['scene_id'] for r in owned))
        text = [f'# {name} — лист живой записи 0.42', '',
                f'{len(owned)} собственных реплик. Не записано. Реплики партнёров — контекст,',
                'их не нужно читать вместо другого исполнителя. Альтернативы не идут подряд.',
                'Главы 1 и пролог: редакция 0.41; главы 2–5: редакция 0.42.',
                'Точные условия и позиции — в постановочных документах. Все сцены — будущая запись.', '']
        for ident in selected:
            title = scene_lookup.get(ident, {}).get('title', ident)
            text.extend([f'## {ident} — {title}', ''])
            for row in (r for r in all_rows if r['scene_id'] == ident):
                label = '**ЗАПИСЬ: ' + row['subtitle_name'] + '**' if row['speaker'] == name else row['subtitle_name']
                text.extend([f"{label} · `{row['line_id']}` · {row['branch']} · {row['channel']}",
                             f"*{row['cue']} {row['direction']}*", '', row['text'], ''])
        (actors / f'{slug}.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    chapters = Counter(r['scene_id'].split('_')[0] for r in rows)
    report = {
        'scope': 'Authored document export only; no game execution, recordings or actor bookings',
        'source_sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (SOURCE, PREVIOUS)},
        'new_lines': len(rows), 'new_scenes': len(scenes),
        'new_words_all_alternatives': sum(len(r['text'].split()) for r in rows),
        'chapter1_lines': len(previous), 'campaign_written_lines': len(all_rows),
        'audition_lines_separate_not_counted': 21,
        'lines_by_group': dict(chapters),
        'campaign_lines_by_role': dict(Counter(r['speaker'] for r in all_rows)),
        'actor_sheets': len(ROLES), 'audio_status': dict(Counter(r['audio_status'] for r in all_rows)),
        'scenes': scenes,
        'runtime_branch_checks_executed': False, 'human_readthrough_executed': False,
        'human_recordings_exist': False, 'game_maps_added': False,
        'duration_measured': False, 'release_ready': False,
    }
    (VOICE / 'export-v042.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    index = ['# Листы для живой записи — 0.42', '',
             'Редакторский пакет, не готовые аудиозаписи. У каждой роли указаны',
             'собственные строки; партнёры остаются в листе для контекста.',
             'Альтернативы и историческая запись исполняются отдельно.', '',
             '| Роль | Собственных строк |', '|---|---:|']
    for name, slug in ROLES.items():
        index.append(f"| [{name}]({slug}.md) | {report['campaign_lines_by_role'].get(name, 0)} |")
    index += ['', f"Всего {len(all_rows)} строк, включая варианты; все `not_recorded`.",
              '21 отдельная кастинговая строка сюда не включена.', '',
              '[Постановка глав 2–5](../../chapters2-5-production-v042.md) ·',
              '[Бриф записи](../production-ru-v040.md) ·',
              '[Читка глав 2–5](../chapters2-5-reading-v042.md)', '']
    (actors / 'README.md').write_text('\n'.join(index), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('source_sha256', 'scenes')}, ensure_ascii=False))


if __name__ == '__main__':
    export()
