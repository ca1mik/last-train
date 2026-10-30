"""Local CC0 base inspection; does not alter source or active characters."""
import bpy,json,shutil,math
from pathlib import Path
from mathutils import Vector
root=Path('H:/game');out=root/'release/companions-v047';out.mkdir(parents=True,exist_ok=True)
source=next((root/'source_25d/base-characters-standard').rglob('Superhero_Female_FullBody.gltf'))
working=root/'development/companions-v047/base';working.mkdir(parents=True,exist_ok=True)
data=json.loads(source.read_text())
for item in data.get('buffers',[])+data.get('images',[]):
    uri=item.get('uri')
    if not uri:continue
    actual=source.parent/uri
    if not actual.exists():actual=source.parent/uri.replace('_Normal_png','_Normal')
    assert actual.exists(),actual
    shutil.copy2(actual,working/actual.name);item['uri']=actual.name
fixed=working/source.name;fixed.write_text(json.dumps(data),encoding='utf-8')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(fixed))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
report={'blender':bpy.app.version_string,'source':str(source),'fixed_copy':str(fixed),
 'meshes':[{ 'name':o.name,'vertices':len(o.data.vertices),'bounds':[list(o.matrix_world@Vector(c)) for c in o.bound_box],
 'materials':[m.name if m else None for m in o.data.materials]} for o in meshes],
 'bones':{b.name:{'head':list(arm.matrix_world@b.head_local),'tail':list(arm.matrix_world@b.tail_local)} for b in arm.data.bones}}
(out/'inventory.json').write_text(json.dumps(report,indent=2),'utf-8')
for o in list(bpy.context.scene.objects):
    if o!=arm and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.camera_add(location=(3,-5,2.5));camera=bpy.context.object
target=Vector((0,0,.95));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=2.3;bpy.context.scene.camera=camera
for pos,energy,size in [((2,-4,5),500,4),((-3,-1,3),350,3),((0,4,4),600,3)]:
    bpy.ops.object.light_add(type='AREA',location=pos);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.resolution_x=800;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.color=(.2,.2,.2);scene.render.filepath=str(out/'base-inspection.png');bpy.ops.render.render(write_still=True)
print('COMPANION_BASE_INSPECTED',out)
