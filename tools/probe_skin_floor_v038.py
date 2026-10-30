import bpy
from pathlib import Path
for filename,clip in [('worker.glb','Man_Idle'),('motion-v38/worker.glb','Rail_Idle')]:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    before=set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath='H:/game/game25d/assets/characters/'+filename)
    arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    for track in arm.animation_data.nla_tracks:track.mute=True
    action=next(a for a in bpy.data.actions if a not in before and a.name.endswith(clip));arm.animation_data.action=action;arm.animation_data.action_slot=action.slots[0]
    bpy.context.scene.frame_set(0);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    for obj in [o for o in bpy.context.scene.objects if o.type=='MESH']:
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();used={v for p in mesh.polygons for v in p.vertices}
        minimum=min(((evaluated.matrix_world@mesh.vertices[i].co).z,i) for i in used)
        print('FLOOR',filename,obj.name,'vertices',len(mesh.vertices),'used',len(used),'min',minimum)
        evaluated.to_mesh_clear()
