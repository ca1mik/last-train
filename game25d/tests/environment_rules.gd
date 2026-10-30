extends SceneTree
var checks:=0
var failures: Array=[]
var game: Node3D
var output:="H:/game/release/environment-v044/rules.json"
func _initialize() -> void:start.call_deferred()
func check(ok: bool,message: String) -> void:
	checks+=1
	if not ok:failures.append(message);push_error(message)
func frames(n: int) -> void:
	for i in range(n):await physics_frame
func key(down: bool) -> void:
	var event=InputEventKey.new();event.keycode=KEY_E;event.physical_keycode=KEY_E;event.pressed=down;Input.parse_input_event(event);Input.flush_buffered_events()
func retry() -> void:
	var event=InputEventKey.new();event.keycode=KEY_R;event.physical_keycode=KEY_R;event.pressed=true;root.push_input(event,true)
	var release=InputEventKey.new();release.keycode=KEY_R;release.physical_keycode=KEY_R;release.pressed=false;root.push_input(release,true)
func start() -> void:
	output=preload("res://tests/qa_report.gd").path(output)
	var campaign=preload("res://scripts/campaign.gd");var before=FileAccess.get_file_as_string(campaign.path()) if FileAccess.file_exists(campaign.path()) else ""
	# Retain the old geometry fixture; the new forest gameplay has its own rules.
	for scene in ["forest_trial","wasteland"]:
		game=load("res://"+scene+".tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true;await frames(3)
		check(game.kit.foliage_count>0,scene+" has real foliage meshes")
		for a in [game.start_point]+game.goals:
			for b in game.goals:
				var route=game.route(a,b);check(a.distance_to(b)<1 or not route.is_empty() and route[-1].distance_to(b)<1,scene+" connected targets "+str(a)+" to "+str(b))
		check(not game.trial_gate_shape.disabled,scene+" gate physically closed initially")
		for foe in game.enemies:foe.queue_free()
		game.enemies.clear();await frames(2)
		game.hero.position=game.goals[0];game.hero.reset_physics_interpolation();game.paused=false;key(true);await frames(15);key(false);await frames(3)
		check(game.mission==0 and game.work==0,scene+" short interaction cancels")
		key(true);await frames(65);check(game.mission==1,scene+" actual E advances one stage")
		check(game.camera.position.distance_to(game.hero.position+Vector3.UP*.8+game.camera_offset)<.75,scene+" camera follows far objective in world space")
		await frames(60);check(game.mission==1,scene+" held E cannot consume another stage")
		key(false);await frames(3)
		for stage in [1,2]:
			game.hero.position=game.goals[stage];game.hero.motion_velocity=Vector2.ZERO;game.hero.velocity=Vector3.ZERO;game.hero.reset_physics_interpolation();await frames(3);key(true);await frames(65);key(false);await frames(3)
		check(game.mission==3,scene+" route has a terminal state")
		check(game.camera.position.distance_to(game.hero.position+Vector3.UP*.8+game.camera_offset)<.75,scene+" camera follows return in world space")
		check(game.trial_open and game.trial_gate_shape.disabled,scene+" operation opens physical gate")
		check(game.objective.text.contains("Участок пройден"),scene+" completion is explicit")
		check(game.flares==3 and game.hero.health==100,scene+" no hidden resource cost in operation fixture")
		retry();await frames(5);game=current_scene;game.paused=true
		check(game.mission==0 and game.hero.alive,scene+" R restarts a completed standalone map")
		game.hero.take_hit(150,Vector3.LEFT);game.paused=false;await frames(3);retry();await frames(5);game=current_scene;game.paused=true
		check(game.mission==0 and game.hero.alive and not game.player_down,scene+" R restores play after staged death")
		game.queue_free();await frames(3)
	var after=FileAccess.get_file_as_string(campaign.path()) if FileAccess.file_exists(campaign.path()) else ""
	check(before==after,"standalone maps never move campaign cursor")
	var selector=load("res://locations.tscn").instantiate();root.add_child(selector);await frames(3)
	var count=0
	for child in selector.get_children():
		if child is Button:count+=1
	check(count==4,"selector exposes three stops and campaign continuation")
	selector.queue_free();await frames(3)
	var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures,"scope":"navigation/state/collision flags plus actual E; staged actors/positions, not human playtest"},"  "));file.close()
	print("ENVIRONMENT_RULES ",checks," failures=",failures);await create_timer(.3).timeout;quit(0 if failures.is_empty() else 1)
