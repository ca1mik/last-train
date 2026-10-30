extends "res://tests/hospital_tour.gd"
## Entire route + receiving preparations by known-goal ordinary input.
var preparing:=false
var preparation_stage:=0
var out_of_view_frames:=0
var work_order: Array[String]=["input","aisle","bag","passage","confirm"]
func tick() -> void:
	if DisplayServer.get_name()!="headless" and not Rect2(Vector2.ZERO,Vector2(root.size)).has_point(game.camera.unproject_position(game.hero.position+Vector3.UP*.8)):out_of_view_frames+=1
	if not preparing and not game.refuge_heard:super.tick();return
	var delta=root.get_process_delta_time();elapsed+=delta;last_attack+=delta;e_wait=maxf(0,e_wait-delta)
	if not preparing:
		preparing=true;key(KEY_E,false);progress_time=elapsed
		if OS.get_cmdline_user_args().has("--prep-order=path-first"):work_order.assign(["passage","bag","aisle","input","confirm"])
		return
	if not game.hero.alive:finish("player defeated");return
	if elapsed>500:finish("time limit");return
	if game.reception.ready_confirmed:finish("receiving prepared");return
	if game.hero.position.distance_to(last_position)>.25:distance_walked+=game.hero.position.distance_to(last_position);last_position=game.hero.position;progress_time=elapsed
	if elapsed-progress_time>20:finish("stuck preparation "+str(preparation_stage));return
	if fight(delta):return
	if game.hero.health<65:
		for id in game.supply_positions:
			if not game.supplies.has(id) and game.hero.position.distance_to(game.supply_positions[id])<6:interact(game.supply_positions[id],delta);return
	if e_wait>0:key(KEY_E,false);move(Vector3.ZERO);return
	var item=work_order[preparation_stage]
	var states={"input":game.reception.input_checked,"aisle":game.reception.aisle_clear,"bag":game.reception.bag_ready,"passage":game.reception.path_clear,"confirm":game.reception.ready_confirmed}
	if states[item]:
		key(KEY_E,false);preparation_stage+=1;e_wait=.2;progress_time=elapsed
		if captures:save_frame("receiving-"+item+".png")
		return
	var targets={"input":game.reception.INPUT,"aisle":game.reception.AISLE,"bag":game.reception.BAG,"passage":game.reception.PASSAGE,"confirm":game.REFUGE}
	interact(targets[item],delta)
func fight(delta: float) -> bool:
	var nearest: RailActor;var distance:=1000.0
	for foe in game.enemies:
		if is_instance_valid(foe) and foe.alive and game.visible_between(foe.position,game.hero.position):
			var d=foe.position.distance_to(game.hero.position)
			if d<distance:distance=d;nearest=foe
	if not nearest or distance>=5.5:key(KEY_SPACE,false);key(KEY_Q,false);return false
	combat_time+=delta;key(KEY_E,false);key(KEY_Q,game.flares>0 and game.flare_cooldown<=0 and game.hero.health<65 and distance<4)
	if nearest.phase in ["windup","charge"] and distance<3 and (nearest.phase=="charge" or nearest.phase_left<=.24):
		var away=(game.hero.position-nearest.position).normalized();var evade=Vector3(-away.z,0,away.x)
		if not game.inside_floor(Vector2(game.hero.position.x+evade.x*2,game.hero.position.z+evade.z*2)):evade=-evade
		move(evade);key(KEY_SPACE,game.hero.dash_cooldown<=0 and game.hero.attack_left<=.26)
	else:
		key(KEY_SPACE,false)
		if distance<1.32:
			move(Vector3.ZERO)
			if not (nearest.enemy_kind=="brute" and nearest.phase=="windup" and nearest.phase_left<.5) and game.hero.attack_left<=0 and game.hero.dash_left<=0 and game.hero.stun<=0 and last_attack>.45:mouse_attack(nearest.position);last_attack=0
		else:go(nearest.position,delta)
	return true
func finish(reason: String) -> void:
	process_frame.disconnect(tick)
	for code in held.keys():key(code,false)
	DirAccess.make_dir_recursive_absolute(output)
	if captures:await save_frame("receiving-final.png")
	var report={"reason":reason,"seconds":elapsed,"health":game.hero.health,"method":method,"work_order":work_order,"preparation":game.reception.save(),"reserve_on":game.reserve_on,"passengers_evacuated":0,"hero_teleports":0,"health_override":false,"input":"actual keyboard/mouse known-goal route; no fixture mutations","human_playtest":false,"actions":game.action_log,"distance":distance_walked,"game_version":ProjectSettings.get_setting("application/config/version"),"hospital_sha256":FileAccess.get_sha256("res://scripts/hospital.gd"),"reception_sha256":FileAccess.get_sha256("res://scripts/hospital_reception.gd")}
	report["out_of_view_frames"]=out_of_view_frames if DisplayServer.get_name()!="headless" else null
	var file=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("RECEPTION_TOUR ",reason," seconds=",elapsed," health=",game.hero.health)
	game.queue_free();await process_frame;await process_frame
	var until=Time.get_ticks_msec()+450
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if reason=="receiving prepared" else 1)
