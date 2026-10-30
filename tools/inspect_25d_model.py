import bpy,json
from mathutils import Vector
from pathlib import Path
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath='H:/game/source_25d/quaternius/Man-CC0.glb')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
report={'meshes':[(o.name,list(o.dimensions),len(o.data.vertices),[m.name for m in o.data.materials]) for o in meshes],
 'bounds':[[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)],
 'bones':[(b.name,list(b.head_local),list(b.tail_local)) for b in arm.data.bones],
 'actions':[(a.name,list(a.frame_range)) for a in bpy.data.actions]}
Path('H:/game/release/model-inspection-25d.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('MODEL_REPORT_WRITTEN')
