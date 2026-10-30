extends "res://scripts/main.gd"
## First expedition. Keeps the combat prototype as a separate diagnostic scene.

const SAVE_VERSION=1
const DOCK=Vector3(-33.3,0,30)
const RELAY=Vector3(20,0,-34)
const GENERATOR=Vector3(22,0,-21)
const STOPPER=Vector3(-20,0,-30)
const MANUAL=Vector3(34,0,-10)
const PATIENT_POINT=Vector3(47,0,-14.7)
const INNER_BOLT=Vector3(54,0,-8.0)
const SERVICE_BOLT=Vector3(-3,0,17)

var zones: Array = [
	{"id":"platform","name":"Служебная платформа","rect":Rect2(-36,12,24,28),"color":Color("687069")},
	{"id":"hall","name":"Зал ожидания","rect":Rect2(-34,-14,28,26),"color":Color("70736a")},
	{"id":"yard","name":"Служебный двор","rect":Rect2(-6,-14,42,26),"color":Color("4e605c")},
	{"id":"workshop","name":"Мастерская","rect":Rect2(-34,-40,28,26),"color":Color("69604f")},
	{"id":"relay","name":"Релейная","rect":Rect2(10,-40,20,26),"color":Color("536665")},
	{"id":"side","name":"Технический проход","rect":Rect2(-6,-33,16,6),"color":Color("4e5b58")},
	{"id":"pharmacy","name":"Вокзальная аптека","rect":Rect2(36,-28,23,22),"color":Color("68786c")},
	{"id":"east","name":"Служебная галерея","rect":Rect2(49,-6,10,18),"color":Color("5f6d62")},
	{"id":"service","name":"Обратный служебный путь","rect":Rect2(-12,12,71,10),"color":Color("4a5956")}
]
var power_on := false
var has_stopper := false
var door_method := ""
var cart_loaded := false
var cart_attached := false
var inner_open := false
var service_open := false
var note_read := false
var supplies_taken: Array = []
var killed: Array = []
var visited: Array = []
var cart: CharacterBody3D
var cart_path: Array[Vector3] = []
var cart_wheels: Array[Node3D] = []
var gates: Dictionary = {}
var target_action := ""
var checkpoint: Dictionary = {}
var save_path := "user://expedition-v036.json"
var fresh := false
var e_latched := false
var map_view: Control
var location_label: Label
var direction_label: Label
var checkpoint_label: Label
var map_clock := 0.0
var checkpoint_time := 0.0
var last_zone := ""
var cart_distance := 0.0
var total_distance := 0.0
var last_hero_position := Vector3.ZERO
var blockout_only := false
var action_log: Array = []
var carry_rig=preload("res://scripts/carry_ik.gd").new()
var supply_positions := {"hall":Vector3(-30,0,3),"relay":Vector3(26,0,-37),"pharmacy":Vector3(39,0,-23)}

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg=="--preview":auto_preview=true
		if arg=="--fresh":fresh=true
		if arg=="--blockout":blockout_only=true
		if arg.begins_with("--capture="):capture_dir=arg.trim_prefix("--capture=")
		if arg.begins_with("--save-slot="):
			var filename=arg.trim_prefix("--save-slot=").get_file()
			if filename.begins_with("qa-"):save_path="user://"+filename
	var fresh_key="fresh_consumed_"+save_path.get_file().replace(".","_").replace("-","_")
	if fresh:
		if get_tree().root.has_meta(fresh_key):fresh=false
		else:get_tree().root.set_meta(fresh_key,true)
	setup_world();build_station();setup_navigation()
	hero=spawn_actor("",DOCK+Vector3(3,0,-2));hero.collision_mask|=8;last_hero_position=hero.position
	spawn_encounters();setup_camera();setup_ui()
	if not fresh and FileAccess.file_exists(save_path):
		var decoded=JSON.parse_string(FileAccess.get_file_as_string(save_path))
		if decoded is Dictionary and decoded.get("version",0)==SAVE_VERSION:checkpoint=decoded;apply_checkpoint()
	if checkpoint.is_empty():save_checkpoint("У поезда")
	update_objective()
	if mission==0:say("Лида · рация\nМихаил в аптеке за двором. Жалюзи заклинило. В мастерской должен быть стопор.",6)
	elif mission==1:say("Нина · рация\nЖалюзи открыты. Проверь аптеку — носилки у дальней стены.",4)
	elif mission==2:say("Лида · рация\nПродолжим. Носилки там, где оставили. Я жду у вагона.",4)
	else:say("Лида · рация\nМихаил в вагоне. Я рядом.",4)
	print("EXPEDITION_READY zones=",zones.size()," actors=",enemies.size()," mission=",mission," save=",save_path)

func setup_world() -> void:
	super.setup_world()
	for node in get_children():
		if node is WorldEnvironment:node.environment.ambient_light_energy=.52;node.environment.fog_density=.002
		if node is DirectionalLight3D:node.light_energy=.62
		if node is ReflectionProbe:node.size=Vector3(110,14,95);node.position=Vector3(10,2,0)

func inside_floor(point: Vector2) -> bool:
	for zone in zones:
		if zone.rect.has_point(point):return true
	return false

func build_station() -> void:
	block(Vector3(10,-.55,0),Vector3(125,.5,110),Color("172724"))
	for zone in zones:
		var r: Rect2=zone.rect;var center=r.get_center()
		var floor_node=block(Vector3(center.x,-.14,center.y),Vector3(r.size.x,.28,r.size.y),zone.color,true)
		var material=ShaderMaterial.new();material.shader=load("res://shaders/expedition_floor.gdshader");material.set_shader_parameter("base_color",zone.color)
		material.set_shader_parameter("tile_size",.5 if zone.id=="pharmacy" else 1.0 if zone.id in ["hall","platform"] else 1.5 if zone.id in ["workshop","relay"] else 0.0);mesh_in(floor_node).material_override=material
	perimeter()
	# Architectural partitions with real, adult-sized openings.
	wall_x(-6,-14,-6);wall_x(-6,-2,12)
	wall_z(-14,-34,-24);wall_z(-14,-20,-6)
	wall_z(-14,10,18);wall_z(-14,22,30)
	wall_x(36,-28,-12);wall_x(36,-8,-6)
	wall_z(-6,36,52);wall_z(-6,56,59)
	wall_z(12,-34,-26);wall_z(12,-22,-6)
	make_gate("pharmacy",Vector3(36,0,-10),4.0,true,false)
	make_gate("inner",Vector3(54,0,-6),4.0,false,false)
	make_gate("service",Vector3(-9,0,17),10.0,true,false)
	make_gate("hall_return",Vector3(-24,0,12),4.0,false,true)
	# Distant destination remains a physical carriage in the same projection.
	block(Vector3(-39,1.4,27),Vector3(4,2.7,24),Color("2c4942"),true,.45,.3)
	for z in range(17,39,3):
		block(Vector3(-36.96,1.8,z),Vector3(.06,.82,1.7),Color("ac9564"))
		block(Vector3(-36.91,1.8,z),Vector3(.035,.64,1.5),Color("435b58"),false,.2,.2)
	block(Vector3(-35.8,.18,30),Vector3(2,.36,3),Color("718279"),true)
	label_world("ПОЕЗД · ПОСАДКА",Vector3(-34,2.2,30),.010)
	for p in [Vector3(-30,0,26),Vector3(-28,0,10),Vector3(-30,0,-9),Vector3(-7,0,-8),Vector3(10,0,4),Vector3(30,0,-7),Vector3(17,0,-17),Vector3(-27,0,-26),Vector3(42,0,-11),Vector3(55,0,6),Vector3(35,0,17),Vector3(5,0,17)]:lamp(p)
	# Interactables have readable geometry even in the blockout pass.
	block(RELAY+Vector3(0,1,0),Vector3(1.6,2,.5),Color("3d5956"),true,.5,.2)
	label_world("РЕЛЕЙНАЯ · ПРИВОД",RELAY+Vector3(0,2.4,.2),.009)
	block(GENERATOR+Vector3(0,.55,-1),Vector3(1.6,1.1,1.2),Color("796448"),true,.6,.3)
	label_world("ГЕНЕРАТОР",GENERATOR+Vector3(0,1.7,-.7),.009)
	block(STOPPER+Vector3(0,.7,-1),Vector3(2.4,1.4,1.1),Color("69523c"),true)
	block(STOPPER+Vector3(0,1.46,-1),Vector3(.45,.08,.13),Color("ac9e7c"),false,.25,.7)
	label_world("МАСТЕРСКАЯ",STOPPER+Vector3(0,2.3,-1),.010)
	label_world("АПТЕКА",Vector3(36.25,2.7,-10),.010).rotation.y=PI*.5
	label_world("СЛУЖЕБНЫЙ ВЫХОД",Vector3(54,2.8,-6),.008)
	for id in supply_positions:
		var p: Vector3=supply_positions[id]
		block(p+Vector3(0,.5,-.4),Vector3(.55,1,.4),Color("8b8e71"),true)
		label_world("ПЕРЕВЯЗКА / РАКЕТА",p+Vector3(0,1.45,-.4),.006)
	build_cart()
	if not blockout_only:dress_level()

func wall_x(x: float,a: float,b: float) -> void:
	if b>a:block(Vector3(x,1.3,(a+b)*.5),Vector3(.24,2.6,b-a),Color("415a53"),true)

func wall_z(z: float,a: float,b: float) -> void:
	if b>a:block(Vector3((a+b)*.5,1.3,z),Vector3(b-a,2.6,.24),Color("415a53"),true)

func perimeter() -> void:
	# Merge occupied one-metre boundary edges into straight wall segments.
	for horizontal in [true,false]:
		var segments: Dictionary={}
		for x in range(-37,61):
			for z in range(-41,42):
				var a=Vector2(x+.5,z-.5) if horizontal else Vector2(x-.5,z+.5)
				var b=Vector2(x+.5,z+.5)
				if inside_floor(a)==inside_floor(b):continue
				var line=z if horizontal else x;var step=x if horizontal else z
				if not segments.has(line):segments[line]=[]
				segments[line].append(step)
		for line in segments:
			var steps: Array=segments[line];steps.sort();var first_step=int(steps[0]);var previous=first_step
			for step in steps.slice(1)+[9999]:
				if int(step)!=previous+1:
					if horizontal:wall_z(line,first_step,previous+1)
					else:wall_x(line,first_step,previous+1)
					first_step=step
				previous=step

func make_gate(id: String,pos: Vector3,width: float,along_z: bool,is_open: bool) -> void:
	var root_node=Node3D.new();add_child(root_node);root_node.position=pos
	var dimensions=Vector3(.22,2.25,width) if along_z else Vector3(width,2.25,.22)
	var panel=block(Vector3(0,1.125,0),dimensions,Color("7b6347"),false,.65,.2,root_node)
	var body=StaticBody3D.new();root_node.add_child(body);body.collision_layer=1
	var shape=CollisionShape3D.new();body.add_child(shape);shape.position.y=1.125
	var box=BoxShape3D.new();box.size=dimensions;shape.shape=box
	var rect=Rect2(Vector2(pos.x-dimensions.x*.5,pos.z-dimensions.z*.5),Vector2(dimensions.x,dimensions.z)).grow(.35)
	gates[id]={"node":root_node,"collider":shape,"rect":rect,"open":is_open,"height":3.0 if is_open else 0.0,"panel":mesh_in(panel)}
	if not is_open:obstacles.append(rect)
	root_node.position.y=3.0 if is_open else 0.0;shape.disabled=is_open

func set_gate(id: String,is_open: bool,instant:=false) -> void:
	var data: Dictionary=gates[id]
	if data.open!=is_open:
		data.open=is_open
		if is_open:obstacles.erase(data.rect)
		else:obstacles.append(data.rect)
		refresh_nav()
	data.collider.set_deferred("disabled",is_open and instant)
	if instant:data.node.position.y=3.0 if is_open else 0.0

func setup_navigation() -> void:
	nav.region=Rect2i(-74,-82,196,166);nav.cell_size=Vector2(.5,.5)
	nav.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES;nav.update();refresh_nav()

func refresh_nav() -> void:
	for x in range(nav.region.position.x,nav.region.end.x):
		for z in range(nav.region.position.y,nav.region.end.y):
			var p=Vector2(x*.5,z*.5);var solid=false
			for offset in [Vector2(-.4,0),Vector2(.4,0),Vector2(0,-.4),Vector2(0,.4)]:
				if not inside_floor(p+offset):solid=true;break
			if not solid:
				for r in obstacles:
					if r.has_point(p):solid=true;break
			if not solid and is_instance_valid(cart) and not cart_attached:
				var local=cart.global_transform.affine_inverse()*Vector3(p.x,0,p.y)
				if absf(local.x)<.78 and absf(local.z)<1.4:solid=true
			nav.set_point_solid(Vector2i(x,z),solid)

func spawn_encounters() -> void:
	var definitions=[
		["walker",Vector3(-25,0,6)],["runner",Vector3(-17,0,-5)],
		["walker",Vector3(-11,0,3)],["runner",Vector3(3,0,-5)],
		["walker",Vector3(13,0,4)],["brute",Vector3(25,0,2)],
		["walker",Vector3(-26,0,-22)],["brute",Vector3(-14,0,-34)],
		["runner",Vector3(-2,0,-30)],["walker",Vector3(6,0,-29)],
		["walker",Vector3(16,0,-27)],["runner",Vector3(26,0,-30)],
		["walker",Vector3(27,0,-37)],["brute",Vector3(31,0,-10)],
		["walker",Vector3(43,0,-22)],["runner",Vector3(54,0,7)],
		["walker",Vector3(40,0,17)],["brute",Vector3(18,0,17)]]
	for i in definitions.size():
		var foe=spawn_actor(definitions[i][0],definitions[i][1]);foe.set_meta("id",i)
		if i in [11,12]:foe.set_meta("hears_generator",true)

func setup_ui() -> void:
	super.setup_ui()
	location_label=make_label("",Vector2(42,110),20,Color("adbfb9"))
	direction_label=make_label("",Vector2(42,141),18,Color("d8be8c"))
	checkpoint_label=make_label("",Vector2(42,180),18,Color("a0c5b6"))
	map_view=load("res://scripts/expedition_map.gd").new();ui.add_child(map_view)
	map_view.position=Vector2(1644,32);map_view.size=Vector2(240,238);map_view.game=self
	make_label("СХЕМА · M",Vector2(1660,39),16,Color("bbc8bb"))

func follow_camera(delta: float) -> void:
	var p=hero.get_global_transform_interpolated().origin
	var target=p+Vector3.UP*.8
	camera.position=camera.position.lerp(target+camera_offset,1-exp(-7*minf(delta,.1)))
	update_occlusion(delta)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode==KEY_R:
			if player_down:restart_checkpoint()
			return
		if event.keycode==KEY_M:
			map_view.visible=not map_view.visible;return
		if event.keycode==KEY_N and mission==3:
			fresh=true;checkpoint.clear();FileAccess.open(save_path,FileAccess.WRITE).store_string("{}");get_tree().reload_current_scene();return
	if cart_attached and event is InputEventMouseButton and event.pressed:return
	if cart_attached and event is InputEventKey and event.keycode==KEY_SPACE:return
	super._unhandled_input(event)

func _physics_process(delta: float) -> void:
	if cart_attached and not paused and not player_down:
		# Cart manoeuvring uses physical walk speed, not instant position snapping.
		if cart.position.distance_to(hero.position)>3.2:
			cart_attached=false;cart_path.clear();refresh_nav();say("Артём\nЗацепилось. Надо освободить проход и взять носилки снова.",3)
	super._physics_process(delta)
	if paused or player_down:return
	total_distance+=hero.position.distance_to(last_hero_position);last_hero_position=hero.position
	for foe in enemies:
		if is_instance_valid(foe) and not foe.alive and not killed.has(foe.get_meta("id",-1)):killed.append(foe.get_meta("id",-1))
	for id in gates:
		var data: Dictionary=gates[id];data.node.position.y=move_toward(data.node.position.y,3.0 if data.open else 0.0,delta*3.5)
		data.collider.set_deferred("disabled",data.open and data.node.position.y>=2.25)
	update_cart(delta)
	carry_rig.apply(hero,cart,cart_attached,delta)
	map_clock+=delta;checkpoint_time=maxf(0,checkpoint_time-delta)
	checkpoint_label.visible=checkpoint_time>0
	if map_clock>.2:
		map_clock=0;map_view.queue_redraw();update_location()
		var distance=hero.position.distance_to(objective_position())
		direction_label.text="До ориентира: "+str(int(distance))+" м · M — схема"
		if mission==0 and not has_stopper and not power_on:direction_label.text="Стопор: "+str(int(hero.position.distance_to(STOPPER)))+" м · Генератор: "+str(int(hero.position.distance_to(GENERATOR)))+" м · M — схема"
	if mission==3 and help.text=="":help.text="Михаил в вагоне · у поезда E — продолжить · N — повторить вылазку"

func movement_speed() -> float:
	return 2.65 if cart_attached else super.movement_speed()

func try_dodge() -> void:
	if cart_attached:return
	super.try_dodge()

func update_location() -> void:
	var point=Vector2(hero.position.x,hero.position.z)
	for zone in zones:
		if zone.rect.has_point(point):
			location_label.text=zone.name
			if not visited.has(zone.id):visited.append(zone.id)
			if last_zone!=zone.id:
				last_zone=zone.id
				if zone.id=="yard" and not note_read and mission==0:say("Нина · рация\nМожно через мастерскую. Или запитать привод в релейной — но генератор будет слышно.",5)
			return

func objective_position() -> Vector3:
	if mission==3:return DOCK
	if mission==2:
		if not inner_open:return INNER_BOLT
		if not service_open:return SERVICE_BOLT
		return DOCK
	if mission==1:return PATIENT_POINT
	if has_stopper:return MANUAL
	if power_on:return RELAY
	return STOPPER

func update_objective() -> void:
	if mission==0:objective.text="Открыть аптеку: стопор в мастерской или питание в релейной"
	if mission==1:objective.text="Найти Михаила и подготовить носилки"
	if mission==2:
		objective.text="Вывести Михаила через служебный выход" if not inner_open else "Отпереть служебную калитку" if not service_open else "Доставить Михаила к вагону"
	if mission==3:objective.text="Михаил в безопасности · первая вылазка завершена"

func interactions(delta: float) -> void:
	help.text="";work_bar.visible=false
	if not Input.is_physical_key_pressed(KEY_E):e_latched=false
	var candidate="";var prompt="";var nearest=1.65;var options: Array=[]
	if mission==0:
		if not power_on:options.append(["generator",GENERATOR,"Запустить генератор · шум привлечёт путевых"])
		if not has_stopper:options.append(["stopper",STOPPER,"Взять стопор со стола"])
		options.append(["relay",RELAY,"Поднять жалюзи" if power_on else "Щит обесточен · генератор южнее"])
		options.append(["manual",MANUAL,"Зафиксировать ручной привод" if has_stopper else "Нужен стопор из мастерской"])
	if mission==1:options.append(["patient",PATIENT_POINT,"Подготовить Михаила к эвакуации"])
	if mission==2:
		if not inner_open:options.append(["inner",INNER_BOLT,"Отпереть засов изнутри"])
		if not service_open:options.append(["service",SERVICE_BOLT,"Отпереть калитку к платформе"])
		if cart.position.distance_to(DOCK)<3.0:options.append(["board",DOCK,"Подать носилки к вагону"])
		if not cart_attached and hero.position.distance_to(cart.position)<3.5:
			var a=cart.to_global(Vector3(0,0,1.4));var b=cart.to_global(Vector3(0,0,-1.4))
			options.append(["cart",a if a.distance_to(hero.position)<b.distance_to(hero.position) else b,"Взять носилки"])
	if mission==3:options.append(["depart",DOCK,"Отправиться на больничную ветку"])
	if not note_read:options.append(["note",STOPPER+Vector3(1.2,0,0),"Прочитать запись дежурного"])
	for id in supply_positions:
		if not supplies_taken.has(id):options.append(["supply:"+id,supply_positions[id],"Перевязка и сигнальная ракета · один раз"])
	for option in options:
		var distance=hero.position.distance_to(option[1])
		if distance<nearest:nearest=distance;candidate=option[0];prompt=option[2]
	if candidate=="" and cart_attached:candidate="cart";prompt="Оставить носилки и освободить руки"
	if candidate=="":work=0;target_action="";return
	help.text="E · "+prompt
	if not Input.is_physical_key_pressed(KEY_E) or e_latched or hero.ground_speed>.15 or hero.attack_left>0 or hero.dash_left>0:
		work=0;return
	if candidate!=target_action:target_action=candidate;work=0
	work+=delta;work_bar.visible=true;work_bar.value=work/.65*100
	if work>=.65:work=0;e_latched=true;perform_action(candidate)

func perform_action(action: String) -> void:
	action_log.append({"action":action,"mission":mission,"seconds":clock,"position":vec(hero.position)})
	match action:
		"depart":
			if mission==3 and hero.position.distance_to(DOCK)<1.65:
				var result=preload("res://scripts/campaign.gd").depart(get_tree())
				if result!=OK:say("Не удалось открыть следующую остановку. Сохранение Михаила осталось на месте.",5)
		"generator":
			power_on=true
			for foe in enemies:
				if is_instance_valid(foe) and foe.alive and foe.has_meta("hears_generator"):foe.home=GENERATOR
			sound("impactMetal_heavy_000",GENERATOR,-12);say("Нина · рация\nПривод ожил. Путевые идут на шум — не задерживайся у генератора.",5)
		"stopper":has_stopper=true;say("Артём\nПодойдёт. Теперь к ручному приводу у аптеки.",4)
		"relay":
			if power_on:open_pharmacy("power")
			else:say("Артём\nПитания нет. Генератор у стены перед релейной.",3)
		"manual":
			if has_stopper:open_pharmacy("stopper")
			else:say("Артём\nБез стопора не удержится. Надо в мастерскую.",3)
		"patient":
			cart_loaded=true;mission=2;cart_attached=false
			set_gate("hall_return",false);set_gate("inner",false)
			say("Михаил\nЯ слышал поезд. Думал, снова проедет мимо.\nНина · рация: Обратные жалюзи упали. Выходите через служебную галерею.",7)
			update_objective();save_checkpoint("Аптека · Михаил найден")
		"inner":inner_open=true;set_gate("inner",true);update_objective();save_checkpoint("Служебный выход открыт")
		"service":service_open=true;set_gate("service",true);update_objective();save_checkpoint("Путь к вагону открыт")
		"cart":
			cart_attached=not cart_attached;cart_path.clear()
			if cart_attached:cart_path.append(hero.position)
			refresh_nav()
		"board":
			if cart_loaded and cart.position.distance_to(DOCK)<3:
				cart_attached=false;mission=3;place_patient_in_train()
				say("Лида · рация\nПриняла. Михаил в вагоне. Держит мою руку — значит, слышит.\nАртём: До следующей станции довезу.",7)
				update_objective();save_checkpoint("Михаил в вагоне")
		"note":note_read=true;say("Запись дежурного\n«Привод не держит. Стопор лежит на верстаке. Служебную калитку отпирать со двора».",7)
	if action.begins_with("supply:"):
		var id=action.trim_prefix("supply:")
		if not supplies_taken.has(id):supplies_taken.append(id);hero.health=minf(100,hero.health+45);flares=mini(3,flares+1);say("Артём\nПеревязка есть. Можно идти.",2)

func open_pharmacy(method: String) -> void:
	mission=1;door_method=method;opened=true;set_gate("pharmacy",true);update_objective()
	say("Нина · рация\nЖалюзи подняты. Проверь аптеку. Носилки у дальней стены.",4)
	save_checkpoint("Аптека открыта")

func place_patient_in_train() -> void:
	if patient.get_parent()!=self:patient.reparent(self)
	patient.global_position=Vector3(-38.0,1.35,30)
	patient.rotation=Vector3(-PI*.5,0,0);patient.visible=true

func build_cart() -> void:
	cart=CharacterBody3D.new();add_child(cart);cart.name="PatientStretcher";cart.position=Vector3(47,0,-17)
	cart.collision_layer=8;cart.collision_mask=1;cart.floor_snap_length=.3
	var collider=CollisionShape3D.new();cart.add_child(collider)
	var box=BoxShape3D.new();box.size=Vector3(.82,1.0,2.05);collider.shape=box;collider.position.y=.5
	block(Vector3(0,.72,0),Vector3(.72,.12,2.05),Color("778b73"),false,.85,0,cart)
	for x in [-.4,.4]:
		block(Vector3(x,.64,0),Vector3(.04,.04,2.55),Color("98a79a"),false,.3,.7,cart)
		for end in [-1.55,1.55]:
			block(Vector3(x,.64,end*.90),Vector3(.04,.04,.40),Color("98a79a"),false,.3,.7,cart)
			block(Vector3(x,.82,end),Vector3(.035,.36,.035),Color("98a79a"),false,.3,.7,cart)
			block(Vector3(x,.99,end),Vector3(.07,.07,.26),Color("34483d"),false,.8,0,cart)
		for z in [-.77,.77]:
			block(Vector3(x,.40,z),Vector3(.04,.55,.04),Color("879b91"),false,.4,.6,cart)
			var wheel=cylinder(Vector3(x,.13,z),.13,.07,Color("243531"),cart);wheel.rotation.z=PI*.5;cart_wheels.append(wheel)
	patient=load("res://assets/characters/patient.glb").instantiate();cart.add_child(patient)
	patient.scale=Vector3.ONE*(1.75/4.805);patient.position=Vector3(0,.84,.84);patient.rotation.x=-PI*.5
	var animation=hero_animation(patient)
	if animation:
		for clip in animation.get_animation_list():
			if clip.ends_with("Man_Idle"):animation.play(clip);animation.advance(0);animation.pause()

func update_cart(delta: float) -> void:
	if not cart_loaded or mission==3:return
	if cart_attached:
		if cart_path.is_empty() or cart_path[-1].distance_to(hero.position)>.28:cart_path.append(hero.position)
		while cart_path.size()>1 and cart.position.distance_to(cart_path[0])<.28:cart_path.remove_at(0)
		var desired=Vector3.ZERO
		var separation=cart.position.distance_to(hero.position)
		if not cart_path.is_empty() and separation>1.32:
			var lead_direction=(hero.position-cart.position).normalized()
			var feed_forward=maxf(0,Vector3(hero.velocity.x,0,hero.velocity.z).dot(lead_direction))
			var tow_speed=clampf(feed_forward+(separation-1.60)*7.0,0,6.3)
			desired=(cart_path[0]-cart.position).normalized()*tow_speed
		var before=cart.position;cart.velocity=Vector3(desired.x,-1,desired.z);cart.move_and_slide()
		var travelled=cart.position.distance_to(before);cart_distance+=travelled
		# Steer the handles toward the person pulling them, rather than toward an
		# old breadcrumb. Keep the nearer end to avoid a 180-degree flip on pickup.
		var lead=hero.position-cart.position;lead.y=0
		if lead.length()>.2:
			var angle=atan2(lead.x,lead.z)
			if lead.dot(cart.basis.z)<0:angle+=PI
			cart.rotation.y=rotate_toward(cart.rotation.y,angle,delta*6.0)
		for wheel in cart_wheels:wheel.rotation.y+=travelled/.13
	else:cart.velocity=Vector3(0,-1,0);cart.move_and_slide()

func vec(point: Vector3) -> Array:return [point.x,point.y,point.z]
func unvec(value: Array) -> Vector3:return Vector3(value[0],value[1],value[2])

func save_checkpoint(label: String) -> void:
	checkpoint={"version":SAVE_VERSION,"label":label,"mission":mission,"power_on":power_on,"has_stopper":has_stopper,"door_method":door_method,"cart_loaded":cart_loaded,"inner_open":inner_open,"service_open":service_open,"note_read":note_read,"supplies":supplies_taken.duplicate(),"killed":killed.duplicate(),"hero":vec(hero.position),"cart":vec(cart.position),"cart_rotation":cart.rotation.y,"health":hero.health,"flares":flares,"visited":visited.duplicate()}
	var file=FileAccess.open(save_path,FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(checkpoint));file.close()
	checkpoint_label.text="Контрольная точка · "+label;checkpoint_time=4

func apply_checkpoint() -> void:
	mission=int(checkpoint.get("mission",0));power_on=checkpoint.get("power_on",false);has_stopper=checkpoint.get("has_stopper",false)
	door_method=checkpoint.get("door_method","");cart_loaded=checkpoint.get("cart_loaded",false);inner_open=checkpoint.get("inner_open",false);service_open=checkpoint.get("service_open",false);note_read=checkpoint.get("note_read",false)
	supplies_taken=checkpoint.get("supplies",[]).duplicate();killed=checkpoint.get("killed",[]).duplicate();visited=checkpoint.get("visited",[]).duplicate()
	# JSON numbers are floats; Array.has on typed Variant values needs matching IDs.
	for i in killed.size():killed[i]=int(killed[i])
	hero.position=unvec(checkpoint.get("hero",vec(DOCK)));hero.health=clampf(checkpoint.get("health",100),1,100);flares=int(checkpoint.get("flares",3));hero.reset_physics_interpolation()
	cart.position=unvec(checkpoint.get("cart",[47,0,-17]));cart.rotation.y=checkpoint.get("cart_rotation",0);cart.reset_physics_interpolation();cart_attached=false;cart_path.clear();patient.visible=mission<3
	if mission==3:place_patient_in_train()
	set_gate("pharmacy",mission>=1,true);set_gate("inner",inner_open,true);set_gate("service",service_open,true);set_gate("hall_return",mission<2,true)
	for foe in enemies:
		if is_instance_valid(foe) and killed.has(foe.get_meta("id",-1)):foe.alive=false;foe.queue_free()
	last_hero_position=hero.position;update_objective()

func restart_checkpoint() -> void:
	# A fresh scene rebuilds enemies/colliders, then restores the persisted checkpoint.
	get_tree().reload_current_scene()

func dress_level() -> void:
	for z in range(15,40,2):
		block(Vector3(-38.5,-.08,z),Vector3(3.5,.16,.20),Color("3b352d"))
	for x in [-39.5,-37.7]:block(Vector3(x,.04,27),Vector3(.07,.12,27),Color("73847a"),false,.3,.7)
	for z in [19,25,36]:
		block(Vector3(-31.8,1.4,z),Vector3(.22,2.8,.22),Color("37534c"),true,.5,.3)
		block(Vector3(-31.8,.12,z),Vector3(.42,.24,.42),Color("8b8e75"))
	block(Vector3(-31.8,2.84,27.5),Vector3(.22,.18,20),Color("36534a"))
	for z in [18,23,36]:bench(Vector3(-22,0,z))
	for p in [Vector3(-30,0,1),Vector3(-20,0,1),Vector3(-30,0,-9),Vector3(-18,0,-9)]:bench(p)
	for p in [Vector3(2,0,6),Vector3(18,0,-8),Vector3(31,0,7),Vector3(-31,0,-32),Vector3(-9,0,-36),Vector3(42,0,20)]:crate(p,Vector3(1.1,1.0,.9))
	for x in [-31,-25,-19,-13]:
		block(Vector3(x,.8,-39),Vector3(1.8,1.6,.7),Color("574f40"),true)
		block(Vector3(x,1.7,-38.9),Vector3(1.7,.12,.8),Color("9d8660"))
	for z in [-24,-20,-16]:
		block(Vector3(58,.8,z),Vector3(.6,1.6,2.4),Color("717c69"),true)
		for y in [.55,1.1,1.6]:block(Vector3(57.65,y,z),Vector3(.2,.05,2.45),Color("b2b09a"))
	for x in [13,17,21,25]:
		block(Vector3(x,1.1,-39.3),Vector3(2,2.2,.6),Color("3c5550"),true,.6,.3)
		for y in [.8,1.3,1.8]:block(Vector3(x,y,-38.96),Vector3(1.7,.025,.035),Color("a18e63"))
	for x in range(-5,34,4):
		block(Vector3(x,.025,10),Vector3(2.5,.04,.18),Color("aca17d"))
	for z in range(14,40,3):
		block(Vector3(-35,.03,z),Vector3(.16,.04,1.1),Color("c8af6e"))
	# Ticket office, workshop machinery and electrical cabinets anchor each room.
	block(Vector3(-9.2,1.0,-9.7),Vector3(3.6,2,2),Color("586c60"),true)
	block(Vector3(-11.05,1.25,-9.7),Vector3(.08,.65,1.4),Color("b4aa7e"))
	label_world("КАССА",Vector3(-11.1,2.2,-9.7),.007).rotation.y=-PI*.5
	for z in [-11,-7,-3,1,5,9]:
		block(Vector3(-33.7,1.5,z),Vector3(.12,1.2,2),Color("708c86"),false,.35,.1)
		for y in [.86,2.14]:block(Vector3(-33.55,y,z),Vector3(.22,.08,2.2),Color("9b9b81"))
	for p in [Vector3(-29,0,-17),Vector3(-10,0,-22)]:
		block(p+Vector3(0,.6,0),Vector3(1.4,1.2,2.2),Color("4d6660"),true,.6,.3)
		cylinder(p+Vector3(0,1.4,-.5),.38,.5,Color("7c8e7e")).rotation.z=PI*.5
	for p in [Vector3(5,0,-11),Vector3(16,0,9),Vector3(33,0,-3)]:
		block(p+Vector3(0,.9,0),Vector3(2,1.8,1.4),Color("536e63"),true,.55,.3)
		for y in [.5,1,1.5]:block(p+Vector3(0,y,.72),Vector3(1.7,.035,.04),Color("8c9b83"))
	for z in [-35,-31,-27]:
		block(Vector3(11,1.4,z),Vector3(.2,1.2,1.7),Color("5f7f7a"))
		block(Vector3(10.8,.76,z),Vector3(.4,.08,1.9),Color("9d9a7d"))
	for x in range(-3,35,3):
		block(Vector3(x,.018,14),Vector3(1.7,.018,.08),Color("b9ad7c"))
	for z in range(-4,12,3):block(Vector3(51,.018,z),Vector3(.08,.018,1.7),Color("b9ad7c"))
	# Drains and industrial notices provide scale without cluttering the route.
	for x in [3,17,30]:
		block(Vector3(x,.012,7),Vector3(2,.024,.35),Color("263b37"))
		for i in range(12):block(Vector3(x-.9+i*.16,.03,7),Vector3(.035,.025,.32),Color("788879"))
	label_world("ПЛАТФОРМА ←",Vector3(-8,2.4,17),.009).rotation.y=PI*.5
	label_world("МАСТЕРСКАЯ ←    РЕЛЕЙНАЯ →",Vector3(-5.7,2.3,-3.8),.007).rotation.y=PI*.5
