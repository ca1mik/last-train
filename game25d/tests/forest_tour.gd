extends "res://tests/reception_tour.gd"
## Known-goal keyboard/mouse traversal. No enemy/hero/mission fixture mutation.
var targets: Array=[]
var states: Array=[]
var last_state:=""
func start() -> void:
	method="manual";output="H:/game/release/audit-v048/forest-manual"
	for arg in OS.get_cmdline_user_args():
		if arg=="--method=power":method="power"
		if arg=="--tour-capture":captures=true
		if arg.begins_with("--tour-output="):output=arg.trim_prefix("--tour-output=")
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED);Engine.max_fps=0
	game=load("res://forest.tscn").instantiate();root.add_child(game);current_scene=game
	await physics_frame;last_position=game.hero.position;process_frame.connect(tick)
func tick() -> void:
	var delta=root.get_process_delta_time();elapsed+=delta;last_attack+=delta
	if not game.hero.alive:finish("defeated");return
	if elapsed>360:finish("time limit");return
	if game.hero.position.distance_to(last_position)>.25:distance_walked+=game.hero.position.distance_to(last_position);last_position=game.hero.position;progress_time=elapsed
	if elapsed-progress_time>25:finish("stuck "+last_state);return
	if game.completed:finish("signal restored and returned");return
	if fight(delta):return
	var next=""
	var target: Vector3
	if not game.has_handle and not game.powered and not game.signal_set:
		next="route";target=game.GENERATOR if method=="power" else game.goals[0]
	elif not game.signal_set:next="signal";target=game.goals[1]
	elif not game.cache_taken:next="cache";target=game.CACHE
	elif game.powered:next="stop_motor";target=game.GENERATOR
	else:next="return";target=game.start_point
	if next!=last_state:
		last_state=next;key(KEY_E,false);path.clear();repath=0;progress_time=elapsed
		if captures:save_frame(next+".png")
		return
	interact(target,delta)
func finish(reason: String) -> void:
	process_frame.disconnect(tick)
	for code in held.keys():key(code,false)
	DirAccess.make_dir_recursive_absolute(output)
	if captures:await save_frame("final.png")
	var report={"reason":reason,"method":method,"seconds":elapsed,"distance":distance_walked,"combat_seconds":combat_time,"health":game.hero.health,"hero":str(game.hero.position),"path":str(path),"chosen_route":game.chosen_route,"completed":game.completed,"cache_taken":game.cache_taken,"powered":game.powered,"actions":game.action_log,"hero_teleports":0,"health_override":false,"human_playtest":false,"input":"keyboard/mouse known-goal input, no state fixture mutations","source_sha256":FileAccess.get_sha256("res://scripts/forest_expedition.gd")}
	var file=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("FOREST_TOUR ",reason," route=",game.chosen_route," seconds=",elapsed)
	game.queue_free();await process_frame;await process_frame
	var until=Time.get_ticks_msec()+450
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if reason=="signal restored and returned" else 1)
