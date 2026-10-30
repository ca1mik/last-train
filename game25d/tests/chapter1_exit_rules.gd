extends SceneTree
var checks := 0
var failures: Array=[]
var game: Node3D
func _initialize() -> void:start.call_deferred()
func check(ok: bool,message: String) -> void:
	checks+=1
	if not ok:failures.append(message);push_error(message)
func key(down: bool) -> void:
	var event=InputEventKey.new();event.keycode=KEY_E;event.physical_keycode=KEY_E;event.pressed=down;Input.parse_input_event(event);Input.flush_buffered_events()
func frames(count: int) -> void:
	for i in range(count):await physics_frame
func reachable(a: Vector3,b: Vector3) -> bool:
	var path=game.route(a,b)
	return not path.is_empty() and path[-1].distance_to(b)<1.5
func start() -> void:
	game=load("res://expedition.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true
	await frames(3)
	var operation=game.exit_stage
	check(not reachable(game.DOCK,operation.DRIVE),"exit courtyard blocked before rescue")
	check(not game.gates.exit_west.collider.disabled and not game.gates.exit_north.collider.disabled,"both physical entry gates closed")
	game.hero.position=game.DOCK;game.perform_action("exit_begin")
	check(operation.stage==0,"exit cannot start before boarding")
	# Explicit fixture: rescue itself is covered by ordinary-input chapter1_tour.
	game.mission=2;game.cart_loaded=true;game.cart.position=game.DOCK+Vector3(2.4,0,0);game.perform_action("board")
	game.perform_action("depart")
	check(operation.stage==0 and current_scene==game,"boarding alone cannot depart")
	var old_checkpoint=game.checkpoint.duplicate(true);old_checkpoint.erase("exit_stage");game.checkpoint=old_checkpoint;game.apply_checkpoint()
	check(game.mission==3 and operation.stage==0,"legacy boarded save defaults to unstarted exit without losing rescue")
	game.hero.position=game.DOCK
	game.paused=false;key(true);await frames(15);key(false);await frames(3)
	check(operation.stage==0 and game.work==0,"short E is interrupted without progress")
	key(true);await frames(55)
	check(operation.stage==1,"actual held E starts exit after boarding")
	await frames(50)
	check(operation.stage==1,"holding E does not consume next step")
	key(false);await frames(3);game.paused=true
	game.set_gate("exit_west",true,true);game.set_gate("exit_north",true,true);await frames(2)
	check(game.gates.exit_west.collider.disabled and game.gates.exit_north.collider.disabled,"opened gates remove physical blockers")
	check(reachable(game.DOCK,operation.ISOLATOR),"west entrance reaches isolator")
	check(reachable(Vector3(19,0,18),operation.DRIVE),"north entrance reaches drive")
	check(reachable(operation.ISOLATOR,operation.DRIVE) and reachable(operation.DRIVE,game.DOCK),"internal bypass and return route connected")
	game.hero.position=operation.DRIVE;game.perform_action("exit_clear");game.perform_action("exit_throw");game.perform_action("exit_lock")
	check(operation.stage==1 and operation.debris.visible,"wrong order does not clear or move drive")
	game.perform_action("exit_isolate")
	check(operation.stage==1,"remote isolator call rejected")
	game.hero.position=operation.ISOLATOR;game.perform_action("exit_isolate")
	check(operation.stage==2,"local isolation succeeds")
	game.perform_action("exit_isolate")
	check(operation.stage==2,"completed stage cannot be toggled off or repeated")
	game.hero.health=37;game.flares=1;game.save_checkpoint("QA partial exit")
	game.queue_free();await process_frame;await process_frame
	game=load("res://expedition.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true;operation=game.exit_stage;await frames(2)
	check(operation.stage==2 and game.gates.exit_west.open,"real reload resumes intermediate stage and gates")
	check(game.hero.health==37 and game.flares==1,"reload invents no healing or ammunition")
	check(game.mission==3 and game.patient.get_parent()==game and game.patient.global_position.x< -36,"Mikhail remains physically in carriage")
	game.hero.position=operation.BELL;game.perform_action("exit_bell")
	check(operation.bell_left>0 and operation.bell_cooldown>0,"local reusable sound lure starts")
	operation.bell_left=3;game.perform_action("exit_bell")
	check(operation.bell_left==3,"sound lure observes cooldown")
	game.hero.position=operation.DRIVE;game.perform_action("exit_clear")
	check(operation.stage==3 and not operation.debris.visible,"clear removes visible obstruction after isolation")
	game.perform_action("exit_throw")
	check(operation.stage==4,"manual drive and locking are distinct")
	game.hero.position=game.DOCK;game.perform_action("lida_door");game.perform_action("depart")
	check(operation.stage==4 and current_scene==game,"unlocked drive cannot board Lida or depart")
	game.hero.position=operation.LOCK;game.perform_action("exit_lock")
	check(operation.stage==5,"separate lock check completes route")
	game.hero.position=game.DOCK;game.perform_action("lida_door")
	check(operation.stage==6 and game.checkpoint.get("exit_stage")==6,"manual passenger door persists separately from departure")
	operation.restore(6)
	check(operation.door.position.z>31,"restored passenger door is visually open")
	DirAccess.make_dir_recursive_absolute("H:/game/release/chapter1-v039")
	var file=FileAccess.open(preload("res://tests/qa_report.gd").path("H:/game/release/chapter1-v039/rules.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,"scope":"fixture rescue/positions; actual E interrupt/start; real save/reload; not human playtest"},"  "));file.close()
	operation=null;game.queue_free();game=null;await process_frame;await process_frame
	var drain_until=Time.get_ticks_msec()+500
	while Time.get_ticks_msec()<drain_until:await process_frame
	print("CHAPTER1_EXIT_RULES ",checks," checks; failures=",failures);quit(0 if failures.is_empty() else 1)
