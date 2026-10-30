"""Check current technical evidence; never certify art, fun or campaign duration."""
import hashlib,json,re,statistics,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release/motion-v038'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def video(path):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,duration','-of','json',str(path)],text=True))['streams'][0]
    assert (data['width'],data['height'])==(1600,900),path
    assert data['avg_frame_rate']=='60/1',path
    return data

main_hash=sha(ROOT/'game25d/scripts/main.gd')
actor_hash=sha(ROOT/'game25d/scripts/actor.gd')
checks={}
for name in ['base-gameplay.json','first-routes.json','first-reload.json','hospital-rules.json','campaign-transition.json','rules.json']:
    data=read(OUT/name);assert not data['failures'],(name,data)
    checks[name]=data['checks']
assert sum(checks.values())==108,checks
assert 1.95<read(OUT/'rules.json')['dodge_distance']<2.15

tours={}
for kind in ['first-stopper','first-power','hospital-power','hospital-winch']:
    data=read(OUT/f'native-{kind}/result.json')
    assert data['game_version']=='0.38.0'
    assert data['main_sha256'].upper()==main_hash and data['actor_sha256'].upper()==actor_hash,kind
    assert data['hero_teleports']==0 and not data['health_override'] and data['gpu_screenshots'],kind
    assert data['health']>0,kind
    if kind.startswith('first'):
        assert data['mission']==3 and data['reason']=='patient boarded' and data['cart_teleports']==0 and data['cart_distance']>80,kind
    else:
        assert data['mission']==1 and data['reserve_on'] and not data['passengers_evacuated'],kind
    tours[kind]={'seconds':data['seconds'],'health':data['health'],'input':data['input'],'human_playtest':False}

runtime={}
for name in ['runtime','runtime-close','fps30','fps120']:
    data=read(OUT/name/'samples.json');samples=data['samples']
    assert data['main_sha256'].upper()==main_hash and data['actor_sha256'].upper()==actor_hash,name
    assert all(s['in_view'] for s in samples if s['time']>.5),(name,'camera framing')
    phases={}
    for key,a,b,speed in [('walk',1.5,2.8,1.72),('run',3.5,6.8,3.8),('sprint',7.5,8.8,5.7)]:
        segment=[s for s in samples if a<s['time']<b]
        measured=statistics.median(s['ground_speed'] for s in segment)
        assert abs(measured-speed)<.03,(name,key,measured)
        heights=[s['head'][1]-s['root'][1] for s in segment]
        phases[key]={'speed':measured,'head_joint_height_range':max(heights)-min(heights)}
    assert phases['run']['head_joint_height_range']<.10,(name,phases)
    pause=[s for s in samples if 19.3<s['time']<19.8]
    assert all(s['paused'] for s in pause),name
    assert max(s['head'][1] for s in pause)-min(s['head'][1] for s in pause)<1e-5,name
    assert samples[-1]['player_down'] and samples[-1]['action_left']==0 and samples[-1]['state']=='Death',name
    runtime[name]={'phases':phases,'seconds':data['seconds'],'scope':data['input']}
    if name.startswith('runtime'):
        runtime[name]['video']=video(OUT/name/'motion.mp4')
        assert float(runtime[name]['video']['duration'])>=26.5,name
    else:
        expected_delta=1/(30 if name=='fps30' else 120)
        assert abs(statistics.median(s['render_delta'] for s in samples if s['time']>1)-expected_delta)<1e-5,name

carry=read(OUT/'carry-native/samples.json')
assert carry['actor_sha256'].upper()==actor_hash and carry['main_sha256'].upper()==main_hash
errors=sorted(max(s['L'],s['R']) for s in carry['samples'])
assert max(errors)<.03,max(errors)
carry_metrics={'max_wrist_error':max(errors),'p95_wrist_error':errors[int(len(errors)*.95)],'video':video(OUT/'carry-native/motion.mp4'),'acceptance':'joint target metric, not finished finger/clothing art'}

pngs=list((OUT/'views').glob('[0-9]*.png'))
assert len(pngs)==56,len(pngs)
pngs += [OUT/'export-first/scene-25d.png',OUT/'export-resume/scene-25d.png',OUT/'export-boarded/scene-25d.png']
pngs += [OUT/f'native-{name}/final.png' for name in ['first-stopper','first-power','hospital-power','hospital-winch']]
for path in pngs:
    with Image.open(path) as picture:assert picture.size==(1600,900),(path,picture.size)

log_files=[ROOT/'release'/f'{name}-err.log' for name in ['import-25d','qa-25d','qa-expedition','qa-expedition-reload','qa-hospital-rules','qa-campaign-transition','qa-motion','qa-hospital-power','qa-hospital-winch','export-25d']]
log_files += [OUT/f'native-{name}-err.log' for name in ['first-stopper','first-power','hospital-power','hospital-winch']]
log_files += [OUT/f'{name}/capture-err.log' for name in ['runtime','runtime-close','carry-native']]
log_files += [OUT/f'{name}-err.log' for name in ['views','fps30','fps120','export-first','export-resume','export-boarded']]
for path in log_files:assert not re.search(r'SCRIPT ERROR|Parse Error|^ERROR:',path.read_text(encoding='utf-8',errors='replace'),re.M),path

exe=ROOT/'dist/LastTrain-0.38-25D/LastTrain.exe'
manifest=read(exe.parent/'build-manifest.json');assert manifest['sha256']==sha(exe)
assert (exe.parent/'licenses/UAL-CC0.txt').is_file()
models={name:{'sha256':sha(ROOT/f'game25d/assets/characters/motion-v38/{name}.glb'),'bytes':(ROOT/f'game25d/assets/characters/motion-v38/{name}.glb').stat().st_size} for name in ['worker','wraith']}
models['patient']={'sha256':sha(ROOT/'game25d/assets/characters/patient.glb'),'bytes':(ROOT/'game25d/assets/characters/patient.glb').stat().st_size}
assert read(OUT/'export-prep.json')['checkpoint_unchanged']
report={'version':'0.38','checks':checks,'total_state_checks':sum(checks.values()),'ordinary_input_native_tours':tours,'runtime':runtime,'carry':carry_metrics,'models':models,'main_sha256':main_hash,'actor_sha256':actor_hash,'exe_sha256':sha(exe),'review':'design/progress-v038.md','scope':'Technical runtime, posed views and captured motion. No human first-play or final art approval.','campaign_target_minutes':[240,300],'campaign_complete':False,'human_playtest':False,'art_accepted':False,'release_ready':False,'open':['Campaign duration/content', 'Coat deformation and anatomy', 'Attack transitions/contact and enemy charge', 'Shadow grain', 'Vulkan shutdown: 7 Texture RIDs']}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':sum(checks.values()),'tours':tours,'carry':carry_metrics,'exe_sha256':report['exe_sha256'],'release_ready':False},ensure_ascii=False))
