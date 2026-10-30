extends SceneTree
## Isolated movement fixture; not an input-driven mission playthrough.
var game: Node3D
var elapsed := 0.0
var samples: Array = []
var start_basis: Basis
var report_path := "H:/game/release/expedition-v036/carry-motion.json"

func _initialize() -> void:start.call_deferred()

func start() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--carry-output="):report_path=arg.trim_prefix("--carry-output=")
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED);Engine.max_fps=0
	game=load("res://expedition.tscn").instantiate();root.add_child(game);game.paused=true
	for foe in game.enemies:foe.queue_free()
	game.enemies.clear()
	for label in game.world_labels:label.visible=false
	game.hero.position=Vector3(4,0,0);game.hero.face(Vector3.BACK,.016,true);game.hero.reset_physics_interpolation()
	game.cart.position=Vector3(4,0,-1.85);game.cart.rotation.y=0;game.cart.reset_physics_interpolation();game.cart_loaded=true;game.cart_attached=true;game.cart_path.clear();game.cart_path.append(game.hero.position)
	var center=(game.hero.position+game.cart.position)*.5+Vector3.UP*.7
	game.camera.size=6.8;game.camera.position=center+Vector3(4,5,6);game.camera.look_at(center);start_basis=game.camera.basis
	game.objective.text="Проверка движения с носилками · поворот / остановка / отпускание";game.radio.visible=false
	physics_frame.connect(tick);process_frame.connect(follow_camera)

func follow_camera() -> void:
	var center=(game.hero.get_global_transform_interpolated().origin+game.cart.get_global_transform_interpolated().origin)*.5+Vector3.UP*.7
	game.camera.position=center+Vector3(4,5,6)

func tick() -> void:
	var delta=1.0/60;elapsed+=delta
	if elapsed>=13:finish();return
	var direction=Vector3.ZERO
	if elapsed>.7 and elapsed<3:direction=Vector3.BACK
	elif elapsed>=3 and elapsed<5:direction=Vector3.RIGHT
	elif elapsed>=5 and elapsed<7:direction=Vector3.FORWARD
	elif elapsed>=7 and elapsed<9:direction=Vector3.LEFT
	elif elapsed>=11:direction=Vector3.BACK
	game.cart_attached=elapsed<10
	game.hero.clocks(delta);game.hero.move_ground(direction,2.65,delta);game.hero.advance_pose(delta)
	game.update_cart(delta);game.carry_rig.apply(game.hero,game.cart,game.cart_attached,delta)
	if elapsed>.6 and elapsed<9.5:samples.append({"t":elapsed,"L":game.carry_rig.errors.get("L",0),"R":game.carry_rig.errors.get("R",0),"distance":game.hero.position.distance_to(game.cart.position),"hero":game.vec(game.hero.position),"cart":game.vec(game.cart.position)})
	game.check_occlusion();game.update_occlusion(delta)

func finish() -> void:
	physics_frame.disconnect(tick)
	process_frame.disconnect(follow_camera)
	var path=report_path
	var file=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify({"seconds":elapsed,"fps":60,"samples":samples,"fixture":true,"root_movement":"CharacterBody3D controller and colliding cart","limits":"No enemies; fixture input and staged start; contact metrics are not final visual acceptance","main_sha256":FileAccess.get_sha256("res://scripts/main.gd"),"actor_sha256":FileAccess.get_sha256("res://scripts/actor.gd"),"carry_sha256":FileAccess.get_sha256("res://scripts/carry_ik.gd")},"  "));file.close()
	print("CARRY_MOTION_COMPLETE ",elapsed)
	quit()
