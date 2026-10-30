extends "res://tests/chapter1_tour.gd"
var environment_name:="forest"
var last_mission:=-1
var out_of_view_frames:=0
func start() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--landscape="):environment_name=arg.trim_prefix("--landscape=")
		if arg.begins_with("--tour-output="):output=arg.trim_prefix("--tour-output=")
		if arg=="--tour-capture":captures=true
	game=load("res://"+environment_name+".tscn").instantiate();root.add_child(game);current_scene=game
	await physics_frame;last_position=game.hero.position;process_frame.connect(tick)
func tick() -> void:
	var delta=root.get_process_delta_time();elapsed+=delta;last_attack+=delta
	if DisplayServer.get_name()!="headless" and not Rect2(Vector2.ZERO,Vector2(root.size)).has_point(game.camera.unproject_position(game.hero.position+Vector3.UP*.8)):out_of_view_frames+=1
	if not game.hero.alive:finish("defeated");return
	if elapsed>300:finish("time limit");return
	if game.mission==3:finish("completed");return
	if game.hero.position.distance_to(last_position)>.25:last_position=game.hero.position;progress_time=elapsed
	if elapsed-progress_time>20:finish("stuck");return
	if game.mission!=last_mission:
		last_mission=game.mission;key(KEY_E,false);progress_time=elapsed
		if captures:save_frame("stage-%02d.png"%last_mission)
	var nearest: RailActor=null;var distance=1000.0
	for foe in game.enemies:
		if is_instance_valid(foe) and foe.alive:
			var d=foe.position.distance_to(game.hero.position)
			if d<distance and game.visible_between(game.hero.position,foe.position):nearest=foe;distance=d
	if nearest and distance<5.5:
		combat_time+=delta;key(KEY_E,false)
		key(KEY_Q,game.hero.health<65 and game.flares>0 and distance<4 and game.flare_cooldown<=0)
		if nearest.phase in ["windup","charge"] and distance<3 and (nearest.phase=="charge" or nearest.phase_left<.24):
			var away=(game.hero.position-nearest.position).normalized();var evade=Vector3(-away.z,0,away.x)
			if not game.inside_floor(Vector2(game.hero.position.x+evade.x*2,game.hero.position.z+evade.z*2)):evade=-evade
			move(evade);key(KEY_SPACE,game.hero.dash_cooldown<=0 and game.hero.attack_left<=.26)
		else:
			key(KEY_SPACE,false)
			if distance<1.32:
				move(Vector3.ZERO)
				if not (nearest.enemy_kind=="brute" and nearest.phase=="windup" and nearest.phase_left<.5) and game.hero.attack_left<=0 and game.hero.dash_left<=0 and game.hero.stun<=0 and last_attack>.45:mouse_attack(nearest.position);last_attack=0
			else:go(nearest.position,delta)
		return
	key(KEY_SPACE,false);key(KEY_Q,false);interact(game.goals[game.mission],delta)
func finish(reason: String) -> void:
	process_frame.disconnect(tick)
	for code in held.keys():key(code,false)
	DirAccess.make_dir_recursive_absolute(output)
	if captures:await save_frame("final.png")
	var file=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"reason":reason,"landscape":environment_name,"seconds":elapsed,"health":game.hero.health,"mission":game.mission,"gate_open":game.trial_open,"combat_seconds":combat_time,"actions":game.actions,"hero_teleports":0,"health_override":false,"out_of_view_frames":out_of_view_frames if DisplayServer.get_name()!="headless" else null,"input":"engine keyboard/mouse automation; known objectives and nav","human_playtest":false},"  "));file.close()
	print("ENVIRONMENT_TOUR ",environment_name," ",reason," ",elapsed)
	game.queue_free();await process_frame;await process_frame
	var drain_until=Time.get_ticks_msec()+500
	while Time.get_ticks_msec()<drain_until:await process_frame
	quit(0 if reason=="completed" else 1)
