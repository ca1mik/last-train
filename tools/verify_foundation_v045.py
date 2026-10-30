"""Verify executed 0.45 evidence; does not certify art, fun, voices or a release."""
from pathlib import Path
import argparse,hashlib,json,re
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'release/build-0.45'
PROOF=ROOT/'release/foundation-v045'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf-8-sig'))
parser=argparse.ArgumentParser();parser.add_argument('--snapshot',action='store_true')
args=parser.parse_args()
source_dir=PROOF/'source' if args.snapshot else ROOT/'game25d/scripts'
manifest=read(ROOT/'dist/LastTrain-0.45-25D/build-manifest.json')
exe=ROOT/'dist/LastTrain-0.45-25D/LastTrain.exe'
assert manifest['sha256'].lower()==digest(exe)
assert not manifest['release_ready'] and not manifest['human_playtest']
checks={}
for name in ['base-gameplay','campaign-transition','environment-rules','exit-rules',
             'first-reload','first-routes','foundation-rules','hospital-rules',
             'locations-controls','motion-rules']:
    data=read(BUILD/(name+'.json'))
    assert not data['failures'],(name,data)
    checks[name]=data['checks']
assert sum(checks.values())==232,checks
routes={}
source={name:digest(source_dir/name) for name in
        ['main.gd','actor.gd','hospital.gd','expedition.gd','pause_overlay.gd',
         'dialogue_book.gd','player_preferences.gd','chapter1_exit.gd']}
if (PROOF/'verification.json').exists():
    assert source==read(PROOF/'verification.json')['source_sha256'],'Source moved past 0.45; verify archived evidence with --snapshot'
for name in ['first-stopper','first-power','hospital-power','hospital-winch','forest','wasteland']:
    data=read(BUILD/name/'result.json')
    assert data['hero_teleports']==0 and not data['health_override'],(name,data)
    if name.startswith('first'):
        assert data['reason']=='exit ready' and data['hospital_arrived'] and data['checkpoint_preserved']
        assert data['cart_teleports']==0 and data['exit_stage']==6
    elif name.startswith('hospital'):
        assert data['reason']=='route restored; refuge contacted' and data['reserve_on']
        assert not data['passengers_evacuated']
    else:assert data['reason']=='completed' and data['mission']==3 and data['gate_open']
    if 'main_sha256' in data:assert data['main_sha256']==source['main.gd']
    if 'actor_sha256' in data:assert data['actor_sha256']==source['actor.gd']
    routes[name]={k:data[k] for k in ['reason','seconds','health']}
native=read(PROOF/'native/result.json')
assert not native['failures']
assert native['main_sha256']==source['main.gd'] and native['actor_sha256']==source['actor.gd']
assert native['viewport']==[1920,1080] or native['viewport']==[1600,900]
assert '5070' in native['gpu']
assert any(s['phase']=='strike' and s['health']==100 for s in native['samples'])
assert any(s['phase']=='recover' and s['health']==76 for s in native['samples'])
assert any(s['paused'] and .42<=s['sfx']<=.58 for s in native['samples'])
assert any(s['time']<1 and abs(s['sfx']-.83)<.01 for s in native['samples'])
images=[]
for p in sorted((PROOF/'native').glob('*.png')):
    with Image.open(p) as im:assert im.size==(1600,900),(p,im.size)
    images.append(str(p.relative_to(PROOF)))
assert len(images)==6
for name in ['forest-01','forest-02','forest-03','hospital','first']:
    stem=PROOF/('export-final-'+name)
    with Image.open(stem/'scene-25d.png') as im:assert im.size==(1600,900)
    assert 'CAPTURED_25D' in Path(str(stem)+'.log').read_text('utf-8-sig')
    err=Path(str(stem)+'-err.log').read_text('utf-8-sig')
    assert not re.search(r'SCRIPT ERROR|Parse Error|^ERROR:',err,re.M),(name,err)
for p in BUILD.glob('*.log'):
    assert not re.search(r'SCRIPT ERROR|Parse Error|^ERROR:',p.read_text('utf-8-sig'),re.M),p
report={'version':'0.45','total_state_checks':sum(checks.values()),'checks':checks,
        'source_basis':'archived verified 0.45' if args.snapshot else 'current verified 0.45',
        'routes':routes,'exe_sha256':digest(exe),'source_sha256':source,
        'gpu':native['gpu'],'images':images,'release_ready':False,
        'human_playtest':False,'full_campaign':False,'full_hospital_evacuation':False,
        'voices_recorded':False,'art_accepted':False,
        'known_open':['B08: 7 Texture RIDs with ReflectionProbe on GPU shutdown',
                      'Full campaign, NPC staging, art/animation/audio acceptance and Steam release'],
        'scope':'232 behavior rules, 6 known-goal automated input routes, staged GPU contact/pause/journal/slider and packaged startup; not a first human playthrough'}
(PROOF/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'checks':report['total_state_checks'],'routes':len(routes),'sha256':report['exe_sha256']}))
