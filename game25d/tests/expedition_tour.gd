extends SceneTree
## Ordinary engine keyboard/mouse input, no hero/cart teleports or health changes.
var game: Node3D
var held: Dictionary = {}
var path: Array[Vector3] = []
var repath := 0.0
var elapsed := 0.0
var combat_time := 0.0
var stage := 0
var waypoint := 0
var last_attack := 0.0
var e_wait := 0.0
var method := "stopper"
var idle_time := 0.0
var last_position := Vector3.ZERO
var progress_time := 0.0
var detach_count := 0
var attached_last := false
var output := "H:/game/release/expedition-v036/tour-stopper"
var previous_stage := -1
var captures := false
var attack_events: Array = []
var waypoints: Array[Vector3] = [Vector3(54,0,-11),Vector3(54,0,-3),Vector3(54,0,17),Vector3(42,0,17),Vector3(30,0,17),Vector3(18,0,17),Vector3(0,0,17),Vector3(-3,0,17),Vector3(-15,0,17),Vector3(-27,0,24),Vector3(-28,0,30)]

func _initialize() -> void:start.call_deferred()

func start() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg=="--method=power":method="power";output="H:/game/release/expedition-v036/tour-power"
		if arg=="--tour-capture":captures=true
		if arg.begins_with("--tour-output="):output=arg.trim_prefix("--tour-output=")
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED);Engine.max_fps=0
	game=load("res://expedition.tscn").instantiate();root.add_child(game)
	waypoints[-1]=game.DOCK
	await physics_frame
	last_position=game.hero.position
	process_frame.connect(tick)
	print("EXPEDITION_TOUR_BEGIN method=",method," keyboard+mouse input; no fixture state mutations")

func key(code: int,down: bool) -> void:
	# Native window focus changes can clear Godot's pressed state. Reconcile
	# through the same real key event instead of trusting the harness cache.
	if held.get(code,false)==down and Input.is_physical_key_pressed(code)==down:return
	held[code]=down
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=down;event.ctrl_pressed=held.get(KEY_CTRL,false);event.shift_pressed=held.get(KEY_SHIFT,false);Input.parse_input_event(event)

func mouse_attack(target: Vector3) -> void:
	var point=game.camera.unproject_position(target+Vector3.UP*.7)
	var motion=InputEventMouseMotion.new();motion.position=point;motion.global_position=point;root.push_input(motion,true)
	var event=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.position=point;event.pressed=true;root.push_input(event,true)
	var released=InputEventMouseButton.new();released.button_index=MOUSE_BUTTON_LEFT;released.position=point;released.pressed=false;root.push_input(released,true)
	if attack_events.size()<20:attack_events.append({"mouse_sent":str(point),"mouse_read":str(root.get_mouse_position()),"aim_dot":game.hero.facing.dot((target-game.hero.position).normalized()),"attack_left":game.hero.attack_left,"time":elapsed,"flares":game.flares})

func move(direction: Vector3,fast:=false) -> void:
	var right=game.camera.global_basis.x;right.y=0;right=right.normalized()
	var forward=game.camera.global_basis.z;forward.y=0;forward=forward.normalized()
	var x=direction.dot(right);var y=direction.dot(forward)
	key(KEY_D,x>.29);key(KEY_A,x< -.29);key(KEY_S,y>.29);key(KEY_W,y< -.29);key(KEY_SHIFT,fast)

func go(target: Vector3,delta: float) -> void:
	repath-=delta
	if repath<=0:path=game.route(game.hero.position,target);repath=.4
	while not path.is_empty() and game.hero.position.distance_to(path[0])<.32:path.remove_at(0)
	var direction=(path[0]-game.hero.position).normalized() if not path.is_empty() else (target-game.hero.position).normalized()
	direction.y=0;move(direction,false)

func interact(target: Vector3,delta: float,radius:=1.3) -> void:
	if game.hero.position.distance_to(target)<radius:move(Vector3.ZERO);key(KEY_E,true)
	else:key(KEY_E,false);go(target,delta)

func tick() -> void:
	var delta=root.get_process_delta_time();elapsed+=delta;last_attack+=delta;e_wait=maxf(0,e_wait-delta)
	if not game.hero.alive:finish("player defeated");return
	if elapsed>600:finish("time limit");return
	if game.mission==3:finish("patient boarded");return
	if game.hero.position.distance_to(last_position)>.25:last_position=game.hero.position;progress_time=elapsed
	if elapsed-progress_time>18:finish("stuck: stage "+str(stage)+" waypoint "+str(waypoint));return
	if attached_last and not game.cart_attached:detach_count+=1
	attached_last=game.cart_attached
	var nearest: RailActor=null;var distance=1000.0
	for foe in game.enemies:
		if is_instance_valid(foe) and foe.alive:
			var d=game.hero.position.distance_to(foe.position)
			if d<distance and game.visible_between(game.hero.position,foe.position):nearest=foe;distance=d
	if nearest and distance<5.5:
		combat_time+=delta
		if game.cart_attached:interact(game.hero.position,delta);return
		key(KEY_E,false)
		if game.flares>0 and game.flare_cooldown<=0 and game.hero.health<65 and distance<4.0:
			key(KEY_Q,true)
		else:key(KEY_Q,false)
		if nearest.phase in ["windup","charge"] and distance<3.0 and (nearest.phase=="charge" or nearest.phase_left<=.24):
			var away=(game.hero.position-nearest.position).normalized()
			var evade=Vector3(-away.z,0,away.x)
			if not game.inside_floor(Vector2(game.hero.position.x+evade.x*2,game.hero.position.z+evade.z*2)):evade=-evade
			move(evade);key(KEY_SPACE,game.hero.dash_cooldown<=0 and game.hero.attack_left<=.26)
		else:
			key(KEY_SPACE,false)
			if distance<1.32:
				move(Vector3.ZERO)
				var safe_attack=not (nearest.enemy_kind=="brute" and nearest.phase=="windup" and nearest.phase_left<.5)
				if safe_attack and game.hero.attack_left<=0 and game.hero.dash_left<=0 and game.hero.stun<=0 and last_attack>.45:mouse_attack(nearest.position);last_attack=0
			else:go(nearest.position,delta)
		return
	key(KEY_SPACE,false)
	key(KEY_Q,false)
	# Resupply is an actual finite interaction, not a health override.
	if game.hero.health<65 and not game.cart_attached:
		for id in game.supply_positions:
			if not game.supplies_taken.has(id) and game.hero.position.distance_to(game.supply_positions[id])<6:
				interact(game.supply_positions[id],delta);return
	if stage!=previous_stage:
		previous_stage=stage;progress_time=elapsed
		print("TOUR_STAGE ",stage," pos=",game.hero.position," health=",game.hero.health)
		if captures:save_frame("stage-%02d.png"%stage)
	if stage==0:
		if (game.has_stopper if method=="stopper" else game.power_on):stage=1;key(KEY_E,false);return
		interact(game.STOPPER if method=="stopper" else game.GENERATOR,delta)
	elif stage==1:
		if method=="power" and game.hero.health<80 and not game.supplies_taken.has("relay"):interact(game.supply_positions.relay,delta);return
		if game.mission==1:stage=2;key(KEY_E,false);return
		interact(game.MANUAL if method=="stopper" else game.RELAY,delta)
	elif stage==2:
		if game.mission==2:stage=3;key(KEY_E,false);return
		interact(game.PATIENT_POINT,delta)
	elif stage==3:
		if game.hero.health<80 and not game.supplies_taken.has("pharmacy"):interact(game.supply_positions.pharmacy,delta);return
		if game.inner_open:stage=4;key(KEY_E,false);return
		interact(game.INNER_BOLT,delta)
	elif stage==4:
		if game.cart_attached:stage=5;key(KEY_E,false);return
		interact(game.cart.to_global(Vector3(0,0,1.7)),delta,.4)
	elif stage==5:
		if not game.cart_attached:stage=4;key(KEY_E,false);return
		if waypoint>=waypoints.size():stage=6;key(KEY_E,false);return
		if waypoint==7 and not game.service_open:interact(game.SERVICE_BOLT,delta);return
		key(KEY_E,false)
		var target=waypoints[waypoint]
		if game.hero.position.distance_to(target)<1.2:waypoint+=1;progress_time=elapsed
		else:go(target,delta)
	elif stage==6:
		if game.cart.position.distance_to(game.DOCK)>=3:
			key(KEY_E,false);move(Vector3.ZERO)
		else:interact(game.DOCK,delta)

func save_frame(name: String) -> void:
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(output);root.get_texture().get_image().save_png(output.path_join(name))

func finish(reason: String) -> void:
	process_frame.disconnect(tick)
	for code in held.keys():key(code,false)
	DirAccess.make_dir_recursive_absolute(output)
	var report={"reason":reason,"seconds":elapsed,"health":game.hero.health,"mission":game.mission,"method":method,"combat_seconds":combat_time,"hero_distance":game.total_distance,"cart_distance":game.cart_distance,"cart_position":game.vec(game.cart.position),"hero_position":game.vec(game.hero.position),"cart_detaches":detach_count,"actions":game.action_log,"automated":true,"hero_teleports":0,"cart_teleports":0,"health_override":false,"normal_supply_interactions":game.supplies_taken,"input":"keyboard and mouse events through Input/Viewport"}
	report["game_version"]=ProjectSettings.get_setting("application/config/version")
	report["main_sha256"]=FileAccess.get_sha256("res://scripts/main.gd");report["actor_sha256"]=FileAccess.get_sha256("res://scripts/actor.gd")
	var file=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	report["gpu_screenshots"]=captures
	file=FileAccess.open(output.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	var debug_file=FileAccess.open(output.path_join("input-diagnostics.json"),FileAccess.WRITE);debug_file.store_string(JSON.stringify({"attacks":attack_events,"flares_left":game.flares,"killed":game.killed},"  "));debug_file.close()
	print("EXPEDITION_TOUR_END ",reason," time=",elapsed," health=",game.hero.health," mission=",game.mission)
	if captures:await save_frame("final.png")
	game.queue_free();await process_frame;await process_frame
	var drain_until=Time.get_ticks_msec()+400
	while Time.get_ticks_msec()<drain_until:await process_frame
	quit(0 if reason=="patient boarded" else 1)
