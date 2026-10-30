extends "res://tests/evac_full_tour.gd"
## Ordinary input across a real scene transition and into the forest stop.
var leaving:=false
var in_forest:=false
var forest_stage:=""
var hospital_trace: Dictionary={}
var transition_gap_frames:=0
func start() -> void:
	root.set_meta("campaign_playing",true)
	await super.start();current_scene=game
func tick() -> void:
	if not leaving:super.tick();return
	var delta=root.get_process_delta_time();elapsed+=delta;last_attack+=delta
	if not in_forest:
		if is_instance_valid(current_scene) and current_scene.is_inside_tree() and current_scene.is_node_ready() and current_scene.scene_file_path=="res://forest.tscn":
			game=current_scene;in_forest=true;key(KEY_E,false);path.clear();repath=0;last_position=game.hero.position;progress_time=elapsed
			if captures:save_frame("forest-arrival.png")
			return
		# A valid old scene can already be detached before the new scene is ready.
		# Release input without querying an out-of-tree camera during this gap.
		if is_instance_valid(game) and game.is_inside_tree() and game.camera.is_inside_tree():interact(game.evacuation.transport.TALK,delta)
		else:
			transition_gap_frames+=1
			for code in held.keys():key(code,false)
		if elapsed-progress_time>15:finish("departure failed")
		return
	if not game.hero.alive:finish("defeated in forest");return
	if elapsed>700:finish("combined time limit");return
	if game.hero.position.distance_to(last_position)>.25:last_position=game.hero.position;progress_time=elapsed
	if elapsed-progress_time>25:finish("stuck forest "+forest_stage);return
	if game.completed:finish("hospital departure and forest complete");return
	if fight(delta):return
	var next="";var target: Vector3
	if not game.has_handle and not game.powered and not game.signal_set:
		next="handle";target=game.goals[0]
	elif not game.signal_set:next="signal";target=game.goals[1]
	else:next="return";target=game.start_point
	if next!=forest_stage:
		forest_stage=next;key(KEY_E,false);path.clear();repath=0;progress_time=elapsed
		if captures:save_frame("forest-"+next+".png")
		return
	interact(target,delta)
func finish(reason: String) -> void:
	if reason=="four received and truth chosen" and not leaving:
		hospital_trace={"boarded":game.evacuation.boarded.duplicate(),"fourth":game.evacuation.transport.snapshot(),"actions":game.action_log.duplicate(true),"seconds":elapsed}
		leaving=true;progress_time=elapsed;key(KEY_E,false);move(Vector3.ZERO)
		if captures:save_frame("hospital-complete.png")
		return
	process_frame.disconnect(tick)
	for code in held.keys():key(code,false)
	DirAccess.make_dir_recursive_absolute(output)
	if captures and is_instance_valid(game):await save_frame("combined-final.png")
	var campaign=preload("res://scripts/campaign.gd")
	var report={"reason":reason,"seconds":elapsed,"hospital":hospital_trace,"cursor":campaign.read(),"resume_scene":campaign.saved_scene(),"in_forest":in_forest,"forest_complete":game.completed if in_forest else false,"forest_save_path":game.save_path if in_forest else "","transition_gap_frames":transition_gap_frames,"hero_teleports":0,"health_override":false,"human_playtest":false,"method":"ordinary keyboard/mouse from fresh hospital through evacuation, truth, departure and forest"}
	var file=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("HOSPITAL_FOREST_TOUR ",reason," seconds=",elapsed)
	if is_instance_valid(game):game.queue_free()
	await process_frame;await process_frame
	var until=Time.get_ticks_msec()+450
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if reason=="hospital departure and forest complete" else 1)
