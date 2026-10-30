extends "res://scripts/main.gd"
## Standalone route trials. No campaign/checkpoint mutation.
@export var landscape := "forest"
var kit: RefCounted
var bounds:=Rect2(-28,-26,56,50)
var start_point:=Vector3(-22,0,17)
var goals: Array[Vector3]=[]
var captions: Array[String]=[]
var task_names: Array[String]=[]
var input_latched:=false
var trial_gate: Node3D
var trial_gate_shape: CollisionShape3D
var trial_gate_rect: Rect2
var trial_open:=false
var signal_light: OmniLight3D
var landmark: Label
var actions: Array=[]

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg=="--preview":auto_preview=true
		if arg.begins_with("--capture="):capture_dir=arg.trim_prefix("--capture=")
	kit=preload("res://scripts/environment_kit.gd").new(self,4411 if landscape=="forest" else 4422)
	goals.assign([Vector3(-17,0,-17),Vector3(19,0,-16),start_point] if landscape=="forest" else [Vector3(-16,0,-14),Vector3(19,0,-13),start_point])
	if landscape=="forest":
		captions.assign(["Взять сигнальную рукоять у путевой будки","Вернуть выходной сигнал на посту","Вернуться к составу через открытый проход"])
		task_names.assign(["Взять рукоять","Проверить и перевести сигнал","Завершить вылазку у состава"])
	else:
		captions.assign(["Забрать перемычку в грузовом дворе","Подать питание на проходные ворота","Вернуться к составу по открытому пути"])
		task_names.assign(["Взять перемычку","Восстановить привод ворот","Завершить вылазку у состава"])
	setup_world();build_station();setup_navigation()
	hero=spawn_actor("",start_point)
	var positions=[Vector3(-10,0,10),Vector3(8,0,-6),Vector3(16,0,-10),Vector3(-13,0,-10)] if landscape=="forest" else [Vector3(-10,0,12),Vector3(1,0,-4),Vector3(16,0,-10),Vector3(-17,0,-8),Vector3(19,0,6)]
	for i in positions.size():spawn_actor(["walker","runner","brute","walker","runner"][i],positions[i])
	setup_camera();setup_ui();update_task()
	say("Путевой пост за лесом. Найди рукоять у будки и верни сигнал. Обратно можно открыть короткий проход." if landscape=="forest" else "В грузовом дворе осталась целая перемычка. Она вернёт питание воротам и откроет короткий путь к составу.",7)
	print("ENVIRONMENT_READY ",landscape," obstacles=",obstacles.size())

func setup_world() -> void:
	super.setup_world()
	for node in get_children():
		if node is WorldEnvironment:
			node.environment.ambient_light_energy=.66;node.environment.fog_density=.003 if landscape=="forest" else .0015
		if node is DirectionalLight3D:node.light_energy=.8

func build_station() -> void:
	block(Vector3(0,-.5,0),Vector3(92,.6,90),Color("2c3930") if landscape=="forest" else Color("494c3d"))
	var floor_node=block(Vector3(0,-.14,-1),Vector3(56,.28,50),Color("495945") if landscape=="forest" else Color("686750"),true,.98)
	var shader=ShaderMaterial.new();shader.shader=load("res://shaders/expedition_floor.gdshader");shader.set_shader_parameter("base_color",Color("46523c") if landscape=="forest" else Color("6a6851"));shader.set_shader_parameter("tile_size",0.0);mesh_in(floor_node).material_override=shader
	# Low real perimeter prevents falling; distant landscape continues behind it.
	for x in [-28.2,28.2]:block(Vector3(x,.3,-1),Vector3(.3,.6,50),Color("3e4c3a"),true)
	for z in [-26.2,24.2]:block(Vector3(0,.3,z),Vector3(56,.6,.3),Color("3e4c3a"),true)
	block(Vector3(-27.1,1.45,17),Vector3(2.2,2.6,11),Color("29483d"),true,.55,.3)
	for z in [13,16,19,22]:block(Vector3(-25.95,1.8,z),Vector3(.04,.8,1.5),Color("b6a16d"))
	label_world("СОСТАВ",start_point+Vector3(0,2.2,1),.008)
	if landscape=="forest":build_forest()
	else:build_wasteland()
	build_trial_gate()
	for p in [start_point,goals[0],goals[1]]:lamp(p+Vector3(-2,0,-1))
	for i in range(2):
		block(goals[i]+Vector3(0,.6,-.9),Vector3(1.2,1.2,.7),Color("7c795d"),true)
		label_world("РУКОЯТЬ" if i==0 and landscape=="forest" else "ПЕРЕМЫЧКА" if i==0 else "ВЫХОДНОЙ ПОСТ" if landscape=="forest" else "ПИТАНИЕ ВОРОТ",goals[i]+Vector3(0,1.9,-.9),.007)
	signal_light=OmniLight3D.new();add_child(signal_light);signal_light.position=goals[1]+Vector3(0,3,-.9);signal_light.light_color=Color("c97c4b");signal_light.light_energy=1.8;signal_light.omni_range=5
	kit.finish_grass()

func build_forest() -> void:
	kit.path_strip(start_point,Vector3(-15,0,3),3.1,Color("79785d"))
	kit.path_strip(Vector3(-15,0,3),goals[0],2.7,Color("79785d"))
	kit.path_strip(goals[0],Vector3(1,0,-19),2.6,Color("79785d"))
	kit.path_strip(Vector3(1,0,-19),goals[1],2.6,Color("79785d"))
	kit.path_strip(goals[1],Vector3(15,0,8),2.5,Color("79785d"))
	kit.path_strip(Vector3(15,0,8),start_point,2.5,Color("79785d"))
	kit.hut(Vector3(-18,0,-22),Color("788373"))
	for x in [-25,-22,-19,-16,-13,-10,-7,-4,-1,2,5,8,11,14,17,20,23,26]:
		kit.tree(Vector3(x+rng_offset(x),0,-28),x%3==0,5.4+fposmod(x,3)*.35)
	for p in [Vector3(-25,0,-10),Vector3(-24,0,1),Vector3(-23,0,9),Vector3(-19,0,-5),Vector3(-7,0,-20),Vector3(-5,0,-13),Vector3(-6,0,-5),Vector3(-2,0,0),Vector3(3,0,2),Vector3(8,0,16),Vector3(14,0,17),Vector3(25,0,17),Vector3(25,0,8),Vector3(26,0,-2),Vector3(25,0,-19),Vector3(9,0,-23),Vector3(2,0,-7)]:kit.tree(p,int(absf(p.x+p.z))%2==0,4.8+fposmod(p.x,2))
	for p in [Vector3(-12,0,-4),Vector3(4,0,-13),Vector3(9,0,7),Vector3(-19,0,9),Vector3(23,0,-7)]:
		kit.bush(p,.75);kit.stone(p+Vector3(.8,0,1.5),Vector3(1.5,.8,1.3),Color("777c64"),true)
	for z in range(-24,25,3):
		block(Vector3(5,.07,z),Vector3(3.2,.13,.22),Color("514a35"))
	for x in [4.3,5.7]:block(Vector3(x,.16,0),Vector3(.08,.15,50),Color("8a907a"),false,.3,.65)
	for p in [Vector2(-24,-6),Vector2(-3,-10),Vector2(24,7),Vector2(10,19),Vector2(-8,19)]:kit.grass_patch(p,Vector2(6,7),100)
	for z in [-22,-13,-4,5,14,23]:
		for x in [-31,31]:kit.stone(Vector3(x,0,z),Vector3(7,2.3,10),Color("46533b"))
	label_world("ПУТЕВОЙ ПОСТ →",Vector3(-14,2,-17),.008)

func rng_offset(value: int) -> float:return sin(value*2.3)*.6

func inside_floor(point: Vector2) -> bool:return bounds.has_point(point)

func footstep_prefix() -> String:return "footstep_grass_00" if landscape=="forest" else "footstep_concrete_00"

func build_wasteland() -> void:
	kit.path_strip(start_point,Vector3(-14,0,2),3.5,Color("7a7963"));kit.path_strip(Vector3(-14,0,2),goals[0],3.5,Color("7a7963"))
	kit.path_strip(goals[0],goals[1],3.2,Color("7a7963"));kit.path_strip(goals[1],Vector3(17,0,12),3.0,Color("7a7963"));kit.path_strip(Vector3(17,0,12),start_point,3.0,Color("7a7963"))
	for p in [Vector3(-5,0,7),Vector3(12,0,-5),Vector3(-13,0,-21)]:kit.tank(p)
	for p in [Vector3(-12,0,0),Vector3(5,0,14),Vector3(22,0,16),Vector3(3,0,-20),Vector3(24,0,-20)]:
		block(p+Vector3.UP*.7,Vector3(3,1.4,2.3),Color("7e7b65"),true)
		for i in range(3):block(p+Vector3(-1+i,.72,1.17),Vector3(.08,1.2,.045),Color("4e6052"))
	for p in [Vector3(-23,0,-6),Vector3(-5,0,-14),Vector3(8,0,6),Vector3(24,0,4)]:
		kit.stone(p,Vector3(3.8,1.0,2.2),Color("777963"),true);kit.grass_patch(Vector2(p.x,p.z),Vector2(7,6),80)
	# Large crane silhouette beyond the walkable north edge.
	for x in [9,16]:
		block(Vector3(x,5.3,-29),Vector3(.8,10.6,.8),Color("566454"))
		for y in [2,4,6,8]:tube(Vector3(9,y,-29),Vector3(16,y+2,-29),.075,Color("7d8165"))
	block(Vector3(12.5,10.8,-29),Vector3(16,.65,1),Color("747b5f"))
	tube(Vector3(5,10.5,-29),Vector3(5,4.2,-29),.045,Color("424f44"))
	kit.hut(Vector3(19,0,-21),Color("8b846d"))
	kit.fence(Vector3(-25,0,-24),Vector3(-4,0,-24));kit.fence(Vector3(25,0,-23),Vector3(25,0,-8))
	for p in [Vector3(-23,0,7),Vector3(-1,0,20),Vector3(22,0,19)]:kit.bush(p,.6)
	var random=RandomNumberGenerator.new();random.seed=4422
	for i in range(65):
		var p=Vector3(random.randf_range(-24,24),0,random.randf_range(-24,21));kit.stone(p,Vector3(.15,.08,.13),Color("93917b"))
	label_world("ГРУЗОВОЙ ДВОР",Vector3(-16,2,-17),.008)

func build_trial_gate() -> void:
	kit.fence(Vector3(-10,0,4),Vector3(-2.2,0,4));kit.fence(Vector3(2.2,0,4),Vector3(11,0,4))
	trial_gate=block(Vector3(0,1.0,4),Vector3(4.2,2,.18),Color("66765a"))
	var body=StaticBody3D.new();trial_gate.add_child(body);trial_gate_shape=CollisionShape3D.new();body.add_child(trial_gate_shape);var box=BoxShape3D.new();box.size=Vector3(4.2,2,.18);trial_gate_shape.shape=box
	trial_gate_rect=Rect2(-2.5,3.5,5,1);obstacles.append(trial_gate_rect)

func setup_navigation() -> void:
	nav.region=Rect2i(-58,-56,116,110);nav.cell_size=Vector2(.5,.5);nav.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES;nav.update();refresh_nav()

func refresh_nav() -> void:
	for x in range(nav.region.position.x,nav.region.end.x):
		for z in range(nav.region.position.y,nav.region.end.y):
			var p=Vector2(x*.5,z*.5);var solid=not bounds.grow(-.65).has_point(p)
			if not solid:
				for rect in obstacles:
					if rect.has_point(p):solid=true;break
			nav.set_point_solid(Vector2i(x,z),solid)

func setup_ui() -> void:
	super.setup_ui();landmark=make_label("ЛЕСНОЙ ПОЛУСТАНОК" if landscape=="forest" else "ПРОМЫТЫЙ ГРУЗОВОЙ ДВОР",Vector2(42,112),21,Color("acbf9a"))

func follow_camera(delta: float) -> void:
	var center=hero.get_global_transform_interpolated().origin+Vector3.UP*.8
	camera.position=camera.position.lerp(center+camera_offset,1.0-exp(-7.0*minf(delta,.1)))
	update_occlusion(delta)

func update_task() -> void:
	objective.text=captions[mission] if mission<3 else "Участок пройден · F2 — другие остановки · R — повторить"
	help.text="";work_bar.visible=false

func interactions(delta: float) -> void:
	help.text="";work_bar.visible=false
	if trial_open:trial_gate.position.y=move_toward(trial_gate.position.y,3.5,delta*2)
	if mission>=3:return
	if not Input.is_physical_key_pressed(KEY_E):input_latched=false
	if hero.position.distance_to(goals[mission])>=1.65:work=0;return
	help.text="Удерживать E · "+task_names[mission]
	if input_latched or not Input.is_physical_key_pressed(KEY_E) or hero.ground_speed>.15 or hero.attack_left>0 or hero.dash_left>0 or hero.stun>0:work=0;return
	work+=delta;work_bar.visible=true;work_bar.value=work/.7*100
	if work>=.7:
		work=0;input_latched=true;actions.append({"stage":mission,"seconds":clock});mission+=1
		if mission==2:
			trial_open=true;trial_gate_shape.set_deferred("disabled",true);obstacles.erase(trial_gate_rect);refresh_nav();signal_light.light_color=Color("8db39a")
		sound("impactMetal_medium_003",hero.position,-18);update_task()
		say("Пост проверен. Проход открыт, возвращайся к составу." if mission==2 else "Рукоять целая. Теперь к сигнальному посту." if mission==1 and landscape=="forest" else "Перемычка найдена. Теперь к приводу ворот." if mission==1 else "Вылазка завершена. Можно выбрать другую остановку — F2.",5)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode==KEY_R and (player_down or mission>=3):get_tree().reload_current_scene();return
	super._unhandled_input(event)
