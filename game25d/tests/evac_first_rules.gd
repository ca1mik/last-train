extends SceneTree
var game: Node3D
var checks:=0
var failures: Array=[]
var output:="H:/game/release/evacuation-v047/rules.json"
func _initialize() -> void:start.call_deferred()
func check(ok: bool,message: String) -> void:
	checks+=1
	if not ok:failures.append(message);push_error(message)
func frames(n: int) -> void:
	for i in range(n):await physics_frame
func build() -> void:
	game=load("res://hospital.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true;await frames(3)
func discard() -> void:
	game.set_paused(false);game.queue_free();await frames(3)
func start() -> void:
	DirAccess.make_dir_recursive_absolute(output.get_base_dir());await build()
	check(game.evacuation!=null,"candidate preview explicitly enables staging")
	check(game.evacuation.people.size()==5,"Nina/Lida/three first-group residents have distinct actors")
	check(game.get_node_or_null("MikhailInWagon")!=null and game.get_node_or_null("FourthHospitalResident")!=null,"Mikhail and fourth resident remain distinct from first group")
	game.perform_action("evac_first");check(game.evacuation.stage=="waiting","cannot begin evacuation before receiving preparation")
	game.reception.known=true;game.reception.input_checked=true;game.reception.aisle_clear=true;game.reception.bag_ready=true;game.reception.path_clear=true;game.complete_route("power");game.perform_action("receive_confirm")
	game.hero.position=game.REFUGE;game.hero.reset_physics_interpolation();game.perform_action("evac_first")
	check(game.evacuation.stage=="leading" and game.evacuation.boarded.is_empty(),"starting group does not mark passengers received")
	var before={}
	for id in game.evacuation.people:before[id]=game.evacuation.people[id].position
	game.perform_action("evac_board");check(game.evacuation.stage=="leading" and game.evacuation.boarded.is_empty(),"boarding is rejected while group remains away from train")
	game.evacuation.toggle_wait();check(game.evacuation.manual_wait,"G command can hold group without a timer")
	game.evacuation.tick(.016)
	check(game.evacuation.people.raisa.position.distance_to(before.raisa)<.01,"held group stays physically at its position")
	game.evacuation.toggle_wait()
	# The boarding fixture stages a group at the real door; the complete input
	# route is a separate test. No kill-all flag is used by the boarding rule.
	for actor in game.enemies:actor.queue_free()
	game.enemies.clear();await frames(3)
	game.hero.position=game.evacuation.DOOR;game.hero.reset_physics_interpolation()
	var positions=[Vector3(-31,0,24),Vector3(-29.5,0,24.5),Vector3(-28.8,0,25)]
	for i in range(3):
		var actor=game.evacuation.people[game.evacuation.FIRST[i]];actor.position=positions[i];actor.reset_physics_interpolation()
	game.evacuation.people.nina.position=Vector3(-31,0,26.5);game.evacuation.people.nina.reset_physics_interpolation()
	game.perform_action("evac_board");check(game.evacuation.stage=="boarding","physical nearby group can start orderly boarding")
	game.hero.position=Vector3(-29,0,22.5);game.hero.reset_physics_interpolation();game.paused=false
	var seconds:=0.0
	while game.evacuation.boarded.size()<1 and seconds<45:await physics_frame;seconds+=1.0/60
	game.paused=true
	check(game.evacuation.boarded.size()>=1,"first resident physically enters and sits before ID is counted")
	var saved_ids=game.evacuation.boarded.duplicate();game.save_checkpoint();await discard();await build()
	check(game.evacuation.boarded==saved_ids,"real scene reconstruction keeps each received ID")
	for id in saved_ids:check(game.evacuation.people[id].seated,"received actor remains seated after reload: "+id)
	check(game.evacuation.people.size()==5,"reload does not duplicate people")
	game.hero.position=Vector3(-29,0,22.5);game.hero.reset_physics_interpolation();game.paused=false;seconds=0
	while game.evacuation.boarded.size()<3 and seconds<70:await physics_frame;seconds+=1.0/60
	game.paused=true
	check(game.evacuation.boarded.size()==3 and game.evacuation.stage=="first_received","all three are individually received")
	check(not game.evacuation.boarded.has("nina") and not game.evacuation.boarded.has("lida"),"guides are not counted as hospital residents")
	check(game.evacuation.patient.global_position.x>28 and game.evacuation.people.lida.position.x>28,"Lida remains with distinct fourth resident")
	var stable=game.evacuation.boarded.duplicate();game.perform_action("evac_board");game.perform_action("evac_first")
	check(game.evacuation.boarded==stable,"repeated inputs cannot count the same resident twice")
	await last_journey_rules()
	var trace={"checks":checks,"failures":failures,"boarded":game.evacuation.boarded,"phase":game.evacuation.stage,"scope":"staged preparation/group at real door, physics/animation boarding and actual scene reload; full player route separate; fourth rescue not implemented in this step"}
	trace["transport"]=game.evacuation.transport.snapshot();trace["scope"]="staged preparation and positions; real physics/animation transfers, pause, scene reconstruction, guarded reception and keyboard dialogue choice; full route separate"
	await discard();var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(trace,"  "));file.close()
	print("EVAC_FIRST_RULES ",checks," failures=",failures)
	var until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<until:await process_frame
	quit(0 if failures.is_empty() else 1)

func last_journey_rules() -> void:
	var evac=game.evacuation;var last=evac.transport
	game.perform_action("evac_last_load");game.perform_action("evac_last_receive");check(not last.loaded and not last.received,"fourth cannot be received remotely or before loading")
	game.hero.position=game.REFUGE;evac.people.nina.position=Vector3(39,0,-3);evac.people.lida.position=Vector3(42,0,-4.8)
	game.perform_action("evac_last_plan");check(last.state=="bedside","return with Nina unlocks fourth preparation")
	game.perform_action("evac_last_bag");check(not last.bag_taken,"bag stays in refuge before patient and apparatus are ready")
	last.cart.position=last.LOAD_POINT;last.cart.reset_physics_interpolation();game.hero.position=Vector3(41.5,0,-4.9);game.hero.reset_physics_interpolation()
	game.perform_action("evac_last_load");check(last.lift_left>0 and not last.loaded,"starting lift does not complete transport immediately")
	game.paused=false;await frames(35);game.set_paused(true)
	var frozen=last.lift_left;var pose=evac.patient.global_position
	for i in range(12):await process_frame
	check(is_equal_approx(last.lift_left,frozen) and evac.patient.global_position.distance_to(pose)<.001,"full pause freezes patient transfer and its completion")
	game.set_paused(false);await frames(120);game.paused=true
	check(last.loaded and evac.patient.get_parent()==last.cart,"fourth finishes physical transfer onto cart before loaded flag")
	check(last.apparatus.get_parent()==last.cart and last.cable.get_parent()==last.cart,"apparatus and cable travel with patient")
	game.save_checkpoint();await discard();await build();evac=game.evacuation;last=evac.transport
	check(last.loaded and not last.attached and not last.received,"reload reconstructs loaded cart with hands free")
	check(evac.patient.get_parent()==last.cart and game.get_node_or_null("MikhailInWagon")!=null,"reload preserves separate fourth patient and Mikhail")
	game.hero.position=last.handle();game.perform_action("evac_cart");check(last.attached,"nearby handles can be taken")
	var attack=InputEventMouseButton.new();attack.button_index=MOUSE_BUTTON_LEFT;attack.pressed=true;game._unhandled_input(attack);game.try_dodge()
	check(game.hero.attack_left<=0 and game.hero.dash_left<=0,"pulling cart requires freeing hands before attack or dodge")
	game.perform_action("evac_cart");check(not last.attached,"cart can be released for combat")
	last.cart.position=last.PARK;last.cart.rotation.y=0;last.cart.reset_physics_interpolation()
	game.perform_action("evac_last_receive");check(not last.received,"in-wagon cart without Lida's bag is not received")
	game.hero.position=game.reception.BAG;evac.people.lida.position=game.reception.BAG+Vector3(.65,0,.3);game.perform_action("evac_last_bag")
	check(last.bag_taken and game.reception.bag.get_parent()==evac.people.lida,"bag is collected locally and remains physically with Lida")
	last.cart.position=Vector3(-34.7,0,24);game.perform_action("evac_last_receive");check(not last.received,"cart overlapping doorway is not counted inside")
	last.cart.position=last.PARK;game.hero.position=last.PARK;game.perform_action("evac_last_receive");check(not last.received,"Nina and Lida must actually arrive")
	evac.people.nina.position=Vector3(-36.2,0,27.5);evac.people.lida.position=Vector3(-36.2,0,22);game.perform_action("evac_last_receive")
	check(last.received and evac.boarded.size()==3 and last.footprint_inside(),"three separate residents plus fourth cart are received; no guide counted")
	game.hero.position=last.TALK;game.perform_action("evac_truth");check(last.question.visible and game.paused and paused,"wagon question pauses whole tree")
	var event=InputEventKey.new();event.physical_keycode=KEY_1;event.keycode=KEY_1;event.pressed=true;root.push_input(event,true)
	for i in range(3):await process_frame
	check(last.truth=="admit","ordinary keyboard selects explicit admission")
	last.choose("defend");check(last.truth=="admit","chosen admission cannot be overwritten by repeated input")
	check("Я видел платформу. И не остановился." in game.dialogue_book.text_for(game.dialogue_scope()),"admission remains in journal")
	last.question.close();await discard();await build();last=game.evacuation.transport
	check(last.received and last.truth=="admit" and not last.question.visible,"actual reload preserves received fourth and unique choice without reopening question")
	check(game.evacuation.people.size()==5,"final reload creates no duplicate companions")
