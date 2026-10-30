extends RefCounted
## Candidate-only staging behind --hospital-evacuation-preview. Final art unapproved.
const FRIEND=preload("res://scripts/escort_actor.gd")
const FIRST=["raisa","neighbour_a","neighbour_b"]
const DOOR=Vector3(-33.0,0,24.5)
const SEAT_Z={"raisa":22.0,"neighbour_a":19.5,"neighbour_b":27.0}
var game: Node3D
var people: Dictionary={}
var stage:="waiting"
var boarded: Array=[]
var manual_wait:=false
var danger_wait:=false
var trail: Array[Vector3]=[]
var anchor: Dictionary={}
var boarding_id:=""
var progress_clock:=0.0
var patient: Node3D
var name_labels: Dictionary={}
var transport: RefCounted

func _init(owner: Node3D) -> void:game=owner
func build() -> void:
	var definitions={"nina":[1.70,Vector3(37,0,-.8)],"lida":[1.65,Vector3(42,0,-4.8)],"raisa":[1.61,Vector3(34,0,-7)],"neighbour_a":[1.75,Vector3(37,0,-6)],"neighbour_b":[1.72,Vector3(40,0,-4)]}
	for id in definitions:
		var actor=FRIEND.new();game.add_child(actor);var entry=definitions[id]
		var path="res://review_assets/companions-v047/"+id+".glb" if id in ["nina","lida","raisa"] else "res://assets/characters/patient.glb"
		actor.setup(id,path,entry[0],0.0 if id in ["nina","lida","raisa"] else 4.805)
		actor.position=entry[1];actor.reset_physics_interpolation();people[id]=actor
		var label=game.label_world({"nina":"НИНА","lida":"ЛИДА","raisa":"РАИСА","neighbour_a":"СОСЕД","neighbour_b":"СОСЕД"}[id],Vector3.UP*(entry[0]+.2),.005)
		game.world_labels.erase(label);label.reparent(actor,false);name_labels[id]=label
	# Fourth resident is kept separate from Mikhail, awaiting the second journey.
	patient=load("res://assets/characters/patient.glb").instantiate();game.add_child(patient);patient.name="FourthHospitalResident";patient.scale=Vector3.ONE*(1.73/4.805);patient.position=Vector3(43,1.04,-5.85);patient.rotation.x=-PI*.5
	var anim=game.hero_animation(patient)
	if anim:
		for clip in anim.get_animation_list():
			if clip.ends_with("Man_Idle"):anim.play(clip);anim.advance(0);anim.pause()
	var apparatus=game.block(Vector3(44.1,.7,-6.7),Vector3(.45,.6,.4),Color("879786"))
	var cable=Node3D.new();game.add_child(cable)
	game.tube(Vector3(44.0,.8,-6.5),Vector3(43.4,.9,-6.4),.018,Color("8a9b94")).reparent(cable)
	transport=preload("res://scripts/hospital_patient_transport.gd").new(self);transport.build(apparatus,cable)
	game.make_label("ПРОБА ПОСТАНОВКИ · 3D-ОБРАЗЫ ЕЩЁ НЕ УТВЕРЖДЕНЫ",Vector2(42,185),17,Color("c6b593"))
	game.hero.collision_mask|=8
	for foe in game.enemies:foe.collision_mask|=8
	capture_anchor()

func actor_state() -> Dictionary:
	var result={}
	for id in people:
		var actor=people[id];result[id]={"position":vec(actor.position),"yaw":actor.rotation.y,"seated":actor.seated}
	return result
func vec(v: Vector3) -> Array:return [v.x,v.y,v.z]
func from_vec(v: Array) -> Vector3:return Vector3(v[0],v[1],v[2])
func foes_state() -> Array:
	var result=[]
	for foe in game.enemies:
		if is_instance_valid(foe) and foe.alive:result.append({"id":foe.get_meta("id",-1),"position":vec(foe.position),"home":vec(foe.home),"health":foe.health})
	return result
func capture_anchor() -> void:
	anchor={"hero":vec(game.hero.position),"people":actor_state(),"foes":foes_state()}
	if transport:anchor["transport"]=transport.snapshot()
func first_active() -> bool:return stage in ["leading","boarding","first_received"]
func danger_near(point: Vector3,radius:=6.0) -> bool:
	for foe in game.enemies:
		if is_instance_valid(foe) and foe.alive and foe.stun<=0 and foe.position.distance_to(point)<radius and game.visible_between(point,foe.position):return true
	return false
func safe_to_checkpoint() -> bool:
	if stage=="first_received":return transport.safe_here()
	var refuge=Rect2(29,-11,16,18);var train=Rect2(-39,14,31,20)
	var in_refuge=true;var in_train=true
	for id in FIRST+["nina"]:
		var pos=people[id].position;in_refuge=in_refuge and refuge.has_point(Vector2(pos.x,pos.z));in_train=in_train and train.has_point(Vector2(pos.x,pos.z))
		if danger_near(pos,8):return false
	var hero=Vector2(game.hero.position.x,game.hero.position.z)
	return in_refuge and refuge.has_point(hero) or in_train and train.has_point(hero)
func target_back(distance: float) -> Vector3:
	var previous=game.hero.position;var left=distance
	for i in range(trail.size()-1,-1,-1):
		var span=previous.distance_to(trail[i])
		if span>=left:return previous.lerp(trail[i],left/maxf(.001,span))
		left-=span;previous=trail[i]
	return previous
func go(actor: EscortActor,target: Vector3,speed: float,delta: float) -> void:
	actor.repath-=delta
	if actor.repath<=0 or actor.last_target.distance_to(target)>.8:actor.path=game.route(actor.position,target);actor.repath=.3;actor.last_target=target
	while not actor.path.is_empty() and actor.position.distance_to(actor.path[0])<.32:actor.path.remove_at(0)
	var direction=(actor.path[0]-actor.position).normalized() if not actor.path.is_empty() and actor.position.distance_to(target)>.45 else Vector3.ZERO
	actor.move_direction(direction,speed,delta)
func tick(delta: float) -> void:
	for id in name_labels:name_labels[id].visible=people[id].position.distance_to(game.hero.position)<6
	if stage=="first_received":
		if trail.is_empty() or game.hero.position.distance_to(trail[-1])>.3:trail.append(game.hero.position)
		if trail.size()>400:trail.remove_at(0)
	if stage=="leading":
		if trail.is_empty() or game.hero.position.distance_to(trail[-1])>.3:trail.append(game.hero.position)
		if trail.size()>400:trail.remove_at(0)
		danger_wait=danger_near(game.hero.position)
		for id in FIRST:
			if not boarded.has(id) and danger_near(people[id].position):danger_wait=true
		var party=["nina"]+FIRST
		for i in range(party.size()):
			var actor=people[party[i]]
			if manual_wait or danger_wait or actor.position.distance_to(game.hero.position)>7:actor.move_direction(Vector3.ZERO,0,delta)
			else:go(actor,target_back(1.2+i*.85),2.5,delta)
	elif stage=="boarding":
		for id in FIRST:
			var actor=people[id]
			if boarded.has(id):actor.move_direction(Vector3.ZERO,0,delta);continue
			if boarding_id=="":boarding_id=id
			if id!=boarding_id:actor.move_direction(Vector3.ZERO,0,delta);continue
			var approach=Vector3(-37.0,0,SEAT_Z[id])
			if actor.seating_left>0:actor.advance_pose(delta)
			elif actor.position.distance_to(approach)>.55:go(actor,approach,1.8,delta)
			else:
				var root=Vector3(-38.25,0,SEAT_Z[id])-Basis(Vector3.UP,PI/2)*actor.sit_offset;root.y=0
				actor.begin_sitting(root,PI/2,board_person.bind(id))
		go(people.nina,Vector3(-31,0,27),2.2,delta)
	elif stage=="first_received":
		for id in FIRST:people[id].move_direction(Vector3.ZERO,0,delta)
		transport.tick(delta)
	else:
		for id in people:people[id].move_direction(Vector3.ZERO,0,delta)
	for id in people:
		var actor=people[id]
		if actor.footfall:
			game.sound("footstep_concrete_00"+str(randi_range(0,4)),actor.position,-30)
			game.emit_noise(actor.position,2.5 if actor.ground_speed<1.9 else 4.0,2)
	if first_active():
		progress_clock+=delta
		if progress_clock>.5:
			progress_clock=0
			if safe_to_checkpoint():capture_anchor()
	game.update_objective()
func board_person(id: String) -> void:
	if boarded.has(id):return
	boarded.append(id);boarding_id="";capture_anchor()
	if boarded.size()==3:
		stage="first_received";game.say("Лида · из убежища\nТрое на месте. Я остаюсь с четвёртым. Возвращайтесь за нами.",5)
	game.action_log.append({"action":"evac_board:"+id,"changed":true,"seconds":game.clock,"people_received":boarded.size()})
	game.save_checkpoint()
func options() -> Array:
	if not game.reception.ready_confirmed:return []
	if stage=="first_received":return transport.options()
	if stage=="waiting":return [["evac_first",game.REFUGE,"Начать выход первой группы · G — остановить / продолжить"]]
	if stage=="leading" and game.hero.position.distance_to(DOOR)<4:return [["evac_board",DOOR,"Помочь троим пройти в вагон"]]
	return []
func perform(action: String) -> bool:
	if stage=="first_received":return transport.perform(action)
	if action=="evac_first" and stage=="waiting" and game.reception.ready_confirmed:
		if danger_near(game.REFUGE):game.say("Лида\nВ проходе Путевой. Люди подождут здесь.",3);return false
		stage="leading";manual_wait=false;trail.assign([game.hero.position]);capture_anchor();return true
	if action=="evac_board" and stage=="leading":
		for id in FIRST:
			if people[id].position.distance_to(DOOR)>5:game.say("Нина\nДождись людей у двери.",3);return false
		if danger_near(DOOR):return false
		stage="boarding";manual_wait=false;return true
	return false
func toggle_wait() -> void:
	if stage!="leading" and not (stage=="first_received" and transport.loaded and not transport.received):return
	manual_wait=not manual_wait;game.save_checkpoint()
func objective_position() -> Vector3:
	if stage=="first_received":return transport.objective_position()
	if stage=="leading":
		for id in FIRST:
			if people[id].position.distance_to(game.hero.position)>6.5:return people[id].position
		return DOOR
	return DOOR if stage=="boarding" else game.REFUGE
func objective() -> String:
	if stage=="first_received":return transport.objective()
	if stage=="waiting":return "Приём готов · вывести первую группу из убежища"
	if stage=="leading":return "Группа ждёт · G — продолжить" if manual_wait else "Освободить проход · люди ждут" if danger_wait else "Провести людей к вагону · G — остановить группу"
	if stage=="boarding":return "Освободить дверной проход для людей" if game.hero.position.distance_to(DOOR)<1.5 else "Посадка первой группы · принято "+str(boarded.size())+" / 3"
	return "Трое в вагоне · вернуться к Лиде и четвёртому человеку"
func save() -> Dictionary:return {"stage":stage,"boarded":boarded,"anchor":anchor,"manual_wait":manual_wait}
func restore(data: Dictionary) -> void:
	stage=data.get("stage","waiting")
	if stage not in ["waiting","leading","boarding","first_received"]:stage="waiting"
	boarded=[]
	for id in data.get("boarded",[]):
		if FIRST.has(id) and not boarded.has(id):boarded.append(id)
	anchor=data.get("anchor",anchor);boarding_id="";manual_wait=stage=="leading";trail.clear()
	for id in people:
		var info=anchor.get("people",{}).get(id,{})
		if info.has("position"):people[id].position=from_vec(info.position)
		if boarded.has(id):
			var point=Vector3(-38.25,0,SEAT_Z[id])-Basis(Vector3.UP,PI/2)*people[id].sit_offset;point.y=0;people[id].sit_at(point,PI/2)
		people[id].reset_physics_interpolation()
	for foe in game.enemies:
		for saved in anchor.get("foes",[]):
			if is_instance_valid(foe) and saved.id==foe.get_meta("id",-1):foe.position=from_vec(saved.position);foe.home=from_vec(saved.home);foe.health=saved.health;foe.reset_physics_interpolation()
	transport.restore(anchor.get("transport",{}))
