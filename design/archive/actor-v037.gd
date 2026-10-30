class_name RailActor
extends CharacterBody3D

var visual: Node3D
var animator: AnimationPlayer
var clips: Dictionary = {}
var current_clip := ""
var enemy_kind := ""
var health := 100.0
var max_health := 100.0
var facing := Vector3(0,0,1)
var attack_left := 0.0
var attack_hit := false
var dash_left := 0.0
var dash_cooldown := 0.0
var dash_direction := Vector3.ZERO
var hurt_left := 0.0
var phase := "idle"
var phase_left := 0.0
var target_direction := Vector3.FORWARD
var home := Vector3.ZERO
var path: Array[Vector3] = []
var repath := 0.0
var stun := 0.0
var corpse_time := 0.0
var ground_speed := 0.0
var alive := true
var motion_freeze := 0.0
var step_clock := 0.0
var charge_hit := false
var knockback := Vector3.ZERO
var animation_tree: AnimationTree
var action_node: AnimationNodeAnimation
var action_blend: AnimationNodeBlend2
var animation_speed := 0.0
var action_remaining := 0.0
var action_weight := 0.0
var action_elapsed := 0.0
var review_motion := false
var motion_velocity := Vector2.ZERO

func setup(kind: String, source: PackedScene) -> void:
	enemy_kind=kind
	visual=source.instantiate()
	add_child(visual)
	var height := 1.78
	if kind=="runner": height=1.85; health=80
	if kind=="brute": height=1.95; health=165
	max_health=health
	visual.scale=Vector3.ONE*(height/4.805)
	if kind=="brute": visual.scale.x*=1.22; visual.scale.z*=1.22
	if kind=="runner": visual.scale.x*=.91; visual.scale.z*=.91
	animator=find_animation(visual)
	if animator:
		for clip in animator.get_animation_list():
			for state in ["Idle","Walk","Run","Punch","SwordSlash","Death","Jump","Sitting"]:
				if clip.ends_with("Man_"+state):
					clips[state]=clip
					if state in ["Idle","Walk","Run"]: animator.get_animation(clip).loop_mode=Animation.LOOP_LINEAR
		print("ACTOR ",kind," clips=",clips.keys())
		build_animation_tree()
	var shape=CollisionShape3D.new();shape.name="BodyShape"
	var capsule=CapsuleShape3D.new();capsule.radius=.29 if kind!="brute" else .37;capsule.height=height
	shape.shape=capsule;shape.position.y=height*.5;add_child(shape)
	collision_layer=2 if kind=="" else 4
	collision_mask=1|2|4
	floor_snap_length=.25
	play("Idle")
	reset_physics_interpolation()

func find_animation(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:return node
	for child in node.get_children():
		var found=find_animation(child)
		if found:return found
	return null

func play(state: String, speed:=1.0, force:=false) -> void:
	if not animator or not clips.has(state):return
	if state in ["Idle","Walk","Run"]:
		if review_motion:
			animation_speed=0 if state=="Idle" else 1.72 if state=="Walk" else 3.9
			update_motion(.016)
			action_remaining=0;action_weight=0;animation_tree.set("parameters/action_blend/blend_amount",0.0)
		current_clip=state;return
	if current_clip==state and not force:return
	current_clip=state;action_node.animation=clips[state]
	action_remaining=animator.get_animation(clips[state]).length/maxf(speed,.01);action_elapsed=0
	action_blend.filter_enabled=state!="Death"
	animation_tree.set("parameters/action_time/scale",speed)
	animation_tree.set("parameters/action_seek/seek_request",0.0)
	if review_motion:action_weight=1.0;animation_tree.set("parameters/action_blend/blend_amount",1.0)

func face(direction: Vector3, delta: float, snap:=false) -> void:
	if direction.length_squared()<.001:return
	facing=direction.normalized()
	if snap:visual.rotation.y=atan2(facing.x,facing.z);visual.reset_physics_interpolation()

func clocks(delta: float) -> void:
	dash_cooldown=maxf(0,dash_cooldown-delta)
	hurt_left=maxf(0,hurt_left-delta)
	stun=maxf(0,stun-delta)
	attack_left=maxf(0,attack_left-delta)
	if visual and alive:visual.rotation.y=rotate_toward(visual.rotation.y,atan2(facing.x,facing.z),delta*(22.0 if attack_left>0 else 13.0))
	if animation_tree:
		action_remaining=maxf(0,action_remaining-delta);action_elapsed+=delta
		action_weight=move_toward(action_weight,1.0 if action_remaining>0 or not alive else 0.0,delta/(.065 if action_remaining>0 else .12))
		animation_tree.set("parameters/action_blend/blend_amount",action_weight)
	if not alive:
		corpse_time+=delta
		if corpse_time>2.0:
			fade_meshes(visual,clampf((corpse_time-2.0)/1.4,0,1))
		if corpse_time>3.5:queue_free()

func fade_meshes(node: Node,amount: float) -> void:
	if node is GeometryInstance3D:node.transparency=amount
	for child in node.get_children():fade_meshes(child,amount)

func move_ground(direction: Vector3,speed: float,delta: float) -> void:
	var before=global_position
	var desired=Vector2(direction.x,direction.z)*speed
	motion_velocity=desired if speed>=10 else motion_velocity.move_toward(desired,(48 if desired.length()>.1 else 62)*delta)
	velocity.x=motion_velocity.x+knockback.x;velocity.z=motion_velocity.y+knockback.z
	knockback=knockback.move_toward(Vector3.ZERO,16*delta)
	velocity.y=-1 if is_on_floor() else maxf(-14,velocity.y-28*delta)
	move_and_slide()
	ground_speed=Vector2(global_position.x-before.x,global_position.z-before.z).length()/maxf(delta,.001)
	if alive:
		animation_speed=move_toward(animation_speed,ground_speed,delta*25)
		update_motion(delta)
	if ground_speed>.2 and attack_left<=0:face(direction,delta)

func begin_attack(direction: Vector3) -> void:
	if not alive or attack_left>0 or dash_left>0 or stun>0:return
	face(direction,.016)
	attack_left=.44;attack_hit=false
	play("SwordSlash",2.4,true)

func take_hit(amount: float, force: Vector3) -> bool:
	if not alive or hurt_left>0 or dash_left>0:return false
	health-=amount;hurt_left=.26 if enemy_kind!="" else .9
	knockback=force*2.7
	if enemy_kind!="brute" or phase!="windup":stun=.18;phase="idle"
	if health<=0:
		alive=false;collision_layer=0;collision_mask=1
		play("Death",1.2,true)
	return true

func phase_aligned(source: Animation,offset: float) -> Animation:
	var result=Animation.new();result.length=1.0;result.loop_mode=Animation.LOOP_LINEAR
	for track in source.get_track_count():
		var type=source.track_get_type(track);var id=result.add_track(type)
		result.track_set_path(id,source.track_get_path(track));result.track_set_interpolation_type(id,source.track_get_interpolation_type(track));result.track_set_interpolation_loop_wrap(id,true)
		for key in source.track_get_key_count(track):
			var t=source.track_get_key_time(track,key)
			if t>=source.length-.0001:continue
			result.track_insert_key(id,fposmod(t/source.length-offset,1.0),source.track_get_key_value(track,key))
		var sample_time=offset*source.length
		if type==Animation.TYPE_POSITION_3D:result.track_insert_key(id,0.0,source.position_track_interpolate(track,sample_time))
		elif type==Animation.TYPE_ROTATION_3D:result.track_insert_key(id,0.0,source.rotation_track_interpolate(track,sample_time))
		elif type==Animation.TYPE_SCALE_3D:result.track_insert_key(id,0.0,source.scale_track_interpolate(track,sample_time))
	return result

func soften_tool_arm(run: Animation,walk: Animation) -> void:
	# Keep the railway key close to the body instead of flinging it above the shoulder.
	for track in run.get_track_count():
		var path=run.track_get_path(track);var name=String(path).get_slice(":",1)
		if run.track_get_type(track)!=Animation.TYPE_ROTATION_3D or not name.ends_with(".R") or not ("Arm" in name or "Palm" in name or "Finger" in name or "Thumb" in name):continue
		var other=walk.find_track(path,Animation.TYPE_ROTATION_3D)
		if other<0:continue
		var rotations: Array[Quaternion]=[]
		for i in range(61):rotations.append(run.rotation_track_interpolate(track,i/60.0).slerp(walk.rotation_track_interpolate(other,i/60.0),.65))
		for i in range(run.track_get_key_count(track)-1,-1,-1):run.track_remove_key(track,i)
		for i in range(61):run.track_insert_key(track,i/60.0,rotations[i])

func clip_node(name: String) -> AnimationNodeAnimation:
	var node=AnimationNodeAnimation.new();node.animation=name;return node

func build_animation_tree() -> void:
	# Contact phases measured from Foot.L in the imported clips, not guessed by FPS.
	var walk=phase_aligned(animator.get_animation(clips["Walk"]),0.0);var run=phase_aligned(animator.get_animation(clips["Run"]),.32)
	soften_tool_arm(run,walk)
	var library=AnimationLibrary.new();library.add_animation("RunAligned",run);library.add_animation("WalkAligned",walk);animator.add_animation_library("rail",library)
	var blend_tree=AnimationNodeBlendTree.new()
	var space=AnimationNodeBlendSpace1D.new();space.min_space=1.72;space.max_space=3.9;space.sync_mode=AnimationNodeBlendSpace1D.SYNC_MODE_CYCLIC_CONSTANT;space.cyclic_length=1.0
	space.add_blend_point(clip_node("rail/WalkAligned"),1.72,-1,&"walk");space.add_blend_point(clip_node("rail/RunAligned"),3.9,-1,&"run")
	blend_tree.add_node("locomotion",space);blend_tree.add_node("locomotion_time",AnimationNodeTimeScale.new());blend_tree.connect_node("locomotion_time",0,"locomotion")
	blend_tree.add_node("idle",clip_node(clips["Idle"]))
	var movement=AnimationNodeBlend2.new();movement.sync=true;blend_tree.add_node("movement",movement);blend_tree.connect_node("movement",0,"idle");blend_tree.connect_node("movement",1,"locomotion_time")
	action_node=clip_node(clips["SwordSlash"]);blend_tree.add_node("action",action_node);blend_tree.add_node("action_seek",AnimationNodeTimeSeek.new());blend_tree.connect_node("action_seek",0,"action");blend_tree.add_node("action_time",AnimationNodeTimeScale.new());blend_tree.connect_node("action_time",0,"action_seek")
	action_blend=AnimationNodeBlend2.new();action_blend.sync=true
	var attack=animator.get_animation(clips["SwordSlash"])
	for i in attack.get_track_count():
		var path=attack.track_get_path(i);var bone=String(path).get_slice(":",1)
		if bone in ["Torso","Neck","Head"] or "Arm" in bone or "Palm" in bone or "Finger" in bone or "Thumb" in bone:action_blend.set_filter_path(path,true)
	blend_tree.add_node("action_blend",action_blend);blend_tree.connect_node("action_blend",0,"movement");blend_tree.connect_node("action_blend",1,"action_time");blend_tree.connect_node("output",0,"action_blend")
	animation_tree=AnimationTree.new();animation_tree.name="AnimationTree";add_child(animation_tree);animation_tree.anim_player=animation_tree.get_path_to(animator);animation_tree.tree_root=blend_tree;animation_tree.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL;animation_tree.active=true
	animation_tree.set("parameters/action_blend/blend_amount",0.0);animation_tree.set("parameters/movement/blend_amount",0.0)

func update_motion(_delta: float) -> void:
	if not animation_tree:return
	var weight=clampf((animation_speed-1.72)/(3.9-1.72),0,1)
	var stride=lerpf(1.72*1.041667,3.9*.875,weight)
	animation_tree.set("parameters/locomotion/blend_position",clampf(animation_speed,1.72,3.9))
	animation_tree.set("parameters/locomotion_time/scale",clampf(animation_speed/stride,0.0,1.8))
	animation_tree.set("parameters/movement/blend_amount",smoothstep(.08,.65,animation_speed))

func advance_pose(delta: float) -> void:
	if animation_tree:animation_tree.advance(delta)
