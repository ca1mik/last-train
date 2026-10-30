"""Validate evidence files, not artistic acceptance or player duration."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'release/campaign-v037'

def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

checks = {}
for name in ['base-gameplay.json', 'first-routes.json', 'first-reload.json', 'rules.json', 'transition.json']:
    data = read(name)
    assert not data.get('failures', []), (name, data)
    checks[name] = data.get('checks', data.get('passed'))

tours = {}
for method in ['power', 'winch']:
    data = read(f'native-{method}/result.json')
    assert data['mission'] == 1 and data['method'] == method, data
    assert data['reason'] == 'route restored; refuge contacted', data
    assert data['hero_teleports'] == 0 and not data['health_override'], data
    assert data['reserve_on'] and not data['passengers_evacuated'], data
    assert data['gpu_screenshots'], data
    actions = [row['action'] for row in data['actions']]
    if method == 'winch':
        assert actions.count('manual') == 8, actions
    else:
        required = ['jumper', 'install', 'feed_a', 'feed_b', 'test', 'drive']
        assert [action for action in actions if action in required] == required, actions
    tours[method] = {'seconds': data['seconds'], 'health': data['health'], 'combat_seconds': data['combat_seconds']}

captures = {}
for path in sorted(OUT.glob('gallery/*.png')) + [OUT/'native-power/final.png', OUT/'native-winch/final.png', OUT/'export-first/scene-25d.png', OUT/'export-resume/scene-25d.png']:
    with Image.open(path) as picture:
        assert picture.size == (1600, 900), (path, picture.size)
        captures[str(path.relative_to(OUT))] = {'dimensions': list(picture.size), 'sha256': digest(path)}

video = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,avg_frame_rate,duration', '-of', 'json', str(OUT/'hospital-motion.mp4')], text=True))['streams'][0]
assert (video['width'], video['height']) == (1600, 900)
assert video['avg_frame_rate'] == '60/1' and float(video['duration']) >= 11

log_names = ['import-25d', 'qa-25d', 'qa-expedition', 'qa-expedition-reload', 'qa-hospital-rules', 'qa-campaign-transition', 'qa-hospital-power', 'qa-hospital-winch', 'export-25d', 'native-power-v037', 'native-winch-v037']
for name in log_names:
    for suffix in ['.log', '-err.log']:
        path = ROOT/'release'/(name+suffix)
        assert not re.search(r'SCRIPT ERROR|Parse Error|^ERROR:', path.read_text(encoding='utf-8', errors='replace'), re.M), path
for name in ['export-first', 'export-resume', 'motion']:
    path=OUT/(name+'-err.log')
    assert not re.search(r'SCRIPT ERROR|Parse Error|^ERROR:', path.read_text(encoding='utf-8', errors='replace'), re.M), path

exe = ROOT/'dist/LastTrain-0.37-25D/LastTrain.exe'
manifest = json.loads((exe.parent/'build-manifest.json').read_text(encoding='utf-8-sig'))
assert manifest['sha256'] == digest(exe)
report = {'version':'0.37', 'checks':checks, 'ordinary_input_native_tours':tours, 'captures':captures, 'video':video, 'exe_sha256':digest(exe), 'script_sha256':{name:digest(ROOT/'game25d/scripts'/name) for name in ['hospital.gd','campaign.gd','expedition.gd','main.gd']}, 'campaign_target_minutes':[240,300], 'human_duration_measured':False, 'art_accepted':False, 'release_ready':False, 'known_open':['Full first chapter and hospital evacuation incomplete', 'Chapters 3-5 not migrated', 'Character motion/contact and environment art unfinished', 'Vulkan exit warning: 7 Texture RIDs'], 'visual_review_record':'design/progress-v037.md', 'harness_failure_preserved':'native-winch-focus-failure.json'}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':checks,'native_tours':tours,'exe_sha256':report['exe_sha256'],'release_ready':False},ensure_ascii=False))
