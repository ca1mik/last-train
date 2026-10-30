extends SceneTree
## Read the completed ordinary-input tour save; do not stage quest flags.
func _initialize() -> void:start.call_deferred()

func start() -> void:
	var game=load("res://expedition.tscn").instantiate();root.add_child(game);game.paused=true
	var location=game.patient.global_position
	var saved=game.mission==3 and game.cart_loaded
	var placed=game.patient.get_parent()==game and location.x> -41 and location.x< -37 and absf(location.z-30)<1 and location.y>1
	var consistent=game.latest_message().contains("Михаил в вагоне")
	var report={"completed_save_loaded":saved,"patient_in_carriage_volume":placed,"resume_line_consistent":consistent,"patient_position":[location.x,location.y,location.z],"scope":"Reload of the actual completed keyboard/mouse tour save; no staged quest/position changes"}
	var file=FileAccess.open("H:/game/release/expedition-v036/boarding-probe.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("BOARDING_PROBE ",report)
	game.queue_free();await process_frame;await process_frame;quit(0 if saved and placed and consistent else 1)
