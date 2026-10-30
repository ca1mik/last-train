extends SceneTree
var checks := 0
var failures: Array = []

func _initialize() -> void:start.call_deferred()
func check(condition: bool,message: String) -> void:
	checks+=1
	if not condition:failures.append(message);push_error(message)

func press(code: int) -> void:
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true;Input.parse_input_event(event)
	var release=InputEventKey.new();release.keycode=code;release.physical_keycode=code;release.pressed=false;Input.parse_input_event(release)

func settle() -> void:
	for i in range(8):await process_frame

func start() -> void:
	var source=FileAccess.get_file_as_string("user://qa-final-native-v036.json")
	var copy=FileAccess.open("user://qa-controls-v036.json",FileAccess.WRITE);copy.store_string(source);copy.close()
	var game=load("res://expedition.tscn").instantiate();root.add_child(game);current_scene=game
	await settle()
	check(game.mission==3,"completed ordinary-input save loaded for controls probe")
	var visible_before=game.map_view.visible
	press(KEY_M);await settle();check(game.map_view.visible!=visible_before,"M hides the map")
	press(KEY_M);await settle();check(game.map_view.visible==visible_before,"M restores the map")
	game.player_down=true;game.hero.alive=false
	press(KEY_R);await settle();game=current_scene
	check(is_instance_valid(game) and not game.player_down and game.hero.alive,"R rebuilds playable scene after staged death")
	check(game.mission==3,"R retains completed checkpoint state")
	check(game.patient.get_parent()==game,"R restores patient in carriage rather than on stretcher")
	press(KEY_N);await settle();game=current_scene
	check(game.mission==0 and not game.cart_loaded,"N starts a new expedition after completion")
	check(game.hero.position.distance_to(game.DOCK+Vector3(3,0,-2))<.5,"new expedition returns to the intended start")
	var file=FileAccess.open("H:/game/release/expedition-v036/controls.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,"input":"actual M/R/N keyboard events","scope":"Map full cycle; restart after fixture-staged death; new game using a copy of the completed tour save"},"  "));file.close()
	print("EXPEDITION_CONTROLS ",checks," checks; failures=",failures)
	game.queue_free();await process_frame;await process_frame;await create_timer(.25).timeout
	quit(0 if failures.is_empty() else 1)
