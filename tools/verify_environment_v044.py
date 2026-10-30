"""Verify executed environment 0.44 evidence. Does not certify art or human appeal."""
from pathlib import Path
import json,hashlib,re,shutil,subprocess
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release/environment-v044';BUILD=ROOT/'release/build-0.44'
def read(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
for name in ['base-gameplay','first-routes','first-reload','hospital-rules','campaign-transition','motion-rules']:
    data=read(BUILD/(name+'.json'));assert not data['failures'],(name,data);checks[name]=data['checks']
exit_rules=read(ROOT/'release/chapter1-v039/rules.json');assert not exit_rules['failures'];checks['exit-rules']=exit_rules['checks'];shutil.copy2(ROOT/'release/chapter1-v039/rules.json',OUT/'exit-rules.json')
for name in ['rules','locations-controls']:
    data=read(OUT/(name+'.json'));assert not data['failures'],(name,data);checks[name]=data['checks']
tours={}
for name in ['tour-forest','tour-wasteland','native-forest']:
    d=read(OUT/name/'result.json');assert d['reason']=='completed' and d['mission']==3 and d['gate_open'],(name,d)
    assert d['hero_teleports']==0 and not d['health_override'],(name,d)
    assert d['out_of_view_frames']==0 if name=='native-forest' else d['out_of_view_frames'] is None,(name,d)
    tours[name]=d
for name in ['hospital-power','hospital-winch']:
    d=read(BUILD/name/'result.json');assert d['reason']=='route restored; refuge contacted',d;tours[name]=d
for scene in ['forest','wasteland','hospital']:
    path=OUT/('export-'+scene)/'scene-25d.png'
    with Image.open(path) as im:assert im.size==(1600,900),(path,im.size)
    assert 'CAPTURED_25D' in (OUT/('export-'+scene+'.log')).read_text('utf-8-sig')
with Image.open(OUT/'export-menu.png') as im:assert im.size==(1600,900)
for path in [*OUT.glob('*.log'),*BUILD.glob('*.log')]:
    log=path.read_text('utf-8-sig',errors='replace');assert not re.search(r'SCRIPT ERROR|Parse Error|^ERROR:',log,re.M),(path,log[-1200:])
exe=ROOT/'dist/LastTrain-0.44-25D/LastTrain.exe'
sources=[*ROOT.joinpath('game25d/scripts').glob('*.gd'),*ROOT.joinpath('game25d/shaders').glob('*.gdshader')]
report={'version':'0.44.0','engine':'Godot 4.7.2 Forward+','state_checks':checks,'total_state_checks':sum(checks.values()),'routes':tours,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},'exe_sha256':sha(exe),'gpu_gallery':read(OUT/'gallery/manifest.json'),'human_playtest':False,'art_accepted':False,'campaign_complete':False,'scope':'Hospital dressing + standalone forest/freight-yard scenes + location selector. No full new campaign chapters.','known_open':['7 Texture RIDs warning at native shutdown','Character/interact animation, audio and full campaign remain open','Standalone maps are short prototypes; final art and independent first playtest remain open']}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=read(exe.parent/'build-manifest.json');manifest.update({'version':'0.44','sha256':sha(exe).upper(),'scope':report['scope'],'release_ready':False,'standalone_locations':['forest','wasteland'],'evidence':'release/environment-v044/verification.json'})
(exe.parent/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':sum(checks.values()),'exe_sha256':sha(exe),'routes':{n:round(d['seconds'],2) for n,d in tours.items()},'release_ready':False}))
