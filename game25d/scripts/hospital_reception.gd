extends RefCounted
## Physical receiving preparations. Does not claim passenger boarding.
const INPUT=Vector3(-37.2,0,18)
const AISLE=Vector3(-36.4,0,24.5)
const BAG=Vector3(37,0,1)
const PASSAGE=Vector3(27,0,-3.8)
var game: Node3D
var known:=false
var input_checked:=false
var aisle_clear:=false
var bag_ready:=false
var path_clear:=false
var ready_confirmed:=false
var busy:=false
var bag: Node3D
var luggage: Node3D
var cable: Node3D
var screen: Node3D
var input_lamp: MeshInstance3D
var screen_rect: Rect2
var luggage_rect: Rect2
var suitcase_pose=Vector3(-37.1,.3,24.4)
var screen_pose=Vector3(28,.85,-1.9)

func build(owner: Node3D) -> void:
	game=owner
	# Actual wagon floor and a three metre open doorway join the platform. No teleport.
	for z in [16,20,29,32]:game.block(Vector3(-34.96,1.8,z),Vector3(.06,.75,1.7),Color("bca978"))
	game.block(Vector3(-38,.38,29.5),Vector3(.86,.76,2.3),Color("5e7567"),true)
	game.block(Vector3(-38,.8,29.5),Vector3(.88,.08,2.32),Color("b1aa87"))
	var mikhail=load("res://assets/characters/patient.glb").instantiate();game.add_child(mikhail)
	mikhail.name="MikhailInWagon";mikhail.scale=Vector3.ONE*(1.75/4.805);mikhail.position=Vector3(-38,1.04,30.35);mikhail.rotation.x=-PI*.5
	var animation=game.hero_animation(mikhail)
	if animation:
		for clip in animation.get_animation_list():
			if clip.ends_with("Man_Idle"):animation.play(clip);animation.advance(0);animation.pause()
	game.label_world("МИХАИЛ",Vector3(-38,1.8,29.5),.005)
	game.block(Vector3(-38.1,.8,18),Vector3(.35,1.6,1.0),Color("405b53"),true)
	input_lamp=game.mesh_in(game.block(Vector3(-37.9,1.24,18),Vector3(.05,.18,.2),Color("a68e56")))
	game.label_world("ШТАТНЫЙ ВВОД",INPUT+Vector3(0,1.8,0),.005)
	game.block(Vector3(-38.1,.42,21),Vector3(.65,.84,2.0),Color("636f5d"),true)
	luggage=game.block(suitcase_pose,Vector3(.5,.6,1.0),Color("6b5848"),true)
	luggage_rect=game.obstacles[-1]
	cable=Node3D.new();game.add_child(cable)
	game.tube(Vector3(-35,.04,24.7),Vector3(-37.7,.04,24.7),.026,Color("a89256")).reparent(cable)
	game.label_world("ПРОХОД В ВАГОН",AISLE+Vector3(0,1.8,0),.005)
	game.block(BAG+Vector3(0,.35,.85),Vector3(1.1,.7,.7),Color("657466"),true)
	bag=Node3D.new();game.add_child(bag);bag.position=BAG+Vector3(0,.7,.85)
	game.block(Vector3(0,.2,0),Vector3(.65,.4,.38),Color("5c6d52"),false,.96,0,bag)
	game.tube(Vector3(-.2,.4,0),Vector3(-.12,.59,0),.025,Color("303e31")).reparent(bag,false)
	game.tube(Vector3(-.12,.59,0),Vector3(.12,.59,0),.025,Color("303e31")).reparent(bag,false)
	game.tube(Vector3(.12,.59,0),Vector3(.2,.4,0),.025,Color("303e31")).reparent(bag,false)
	game.label_world("СУМКА ЛИДЫ",BAG+Vector3(0,1.7,.85),.005)
	screen=game.block(screen_pose,Vector3(.45,1.7,1.6),Color("7a806c"),true)
	screen_rect=game.obstacles[-1]
	game.label_world("ШИРОКИЙ ПРОХОД",PASSAGE+Vector3(0,1.8,0),.005)
	for z in [19.5,22,27]:
		game.block(Vector3(-38.4,.23,z),Vector3(.7,.46,1.25),Color("68745e"),true)
		game.block(Vector3(-38.72,.85,z),Vector3(.15,.78,1.25),Color("566854"))
	game.block(Vector3(-38.72,1.9,24),Vector3(.35,.08,16.5),Color("92917a"))
	for z in [22,30]:warm_light(Vector3(-38.85,2.2,z),Vector3.RIGHT)
	for z in [16,20,29,32]:
		game.block(Vector3(-35.12,1.7,z),Vector3(.04,.68,1.55),Color("8b9e8e"),false,.35)
	for z in [17.5,31.5]:
		var wheel=game.cylinder(Vector3(-34.95,-.25,z),.4,.2,Color("304139"));wheel.rotation.z=PI*.5
	game.block(Vector3(-35.02,2.65,24),Vector3(.12,.16,18.2),Color("bac0aa"))
	build_refuge()

func warm_light(point: Vector3,normal:=Vector3.BACK) -> void:
	var light=OmniLight3D.new();game.add_child(light);light.position=point+normal*.35;light.light_color=Color("ffd5a0");light.light_energy=2.4;light.omni_range=6;light.shadow_enabled=true;light.light_size=.3
	var housing=game.block(point,Vector3(.6,.25,.14),Color("c7b88c"));housing.rotation.y=atan2(normal.x,normal.z)
	var fixture=game.mesh_in(housing)
	var material=game.mat(Color("c7b88c")).duplicate();material.emission_enabled=true;material.emission=Color("ddbf85");material.emission_energy_multiplier=.8;fixture.material_override=material

func build_refuge() -> void:
	# The former registration area is occupied by four current residents. These
	# are environment props, not a substitute for their future visible actors.
	for point in [Vector3(34,0,-9.2),Vector3(37.1,0,-9.2),Vector3(40.2,0,-9.2),Vector3(43,0,-6.7)]:
		game.block(point+Vector3.UP*.38,Vector3(.95,.76,2.2),Color("687467"),true,.7,.2)
		game.block(point+Vector3.UP*.8,Vector3(.97,.1,2.23),Color("b1b097"))
		game.block(point+Vector3(0,.88,-.72),Vector3(.65,.1,.4),Color("c1bfa5"))
		game.block(point+Vector3(0,.87,.25),Vector3(.94,.08,1.3),Color("737b63"))
		game.block(point+Vector3(.68,.25,-.45),Vector3(.3,.5,.4),Color("6f6450"),true)
	game.block(Vector3(44.4,.85,5),Vector3(1.0,1.7,.65),Color("82907b"),true)
	game.block(Vector3(43.86,.9,5),Vector3(.03,.35,.08),Color("b6b89e"))
	game.block(Vector3(34.3,.43,4.6),Vector3(1.5,.86,.8),Color("716d57"),true)
	game.block(Vector3(34.1,.88,4.5),Vector3(.35,.015,.25),Color("c7c0a1"))
	game.block(Vector3(34.55,.9,4.5),Vector3(.13,.05,.2),Color("555d4b"))
	for z in [-8.7,-4.7]:game.cylinder(Vector3(44.8,1.1,z),.027,2.2,Color("91a294"))
	game.tube(Vector3(44.8,2.2,-8.7),Vector3(44.8,2.2,-4.7),.025,Color("91a294"))
	game.block(Vector3(44.8,1.25,-7.6),Vector3(.035,1.8,2.1),Color("8d9a82"))
	warm_light(Vector3(35,2.2,-11.8));warm_light(Vector3(45.85,2.2,1),Vector3.LEFT)

func options() -> Array:
	if not known or busy:return []
	var result: Array=[]
	if not input_checked:result.append(["receive_input",INPUT,"Проверить штатный ввод с Ниной"])
	if not aisle_clear:result.append(["receive_aisle",AISLE,"Спросить Михаила и освободить проход"])
	if not bag_ready:result.append(["receive_bag",BAG,"Подготовить сумку с Лидой"])
	if not path_clear:result.append(["receive_passage",PASSAGE,"Убрать ширму с широкого прохода"])
	if all_ready() and not ready_confirmed:result.append(["receive_confirm",game.REFUGE,"Подтвердить готовность выхода"])
	return result

func receiving_ready() -> bool:return input_checked and aisle_clear
func all_ready() -> bool:return game.mission==1 and known and receiving_ready() and bag_ready and path_clear
func target() -> Vector3:
	if not known:return game.REFUGE
	if not input_checked:return INPUT
	if not aisle_clear:return AISLE
	if not bag_ready:return BAG
	if not path_clear:return PASSAGE
	return game.REFUGE
func objective() -> String:
	if not known:return "Стрелка восстановлена · связаться с Лидой у убежища"
	if not input_checked:return "Подготовить приём · проверить штатный ввод в вагоне"
	if not aisle_clear:return "Освободить проход в вагоне · место Михаила не трогать"
	if not bag_ready:return "Подготовить с Лидой сумку · оставить её у людей"
	if not path_clear:return "Освободить широкий проход от убежища к поезду"
	return "Путь и приём готовы · люди ждут у убежища" if ready_confirmed else "Вернуться к Лиде · подтвердить готовность выхода"

func perform(action: String) -> bool:
	if busy or not known:return false
	match action:
		"receive_input":
			if input_checked:return false
			input_checked=true
			game.say("Нина · рация\nШтатный ввод проверен. Переносной источник остаётся у Лиды рядом с человеком. Нам ещё нужен свободный проход.",6)
		"receive_aisle":
			if aisle_clear:return false
			busy=true
			game.say("Михаил\nМоя сумка. Под сиденье, ручками сюда. Там телефон.\nАртём: Ваше место оставим как есть.",5)
			var tween=game.create_tween();tween.tween_property(luggage,"position",Vector3(-38,.22,30.6),.45)
			tween.tween_callback(complete_aisle);return false
		"receive_bag":
			if bag_ready:return false
			bag_ready=true
			game.say("Лида · рация из убежища\nСумку проверила. Когда скажу — возьмёшь. Пока не уноси: вдруг что понадобится до выхода. Исторический список в неё не клади.",6)
		"receive_passage":
			if path_clear:return false
			busy=true
			var tween=game.create_tween();tween.tween_property(screen,"scale:z",.18,.4)
			tween.tween_callback(complete_passage);return false
		"receive_confirm":
			if ready_confirmed or not all_ready():return false
			ready_confirmed=true;game.refuge_heard=true
			game.say("Лида · рация из убежища\nПуть проверен, место готово. Сумка здесь. Переносной источник я проверила сама. Рядом с человеком остаюсь я.",6)
		_:return false
	apply_visuals();return true

func complete_aisle() -> void:
	aisle_clear=true;busy=false;apply_visuals();commit("receive_aisle")
func complete_passage() -> void:
	path_clear=true;busy=false;apply_visuals();commit("receive_passage")
func commit(action: String) -> void:
	game.action_log.append({"action":action,"changed":true,"seconds":game.clock,"mission":game.mission,"preparation":true})
	game.update_objective();game.save_checkpoint()
func clear_collision(node: Node3D,rect: Rect2) -> void:
	game.obstacles.erase(rect)
	for child in node.get_children():
		if child is StaticBody3D:
			for shape in child.get_children():
				if shape is CollisionShape3D:shape.set_deferred("disabled",true)
func apply_visuals() -> void:
	input_lamp.material_override=game.mat(Color("a3be8b") if input_checked else Color("a68e56"))
	if aisle_clear:
		luggage.position=Vector3(-38,.22,30.6);cable.position=Vector3(-.7,0,-2.7);clear_collision(luggage,luggage_rect)
	if path_clear:screen.scale.z=.18;clear_collision(screen,screen_rect)
	bag.rotation.y=.18 if bag_ready else 0.0
	game.setup_navigation()
func save() -> Dictionary:
	return {"known":known,"input_checked":input_checked,"aisle_clear":aisle_clear,"bag_ready":bag_ready,"path_clear":path_clear,"ready_confirmed":ready_confirmed}
func restore(data: Dictionary) -> void:
	known=bool(data.get("known",game.refuge_heard));input_checked=bool(data.get("input_checked",false));aisle_clear=bool(data.get("aisle_clear",false));bag_ready=bool(data.get("bag_ready",false));path_clear=bool(data.get("path_clear",false));ready_confirmed=bool(data.get("ready_confirmed",false));busy=false
	apply_visuals()
