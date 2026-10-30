"""Patch only authored finger quaternion samples in a new GLB copy.

glTF 2 uses xyzw quaternions. Mesh, bind, hierarchy, times and other tracks
remain byte-identical. Original and rejected roundtrip candidate are retained.
"""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'game25d/assets/characters/motion-v38/worker.glb'
OLD = {'MiddleHand.R':(0,-.2),'Fingers.R':(0,-1.65),
       'Thumb1.R':(2,.5),'Thumb2.R':(0,.55)}
VARIANTS = {
    'c': {'MiddleHand.R':(0,-.4),'Fingers.R':(0,-1.7),'Thumb1.R':(2,.5),'Thumb2.R':(0,1.5)},
    'd': {'MiddleHand.R':(0,-.55),'Fingers.R':(0,-1.45),'Thumb1.R':(2,.7),'Thumb2.R':(0,1.85)},
}


def multiply(a,b):
    x,y,z,w=a;u,v,s,t=b
    return (w*u+x*t+y*s-z*v,w*v-x*s+y*t+z*u,w*s+x*v-y*u+z*t,w*t-x*u-y*v-z*s)


def axis_quat(spec):
    axis,angle=spec
    q=[0.,0.,0.,math.cos(angle/2)]
    q[axis]=math.sin(angle/2)
    return q


def run(variant):
    original=SOURCE.read_bytes();data=bytearray(original)
    assert struct.unpack_from('<4sII',data)==(b'glTF',2,len(data))
    length,kind=struct.unpack_from('<II',data,12)
    assert kind==0x4E4F534A
    gltf=json.loads(data[20:20+length]);binary=28+length
    assert struct.unpack_from('<I',data,24+length)[0]==0x004E4942
    uses={}
    for anim in gltf['animations']:
        for channel in anim['channels']:
            sampler=anim['samplers'][channel['sampler']]
            uses.setdefault(sampler['output'],[]).append((anim['name'],gltf['nodes'][channel['target']['node']]['name'],channel['target']['path']))
    patched=set();ranges=set();changes=[]
    for index,targets in uses.items():
        if not any(bone in OLD and path=='rotation' for _,bone,path in targets):
            continue
        assert all(bone in OLD and path=='rotation' for _,bone,path in targets),targets
        bones={bone for _,bone,_ in targets};assert len(bones)==1
        bone=next(iter(bones));a=gltf['accessors'][index];view=gltf['bufferViews'][a['bufferView']]
        assert a['type']=='VEC4' and a['componentType']==5126 and 'sparse' not in a
        assert 'min' not in a and 'max' not in a
        old=axis_quat(OLD[bone]);new=axis_quat(VARIANTS[variant][bone])
        delta=multiply([-old[0],-old[1],-old[2],old[3]],new)
        start=binary+view.get('byteOffset',0)+a.get('byteOffset',0)
        stride=view.get('byteStride',16)
        for sample in range(a['count']):
            offset=start+sample*stride
            if offset in patched:
                continue
            old_q=struct.unpack_from('<4f',data,offset);new_q=multiply(old_q,delta)
            norm=math.sqrt(sum(x*x for x in new_q));assert norm>.99
            struct.pack_into('<4f',data,offset,*(x/norm for x in new_q))
            patched.add(offset);ranges.update(range(offset,offset+16))
        changes.append({'accessor':index,'bone':bone,'samples':a['count'],'clips':[x[0] for x in targets]})
    changed={i for i,(a,b) in enumerate(zip(original,data)) if a!=b}
    assert changed and changed<=ranges
    # Guard against accessor aliases with any geometry, inverse bind, or time input.
    used_as_input={s['input'] for anim in gltf['animations'] for s in anim['samplers']}
    protected=used_as_input|{skin['inverseBindMatrices'] for skin in gltf['skins']}
    for mesh in gltf['meshes']:
        for primitive in mesh['primitives']:
            protected.update(primitive['attributes'].values())
            if 'indices' in primitive:protected.add(primitive['indices'])
    widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
    components={5121:1,5123:2,5125:4,5126:4}
    for index in protected:
        a=gltf['accessors'][index];v=gltf['bufferViews'][a['bufferView']]
        width=widths[a['type']]*components[a['componentType']]
        start=binary+v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',width)
        for sample in range(a['count']):
            offset=start+sample*stride
            assert data[offset:offset+width]==original[offset:offset+width]
    output=ROOT/f'game25d/assets/characters/grip-v43/worker-{variant}.glb'
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(data)
    report={'source_sha256':hashlib.sha256(original).hexdigest(),'output_sha256':hashlib.sha256(data).hexdigest(),
            'variant':variant,'output':str(output),'basis_axes_angles':VARIANTS[variant],
            'changed_bytes':len(changed),'quaternion_samples':len(patched),'changed_tracks':changes,
            'protected_accessors_byte_identical':len(protected),'all_other_bytes_identical':True,
            'status':'candidate; GPU and temporal review required'}
    (ROOT/f'release/tool-contact-v043/patch-{variant}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['variant','changed_bytes','quaternion_samples','protected_accessors_byte_identical','all_other_bytes_identical']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=VARIANTS,default='c')
    run(parser.parse_args().variant)
