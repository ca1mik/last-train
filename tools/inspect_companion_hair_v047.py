import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path('H:/game/source_25d/base-characters-standard');report={}
for name in ['Hair_Long','Hair_SimpleParted','Hair_Buns','Hair_BuzzedFemale']:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    path=next(p for p in root.rglob(name+'.gltf') if 'Origin at 0' in str(p))
    bpy.ops.import_scene.gltf(filepath=str(path))
    report[name]={'path':str(path),'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'bounds':[list(o.matrix_world@Vector(c)) for c in o.bound_box]} for o in bpy.context.scene.objects if o.type=='MESH']}
Path('H:/game/release/companions-v047/hair-inspection.json').write_text(json.dumps(report,indent=2),'utf-8')
print('HAIR_INSPECTED')
