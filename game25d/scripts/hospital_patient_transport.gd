extends RefCounted
## Optional evacuation staging. The fourth resident, Mikhail and the first three
## keep separate identities. Transport completion follows physical arrival.
const LOAD_POINT=Vector3(41.5,0,-6.7)
const PARK=Vector3(-36.2,0,24.0)
const TALK=Vector3(-36.2,0,26.5)
var evacuation_ref: WeakRef
var evac: RefCounted:
	get:return evacuation_ref.get_ref()
var game: Node3D
var cart: CharacterBody3D
var wheels: Array=[]
var cart_path: Array[Vector3]=[]
var state:="awaiting"
var attached:=false
var loaded:=false
var received:=false
var bag_taken:=false
var truth:=""
var lift_left:=0.0
var lift_from:=Vector3.ZERO
var lift_to:=Vector3.ZERO
var apparatus: Node3D
var cable: Node3D
var carry_rig=preload("res://scripts/carry_ik.gd").new()
var question: Control

func _init(owner: RefCounted) -> void:evacuation_ref=weakref(owner);game=owner.game
func build(source: Node3D,source_cable: Node3D) -> void:
	apparatus=source;cable=source_cable
	cart=CharacterBody3D.new();game.add_child(cart);cart.name="FourthResidentStretcher";cart.position=Vector3(42.5,0,-.5)
	cart.collision_layer=16;cart.collision_mask=1|8;cart.floor_snap_length=.3
	var collision=CollisionShape3D.new();cart.add_child(collision);collision.name="CartShape"
	var box=BoxShape3D.new();box.size=Vector3(.82,1.0,2.05);collision.shape=box;collision.position.y=.5
	game.block(Vector3(0,.78,0),Vector3(.72,.12,2.05),Color("778b73"),false,.85,0,cart)
	game.block(Vector3(0,.85,-.72),Vector3(.55,.08,.35),Color("b1b097"),false,.9,0,cart)
	for x in [-.4,.4]:
		game.block(Vector3(x,.7,0),Vector3(.04,.04,2.55),Color("98a79a"),false,.3,.7,cart)
		for end in [-1.55,1.55]:
			game.block(Vector3(x,.7,end*.9),Vector3(.04,.04,.4),Color("98a79a"),false,.3,.7,cart)
			game.block(Vector3(x,.87,end),Vector3(.035,.36,.035),Color("98a79a"),false,.3,.7,cart)
			game.block(Vector3(x,1.06,end),Vector3(.07,.07,.26),Color("34483d"),false,.8,0,cart)
		for z in [-.77,.77]:
			game.block(Vector3(x,.44,z),Vector3(.04,.55,.04),Color("879b91"),false,.4,.6,cart)
			var wheel=game.cylinder(Vector3(x,.13,z),.13,.07,Color("243531"),cart);wheel.rotation.z=PI*.5;wheels.append(wheel)
	game.hero.collision_mask|=16
	for id in evac.people:evac.people[id].collision_mask|=16
	question=load("res://scripts/hospital_truth_panel.gd").new(self);game.ui.add_child(question)
	game.setup_navigation()

func active() -> bool:return evac.stage=="first_received" and not received
func handle() -> Vector3:
	var a=cart.to_global(Vector3(0,0,1.55));var b=cart.to_global(Vector3(0,0,-1.55))
	return a if a.distance_to(game.hero.position)<b.distance_to(game.hero.position) else b
func footprint_inside() -> bool:
	for x in [-.43,.43]:
		for z in [-1.58,1.58]:
			var p=cart.to_global(Vector3(x,0,z))
			if not Rect2(-38.8,15.2,3.6,17.6).has_point(Vector2(p.x,p.z)):return false
	return true
func companions_near(point: Vector3,radius: float) -> bool:
	return evac.people.nina.position.distance_to(point)<radius and evac.people.lida.position.distance_to(point)<radius
func safe_here() -> bool:
	var region=Rect2(29,-11,16,18) if cart.position.x>28 else Rect2(-39,14,31,20)
	for p in [game.hero.position,cart.position,evac.people.nina.position,evac.people.lida.position]:
		if not region.has_point(Vector2(p.x,p.z)) or evac.danger_near(p,8):return false
	return lift_left<=0
func options() -> Array:
	if evac.stage!="first_received":return []
	if received:
		return [["evac_truth",TALK,"Поговорить с Ниной в вагоне"]] if truth=="" else [["evac_depart",TALK,"Отправиться к лесному полустанку"]]
	var result: Array=[]
	if state=="awaiting":return [["evac_last_plan",game.REFUGE,"Вернуться с Ниной за последним человеком"]]
	if lift_left>0:return []
	var at_bedside=not loaded and cart.position.distance_to(LOAD_POINT)<1.1
	if at_bedside and not attached:result.append(["evac_last_load",handle(),"Помочь Лиде и Нине переложить человека на носилки"])
	if loaded and not bag_taken:result.append(["evac_last_bag",game.reception.BAG,"Взять подготовленную сумку Лиды"])
	if loaded and cart.position.distance_to(PARK)<3:result.append(["evac_last_receive",PARK,"Принять последние носилки в вагон"])
	if attached or not at_bedside:result.append(["evac_cart",game.hero.position if attached else handle(),"Оставить носилки · освободить руки" if attached else "Взяться за ручки носилок"])
	return result
func perform(action: String) -> bool:
	if evac.stage!="first_received":return false
	match action:
		"evac_last_plan":
			if state!="awaiting" or game.hero.position.distance_to(game.REFUGE)>2:return false
			if not companions_near(game.REFUGE,6):game.say("Лида\nДождёмся Нины. Перенесём вместе.",3);return false
			state="bedside";evac.capture_anchor()
			game.say("Лида\nПодай пустые носилки к этой койке. Переложим вместе. Аппарат поедет рядом, сумку возьмём перед выходом.",6);return true
		"evac_cart":
			if received or state=="awaiting" or lift_left>0:return false
			if not attached and (game.hero.position.distance_to(handle())>1.65 or game.hero.attack_left>0 or game.hero.dash_left>0):return false
			attached=not attached;cart_path.clear()
			if attached:cart_path.append(game.hero.position)
			game.setup_navigation()
			if safe_here():evac.capture_anchor()
			return true
		"evac_last_load":
			if loaded or lift_left>0 or cart.position.distance_to(LOAD_POINT)>1.1 or not companions_near(LOAD_POINT,5) or evac.danger_near(LOAD_POINT):return false
			attached=false;cart_path.clear();lift_left=2.2;lift_from=evac.patient.global_position;lift_to=cart.to_global(Vector3(0,1.04,.84))
			game.setup_navigation()
			evac.people.nina.begin_interaction(2.2);evac.people.lida.begin_interaction(2.2)
			game.say("Лида\nНа счёт три. Не торопимся.",3);return false
		"evac_last_bag":
			if not loaded or bag_taken or game.hero.position.distance_to(game.reception.BAG)>1.65:return false
			if evac.people.lida.position.distance_to(game.reception.BAG)>2.2:game.say("Артём\nДождусь Лиды у сумки.",3);return false
			bag_taken=true;game.reception.bag.reparent(evac.people.lida,true)
			var tween=game.create_tween();tween.tween_property(game.reception.bag,"position",Vector3(.28,.75,.1),.45)
			game.say("Лида\nСумка у меня. Можно идти.",3)
			if safe_here():evac.capture_anchor()
			return true
		"evac_last_receive":
			if not loaded or received or not footprint_inside() or not bag_taken:return false
			if not companions_near(PARK,6) or evac.danger_near(PARK):game.say("Артём\nДождусь Лиды и Нины у носилок.",3);return false
			attached=false;received=true;state="received";game.setup_navigation();evac.capture_anchor()
			game.say("Лида\nВсе четверо здесь. Михаил на своём месте. Сумка рядом, ввод доступен. Теперь можно поговорить.",6);return true
		"evac_truth":
			if received and truth=="" and game.hero.position.distance_to(TALK)<1.65 and not evac.danger_near(TALK):question.open();return false
		"evac_depart":
			if not received or truth=="" or question.visible or game.hero.position.distance_to(TALK)>=1.65:return false
			var campaign=preload("res://scripts/campaign.gd")
			var result=campaign.mark_hospital_departure(truth)
			if result!=OK:game.say("Не удалось сохранить отправление: "+error_string(result),5);return false
			game.save_checkpoint();game.get_tree().root.set_meta("campaign_playing",true)
			game.get_tree().change_scene_to_file.call_deferred(campaign.FOREST);return false
	return false
func choose(value: String) -> void:
	if not received or truth!="" or value not in ["admit","defend"]:return
	truth=value
	var reply="Артём: Я видел платформу. И не остановился.\nНина: Ты говорил маме, что там никого не было.\nАртём: Да.\nНина: Я хочу послушать запись целиком. Когда сможешь говорить дальше — скажи." if value=="admit" else "Артём: Я боялся, что состав смоет. Что все, кто уже внутри…\nНина: Ты видел тех, кто снаружи?\nАртём: Видел. И не остановился.\nНина: Тогда начни с этого. А потом расскажешь, чего боялся."
	game.dialogue_book.add(reply,game.dialogue_scope());question.show_reply(reply);evac.capture_anchor();game.save_checkpoint()
	game.action_log.append({"action":"hospital_truth:"+value,"changed":true,"seconds":game.clock})
func tick(delta: float) -> void:
	if evac.stage!="first_received":return
	if received:
		evac.go(evac.people.nina,Vector3(-36.2,0,27.5),1.8,delta);evac.go(evac.people.lida,Vector3(-36.2,0,22),1.8,delta);return
	if state=="awaiting":
		evac.go(evac.people.nina,evac.target_back(1.4),2.8,delta);evac.people.lida.move_direction(Vector3.ZERO,0,delta)
	elif not loaded:
		evac.go(evac.people.nina,Vector3(40.5,0,-3.5),2.3,delta);evac.people.lida.move_direction(Vector3.ZERO,0,delta)
	elif not bag_taken:
		evac.go(evac.people.lida,game.reception.BAG+Vector3(.65,0,.3),2.0,delta);evac.people.nina.move_direction(Vector3.ZERO,0,delta)
	else:
		var danger=evac.danger_near(cart.position) or evac.danger_near(game.hero.position)
		if danger or evac.manual_wait:
			for id in ["nina","lida"]:evac.people[id].move_direction(Vector3.ZERO,0,delta)
		elif cart.position.distance_to(PARK)<9:
			# Keep the doorway and both stretcher handles accessible while Artem
			# turns the cart. Following his old trail packs everyone into the door.
			evac.go(evac.people.nina,Vector3(-32,0,22.0),2.5,delta)
			evac.go(evac.people.lida,Vector3(-32,0,27.0),2.5,delta)
		else:
			evac.go(evac.people.nina,evac.target_back(3.6),2.5,delta);evac.go(evac.people.lida,evac.target_back(4.6),2.5,delta)
	if lift_left>0:
		lift_left=maxf(0,lift_left-delta);var t=smoothstep(0.0,1.0,1-lift_left/2.2)
		evac.patient.global_position=lift_from.lerp(lift_to,t)+Vector3.UP*sin(t*PI)*.18
		if lift_left<=0:
			loaded=true;state="loaded";evac.patient.reparent(cart,true);evac.patient.position=Vector3(0,1.04,.84);evac.patient.rotation=Vector3(-PI*.5,0,0)
			apparatus.reparent(cart,true);apparatus.position=Vector3(.51,.85,-.65);cable.reparent(cart,true);cable.position=Vector3.ZERO
			# Cable stays with its apparatus and patient; no remaining connection to the bed.
			for child in cable.get_children():child.queue_free()
			game.tube(Vector3(.51,.9,-.65),Vector3(.22,1.0,.15),.018,Color("8a9b94")).reparent(cable,false)
			evac.capture_anchor();game.action_log.append({"action":"evac_fourth_loaded","changed":true,"seconds":game.clock});game.save_checkpoint()
	update_cart(delta);carry_rig.apply(game.hero,cart,attached,delta)
func update_cart(delta: float) -> void:
	if attached:
		if cart.position.distance_to(game.hero.position)>3.6:
			attached=false;cart_path.clear();game.setup_navigation();game.say("Артём\nНосилки зацепились. Освобожу проход и возьмусь снова.",3);return
		if cart_path.is_empty() or cart_path[-1].distance_to(game.hero.position)>.25:cart_path.append(game.hero.position)
		while cart_path.size()>1 and cart.position.distance_to(cart_path[0])<.28:cart_path.remove_at(0)
		var direction=Vector3.ZERO;var separation=cart.position.distance_to(game.hero.position)
		if not cart_path.is_empty() and separation>1.35:
			var lead=(game.hero.position-cart.position).normalized();var forward=maxf(0,Vector3(game.hero.velocity.x,0,game.hero.velocity.z).dot(lead))
			direction=(cart_path[0]-cart.position).normalized()*clampf(forward+(separation-1.7)*7,0,5.5)
		var before=cart.position;cart.velocity=Vector3(direction.x,-1,direction.z);cart.move_and_slide()
		var lead=game.hero.position-cart.position;lead.y=0
		if lead.length()>.2:
			var angle=atan2(lead.x,lead.z)
			if lead.dot(cart.basis.z)<0:angle+=PI
			var yaw=rotate_toward(cart.rotation.y,angle,delta*4)
			var query=PhysicsShapeQueryParameters3D.new();query.shape=cart.get_node("CartShape").shape;query.collision_mask=1;query.exclude=[cart.get_rid()]
			query.transform=Transform3D(Basis(Vector3.UP,yaw),cart.position+Vector3.UP*.55)
			if game.get_world_3d().direct_space_state.intersect_shape(query,1).is_empty():cart.rotation.y=yaw
		for wheel in wheels:wheel.rotation.y+=cart.position.distance_to(before)/.13
	else:cart.velocity=Vector3(0,-1,0);cart.move_and_slide()
func objective_position() -> Vector3:
	if received:return TALK
	if state=="awaiting":return game.REFUGE
	if not loaded:return LOAD_POINT if attached else handle()
	if not bag_taken:return game.reception.BAG
	return PARK
func objective() -> String:
	if received:return "Путь проверен, все в вагоне · отправиться к лесному полустанку" if truth!="" else "Все четверо в вагоне · поговорить с Ниной"
	if state=="awaiting":return "Трое в вагоне · вернуться с Ниной к Лиде"
	if lift_left>0:return "Перекладываем четвёртого человека · Лида и Нина рядом"
	if not loaded:return "Подать пустые носилки к четвёртой койке"
	if not bag_taken:return "Человек и аппарат готовы · взять сумку Лиды перед выходом"
	return "Доставить последние носилки в вагон · E — отпустить, G — остановить спутников"
func snapshot() -> Dictionary:
	return {"state":state,"loaded":loaded,"received":received,"bag_taken":bag_taken,"truth":truth,"cart":evac.vec(cart.position),"yaw":cart.rotation.y}
func restore(data: Dictionary) -> void:
	state=data.get("state","awaiting");loaded=bool(data.get("loaded",false));received=bool(data.get("received",false));bag_taken=bool(data.get("bag_taken",false));truth=data.get("truth","")
	attached=false;lift_left=0;cart_path.clear();cart.position=evac.from_vec(data.get("cart",[42.5,0,-.5]));cart.rotation.y=data.get("yaw",0.0);cart.reset_physics_interpolation()
	if loaded:
		evac.patient.reparent(cart,true);evac.patient.position=Vector3(0,1.04,.84);evac.patient.rotation=Vector3(-PI*.5,0,0)
		apparatus.reparent(cart,true);apparatus.position=Vector3(.51,.85,-.65);cable.reparent(cart,true);cable.position=Vector3.ZERO
		for child in cable.get_children():child.queue_free()
		game.tube(Vector3(.51,.9,-.65),Vector3(.22,1.0,.15),.018,Color("8a9b94")).reparent(cable,false)
	if bag_taken:game.reception.bag.reparent(evac.people.lida,true);game.reception.bag.position=Vector3(.28,.75,.1)
	game.setup_navigation()
