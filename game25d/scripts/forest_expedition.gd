extends "res://scripts/environment_trial.gd"
## Authored route choice. The train, signal and two approaches have distinct
## persistent consequences; this standalone stop does not skip campaign chapters.
const GENERATOR=Vector3(0,0,9)
const BELL=Vector3(-13,0,6)
const CACHE=Vector3(23,0,15)
const NOTE=Vector3(-21,0,-18)
var has_handle:=false
var powered:=false
var signal_set:=false
var cache_taken:=false
var note_read:=false
var completed:=false
var chosen_route:=""
var action_target:=""
var bell_cooldown:=0.0
var motor_clock:=0.0
var save_path:="user://forest-v048.json"
var motor_light: OmniLight3D
var route_label: Label
var map_view: Control
var map_large:=false
var save_error:=""
var action_log: Array=[]
var signal_arm: Node3D
var signal_lens: StandardMaterial3D

func _ready() -> void:
	landscape="forest"
	var campaign_mode=bool(get_tree().root.get_meta("campaign_playing",false))
	if campaign_mode:save_path="user://forest-campaign-v048.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--save-slot="):
			var slot=arg.trim_prefix("--save-slot=").get_file()
			if slot.begins_with("qa-"):save_path="user://forest-"+("campaign-" if campaign_mode else "")+slot
		if arg.begins_with("--capture="):capture_dir=arg.trim_prefix("--capture=")
	kit=preload("res://scripts/environment_kit.gd").new(self,4803)
	goals.assign([Vector3(-17,0,-17),Vector3(19,0,-16),start_point])
	setup_world();build_station();setup_navigation()
	hero=spawn_actor("",start_point)
	# Each group guards an approach; there is no kill-all completion condition.
	for encounter in [["walker",Vector3(-11,0,-9)],["walker",Vector3(-3,0,-18)],["runner",Vector3(7,0,-6)],["brute",Vector3(16,0,-9)],["walker",Vector3(20,0,9)]]:
		spawn_actor(encounter[0],encounter[1])
	setup_camera();setup_ui();load_checkpoint();apply_world();update_task()
	say("Нина · рация\nУ поста два привода. Рукоять в будке позволит обойтись без мотора. Электрический откроет ближнюю калитку, но его услышат Путевые. На посту в любом случае проверь и зафиксируй сигнал.",9)
	print("FOREST_EXPEDITION_READY route=",chosen_route," saved=",save_path)

func setup_world() -> void:
	super.setup_world()
	for node in get_children():
		if node is WorldEnvironment:node.environment.ambient_light_energy=.40
		if node is DirectionalLight3D:node.light_energy=.52

func build_station() -> void:
	super.build_station()
	# Visible equipment at the actual interaction points, rather than labels alone.
	block(NOTE+Vector3(0,.68,-.8),Vector3(1.0,.08,.6),Color("8b8061"),true)
	for x in [-.4,.4]:block(NOTE+Vector3(x,.34,-.8),Vector3(.06,.68,.48),Color("52614d"))
	block(NOTE+Vector3(0,.735,-.8),Vector3(.43,.025,.32),Color("d6c8a4"))
	label_world("СМЕННЫЙ ЖУРНАЛ",NOTE+Vector3(0,1.5,-.8),.005)
	tube(goals[0]+Vector3(-.35,1.23,-.9),goals[0]+Vector3(.3,1.23,-.9),.035,Color("c8b280"))
	tube(goals[0]+Vector3(.3,1.23,-.9),goals[0]+Vector3(.3,1.46,-.9),.045,Color("6e785e"))
	var mast=goals[1]+Vector3(1.5,0,-1.2)
	cylinder(mast+Vector3.UP*2.2,.10,4.4,Color("536859"))
	signal_arm=Node3D.new();add_child(signal_arm);signal_arm.position=mast+Vector3.UP*3.9
	block(Vector3(.65,0,0),Vector3(1.5,.25,.12),Color("bdaf8c"),false,.8,0,signal_arm)
	block(Vector3(1.15,0,.07),Vector3(.24,.25,.02),Color("a66f53"),false,.8,0,signal_arm)
	var lens=mesh_in(block(mast+Vector3(0,3.2,.1),Vector3(.28,.36,.13),Color("bc7259")))
	signal_lens=mat(Color("bc7259")).duplicate();signal_lens.emission_enabled=true;lens.material_override=signal_lens

func build_forest() -> void:
	super.build_forest()
	# Berms break sight lines, framing the service path and an optional eastern loop.
	for p in [Vector3(-10,0,0),Vector3(-10,0,-14),Vector3(12,0,6)]:
		kit.stone(p,Vector3(4.5,1.9,2.5),Color("65715c"),true)
	kit.path_strip(start_point,BELL,2.7,Color("737257"))
	kit.path_strip(BELL,GENERATOR,3,Color("737257"))
	kit.path_strip(GENERATOR,Vector3(0,0,-7),3,Color("737257"))
	kit.path_strip(Vector3(15,0,8),CACHE,2.5,Color("737257"))
	block(GENERATOR+Vector3(1.5,.7,0),Vector3(1.5,1.4,1.2),Color("6c7155"),true)
	for z in [-.4,-.2,0,.2,.4]:block(GENERATOR+Vector3(1.5,1.1,z),Vector3(1.2,.035,.04),Color("3b4a3e"))
	cylinder(GENERATOR+Vector3(1.7,1.9,-.3),.1,1.1,Color("465548"))
	label_world("МОТОР · ШУМНЫЙ КОРОТКИЙ ПУТЬ",GENERATOR+Vector3(0,2.3,0),.006)
	motor_light=OmniLight3D.new();add_child(motor_light);motor_light.position=GENERATOR+Vector3(1.4,1.7,0);motor_light.light_color=Color("dda55f");motor_light.omni_range=3
	for x in [-.6,.6]:block(BELL+Vector3(x,1.1,-1),Vector3(.08,2.2,.08),Color("65705a"))
	block(BELL+Vector3(0,2.2,-1),Vector3(1.4,.12,.12),Color("65705a"))
	cylinder(BELL+Vector3(0,1.8,-1),.25,.35,Color("a79768"))
	label_world("ПУТЕВОЙ КОЛОКОЛ",BELL+Vector3(0,2.7,-1),.006)
	block(CACHE+Vector3(0,.45,-.8),Vector3(1.1,.9,.65),Color("64735c"),true)
	block(CACHE+Vector3(0,.92,-.8),Vector3(.8,.04,.5),Color("baaf86"))
	label_world("ЗАПАС ПУТЕЙЦА",CACHE+Vector3(0,1.7,-.8),.006)
	label_world("БУДКА ←   ПРИВОД →",Vector3(-17,2,9),.007)

func setup_ui() -> void:
	super.setup_ui()
	landmark.text="ЛЕСНОЙ ПОЛУСТАНОК"
	route_label=make_label("",Vector2(42,151),19,Color("b5bea2"))
	map_view=load("res://scripts/forest_map.gd").new();map_view.game=self;ui.add_child(map_view)
	map_view.position=Vector2(1585,28);map_view.size=Vector2(305,280);map_view.mouse_filter=Control.MOUSE_FILTER_IGNORE

func update_task() -> void:
	if not is_instance_valid(objective):return
	objective.text="Вернуться к составу · выходной сигнал открыт" if signal_set else "Вернуть выходной сигнал на лесном посту"
	if completed:objective.text="Лесной полустанок пройден · путь для состава готов"
	route_label.text="Ручная рукоять: будка на западе  •  Мотор: ближняя просека  •  M — схема"
	if has_handle and not signal_set:route_label.text="Рукоять с собой · пост за северной просекой · можно пройти без мотора"
	if powered:route_label.text="Мотор слышен на просеке · ближняя калитка открыта · пост на северо-востоке"
	if signal_set:route_label.text="Сигнал зафиксирован · возвращайся через центральную калитку"
	if completed:route_label.text="F2 — остановки · R — повторить вылазку"
	if save_error!="":route_label.text=save_error

func options() -> Array:
	if completed:return []
	var result: Array=[]
	if not has_handle and not signal_set:result.append(["handle",goals[0],"Взять ручную рукоять · тихий обход"])
	if not signal_set:
		if not powered:result.append(["power",GENERATOR,"Запустить мотор · откроет калитку, привлечёт Путевых"])
		result.append(["signal",goals[1],"Проверить и зафиксировать сигнал" if has_handle or powered else "Нужна рукоять из будки или работающий мотор"])
	else:
		result.append(["return",start_point,"Подтвердить путь у состава · завершить вылазку"])
		if powered:result.append(["stop_motor",GENERATOR,"Заглушить мотор · сигнал уже зафиксирован"])
	if bell_cooldown<=0:result.append(["bell",BELL,"Ударить в колокол · отвлечь к будке"])
	if not cache_taken:result.append(["cache",CACHE,"Забрать запас · перевязка и две ракеты"])
	if not note_read:result.append(["note",NOTE,"Прочитать сменный журнал путейца"])
	return result

func interactions(delta: float) -> void:
	bell_cooldown=maxf(0,bell_cooldown-delta);motor_clock-=delta
	if powered and motor_clock<=0:
		motor_clock=1.8;emit_noise(GENERATOR,29,3.5);sound("impactMetal_heavy_002",GENERATOR,-27)
	if trial_open:trial_gate.position.y=move_toward(trial_gate.position.y,3.5,delta*2)
	signal_arm.rotation.z=move_toward(signal_arm.rotation.z,-PI/4 if signal_set else 0,delta)
	help.text="";work_bar.visible=false;map_view.queue_redraw()
	if not Input.is_physical_key_pressed(KEY_E):input_latched=false
	var nearest=1.65;var candidate="";var caption=""
	for option in options():
		var distance=hero.position.distance_to(option[1])
		if distance<nearest:nearest=distance;candidate=option[0];caption=option[2]
	if candidate=="":work=0;action_target="";return
	help.text="E · "+caption
	if input_latched or not Input.is_physical_key_pressed(KEY_E) or hero.ground_speed>.15 or hero.attack_left>0 or hero.dash_left>0 or hero.stun>0:work=0;return
	if candidate!=action_target:action_target=candidate;work=0
	work+=delta;work_bar.visible=true;work_bar.value=work/.65*100
	if work>=.65:
		work=0;input_latched=true
		if perform(candidate):
			action_log.append({"action":candidate,"seconds":clock});apply_world();save_checkpoint();update_task()

func perform(action: String) -> bool:
	match action:
		"handle":
			if has_handle or signal_set:return false
			has_handle=true;say("Артём\nРукоять целая. Пройду вдоль северной ограды и переведу сигнал вручную.",5)
		"power":
			if powered or signal_set:return false
			powered=true;motor_clock=0;say("Нина · рация\nКалитка поднялась. Мотор собирает их на просеке — не задерживайся возле него.",5)
		"signal":
			if signal_set:return false
			if not has_handle and not powered:say("Артём\nБез рукояти или мотора привод не сдвинуть. Будка на западе, мотор у ближней просеки.",5);return false
			signal_set=true;chosen_route="power" if powered else "manual"
			say("Артём\nСигнал открыт. Защёлка держит. Назад через калитку — больше не надо обходить весь лес.",5)
		"bell":
			if bell_cooldown>0:return false
			bell_cooldown=7;emit_noise(BELL,30,6);sound("impactMetal_medium_003",BELL,-11)
			say("Колокол слышен с просеки. Путевые ищут источник, если уже не видят тебя.",4);return false
		"cache":
			if cache_taken:return false
			cache_taken=true;hero.health=minf(100,hero.health+30);flares=mini(5,flares+2)
			say("Запас путейца: перевязка и две сигнальные ракеты. Коробка теперь пуста.",4)
		"note":
			if note_read:return false
			note_read=true;say("Сменный журнал\n«Ручную рукоять оставил в будке. Запас справа за просекой. После проверки фиксируйте защёлку: мотор можно заглушить». На полях — список покупок к следующей смене.",8)
		"stop_motor":
			if not powered or not signal_set:return false
			powered=false;say("Артём\nМотор выключен. Сигнал держится на защёлке.",4)
		"return":
			if not signal_set or completed:return false
			completed=true;say("Нина · рация\nВижу открытый сигнал. Путь проверен. Возвращайся в кабину.",5)
		_:return false
	return true

func apply_world() -> void:
	trial_open=powered or signal_set
	trial_gate_shape.set_deferred("disabled",trial_open)
	if trial_open:obstacles.erase(trial_gate_rect)
	elif not obstacles.has(trial_gate_rect):obstacles.append(trial_gate_rect)
	refresh_nav()
	signal_light.light_color=Color("8db39a") if signal_set else Color("c97c4b")
	signal_lens.albedo_color=Color("8db39a") if signal_set else Color("bc7259");signal_lens.emission=signal_lens.albedo_color
	motor_light.light_energy=1.8 if powered else .1
	mission=3 if completed else 2 if signal_set else 1 if has_handle or powered else 0

func save_checkpoint() -> void:
	var actors: Array=[]
	for foe in enemies:
		if not is_instance_valid(foe):actors.append({"alive":false});continue
		actors.append({"alive":foe.alive,"health":foe.health,"position":[foe.position.x,foe.position.z]})
	var data={"version":1,"handle":has_handle,"powered":powered,"signal":signal_set,"cache":cache_taken,"note":note_read,"completed":completed,"route":chosen_route,"hero":[hero.position.x,hero.position.z],"health":hero.health,"flares":flares,"enemies":actors}
	var file=FileAccess.open(save_path,FileAccess.WRITE)
	if not file:save_error="Не удалось сохранить вылазку · "+error_string(FileAccess.get_open_error());return
	file.store_string(JSON.stringify(data));file.close()

func load_checkpoint() -> void:
	if not FileAccess.file_exists(save_path):return
	var data=JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if not data is Dictionary or data.get("version",0)!=1:return
	if not data.get("hero") is Array or data.hero.size()!=2:return
	var restored_position=Vector3(float(data.hero[0]),0,float(data.hero[1]))
	if not bounds.grow(-.4).has_point(Vector2(restored_position.x,restored_position.z)):return
	has_handle=data.get("handle",false);powered=data.get("powered",false);signal_set=data.get("signal",false);cache_taken=data.get("cache",false);note_read=data.get("note",false)
	completed=data.get("completed",false) and signal_set;chosen_route=data.get("route","")
	hero.position=restored_position;hero.health=clampf(float(data.get("health",100)),1,100);flares=clampi(int(data.get("flares",3)),0,5);hero.reset_physics_interpolation()
	var actors=data.get("enemies",[])
	for i in mini(actors.size(),enemies.size()):
		var saved=actors[i];var foe=enemies[i]
		if not saved.get("alive",true):foe.alive=false;foe.collision_layer=0;foe.hide()
		else:
			foe.health=clampf(float(saved.get("health",foe.health)),1,foe.health)
			if saved.get("position") is Array and saved.position.size()==2:foe.position=Vector3(float(saved.position[0]),0,float(saved.position[1]));foe.reset_physics_interpolation()
	if powered or signal_set:trial_gate.position.y=3.5

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode==KEY_M:
			map_large=not map_large;map_view.position=Vector2(475,170) if map_large else Vector2(1585,28);map_view.size=Vector2(970,750) if map_large else Vector2(305,280);map_view.queue_redraw();return
		if event.keycode==KEY_R:
			if completed:DirAccess.remove_absolute(save_path)
			if completed or player_down:get_tree().reload_current_scene()
			return
	super._unhandled_input(event)
