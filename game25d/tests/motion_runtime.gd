extends SceneTree
var game: Node3D
var held: Dictionary={}
var elapsed := 0.0
var samples: Array=[]
var flags: Dictionary={}
var close := false
var skeleton: Skeleton3D
var output := "H:/game/release/motion-v038/runtime"
var capture_frames := false

func _initialize() -> void:start.call_deferred()
func key(code: int,down: bool) -> void:
	if held.get(code,false)==down and Input.is_physical_key_pressed(code)==down:return
	held[code]=down;var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=down;event.ctrl_pressed=held.get(KEY_CTRL,false);event.shift_pressed=held.get(KEY_SHIFT,false);Input.parse_input_event(event)

func click() -> void:
	var point=game.camera.unproject_position(game.hero.position+game.hero.facing*2+Vector3.UP*.7)
	var event=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.position=point;event.pressed=true;root.push_input(event,true)
	var released=InputEventMouseButton.new();released.button_index=MOUSE_BUTTON_LEFT;released.position=point;released.pressed=false;root.push_input(released,true)

func once(id: String) -> bool:
	if flags.has(id):return false
	flags[id]=true;return true

func start() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg=="--motion-close":close=true;output+="-close"
		if arg.begins_with("--motion-output="):output=arg.trim_prefix("--motion-output=")
		if arg=="--motion-frames":capture_frames=true
	game=load("res://tests/motion_world.gd").new();root.add_child(game)
	for foe in game.enemies:foe.queue_free()
	game.enemies.clear()
	if close:game.camera.size=5.5
	skeleton=preload("res://scripts/carry_ik.gd").new().find_skeleton(game.hero)
	game.radio.visible=false;physics_frame.connect(tick)

func point(name: String) -> Array:
	var index=skeleton.find_bone(name);var p=skeleton.global_transform*skeleton.get_bone_global_pose(index).origin
	return [p.x,p.y,p.z]

func tick() -> void:
	elapsed+=1.0/60.0
	key(KEY_CTRL,elapsed>=1 and elapsed<3)
	key(KEY_W,elapsed>=1 and elapsed<9)
	key(KEY_SHIFT,elapsed>=7 and elapsed<9)
	key(KEY_S,elapsed>=10 and elapsed<10.8)
	key(KEY_D,elapsed>=11.2 and elapsed<12 or elapsed>=13 and elapsed<14 or elapsed>=16.5 and elapsed<17.5)
	key(KEY_SPACE,elapsed>=11.3 and elapsed<11.35 or elapsed>=13.1 and elapsed<13.15)
	if elapsed>=11.65 and once("dodge-follow-up"):click()
	if elapsed>=15 and once("attack-1"):click()
	if elapsed>=15.5 and once("attack-2"):click()
	if elapsed>=16.8 and once("moving-attack"):click()
	if elapsed>=18 and once("hurt"):game.hero.take_hit(10,Vector3.LEFT)
	if elapsed>=19 and once("pause"):key(KEY_ESCAPE,true)
	if elapsed>=19.1 and elapsed<19.2:key(KEY_ESCAPE,false)
	if elapsed>=20 and once("resume"):key(KEY_ESCAPE,true)
	if elapsed>=20.1:key(KEY_ESCAPE,false)
	if elapsed>=22 and once("death"):game.hero.hurt_left=0;game.hero.take_hit(150,Vector3.LEFT)
	game.objective.text="Motion review · "+str(snappedf(elapsed,.1))+" s · "+game.hero.current_clip
	if capture_frames:
		for stamp in [2.0,5.0,8.0,11.5,18.15,24.5]:
			if elapsed>=stamp and once("frame-"+str(stamp)):save_frame(str(stamp)+".png")
	var screen=game.camera.unproject_position(game.hero.position+Vector3.UP*.8)
	samples.append({"time":elapsed,"root":[game.hero.position.x,game.hero.position.y,game.hero.position.z],"left_foot":point("Foot.L"),"right_foot":point("Foot.R"),"head":point("Head"),"ground_speed":game.hero.ground_speed,"animation_speed":game.hero.animation_speed,"state":game.hero.current_clip,"action_left":game.hero.action_remaining,"action_weight":game.hero.action_weight,"dash_left":game.hero.dash_left,"paused":game.paused,"player_down":game.player_down,"in_view":Rect2(Vector2.ZERO,root.size).has_point(screen),"render_delta":root.get_process_delta_time()})
	if elapsed>=26.5:finish()

func finish() -> void:
	physics_frame.disconnect(tick)
	for code in held.keys():key(code,false)
	DirAccess.make_dir_recursive_absolute(output)
	var file=FileAccess.open(output.path_join("samples.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"seconds":elapsed,"samples":samples,"input":"actual keyboard/mouse; damage/death fixture staged","world":"isolated metre grid; no campaign content claim","close_camera":close,"human_playtest":false,"game_version":ProjectSettings.get_setting("application/config/version"),"main_sha256":FileAccess.get_sha256("res://scripts/main.gd"),"actor_sha256":FileAccess.get_sha256("res://scripts/actor.gd")},"  "));file.close()
	print("MOTION_RUNTIME_COMPLETE ",elapsed," death_elapsed=",game.hero.action_elapsed," corpse_valid=",is_instance_valid(game.hero))
	game.queue_free();cleanup.call_deferred()

func cleanup() -> void:
	var until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<until:await process_frame
	quit()

func save_frame(filename: String) -> void:
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(output);root.get_texture().get_image().save_png(output.path_join(filename))
