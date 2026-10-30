extends SceneTree
var game: Node3D
var output := "H:/game/release/expedition-v036/gallery"

func _initialize() -> void:start.call_deferred()

func shot(name: String,point: Vector3,size:=11.8) -> void:
	game.hero.position=point;game.hero.reset_physics_interpolation()
	game.camera.size=size;game.camera.position=point+Vector3(0,.8,0)+game.camera_offset;game.camera.look_at(point+Vector3(0,.8,0))
	game.check_occlusion();game.update_occlusion(1.0)
	await process_frame;await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name+".png"))

func start() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps=0
	game=load("res://expedition.tscn").instantiate();root.add_child(game);game.paused=true
	for actor in [game.hero]+game.enemies:actor.advance_pose(0.0);actor.advance_pose(.5)
	DirAccess.make_dir_recursive_absolute(output)
	var points={"platform":Vector3(-26,0,27),"hall":Vector3(-23,0,2),"yard":Vector3(8,0,-3),"workshop":Vector3(-21,0,-29),"relay":Vector3(21,0,-30),"pharmacy":Vector3(46,0,-15),"service":Vector3(25,0,17)}
	for name in points:await shot(name,points[name])
	for label in game.world_labels:label.visible=false
	await shot("layout",Vector3(10,0,0),135)
	print("EXPEDITION_GALLERY 8 staged GPU screenshots; hero positions are fixtures, not playthrough")
	game.queue_free();await process_frame;await process_frame;quit()
