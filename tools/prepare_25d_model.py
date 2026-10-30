"""Adapt the CC0 Quaternius character as an authored 3D worker, preserving its rig."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
root=Path('H:/game');out=root/'game25d/assets/characters'
for arg in sys.argv:
    if arg.startswith('--output-dir='):out=Path(arg.split('=',1)[1])
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(root/'source_25d/quaternius/Man-CC0.glb'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
for o in list(bpy.context.scene.objects):
    if o.type=='MESH' and not any(m.type=='ARMATURE' for m in o.modifiers):bpy.data.objects.remove(o,do_unlink=True)
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
# Correct the oversized source hands at bind pose, keeping wrist placement and
# existing topology/weights. The entire descendant chain and weighted geometry
# receive the same rest-space correction, so animation does not stretch bones.
hand_factor=.72
hand_sets={side:{'Palm.'+side,'MiddleHand.'+side,'Fingers.'+side,'Thumb1.'+side,'Thumb2.'+side} for side in ['L','R']}
anchors={side:arm.matrix_world@arm.data.bones['Palm.'+side].head_local for side in ['L','R']}
for side,names in hand_sets.items():
    group_ids={g.index for g in mesh.vertex_groups if g.name in names}
    for vertex in mesh.data.vertices:
        weight=min(1.0,sum(g.weight for g in vertex.groups if g.group in group_ids))
        if weight>0:
            world_point=mesh.matrix_world@vertex.co
            corrected=anchors[side]+(world_point-anchors[side])*hand_factor
            vertex.co=mesh.matrix_world.inverted()@world_point.lerp(corrected,weight)
bpy.context.view_layer.objects.active=arm;arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for side,names in hand_sets.items():
    anchor=arm.data.edit_bones['Palm.'+side].head.copy()
    for name in names:
        bone=arm.data.edit_bones[name]
        bone.head=anchor+(bone.head-anchor)*hand_factor
        bone.tail=anchor+(bone.tail-anchor)*hand_factor
bpy.ops.object.mode_set(mode='OBJECT')
colors={'Shirt':(.055,.09,.105,1),'Pants':(.045,.065,.075,1),'Hair':(.36,.36,.33,1),'Skin':(.55,.37,.27,1),'Eyes':(.015,.023,.025,1),'Socks':(.08,.065,.045,1)}
for mat in bpy.data.materials:
    if mat.name in colors:
        mat.diffuse_color=colors[mat.name]
        if mat.use_nodes:
            node=mat.node_tree.nodes.get('Principled BSDF')
            if node:node.inputs['Base Color'].default_value=colors[mat.name];node.inputs['Roughness'].default_value=.85
# Jacket sleeves use the original skinned arm surfaces. Hands remain bare.
shirt=next(i for i,m in enumerate(mesh.data.materials) if m.name=='Shirt')
skin=next(i for i,m in enumerate(mesh.data.materials) if m.name=='Skin')
pants=next(i for i,m in enumerate(mesh.data.materials) if m.name=='Pants')
leg_groups={g.index for g in mesh.vertex_groups if g.name in ('UpperLeg.L','LowerLeg.L','UpperLeg.R','LowerLeg.R')}
for face in mesh.data.polygons:
    if face.material_index==skin and sum(sum(g.weight for g in mesh.data.vertices[v].groups if g.group in leg_groups) for v in face.vertices)/len(face.vertices)>.55:
        face.material_index=pants
arm_groups={g.index for g in mesh.vertex_groups if g.name in ('UpperArm.L','LowerArm.L','UpperArm.R','LowerArm.R')}
for face in mesh.data.polygons:
    if face.material_index==skin and sum(sum(g.weight for g in mesh.data.vertices[v].groups if g.group in arm_groups) for v in face.vertices)/len(face.vertices)>.55:face.material_index=shirt
bpy.ops.export_scene.gltf(filepath=str(out/'patient.glb'),export_format='GLB',export_animations=True,export_nla_strips=True)
def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.8
    return m
cloth=bpy.data.materials['Shirt'];red=material('Burgundy scarf',(.29,.055,.06));leather=material('Worn leather',(.19,.105,.05));steel=material('Rail key steel',(.22,.25,.25))
inverse=arm.matrix_world.inverted()
def skinned(name,verts,faces,mat,weights):
    data=bpy.data.meshes.new(name);data.from_pydata([inverse@Vector(v) for v in verts],[],faces);data.materials.append(mat)
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.parent=arm;o.matrix_parent_inverse=Matrix.Identity(4)
    groups={n:o.vertex_groups.new(name=n) for n in {k for row in weights for k in row}}
    for i,row in enumerate(weights):
        for bone,weight in row.items():groups[bone].add([i],weight,'REPLACE')
    mod=o.modifiers.new('Original skeleton','ARMATURE');mod.object=arm
    return o
angles=[math.radians(-65+i*310/12) for i in range(13)]
verts=[];weights=[]
for z,rx,ry in ((1.28,.67,.47),(1.96,.56,.42),(2.65,.54,.39)):
    for a in angles:
        x=rx*math.cos(a);verts.append((x,ry*math.sin(a)-.03,z))
        weights.append({'Hips':.65,'UpperLeg.L' if x>0 else 'UpperLeg.R':.35} if z<1.5 else {'Hips':1} if z<2.2 else {'Hips':.4,'Torso':.6})
faces=[(r*13+i,r*13+i+1,(r+1)*13+i+1,(r+1)*13+i) for r in range(2) for i in range(12)]
skinned('Work coat tails',verts,faces,cloth,weights)
# A scarf follows the neck; its tail follows the chest rather than stretching limbs.
verts=[]
for z,rx,ry in ((3.85,.38,.30),(4.03,.34,.28)):
    verts += [(rx*math.cos(i*math.tau/12),ry*math.sin(i*math.tau/12)+.08,z) for i in range(12)]
skinned('Scarf collar',verts,[(i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)],red,[{'Neck':1}]*24)
skinned('Scarf tail',[(-.12,-.25,3.88),(.17,-.25,3.88),(.28,-.44,3.05),(.04,-.47,3.0)],[(0,1,2,3)],red,[{'Torso':1}]*4)
def cube_skin(name,center,size,mat,bone):
    c=Vector(center);s=Vector(size)*.5
    v=[c+Vector((x*s.x,y*s.y,z*s.z)) for x,y,z in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    return skinned(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,[{bone:1}]*8)
cube_skin('Satchel',(.72,-.02,1.94),(.64,.29,.70),leather,'Hips')
skinned('Satchel strap',[(-.46,-.43,3.54),(-.35,-.44,3.57),(.83,-.40,2.15),(.71,-.40,2.12)],[(0,1,2,3)],leather,[{'Torso':1}]*4)
# A grip is measured from the palm/finger landmarks, never the wrist origin.
# The original hand is open. Bake a stable local grip in every action so exports
# and native renders agree; this rig has a single combined Fingers.R segment.
grip_rotations={'MiddleHand.R':(-.20,0,0),'Fingers.R':(-1.65,0,0),'Thumb1.R':(0,0,.5),'Thumb2.R':(.55,0,0)}
from mathutils import Euler
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for bone_name,angles in grip_rotations.items():
                    path='pose.bones["'+bone_name+'"].rotation_quaternion'
                    for curve in list(bag.fcurves):
                        if curve.data_path==path:bag.fcurves.remove(curve)
                    rotation=Euler(angles,'XYZ').to_quaternion()
                    for component in range(4):
                        curve=bag.fcurves.new(path,index=component)
                        curve.keyframe_points.insert(0,rotation[component])
                        curve.keyframe_points.insert(action.frame_range[1],rotation[component])
palm_matrix=arm.matrix_world@arm.data.bones['Palm.R'].matrix_local
middle=arm.matrix_world@arm.data.bones['MiddleHand.R'].head_local
fingers=arm.matrix_world@arm.data.bones['Fingers.R'].head_local
normal=palm_matrix.to_3x3().col[2].normalized()
grip=middle.lerp(fingers,.60)-normal*.065
axis=-palm_matrix.to_3x3().col[0].normalized()
cross=(fingers-middle).normalized();side=axis.cross(cross).normalized()
def key_part(name,center,length,width,depth):
    verts=[center+axis*(a*length*.5)+cross*(b*width*.5)+side*(c*depth*.5)
           for a,b,c in ((-1,-1,-1),(-1,1,-1),(1,1,-1),(1,-1,-1),(-1,-1,1),(-1,1,1),(1,1,1),(1,-1,1))]
    return skinned(name,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],steel,[{'Palm.R':1}]*8)
key_part('Rail key shaft',grip+axis*.23,.80,.085,.085)
key_part('Rail key head',grip+axis*.62,.12,.34,.14)
report={'height_source':max((mesh.matrix_world@Vector(v)).z for v in mesh.bound_box),
        'bones_world':{b.name:list(arm.matrix_world@b.head_local) for b in arm.data.bones},
        'animation_clips':[a.name for a in bpy.data.actions]}
(root/'release/worker-model-v33.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.export_scene.gltf(filepath=str(out/'worker.glb'),export_format='GLB',export_animations=True,export_nla_strips=True)
for o in list(bpy.context.scene.objects):
    if o.name.startswith('Satchel'):bpy.data.objects.remove(o,do_unlink=True)
for name in ('Skin','Eyes','Hair'):
    mat=bpy.data.materials[name];mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.012,.018,.021,1)
red.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.08,.12,.13,1)
hood=material('Empty railway hood',(.035,.065,.07))
angles=[math.radians(-55+i*290/16) for i in range(17)]
v=[]
for z,rx,ry in ((3.95,.32,.34),(4.26,.52,.48),(4.65,.47,.44),(4.93,.13,.19)):
    v += [(rx*math.cos(a),ry*math.sin(a)+.12,z) for a in angles]
skinned('Railway hood',v,[(r*17+i,r*17+i+1,(r+1)*17+i+1,(r+1)*17+i) for r in range(3) for i in range(16)],hood,[{'Head':1}]*len(v))
bpy.ops.export_scene.gltf(filepath=str(out/'wraith.glb'),export_format='GLB',export_animations=True,export_nla_strips=True)
# One native beveled mesh is reused for industrial props; dimensions are set in metres.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=1);box=bpy.context.object
bevel=box.modifiers.new('Soft industrial edges','BEVEL');bevel.width=.035;bevel.segments=2
bpy.ops.object.modifier_apply(modifier=bevel.name)
propdir=root/'game25d/assets/props';propdir.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(propdir/'beveled-box.glb'),export_format='GLB',export_animations=False)
print('WORKER_EXPORTED')
