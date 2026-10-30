"""Blender-only diagnostic of the current mesh, pose and grip; no asset writes."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'game25d/assets/characters/motion-v38/worker.glb'))
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
for track in arm.animation_data.nla_tracks:
    track.mute = True
idle = next(a for a in bpy.data.actions if a.name.endswith('Rail_Idle'))
arm.animation_data.action = idle
arm.animation_data.action_slot = idle.slots[0]
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()
palm = arm.matrix_world @ arm.pose.bones['Palm.R'].matrix
inv = palm.inverted()
rows = {}
for bone in arm.pose.bones:
    if bone.name in ['LowerArm.R','Palm.R','MiddleHand.R','Fingers.R','Thumb1.R','Thumb2.R']:
        rows[bone.name] = {'head_palm':list(inv @ arm.matrix_world @ bone.head),
                           'tail_palm':list(inv @ arm.matrix_world @ bone.tail),
                           'basis_euler':list(bone.matrix_basis.to_euler()),
                           'rest_matrix':[list(row) for row in arm.data.bones[bone.name].matrix_local]}
meshes = {}
depsgraph = bpy.context.evaluated_depsgraph_get()
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH':
        continue
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    groups = {g.index:g.name for g in obj.vertex_groups}
    points = []
    for vertex in mesh.vertices:
        influences = {groups[g.group]:g.weight for g in obj.data.vertices[vertex.index].groups}
        if any(influences.get(n,0)>.1 for n in ['Palm.R','MiddleHand.R','Fingers.R','Thumb1.R','Thumb2.R']) or 'Rail key' in obj.name:
            points.append({'vertex':vertex.index,'palm_local':list(inv @ evaluated.matrix_world @ vertex.co),
                           'rest':list(obj.data.vertices[vertex.index].co),'groups':influences})
    if points:
        meshes[obj.name] = {'points':points,'polygons': [{'vertices':list(p.vertices),'material':obj.data.materials[p.material_index].name} for p in obj.data.polygons if any(v in {x['vertex'] for x in points} for v in p.vertices)]}
    evaluated.to_mesh_clear()
report={'blender':bpy.app.version_string,'bones':rows,'meshes':meshes}
(ROOT/'release/tool-contact-v043/before/blender-contact.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('CONTACT_DIAGNOSED', {name:len(data['points']) for name,data in meshes.items()})
