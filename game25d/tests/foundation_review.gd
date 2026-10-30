extends SceneTree
## GPU evidence: real scene, isolated staged foe, actual Esc/J and slider input.
var game: Node3D
var elapsed:=0.0
var flags: Dictionary={}
var samples: Array=[]
var output:="H:/game/release/foundation-v045/native"
var attacker: RailActor
var frozen_clock:=0.0
var failures: Array=[]

func _initialize() -> void:start.call_deferred()
func press(code: int) -> void:
	var down=InputEventKey.new();down.keycode=code;down.physical_keycode=code;down.pressed=true;root.push_input(down,true)
	var up=InputEventKey.new();up.keycode=code;up.physical_keycode=code;up.pressed=false;root.push_input(up,true)
func once(id: String) -> bool:
	if flags.has(id):return false
	flags[id]=true;return true
func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name+".png"))
func start() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	var preferences=preload("res://scripts/player_preferences.gd").new();preferences.load_all();preferences.set_volume("SFX",.83)
	game=load("res://expedition.tscn").instantiate();root.add_child(game);current_scene=game
	for foe in game.enemies:foe.queue_free()
	game.enemies.clear();await physics_frame;await physics_frame
	game.hero.position=Vector3(-4,0,0);game.hero.reset_physics_interpolation();game.hero.face(Vector3.FORWARD,.1)
	attacker=game.spawn_actor("walker",Vector3(-4,0,-.85));attacker.face(Vector3.BACK,.1)
	game.camera.size=6.8;game.follow_camera(.016);physics_frame.connect(tick)
func tick() -> void:
	elapsed+=1.0/60.0
	if elapsed>=.25 and once("windup"):shot("01-windup")
	if attacker.phase=="strike" and once("strike"):shot("02-strike-start")
	if game.hero.health<100 and once("contact"):shot("03-contact")
	if elapsed>=1.4 and once("pause"):
		press(KEY_ESCAPE);frozen_clock=game.clock;shot("04-pause-journal")
	if elapsed>=2.8 and once("frozen"):
		if not paused or absf(game.clock-frozen_clock)>.001:failures.append("world advanced during visible pause")
	if elapsed>=3.2 and once("resume"):press(KEY_ESCAPE)
	if elapsed>=4 and once("dodge"):press(KEY_SPACE)
	if elapsed>=5 and once("journal"):press(KEY_J);shot("05-journal-reopened")
	if elapsed>=5.6 and once("slider"):
		# Convert the actual Control's canvas coordinates into viewport input.
		var slider: HSlider
		for node in game.pause_overlay.get_children():
			if node is HSlider and node.position.y>590 and node.position.y<610:slider=node
		if slider:
			var point=slider.get_global_rect().get_center()
			var down=InputEventMouseButton.new();down.button_index=MOUSE_BUTTON_LEFT;down.position=point;down.pressed=true;root.push_input(down,true)
			var up=InputEventMouseButton.new();up.button_index=MOUSE_BUTTON_LEFT;up.position=point;up.pressed=false;root.push_input(up,true)
		else:failures.append("SFX slider missing")
	if elapsed>=6.2 and once("volume"):
		if absf(float(game.preferences.values.SFX)-.5)>.08:failures.append("actual slider did not change SFX bus")
		shot("06-volume-changed")
	if elapsed>=7 and once("close"):press(KEY_J)
	samples.append({"time":elapsed,"world_clock":game.clock,"paused":paused,"health":game.hero.health,"phase":attacker.phase,"clip":attacker.current_clip,"attack_elapsed":attacker.action_elapsed,"sfx":game.preferences.values.SFX})
	if elapsed>=8:finish()
func finish() -> void:
	physics_frame.disconnect(tick)
	game.set_paused(false)
	var file=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"seconds":elapsed,"failures":failures,"samples":samples,"gpu":RenderingServer.get_video_adapter_name(),"viewport":[root.size.x,root.size.y],"input":"actual Esc/J/space/GUI slider; isolated staged foe and hero placement","human_playtest":false,"main_sha256":FileAccess.get_sha256("res://scripts/main.gd"),"actor_sha256":FileAccess.get_sha256("res://scripts/actor.gd")},"  "));file.close()
	print("FOUNDATION_REVIEW failures=",failures)
	game.queue_free();await process_frame;await process_frame
	var until=Time.get_ticks_msec()+450
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if failures.is_empty() else 1)
