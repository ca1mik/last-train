extends SceneTree
var game: Node3D
var output := "H:/game/release/expedition-v036/carry"
var samples: Array = []

func _initialize() -> void:start.call_deferred()

func start() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED);Engine.max_fps=0
	game=load("res://expedition.tscn").instantiate();root.add_child(game);game.paused=true
	for label in game.world_labels:label.visible=false
	for actor in [game.hero]+game.enemies:actor.advance_pose(0);actor.advance_pose(.5)
	DirAccess.make_dir_recursive_absolute(output)
	game.objective.text="Проверка контакта рук · реальные модели и IK";game.radio.visible=false
	for heading in 8:
		var angle=heading*TAU/8;var direction=Vector3(sin(angle),0,cos(angle))
		game.cart.position=Vector3(47,0,-17);game.cart.rotation.y=angle
		game.hero.position=game.cart.position+direction*1.85;game.hero.face(direction,.016,true)
		game.hero.reset_physics_interpolation();game.cart.reset_physics_interpolation()
		for frame in 30:game.hero.advance_pose(1.0/60);game.carry_rig.apply(game.hero,game.cart,true,1.0/60)
		var center=game.cart.position+direction*.5+Vector3.UP*.7
		game.camera.size=4.8;game.camera.position=center+Vector3(4,5,6);game.camera.look_at(center)
		await process_frame;await RenderingServer.frame_post_draw
		var file="carry-%03d.png"%(heading*45)
		root.get_texture().get_image().save_png(output.path_join(file))
		samples.append({"heading":heading*45,"errors_m":game.carry_rig.errors.duplicate(),"file":file})
	var tool_states: Array=[]
	for node in game.carry_rig.tools:tool_states.append({"name":String(node.name),"visible":node.visible})
	var report=FileAccess.open(output.path_join("contact.json"),FileAccess.WRITE);report.store_string(JSON.stringify({"samples":samples,"tool_nodes":tool_states,"fixture":true,"limits":"Stationary contact fixture; does not prove moving contacts or final animation quality"},"  "));report.close()
	print("CARRY_REVIEW ",samples)
	game.queue_free();await process_frame;await process_frame;quit()
