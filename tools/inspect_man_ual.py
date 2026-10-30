import bpy,json
from pathlib import Path
root=Path('H:/game')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(root/'game25d/assets/characters/worker.glb'))
target=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(next((root/'source_25d/ual-standard').rglob('UAL1_Standard.glb'))))
source=next(o for o in bpy.data.objects if o not in before and o.type=='ARMATURE')
report={}
for label,arm in [('man',target),('ual',source)]:
    report[label]={'world_matrix':[list(row) for row in arm.matrix_world], 'bones':{b.name:{'parent':b.parent.name if b.parent else None,'head':list(arm.matrix_world@b.head_local),'world_matrix':[list(row) for row in arm.matrix_world@b.matrix_local]} for b in arm.data.bones}}
report['actions']=[{'name':a.name,'frames':list(a.frame_range),'slots':[s.identifier for s in a.slots]} for a in bpy.data.actions]
out=root/'release/motion-v038';out.mkdir(exist_ok=True)
(out/'rigs.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for label in ['man','ual']:
    print(label,report[label]['world_matrix'])
    print([(name,b['parent'],[round(n,4) for n in b['head']]) for name,b in report[label]['bones'].items() if any(w in name.lower() for w in ['hips','body','bone','pelvis','root','thigh','calf','foot','leg','arm','hand','palm'])])
print('ACTIONS',[(a['name'],a['frames']) for a in report['actions']])
