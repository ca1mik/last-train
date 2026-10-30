extends RefCounted
## Playable exit operation. Staged mechanism; companions are still radio-only.
const ISOLATOR=Vector3(2,0,38)
const DRIVE=Vector3(24,0,36)
const LOCK=Vector3(24,0,40)
const BELL=Vector3(1,0,27)
var game: Node3D
var stage := 0
var bell_left := 0.0
var bell_cooldown := 0.0
var debris: Node3D
var lever: Node3D
var indicator: MeshInstance3D
var door: Node3D

func build(owner: Node3D) -> void:
	game=owner
	# Two entrances, both physically closed until the rescue has finished.
	game.wall_x(-12,22,30);game.wall_x(-12,34,44)
	game.wall_z(22,-12,17);game.wall_z(22,21,30)
	game.make_gate("exit_west",Vector3(-12,0,32),4,true,false)
	game.make_gate("exit_north",Vector3(19,0,22),4,false,false)
	# Cover divides an upper and a lower route, with wide cross-connections.
	game.block(Vector3(8,1.0,33),Vector3(10,2.0,2.0),Color("455e56"),true)
	game.block(Vector3(20,.7,28),Vector3(2.0,1.4,3),Color("71684e"),true)
	game.block(ISOLATOR+Vector3(0,.8,-.8),Vector3(1.1,1.6,.5),Color("626c53"),true)
	game.label_world("ОТКЛЮЧЕНИЕ ПРИВОДА",ISOLATOR+Vector3(0,2,-.7),.007)
	indicator=game.cylinder(ISOLATOR+Vector3(0,1.65,-.8),.1,.12,Color("dba75b"))
	game.block(DRIVE+Vector3(0,.3,-1.2),Vector3(2,.6,1.8),Color("3b514b"),true)
	lever=Node3D.new();game.add_child(lever);lever.position=DRIVE+Vector3(0,.6,-1)
	game.block(Vector3(0,.65,0),Vector3(.1,1.3,.1),Color("b7aa80"),false,.4,.5,lever)
	game.block(Vector3(0,1.28,0),Vector3(.6,.12,.12),Color("605c46"),false,.8,0,lever)
	debris=game.block(DRIVE+Vector3(0,.46,-.25),Vector3(2.6,.18,.5),Color("8d7757"))
	debris.rotation.y=.35
	game.label_world("ВЫХОДНОЙ ПРИВОД",DRIVE+Vector3(0,2.3,-.8),.008)
	game.block(LOCK+Vector3(0,.4,0),Vector3(.5,.8,.5),Color("67796a"),true)
	game.label_world("ЗАМОК / ПРОВЕРКА",LOCK+Vector3(0,1.5,0),.006)
	game.block(BELL+Vector3(0,.7,-.8),Vector3(.12,1.4,.12),Color("768474"),true)
	game.cylinder(BELL+Vector3(0,1.45,-.8),.22,.25,Color("b3a16b"))
	game.label_world("СИГНАЛЬНЫЙ ЗВОНОК",BELL+Vector3(0,2,-.8),.006)
	door=game.block(Vector3(-36.75,1.5,30),Vector3(.15,2.0,1.5),Color("7d947d"))
	for p in [Vector3(-7,0,28),Vector3(4,0,41),Vector3(26,0,25),Vector3(26,0,41)]:game.lamp(p)

func restore(value: int) -> void:
	stage=clampi(value,0,6)
	game.set_gate("exit_west",stage>0,true);game.set_gate("exit_north",stage>0,true)
	debris.visible=stage<3;lever.rotation.z=-.9 if stage>=4 else .35
	door.position.z=31.7 if stage>=6 else 30.0
	game.mesh_in(indicator).material_override=game.mat(Color("637462") if stage>=2 else Color("dba75b"))

func options() -> Array:
	if game.mission!=3:return []
	match stage:
		0:return [["exit_begin",game.DOCK,"Подготовить выход состава · Михаил остаётся в вагоне"]]
		1:return [["exit_isolate",ISOLATOR,"Обесточить заевший привод"],["exit_bell",BELL,"Позвонить · отвлечь Путевых"]]
		2:return [["exit_clear",DRIVE,"Освободить тягу обесточенного привода"],["exit_bell",BELL,"Позвонить · отвлечь Путевых"]]
		3:return [["exit_throw",DRIVE,"Перевести привод вручную"],["exit_bell",BELL,"Позвонить · отвлечь Путевых"]]
		4:return [["exit_lock",LOCK,"Зафиксировать и проверить положение"],["exit_bell",BELL,"Позвонить · отвлечь Путевых"]]
		5:return [["lida_door",game.DOCK,"Открыть пассажирскую дверь Лиде вручную"],["exit_bell",BELL,"Позвонить · отвлечь Путевых"]]
	return [["depart",game.DOCK,"Отправиться на больничную ветку"]]

func objective_position() -> Vector3:
	return [game.DOCK,ISOLATOR,DRIVE,DRIVE,LOCK,game.DOCK,game.DOCK][stage]

func objective_text() -> String:
	return ["Михаил в вагоне · подготовить выход состава у поезда",
		"Выход состава · обесточить заевший привод",
		"Выход состава · освободить тягу",
		"Выход состава · перевести ручной привод",
		"Выход состава · зафиксировать и проверить положение",
		"Вернуться и открыть пассажирскую дверь Лиде",
		"Люди в вагоне · можно отправляться"][stage]

func intro() -> String:
	return ["Лида · рация\nМихаил в вагоне. Я рядом. Но выход состава ещё не готов.",
		"Нина · рация\nВыходной привод заклинило. Отключение в нижнем дворе, тяга у восточной стены. Начни с отключения.",
		"Артём\nПривод обесточен. Теперь можно освободить тягу.",
		"Нина · рация\nТяга свободна. Переведи привод, потом проверь замок отдельно.",
		"Нина · рация\nПоложение изменилось. Осталась фиксация у дальней стойки.",
		"Лида · рация\nВы тогда тоже это сказали. Через громкоговоритель.\nАртём: Я открою дверь сам.",
		"Лида · рация\nДо следующей — довезите.\nНина: Люди в вагоне. Можно отправляться."][stage]

func perform(action: String) -> bool:
	if game.mission!=3:return false
	if action=="exit_bell":
		if stage>0 and bell_cooldown<=0 and game.hero.position.distance_to(BELL)<1.65:
			bell_left=8;bell_cooldown=4
			game.sound("impactMetal_light_001",BELL,-12)
			game.say("Артём\nИдут на звон. Есть проход с другой стороны.",3)
		return true
	var expected=["exit_begin","exit_isolate","exit_clear","exit_throw","exit_lock","lida_door"]
	if stage>=6 or action!=expected[stage]:return false
	# Checks also apply to direct calls: no remote mechanism or skipped stages.
	if game.hero.position.distance_to(objective_position())>=1.65:return false
	stage+=1
	if stage==1:
		game.set_gate("exit_west",true);game.set_gate("exit_north",true)
	if stage==2:indicator.material_override=game.mat(Color("637462"))
	if stage==3:debris.visible=false
	game.update_objective();game.say(intro(),7)
	game.save_checkpoint(["","Выходной двор открыт","Привод обесточен","Тяга освобождена","Привод переведён","Выход закреплён","Лида в вагоне"][stage])
	return true

func tick(delta: float) -> void:
	bell_left=maxf(0,bell_left-delta);bell_cooldown=maxf(0,bell_cooldown-delta)
	lever.rotation.z=move_toward(lever.rotation.z,-.9 if stage>=4 else .35,delta*1.8)
	door.position.z=move_toward(door.position.z,31.7 if stage>=6 else 30.0,delta*1.4)

func enemy_tick(foe: RailActor,delta: float) -> bool:
	if not foe.has_meta("exit_yard"):return false
	if stage==0:
		foe.move_ground(Vector3.ZERO,0,delta);return true
	if bell_left<=0 or foe.phase in ["windup","strike","charge","recover"] or foe.stun>0:return false
	if foe.position.distance_to(game.hero.position)<2.8 and game.visible_between(foe.position,game.hero.position) or foe.position.distance_to(BELL)>28:return false
	foe.repath-=delta
	if foe.repath<=0:foe.path=game.route(foe.position,BELL);foe.repath=.4
	while not foe.path.is_empty() and foe.position.distance_to(foe.path[0])<.35:foe.path.remove_at(0)
	var direction=(foe.path[0]-foe.position).normalized() if not foe.path.is_empty() else Vector3.ZERO
	foe.move_ground(direction,2.9 if foe.enemy_kind=="runner" else 1.65 if foe.enemy_kind=="brute" else 2.2,delta)
	return true
