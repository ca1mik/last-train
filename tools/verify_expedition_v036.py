"""Collect evidence for this milestone, without treating it as Steam readiness."""
import hashlib
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release/expedition-v036'
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
build=read(ROOT/'dist/LastTrain-0.36-25D/build-manifest.json')
executable=ROOT/'dist/LastTrain-0.36-25D/LastTrain.exe'
if hashlib.sha256(executable.read_bytes()).hexdigest().lower()!=build['sha256'].lower():raise RuntimeError('Executable hash mismatch')
baseline=read(ROOT/'release/gameplay-latest.json')
routes=read(OUT/'routes.json');reload=read(OUT/'reload.json')
controls=read(OUT/'controls.json');boarding=read(OUT/'boarding-probe.json')
stopper=read(OUT/'native-stopper/result.json');power=read(OUT/'tour-power/result.json')
for result in [baseline,routes,reload,controls]:
    if result['failures']:raise RuntimeError(result['failures'])
if not all(boarding[key] for key in ['completed_save_loaded','patient_in_carriage_volume','resume_line_consistent']):raise RuntimeError('Boarding state did not survive reload')
for result in [stopper,power]:
    if result['reason']!='patient boarded' or result['mission']!=3:raise RuntimeError('Incomplete route')
    if result['hero_teleports'] or result['cart_teleports'] or result['health_override']:raise RuntimeError('Fixture mutation in tour')
    if result['cart_distance']<80:raise RuntimeError('Cart did not traverse the return route')
images=[]
for path in [OUT/'export-resume/scene-25d.png',OUT/'native-stopper/final.png',*sorted((OUT/'carry').glob('*.png'))]:
    data=path.read_bytes()
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise RuntimeError('Invalid capture')
    width,height=struct.unpack_from('>II',data,16)
    images.append({'path':str(path.relative_to(ROOT)),'width':width,'height':height,'sha256':hashlib.sha256(data).hexdigest()})
contact=read(OUT/'carry/contact.json')
max_static_error=max(v for row in contact['samples'] for v in row['errors_m'].values())
if max_static_error>.01:raise RuntimeError('Static IK wrist contact exceeds 1 cm')
if not contact['tool_nodes'] or any(t['visible'] for t in contact['tool_nodes']):raise RuntimeError('Tool still visible while holding stretcher')
summary={'build':build,'baseline_checks':baseline['checks'],'expedition_route_checks':routes['checks'],
         'reload_checks':reload['checks'],'controls_probe':controls,'boarding_probe':boarding,'stopper_input_tour':stopper,'power_input_tour':power,
         'static_ik_max_wrist_error_m':max_static_error,'static_ik_scope':'Eight stationary orientations; not moving hand quality',
         'captures':images,'human_playtest':False,'release_ready':False,
         'target_first_play_minutes':'10-15, NOT established by automated routes',
         'remaining':['Final characters and animation library integration','Environment art beyond schematic layout',
                      'Moving carry-contact polish','Physical companion characters and paired carry scene',
                      'Remaining chapters and campaign pacing','Music, voices, human playtest and Steamworks setup',
                      '7 Texture RID warning at Vulkan shutdown']}
if (OUT/'carry-motion.json').is_file():
    motion=read(OUT/'carry-motion.json')
    errors=sorted(max(s['L'],s['R']) for s in motion['samples'])
    summary['moving_ik']={'max_m':max(errors),'p95_m':errors[int(len(errors)*.95)],'seconds':motion['seconds'],
                          'scope':motion['limits']}
(OUT/'verification.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'checks':[baseline['checks'],routes['checks'],reload['checks']],
                  'stopper_seconds':stopper['seconds'],'power_seconds':power['seconds'],
                  'cart_metres':stopper['cart_distance'],'static_wrist_error_m':max_static_error,
                  'release_ready':False},ensure_ascii=False))
