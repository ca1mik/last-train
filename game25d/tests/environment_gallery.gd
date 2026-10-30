extends SceneTree
func _initialize() -> void:start.call_deferred()
func start() -> void:
	var output="H:/game/release/environment-v044/gallery";DirAccess.make_dir_recursive_absolute(output)
	var records=[]
	for scene in ["hospital","forest","wasteland"]:
		var game=load("res://"+scene+".tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true
		await physics_frame;await physics_frame
		for actor in [game.hero]+game.enemies:
			actor.update_motion(.016);actor.advance_pose(.6)
		var points=[Vector3(-22,0,16),Vector3(11,0,5),Vector3(36,0,-8.5),Vector3(-23,0,-28)] if scene=="hospital" else [Vector3(-20,0,14),Vector3(-15,0,-16),Vector3(16,0,-12),Vector3(4,0,8)]
		for i in points.size():
			game.hero.position=points[i];game.hero.reset_physics_interpolation();var center=points[i]+Vector3.UP*.8;game.camera.position=center+game.camera_offset;game.camera.look_at(center)
			game.check_occlusion();game.update_occlusion(1.0)
			for label in game.world_labels:label.visible=label.position.distance_to(points[i])<5
			game.health_bar.value=game.hero.health;game.status.text="АРТЁМ · "+str(int(game.hero.health))+" / 100"
			for j in range(3):await process_frame
			await RenderingServer.frame_post_draw
			var filename=scene+"-%02d.png"%i;var im=root.get_texture().get_image();im.save_png(output.path_join(filename));records.append({"file":filename,"width":im.get_width(),"height":im.get_height(),"fixture":true,"hero_position":str(points[i])})
		game.queue_free();await process_frame;await process_frame
	var selector=load("res://locations.tscn").instantiate();root.add_child(selector);await process_frame;await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(output.path_join("locations.png"));selector.queue_free();await process_frame
	var file=FileAccess.open(output.path_join("manifest.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"renderer":RenderingServer.get_current_rendering_method(),"gpu":RenderingServer.get_video_adapter_name(),"captures":records,"scope":"staged viewpoints; no playthrough claim"},"  "));file.close();quit()
