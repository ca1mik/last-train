extends SceneTree
var game: Node3D
var model: Node3D
var animator: AnimationPlayer
var output="H:/game/release/motion-v038/candidate"
var character := "worker"

func _initialize() -> void:start.call_deferred()
func find_animation(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:return node
	for child in node.get_children():
		var found=find_animation(child)
		if found:return found
	return null

func start() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg=="--character=wraith":character="wraith";output="H:/game/release/motion-v038/candidate-wraith"
	game=load("res://main.tscn").instantiate();root.add_child(game);game.paused=true
	game.hero.visible=false
	for foe in game.enemies:foe.queue_free()
	game.enemies.clear()
	if game.ambient_particles:game.ambient_particles.visible=false
	for label in game.world_labels:label.visible=false
	model=load("res://assets/characters/motion-v38/"+character+".glb").instantiate();game.add_child(model);model.scale=Vector3.ONE*(1.78/4.805);model.position=Vector3(0,0,7)
	var light=OmniLight3D.new();game.add_child(light);light.position=model.position+Vector3(1,2,3);light.light_energy=3;light.omni_range=8
	animator=find_animation(model)
	print("CANDIDATE_CLIPS ",animator.get_animation_list())
	game.camera.size=3.2;var target=model.position+Vector3.UP*.85;game.camera.position=target+Vector3(3,2,5);game.camera.look_at(target)
	game.objective.text="Кандидат движения · не принятая анимация";game.radio.visible=false
	DirAccess.make_dir_recursive_absolute(output)
	var metadata={}
	for state in ["Idle","Walk","Jog","Sprint","Roll","Hurt","Death","Attack"]:
		var clip=""
		for name in animator.get_animation_list():
			if String(name).ends_with("Rail_"+state):clip=name;break
		if clip=="":push_error("Missing Rail_"+state);quit(1);return
		var length=animator.get_animation(clip).length;metadata[state]={"clip":clip,"seconds":length}
		for sample in [0.0,.25,.5,.75,.99]:
			animator.play(clip);animator.seek(sample*length,true);animator.pause();game.objective.text=state+" · "+str(snappedf(sample*length,.001))+" s"
			for i in range(3):await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(output.path_join(state.to_lower()+"-%02d.png"%int(sample*100)))
	var file=FileAccess.open(output.path_join("clips.json"),FileAccess.WRITE);file.store_string(JSON.stringify(metadata,"  "));file.close()
	game.queue_free();await process_frame;await process_frame
	quit()
