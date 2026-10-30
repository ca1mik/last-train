extends SceneTree

func _initialize() -> void:
	start.call_deferred()

func start() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps=0
	var game=load("res://main.tscn").instantiate();root.add_child(game)
