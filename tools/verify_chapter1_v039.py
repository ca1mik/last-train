"""Check versioned technical evidence; never certify art or human duration."""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release/chapter1-v039'
BUILD=ROOT/'release/build-0.39'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
checks={}
for name in ['base-gameplay','first-routes','first-reload','hospital-rules','campaign-transition','motion-rules']:
    d=read(BUILD/f'{name}.json');assert not d['failures'],(name,d)
    checks[name]=d['checks']
d=read(OUT/'rules.json');assert not d['failures'],d;checks['exit-rules']=d['checks']
assert sum(checks.values())==135,checks
hashes={name:sha(ROOT/f'game25d/scripts/{name}.gd') for name in ['main','actor','expedition','chapter1_exit']}
tours={}
for method in ['stopper','power']:
    folder=OUT/f'native-{method}'
    d=read(folder/'result.json')
    assert d['reason']=='exit ready' and d['mission']==3 and d['exit_stage']==6,(method,d)
    assert d['game_version']=='0.39.0' and d['hospital_arrived'] and d['checkpoint_preserved'],method
    assert d['hero_teleports']==d['cart_teleports']==0 and not d['health_override'],method
    assert d['cart_distance']>80 and d['health']>0 and d['bell_rung'] and d['gpu_screenshots'],method
    for key,name in [('main','main'),('actor','actor'),('expedition','expedition'),('exit','chapter1_exit')]:
        assert d[f'{key}_sha256'].upper()==hashes[name],(method,name)
    ordered=[a['action'] for a in d['actions'] if a['action'].startswith('exit_') and a['action']!='exit_bell' or a['action']=='lida_door']
    assert ordered==['exit_begin','exit_isolate','exit_clear','exit_throw','exit_lock','lida_door'],ordered
    for png in [*folder.glob('exit-*.png'),folder/'final.png',folder/'hospital-arrival.png']:
        with Image.open(png) as im:assert im.size==(1600,900),(png,im.size)
    tours[method]={k:d[k] for k in ['seconds','health','combat_seconds','hero_distance','cart_distance','hospital_arrived','checkpoint_preserved']}
    tours[method]['scope']='ordinary engine keyboard/mouse automation, not human first-play'
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,duration','-of','json',str(OUT/'native-stopper/route.mp4')],text=True))['streams'][0]
assert (meta['width'],meta['height'],meta['avg_frame_rate'])==(1600,900,'60/1'),meta
assert tours['stopper']['seconds']<float(meta['duration'])<tours['stopper']['seconds']+5,meta
prep=read(OUT/'export-prep.json');assert prep['source_unchanged'] and prep['copy_identical'],prep
for name in ['export-fresh','export-exit','export-first-launcher']:
    with Image.open(OUT/name/'scene-25d.png') as im:assert im.size==(1600,900)
assert 'EXPEDITION_READY' in (OUT/'export-first-launcher.log').read_text(encoding='utf-8-sig')
for p in [*BUILD.glob('*.log'),OUT/'native-stopper-err.log',OUT/'native-power-err.log',OUT/'export-fresh-err.log',OUT/'export-exit-err.log',OUT/'export-first-launcher-err.log']:
    log=p.read_text(encoding='utf-8-sig',errors='replace')
    assert not any(token in log for token in ['SCRIPT ERROR','Parse Error','\nERROR:']),(p,log[-1500:])
exe=ROOT/'dist/LastTrain-0.39-25D/LastTrain.exe';manifest=read(exe.parent/'build-manifest.json')
assert manifest['sha256']==sha(exe) and manifest['version']=='0.39' and not manifest['release_ready']
report={'version':'0.39','state_checks':checks,'total_state_checks':sum(checks.values()),'native_tours':tours,'video':meta,'source_sha256':hashes,'exe_sha256':sha(exe),'review':'design/progress-v039.md','campaign_target_minutes':[240,300],'campaign_complete':False,'human_playtest':False,'art_accepted':False,'release_ready':False,'open':['Full first chapter, prologue and campaign content','Visible companions and staged interactions','Finished environment and character art','Human duration and gameplay review','Vulkan shutdown: 7 Texture RIDs']}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':sum(checks.values()),'tours':tours,'exe_sha256':sha(exe),'release_ready':False}))
