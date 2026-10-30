extends SceneTree
var game: Node3D
var output:="H:/game/release/reception-v046/gallery"
func _initialize() -> void:start.call_deferred()
func shot(name: String,point: Vector3,size:=11.8) -> void:
	game.hero.position=point;game.hero.reset_physics_interpolation();game.camera.size=size
	var target=point+Vector3.UP*.8;game.camera.position=target+game.camera_offset;game.camera.look_at(target)
	game.check_occlusion();game.update_occlusion(1)
	for label in game.world_labels:label.visible=label.position.distance_to(point)<5
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name+".png"))
func start() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	game=load("res://hospital.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true
	await physics_frame;await physics_frame
	for actor in [game.hero]+game.enemies:actor.update_motion(.016);actor.advance_pose(.6)
	game.reception.known=true;game.update_objective();game.health_bar.value=game.hero.health;game.status.text="АРТЁМ · 100 / 100"
	await shot("01-wagon-entry",Vector3(-33,0,24.5))
	await shot("02-wagon-passenger",Vector3(-36.5,0,29),7.5)
	await shot("03-input-unchecked",game.reception.INPUT,7.5)
	game.perform_action("receive_input")
	await shot("04-input-checked",game.reception.INPUT,7.5)
	await shot("05-aisle-before",game.reception.AISLE,7.5)
	game.perform_action("receive_aisle");await create_timer(.6).timeout
	await shot("06-aisle-clear",game.reception.AISLE,7.5)
	await shot("07-bag-at-refuge",game.reception.BAG,7.5)
	game.perform_action("receive_bag");await shot("08-bag-prepared-stays",game.reception.BAG,7.5)
	await shot("09-narrow-passage",game.reception.PASSAGE,7.5)
	game.perform_action("receive_passage");await create_timer(.6).timeout
	await shot("10-wide-passage",game.reception.PASSAGE,7.5)
	await shot("11-refuge-room",Vector3(38,0,-5.5),12.5)
	var file=FileAccess.open(output.path_join("manifest.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"fixture":true,"gpu":RenderingServer.get_video_adapter_name(),"scope":"staged viewpoints and preparation props; existing Mikhail, no new approved NPC models","hospital_sha256":FileAccess.get_sha256("res://scripts/hospital.gd"),"reception_sha256":FileAccess.get_sha256("res://scripts/hospital_reception.gd")},"  "));file.close()
	game.queue_free();await process_frame;await process_frame
	var until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<until:await process_frame
	quit()
