extends "res://tests/expedition_tour.gd"
## Reuses keyboard/mouse movement and combat helpers, not mission fixture mutations.
var last_manual := 0
var last_turns := 0
var distance_walked := 0.0
var route_reached := false

func start() -> void:
	method="power";output="H:/game/release/campaign-v037/tour-power"
	for arg in OS.get_cmdline_user_args():
		if arg=="--method=winch":method="winch";output="H:/game/release/campaign-v037/tour-winch"
		if arg=="--tour-capture":captures=true
		if arg.begins_with("--tour-output="):output=arg.trim_prefix("--tour-output=")
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED);Engine.max_fps=0
	game=load("res://hospital.tscn").instantiate();root.add_child(game)
	await physics_frame
	last_position=game.hero.position
	process_frame.connect(tick)
	print("HOSPITAL_TOUR_BEGIN method=",method," keyboard+mouse; no teleports/health mutations")

func tick() -> void:
	var delta=root.get_process_delta_time();elapsed+=delta;last_attack+=delta;e_wait=maxf(0,e_wait-delta)
	if not game.hero.alive:finish("player defeated");return
	if elapsed>420:finish("time limit");return
	if game.hero.position.distance_to(last_position)>.25:
		distance_walked+=game.hero.position.distance_to(last_position);last_position=game.hero.position;progress_time=elapsed
	if elapsed-progress_time>20:finish("stuck stage "+str(stage));return
	if game.mission==1 and not route_reached:
		route_reached=true;key(KEY_E,false);progress_time=elapsed
		if captures:save_frame("switch-set.png")
	if game.mission==1 and game.refuge_heard:finish("route restored; refuge contacted");return
	var nearest: RailActor=null;var distance=1000.0
	for foe in game.enemies:
		if is_instance_valid(foe) and foe.alive:
			var d=game.hero.position.distance_to(foe.position)
			if d<distance and game.visible_between(game.hero.position,foe.position):nearest=foe;distance=d
	if nearest and distance<5.5:
		combat_time+=delta;key(KEY_E,false)
		key(KEY_Q,game.flares>0 and game.flare_cooldown<=0 and game.hero.health<65 and distance<4)
		if nearest.phase in ["windup","charge"] and distance<3 and (nearest.phase=="charge" or nearest.phase_left<=.24):
			var away=(game.hero.position-nearest.position).normalized();var evade=Vector3(-away.z,0,away.x)
			if not game.inside_floor(Vector2(game.hero.position.x+evade.x*2,game.hero.position.z+evade.z*2)):evade=-evade
			move(evade);key(KEY_SPACE,game.hero.dash_cooldown<=0 and game.hero.attack_left<=.26)
		else:
			key(KEY_SPACE,false)
			if distance<1.32:
				move(Vector3.ZERO)
				var safe_attack=not (nearest.enemy_kind=="brute" and nearest.phase=="windup" and nearest.phase_left<.5)
				if safe_attack and game.hero.attack_left<=0 and game.hero.dash_left<=0 and game.hero.stun<=0 and last_attack>.45:mouse_attack(nearest.position);last_attack=0
			else:go(nearest.position,delta)
		return
	key(KEY_SPACE,false);key(KEY_Q,false)
	if game.hero.health<65:
		for id in game.supply_positions:
			if not game.supplies.has(id) and game.hero.position.distance_to(game.supply_positions[id])<6:interact(game.supply_positions[id],delta);return
	if e_wait>0:key(KEY_E,false);move(Vector3.ZERO);return
	if game.mission==1:interact(game.REFUGE,delta);return
	var targets=[game.JUMPER,game.SOCKET,game.FEED_A,game.FEED_B,game.TEST,game.DRIVE] if method=="power" else [game.WINCH,game.DRIVE]
	var conditions=[game.has_jumper,game.installed,game.feed_a,game.feed_b,game.tested,game.mission==1] if method=="power" else [game.has_winch,game.mission==1]
	if stage<conditions.size() and conditions[stage]:
		stage+=1;key(KEY_E,false);e_wait=.15;progress_time=elapsed
		if captures:save_frame("stage-%02d.png"%stage)
		return
	if method=="winch" and (game.winch_stage!=last_manual or game.winch_turns!=last_turns):
		last_manual=game.winch_stage;last_turns=game.winch_turns;key(KEY_E,false);e_wait=.15;progress_time=elapsed;return
	if stage<targets.size():interact(targets[stage],delta)

func finish(reason: String) -> void:
	process_frame.disconnect(tick)
	for code in held.keys():key(code,false)
	DirAccess.make_dir_recursive_absolute(output)
	var report={"reason":reason,"seconds":elapsed,"health":game.hero.health,"mission":game.mission,"method":game.route_method,"combat_seconds":combat_time,"hero_distance":distance_walked,"actions":game.action_log,"automated":true,"hero_teleports":0,"health_override":false,"reserve_on":game.reserve_on,"passengers_evacuated":false,"gpu_screenshots":captures,"input":"keyboard and mouse events through Input/Viewport"}
	report["game_version"]=ProjectSettings.get_setting("application/config/version")
	report["main_sha256"]=FileAccess.get_sha256("res://scripts/main.gd");report["actor_sha256"]=FileAccess.get_sha256("res://scripts/actor.gd")
	var file=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("HOSPITAL_TOUR_END ",reason," time=",elapsed," health=",game.hero.health)
	var succeeded=game.mission==1 and reason=="route restored; refuge contacted"
	if captures:await save_frame("final.png")
	game.queue_free();await process_frame;await process_frame
	# Audio decoders run on wall time even when --fixed-fps races virtual time.
	var drain_until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<drain_until:await process_frame
	quit(0 if succeeded else 1)
