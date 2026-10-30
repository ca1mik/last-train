extends "res://tests/reception_tour.gd"
## Ordinary input from fresh hospital through preparation and first-group seats.
var first_started:=false
var escort_point:=0
var tested_wait:=false
var wait_left:=0.0
var out_of_view:=0
var receiving_handoff:=false
var escort_points=[Vector3(26,0,-3.8),Vector3(0,0,-1),Vector3(-22,0,-1),Vector3(-22,0,20),Vector3(-33,0,24.5)]
func tap(code: int) -> void:key(code,true);key(code,false)
func tick() -> void:
	if not game.reception.ready_confirmed:super.tick();return
	var delta=root.get_process_delta_time();elapsed+=delta;last_attack+=delta;e_wait=maxf(0,e_wait-delta)
	if not receiving_handoff:
		receiving_handoff=true;key(KEY_E,false);progress_time=elapsed;return
	if DisplayServer.get_name()!="headless" and not Rect2(Vector2.ZERO,Vector2(root.size)).has_point(game.camera.unproject_position(game.hero.position+Vector3.UP*.8)):out_of_view+=1
	if not game.hero.alive:finish("defeated");return
	if elapsed>600:finish("time limit");return
	if game.hero.position.distance_to(last_position)>.25:distance_walked+=game.hero.position.distance_to(last_position);last_position=game.hero.position;progress_time=elapsed
	if elapsed-progress_time>30:finish("stuck "+game.evacuation.stage+" waypoint "+str(escort_point));return
	if game.evacuation.stage=="first_received":finish("three received");return
	if fight(delta):return
	var state=game.evacuation.stage
	if state=="waiting":interact(game.REFUGE,delta);return
	if state=="boarding":
		key(KEY_E,false)
		if game.hero.position.distance_to(Vector3(-29,0,22.5))>1:go(Vector3(-29,0,22.5),delta)
		else:move(Vector3.ZERO);progress_time=elapsed
		return
	if not first_started:
		first_started=true;key(KEY_E,false);progress_time=elapsed
		if captures:save_frame("group-start.png")
		return
	if not tested_wait and escort_point>=1:
		tap(KEY_G);tested_wait=true;wait_left=1.5
	if wait_left>0:
		wait_left-=delta;move(Vector3.ZERO);key(KEY_E,false)
		if wait_left<=0:tap(KEY_G)
		return
	if escort_point>=escort_points.size():interact(game.evacuation.DOOR,delta,.8);return
	key(KEY_E,false)
	var target: Vector3=escort_points[escort_point]
	# The game itself reports a lagging party; return through ordinary movement.
	var lagging=game.evacuation.objective_position()
	if lagging!=game.evacuation.DOOR and game.hero.position.distance_to(lagging)>5.5:go(lagging,delta);return
	if game.hero.position.distance_to(target)<1.0:
		escort_point+=1;progress_time=elapsed
		if captures:save_frame("escort-%02d.png"%escort_point)
		return
	go(target,delta)
func finish(reason: String) -> void:
	process_frame.disconnect(tick)
	for code in held.keys():key(code,false)
	DirAccess.make_dir_recursive_absolute(output)
	if captures:await save_frame("first-group-final.png")
	var result={"reason":reason,"seconds":elapsed,"health":game.hero.health,"boarded":game.evacuation.boarded,"stage":game.evacuation.stage,"wait_control_tested":tested_wait,"hero_teleports":0,"health_override":false,"input":"actual keyboard/mouse known-goal navigation from fresh hospital; no fixture changes","human_playtest":false,"out_of_view_frames":out_of_view if DisplayServer.get_name()!="headless" else null,"actions":game.action_log,"hospital_sha256":FileAccess.get_sha256("res://scripts/hospital.gd"),"evacuation_sha256":FileAccess.get_sha256("res://scripts/hospital_evacuation.gd"),"actor_sha256":FileAccess.get_sha256("res://scripts/escort_actor.gd"),"fourth_received":false}
	var file=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));file.close()
	print("EVAC_FIRST_TOUR ",reason," seconds=",elapsed," health=",game.hero.health," group=",game.evacuation.boarded)
	game.queue_free();await process_frame;await process_frame
	var until=Time.get_ticks_msec()+450
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if reason=="three received" else 1)
