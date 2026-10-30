extends SceneTree
func _initialize() -> void:start.call_deferred()

func start() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var game=load("res://hospital.tscn").instantiate();root.add_child(game);game.paused=true
	await process_frame
	for foe in game.enemies:foe.advance_pose(.5)
	var output="H:/game/release/campaign-v037/gallery";DirAccess.make_dir_recursive_absolute(output)
	var shots={"arrival":game.DOCK,"panel":game.TEST,"switch":game.DRIVE,"refuge":game.REFUGE,"court":Vector3(12,0,1)}
	for id in shots:
		game.hero.position=shots[id];game.hero.reset_physics_interpolation();game.hero.advance_pose(.5)
		var target=game.hero.position+Vector3.UP*.8;game.camera.position=target+game.camera_offset
		for i in range(8):await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(output.path_join(id+".png"))
	game.camera.size=85;var center=Vector3(5,0,-1);game.camera.position=center+game.camera_offset;game.camera.look_at(center)
	for i in range(8):await process_frame
	await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(output.path_join("layout.png"))
	game.queue_free();await process_frame;await process_frame;quit()
