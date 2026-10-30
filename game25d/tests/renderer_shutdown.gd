extends SceneTree
## Minimal native renderer diagnosis; not exported or a visual quality test.
class WorldProbe extends "res://scripts/main.gd":
	func _ready() -> void:
		set_physics_process(false);set_process(false);setup_world()
		var view=Camera3D.new();add_child(view);view.position=Vector3(4,5,6);view.look_at(Vector3.ZERO)
		block(Vector3.ZERO,Vector3.ONE,Color.GRAY)
var probe: Node3D
func _initialize() -> void:start.call_deferred()
func start() -> void:
	var mode="empty"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--probe-mode="):mode=arg.trim_prefix("--probe-mode=")
	probe=Node3D.new() if mode=="empty" else WorldProbe.new();root.add_child(probe)
	for node in probe.get_children():
		if mode=="no-probe" and node is ReflectionProbe:node.queue_free()
		if node is WorldEnvironment:
			if mode=="no-ssr":node.environment.ssr_enabled=false
			if mode=="no-ssao":node.environment.ssao_enabled=false
			if mode=="no-sky":node.environment.sky=null;node.environment.reflected_light_source=Environment.REFLECTION_SOURCE_DISABLED
	for i in range(30):await process_frame
	probe.queue_free()
	for i in range(12):await process_frame
	print("RENDERER_SHUTDOWN mode=",mode);quit()
