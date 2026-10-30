extends SceneTree
var game: Node3D
var checks:=0
var failures: Array=[]
var output:="H:/game/release/reception-v046/rules.json"
func _initialize() -> void:start.call_deferred()
func check(ok: bool,message: String) -> void:
	checks+=1
	if not ok:failures.append(message);push_error(message)
func frames(n: int) -> void:
	for i in range(n):await physics_frame
func key(down: bool) -> void:
	var event=InputEventKey.new();event.keycode=KEY_E;event.physical_keycode=KEY_E;event.pressed=down;Input.parse_input_event(event);Input.flush_buffered_events()
func create(reset:=false) -> void:
	if reset and FileAccess.file_exists("user://hospital-qa-reception-rules-v046.json"):DirAccess.remove_absolute("user://hospital-qa-reception-rules-v046.json")
	game=load("res://hospital.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true;await frames(3)
func remove() -> void:
	game.set_paused(false);game.queue_free();await frames(3)
func wait_motion() -> void:await create_timer(.65).timeout
func blocked(a: Vector3,b: Vector3) -> bool:
	return not game.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1)).is_empty()
func start() -> void:
	DirAccess.make_dir_recursive_absolute(output.get_base_dir())
	await create(true)
	check(not game.reception.known and not game.reception.all_ready(),"fresh receiving is not implicitly complete")
	check(game.objective_position()==game.REFUGE,"first objective introduces the people before proposing machinery")
	game.perform_action("receive_confirm");check(not game.reception.ready_confirmed,"cannot confirm before meeting people/preparing anything")
	check(game.get_node_or_null("MikhailInWagon")!=null,"existing Mikhail mesh remains visible separately from four hospital residents")
	var ward_clear=true
	for foe in game.enemies:
		if Rect2(28,-12,18,20).has_point(Vector2(foe.position.x,foe.position.z)):ward_clear=false
	check(ward_clear,"no hostile starts among the waiting residents' beds")
	check(game.route(game.DOCK,game.reception.INPUT).size()>8,"actual wagon entrance and interior have a navigation route")
	check(game.inside_floor(Vector2(-36,24.5)) and game.inside_floor(Vector2(-34.5,24.5)),"interior and doorway are connected real floor")
	game.perform_action("refuge");check(game.reception.known and not game.refuge_heard,"early meeting enables independent preparation without faking post-route contact")
	game.hero.position=game.reception.INPUT;game.hero.reset_physics_interpolation();await frames(3)
	key(true)
	for i in range(18):game.interactions(1.0/60);await physics_frame
	key(false);game.interactions(1.0/60)
	check(not game.reception.input_checked and game.work==0,"released E interrupts receiving inspection")
	game.hero.stun=.5;key(true);game.interactions(.7);key(false);game.interactions(.016)
	check(not game.reception.input_checked,"stunned hero cannot complete a held interaction")
	game.hero.stun=0;key(true)
	for i in range(42):game.interactions(1.0/60);await physics_frame
	key(false);game.interactions(.016)
	check(game.reception.input_checked,"actual held E completes inspection inside wagon")
	check(blocked(Vector3(-36,.35,24.4),Vector3(-37.7,.35,24.4)),"luggage is a real collision before moving")
	game.perform_action("receive_aisle");await create_timer(.12).timeout
	game.set_paused(true);var held_luggage=game.reception.luggage.position;await create_timer(.2,true).timeout
	check(game.reception.luggage.position==held_luggage and not game.reception.aisle_clear,"visible pause freezes actual prop motion and its completion")
	game.set_paused(false);game.paused=true;await wait_motion()
	check(game.reception.aisle_clear and not game.obstacles.has(game.reception.luggage_rect),"luggage visibly relocates and its old navigation obstruction is removed")
	check(not blocked(Vector3(-36,.35,24.4),Vector3(-37.7,.35,24.4)),"old luggage position really becomes physically clear")
	var saved=game.reception.save();game.save_checkpoint();await remove();await create()
	check(game.reception.save()==saved,"real scene reconstruction preserves independently completed receiving steps")
	check(game.reception.luggage.position.distance_to(Vector3(-38,.22,30.6))<.01,"restored luggage stays under original passenger's bed")
	check(not game.reception.bag_ready and not game.reception.path_clear,"reload does not complete unrelated preparations")
	check(blocked(Vector3(27,.85,-1.9),Vector3(29,.85,-1.9)),"portable screen initially occupies the narrow part of the doorway")
	game.perform_action("receive_passage");await wait_motion()
	check(not blocked(Vector3(27,.85,-1.9),Vector3(29,.85,-1.9)),"folded screen physically opens the wider doorway")
	await remove()
	var orders=[["wagon","bag","path"],["wagon","path","bag"],["bag","wagon","path"],["bag","path","wagon"],["path","wagon","bag"],["path","bag","wagon"]]
	for order in orders:
		await create(true);game.reception.known=true
		for part in order:
			if part=="wagon":game.perform_action("receive_input");game.perform_action("receive_aisle")
			elif part=="bag":game.perform_action("receive_bag")
			else:game.perform_action("receive_passage")
			await wait_motion()
		check(game.reception.receiving_ready() and game.reception.bag_ready and game.reception.path_clear,"independent preparation order works: "+str(order))
		check(not game.reception.all_ready(),"preparing people never substitutes for locking train route: "+str(order))
		game.complete_route("power");game.update_objective()
		check(game.reception.all_ready(),"route can be the last independent requirement: "+str(order))
		game.perform_action("receive_confirm")
		check(game.reception.ready_confirmed and game.refuge_heard,"one final confirmation acknowledges complete preparation: "+str(order))
		var stable=FileAccess.get_file_as_string(game.save_path);game.perform_action("receive_confirm");game.perform_action("receive_bag")
		check(FileAccess.get_file_as_string(game.save_path)==stable,"repeated preparations do not rewrite checkpoint or issue duplicates: "+str(order))
		check(game.mission==1 and game.reception.bag.position.x>30,"preparation keeps people and medical bag at refuge until actual evacuation")
		await remove()
	var old=JSON.parse_string(FileAccess.get_file_as_string("user://hospital-qa-reception-rules-v046.json"));old.erase("reception")
	var migration=FileAccess.open("user://hospital-qa-reception-rules-v046.json",FileAccess.WRITE);migration.store_string(JSON.stringify(old));migration.close()
	await create()
	check(not game.reception.receiving_ready() and not game.reception.bag_ready and game.obstacles.has(game.reception.luggage_rect),"real old save without receiving fields never gets automatic completion or moved luggage")
	await remove()
	var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures,"scope":"fixture positions, actual held E/interruption, six orders and real scene reconstruction; preparation only, not physical evacuation or human playtest"},"  "));file.close()
	print("RECEPTION_RULES ",checks," failures=",failures)
	var until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if failures.is_empty() else 1)
