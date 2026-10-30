extends SceneTree
var failures: Array=[]
var checks:=0
func _initialize() -> void:start.call_deferred()
func frames(n: int) -> void:
	for i in range(n):await process_frame
func check(ok: bool,message: String) -> void:
	checks+=1
	if not ok:failures.append(message);push_error(message)
func start() -> void:
	var campaign=preload("res://scripts/campaign.gd");var before=FileAccess.get_file_as_string(campaign.path()) if FileAccess.file_exists(campaign.path()) else ""
	for scene in ["hospital","forest","wasteland"]:
		var menu=load("res://locations.tscn").instantiate();root.add_child(menu);current_scene=menu;await frames(3)
		# Button signal exercises the same callback as a click, not scene mutation.
		var index=["hospital","forest","wasteland"].find(scene);var buttons: Array=[]
		for child in menu.get_children():
			if child is Button:buttons.append(child)
		buttons[index].pressed.emit();await frames(5)
		check(is_instance_valid(current_scene) and current_scene.scene_file_path=="res://"+scene+".tscn","selector loads "+scene)
		var event=InputEventKey.new();event.keycode=KEY_F2;event.physical_keycode=KEY_F2;event.pressed=true;root.push_input(event,true);await frames(5)
		check(current_scene.scene_file_path=="res://locations.tscn","F2 returns from "+scene)
		current_scene.queue_free();await frames(3)
	var after=FileAccess.get_file_as_string(campaign.path()) if FileAccess.file_exists(campaign.path()) else ""
	check(before==after,"selection preserves campaign cursor")
	var file=FileAccess.open(preload("res://tests/qa_report.gd").path("H:/game/release/environment-v044/locations-controls.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures,"scope":"actual button callback and F2 input; no human navigation claim"},"  "));file.close()
	var until=Time.get_ticks_msec()+500
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if failures.is_empty() else 1)
