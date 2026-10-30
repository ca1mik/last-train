extends SceneTree
## Actual mesh/collision/animation movement fixture; not a player playthrough.
var game: Node3D
var actors: Array=[]
var targets: Dictionary={}
var elapsed:=0.0
var flags: Dictionary={}
var samples: Array=[]
var output:="H:/game/release/companions-v047/locomotion"
func _initialize() -> void:start.call_deferred()
func once(id: String) -> bool:
	if flags.has(id):return false
	flags[id]=true;return true
func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name+".png"))
func start() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	game=load("res://hospital.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true
	for foe in game.enemies:foe.queue_free()
	game.enemies.clear();game.hero.position=Vector3(27,0,5);game.hero.reset_physics_interpolation();await physics_frame;await physics_frame
	var ids=["nina","lida","raisa"];var heights=[1.70,1.65,1.61]
	for i in range(3):
		var actor=preload("res://scripts/escort_actor.gd").new();game.add_child(actor);actor.setup(ids[i],"res://review_assets/companions-v047/"+ids[i]+".glb",heights[i]);actor.position=Vector3(32+i*3,0,-5);actor.reset_physics_interpolation();actors.append(actor)
	game.camera.size=12.5;var center=Vector3(37,.8,-4);game.camera.position=center+game.camera_offset;game.camera.look_at(center)
	game.health_bar.value=100;game.objective.text="КАНДИДАТЫ · НИНА / ЛИДА / РАИСА · НЕ УТВЕРЖДЕНЫ";game.radio.visible=false
	physics_frame.connect(tick)
func tick() -> void:
	elapsed+=1.0/60.0
	if elapsed>=3 and once("pause"):game.set_paused(true);shot("paused")
	if elapsed>=4 and once("resume"):game.set_paused(false);game.paused=true
	if not paused:
		for i in range(actors.size()):
			var actor=actors[i];var goal=Vector3(32+i*3,0,3) if elapsed<7 else Vector3(32+i*3,0,-4.5)
			var path=game.route(actor.position,goal)
			while not path.is_empty() and actor.position.distance_to(path[0])<.3:path.remove_at(0)
			var direction=(path[0]-actor.position).normalized() if not path.is_empty() and actor.position.distance_to(goal)>.35 else Vector3.ZERO
			actor.move_direction(direction,1.65,1.0/60.0)
			var skel=preload("res://scripts/carry_ik.gd").new().find_skeleton(actor)
			var left=skel.global_transform*skel.get_bone_global_pose(skel.find_bone("foot_l")).origin
			var right=skel.global_transform*skel.get_bone_global_pose(skel.find_bone("foot_r")).origin
			samples.append({"time":elapsed,"id":actor.actor_id,"root":str(actor.position),"speed":actor.ground_speed,"left_foot":str(left),"right_foot":str(right)})
	for stamp in [1,2,5,8,10]:
		if elapsed>=stamp and once(str(stamp)):shot("move-"+str(stamp))
	if elapsed>=12:finish()
func finish() -> void:
	physics_frame.disconnect(tick);game.set_paused(false)
	var file=FileAccess.open(output.path_join("samples.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"scope":"staged NPC movement/collisions/pose clocks/pause; not ordinary player route or final art acceptance","samples":samples,"candidate_status":"unapproved","gpu":RenderingServer.get_video_adapter_name()},"  "));file.close()
	game.queue_free();await process_frame;await process_frame
	var until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<until:await process_frame
	quit()
