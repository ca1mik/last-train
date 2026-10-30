extends SceneTree
var game: Node3D
var checks := 0
var failures: Array=[]
var held: Dictionary={}
func _initialize() -> void:start.call_deferred()
func check(condition: bool,message: String) -> void:
	checks+=1
	if not condition:failures.append(message);push_error(message)
func key(code: int,down: bool) -> void:
	held[code]=down
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=down;event.ctrl_pressed=held.get(KEY_CTRL,false);event.shift_pressed=held.get(KEY_SHIFT,false);Input.parse_input_event(event)
	Input.flush_buffered_events()
func frames(count: int) -> void:
	for i in range(count):await physics_frame
func start() -> void:
	game=load("res://tests/motion_world.gd").new();root.add_child(game)
	for foe in game.enemies:foe.queue_free()
	game.enemies.clear();await frames(4)
	for kind in ["worker","wraith"]:
		var baseline=load("res://assets/characters/"+kind+".glb").instantiate();var updated=load("res://assets/characters/motion-v38/"+kind+".glb").instantiate()
		game.add_child(baseline);game.add_child(updated);baseline.visible=false;updated.visible=false
		var finder=preload("res://scripts/carry_ik.gd").new();var a=finder.find_skeleton(baseline);var b=finder.find_skeleton(updated);var error=0.0
		for index in a.get_bone_count():
			var other=b.find_bone(a.get_bone_name(index))
			if other<0:error=INF;break
			error=maxf(error,(a.global_transform*a.get_bone_global_rest(index).origin).distance_to(b.global_transform*b.get_bone_global_rest(other).origin))
		check(a.get_bone_count()==b.get_bone_count() and error<.001,kind+" preserves skeleton rest landmarks")
		baseline.queue_free();updated.queue_free()
	for state in ["Idle","Walk","Run","Sprint","Dodge","Hurt","Death"]:check(game.hero.clips.has(state) and String(game.hero.clips[state]).begins_with("Rail_"),"retargeted state "+state+" loaded")
	key(KEY_CTRL,true);check(is_equal_approx(game.movement_speed(),1.72),"Ctrl selects deliberate walk speed");key(KEY_CTRL,false);await frames(2)
	var start_position=game.hero.position
	key(KEY_SPACE,true);await frames(2);key(KEY_SPACE,false)
	check(game.hero.current_clip=="Dodge" and not game.hero.action_blend.filter_enabled,"dodge uses independent full-body action")
	check(not game.hero.take_hit(10,Vector3.LEFT),"travel phase retains damage avoidance")
	game.hero.begin_attack(Vector3.BACK);check(game.hero.attack_left==0,"attack cannot replace tucked dodge pose")
	await frames(17)
	var travelled=game.hero.position.distance_to(start_position)
	check(travelled>1.95 and travelled<2.15,"dodge covers two metres including its braking tail with real physics")
	var click=InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_LEFT;click.pressed=true;click.position=game.camera.unproject_position(game.hero.position+game.hero.facing*2+Vector3.UP*.7);root.push_input(click,true)
	check(game.hero.attack_left==0 and game.hero.attack_buffer>0,"actual click near dodge recovery is buffered without cutting tucked pose")
	var release=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;release.pressed=false;release.position=click.position;root.push_input(release,true)
	await frames(9);check(game.hero.current_clip=="SwordSlash" and game.hero.attack_left>0,"buffered click starts once the dodge pose recovers")
	await frames(24);game.hero.hurt_left=0;game.hero.take_hit(5,Vector3.LEFT)
	check(game.hero.current_clip=="Hurt" and game.hero.action_blend.filter_enabled,"survived hit plays upper-body hurt")
	await frames(60);game.hero.hurt_left=0;game.hero.take_hit(150,Vector3.LEFT)
	await frames(150)
	check(game.player_down and is_instance_valid(game.hero),"dead hero persists for retry interface")
	check(game.hero.action_elapsed>2.3 and game.hero.action_remaining==0,"death advances through final pose after player_down")
	check(not game.hero.action_blend.filter_enabled,"death uses full-body pose")
	DirAccess.make_dir_recursive_absolute("H:/game/release/motion-v038")
	var file=FileAccess.open(preload("res://tests/qa_report.gd").path("H:/game/release/motion-v038/rules.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures,"dodge_distance":travelled,"scope":"isolated ground; real keys for walk/dodge; staged damage/death"},"  "));file.close()
	print("MOTION_RULES ",checks," failures=",failures)
	game.queue_free();await process_frame;await process_frame
	var until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if failures.is_empty() else 1)
