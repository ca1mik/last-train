extends Node3D

const ACTOR=preload("res://scripts/actor.gd")
const WORKER=preload("res://assets/characters/motion-v38/worker.glb")
const WRAITH=preload("res://assets/characters/motion-v38/wraith.glb")
const BOX=preload("res://assets/props/beveled-box.glb")
var hero: RailActor
var enemies: Array[RailActor] = []
var camera: Camera3D
var obstacles: Array[Rect2] = []
var nav := AStarGrid2D.new()
var clock := 0.0
var hit_pause := 0.0
var gate: Node3D
var gate_collider: CollisionShape3D
var gate_obstacle: Rect2
var opened := false
var opening := 0.0
var work := 0.0
var mission := 0
var ui: CanvasLayer
var status: Label
var objective: Label
var help: Label
var health_bar: ProgressBar
var dash_bar: ProgressBar
var work_bar: ProgressBar
var radio: Label
var radio_time := 0.0
var splinters: Array[Node] = []
var barrels: Array[Node3D] = []
var lamps: Array[OmniLight3D] = []
var hanging: Array[Node3D] = []
var props_materials: Dictionary = {}
var paused := false
var auto_preview := false
var capture_dir := ""
var frame := 0
var captured := false
var player_down := false
var flares := 3
var flare_cooldown := 0.0
var ambient_particles: GPUParticles3D
var patient: Node3D
var camera_offset := Vector3(8,15,11)
var review := false
var review_dir := ""
var review_clock := 0.0
var last_step := 0.0
var audio_cache: Dictionary = {}
var review_shot := -1
var review_saved := -1
var world_labels: Array[Label3D] = []
var occluded: Dictionary = {}
var occluder_candidates: Array[MeshInstance3D] = []
var preferences=preload("res://scripts/player_preferences.gd").new()
var dialogue_book=preload("res://scripts/dialogue_book.gd").new()
var dialogue_queue: Array=[]
var active_dialogue:=""
var pause_overlay: Control

func _exit_tree() -> void:
	if paused and get_tree():get_tree().paused=false
	# Explicitly release live one-shot decoders before tearing down the world.
	for child in get_children():
		if child is AudioStreamPlayer3D:child.stop();child.stream=null
	audio_cache.clear()

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg=="--preview":auto_preview=true
		if arg.begins_with("--capture="):capture_dir=arg.trim_prefix("--capture=")
		if arg.begins_with("--review="):review=true;review_dir=arg.trim_prefix("--review=")
	setup_world()
	build_station()
	setup_navigation()
	hero=spawn_actor("",Vector3(-4,0,5))
	spawn_actor("runner",Vector3(-.3,0,1))
	spawn_actor("walker",Vector3(3,0,-2))
	spawn_actor("brute",Vector3(-2,0,-5.7))
	setup_camera()
	setup_ui()
	if review:setup_review()
	say("Нина · рация\nВ аптеке раненый. Подними жалюзи у дальнего щита. Я за носилками.",5)
	print("READY_25D height=1.78 door=2.15 bench=0.46 camera=orthographic")

func mat(color: Color,rough:=.8,metal:=0.0) -> StandardMaterial3D:
	var key=str(color)+str(rough)+str(metal)
	if props_materials.has(key):return props_materials[key]
	var m=StandardMaterial3D.new();m.albedo_color=color;m.roughness=rough;m.metallic=metal
	props_materials[key]=m;return m

func mesh_in(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:return node
	for child in node.get_children():
		var found=mesh_in(child)
		if found:return found
	return null

func block(pos: Vector3,size: Vector3,color: Color,solid:=false,rough:=.8,metal:=0.0,parent: Node=null) -> Node3D:
	var node=Node3D.new();(parent if parent else self).add_child(node);node.position=pos
	var shape=BOX.instantiate();node.add_child(shape);shape.scale=size
	mesh_in(shape).material_override=mat(color,rough,metal)
	if solid and pos.y+size.y*.5>1.2:node.set_meta("occluder_mesh",mesh_in(shape))
	if pos.y+size.y*.5>1.5:occluder_candidates.append(mesh_in(shape))
	if solid:
		var body=StaticBody3D.new();body.collision_layer=1;node.add_child(body)
		var collision=CollisionShape3D.new();var box=BoxShape3D.new();box.size=size;collision.shape=box;body.add_child(collision)
		if pos.y+size.y*.5>.38:obstacles.append(Rect2(Vector2(pos.x-size.x*.5,pos.z-size.z*.5),Vector2(size.x,size.z)).grow(.34))
	return node

func cylinder(pos: Vector3,radius: float,height: float,color: Color,parent: Node=null) -> MeshInstance3D:
	var node=MeshInstance3D.new();(parent if parent else self).add_child(node)
	var mesh=CylinderMesh.new();mesh.top_radius=radius;mesh.bottom_radius=radius;mesh.height=height;mesh.radial_segments=12
	node.mesh=mesh;node.position=pos;node.material_override=mat(color,.7,.25);return node

func setup_world() -> void:
	var environment=WorldEnvironment.new();add_child(environment)
	var env=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color("111c24")
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color("7e9ca8");env.ambient_light_energy=.36
	env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	var sky=Sky.new();var sky_material=ProceduralSkyMaterial.new();sky_material.sky_top_color=Color("172c40");sky_material.sky_horizon_color=Color("60717a");sky_material.ground_horizon_color=Color("4b585b");sky_material.ground_bottom_color=Color("131e22");sky.sky_material=sky_material;env.sky=sky;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	env.ssao_enabled=true;env.ssao_radius=1.2;env.ssao_intensity=1.8
	env.ssr_enabled=true;env.glow_enabled=true;env.glow_intensity=.35
	env.fog_enabled=true;env.fog_light_color=Color("172a33");env.fog_density=.003
	environment.environment=env
	var moon=DirectionalLight3D.new();add_child(moon);moon.rotation_degrees=Vector3(-58,-32,0);moon.light_color=Color("98b9c9");moon.light_energy=.43;moon.shadow_enabled=true;moon.light_angular_distance=2.5
	var probe=ReflectionProbe.new();add_child(probe);probe.position=Vector3(0,2,0);probe.size=Vector3(36,12,36);probe.intensity=.8;probe.box_projection=true

func lamp(pos: Vector3) -> void:
	cylinder(pos+Vector3(0,1.4,0),.045,2.8,Color("354649"))
	block(pos+Vector3(0,2.8,0),Vector3(.38,.12,.38),Color("26373b"))
	var bulb=block(pos+Vector3(0,2.63,0),Vector3(.18,.28,.18),Color("ffca77"))
	var glow=StandardMaterial3D.new();glow.albedo_color=Color("ffca77");glow.emission_enabled=true;glow.emission=Color("ffb763");glow.emission_energy_multiplier=2.0
	mesh_in(bulb).material_override=glow
	var light=OmniLight3D.new();add_child(light);light.position=pos+Vector3(0,2.4,0);light.light_color=Color("ffd39b");light.light_energy=4.0;light.omni_range=6.0;light.shadow_enabled=true;light.light_size=.25;light.omni_attenuation=1.5;lamps.append(light)

func bench(pos: Vector3) -> void:
	block(pos+Vector3(0,.42,0),Vector3(1.8,.06,.48),Color("263a3c"),true)
	for z in [-.18,-.06,.06,.18]:block(pos+Vector3(0,.47,z),Vector3(1.84,.06,.092),Color("795b3e"))
	for y in [.70,.87,1.04]:block(pos+Vector3(0,y,-.24),Vector3(1.84,.12,.055),Color("795b3e"))
	for x in [-.68,.68]:
		block(pos+Vector3(x,.22,0),Vector3(.055,.44,.40),Color("27383b"))
		block(pos+Vector3(x,.69,-.25),Vector3(.055,.70,.055),Color("27383b"))
		block(pos+Vector3(x,.65,.03),Vector3(.055,.055,.46),Color("27383b"))

func build_station() -> void:
	# Metres throughout. Geometry and collision share the same dimensions.
	block(Vector3(0,-.66,0),Vector3(65,.70,65),Color("141f24"),false,.95)
	block(Vector3(1,-.18,0),Vector3(22,.35,24),Color("343f40"),true,.55)
	var rng=RandomNumberGenerator.new();rng.seed=39
	for x in range(-9,11):
		for z in range(-10,12):
			var c=Color("535b58").darkened(rng.randf_range(0,.13))
			var tile=block(Vector3(x+.5,.006,z+.5),Vector3(.992,.018,.992),c,false,.68)
			var material=ShaderMaterial.new();material.shader=load("res://shaders/concrete.gdshader");material.set_shader_parameter("base_color",c);mesh_in(tile).material_override=material
	block(Vector3(0,1.4,-10),Vector3(19,2.8,.3),Color("344e4b"),true)
	block(Vector3(-9,1.1,-2),Vector3(.3,2.2,16),Color("344e4b"),true)
	block(Vector3(10.5,1.4,-6.5),Vector3(.3,2.8,7),Color("344e4b"),true)
	block(Vector3(8.5,1.1,1.5),Vector3(.3,2.2,9),Color("344e4b"),true)
	for x in range(-8,10,3):
		block(Vector3(x,1.55,-9.80),Vector3(1.4,1.3,.08),Color("243c45"),false,.2,.2)
		block(Vector3(x,2.24,-9.73),Vector3(1.6,.08,.12),Color("99917a"))
		block(Vector3(x,.80,-9.73),Vector3(1.6,.10,.18),Color("99917a"))
		block(Vector3(x,1.55,-9.70),Vector3(.06,1.4,.09),Color("99917a"))
	for x in [-6,5.8]:
		for z in [-4,1,5]:
			block(Vector3(x,1.4,z),Vector3(.32,2.8,.32),Color("264243"),true,.48,.3)
			block(Vector3(x,.14,z),Vector3(.48,.28,.48),Color("73796a"))
	for p in [Vector3(-3,0,-2),Vector3(1,0,-2),Vector3(-3,0,2.8),Vector3(2,0,2.8)]:bench(p)
	# Medical annex and a door that opens in the world.
	block(Vector3(5,1.3,-8.45),Vector3(.22,2.6,3.1),Color("3d5751"),true)
	block(Vector3(5,1.3,-4.15),Vector3(.22,2.6,2.3),Color("3d5751"),true)
	gate=Node3D.new();add_child(gate);gate.position=Vector3(5,0,-6.75)
	var panel=block(Vector3(0,1.07,.68),Vector3(.16,2.14,1.36),Color("6d4c31"),false,.66,0,gate)
	gate.set_meta("occluder_mesh",mesh_in(panel))
	var body=StaticBody3D.new();gate.add_child(body);body.collision_layer=1
	gate_collider=CollisionShape3D.new();var shape=BoxShape3D.new();shape.size=Vector3(.2,2.15,1.36);gate_collider.shape=shape;gate_collider.position=Vector3(0,1.08,.68);body.add_child(gate_collider)
	gate_obstacle=Rect2(Vector2(4.5,-6.9),Vector2(1,1.7));obstacles.append(gate_obstacle)
	block(Vector3(5,2.35,-6.05),Vector3(.5,.32,1.5),Color("2f483e"))
	label_world("АПТЕКА",Vector3(5.28,2.35,-6.05),.009).rotation.y=PI*.5
	# Relay, signs, work surfaces and props have independent depth.
	block(Vector3(-6,1.15,-8.9),Vector3(.8,1.1,.35),Color("465657"),true,.46,.3)
	block(Vector3(-6,1.20,-8.68),Vector3(.11,.11,.06),Color("c28548"))
	label_world("ЖАЛЮЗИ",Vector3(-6,1.9,-8.65),.009)
	for p in [Vector3(-6,0,-6.5),Vector3(4,0,4.5),Vector3(6.9,0,-2.1)]:
		var barrel=cylinder(p+Vector3(0,.48,0),.35,.96,Color("5c4333"));barrels.append(barrel)
		for y in [-.26,.26]:cylinder(Vector3(0,y,0),.365,.06,Color("263a3d"),barrel)
		var barrel_body=StaticBody3D.new();barrel.add_child(barrel_body);barrel_body.collision_layer=1
		var collision=CollisionShape3D.new();var drum=CylinderShape3D.new();drum.radius=.35;drum.height=.96;collision.shape=drum;barrel_body.add_child(collision)
		var rect=Rect2(Vector2(p.x-.65,p.z-.65),Vector2(1.3,1.3));obstacles.append(rect);barrel.set_meta("nav_rect",rect)
	for p in [Vector3(-7.8,0,3.5),Vector3(-7.8,0,-5.6),Vector3(6.8,0,-8.5),Vector3(6.8,0,4.5)]:lamp(p)
	# Railway platform, rail and a parked carriage, all in the same projection.
	for z in range(-12,13):
		block(Vector3(-10.2,.03,z),Vector3(2.3,.16,.19),Color("382f28"))
	for x in [-10.8,-9.55]:block(Vector3(x,.13,0),Vector3(.065,.13,26),Color("757b75"),false,.25,.7)
	block(Vector3(-11.1,1.5,2),Vector3(2.5,2.5,18),Color("29443e"),true,.48,.35)
	for z in range(-5,11,2):
		block(Vector3(-9.80,1.8,z),Vector3(.04,.84,1.25),Color("ad8b52"),false,.26,.05)
		block(Vector3(-9.78,1.8,z),Vector3(.02,.67,1.06),Color("344b4d"),false,.15,.3)
	for z in range(6,12):block(Vector3(-8.6,.025,z),Vector3(.13,.035,.6),Color("b4a26e"))
	# Stretcher: adult proportions; its patient will be replaced with the animated body.
	block(Vector3(7.8,.67,-6.4),Vector3(.72,.09,2.05),Color("647866"),true)
	for x in [-.42,.42]:
		cylinder(Vector3(7.8+x,.62,-6.4),.025,1.2,Color("8b9082")).rotation_degrees.x=90
	for x in [-.30,.30]:
		for z in [-.8,.8]:block(Vector3(7.8+x,.33,-6.4+z),Vector3(.055,.65,.055),Color("738380"))
	if ResourceLoader.exists("res://assets/characters/patient.glb"):
		patient=load("res://assets/characters/patient.glb").instantiate();add_child(patient);patient.position=Vector3(7.8,.79,-5.54);patient.scale=Vector3.ONE*(1.75/4.805);patient.rotation.x=-PI*.5
		var anim=hero_animation(patient)
		if anim:
			for clip in anim.get_animation_list():
				if clip.ends_with("Man_Idle"):anim.get_animation(clip).loop_mode=Animation.LOOP_LINEAR;anim.play(clip)
	# Hanging signs sway around their suspension point instead of static painted detail.
	var sign=Node3D.new();add_child(sign);sign.position=Vector3(-1,2.65,3.5);hanging.append(sign)
	block(Vector3(0,-.24,0),Vector3(1.7,.40,.08),Color("395449"),false,.8,0,sign)
	for x in [-.65,.65]:cylinder(Vector3(x,0,0),.013,.5,Color("929789"),sign)
	station_detail(rng)
	setup_rain()

func label_world(text: String,pos: Vector3,pixel: float) -> Label3D:
	var label=Label3D.new();add_child(label);label.text=text;label.position=pos;label.pixel_size=pixel;label.font_size=24;label.modulate=Color("e3d9b8");label.outline_size=2
	world_labels.append(label)
	return label

func setup_rain() -> void:
	var particles=GPUParticles3D.new();add_child(particles);particles.position=Vector3(-4,5,9);particles.amount=280;particles.lifetime=.7;particles.visibility_aabb=AABB(Vector3(-10,-6,-5),Vector3(20,12,10))
	var process=ParticleProcessMaterial.new();process.emission_shape=ParticleProcessMaterial.EMISSION_SHAPE_BOX;process.emission_box_extents=Vector3(6,.2,3);process.direction=Vector3(-.12,-1,0);process.spread=0;process.initial_velocity_min=9;process.initial_velocity_max=12;process.gravity=Vector3(0,-8,0)
	particles.process_material=process
	var mesh=QuadMesh.new();mesh.size=Vector2(.012,.22);var m=StandardMaterial3D.new();m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;m.albedo_color=Color(.55,.70,.75,.28);m.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;m.billboard_mode=BaseMaterial3D.BILLBOARD_ENABLED;mesh.material=m;particles.draw_pass_1=mesh

func setup_navigation() -> void:
	nav.region=Rect2i(-19,-20,41,44);nav.cell_size=Vector2(.5,.5);nav.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES;nav.update()
	refresh_nav()

func refresh_nav() -> void:
	for x in range(-19,22):
		for z in range(-20,24):
			var p=Vector2(x*.5,z*.5);var solid=p.x< -8.6 or p.x>10.1 or p.y< -9.6 or p.y>11.5
			for r in obstacles:
				if r.has_point(p):solid=true
			nav.set_point_solid(Vector2i(x,z),solid)

func route(from: Vector3,to: Vector3) -> Array[Vector3]:
	var a=Vector2i(roundi(from.x*2),roundi(from.z*2));var b=Vector2i(roundi(to.x*2),roundi(to.z*2));var result: Array[Vector3]=[]
	if not nav.is_in_boundsv(a) or not nav.is_in_boundsv(b):return result
	a=free_cell(a);b=free_cell(b)
	for p in nav.get_id_path(a,b,true):result.append(Vector3(p.x*.5,0,p.y*.5))
	if result.size()>0:result.remove_at(0)
	return result

func spawn_actor(kind: String,pos: Vector3) -> RailActor:
	var actor=ACTOR.new();add_child(actor);actor.position=pos;actor.setup(kind,WORKER if kind=="" else WRAITH);actor.home=pos
	if kind!="":enemies.append(actor)
	return actor

func setup_camera() -> void:
	camera=Camera3D.new();add_child(camera);camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=11.8;camera.near=.1;camera.far=100
	var target=hero.position+Vector3(0,.65,0);camera.position=target+camera_offset;camera.look_at(target);camera.current=true;camera.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF
	var listener=AudioListener3D.new();hero.add_child(listener);listener.position.y=1.2;listener.rotation.y=camera.rotation.y;listener.make_current()

func make_label(text: String,pos: Vector2,size: int,color: Color) -> Label:
	var l=Label.new();ui.add_child(l);l.position=pos;l.text=text;l.add_theme_font_size_override("font_size",size);l.add_theme_color_override("font_color",color);return l

func bar(pos: Vector2,size: Vector2,color: Color) -> ProgressBar:
	var b=ProgressBar.new();ui.add_child(b);b.position=pos;b.size=size;b.show_percentage=false
	var background=StyleBoxFlat.new();background.bg_color=Color("122329");background.corner_radius_top_left=3;background.corner_radius_bottom_right=3
	var fill=StyleBoxFlat.new();fill.bg_color=color;fill.corner_radius_top_left=3;fill.corner_radius_bottom_right=3
	b.add_theme_stylebox_override("background",background);b.add_theme_stylebox_override("fill",fill);b.size=size;return b

func setup_ui() -> void:
	preferences.load_all()
	ui=CanvasLayer.new();add_child(ui)
	make_label("ПОСЛЕДНИЙ РЕЙС",Vector2(42,28),23,Color("a5b8b3"))
	make_label("F2 — остановки · J — журнал",Vector2(42,1042),16,Color("a0b5a7"))
	objective=make_label("Открыть аптеку у дальнего щита",Vector2(42,64),28,Color("e6d7b1"))
	status=make_label("",Vector2(42,945),20,Color("dce3d5"))
	health_bar=bar(Vector2(42,990),Vector2(240,12),Color("b86f59"))
	dash_bar=bar(Vector2(42,1015),Vector2(100,5),Color("c5b580"))
	work_bar=bar(Vector2(780,876),Vector2(360,8),Color("c9b27c"));work_bar.visible=false
	help=make_label("",Vector2(360,810),23,Color("e7dab5"));help.size=Vector2(1200,60);help.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;help.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	make_label("WASD — движение   Ctrl — шаг   Shift — бег   ЛКМ — удар   Пробел — уклонение   E — действие",Vector2(750,1024),18,Color("9fafaa"))
	radio=make_label("",Vector2(580,892),23,Color("e3e0cd"));radio.size=Vector2(1120,126);radio.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;radio.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	pause_overlay=preload("res://scripts/pause_overlay.gd").new(self);ui.add_child(pause_overlay)

func dialogue_scope() -> String:
	return scene_file_path.get_file().get_basename() if scene_file_path.get_file() in ["forest.tscn","wasteland.tscn","main.tscn"] else "campaign"

func latest_message() -> String:return dialogue_book.latest(dialogue_scope())

func say(text: String,seconds: float,priority:=1) -> void:
	dialogue_book.add(text,dialogue_scope())
	if active_dialogue==text and radio_time>0:return
	for pending in dialogue_queue:
		if pending.text==text:return
	if priority==0:
		for i in range(dialogue_queue.size()-1,-1,-1):
			if dialogue_queue[i].priority==0:dialogue_queue.remove_at(i)
	dialogue_queue.append({"text":text,"seconds":seconds,"priority":priority})

func dialogue_threat_near() -> bool:
	for foe in enemies:
		if is_instance_valid(foe) and foe.alive and foe.position.distance_to(hero.position)<5.5 and visible_between(foe.position,hero.position):return true
	return false

func update_dialogue(delta: float) -> void:
	# Story text waits through immediate danger; preserve its remaining reading
	# time, then resume after combat. Received lines remain available in J.
	if not hero.alive or dialogue_threat_near():
		radio.visible=false;return
	radio_time=maxf(0,radio_time-delta)
	if radio_time<=0 and not dialogue_queue.is_empty():
		var pending=dialogue_queue.pop_front();active_dialogue=pending.text;radio.text=pending.text;radio_time=pending.seconds
	radio.visible=radio_time>0

func set_paused(value: bool) -> void:
	paused=value
	if pause_overlay:
		if value:pause_overlay.show_book()
		else:pause_overlay.visible=false
	get_tree().paused=value

func aim(mouse:=Vector2.INF) -> Vector3:
	# Use the click's viewport coordinates. Polling OS cursor state can be stale
	# for recorded/forwarded input and during window/camera updates.
	if not mouse.is_finite():mouse=get_viewport().get_mouse_position()
	var origin=camera.project_ray_origin(mouse);var normal=camera.project_ray_normal(mouse)
	var hit=Plane(Vector3.UP,.7).intersects_ray(origin,normal)
	if hit is Vector3:return Vector3(hit.x-hero.position.x,0,hit.z-hero.position.z).normalized()
	return hero.facing

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode==KEY_F2:get_tree().change_scene_to_file("res://locations.tscn");return
		if event.keycode==KEY_ESCAPE or event.keycode==KEY_J or event.physical_keycode==KEY_J:
			get_viewport().set_input_as_handled();set_paused(not paused);return
		if event.keycode==KEY_F11:DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if DisplayServer.window_get_mode()==DisplayServer.WINDOW_MODE_FULLSCREEN else DisplayServer.WINDOW_MODE_FULLSCREEN)
		if event.keycode==KEY_R and (player_down or mission==2):get_tree().reload_current_scene()
		if event.keycode==KEY_SPACE:try_dodge()
		if event.keycode==KEY_Q and not paused and not player_down and flares>0 and flare_cooldown<=0:
			flares-=1;flare_cooldown=1.0;sound("impactMetal_light_001",hero.position,-15);emit_noise(hero.position,10,4)
			var light=OmniLight3D.new();add_child(light);light.position=hero.position+Vector3.UP;light.light_color=Color("ff633a");light.light_energy=8;light.omni_range=7
			var tween=create_tween();tween.tween_property(light,"light_energy",0.0,2.6);tween.tween_callback(light.queue_free)
			for foe in enemies:
				if is_instance_valid(foe) and foe.alive and foe.position.distance_to(hero.position)<4.5:foe.stun=2.6;foe.phase="idle";spark(foe.position+Vector3.UP,Color("e9b976"))
	if event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_LEFT and not paused:hero.begin_attack(aim(event.position))
	if event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_RIGHT:try_dodge()

func try_dodge() -> void:
	if paused or player_down or hero.dash_cooldown>0 or hero.attack_left>.26:return
	var input=Vector2(float(Input.is_physical_key_pressed(KEY_D))-float(Input.is_physical_key_pressed(KEY_A)),float(Input.is_physical_key_pressed(KEY_S))-float(Input.is_physical_key_pressed(KEY_W)))
	var right=camera.global_basis.x;right.y=0;var forward=camera.global_basis.z;forward.y=0
	var direction=right.normalized()*input.x+forward.normalized()*input.y
	hero.attack_left=0;hero.attack_buffer=0;hero.dash_left=.26;hero.dash_cooldown=.72;hero.dash_direction=direction.normalized() if direction.length()>.1 else hero.facing
	hero.face(hero.dash_direction,.016)
	if hero.clips.has("Dodge"):hero.play("Dodge",hero.animator.get_animation(hero.clips["Dodge"]).length/.52,true)

func movement_speed() -> float:
	return 1.72 if Input.is_physical_key_pressed(KEY_CTRL) else 5.7 if Input.is_physical_key_pressed(KEY_SHIFT) else 3.8

func _physics_process(delta: float) -> void:
	frame+=1
	if paused:return
	if player_down:
		# Death must reach its final pose while the retry UI is visible.
		hero.clocks(delta);hero.advance_pose(delta);return
	clock+=delta
	if review:review_tick(delta);return
	hit_pause=maxf(0,hit_pause-delta)
	hero.clocks(delta)
	flare_cooldown=maxf(0,flare_cooldown-delta)
	var input=Vector2(float(Input.is_physical_key_pressed(KEY_D))-float(Input.is_physical_key_pressed(KEY_A)),float(Input.is_physical_key_pressed(KEY_S))-float(Input.is_physical_key_pressed(KEY_W)))
	if auto_preview:input=Vector2(sin(clock*.5),cos(clock*.5))*.7
	var right=camera.global_basis.x;right.y=0;right=right.normalized();var forward=camera.global_basis.z;forward.y=0;forward=forward.normalized()
	var direction=(right*input.x+forward*input.y).normalized();var speed=movement_speed()
	if hero.attack_left>0:speed*=.42
	var dashing=hero.dash_left>0
	if dashing:
		direction=hero.dash_direction
		# A bounded travel curve avoids a velocity step and an unaccounted glide
		# after the dodge. Integral is approximately two metres over 0.26 seconds.
		speed=12.25*sin(PI*clampf(1.0-hero.dash_left/.26,0,1))
		hero.dash_left=maxf(0,hero.dash_left-delta)
	hero.move_ground(direction,speed,delta,dashing)
	last_step+=delta
	if hero.ground_speed>.4 and hero.dash_left<=0 and last_step>(.28 if hero.ground_speed>4 else .39):
		sound(footstep_prefix()+str(randi_range(0,4)),hero.position,-23)
		emit_noise(hero.position,2.3 if hero.ground_speed<2 else 8.5 if hero.ground_speed>4.5 else 5.0,2.5);last_step=0
	if hero.attack_left>0 and hero.attack_left<.26 and not hero.attack_hit:
		hero.attack_hit=true;strike()
	for foe in enemies:
		if not is_instance_valid(foe):continue
		foe.clocks(delta)
		if not foe.alive:continue
		enemy_tick(foe,delta)
	hero.advance_pose(delta)
	for foe in enemies:
		if is_instance_valid(foe):foe.advance_pose(delta)
	check_occlusion()
	interactions(delta)
	for i in lamps.size():lamps[i].light_energy=4.0+sin(clock*2.2+i*1.7)*.045
	for sign in hanging:sign.rotation.z=sin(clock*.9)*.018
	for label in world_labels:label.visible=hero.position.distance_to(label.position)<5.0
	health_bar.value=hero.health;dash_bar.value=(1-hero.dash_cooldown/.72)*100
	status.text="АРТЁМ  ·  "+str(int(hero.health))+" / 100     Q · РАКЕТЫ "+str(flares)
	update_dialogue(delta)
	if not hero.alive:player_down=true;help.text="Рейс прерван. R — контрольная точка."
	if capture_dir!="" and frame>=100 and not captured:
		captured=true;capture.call_deferred()

func visible_between(a: Vector3,b: Vector3) -> bool:
	var query=PhysicsRayQueryParameters3D.create(a+Vector3.UP*.85,b+Vector3.UP*.85,1)
	return get_world_3d().direct_space_state.intersect_ray(query).is_empty()

func footstep_prefix() -> String:return "footstep_concrete_00"

func emit_noise(position: Vector3,radius: float,duration:=5.0) -> void:
	for foe in enemies:
		if is_instance_valid(foe) and foe.alive and foe.position.distance_to(position)<radius:
			foe.investigate_position=position;foe.investigate_left=duration;foe.repath=0

func enemy_tick(foe: RailActor,delta: float) -> void:
	if foe.stun>0:foe.move_ground(Vector3.ZERO,0,delta);return
	var difference=hero.position-foe.position;difference.y=0;var distance=difference.length()
	if distance<7.5 and visible_between(foe.position,hero.position):foe.awareness_left=3;foe.last_known_position=hero.position
	if foe.phase=="charge":
		foe.phase_left-=delta;foe.move_ground(foe.target_direction,12,delta)
		if not foe.charge_hit and distance<.75:
			foe.charge_hit=true
			if hero.take_hit(24,foe.target_direction):hurt()
		if foe.phase_left<=0 or foe.ground_speed<1:foe.phase="recover";foe.phase_left=1.0
		return
	if foe.phase in ["windup","strike","recover"]:
		foe.phase_left-=delta;foe.move_ground(Vector3.ZERO,0,delta)
		if foe.phase_left<=0:
			if foe.phase=="windup":
				if foe.enemy_kind=="runner":foe.phase="charge";foe.phase_left=.29;foe.charge_hit=false
				else:
					foe.play("SwordSlash" if foe.enemy_kind=="brute" else "Punch",1.8,true);foe.phase="strike";foe.phase_left=.24 if foe.enemy_kind=="brute" else .18
			elif foe.phase=="strike":
				var radius=1.9 if foe.enemy_kind=="brute" else 1.05
				if distance<radius and difference.normalized().dot(foe.target_direction)>.25 and visible_between(foe.position,hero.position):
					if hero.take_hit(32 if foe.enemy_kind=="brute" else 24,foe.target_direction):hurt()
				foe.phase="recover";foe.phase_left=.91 if foe.enemy_kind=="brute" else .67
			else:foe.phase="idle"
		return
	var reach=2.6 if foe.enemy_kind=="runner" else 1.55 if foe.enemy_kind=="brute" else .95
	if distance<reach and visible_between(foe.position,hero.position):
		foe.phase="windup";foe.phase_left=.8 if foe.enemy_kind=="brute" else .5 if foe.enemy_kind=="runner" else .42
		foe.target_direction=difference.normalized();foe.face(foe.target_direction,delta)
		foe.play("Punch",.35,true);spark(foe.position+Vector3.UP*1.5,Color("bb8c59"),.12)
		return
	foe.repath-=delta
	if foe.repath<=0:
		var target=foe.last_known_position if foe.awareness_left>0 else foe.investigate_position if foe.investigate_left>0 else foe.home
		foe.path=route(foe.position,target);foe.repath=.4
	while not foe.path.is_empty() and foe.position.distance_to(foe.path[0])<.35:foe.path.remove_at(0)
	var move=(foe.path[0]-foe.position).normalized() if not foe.path.is_empty() else Vector3.ZERO
	move.y=0
	foe.move_ground(move,2.9 if foe.enemy_kind=="runner" else 1.65 if foe.enemy_kind=="brute" else 2.2,delta)

func strike() -> void:
	slash_arc(hero.position,hero.facing)
	var hit=false
	for foe in enemies:
		if not is_instance_valid(foe) or not foe.alive:continue
		var d=foe.position-hero.position;d.y=0
		if d.length()<1.55 and (d.length()<.1 or d.normalized().dot(hero.facing)>.3) and visible_between(hero.position,foe.position):
			if foe.take_hit(55,d.normalized()):spark(foe.position+Vector3.UP,Color("e3bf7e"));hit=true
	for barrel in barrels:
		if is_instance_valid(barrel):
			var d=barrel.position-hero.position;d.y=0
			if d.length()<1.55 and d.normalized().dot(hero.facing)>.3 and visible_between(hero.position,barrel.position-hero.facing*.4):break_barrel(barrel);hit=true
	if hit:hit_pause=.035;sound("impactMetal_medium_001",hero.position,-16)
	else:sound("impactMetal_light_000",hero.position,-26)

func slash_arc(pos: Vector3,direction: Vector3) -> void:
	var surface=SurfaceTool.new();surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var angle=atan2(direction.x,direction.z)
	for i in range(12):
		var a=angle-.9+i*1.5/12;var b=angle-.9+(i+1)*1.5/12
		var width=.018+.035*sin(i*PI/12)
		var points=[Vector3(sin(a)*.86,1.0,cos(a)*.86),Vector3(sin(a)*(.86+width),1.01,cos(a)*(.86+width)),Vector3(sin(b)*(.86+width),1.01,cos(b)*(.86+width)),Vector3(sin(b)*.86,1.0,cos(b)*.86)]
		for index in [0,1,2,0,2,3]:surface.add_vertex(points[index])
	var arc=MeshInstance3D.new();add_child(arc);arc.position=pos;arc.mesh=surface.commit();arc.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material=StandardMaterial3D.new();material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;material.cull_mode=BaseMaterial3D.CULL_DISABLED;material.albedo_color=Color("d8bd83");material.emission_enabled=true;material.emission=Color("c2a774");material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;arc.material_override=material
	var tween=create_tween();tween.tween_property(material,"albedo_color:a",0.0,.11);tween.tween_callback(arc.queue_free)

func hurt() -> void:
	work=0;hit_pause=.045;spark(hero.position+Vector3.UP,Color("b66a53"));sound("impactMetal_heavy_002",hero.position,-18)

func spark(pos: Vector3,color: Color,lifetime:=.22) -> void:
	for i in range(5):
		var p=MeshInstance3D.new();add_child(p);var m=SphereMesh.new();m.radius=.025;m.height=.05;p.mesh=m;p.material_override=mat(color,.3);p.position=pos
		var tween=create_tween();tween.tween_property(p,"position",pos+Vector3(randf_range(-.35,.35),randf_range(-.15,.4),randf_range(-.35,.35)),lifetime);tween.tween_callback(p.queue_free)

func break_barrel(barrel: Node3D) -> void:
	var pos=barrel.position;barrel.queue_free()
	if barrel.has_meta("nav_rect"):obstacles.erase(barrel.get_meta("nav_rect"));refresh_nav()
	for i in range(7):
		var piece=RigidBody3D.new();add_child(piece);piece.position=pos;piece.mass=.15
		var mesh=MeshInstance3D.new();piece.add_child(mesh);var box=BoxMesh.new();box.size=Vector3(.07,.25,.12);mesh.mesh=box;mesh.material_override=mat(Color("796044"))
		var collision=CollisionShape3D.new();var shape=BoxShape3D.new();shape.size=box.size;collision.shape=shape;piece.add_child(collision)
		piece.apply_central_impulse(Vector3(randf_range(-.7,.7),randf_range(.5,1.1),randf_range(-.7,.7)));piece.angular_velocity=Vector3(randf()*6,randf()*6,randf()*6)
		get_tree().create_timer(4).timeout.connect(piece.queue_free)

func interactions(delta: float) -> void:
	help.text="";work_bar.visible=false
	if opened and opening<1:
		opening=minf(1,opening+delta*1.5);gate.rotation.y=-opening*PI*.52
		if opening==1:gate_collider.disabled=true
	if mission>=2:help.text="R — повторить вылазку";return
	var target=Vector3(-6,0,-8.0) if mission==0 else Vector3(7.8,0,-6.4)
	if hero.position.distance_to(target)<1.5:
		help.text="Удерживать E — поднять жалюзи" if mission==0 else "E — Михаил, мы за вами"
		if Input.is_physical_key_pressed(KEY_E) and hero.ground_speed<.15 and hero.attack_left<=0 and hero.dash_left<=0 and mission<2:
			work+=delta;work_bar.visible=true;work_bar.value=work/1.1*100
			if work>=1.1:
				work=0
				if mission==0:
					mission=1;opened=true;obstacles.erase(gate_obstacle);refresh_nav();sound("impactMetal_medium_003",Vector3(5,1,-6),-15);objective.text="Забрать раненого из аптеки";say("Нина · рация\nПроход открыт. Я несу носилки.",3)
				else:mission=2;objective.text="Михаил найден • участок завершён";say("Михаил\nЯ слышал поезд. Думал, снова проедет мимо.",4)
		else:work=0
	else:work=0

func capture() -> void:
	await RenderingServer.frame_post_draw
	var image=get_viewport().get_texture().get_image();DirAccess.make_dir_recursive_absolute(capture_dir);image.save_png(capture_dir.path_join("scene-25d.png"))
	print("CAPTURED_25D ",capture_dir)
	if auto_preview:finish_preview.call_deferred()

func finish_preview() -> void:
	# --fixed-fps can finish a capture faster than audio's wall-clock decoder.
	# Stop new sounds and drain live players before asking the engine to exit.
	set_physics_process(false);set_process(false)
	for child in get_children():
		if child is AudioStreamPlayer3D:child.stop();child.stream=null;child.queue_free()
	audio_cache.clear()
	var until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<until:await get_tree().process_frame
	get_tree().quit()

func hero_animation(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:return node
	for child in node.get_children():
		var found=hero_animation(child)
		if found:return found
	return null

func free_cell(cell: Vector2i) -> Vector2i:
	if not nav.is_point_solid(cell):return cell
	for radius in range(1,5):
		for dx in range(-radius,radius+1):
			for dz in range(-radius,radius+1):
				var p=cell+Vector2i(dx,dz)
				if nav.is_in_boundsv(p) and not nav.is_point_solid(p):return p
	return cell

func sound(clip: String,pos: Vector3,volume: float,bus:="SFX") -> void:
	var path="res://assets/audio/"+clip+".ogg"
	if not ResourceLoader.exists(path):return
	if not audio_cache.has(clip):audio_cache[clip]=load(path)
	var player=AudioStreamPlayer3D.new();add_child(player);player.bus=bus;player.stream=audio_cache[clip];player.position=pos;player.volume_db=volume;player.max_distance=18;player.unit_size=5;player.pitch_scale=randf_range(.95,1.05);player.finished.connect(player.queue_free);player.play()

func tube(a: Vector3,b: Vector3,radius: float,color: Color) -> Node3D:
	var piece=cylinder((a+b)*.5,radius,a.distance_to(b),color)
	piece.quaternion=Quaternion(Vector3.UP,(b-a).normalized())
	return piece

func puddle(pos: Vector3,size: Vector2,rng: RandomNumberGenerator) -> void:
	var surface=SurfaceTool.new();surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var ring: Array[Vector3]=[]
	for i in range(24):
		var angle=i*TAU/24.0;var r=rng.randf_range(.83,1.0)
		ring.append(Vector3(cos(angle)*size.x*r,0,sin(angle)*size.y*r))
	for i in range(24):
		for v in [Vector3.ZERO,ring[(i+1)%24],ring[i]]:surface.set_normal(Vector3.UP);surface.add_vertex(v)
	var mesh=MeshInstance3D.new();add_child(mesh);mesh.mesh=surface.commit();mesh.position=pos
	var material=ShaderMaterial.new();material.shader=load("res://shaders/water.gdshader");mesh.material_override=material

func crate(pos: Vector3,size: Vector3) -> void:
	block(pos+Vector3.UP*size.y*.5,size,Color("5a4936"),true)
	for x in [-.34,.34]:block(pos+Vector3(x*size.x,size.y*.5,size.z*.51),Vector3(.065,size.y,.035),Color("282e2b"),false,.4,.5)
	for i in range(4):block(pos+Vector3((i/3.0-.5)*size.x*.9,size.y+.015,0),Vector3(size.x*.215,.035,size.z*.92),Color("756044"))

func station_detail(rng: RandomNumberGenerator) -> void:
	# The foreground is a grounded railway verge, with a physical perimeter.
	for x in [-8.65,10.8]:
		for z in range(-9,13,2):
			if x<0 and z>5:continue
			block(Vector3(x,.49,z),Vector3(.07,.98,.07),Color("33403c"))
			block(Vector3(x,.78,z+.8),Vector3(.04,.045,1.95),Color("51594a"))
			block(Vector3(x,.40,z+.8),Vector3(.04,.045,1.95),Color("51594a"))
	block(Vector3(1,.24,12),Vector3(21,.48,.30),Color("404944"),true)
	block(Vector3(11,.24,2),Vector3(.32,.48,20),Color("404944"),true)
	# Stone coping, stained plaster, timber and steel have distinct scale and finish.
	block(Vector3(0,2.82,-10),Vector3(19.3,.16,.55),Color("726d59"))
	block(Vector3(0,1.88,-9.81),Vector3(18.9,1.75,.035),Color("847b63"))
	block(Vector3(0,.98,-9.73),Vector3(18.9,.12,.12),Color("263b37"))
	for x in range(-9,10,3):
		block(Vector3(x,1.45,-9.65),Vector3(.22,2.7,.25),Color("4d5850"))
		block(Vector3(x,2.77,-9.62),Vector3(.42,.13,.30),Color("94866a"))
	for x in [-6,5.8]:
		block(Vector3(x,2.85,.5),Vector3(.16,.23,11.5),Color("243a37"))
		for z in [-4,1,5]:
			for dx in [-.45,.45]:tube(Vector3(x,2.45,z),Vector3(x+dx,2.85,z),.035,Color("466359"))
	# Tickets, clock and cable runs give the station a purpose beyond an arena.
	block(Vector3(-7.65,.84,-8.6),Vector3(.85,1.68,.6),Color("29483f"),true,.5,.25)
	block(Vector3(-7.65,1.25,-8.28),Vector3(.59,.48,.035),Color("bcaf7b"))
	block(Vector3(-7.65,.82,-8.25),Vector3(.3,.06,.08),Color("182d2b"))
	for x in [-7.82,-7.5]:cylinder(Vector3(x,.98,-8.24),.035,.028,Color("9a8460")).rotation.x=PI*.5
	var clock_face=cylinder(Vector3(-1.0,2.08,-9.57),.38,.07,Color("c4b98e"));clock_face.rotation.x=PI*.5
	for i in range(12):
		var a=i*TAU/12.0
		var tick=block(Vector3(-1+sin(a)*.30,2.08+cos(a)*.30,-9.51),Vector3(.022,.05,.012),Color("354039"));tick.rotation.z=-a
	var hand=block(Vector3(-1.08,2.17,-9.49),Vector3(.025,.24,.018),Color("253b37"));hand.rotation.z=.7
	block(Vector3(-.91,2.08,-9.48),Vector3(.22,.02,.02),Color("253b37"))
	label_world("НОВОРЕЧЬЕ",Vector3(-3.5,2.35,-9.55),.009)
	for z in range(-9,11,2):tube(Vector3(-8.80,.35,z),Vector3(-8.80,.35,z+2),.035,Color("3b433b"))
	crate(Vector3(-7.7,0,-1.6),Vector3(.80,.70,.65));crate(Vector3(-7.7,0,-.7),Vector3(.7,.95,.7));crate(Vector3(7.2,0,6.6),Vector3(1.15,.65,.65))
	# Grates and patches break the metre grid without creating invisible obstacles.
	for z in [-6.2,6.8]:
		block(Vector3(0,.026,z),Vector3(5,.018,.30),Color("1c2c2d"))
		for x in range(-24,25):block(Vector3(x*.1,.044,z),Vector3(.025,.02,.29),Color("5b6457"),false,.4,.45)
	for i in range(95):
		var x=rng.randf_range(-8.2,10);var z=rng.randf_range(-9,11.5)
		if i<22:
			var paper=block(Vector3(x,.035,z),Vector3(rng.randf_range(.09,.22),.006,rng.randf_range(.14,.29)),Color("857d61"));paper.rotation.y=rng.randf()*TAU
		else:
			var edge_x=rng.randf_range(-8.1,-7.8) if i%2==0 else rng.randf_range(9.5,10.0)
			for j in range(3):
				var grass=block(Vector3(edge_x+rng.randf_range(-.1,.1),.10,z),Vector3(.024,rng.randf_range(.13,.32),.024),Color("626d3f"));grass.rotation.z=rng.randf_range(-.45,.45)
	for p in [Vector3(-4,.03,7),Vector3(.7,.03,4.4),Vector3(-6.3,.03,1.1),Vector3(3,.03,-5.3),Vector3(5,.03,7.8)]:puddle(p,Vector2(rng.randf_range(.7,1.4),rng.randf_range(.35,.65)),rng)
	# Spill from the carriage windows ties the safe destination to the same lighting.
	for z in [-3,3,9]:
		var light=OmniLight3D.new();add_child(light);light.position=Vector3(-9.5,1.7,z);light.light_color=Color("edb26f");light.light_energy=1.5;light.omni_range=3.5
	var sign=block(Vector3(-8.35,1.22,7.7),Vector3(.055,.5,1.1),Color("6e4332"))
	label_world("К ПОЕЗДУ",sign.position+Vector3(.04,0,0),.008).rotation.y=PI*.5

func setup_review() -> void:
	for label in world_labels:label.visible=false
	for foe in enemies:foe.set_physics_process(false);foe.collision_layer=0;foe.collision_mask=0
	for actor in [hero]+enemies:actor.review_motion=true
	hero.position=Vector3(-2,0,6.5)
	for i in enemies.size():enemies[i].position=hero.position+Vector3((i+1)*1.9,0,0)
	for actor in [hero]+enemies:actor.reset_physics_interpolation()
	camera.size=8.4;var center=hero.position+Vector3(2.2,.7,0);camera.position=center+camera_offset;camera.look_at(center)
	objective.text="ПРОВЕРКА АНИМАЦИЙ · 8 НАПРАВЛЕНИЙ";radio.visible=false;help.text=""
	DirAccess.make_dir_recursive_absolute(review_dir)

func review_tick(delta: float) -> void:
	review_clock+=delta
	var shot=int(review_clock/1.25)
	var states=["Idle","Walk","Run","SwordSlash","Punch","Death"]
	if shot>=states.size()*8:get_tree().quit();return
	var state=states[shot/8];var heading=(shot%8)*TAU/8
	if shot!=review_shot:
		review_shot=shot
		for actor in [hero]+enemies:
			actor.play(state,1.0,true);actor.face(Vector3(sin(heading),0,cos(heading)),.016,true)
		status.text=state+" · "+str((shot%8)*45)+"°";objective.text="АРТЁМ / БЕГУН / ПУТЕВОЙ / СЦЕПЩИК"
	for actor in [hero]+enemies:actor.advance_pose(delta)
	if fmod(review_clock,1.25)>.65 and review_saved!=shot and not captured:
		captured=true;review_saved=shot;review_capture.call_deferred()

func review_capture() -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(review_dir.path_join("pose-%02d.png"%review_saved))
	captured=false

func _process(delta: float) -> void:
	if not is_instance_valid(hero) or not camera or review or paused:return
	follow_camera(delta)

func follow_camera(delta: float) -> void:
	var p=hero.get_global_transform_interpolated().origin
	var target=Vector3(clampf(p.x,-4.2,5.1),.65,clampf(p.z,-6.8,3.6))
	# A fixed orthographic orientation. Only the camera position follows the interpolated body.
	camera.position=camera.position.lerp(target+camera_offset,1-exp(-7*minf(delta,.1)))
	update_occlusion(delta)

func check_occlusion() -> void:
	for key in occluded.keys():occluded[key][1]=false
	for height in [.35,1.4]:
		var target=hero.global_position+Vector3.UP*height
		var origin=camera.project_ray_origin(camera.unproject_position(target))
		# Test render geometry, including lintels/signs which correctly have no physical collider.
		for mesh in occluder_candidates:
			if not is_instance_valid(mesh):continue
			var inverse=mesh.global_transform.affine_inverse()
			if mesh.get_aabb().intersects_segment(inverse*origin,inverse*target)!=null:occluded[mesh.get_instance_id()]=[mesh,true]

func update_occlusion(delta: float) -> void:
	for key in occluded.keys():
		var item=occluded[key];var mesh=item[0]
		if not is_instance_valid(mesh):occluded.erase(key);continue
		mesh.transparency=move_toward(mesh.transparency,.85 if item[1] else 0.0,delta*6)
		if not item[1] and mesh.transparency<=.001:occluded.erase(key)
