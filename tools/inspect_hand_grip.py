import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'source_25d/quaternius/Man-CC0.glb'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
for obj in bpy.context.scene.objects:
    if obj.animation_data:obj.animation_data_clear()
bpy.context.view_layer.update()
rows={}
for b in arm.data.bones:
    if any(s in b.name for s in ['Palm','Hand','Finger','Thumb','LowerArm']):
        rows[b.name]={'head':list(arm.matrix_world@b.head_local),'tail':list(arm.matrix_world@b.tail_local),'rest_matrix':[list(r) for r in arm.matrix_world@b.matrix_local],'parent':b.parent.name if b.parent else None}
report={'bones':rows,'pose':{b.name:{'rotation_mode':b.rotation_mode,'quaternion':list(b.rotation_quaternion)} for b in arm.pose.bones if b.name in rows}}
(ROOT/'release/capability-audit/hand-inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('HAND_INSPECTION_OK')
