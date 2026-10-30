extends SceneTree
var checks := 0
var failures: Array=[]
const CURSOR=preload("res://scripts/campaign.gd")

func _initialize() -> void:start.call_deferred()
func check(condition: bool,message: String) -> void:
	checks+=1
	if not condition:failures.append(message);push_error(message)

func press(code: int,down: bool) -> void:
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=down;Input.parse_input_event(event)

func start() -> void:
	var game=load("res://expedition.tscn").instantiate();root.add_child(game);current_scene=game
	game.paused=true;await process_frame
	# Staged completed rescue isolates the departure interaction; the full rescue
	# remains covered by expedition_tour, not claimed as replayed here.
	game.mission=2;game.cart_loaded=true;game.cart.position=game.DOCK;game.hero.position=game.DOCK
	game.perform_action("board")
	check(game.mission==3 and game.patient.get_parent()==game,"fixture boards patient before departure")
	# Exit mechanism/door are fixture-completed here; their real input route has
	# separate chapter1_tour coverage. This test isolates the actual scene handoff.
	game.exit_stage.restore(6)
	var first_path=game.save_path;var original=FileAccess.get_file_as_string(first_path)
	check(CURSOR.path().begins_with("user://campaign-qa-"),"campaign test is isolated from player cursor")
	game.paused=false;press(KEY_E,true)
	for i in range(65):await physics_frame
	press(KEY_E,false);await process_frame;await process_frame
	game=current_scene
	check(game.scene_file_path==CURSOR.HOSPITAL,"actual held E at carriage changes level")
	check(CURSOR.saved_scene()==CURSOR.HOSPITAL and CURSOR.read().get("mikhail_boarded",false),"campaign cursor persists arrival chapter independently of preview")
	check(CURSOR.read().get("chapter",0)==2,"saved JSON chapter survives numeric round trip")
	check(FileAccess.get_file_as_string(first_path)==original,"departure preserves expedition checkpoint byte-for-byte")
	check(game.mission==0 and game.hero.position.distance_to(game.DOCK)<.5,"hospital starts at intended arrival")
	game.paused=true;game.perform_action("winch");game.perform_action("manual");var hospital_path=game.save_path
	var result=change_scene_to_file("res://campaign.tscn");check(result==OK,"campaign boot scene can be loaded")
	for i in range(12):await process_frame
	game=current_scene;game.paused=true
	check(game.scene_file_path==CURSOR.HOSPITAL and game.winch_stage==1,"boot resumes hospital checkpoint instead of replaying first rescue")
	check(game.save_path==hospital_path,"hospital retains separate checkpoint filename")
	DirAccess.make_dir_recursive_absolute("H:/game/release/campaign-v037")
	var file=FileAccess.open(preload("res://tests/qa_report.gd").path("H:/game/release/campaign-v037/transition.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures,"scope":"fixture boarding; actual E departure; persisted boot/load"},"  "));file.close()
	game.queue_free();await process_frame;await process_frame;await create_timer(.5).timeout
	print("CAMPAIGN_TRANSITION ",checks," checks; failures=",failures);quit(0 if failures.is_empty() else 1)
