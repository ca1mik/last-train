extends "res://scripts/main.gd"
## Chapter 2 route-restoration slice. Route completion is NOT passenger evacuation.
const DOCK=Vector3(-23,0,25)
const JUMPER=Vector3(-26,0,-30)
const WINCH=Vector3(-12,0,-30)
const SOCKET=Vector3(-22,0,-26)
const FEED_A=Vector3(-24,0,-20)
const FEED_B=Vector3(-15,0,-20)
const TEST=Vector3(-18,0,-25)
const DRIVE=Vector3(17,0,-26)
const REFUGE=Vector3(37,0,-3)
var zones: Array=[
	{"id":"wagon","name":"Пассажирский вагон","rect":Rect2(-39,15,4,18),"color":Color("807861")},
	{"id":"wagon_door","name":"Вход в вагон","rect":Rect2(-35,23,1,3),"color":Color("77785e")},
	{"id":"platform","name":"Больничная платформа","rect":Rect2(-34,14,26,20),"color":Color("68746e")},
	{"id":"west","name":"Хозяйственный проход","rect":Rect2(-32,-12,24,26),"color":Color("566762")},
	{"id":"court","name":"Распределительный двор","rect":Rect2(-8,-12,36,26),"color":Color("445954")},
	{"id":"store","name":"Склад и проверочный щит","rect":Rect2(-32,-36,24,24),"color":Color("696750")},
	{"id":"link","name":"Кабельная галерея","rect":Rect2(-8,-32,12,8),"color":Color("50625d")},
	{"id":"switch","name":"Стрелочный пост","rect":Rect2(4,-36,24,24),"color":Color("5c6f63")},
	{"id":"refuge","name":"Окна убежища","rect":Rect2(28,-12,18,20),"color":Color("716d57")}]
var visited: Array=[]
var killed: Array=[]
var supplies: Array=[]
var has_jumper := false
var has_winch := false
var installed := false
var feed_a := false
var feed_b := false
var tested := false
var winch_stage := 0
var winch_turns := 0
var visual_spin := 0.0
var route_method := ""
var work_branch := ""
var refuge_heard := false
var reserve_on := true
var save_path := "user://hospital-v037.json"
var e_latched := false
var target_action := ""
var action_log: Array=[]
var map_view: Control
var location_label: Label
var checkpoint_label: Label
var rail: Node3D
var winch_spindle: Node3D
var panel_lights: Array[MeshInstance3D]=[]
var checkpoint_clock := 0.0
var map_clock := 0.0
var supply_positions={"west":Vector3(-27,0,7),"court":Vector3(22,0,9),"switch":Vector3(25,0,-31)}
var reception=preload("res://scripts/hospital_reception.gd").new()
var evacuation: RefCounted

func _ready() -> void:
	var fresh=false
	for arg in OS.get_cmdline_user_args():
		if arg=="--fresh":fresh=true
		if arg.begins_with("--capture="):capture_dir=arg.trim_prefix("--capture=")
		if arg.begins_with("--save-slot="):
			var slot=arg.trim_prefix("--save-slot=").get_file()
			if slot.begins_with("qa-"):save_path="user://hospital-"+slot
	var fresh_key="hospital_fresh_"+save_path.get_file().replace(".","_").replace("-","_")
	if fresh:
		if get_tree().root.has_meta(fresh_key):fresh=false
		else:get_tree().root.set_meta(fresh_key,true)
	setup_world();build_station();setup_navigation()
	hero=spawn_actor("",DOCK);spawn_encounters();setup_camera();setup_ui()
	if OS.get_cmdline_user_args().has("--hospital-evacuation-preview"):
		evacuation=preload("res://scripts/hospital_evacuation.gd").new(self);evacuation.build()
	if not fresh:load_checkpoint()
	update_objective();update_indicators()
	if not reception.known:say("Лида · рация из убежища\nЯ у окна. Подойди — надо договориться, как выводить людей. Свет здесь пока оставьте.",6)
	elif mission==1:say("Нина · рация\nПуть выставлен. Убежище на резерве. Проверь приём в вагоне и вернись к Лиде. Одного открытого пути мало.",7)
	elif tested:say("Нина · рация\nСхему уже проверили. Осталось перевести привод у стрелки.",5)
	elif winch_stage>0:
		say("Нина · рация\nПродолжим у ручного привода. "+["","Крепление держит — натяни трос.","Трос натянут — сними собачку.","Собачка снята. Обороты: "+str(winch_turns)+" из четырёх.","Остряк дошёл. Зафиксируй замок."][mini(winch_stage,4)],6)
	elif installed:say("Нина · рация\nПеремычка на месте. Соедини обе ветви и проверь схему. Резерв остаётся включён.",6)
	elif has_winch or has_jumper:say("Нина · рация\nИнструмент с тобой. Лебёдка — к стрелке, перемычка — в проверочный щит.",5)
	else:say("Нина · рация\nУбежище и стрелка на одном вводе. Резерв не трогаем. На складе есть перемычка и ручная лебёдка — выбери путь.",8)
	print("HOSPITAL_READY mission=",mission," method=",route_method," save=",save_path)

func setup_world() -> void:
	super.setup_world()
	for node in get_children():
		if node is WorldEnvironment:node.environment.ambient_light_energy=.52;node.environment.fog_density=.002
		if node is DirectionalLight3D:node.light_energy=.62
		if node is ReflectionProbe:node.size=Vector3(90,14,80)

func inside_floor(p: Vector2) -> bool:
	for zone in zones:
		if zone.rect.has_point(p):return true
	return false

func wall(horizontal: bool,line: float,a: float,b: float) -> void:
	if b<=a:return
	block(Vector3((a+b)*.5,1.3,line) if horizontal else Vector3(line,1.3,(a+b)*.5),Vector3(b-a,2.6,.24) if horizontal else Vector3(.24,2.6,b-a),Color("435c54"),true)

func build_station() -> void:
	block(Vector3(5,-.6,0),Vector3(100,.5,100),Color("192c28"))
	for zone in zones:
		var rect: Rect2=zone.rect;var center=rect.get_center()
		var floor_node=block(Vector3(center.x,-.14,center.y),Vector3(rect.size.x,.28,rect.size.y),zone.color,true)
		var shader=ShaderMaterial.new();shader.shader=load("res://shaders/expedition_floor.gdshader");shader.set_shader_parameter("base_color",zone.color);shader.set_shader_parameter("tile_size",1.0 if zone.id in ["store","refuge"] else 0.0);mesh_in(floor_node).material_override=shader
	# Merge outer floor edges. Shared boundaries are real entrances.
	for horizontal in [true,false]:
		var segments={}
		for x in range(-40,48):
			for z in range(-37,36):
				var a=Vector2(x+.5,z-.5) if horizontal else Vector2(x-.5,z+.5)
				if inside_floor(a)==inside_floor(Vector2(x+.5,z+.5)):continue
				var line=z if horizontal else x;var step=x if horizontal else z
				if not segments.has(line):segments[line]=[]
				segments[line].append(step)
		for line in segments:
			var values: Array=segments[line];values.sort();var first=int(values[0]);var previous=first
			for value in values.slice(1)+[9999]:
				if int(value)!=previous+1:wall(horizontal,line,first,previous+1);first=value
				previous=value
	wall(true,-12,-32,-25);wall(true,-12,-21,-8)
	wall(false,-8,-12,-3);wall(false,-8,1,14)
	wall(true,-12,4,14);wall(true,-12,18,28)
	wall(false,28,-12,-5);wall(false,28,-1,8)
	reception.build(self)
	label_world("ПОЕЗД",DOCK+Vector3(0,2,2),.009)
	for p in [Vector3(-28,0,19),Vector3(-29,0,-6),Vector3(-26,0,-32),Vector3(-6,0,-28),Vector3(8,0,5),Vector3(23,0,-18)]:lamp(p)
	for p in [JUMPER,WINCH]:block(p+Vector3(0,.65,-.8),Vector3(2,1.3,.8),Color("6a654c"),true)
	block(JUMPER+Vector3(0,1.36,-.8),Vector3(.6,.1,.18),Color("b8aa73"))
	cylinder(WINCH+Vector3(0,1.5,-.8),.25,.32,Color("9b976f"))
	label_world("ПЕРЕМЫЧКА",JUMPER+Vector3(0,2.1,-.8),.007)
	label_world("РУЧНАЯ ЛЕБЁДКА",WINCH+Vector3(0,2.1,-.8),.007)
	for p in [SOCKET,FEED_A,FEED_B,TEST]:
		block(p+Vector3(0,.8,-.8),Vector3(1.1,1.6,.5),Color("3e5951"),true,.5,.2)
		panel_lights.append(mesh_in(block(p+Vector3(0,1.3,-.51),Vector3(.25,.16,.04),Color("6b6149"))))
	label_world("ПЕРЕМЫЧКА",SOCKET+Vector3(0,2,-.8),.006)
	label_world("ВЕРХНЯЯ ВЕТВЬ",FEED_A+Vector3(0,2,-.8),.006)
	label_world("НИЖНЯЯ ВЕТВЬ",FEED_B+Vector3(0,2,-.8),.006)
	label_world("ПРОВЕРКА СХЕМЫ",TEST+Vector3(0,2,-.8),.006)
	for x in [14.5,15.8]:block(Vector3(x,.04,-26),Vector3(.08,.08,16),Color("829388"),false,.3,.7)
	rail=block(Vector3(16.8,.055,-26),Vector3(.08,.1,11),Color("bfac75"),false,.3,.7)
	block(DRIVE+Vector3(1,.5,0),Vector3(.9,1,.8),Color("54695a"),true)
	winch_spindle=cylinder(DRIVE+Vector3(1,1.1,0),.28,.17,Color("baaa7d"))
	block(Vector3(.24,.14,0),Vector3(.72,.06,.07),Color("c2ae7a"),false,.35,.6,winch_spindle)
	cylinder(Vector3(.57,.26,0),.045,.25,Color("3d4a3b"),winch_spindle)
	label_world("СТРЕЛОЧНЫЙ ПРИВОД",DRIVE+Vector3(0,2.3,0),.008)
	for z in [-10,-6,2,6]:
		block(Vector3(45.82,1.5,z),Vector3(.1,1.4,2.4),Color("b8a672"))
		block(Vector3(45.74,1.5,z),Vector3(.06,1.2,2.2),Color("737c64"))
	label_world("УБЕЖИЩЕ",REFUGE+Vector3(0,2,0),.009)
	for id in supply_positions:
		block(supply_positions[id]+Vector3(0,.4,-.5),Vector3(.6,.8,.4),Color("89947a"),true)
		label_world("ПЕРЕВЯЗКА / РАКЕТА",supply_positions[id]+Vector3(0,1.3,-.5),.005)
	for p in [Vector3(-29,0,3),Vector3(-12,0,-5),Vector3(3,0,8),Vector3(24,0,3),Vector3(9,0,-20)]:crate(p,Vector3(1.4,1.1,1.2))
	for z in [18,29]:bench(Vector3(-29,0,z))
	preload("res://scripts/environment_kit.gd").new(self,4402).hospital()

func setup_navigation() -> void:
	nav.region=Rect2i(-80,-76,180,152);nav.cell_size=Vector2(.5,.5);nav.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES;nav.update()
	for x in range(nav.region.position.x,nav.region.end.x):
		for z in range(nav.region.position.y,nav.region.end.y):
			var p=Vector2(x*.5,z*.5);var solid=false
			for offset in [Vector2(-.4,0),Vector2(.4,0),Vector2(0,-.4),Vector2(0,.4)]:
				if not inside_floor(p+offset):solid=true;break
			if not solid:
				for rect in obstacles:
					if rect.has_point(p):solid=true;break
			if not solid and evacuation and evacuation.transport and not evacuation.transport.attached:
				var local=evacuation.transport.cart.to_local(Vector3(p.x,0,p.y))
				if absf(local.x)<.80 and absf(local.z)<1.4:solid=true
			nav.set_point_solid(Vector2i(x,z),solid)

func spawn_encounters() -> void:
	var definitions=[["walker",Vector3(-25,0,5)],["runner",Vector3(-17,0,-6)],["brute",Vector3(-26,0,-17)],["walker",Vector3(-13,0,-26)],["runner",Vector3(-3,0,-28)],["walker",Vector3(7,0,-29)],["brute",Vector3(20,0,-31)],["walker",Vector3(22,0,-19)],["runner",Vector3(9,0,-4)],["walker",Vector3(20,0,5)],["walker",Vector3(25,0,-8)],["runner",Vector3(3,0,9)]]
	for i in definitions.size():
		var foe=spawn_actor(definitions[i][0],definitions[i][1]);foe.set_meta("id",i)

func setup_ui() -> void:
	super.setup_ui()
	location_label=make_label("Глава 2 · Чужой ток",Vector2(42,110),21,Color("c4c6a8"))
	checkpoint_label=make_label("",Vector2(42,145),18,Color("a0c5b6"))
	map_view=load("res://scripts/hospital_map.gd").new();ui.add_child(map_view);map_view.position=Vector2(1644,32);map_view.size=Vector2(240,238);map_view.game=self
	make_label("БОЛЬНИЧНАЯ ВЕТКА · M",Vector2(1655,39),14,Color("bbc8bb"))

func follow_camera(delta: float) -> void:
	var target=hero.get_global_transform_interpolated().origin+Vector3.UP*.8
	camera.position=camera.position.lerp(target+camera_offset,1-exp(-7*minf(delta,.1)));update_occlusion(delta)

func _unhandled_input(event: InputEvent) -> void:
	if evacuation and evacuation.transport.attached:
		if event is InputEventMouseButton and event.pressed:return
		if event is InputEventKey and (event.keycode in [KEY_SPACE,KEY_Q] or event.physical_keycode in [KEY_SPACE,KEY_Q]):return
	if event is InputEventKey and event.pressed and not event.echo:
		if evacuation and (event.keycode==KEY_G or event.physical_keycode==KEY_G):evacuation.toggle_wait();return
		if event.keycode==KEY_M:map_view.visible=not map_view.visible;return
		if event.keycode==KEY_R:
			if player_down:get_tree().reload_current_scene()
			return
	super._unhandled_input(event)

func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	if paused or player_down:return
	if evacuation:evacuation.tick(delta)
	for foe in enemies:
		if is_instance_valid(foe) and not foe.alive and not killed.has(foe.get_meta("id",-1)):killed.append(foe.get_meta("id",-1))
	rail.rotation.y=move_toward(rail.rotation.y,.21 if mission==1 else 0.0,delta*.35)
	visual_spin=move_toward(visual_spin,winch_turns*TAU,delta*TAU*2)
	winch_spindle.rotation.y=visual_spin
	checkpoint_clock=maxf(0,checkpoint_clock-delta);checkpoint_label.visible=checkpoint_clock>0
	map_clock+=delta
	if map_clock>.2:
		map_clock=0;map_view.queue_redraw()
		for zone in zones:
			if zone.rect.has_point(Vector2(hero.position.x,hero.position.z)):
				location_label.text="Чужой ток · "+zone.name
				if not visited.has(zone.id):visited.append(zone.id)

func options() -> Array:
	var result: Array=[]
	if mission==0:
		if not has_jumper:result.append(["jumper",JUMPER,"Взять целую перемычку"])
		if not has_winch:result.append(["winch",WINCH,"Взять ручную лебёдку"])
		if not installed:result.append(["install",SOCKET,"Установить перемычку" if has_jumper else "Нужна перемычка со склада"])
		if not tested:
			result.append(["feed_a",FEED_A,"Верхняя ветвь · "+("разомкнуть" if feed_a else "соединить")])
			result.append(["feed_b",FEED_B,"Нижняя ветвь · "+("разомкнуть" if feed_b else "соединить")])
			result.append(["test",TEST,"Проверить схему · резерв остаётся включён"])
		var manual=["Закрепить лебёдку","Натянуть трос","Снять собачку","Повернуть механизм","Зафиксировать замок"]
		manual[3]="Повернуть механизм · обороты "+str(winch_turns)+" / 4"
		result.append(["drive" if tested else "manual",DRIVE,"Перевести электрический привод" if tested else manual[mini(winch_stage,4)] if has_winch else "Для ручного пути нужна лебёдка"])
	if (mission==0 or not refuge_heard) and not reception.all_ready():result.append(["refuge",REFUGE,"Связаться с Лидой у убежища"])
	for id in supply_positions:
		if not supplies.has(id):result.append(["supply:"+id,supply_positions[id],"Перевязка и ракета · один раз"])
	result.append_array(reception.options())
	if evacuation:result.append_array(evacuation.options())
	return result

func interactions(delta: float) -> void:
	help.text="";work_bar.visible=false
	if not Input.is_physical_key_pressed(KEY_E):e_latched=false
	var candidate="";var prompt="";var nearest=1.65
	for option in options():
		var distance=hero.position.distance_to(option[1])
		if distance<nearest:nearest=distance;candidate=option[0];prompt=option[2]
	if candidate=="":work=0;target_action="";return
	help.text="E · "+prompt
	if not Input.is_physical_key_pressed(KEY_E) or e_latched or hero.ground_speed>.15 or hero.attack_left>0 or hero.dash_left>0 or hero.stun>0:work=0;return
	if target_action!=candidate:target_action=candidate;work=0
	work+=delta;work_bar.visible=true;work_bar.value=work/.65*100
	if work>=.65:work=0;e_latched=true;perform_action(candidate)

func perform_action(action: String) -> void:
	var changed=false
	match action:
		"jumper":
			if mission==0 and not has_jumper:has_jumper=true;changed=true;say("Артём\nЦелая. Ставлю в проверочный щит. Работающий резерв не трогаю.",4)
		"winch":
			if mission==0 and not has_winch:has_winch=true;changed=true;say("Нина · рация\nРучной привод у стрелки. Сначала закрепи лебёдку, потом натягивай.",4)
		"install":
			if mission==0 and has_jumper and not installed:installed=true;work_branch="power";changed=true
			elif not has_jumper:say("Артём\nБез целой перемычки разрыв остаётся разрывом.",3)
		"feed_a","feed_b":
			if mission==0 and not tested:
				if action=="feed_a":feed_a=not feed_a
				else:feed_b=not feed_b
				changed=true
		"test":
			if mission==0 and not tested:
				work_branch="power"
				if installed and feed_a and feed_b:tested=true;changed=true;say("Нина · рация\nОбе ветви замкнуты. Проверка прошла. Теперь отдельно переведи привод у стрелки.",5)
				else:say("Нина · рация\n"+("Не установлена перемычка." if not installed else "Нужны обе ветви.")+" Резерв работает, убежище не отключалось.",4)
		"drive":
			if mission==0 and tested:complete_route("power");changed=true
		"manual":
			if mission==0 and has_winch:
				work_branch="winch"
				if winch_stage==3:
					winch_turns+=1
					if winch_turns==4:winch_stage=4
				else:winch_stage+=1
				changed=true
				if winch_stage==5:complete_route("winch")
				else:
					say("Артём\nОборот "+str(winch_turns)+" из четырёх." if winch_stage==3 and winch_turns>0 else ["","Нина · рация\nКрепление держит. Натягивай.","Нина · рация\nТрос натянут. Теперь собачка.","Артём\nСобачка снята. Можно вращать.","Артём\nОстряк дошёл. Остался замок."][winch_stage],3,0)
					sound("impactMetal_light_000",DRIVE,-20)
			elif not has_winch:say("Артём\nРучная лебёдка на складе. Руками привод не удержать.",3)
		"refuge":
			changed=not reception.known or mission==1 and not refuge_heard
			reception.known=true
			if mission==1:refuge_heard=true
			say("Лида · рация из убежища\nЗдесь четверо. Михаил остался в вагоне. Резерв работает. Сначала готовьте путь и приём — я остаюсь с людьми.",7)
	if action.begins_with("supply:"):
		var id=action.trim_prefix("supply:")
		if supply_positions.has(id) and not supplies.has(id):supplies.append(id);hero.health=minf(100,hero.health+45);flares=mini(3,flares+1);changed=true
	if action.begins_with("receive_"):changed=reception.perform(action)
	if action.begins_with("evac_") and evacuation:changed=evacuation.perform(action)
	action_log.append({"action":action,"changed":changed,"seconds":clock,"mission":mission,"reserve_on":reserve_on,"winch_stage":winch_stage})
	update_objective();update_indicators()
	if changed:save_checkpoint()

func complete_route(method: String) -> void:
	mission=1;route_method=method;refuge_heard=false
	for foe in enemies:
		if is_instance_valid(foe) and foe.alive and foe.position.distance_to(DRIVE)<14:foe.home=DRIVE
	say("Нина · рация\nСтрелка зафиксирована. Убежище на резерве.\nЛида: Хорошо. Но людей пока не выводим — приём ещё надо подготовить.",7)

func objective_position() -> Vector3:
	if evacuation and reception.ready_confirmed:return evacuation.objective_position()
	if mission==1:return reception.target()
	if not reception.known and not has_jumper and not has_winch:return REFUGE
	if tested or work_branch=="winch" and has_winch:return DRIVE
	if installed:return FEED_A if not feed_a else FEED_B if not feed_b else TEST
	return SOCKET if has_jumper else DRIVE if has_winch else JUMPER

func update_objective() -> void:
	if evacuation and reception.ready_confirmed:objective.text=evacuation.objective()
	elif mission==1:objective.text=reception.objective()
	elif not reception.known and not has_jumper and not has_winch:objective.text="Подойти к убежищу · договориться с Лидой о выходе людей"
	elif tested:objective.text="Проверка прошла · перевести привод у стрелки"
	elif has_winch and (work_branch=="winch" or not has_jumper):objective.text="Ручной путь: "+["закрепить лебёдку","натянуть трос","снять собачку","повернуть механизм","зафиксировать замок"][mini(winch_stage,4)]
	elif installed:objective.text="Соединить обе ветви и проверить изолированную схему"
	elif has_jumper:objective.text="Установить перемычку в проверочный щит"
	else:objective.text="Восстановить стрелку: перемычка или ручная лебёдка на складе"

func update_indicators() -> void:
	var states=[installed,feed_a,feed_b,tested]
	for i in panel_lights.size():panel_lights[i].material_override=mat(Color("9ac299") if states[i] else Color("6b6149"))

func save_checkpoint() -> void:
	var data={"version":1,"mission":mission,"has_jumper":has_jumper,"has_winch":has_winch,"installed":installed,"feed_a":feed_a,"feed_b":feed_b,"tested":tested,"winch_stage":winch_stage,"winch_turns":winch_turns,"route_method":route_method,"refuge_heard":refuge_heard,"hero":[hero.position.x,hero.position.y,hero.position.z],"health":hero.health,"flares":flares,"killed":killed,"supplies":supplies,"visited":visited}
	data["work_branch"]=work_branch
	data["reception"]=reception.save()
	if evacuation:
		data["evacuation"]=evacuation.save()
		if evacuation.first_active() and evacuation.anchor.has("hero"):data["hero"]=evacuation.anchor.hero
	var file=FileAccess.open(save_path,FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(data));file.close()
	checkpoint_label.text="Контрольная точка · действие сохранено";checkpoint_clock=3

func load_checkpoint() -> void:
	if not FileAccess.file_exists(save_path):return
	var data=JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if not data is Dictionary or data.get("version",0)!=1:return
	mission=int(data.get("mission",0));has_jumper=data.get("has_jumper",false);has_winch=data.get("has_winch",false);installed=data.get("installed",false);feed_a=data.get("feed_a",false);feed_b=data.get("feed_b",false);tested=data.get("tested",false);winch_stage=clampi(int(data.get("winch_stage",0)),0,5);route_method=data.get("route_method","");refuge_heard=data.get("refuge_heard",false)
	winch_turns=clampi(int(data.get("winch_turns",4 if winch_stage>=4 else 0)),0,4);visual_spin=winch_turns*TAU
	work_branch=data.get("work_branch","power" if installed else "winch" if winch_stage>0 else "")
	var receiving_data=data.get("reception",{})
	reception.restore(receiving_data if receiving_data is Dictionary else {})
	var p=data.get("hero",[DOCK.x,DOCK.y,DOCK.z]);hero.position=Vector3(p[0],p[1],p[2]);hero.health=clampf(data.get("health",100),1,100);flares=int(data.get("flares",3));hero.reset_physics_interpolation()
	killed=data.get("killed",[]);supplies=data.get("supplies",[]);visited=data.get("visited",[])
	for i in killed.size():killed[i]=int(killed[i])
	for foe in enemies:
		if killed.has(foe.get_meta("id",-1)):foe.alive=false;foe.queue_free()
	if evacuation:evacuation.restore(data.get("evacuation",{}))
	if mission==1:rail.rotation.y=.21

func movement_speed() -> float:
	var speed=super.movement_speed()
	if evacuation and evacuation.stage=="first_received":
		if evacuation.transport.attached:return minf(speed,2.2)
		if evacuation.transport.state=="awaiting":return minf(speed,2.5)
	return minf(speed,2.2) if evacuation and evacuation.stage=="leading" and not evacuation.manual_wait and not evacuation.danger_wait else speed

func try_dodge() -> void:
	if evacuation and evacuation.transport.attached:return
	super.try_dodge()
