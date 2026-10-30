"""Exercise real Blender APIs on the existing worker without changing its GLB."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'release' / 'capability-audit' / 'blender'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'game25d/assets/characters/worker.glb'))
imported = list(bpy.context.scene.objects)
arm = next(o for o in imported if o.type == 'ARMATURE')
actions = [{'name': a.name, 'frames': list(a.frame_range),
            'slots': [s.identifier for s in a.slots]} for a in bpy.data.actions]
for obj in imported:
    if obj.animation_data:
        obj.animation_data_clear()
bpy.context.view_layer.update()
meshes = [o for o in imported if o.type == 'MESH']
points = [o.matrix_world @ Vector(corner) for o in meshes for corner in o.bound_box]
height = max(v.z for v in points) - min(v.z for v in points)
container = bpy.data.objects.new('Audit display root', None)
bpy.context.collection.objects.link(container)
for obj in imported:
    if obj.parent is None:
        saved = obj.matrix_world.copy()
        obj.parent = container
        obj.matrix_world = saved
factor = 1.78 / height
container.scale = (factor, factor, factor)
container.location.z = -min(v.z for v in points) * factor
bpy.context.view_layer.update()
report = {'blender': bpy.app.version_string, 'input': str(ROOT / 'game25d/assets/characters/worker.glb'),
          'source_height_all_meshes': height, 'audit_display_height': 1.78,
          'display_scale': factor, 'meshes': len(meshes), 'bones': len(arm.data.bones),
          'actions': actions, 'materials': [m.name for m in bpy.data.materials],
          'rest_pose': True, 'source_modified': False,
          'limits': 'Normalized inspection display; game uses its own source-height factor. This does not certify rigging or animation quality.'}
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.005))
floor = bpy.context.object
material = bpy.data.materials.new('Audit neutral floor')
material.diffuse_color = (.15,.17,.19,1)
floor.data.materials.append(material)
world = bpy.data.worlds.new('Audit world')
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.18,.2,.24,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .5
for position, energy, size in [((3,-4,5),550,4),((-3,-1,3),250,3)]:
    data = bpy.data.lights.new('Audit softbox','AREA');data.energy=energy;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(data.name,data);bpy.context.collection.objects.link(obj);obj.location=position
    obj.rotation_euler=(Vector((0,0,.9))-obj.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('Audit camera');camera_data.type='ORTHO';camera_data.ortho_scale=2.6
camera=bpy.data.objects.new('Audit camera',camera_data);bpy.context.collection.objects.link(camera)
scene=bpy.context.scene;scene.camera=camera;scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
for degree in [0,90,180,270]:
    angle=math.radians(degree)
    camera.location=(math.sin(angle)*4,-math.cos(angle)*4,2.8)
    camera.rotation_euler=(Vector((0,0,.9))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT / f'worker-rest-{degree:03d}.png')
    bpy.ops.render.render(write_still=True)
(OUT / 'inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('BLENDER_CHARACTER_AUDIT_OK')
