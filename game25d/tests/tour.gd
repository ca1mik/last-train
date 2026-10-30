extends SceneTree

var game: Node3D
var elapsed := 0.0
var held: Dictionary = {}
var route: Array[Vector3] = []
var repath := 0.0
var combat_time := 0.0
var stage := 0
var report := {}
var key_ready := false
var last_attack := 0.0
var capture_path := "H:/game/release/previews/25d-final"

func _initialize() -> void:
	start.call_deferred()

func start() -> void:
	game=load("res://main.tscn").instantiate();root.add_child(game)
	await physics_frame
	process_frame.connect(tick)
	print("TOUR_START automated keyboard movement; real enemies, health and collision; no teleport")

func key(code: int,down: bool) -> void:
	if held.get(code,false)==down:return
	held[code]=down
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=down;Input.parse_input_event(event)

func move(direction: Vector3,fast:=false) -> void:
	var right=game.camera.global_basis.x;right.y=0;right=right.normalized()
	var forward=game.camera.global_basis.z;forward.y=0;forward=forward.normalized()
	var x=direction.dot(right);var y=direction.dot(forward)
	key(KEY_D,x>.29);key(KEY_A,x< -.29);key(KEY_S,y>.29);key(KEY_W,y< -.29);key(KEY_SHIFT,fast)

func go(target: Vector3,delta: float) -> void:
	repath-=delta
	if repath<=0:route=game.route(game.hero.position,target);repath=.3
	while not route.is_empty() and game.hero.position.distance_to(route[0])<.26:route.remove_at(0)
	var direction=(route[0]-game.hero.position).normalized() if not route.is_empty() else (target-game.hero.position).normalized()
	direction.y=0;move(direction)

func tick() -> void:
	var delta=minf(.05,root.get_process_delta_time())
	elapsed+=delta;last_attack+=delta
	if not is_instance_valid(game) or not game.hero.alive:
		finish("player defeated");return
	var closest: RailActor=null;var distance=100.0
	for foe in game.enemies:
		if is_instance_valid(foe) and foe.alive:
			var d=game.hero.position.distance_to(foe.position)
			if d<distance:closest=foe;distance=d
	if closest and (distance<5.8 or stage==0):
		combat_time+=delta;key(KEY_E,false)
		if closest.phase=="windup" and distance<2.9 and game.hero.dash_cooldown<=0:
			var difference=(game.hero.position-closest.position).normalized();var evade=Vector3(-difference.z,0,difference.x)
			move(evade);game.try_dodge()
		elif distance<1.4:
			move(Vector3.ZERO)
			if game.hero.attack_left<=0 and game.hero.dash_left<=0 and last_attack>.45:
				game.hero.begin_attack((closest.position-game.hero.position).normalized());last_attack=0
		else:go(closest.position,delta)
	else:
		stage=1
		var target=Vector3(-6,0,-8) if game.mission==0 else Vector3(7.8,0,-6.4)
		if game.hero.position.distance_to(target)<1.25:move(Vector3.ZERO);key(KEY_E,true)
		else:key(KEY_E,false);go(target,delta)
	if elapsed>10 and elapsed<10.05:save_frame("combat.png")
	if game.mission==2 or elapsed>65:finish("patient found" if game.mission==2 else "time limit")

func save_frame(name: String) -> void:
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(capture_path);root.get_texture().get_image().save_png(capture_path.path_join(name))

func finish(reason: String) -> void:
	process_frame.disconnect(tick)
	for code in held.keys():key(code,false)
	await save_frame("station.png")
	report={"reason":reason,"seconds":elapsed,"health":game.hero.health,"mission":game.mission,"combat_seconds":combat_time,"automated":true,"teleports":0,"health_override":false}
	var file=FileAccess.open("H:/game/release/tour-v34.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close();print("TOUR_RESULT ",report)
	quit()
