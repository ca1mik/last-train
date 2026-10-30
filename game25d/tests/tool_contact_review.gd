extends SceneTree
## GPU inspection fixture, never a campaign map or gameplay-duration test.
var world: Node3D
var camera: Camera3D
var output := "H:/game/release/tool-contact-v043/contact-before"
var model_path := "res://assets/characters/motion-v38/worker.glb"
var records: Array = []

func _initialize() -> void:
	start.call_deferred()

func start() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--contact-output="):output=arg.trim_prefix("--contact-output=")
		if arg.begins_with("--contact-model="):model_path=arg.trim_prefix("--contact-model=")
	DirAccess.make_dir_recursive_absolute(output)
	world=Node3D.new();root.add_child(world)
	var env=WorldEnvironment.new();world.add_child(env);env.environment=Environment.new()
	env.environment.background_mode=Environment.BG_COLOR;env.environment.background_color=Color("798487")
	env.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color=Color("e0e4e8");env.environment.ambient_light_energy=.65
	var light=DirectionalLight3D.new();world.add_child(light)
	light.rotation_degrees=Vector3(-45,-25,0);light.light_energy=1.4
	camera=Camera3D.new();world.add_child(camera);camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.current=true
	var definitions=[["idle","Idle",.6,1.0],["walk","Walk",.4,1.0],["run","Run",.4,1.0],
		["attack-windup","SwordSlash",.08,2.4],["attack-contact","SwordSlash",.18,2.4],
		["attack-end","SwordSlash",.34,2.4],["dodge","Dodge",.26,1.0],["death","Death",.8,1.0]]
	for heading in range(0,360,45):
		for definition in definitions:
			var actor=load("res://scripts/actor.gd").new();world.add_child(actor)
			actor.setup("",load(model_path));actor.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF
			actor.review_motion=true;actor.face(Vector3(sin(deg_to_rad(heading)),0,cos(deg_to_rad(heading))),.016,true)
			actor.play(definition[1],definition[3],true)
			if definition[1] not in ["Idle","Walk","Run"]:
				actor.animation_speed=0;actor.update_motion(0)
			actor.advance_pose(0);actor.advance_pose(definition[2])
			var skeleton=preload("res://scripts/carry_ik.gd").new().find_skeleton(actor)
			var palm=skeleton.global_transform*skeleton.get_bone_global_pose(skeleton.find_bone("Palm.R")).origin
			for framing in ["body","hand"]:
				var target=Vector3(0,.9,0) if framing=="body" else palm
				camera.size=2.6 if framing=="body" else .55
				camera.position=target+Vector3(8,15,11);camera.look_at(target)
				for frame in range(2):await process_frame
				await RenderingServer.frame_post_draw
				var filename="%03d-%s-%s.png"%[heading,definition[0],framing]
				var captured=root.get_texture().get_image()
				if captured.save_png(output.path_join(filename))!=OK:quit(1);return
				records.append({"file":filename,"state":definition[1],"seconds":definition[2],"speed":definition[3],"angle":heading,"framing":framing,"width":captured.get_width(),"height":captured.get_height()})
			actor.free()
	var file=FileAccess.open(output.path_join("manifest.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"model":model_path,"model_sha256":FileAccess.get_sha256(model_path),"engine":Engine.get_version_info().string,"renderer":RenderingServer.get_current_rendering_method(),"device":RenderingServer.get_video_adapter_name(),"records":records,"fixture":true,"motion_review":false,"human_playtest":false},"  "));file.close()
	print("TOOL_CONTACT_CAPTURE ",records.size());world.queue_free();await process_frame;quit()
