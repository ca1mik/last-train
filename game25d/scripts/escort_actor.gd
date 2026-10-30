class_name EscortActor
extends CharacterBody3D
## Noncombatant native-mesh actor. Identity/asset approval is owned by the scene.
var actor_id:=""
var model: Node3D
var animator: AnimationPlayer
var animation_tree: AnimationTree
var clips: Dictionary={}
var seated:=false
var movement_weight:=0.0
var ground_speed:=0.0
var height:=1.7
var step_clock:=0.0
var seating_left:=0.0
var seating_duration:=1.0
var seating_from:=Vector3.ZERO
var seating_to:=Vector3.ZERO
var seating_done: Callable
var sit_offset:=Vector3.ZERO
var walk_clock:=0.0
var footfall:=false
var path: Array[Vector3]=[]
var repath:=0.0
var last_target:=Vector3.INF
var interaction_left:=0.0

func setup(id: String,path: String,metres: float,source_height:=0.0) -> void:
	actor_id=id;height=metres;name="Escort_"+id
	model=load(path).instantiate();add_child(model)
	if source_height>0:model.scale=Vector3.ONE*(metres/source_height)
	animator=find_player(model);assert(animator!=null)
	animator.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	for clip in animator.get_animation_list():
		for state in ["Idle","Walk","Sit","Enter","Interact","Push"]:
			if String(clip).ends_with("Escort_"+state) or String(clip).ends_with("Man_"+("Sitting" if state=="Sit" else state)):
				clips[state]=clip
	assert(clips.has("Idle") and clips.has("Walk"))
	if clips.has("Sit"):
		animator.play(clips.Sit);animator.advance(0);animator.seek(.2,true)
		var skeleton=preload("res://scripts/carry_ik.gd").new().find_skeleton(model)
		if skeleton:
			skeleton.force_update_all_bone_transforms();var pelvis=skeleton.find_bone("pelvis")
			if pelvis<0:pelvis=skeleton.find_bone("Hips")
			if pelvis>=0:sit_offset=skeleton.global_transform*skeleton.get_bone_global_pose(pelvis).origin-global_position;sit_offset.y=0
		animator.stop()
	for state in ["Idle","Walk","Sit"]:
		if clips.has(state):animator.get_animation(clips[state]).loop_mode=Animation.LOOP_LINEAR
	var tree=AnimationNodeBlendTree.new()
	for state in ["Idle","Walk"]:
		var node=AnimationNodeAnimation.new();node.animation=clips[state];tree.add_node(state.to_lower(),node)
	tree.add_node("walk_seek",AnimationNodeTimeSeek.new());tree.connect_node("walk_seek",0,"walk")
	tree.add_node("walk_rate",AnimationNodeTimeScale.new());tree.connect_node("walk_rate",0,"walk_seek")
	var movement=AnimationNodeBlend2.new();movement.sync=true;tree.add_node("movement",movement);tree.connect_node("movement",0,"idle");tree.connect_node("movement",1,"walk_rate");tree.connect_node("output",0,"movement")
	animation_tree=AnimationTree.new();add_child(animation_tree);animation_tree.anim_player=animation_tree.get_path_to(animator);animation_tree.tree_root=tree;animation_tree.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL;animation_tree.active=true
	walk_clock=fposmod(absf(float(id.hash()))*.013,animator.get_animation(clips.Walk).length)
	animation_tree.set("parameters/walk_seek/seek_request",walk_clock)
	var shape=CollisionShape3D.new();shape.name="EscortShape";var capsule=CapsuleShape3D.new();capsule.radius=.26;capsule.height=height;shape.shape=capsule;shape.position.y=height*.5;add_child(shape)
	collision_layer=8;collision_mask=1|2|4|8;floor_snap_length=.3
	step_clock=fposmod(float(id.hash()),.42);reset_physics_interpolation();advance_pose(.016)

func find_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:return node
	for child in node.get_children():
		var found=find_player(child)
		if found:return found
	return null

func move_direction(direction: Vector3,speed: float,delta: float) -> void:
	if seated or seating_left>0:advance_pose(delta);return
	var desired=direction.normalized()*speed if direction.length()>.01 else Vector3.ZERO
	var horizontal=Vector3(velocity.x,0,velocity.z).move_toward(desired,delta*(8.0 if desired.length()>.01 else 12.0))
	velocity=Vector3(horizontal.x,-1 if is_on_floor() else velocity.y-25*delta,horizontal.z)
	move_and_slide();ground_speed=Vector2(get_real_velocity().x,get_real_velocity().z).length()
	if horizontal.length()>.12:rotation.y=lerp_angle(rotation.y,atan2(horizontal.x,horizontal.z),1-exp(-12*delta))
	advance_pose(delta)

func advance_pose(delta: float) -> void:
	footfall=false
	if interaction_left>0:
		animation_tree.active=false;interaction_left=maxf(0,interaction_left-delta);animator.advance(delta);return
	if seating_left>0:
		animation_tree.active=false;seating_left=maxf(0,seating_left-delta)
		position=seating_from.lerp(seating_to,smoothstep(0.0,1.0,1-seating_left/seating_duration));animator.advance(delta)
		if seating_left<=0:
			seated=true;position=seating_to
			if seating_done.is_valid():seating_done.call()
		return
	if seated:
		animation_tree.active=false
		var clip=clips.get("Sit",clips.Idle)
		if animator.current_animation!=clip:animator.play(clip)
		animator.advance(delta);return
	animation_tree.active=true
	movement_weight=move_toward(movement_weight,1.0 if ground_speed>.12 else 0.0,delta/.16)
	var duration=animator.get_animation(clips.Walk).length
	var stride=1.25*height/1.78
	animation_tree.set("parameters/movement/blend_amount",movement_weight)
	var rate=clampf(ground_speed*duration/stride,0,2.3)
	animation_tree.set("parameters/walk_rate/scale",rate)
	var step=int(floor(walk_clock/(duration*.5)));walk_clock+=rate*delta;footfall=ground_speed>.3 and int(floor(walk_clock/(duration*.5)))>step
	animation_tree.advance(delta)

func begin_interaction(seconds: float) -> void:
	interaction_left=seconds;animation_tree.active=false;animator.play(clips.get("Interact",clips.Idle));animator.advance(0)

func sit_at(point: Vector3,yaw: float) -> void:
	position=point;rotation.y=yaw;seated=true;velocity=Vector3.ZERO;ground_speed=0
	get_node("EscortShape").set_deferred("disabled",true);advance_pose(.016);reset_physics_interpolation()

func begin_sitting(point: Vector3,yaw: float,done: Callable) -> void:
	if seated or seating_left>0:return
	seating_from=position;seating_to=point;rotation.y=yaw;seating_done=done;velocity=Vector3.ZERO;ground_speed=0
	animation_tree.active=false;var clip=clips.get("Enter",clips.get("Sit",clips.Idle));animator.play(clip);animator.advance(0)
	seating_duration=animator.get_animation(clip).length if clips.has("Enter") else .8;seating_left=seating_duration
	get_node("EscortShape").set_deferred("disabled",true)
