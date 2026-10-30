extends SceneTree
## Explicit staging for camera/transfer/wagon inspection, not a player route.
var game: Node3D
var out:="H:/game/release/evacuation-v047/visual"
var records: Array=[]
func _initialize() -> void:start.call_deferred()
func frames(n: int) -> void:
	for i in range(n):await physics_frame
func shot(name: String) -> void:
	await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(out.path_join(name+".png"));records.append(name)
func move_camera(point: Vector3,size: float) -> void:
	game.camera.position=point+game.camera_offset;game.camera.look_at(point);game.camera.size=size
func start() -> void:
	DirAccess.make_dir_recursive_absolute(out)
	game=load("res://hospital.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true;await frames(3)
	for foe in game.enemies:foe.queue_free()
	game.enemies.clear();await frames(3)
	game.reception.known=true;game.reception.input_checked=true;game.reception.aisle_clear=true;game.reception.bag_ready=true;game.reception.path_clear=true;game.reception.ready_confirmed=true;game.reception.apply_visuals();game.mission=1
	var evac=game.evacuation;var last=evac.transport;evac.stage="first_received";evac.boarded.assign(evac.FIRST)
	for id in evac.FIRST:
		var p=Vector3(-38.25,0,evac.SEAT_Z[id])-Basis(Vector3.UP,PI/2)*evac.people[id].sit_offset;p.y=0;evac.people[id].sit_at(p,PI/2)
	last.state="bedside";last.cart.position=last.LOAD_POINT;last.cart.reset_physics_interpolation();evac.people.nina.position=Vector3(40.5,0,-3.5);evac.people.lida.position=Vector3(42,0,-4.8)
	game.hero.position=Vector3(41.5,0,-8.35);game.hero.reset_physics_interpolation();game.paused=false;await frames(30);game.paused=true
	move_camera(Vector3(42,.8,-6.3),7);await frames(3);await shot("bedside")
	game.perform_action("evac_last_load");game.paused=false;await frames(65);game.paused=true;move_camera(Vector3(42,.8,-6.3),7);await frames(3);await shot("transfer-mid")
	game.paused=false;await frames(95);game.paused=true;move_camera(Vector3(42,.8,-6.3),7);await frames(3);await shot("patient-loaded")
	game.hero.position=game.reception.BAG+Vector3(-.9,0,0);game.hero.reset_physics_interpolation();game.paused=false;await frames(210);game.paused=true
	game.perform_action("evac_last_bag");await frames(40);move_camera(Vector3(37.3,.9,1),6);await frames(3);await shot("bag-with-lida")
	last.cart.position=last.PARK;last.cart.rotation.y=0;last.cart.reset_physics_interpolation();evac.people.nina.position=Vector3(-36.2,0,27.5);evac.people.lida.position=Vector3(-36.2,0,22);game.hero.position=last.TALK
	for actor in [game.hero,evac.people.nina,evac.people.lida]:actor.reset_physics_interpolation()
	game.paused=false;await frames(12);game.paused=true;game.perform_action("evac_last_receive")
	move_camera(Vector3(-37,.7,24),18);await frames(3);await shot("wagon-overview")
	move_camera(Vector3(-37.8,.7,22),5.4);await frames(3);await shot("raisa-seat")
	move_camera(Vector3(-36.8,.7,24),6);await frames(3);await shot("fourth-in-wagon")
	game.hero.position=last.TALK;game.perform_action("evac_truth");await frames(3);await shot("wagon-question")
	var event=InputEventKey.new();event.keycode=KEY_2;event.physical_keycode=KEY_2;event.pressed=true;root.push_input(event,true);await frames(3);await shot("wagon-answer")
	last.question.close()
	var report={"scope":"explicit staged positions and completed preparation/first group; actual fourth transfer/physics and paused question; not ordinary-input playthrough","images":records,"transport":last.snapshot(),"gpu":RenderingServer.get_video_adapter_name(),"art_status":"unapproved draft; clothing, age, contacts and shadows remain under review"}
	var file=FileAccess.open(out.path_join("manifest.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	game.set_paused(false);game.queue_free();await frames(3)
	var until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<until:await process_frame
	quit()
