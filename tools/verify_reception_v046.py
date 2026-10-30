"""Evidence for receiving preparation, explicitly not evacuation/release."""
from pathlib import Path
import hashlib,json,re
from PIL import Image
root=Path(__file__).resolve().parents[1];proof=root/'release/reception-v046'
read=lambda p:json.loads(p.read_text('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
counts={}
for name,expected in [('rules',57),('hospital',23),('transition',9),('foundation',38)]:
    data=read(proof/(name+'.json'));assert data['checks']==expected and not data['failures']
    counts[name]=data['checks']
source={name:sha(root/'game25d/scripts'/name) for name in ['hospital.gd','hospital_reception.gd','environment_kit.gd','hospital_map.gd']}
routes={}
for name in ['native-current','tour-winch-current']:
    data=read(proof/name/'result.json')
    assert data['reason']=='receiving prepared' and data['hero_teleports']==0 and not data['health_override']
    assert data['reserve_on'] and data['passengers_evacuated']==0
    assert all(data['preparation'].values())
    assert data['hospital_sha256']==source['hospital.gd'] and data['reception_sha256']==source['hospital_reception.gd']
    if name=='native-current':assert data['out_of_view_frames']==0
    routes[name]={key:data[key] for key in ['seconds','health','method','work_order']}
gallery=read(proof/'gallery/manifest.json')
assert gallery['hospital_sha256']==source['hospital.gd'] and gallery['reception_sha256']==source['hospital_reception.gd']
images=[]
for folder in ['gallery','native-current']:
    for p in sorted((proof/folder).glob('*.png')):
        with Image.open(p) as im:assert im.size==(1600,900),(p,im.size)
        images.append(str(p.relative_to(proof)))
assert len(list((proof/'gallery').glob('*.png')))>=10
for name in ['rules','hospital','transition','foundation','native-current','tour-winch-current','gallery']:
    for suffix in ['.log','-err.log']:
        text=(proof/(name+suffix)).read_text('utf-8-sig')
        assert not re.search(r'SCRIPT ERROR|Parse Error|^ERROR:',text,re.M),(name,suffix,text[-1000:])
result={'stage':'0.46-dev receiving preparation','checks':counts,'total_related_checks':sum(counts.values()),
        'routes':routes,'source_sha256':source,'images':images,'gpu':gallery['gpu'],
        'release_ready':False,'human_playtest':False,'four_people_evacuated':False,
        'scope':'Real wagon/receiving props, held E, collision changes, save reconstruction, independent work order and ordinary known-goal input. Visible Nina/Lida/Raisa/group, boarding and confession remain in production.',
        'known_open':['7 Texture RIDs on renderer shutdown','NPC staging/animation and full hospital evacuation','Full campaign, live voices, independent human playtest and Steam publication']}
(proof/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'checks':sum(counts.values()),'routes':len(routes),'images':len(images),'evacuation':False}))
