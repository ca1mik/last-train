extends SceneTree
var game: Node3D
var elapsed := 0.0
var last_held := false

func _initialize() -> void:start.call_deferred()
func start() -> void:
	game=load("res://hospital.tscn").instantiate();root.add_child(game)
	for foe in game.enemies:foe.queue_free()
	game.enemies.clear();game.hero.position=game.DRIVE;game.hero.reset_physics_interpolation();game.has_winch=true;game.update_objective()
	var target=game.hero.position+Vector3.UP*.8;game.camera.position=target+game.camera_offset
	physics_frame.connect(tick)

func tick() -> void:
	elapsed+=1.0/60.0
	var held=fmod(elapsed,1.15)<.9
	if held!=last_held:
		last_held=held;var event=InputEventKey.new();event.keycode=KEY_E;event.physical_keycode=KEY_E;event.pressed=held;Input.parse_input_event(event)
	if elapsed>11:
		physics_frame.disconnect(tick)
		print("HOSPITAL_MOTION staged character/inventory; actual E sequence. mission=",game.mission," stage=",game.winch_stage)
		game.queue_free();cleanup.call_deferred()

func cleanup() -> void:
	var drain_until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<drain_until:await process_frame
	quit()
