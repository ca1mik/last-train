extends SceneTree
var checks := 0
var failures: Array=[]
var game: Node3D

func _initialize() -> void:start.call_deferred()
func check(condition: bool,message: String) -> void:
	checks+=1
	if not condition:failures.append(message);push_error(message)

func start() -> void:
	game=load("res://hospital.tscn").instantiate();root.add_child(game);game.paused=true
	await process_frame
	for target in [game.JUMPER,game.WINCH,game.SOCKET,game.FEED_A,game.FEED_B,game.TEST,game.DRIVE,game.REFUGE]:
		var route=game.route(game.DOCK,target);check(not route.is_empty() and route[-1].distance_to(target)<1.0,"reachable interactable "+str(target))
	game.perform_action("test");check(not game.tested and game.reserve_on,"bad check cannot disable medical reserve")
	game.perform_action("drive");game.perform_action("manual");check(game.mission==0 and game.winch_stage==0,"neither route completes without its prerequisite")
	game.perform_action("feed_a");game.perform_action("feed_b");game.perform_action("test")
	check(not game.tested and game.reserve_on,"two feeds cannot bridge missing jumper")
	game.perform_action("jumper");game.perform_action("install");game.perform_action("test")
	check(game.tested and game.mission==0,"panel success still requires separate physical drive")
	game.perform_action("feed_a");check(game.feed_a,"tested panel cannot be accidentally reset")
	game.perform_action("drive");check(game.mission==1 and game.route_method=="power" and game.reserve_on,"electrical branch completes only route, reserve unchanged")
	game.perform_action("manual");check(game.winch_stage==0,"completed electrical route cannot run manual sequence")
	game.mission=0;game.tested=false;game.route_method="";game.has_winch=false;game.winch_stage=0
	game.perform_action("winch")
	for i in range(7):game.perform_action("manual")
	check(game.mission==0 and game.winch_stage==4 and game.winch_turns==4,"four manual turns still require final lock")
	game.hero.health=47;game.flares=1;game.perform_action("supply:west")
	check(game.hero.health==92 and game.flares==2,"finite supply restores defined health and flare")
	game.perform_action("supply:west");check(game.hero.health==92 and game.flares==2,"supply cannot be reused")
	game.save_checkpoint();game.queue_free();await process_frame;await process_frame;await create_timer(.25).timeout
	game=load("res://hospital.tscn").instantiate();root.add_child(game);game.paused=true;await process_frame
	check(game.winch_stage==4 and game.has_winch and game.mission==0,"interrupted manual sequence survives scene reconstruction")
	check(game.latest_message().contains("замок"),"resumed journal names unfinished lock rather than sending player for an owned tool")
	check(game.hero.health==92 and game.flares==2 and game.supplies.has("west"),"health/ammo/supply survive reload without free healing")
	game.perform_action("manual");check(game.mission==1 and game.route_method=="winch","manual route resumes and locks")
	game.perform_action("refuge");check(game.latest_message().contains("четверо") and game.latest_message().contains("Михаил остался"),"refuge inhabitants distinct from Mikhail; no evacuation claim")
	DirAccess.make_dir_recursive_absolute("H:/game/release/campaign-v037")
	var file=FileAccess.open(preload("res://tests/qa_report.gd").path("H:/game/release/campaign-v037/rules.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures,"scope":"staged state/guard/navigation/save fixtures, NOT human playtest"},"  "));file.close()
	game.queue_free();await process_frame;await process_frame;await create_timer(.25).timeout
	print("HOSPITAL_RULES ",checks," checks; failures=",failures);quit(0 if failures.is_empty() else 1)
