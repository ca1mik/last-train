extends SceneTree
## Review-only casts. Excluded from exports; no campaign or accepted design change.
class ReviewWorld extends "res://scripts/main.gd":
	func _ready() -> void:
		set_physics_process(false);set_process(false);setup_world()
		block(Vector3(0,-.15,0),Vector3(18,.3,16),Color("63746c"),true)
		for i in range(-6,7):
			block(Vector3(i,.003,0),Vector3(.012,.005,12),Color("75857a"))
			block(Vector3(0,.003,i),Vector3(12,.005,.012),Color("75857a"))
		hero=spawn_actor("",Vector3(-2.4,0,0));hero.advance_pose(.6)
		for x in [1.8,2.95]:block(Vector3(x,1.075,0),Vector3(.12,2.15,.15),Color("263f3b"))
		block(Vector3(2.375,2.21,0),Vector3(1.27,.12,.15),Color("263f3b"))
		setup_camera()
var world: Node3D
var candidate: Node3D
var player: AnimationPlayer
var output: String
var caption: Label
var role:="nina"
var normal_bias:=-1.0
var records: Array=[]
func _initialize() -> void:start.call_deferred()
func find_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:return node
	for child in node.get_children():
		var found=find_player(child)
		if found:return found
	return null
func pose(state: String,time: float) -> void:
	for name in player.get_animation_list():
		if String(name).ends_with("Escort_"+state):player.play(name);player.advance(0);player.seek(time,true);return
	push_error("Missing candidate pose "+state)
func shot(name: String) -> void:
	caption.text="КАНДИДАТ · "+role.to_upper()+" · "+name+" · ОБЛИК НЕ УТВЕРЖДЁН"
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name+".png"));records.append(name+".png")
func start() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--role="):role=arg.trim_prefix("--role=")
		if arg.begins_with("--shadow-normal="):normal_bias=float(arg.trim_prefix("--shadow-normal="))
	output="H:/game/release/companions-v047/"+role+ ("-shadowless" if OS.get_cmdline_user_args().has("--no-shadows") else "-bias-"+str(normal_bias) if normal_bias>=0 else "");DirAccess.make_dir_recursive_absolute(output)
	world=ReviewWorld.new();root.add_child(world);current_scene=world
	for child in world.get_children():
		if child is DirectionalLight3D:
			child.light_color=Color.WHITE;child.light_energy=1.1
			print("REVIEW_SHADOW_DEFAULT ",child.shadow_bias," ",child.shadow_normal_bias)
			if normal_bias>=0:child.shadow_normal_bias=normal_bias
			if OS.get_cmdline_user_args().has("--no-shadows"):child.shadow_enabled=false
		if child is WorldEnvironment:child.environment.ambient_light_color=Color.WHITE;child.environment.ambient_light_energy=.65
	candidate=load("res://review_assets/companions-v047/"+role+".glb").instantiate();world.add_child(candidate);player=find_player(candidate)
	assert(player!=null);player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var ui=CanvasLayer.new();world.add_child(ui);caption=Label.new();ui.add_child(caption);caption.position=Vector2(40,35);caption.add_theme_font_size_override("font_size",25)
	caption.add_theme_color_override("font_color",Color("f2dec1"))
	pose("Idle",.2)
	var center=Vector3(0,.9,0);world.camera.size=2.3;world.camera.position=Vector3(0,1.2,6);world.camera.look_at(center)
	for i in range(8):
		candidate.rotation.y=i*PI/4;await shot("neutral-%02d"%i)
	candidate.rotation.y=0;world.camera.size=5.6;world.camera.position=center+world.camera_offset;world.camera.look_at(center)
	await shot("gameplay-scale")
	world.camera.size=2.5;await shot("gameplay-close")
	pose("Walk",.3);await shot("walk-contact")
	pose("Sit",.3);await shot("sitting")
	var report={"role":role,"status":"unapproved review candidate","source_sha256":FileAccess.get_sha256("res://review_assets/companions-v047/"+role+".glb"),"clips":player.get_animation_list(),"images":records,"gpu":RenderingServer.get_video_adapter_name(),"scope":"staged poses/scale/neutral and gameplay camera; no walking path or final art acceptance"}
	var file=FileAccess.open(output.path_join("manifest.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	world.queue_free();await process_frame;await process_frame
	var until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<until:await process_frame
	quit()
