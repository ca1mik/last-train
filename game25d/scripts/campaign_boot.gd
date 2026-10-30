extends Node

func _ready() -> void:
	start.call_deferred()

func start() -> void:
	var args=OS.get_cmdline_user_args()
	get_tree().root.set_meta("campaign_playing",not (args.has("--map-lab") or args.has("--forest-stop") or args.has("--freight-yard")))
	var campaign=preload("res://scripts/campaign.gd")
	var scene=campaign.current_scene() if campaign.has_launch_override() else "res://menu.tscn"
	var result=get_tree().change_scene_to_file(scene)
	if result!=OK:push_error("Campaign scene failed: "+error_string(result))
