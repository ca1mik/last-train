"""Bake a corrected power grip on the existing mesh, preserving source assets.

Blender 5.1; output is a candidate until GPU/temporal/interaction review.
"""
import bpy
import json
import sys
import hashlib
from pathlib import Path
from mathutils import Euler

ROOT = Path(__file__).resolve().parents[1]
variant = 'a'
for arg in sys.argv:
    if arg.startswith('--variant='):
        variant = arg.split('=',1)[1]
assert variant in ('a','b')
SOURCE = ROOT/'game25d/assets/characters/motion-v38/worker.glb'
OUT = ROOT/f'game25d/assets/characters/grip-v43/worker-{variant}.glb'
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
objects = [arm] + [o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers)]
rotations = {'MiddleHand.R':(-.45,0,0),'Fingers.R':(-1.45,0,0),
             'Thumb1.R':(0,0,.9),'Thumb2.R':(-.85,0,0)}
if variant == 'b':
    rotations = {'MiddleHand.R':(-.6,0,0),'Fingers.R':(-1.25,0,0),
                 'Thumb1.R':(0,0,1.1),'Thumb2.R':(-1.05,0,0)}
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for bone, angles in rotations.items():
                    path=f'pose.bones["{bone}"].rotation_quaternion'
                    curves=[c for c in bag.fcurves if c.data_path==path]
                    if not curves:
                        raise RuntimeError(f'Missing authored grip: {action.name}, {bone}')
                    q=Euler(angles,'XYZ').to_quaternion()
                    for c in curves:
                        for key in c.keyframe_points:
                            key.co.y=q[c.array_index]
                            key.handle_left.y=key.co.y
                            key.handle_right.y=key.co.y
                            key.interpolation='LINEAR'
arm.animation_data.action=None
for track in arm.animation_data.nla_tracks:
    track.mute=False
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=str(OUT),export_format='GLB',use_selection=True,
                          export_animation_mode='NLA_TRACKS',export_force_sampling=True,
                          export_frame_range=False,export_animations=True)
report={'variant':variant,'blender':bpy.app.version_string,'source':str(SOURCE),
        'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'candidate':str(OUT),'candidate_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
        'basis_euler_xyz':rotations,'mesh_edit':False,'bind_edit':False,
        'materials_edit':False,'left_hand_edit':False,'status':'unaccepted candidate'}
(ROOT/f'release/tool-contact-v043/candidate-{variant}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('GRIP_CANDIDATE_EXPORTED',OUT)
