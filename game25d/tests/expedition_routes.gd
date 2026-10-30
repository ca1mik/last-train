extends SceneTree

var game: Node3D
var checks := 0
var failures: Array = []
var output := "H:/game/release/expedition-v036"

func _initialize() -> void:start.call_deferred()

func check(condition: bool,message: String) -> void:
	checks+=1
	if not condition:failures.append(message);push_error(message)

func reachable(a: Vector3,b: Vector3) -> bool:
	var path=game.route(a,b)
	return not path.is_empty() and path[-1].distance_to(b)<2.0

func start() -> void:
	game=load("res://expedition.tscn").instantiate();root.add_child(game)
	await physics_frame
	game.paused=true
	check(reachable(game.DOCK,game.STOPPER),"platform reaches workshop")
	check(reachable(game.DOCK,game.GENERATOR),"platform reaches generator")
	check(reachable(game.GENERATOR,game.RELAY),"generator reaches relay panel")
	check(not reachable(game.MANUAL,game.PATIENT_POINT),"closed pharmacy blocks patient route")
	check(not game.visible_between(Vector3(-11,0,17),Vector3(-7,0,17)),"service gate blocks direct lower shortcut")
	game.perform_action("relay")
	check(game.mission==0,"unpowered relay cannot open pharmacy")
	game.perform_action("manual")
	check(game.mission==0,"manual door needs stopper")
	game.perform_action("stopper");game.perform_action("manual")
	game.paused=false
	for i in range(60):await physics_frame
	game.paused=true
	await process_frame;await process_frame
	check(game.mission==1 and game.door_method=="stopper","workshop branch opens pharmacy")
	check(game.gates.pharmacy.collider.disabled,"open pharmacy actually disables its collision shape")
	check(reachable(game.MANUAL,game.PATIENT_POINT),"open pharmacy becomes reachable")
	game.perform_action("patient")
	check(game.mission==2 and game.cart_loaded,"patient found starts evacuation, does not complete mission")
	check(not game.gates.hall_return.open,"old return gate closes after rescue starts")
	check(not reachable(game.PATIENT_POINT,game.DOCK),"closed return gates enforce alternate exit")
	game.perform_action("board")
	check(game.mission==2,"boarding impossible when stretcher still in pharmacy")
	game.perform_action("inner");game.perform_action("service")
	check(reachable(game.PATIENT_POINT,game.DOCK),"alternate exit reaches train after both bolts")
	check(game.cart.collision_layer==8 and game.cart.collision_mask==1,"stretcher has world collision")
	game.hero.health=40;game.flares=1;game.perform_action("supply:hall")
	var health=game.hero.health;var flares=game.flares
	game.perform_action("supply:hall")
	check(game.hero.health==health and game.flares==flares,"supply cannot be farmed twice")
	game.save_checkpoint("QA restore")
	game.power_on=false;game.has_stopper=false;game.cart_loaded=false;game.inner_open=false
	game.apply_checkpoint()
	await process_frame;await process_frame
	check(game.has_stopper and game.cart_loaded and game.inner_open,"checkpoint restores quest and physical exit state")
	check(game.gates.inner.open and game.gates.service.open,"checkpoint restores open colliders")
	check(game.gates.inner.collider.disabled and game.gates.service.collider.disabled,"restored exits disable physical collision shapes")
	game.mission=0;game.set_gate("pharmacy",false,true);game.power_on=false
	game.perform_action("generator");game.perform_action("relay")
	check(game.mission==1 and game.door_method=="power","generator branch opens pharmacy")
	check(game.enemies.size()==22,"authored encounter actors exist, no infinite wave loop")
	DirAccess.make_dir_recursive_absolute(output)
	var file=FileAccess.open(preload("res://tests/qa_report.gd").path(output.path_join("routes.json")),FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,"scope":"Fixture-staged state/route/collision checks; not ordinary-input playthrough or visual acceptance"},"  "));file.close()
	print("EXPEDITION_ROUTES ",checks," checks; failures=",failures)
	game.queue_free();await process_frame;await process_frame
	await create_timer(.25).timeout
	quit(0 if failures.is_empty() else 1)
