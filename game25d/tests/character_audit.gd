extends SceneTree
## Isolated GPU pose fixture: actual exported characters, no gameplay changes.

var world: Node3D
var camera: Camera3D
var actors: Array = []
var output := "H:/game/release/capability-audit/poses"
var records: Array = []
var model_dir := "res://assets/characters"
var closeup := false

func _initialize() -> void:
	start.call_deferred()

func start() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--audit-output="):output=arg.trim_prefix("--audit-output=")
		if arg.begins_with("--audit-model-dir="):model_dir=arg.trim_prefix("--audit-model-dir=")
		if arg=="--audit-closeup":closeup=true
	DirAccess.make_dir_recursive_absolute(output)
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	world=Node3D.new();root.add_child(world)
	var environment=WorldEnvironment.new();world.add_child(environment)
	environment.environment=Environment.new()
	environment.environment.background_mode=Environment.BG_COLOR
	environment.environment.background_color=Color("303b40")
	environment.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color=Color("d5dbe0")
	environment.environment.ambient_light_energy=.6
	var light=DirectionalLight3D.new();world.add_child(light)
	light.rotation_degrees=Vector3(-45,-25,0);light.light_energy=1.4;light.shadow_enabled=true
	var floor_mesh=MeshInstance3D.new();world.add_child(floor_mesh)
	var plane=PlaneMesh.new();plane.size=Vector2(30,30);floor_mesh.mesh=plane
	var material=StandardMaterial3D.new();material.albedo_color=Color("656e71");material.roughness=.95;floor_mesh.material_override=material
	camera=Camera3D.new();world.add_child(camera)
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=6.8
	camera.position=Vector3(8,15,11)+Vector3(2.4,.8,0);camera.look_at(Vector3(2.4,.8,0));camera.current=true
	var definitions=[["", "worker"],["runner","wraith"],["walker","wraith"],["brute","wraith"]]
	if closeup:
		definitions=[["","worker"]]
		camera.size=2.6;camera.position=Vector3(8,15,11)+Vector3(0,.9,0);camera.look_at(Vector3(0,.9,0))
	var cases=[
		["Idle",0.6],["Walk",0.4],["Run",0.4],["SwordSlash",0.18],
		["Punch",0.25],["Death",0.2],["Death",0.8],["Death",1.0]]
	for case_index in cases.size():
		for heading in 8:
			for actor in actors:actor.free()
			actors.clear()
			for i in definitions.size():
				var actor=load("res://scripts/actor.gd").new();world.add_child(actor)
				actor.setup(definitions[i][0],load(model_dir+"/"+definitions[i][1]+".glb"))
				actor.position=Vector3(i*1.6,0,0);actor.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF
				actor.review_motion=true;actor.play("Idle",1.0,true)
				actor.face(Vector3(sin(heading*TAU/8),0,cos(heading*TAU/8)),.016,true)
				var state=cases[case_index][0];var sample=cases[case_index][1]
				actor.play(state,1.0,true)
				if state not in ["Idle","Walk","Run"]:
					# Standing actions must not inherit the previous locomotion cycle.
					actor.animation_speed=0;actor.update_motion(0)
					sample=actor.animator.get_animation(actor.clips[state]).length*sample
				# Consume action_seek's restart request before sampling the desired time.
				actor.advance_pose(0.0);actor.advance_pose(sample)
				actor.reset_physics_interpolation();actors.append(actor)
			await process_frame
			await RenderingServer.frame_post_draw
			var file="case-%02d-view-%03d.png"%[case_index,heading*45]
			var captured=root.get_texture().get_image()
			var error=captured.save_png(output.path_join(file))
			if error!=OK:push_error("Cannot save character audit image");quit(1);return
			records.append({"file":file,"state":cases[case_index][0],"sample":cases[case_index][1],"heading_degrees":heading*45,"width":captured.get_width(),"height":captured.get_height(),"fixture":true,"root_translation":false})
	var report=FileAccess.open(output.path_join("manifest.json"),FileAccess.WRITE)
	report.store_string(JSON.stringify({"engine":Engine.get_version_info().string,"renderer":RenderingServer.get_current_rendering_method(),"device":RenderingServer.get_video_adapter_name(),"cases":records,"limits":"Isolated pose fixture. Walk/run roots do not travel; this does not certify foot contact or gameplay animation."},"  "))
	report.close();print("CHARACTER_AUDIT_CAPTURED ",records.size());quit()
