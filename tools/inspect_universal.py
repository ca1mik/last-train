import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path('H:/game')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
base=next((root/'source_25d/base-characters-standard').rglob('Superhero_Male_FullBody.gltf'))
bpy.ops.import_scene.gltf(filepath=str(base))
target=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');target.name='Target'
target_meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
before=set(bpy.data.objects)
ual=next((root/'source_25d/ual-standard').rglob('UAL1_Standard.glb'))
bpy.ops.import_scene.gltf(filepath=str(ual))
source=next(o for o in bpy.data.objects if o not in before and o.type=='ARMATURE');source.name='Source'
report={'target_transform':[list(row) for row in target.matrix_world], 'source_transform':[list(row) for row in source.matrix_world],
 'meshes':[(o.name,list(o.dimensions),len(o.data.vertices),[m.name for m in o.data.materials]) for o in target_meshes],
 'target_bones':{b.name:{'parent':b.parent.name if b.parent else None,'head_world':list(target.matrix_world@b.head_local),'matrix_world':[list(row) for row in target.matrix_world@b.matrix_local]} for b in target.data.bones},
 'source_bones':{b.name:{'parent':b.parent.name if b.parent else None,'head_world':list(source.matrix_world@b.head_local),'matrix_world':[list(row) for row in source.matrix_world@b.matrix_local]} for b in source.data.bones},
 'actions':[(a.name,list(a.frame_range),[(s.identifier,s.target_id_type) for s in a.slots]) for a in bpy.data.actions]}
(root/'release/universal-inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('UNIVERSAL_REPORT_WRITTEN')
