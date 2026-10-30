"""CC0 mesh/wardrobe/animation candidates. Review assets only, not approved cast."""
import bpy,bmesh,math,json,sys,shutil
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path('H:/game');OUT=ROOT/'game25d/review_assets/companions-v047'
PROOF=ROOT/'release/companions-v047';OUT.mkdir(parents=True,exist_ok=True);PROOF.mkdir(parents=True,exist_ok=True)
role='nina'
for arg in sys.argv:
    if arg.startswith('--role='):role=arg.split('=',1)[1]
SPECS={
 'nina':dict(height=1.70,coat=(.29,.18,.07),pants=(.075,.12,.18),hair=(.045,.035,.028),hem=.90,bob=True),
 'lida':dict(height=1.65,coat=(.16,.22,.135),pants=(.08,.10,.105),hair=(.36,.37,.33),hem=.79,braid=True),
 'raisa':dict(height=1.61,coat=(.075,.12,.17),pants=(.17,.17,.16),hair=(.43,.43,.39),hem=.48,bun=True),
}
assert role in SPECS
spec=SPECS[role]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
source=ROOT/'development/companions-v047/base/Superhero_Female_FullBody.gltf'
bpy.ops.import_scene.gltf(filepath=str(source))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');arm.name='CompanionRig'
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
for o in list(bpy.context.scene.objects):
    if o!=arm and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
body=max(meshes,key=lambda o:len(o.data.vertices))
TR={b.name:(arm.matrix_world@b.matrix_local).copy() for b in arm.data.bones}
inverse=arm.matrix_world.inverted()
def material(name,color,metal=0):
    m=bpy.data.materials.new(role+' · '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.87;bs.inputs['Metallic'].default_value=metal
    return m
coat=material('canvas coat',spec['coat']);pants=material('trousers',spec['pants']);hair=material('hair',spec['hair'])
shirt=material('cotton shirt',(.52,.51,.43));leather=material('worn leather',(.115,.072,.035));sole=material('rubber soles',(.028,.034,.026))
scarf=material('burgundy wool',(.245,.055,.065));gold=material('spectacle metal',(.34,.25,.11),.7);paper=material('folder',(.52,.49,.38))
for o in meshes:
    if 'Eyebrow' in o.name:o.data.materials.clear();o.data.materials.append(hair)
groups={g.index:g.name for g in body.vertex_groups}
head_points=[body.matrix_world@v.co for v in body.data.vertices if sum(g.weight for g in v.groups if groups[g.group]=='Head')>.5]
head_min=Vector(tuple(min(p[i] for p in head_points) for i in range(3)));head_max=Vector(tuple(max(p[i] for p in head_points) for i in range(3)))
head_center=(head_min+head_max)*.5;head_radius=(head_max-head_min)*.5
def skinned(name,verts,faces,mat,weights):
    data=bpy.data.meshes.new(name);data.from_pydata([inverse@Vector(v) for v in verts],[],faces);data.materials.append(mat);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);obj.parent=arm;obj.matrix_parent_inverse=Matrix.Identity(4)
    names={n for row in weights for n in row};vg={n:obj.vertex_groups.new(name=n) for n in names}
    for i,row in enumerate(weights):
        total=sum(row.values())
        for n,w in row.items():vg[n].add([i],w/total,'REPLACE')
    mod=obj.modifiers.new('Preserved 63-bone skeleton','ARMATURE');mod.object=arm
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(data);bm.free()
    for p in data.polygons:p.use_smooth=True
    meshes.append(obj);return obj
def box(name,center,size,mat,bone):
    c=Vector(center);s=Vector(size)*.5
    verts=[c+Vector((x*s.x,y*s.y,z*s.z)) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    obj=skinned(name,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,[{bone:1}]*8)
    for p in obj.data.polygons:p.use_smooth=False
    return obj
def ellipsoid(name,center,radius,mat,bone,segments=16,rings=8):
    c=Vector(center);r=Vector(radius);verts=[]
    for j in range(rings+1):
        t=.001+(math.pi-.002)*j/rings
        for i in range(segments):
            a=i*math.tau/segments;verts.append(c+Vector((r.x*math.sin(t)*math.cos(a),r.y*math.sin(t)*math.sin(a),r.z*math.cos(t))))
    faces=[(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i) for j in range(rings) for i in range(segments)]
    return skinned(name,verts,faces,mat,[{bone:1}]*len(verts))
def tube(name,a,b,radius,mat,bone,sides=8):
    a=Vector(a);b=Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
    if u.length<.01:u=axis.cross(Vector((0,1,0)))
    u.normalize();v=axis.cross(u).normalized();verts=[p+(u*math.cos(i*math.tau/sides)+v*math.sin(i*math.tau/sides))*radius for p in [a,b] for i in range(sides)]
    return skinned(name,verts,[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)],mat,[{bone:1}]*len(verts))
def torso_weights(z,x):
    if z>=1.28:return {'spine_03':1}
    if z>=1.10:return {'spine_01':.6,'spine_03':.4}
    if z>=.86:return {'pelvis':.65,'spine_01':.35}
    side='l' if x>0 else 'r';w=.3*min(1,(.86-z)/.35)
    return {'pelvis':1-w,'thigh_'+side:w}
def torso():
    # A loose clothing envelope bridges the body surface. It must not copy
    # superhero muscles/breast contours into ordinary workwear.
    width=1.12 if role=='raisa' else 1.04 if role=='lida' else 1.0
    profile=[(spec['hem'],.200*width,.142*width),(1.02,.183*width,.141*width),(1.18,.190*width,.146*width),(1.29,.199*width,.148*width),(1.37,.200,.125),(1.42,.190,.111),(1.47,.110,.084),(1.49,.067,.071)]
    verts=[];weights=[];segments=40
    for z,rx,ry in profile:
        for i in range(segments):
            a=i*math.tau/segments;x=rx*math.cos(a);verts.append((x,.014+ry*math.sin(a),z));row=torso_weights(z,x)
            if z>1.35 and abs(x)>.11:
                influence=min(.45,(abs(x)-.11)*4);side='l' if x>0 else 'r';row={'spine_03':1-influence,'clavicle_'+side:influence}
            weights.append(row)
    faces=[(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i) for j in range(len(profile)-1) for i in range(segments)]
    obj=skinned('Loose work coat',verts,faces,coat,weights)
    obj.data.materials.append(shirt)
    if role=='nina':
        for p in obj.data.polygons:
            c=sum((Vector(verts[v]) for v in p.vertices),Vector())/len(p.vertices)
            if c.y<-.08 and abs(c.x)<.065 and c.z>1.05:p.material_index=1
    for side in ['l','r']:
        shoulder=TR['upperarm_'+side].translation;elbow=TR['lowerarm_'+side].translation;hand=TR['hand_'+side].translation
        end=elbow.lerp(hand,.57 if role=='nina' else .94)
        rings=[shoulder,shoulder.lerp(elbow,.5),elbow,end];radii=[.069,.066,.060,.054];vs=[];ws=[]
        for j,p in enumerate(rings):
            for i in range(20):
                a=i*math.tau/20;vs.append(p+Vector((0,math.cos(a)*radii[j],math.sin(a)*radii[j])))
                ws.append({'clavicle_'+side:.25,'upperarm_'+side:.75} if j==0 else {'upperarm_'+side:1} if j==1 else {'upperarm_'+side:.4,'lowerarm_'+side:.6} if j==2 else {'lowerarm_'+side:1})
        skinned('Work sleeve '+side,vs,[(j*20+i,j*20+(i+1)%20,(j+1)*20+(i+1)%20,(j+1)*20+i) for j in range(3) for i in range(20)],coat,ws)
        if role=='nina':ellipsoid('Rolled light cuff '+side,end,(.022,.058,.058),shirt,'lowerarm_'+side,12,6)
    # Small front construction details sit over, rather than inside, the coat.
    for sign in [-1,1]:
        skinned('Lapel '+str(sign),[(sign*.04,-.082,1.47),(sign*.13,-.15,1.35),(sign*.065,-.176,1.28)],[(0,1,2)],coat,[{'spine_03':1}]*3)
        box('Hip pocket '+str(sign),(sign*.115,-.165,1.0),(.085,.014,.10),coat,'pelvis')
    for z in [1.08,1.19,1.30]:ellipsoid('Button',(0,-.174,z),(.009,.006,.009),leather,'spine_01' if z<1.2 else 'spine_03',8,4)
torso()
for side in ['l','r']:
    hip=TR['thigh_'+side].translation;knee=TR['calf_'+side].translation;ankle=TR['foot_'+side].translation
    vs=[];ws=[]
    for j,(point,radius) in enumerate([(hip,.105),(hip.lerp(knee,.5),.092),(knee,.078),(ankle+Vector((0,0,.05)),.060)]):
        for i in range(16):
            a=i*math.tau/16;vs.append(point+Vector((math.cos(a)*radius,math.sin(a)*radius,0)))
            ws.append({'thigh_'+side:1} if j<2 else {'thigh_'+side:.35,'calf_'+side:.65} if j==2 else {'calf_'+side:1})
    skinned('Loose trouser '+side,vs,[(j*16+i,j*16+(i+1)%16,(j+1)*16+(i+1)%16,(j+1)*16+i) for j in range(3) for i in range(16)],pants,ws)
    foot=TR['foot_'+side].translation
    ellipsoid('Boot '+side,foot+Vector((0,-.055,-.012)),(.073,.151,.072),leather,'foot_'+side)
    ellipsoid('Sole '+side,foot+Vector((0,-.055,-.052)),(.075,.153,.025),sole,'foot_'+side)
    vs=[]
    for z,r in [(foot.z,.066),(foot.z+.15,.064)]:
        for i in range(16):vs.append((foot.x+math.cos(i*math.tau/16)*r,foot.y+math.sin(i*math.tau/16)*r,z))
    skinned('Laced ankle boot '+side,vs,[(i,(i+1)%16,(i+1)%16+16,i+16) for i in range(16)],leather,[{'calf_'+side:.75,'foot_'+side:.25}]*32)
    for y in [-.11,-.085,-.06]:tube('Boot fastening',foot+Vector((-.037,y,.035)),foot+Vector((.037,y,.035)),.0038,sole,'foot_'+side)
# Remove hidden muscular body surfaces: clothes have their own volume, not skin paint.
bm=bmesh.new();bm.from_mesh(body.data);bm.faces.ensure_lookup_table();delete=[]
for face in bm.faces:
    original=body.data.polygons[face.index];scores={}
    for vi in original.vertices:
        for g in body.data.vertices[vi].groups:scores[groups[g.group]]=scores.get(groups[g.group],0)+g.weight
    dominant=max(scores,key=scores.get) if scores else ''
    p=body.matrix_world@face.calc_center_median()
    keep=(dominant in ['Head','neck_01','neck_02'] and p.z>1.48) or 'hand_' in dominant or any(s in dominant for s in ['thumb','index','middle','ring','pinky'])
    if role=='nina' and 'lowerarm' in dominant and abs(p.x)>.52:keep=True
    if not keep:delete.append(face)
bmesh.ops.delete(bm,geom=delete,context='FACES_ONLY');bm.to_mesh(body.data);bm.free()
# The local CC0 hair pack has a proper jaw-length silhouette and head surface.
# Preserve its geometry, bind it to this exact Head; no helmet/earmuff ellipsoids.
c=head_center;r=head_radius+Vector((.010,.011,.012))
hair_name='Hair_Long' if role=='nina' else 'Hair_BuzzedFemale'
hair_path=next(p for p in (ROOT/'source_25d/base-characters-standard').rglob(hair_name+'.gltf') if 'Origin at 0' in str(p))
before_hair=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(hair_path))
hair_objects=[o for o in bpy.data.objects if o not in before_hair]
for obj in hair_objects:
    if obj.type=='MESH':
        coords=[obj.matrix_world@v.co for v in obj.data.vertices];polygons=[tuple(p.vertices) for p in obj.data.polygons]
        skinned('Bound '+hair_name,coords,polygons,hair,[{'Head':1}]*len(coords))
for obj in hair_objects:bpy.data.objects.remove(obj,do_unlink=True)
if spec.get('braid'):
    for i in range(5):ellipsoid('Short braid '+str(i),c+Vector((.009*(-1 if i%2 else 1),r.y+.014,-.04-i*.031)),(.030-i*.002,.026-i*.002,.027),hair,'Head',12,6)
if spec.get('bun'):ellipsoid('Low gray bun',c+Vector((0,r.y+.028,-.015)),(.059,.052,.052),hair,'Head')
if role in ['lida','raisa']:
    # Identity from existing scarves; geometric folds follow the torso/neck.
    vs=[];ws=[]
    for z,rx,ry in [(1.40,.105,.104),(1.46,.090,.093),(1.49,.079,.083)]:
        for i in range(20):
            a=i*math.tau/20;vs.append((math.cos(a)*rx,.015+math.sin(a)*ry,z));ws.append({'spine_03':.6,'neck_01':.4})
    skinned('Wool scarf collar',vs,[(j*20+i,j*20+(i+1)%20,(j+1)*20+(i+1)%20,(j+1)*20+i) for j in range(2) for i in range(20)],scarf,ws)
    skinned('Scarf ends',[(-.055,-.118,1.43),(.05,-.118,1.43),(.07,-.172,1.04),(-.02,-.175,1.06)],[(0,1,2,3)],scarf,[{'spine_03':1},{'spine_03':1},{'spine_01':1},{'spine_01':1}])
if role=='raisa':
    for sign in [-1,1]:
        points=[Vector((sign*.032+math.cos(i*math.tau/20)*.028,-.174,1.20+math.sin(i*math.tau/20)*.018)) for i in range(20)]
        for i in range(20):tube('Spectacle rim',points[i],points[(i+1)%20],.0015,gold,'spine_03',6)
        tube('Spectacle cord',(sign*.055,-.12,1.42),(sign*.055,-.174,1.20),.0018,leather,'spine_03',6)
    tube('Spectacle bridge',(-.004,-.174,1.20),(.004,-.174,1.20),.0015,gold,'spine_03',6)
# Retarget against both actual rest matrices. No skeleton/body scaling keys.
before=set(bpy.data.objects);old_actions=set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=str(next((ROOT/'source_25d/ual-standard').rglob('UAL1_Standard.glb'))))
source_arm=next(o for o in bpy.data.objects if o not in before and o.type=='ARMATURE')
source_objects=[o for o in bpy.data.objects if o not in before]
source_actions={a.name:a for a in bpy.data.actions if a not in old_actions}
for obj in [arm,source_arm]:
    if obj.animation_data:
        for track in obj.animation_data.nla_tracks:track.mute=True
SR={b.name:(source_arm.matrix_world@b.matrix_local).copy() for b in source_arm.data.bones}
leg_scale=((TR['calf_l'].translation-TR['thigh_l'].translation).length+(TR['foot_l'].translation-TR['calf_l'].translation).length)/((SR['calf_l'].translation-SR['thigh_l'].translation).length+(SR['foot_l'].translation-SR['calf_l'].translation).length)
def set_global(name,rotation,position,poses):
    bone=arm.data.bones[name];world=Matrix.LocRotScale(position,rotation,TR[name].to_scale());kwargs={}
    if bone.parent:kwargs={'parent_matrix':poses[bone.parent.name],'parent_matrix_local':bone.parent.matrix_local}
    basis=bone.convert_local_to_pose(inverse@world,bone.matrix_local,invert=True,**kwargs)
    pb=arm.pose.bones[name];pb.location=basis.translation;pb.rotation_mode='QUATERNION';pb.rotation_quaternion=basis.to_quaternion();pb.scale=(1,1,1)
    poses[name]=bone.convert_local_to_pose(Matrix.LocRotScale(pb.location,pb.rotation_quaternion,Vector((1,1,1))),bone.matrix_local,**kwargs)
actions=[];clip_report={};scene=bpy.context.scene;scene.render.fps=30
for label,name in {'Idle':'Idle_Loop','Walk':'Walk_Loop','Sit':'Sitting_Idle_Loop','Enter':'Sitting_Enter','Interact':'Interact','Push':'Push_Loop'}.items():
    source_action=source_actions[name];duration=(source_action.frame_range[1]-source_action.frame_range[0])/24.0
    source_arm.animation_data.action=source_action;source_arm.animation_data.action_slot=source_action.slots[0]
    baked=bpy.data.actions.new('Escort_'+label);arm.animation_data_create();arm.animation_data.action=baked
    count=round(duration*30);previous={}
    for frame in range(count+1):
        src=source_action.frame_range[0]+min(duration,frame/30)*24;scene.frame_set(int(src),subframe=src-int(src));bpy.context.view_layer.update()
        poses={}
        for bone in arm.data.bones:
            n=bone.name;base=poses[bone.parent.name]@bone.parent.matrix_local.inverted()@bone.matrix_local if bone.parent else bone.matrix_local.copy()
            pos=(arm.matrix_world@base).translation;rot=(arm.matrix_world@base).to_quaternion()
            if n in SR:
                current=source_arm.matrix_world@source_arm.pose.bones[n].matrix;rot=current.to_quaternion()@SR[n].to_quaternion().inverted()@TR[n].to_quaternion()
                if n=='pelvis':pos=TR[n].translation+(current.translation-SR[n].translation)*leg_scale
                if n=='root':pos=TR[n].translation
            set_global(n,rot,pos,poses)
        for bone in arm.pose.bones:
            q=bone.rotation_quaternion
            if bone.name in previous and q.dot(previous[bone.name])<0:bone.rotation_quaternion=-q
            previous[bone.name]=bone.rotation_quaternion.copy()
            bone.keyframe_insert('location',frame=frame);bone.keyframe_insert('rotation_quaternion',frame=frame)
    actions.append(baked);clip_report[label]={'frames':count+1,'seconds':duration}
    print('COMPANION_CLIP',role,label,count+1,flush=True)
idle=actions[0];arm.animation_data.action=idle;arm.animation_data.action_slot=idle.slots[0];scene.frame_set(0);bpy.context.view_layer.update()
def posed_prop(name,center,size,mat,bone):
    c=Vector(center);s=Vector(size)*.5;pose=arm.matrix_world@arm.pose.bones[bone].matrix
    verts=[TR[bone]@pose.inverted()@(c+Vector((x*s.x,y*s.y,z*s.z))) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    obj=skinned(name,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,[{bone:1}]*8)
    for p in obj.data.polygons:p.use_smooth=False
if role=='nina':posed_prop('Reference folder',(arm.matrix_world@arm.pose.bones['hand_l'].matrix).translation+Vector((0,-.018,.11)),(.20,.035,.28),paper,'hand_l')
if role=='raisa':posed_prop('Personal document',(arm.matrix_world@arm.pose.bones['hand_r'].matrix).translation+Vector((0,-.018,.045)),(.080,.017,.12),scarf,'hand_r')
for obj in source_objects:bpy.data.objects.remove(obj,do_unlink=True)
for action in source_actions.values():
    if action.users==0:bpy.data.actions.remove(action)
for track in list(arm.animation_data.nla_tracks):arm.animation_data.nla_tracks.remove(track)
arm.animation_data.action=None
for action in actions:
    track=arm.animation_data.nla_tracks.new();track.name=action.name;strip=track.strips.new(action.name,0,action);strip.action_frame_start=action.frame_range[0];strip.action_frame_end=action.frame_range[1]
# Normalize once at the exported model root, keeping bone lengths and keyframes.
wrapper=bpy.data.objects.new(role+' candidate metres',None);bpy.context.collection.objects.link(wrapper)
arm.parent=wrapper;arm.matrix_parent_inverse=Matrix.Identity(4)
height=head_max.z-min((o.matrix_world@Vector(c)).z for o in meshes for c in o.bound_box)
wrapper.scale=(spec['height']/height,)*3
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT');wrapper.select_set(True);arm.select_set(True)
for obj in meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=arm
path=OUT/(role+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_animations=True,export_nla_strips=True,export_animation_mode='NLA_TRACKS')
report={'role':role,'status':'proposal; not approved; review-only asset','reference':'assets/characters/'+role+'-idle-v01.png','source':str(source),'license':'Quaternius Universal Base Characters Standard CC0; UAL Standard CC0','blender':bpy.app.version_string,'height_metres_proposed':spec['height'],'head_bounds_source':[list(head_min),list(head_max)],'bone_count':len(arm.data.bones),'rest_mapping':'source_pose * inverse(source_rest) * target_rest; per-target hierarchy positions; leg-scaled pelvis delta; no bone scales','clips':clip_report,'limits':'candidate wardrobe, ages, hand contacts, foot contacts and deformation require engine review; no artistic acceptance','output':str(path)}
(PROOF/(role+'-build.json')).write_text(json.dumps(report,indent=2),'utf-8')
print('COMPANION_CANDIDATE_EXPORTED',role,path,flush=True)
