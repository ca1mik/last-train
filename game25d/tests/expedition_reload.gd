extends SceneTree
var failures: Array = []

func _initialize() -> void:start.call_deferred()

func check(condition: bool,message: String) -> void:
	if not condition:failures.append(message);push_error(message)

func start() -> void:
	var game=load("res://expedition.tscn").instantiate();root.add_child(game);game.paused=true
	game.perform_action("stopper");game.perform_action("manual");game.perform_action("patient");game.perform_action("inner")
	game.hero.health=28;game.flares=1;game.supplies_taken=["hall"];game.killed=[0,1]
	game.save_checkpoint("Reload fixture")
	var expected_position=game.hero.position
	game.queue_free();await process_frame;await process_frame
	game=load("res://expedition.tscn").instantiate();root.add_child(game);game.paused=true
	check(game.mission==2 and game.cart_loaded,"reload retains evacuation state")
	check(game.inner_open and game.gates.inner.open,"reload retains physical open inner gate")
	check(not game.gates.service.open and not game.gates.hall_return.open,"reload retains closed return gates")
	check(game.hero.position.distance_to(expected_position)<.01,"reload retains checkpoint position")
	check(game.hero.health==28 and game.flares==1,"reload does not invent healing or ammunition")
	check(game.supplies_taken.has("hall"),"reload retains consumed supply")
	var alive_ids: Array=[]
	for foe in game.enemies:
		if is_instance_valid(foe) and foe.alive:alive_ids.append(foe.get_meta("id",-1))
	check(not alive_ids.has(0) and not alive_ids.has(1),"reload removes defeated checkpoint enemies")
	game.perform_action("supply:hall")
	check(game.hero.health==28 and game.flares==1,"reloaded supply cannot be farmed")
	var file=FileAccess.open(preload("res://tests/qa_report.gd").path("H:/game/release/expedition-v036/reload.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":8,"failures":failures,"scope":"Two real scene instantiations and persisted QA save; fixture-staged quest state"},"  "));file.close()
	print("EXPEDITION_RELOAD 8 checks; failures=",failures)
	game.queue_free();await process_frame;await process_frame
	await create_timer(.25).timeout
	quit(0 if failures.is_empty() else 1)
