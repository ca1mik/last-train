extends SceneTree
## Staged state/physics fixtures; separate from forest_tour ordinary input.
var game: Node3D
var checks:=0
var failures: Array=[]
var output:="H:/game/release/audit-v048/forest-rules.json"
func _initialize() -> void:start.call_deferred()
func check(ok: bool,message: String) -> void:
	checks+=1
	if not ok:failures.append(message);push_error(message)
func frames(count: int) -> void:
	for i in count:await physics_frame
func key(code: int,down: bool) -> void:
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=down;Input.parse_input_event(event);Input.flush_buffered_events()
func build() -> void:
	game=load("res://forest.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true;await frames(3)
func clear() -> void:
	game.queue_free();await frames(3)
func start() -> void:
	await build()
	check(game.save_path.get_file().begins_with("forest-qa-"),"fixture uses QA save slot")
	if not game.save_path.get_file().begins_with("forest-qa-"):quit(2);return
	var campaign=preload("res://scripts/campaign.gd");var before=campaign.read()
	for a in [game.start_point,game.GENERATOR,game.BELL,game.CACHE]+game.goals:
		for b in [game.start_point,game.GENERATOR,game.CACHE]+game.goals:
			var route=game.route(a,b);check(a.distance_to(b)<1 or not route.is_empty() and route[-1].distance_to(b)<1,"route connects "+str(a)+" to "+str(b))
	check(not game.perform("signal") and not game.signal_set,"cannot confirm signal without a drive")
	check(not game.perform("return") and not game.completed,"cannot finish before signal")
	game.perform("power");game.apply_world();await frames(2)
	check(game.trial_open and game.trial_gate_shape.disabled,"motor opens collision and route")
	game.paused=false;await frames(2);game.paused=true
	check(game.enemies.any(func(foe):return foe.investigate_left>0 and foe.investigate_position==game.GENERATOR),"motor attracts actual enemies")
	check(not game.perform("stop_motor") and game.powered,"cannot remove power before mechanical latch")
	game.perform("signal");game.apply_world();game.perform("stop_motor");game.apply_world()
	check(game.signal_set and game.chosen_route=="power" and game.trial_open and not game.powered,"latch holds signal after power off")
	game.hero.health=45;game.flares=0;game.perform("cache");var health=game.hero.health;var flares=game.flares
	check(health==75 and flares==2,"cache provides finite supplies")
	check(not game.perform("cache") and game.hero.health==health and game.flares==flares,"cache cannot be farmed")
	game.enemies[0].queue_free();await frames(3)
	game.save_checkpoint();await clear();await build()
	check(game.signal_set and game.cache_taken and game.chosen_route=="power" and not game.powered,"reload keeps route and one-use reward")
	check(game.hero.health==75 and game.flares==2,"reload keeps resources")
	check(not game.enemies[0].alive,"removed dead enemy stays defeated after saving and reload")
	game.perform("return");game.save_checkpoint();await clear();await build()
	check(game.completed and game.trial_gate_shape.disabled,"completed stop survives reload")
	DirAccess.remove_absolute(game.save_path);await clear();await build()
	# Fresh manual route with real held E, cancelled then interrupted by pause.
	for foe in game.enemies:foe.alive=false;foe.collision_layer=0;foe.hide()
	game.hero.position=game.goals[0];game.hero.reset_physics_interpolation();game.paused=false;await frames(3)
	key(KEY_E,true);await frames(15);key(KEY_E,false);await frames(3)
	check(not game.has_handle and game.work==0,"short E cancels operation")
	key(KEY_E,true);await frames(15);game.set_paused(true);var progress=game.work;await frames(60)
	check(is_equal_approx(progress,game.work) and not game.has_handle,"pause freezes operation")
	game.set_paused(false);await frames(60);key(KEY_E,false);await frames(3)
	check(game.has_handle and not game.powered,"real E collects manual handle")
	game.perform("signal");game.apply_world();game.save_checkpoint();await clear();await build()
	check(game.chosen_route=="manual" and game.signal_set and not game.powered,"manual route reloads without motor")
	check(campaign.read()==before,"standalone expedition preserves campaign cursor")
	var standalone_path=game.save_path
	await clear()
	root.set_meta("campaign_playing",true);await build()
	check(game.save_path!=standalone_path and not game.signal_set,"campaign forest is separate from completed standalone stop")
	await clear();root.set_meta("campaign_playing",false)
	var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures,"method":"staged logic/collision fixtures and held-E/pause/reload; not human test"},"  "));file.close()
	print("FOREST_RULES checks=",checks," failures=",failures)
	var until=Time.get_ticks_msec()+450
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if failures.is_empty() else 1)
