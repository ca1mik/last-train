"""UAL -> existing Man rig. Candidate only; preserves original files and rest mesh.
Blender world-space rest correction, analytic leg contacts, no bone scale keys.
"""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path('H:/game');OUT=ROOT/'game25d/assets/characters/motion-v38'
character='worker'
for arg in sys.argv:
    if arg.startswith('--character='):character=arg.split('=',1)[1]
assert character in ['worker','wraith']
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/f'game25d/assets/characters/{character}.glb'))
target_objects=list(bpy.context.scene.objects)
target=next(o for o in target_objects if o.type=='ARMATURE')
target_objects=[target]+[o for o in target_objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==target for m in o.modifiers)]
old_actions=list(bpy.data.actions)
for track in target.animation_data.nla_tracks:track.mute=True
idle=next(a for a in old_actions if a.name.endswith('Man_Idle'))
target.animation_data.action=idle;target.animation_data.action_slot=idle.slots[0]
bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
fingers={b.name:b.rotation_quaternion.copy() for b in target.pose.bones if any(s in b.name for s in ['MiddleHand','Finger','Thumb'])}
before=set(bpy.data.objects)
source_path=next((ROOT/'source_25d/ual-standard').rglob('UAL1_Standard.glb'))
bpy.ops.import_scene.gltf(filepath=str(source_path))
source=next(o for o in bpy.data.objects if o not in before and o.type=='ARMATURE')
for track in source.animation_data.nla_tracks:track.mute=True
source_actions={a.name:a for a in bpy.data.actions if a not in old_actions}
mapping={'Bone':'root','Body':'pelvis','Hips':'pelvis','Abdomen':'spine_01','Torso':'spine_03','Neck':'neck_01','Head':'Head'}
for side,s in [('L','l'),('R','r')]:
    for t,u in [('Shoulder','clavicle'),('UpperArm','upperarm'),('LowerArm','lowerarm'),('Palm','hand'),('UpperLeg','thigh'),('LowerLeg','calf'),('Foot','foot')]:mapping[f'{t}.{side}']=f'{u}_{s}'
TR={b.name:(target.matrix_world@b.matrix_local).copy() for b in target.data.bones}
SR={b.name:(source.matrix_world@b.matrix_local).copy() for b in source.data.bones}
INV=target.matrix_world.inverted();IDENT=Matrix.Identity(4)
leg_lengths={}
for side in ['L','R']:
    leg_lengths[side]=((TR['LowerLeg.'+side].translation-TR['UpperLeg.'+side].translation).length,(TR['Foot.'+side].translation-TR['LowerLeg.'+side].translation).length)
source_leg=(SR['calf_l'].translation-SR['thigh_l'].translation).length+(SR['foot_l'].translation-SR['calf_l'].translation).length
leg_scale=sum(leg_lengths['L'])/source_leg
skin_points=[]
for obj in target_objects:
    if obj.type!='MESH':continue
    groups={g.index:g.name for g in obj.vertex_groups}
    for vertex in obj.data.vertices:
        weights=[(groups[g.group],g.weight) for g in vertex.groups if groups[g.group] in TR]
        skin_points.append((obj.matrix_world@vertex.co,weights))
rest_inverses={name:matrix.inverted() for name,matrix in TR.items()}
print('RETARGET_API',bpy.app.version_string,target.data.bones[0].convert_local_to_pose.__doc__[:160])
print('LEG_SCALE',leg_scale,'MAP',mapping)
report={'blender':bpy.app.version_string,'source':str(source_path),'target':f'game25d/assets/characters/{character}.glb','mapping':mapping,'leg_scale':leg_scale,'clips':{},'root_motion':'controller-owned; root horizontal translation removed; pelvis/feet local movement retained','limits':'candidate; foot IK and contact require runtime render; fingers retain authored grip'}
new_actions=[]
clips={'Idle':'Idle_Loop','Walk':'Walk_Loop','Jog':'Jog_Fwd_Loop','Sprint':'Sprint_Loop','Roll':'Roll','Hurt':'Hit_Chest','Death':'Death01','Attack':'Sword_Attack'}
bpy.context.scene.render.fps=60

def set_global(name,rotation,position,poses):
    bone=target.data.bones[name];rest=TR[name]
    world=Matrix.LocRotScale(position,rotation,rest.to_scale())
    kwargs={}
    if bone.parent:kwargs={'parent_matrix':poses[bone.parent.name],'parent_matrix_local':bone.parent.matrix_local}
    basis=bone.convert_local_to_pose(INV@world,bone.matrix_local,invert=True,**kwargs)
    pb=target.pose.bones[name];pb.location=basis.translation;pb.rotation_mode='QUATERNION';pb.rotation_quaternion=basis.to_quaternion();pb.scale=(1,1,1)
    poses[name]=bone.convert_local_to_pose(Matrix.LocRotScale(pb.location,pb.rotation_quaternion,Vector((1,1,1))),bone.matrix_local,**kwargs)

def world_pose(name,poses):return target.matrix_world@poses[name]

def leg_ik(side,foot_pos,source_pose,poses):
    upper='UpperLeg.'+side;lower='LowerLeg.'+side;foot='Foot.'+side;s=side.lower()
    hip=world_pose(upper,poses).translation;current_knee=world_pose(lower,poses).translation
    a,b=leg_lengths[side];difference=foot_pos-hip;distance=min(max(difference.length,abs(a-b)+1e-4),a+b-1e-4)
    direction=difference.normalized();hint=source_pose['calf_'+s].translation-source_pose['thigh_'+s].translation
    pole=hint-direction*hint.dot(direction)
    if pole.length<1e-4:pole=Vector((0,-1,0))-direction*direction.dot(Vector((0,-1,0)))
    pole.normalize();along=(a*a-b*b+distance*distance)/(2*distance);height=math.sqrt(max(0,a*a-along*along))
    knee=hip+direction*along+pole*height
    up_rot=world_pose(upper,poses).to_quaternion();swing=(current_knee-hip).normalized().rotation_difference((knee-hip).normalized())
    set_global(upper,swing@up_rot,hip,poses)
    # Updating the parent rotates the child's original local head, preserving length.
    lower_bone=target.data.bones[lower]
    local_rest=target.data.bones[upper].matrix_local.inverted()@lower_bone.matrix_local
    knee=(target.matrix_world@poses[upper]@local_rest).translation
    lower_rot=world_pose(lower,poses).to_quaternion()
    original_direction=(TR[foot].translation-TR[lower].translation).normalized()
    # Rotate the rest ankle vector by current lower-leg world delta.
    current_direction=(lower_rot@TR[lower].to_quaternion().inverted())@original_direction
    swing=current_direction.rotation_difference((foot_pos-knee).normalized())
    set_global(lower,swing@lower_rot,knee,poses)

for label,source_name in clips.items():
    action=source_actions[source_name];duration=(action.frame_range[1]-action.frame_range[0])/24.0
    source.animation_data.action=action;source.animation_data.action_slot=action.slots[0]
    baked=bpy.data.actions.new('Rail_'+label);baked.use_fake_user=True;target.animation_data.action=baked
    new_actions.append(baked);count=round(duration*60);metrics=[];previous_quats={};max_lift=0.0
    for frame in range(count+1):
        t=frame/60.0;src_frame=action.frame_range[0]+min(t,duration)*24
        bpy.context.scene.frame_set(int(src_frame),subframe=src_frame-int(src_frame));bpy.context.view_layer.update()
        source_pose={n:(source.matrix_world@source.pose.bones[n].matrix).copy() for n in mapping.values()}
        for s in ['l','r']:
            for n in ['calf_'+s,'thigh_'+s,'foot_'+s]:source_pose[n]=(source.matrix_world@source.pose.bones[n].matrix).copy()
        poses={}
        for bone in target.data.bones:
            name=bone.name
            base=poses[bone.parent.name]@bone.parent.matrix_local.inverted()@bone.matrix_local if bone.parent else bone.matrix_local.copy()
            position=(target.matrix_world@base).translation
            rotation=(target.matrix_world@base).to_quaternion()
            if name in mapping:
                u=mapping[name];rotation=source_pose[u].to_quaternion()@SR[u].to_quaternion().inverted()@TR[name].to_quaternion()
                if name=='Bone':position=TR[name].translation
                elif name=='Body':position=TR[name].translation+(source_pose['pelvis'].translation-SR['pelvis'].translation)*leg_scale
                elif name.startswith('Foot.'):
                    position=TR[name].translation+(source_pose[u].translation-SR[u].translation)*leg_scale
            set_global(name,rotation,position,poses)
        for side in ['L','R']:
            foot='Foot.'+side;foot_pos=world_pose(foot,poses).translation.copy()
            leg_ik(side,foot_pos,source_pose,poses)
        for name,q in fingers.items():
            pb=target.pose.bones[name];pb.rotation_quaternion=q;bone=target.data.bones[name]
            poses[name]=bone.convert_local_to_pose(Matrix.LocRotScale(pb.location,q,Vector((1,1,1))),bone.matrix_local,parent_matrix=poses[bone.parent.name],parent_matrix_local=bone.parent.matrix_local)
        skin_matrices={name:target.matrix_world@pose@rest_inverses[name] for name,pose in poses.items()}
        minimum=min(sum(((skin_matrices[name]@point)*weight for name,weight in weights),Vector((0,0,0))).z if weights else point.z for point,weights in skin_points)
        lift=max(0.0,-minimum);max_lift=max(max_lift,lift)
        if lift>0:
            current=world_pose('Bone',poses)
            set_global('Bone',current.to_quaternion(),current.translation+Vector((0,0,lift)),poses)
        for pb in target.pose.bones:
            if pb.name in previous_quats and pb.rotation_quaternion.dot(previous_quats[pb.name])<0:pb.rotation_quaternion.negate()
            previous_quats[pb.name]=pb.rotation_quaternion.copy()
            pb.keyframe_insert('location',frame=frame,group=pb.name)
            pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name)
        if frame%6==0:metrics.append({'t':t,'floor_lift':lift,'pelvis':list(world_pose('Body',poses).translation+Vector((0,0,lift))),'left_foot':list(world_pose('Foot.L',poses).translation+Vector((0,0,lift))),'right_foot':list(world_pose('Foot.R',poses).translation+Vector((0,0,lift)))})
    report['clips'][label]={'source':source_name,'seconds':duration,'samples':count+1,'max_floor_lift':max_lift,'sampled_positions':metrics}
    print('BAKED',label,duration,count+1)

# Original clips retain their real duration when scene export moves to 60 FPS.
for action in old_actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.co.x*=2.5;key.handle_left.x*=2.5;key.handle_right.x*=2.5
target.animation_data.action=None
for track in list(target.animation_data.nla_tracks):target.animation_data.nla_tracks.remove(track)
for action in old_actions+new_actions:
    track=target.animation_data.nla_tracks.new();track.name=action.name
    strip=track.strips.new(action.name,0,action);strip.action_slot=action.slots[0]
    track.mute=False
bpy.context.scene.frame_set(0)
bpy.ops.object.select_all(action='DESELECT')
for obj in target_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=target
bpy.ops.export_scene.gltf(filepath=str(OUT/f'{character}.glb'),export_format='GLB',use_selection=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_frame_range=False,export_animations=True)
(ROOT/f'release/motion-v038/retarget-{character}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('RETARGET_CANDIDATE_EXPORTED',OUT/f'{character}.glb')
