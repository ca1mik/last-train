extends "res://tests/evac_first_tour.gd"
## Complete fresh hospital route, first group, empty cart, fourth resident and
## wagon question through ordinary keys/mouse. No actor or objective mutations.
var return_index:=0
var last_handoff:=false
var cart_waypoint:=0
var phase_seen:=""
var detach_retries:=0
var had_cart:=false
var fourth_reached:=false
var return_points=[Vector3(-22,0,20),Vector3(-22,0,-1),Vector3(0,0,-1),Vector3(26,0,-3.8),Vector3(37,0,-3)]
var last_points=[Vector3(41.5,0,-4),Vector3(41.5,0,-8.35)]
var train_points=[Vector3(37,0,-3),Vector3(26,0,-3.8),Vector3(0,0,-1),Vector3(-22,0,-1),Vector3(-22,0,20),Vector3(-32,0,24.5),Vector3(-38.0,0,24.5),Vector3(-37.3,0,26.3),Vector3(-36.7,0,28.0)]
func tick() -> void:
	if not game.evacuation or game.evacuation.stage!="first_received":super.tick();return
	var delta=root.get_process_delta_time();elapsed+=delta;last_attack+=delta;e_wait=maxf(0,e_wait-delta)
	var last=game.evacuation.transport
	if not last_handoff:last_handoff=true;key(KEY_E,false);path.clear();repath=0;progress_time=elapsed;return
	if not game.hero.alive:finish("defeated");return
	if elapsed>950:finish("time limit");return
	if game.hero.position.distance_to(last_position)>.25:distance_walked+=game.hero.position.distance_to(last_position);last_position=game.hero.position;progress_time=elapsed
	if phase_seen!=last.state:
		phase_seen=last.state;progress_time=elapsed;key(KEY_E,false);path.clear();repath=0
		if captures:save_frame("fourth-"+last.state+".png")
		return
	if elapsed-progress_time>35:finish("stuck last "+last.state+" point "+str(cart_waypoint)+" hero "+str(game.hero.position)+" cart "+str(last.cart.position));return
	if last.received:
		fourth_reached=true
		if last.truth!="":
			if last.question.visible:last.question.close()
			finish("four received and truth chosen");return
		if last.question.visible:
			move(Vector3.ZERO);key(KEY_E,false);var event=InputEventKey.new();event.keycode=KEY_2 if OS.get_cmdline_user_args().has("--truth=defend") else KEY_1;event.physical_keycode=event.keycode;event.pressed=true;root.push_input(event,true);return
		interact(last.TALK,delta);return
	if last.attached and not had_cart:had_cart=true;key(KEY_E,false);repath=0;return
	elif not last.attached and had_cart:had_cart=false;detach_retries+=1;key(KEY_E,false);repath=0;return
	if fight(delta):
		if last.attached:move(Vector3.ZERO);interact(game.hero.position,delta)
		return
	if last.state=="awaiting":
		if return_index<return_points.size():
			var target=return_points[return_index]
			if game.hero.position.distance_to(target)<1: return_index+=1;key(KEY_E,false);repath=0;return
			go(target,delta);return
		interact(game.REFUGE,delta);return
	if last.lift_left>0:move(Vector3.ZERO);key(KEY_E,false);progress_time=elapsed;return
	if not last.loaded:
		if last.cart.position.distance_to(last.LOAD_POINT)<.9:
			if last.attached:interact(game.hero.position,delta);return
			interact(last.handle(),delta,1.3);return
		if not last.attached:interact(last.handle(),delta,.9);return
		key(KEY_E,false)
		if cart_waypoint<last_points.size():
			if game.hero.position.distance_to(last_points[cart_waypoint])<.6:cart_waypoint+=1;repath=0;return
			go(last_points[cart_waypoint],delta)
		else:move(Vector3.ZERO)
		return
	if not last.bag_taken:
		cart_waypoint=0;interact(game.reception.BAG,delta);return
	if not last.attached:
		if last.footprint_inside():interact(last.PARK,delta,1.5)
		else:interact(last.handle(),delta,.9)
		return
	key(KEY_E,false)
	if last.footprint_inside():
		# Release at actual arrival, then step within reach of the reception point.
		interact(game.hero.position,delta);return
	if cart_waypoint<train_points.size():
		var target=train_points[cart_waypoint]
		if game.hero.position.distance_to(target)<.7:cart_waypoint+=1;repath=0;return
		go(target,delta)
	else:move(Vector3.ZERO)
func finish(reason: String) -> void:
	process_frame.disconnect(tick)
	for code in held.keys():key(code,false)
	DirAccess.make_dir_recursive_absolute(output)
	if captures:await save_frame("evacuation-final.png")
	var last=game.evacuation.transport
	var result={"reason":reason,"seconds":elapsed,"health":game.hero.health,"method":method,"boarded":game.evacuation.boarded,"fourth":last.snapshot(),"hero_teleports":0,"health_override":false,"input":"actual keyboard/mouse known-goal route from fresh hospital; no fixture changes","human_playtest":false,"actions":game.action_log,"detach_events":detach_retries,"hero":str(game.hero.position),"nina":str(game.evacuation.people.nina.position),"lida":str(game.evacuation.people.lida.position),"source_sha256":{}}
	for source in ["hospital.gd","hospital_reception.gd","hospital_evacuation.gd","hospital_patient_transport.gd","hospital_truth_panel.gd","escort_actor.gd"]:result.source_sha256[source]=FileAccess.get_sha256("res://scripts/"+source)
	var file=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));file.close()
	print("EVAC_FULL_TOUR ",reason," seconds=",elapsed," fourth=",last.snapshot())
	game.set_paused(false);game.queue_free();await process_frame;await process_frame
	var until=Time.get_ticks_msec()+450
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if reason=="four received and truth chosen" else 1)
