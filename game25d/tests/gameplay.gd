extends SceneTree

var checks := 0
var failures: Array[String] = []
var game: Node3D

func _initialize() -> void:
	run.call_deferred()

func check(condition: bool,label: String) -> void:
	checks+=1
	if not condition:failures.append(label);push_error("FAIL: "+label)

func wait_frames(count: int) -> void:
	for i in range(count):await physics_frame

func run() -> void:
	game=load("res://main.tscn").instantiate();root.add_child(game);await wait_frames(4)
	game.paused=true
	check(game.camera.projection==Camera3D.PROJECTION_ORTHOGONAL,"orthographic camera")
	var capsule=game.hero.get_node("BodyShape").shape
	check(abs(capsule.height-1.78)<.001,"hero height is 1.78 metres")
	check(game.nav.is_point_solid(Vector2i(-6,6)),"bench seat participates in navigation")
	check(game.obstacles.has(game.gate_obstacle),"closed door blocks navigation")
	check(game.route(Vector3(-4,0,5),Vector3(-6,0,-8)).size()>4,"relay route exists")
	check(game.health_bar.size.y<14,"health bar respects requested thin height")
	check(game.dash_bar.size.y<7,"dash bar respects requested thin height")
	game.hero.position=Vector3(0,.02,7)
	for foe in game.enemies:foe.position=Vector3(6,.02,9)
	var front=game.enemies[0];front.position=Vector3(0,.02,8.15)
	var back=game.enemies[1];back.position=Vector3(0,.02,5.9)
	await wait_frames(3)
	game.hero.facing=Vector3.BACK;game.strike()
	check(front.health==25,"directed strike hits front enemy for 55")
	check(back.health==100,"directed strike ignores enemy behind")
	front.hurt_left=0;front.dash_left=0;front.stun=0;game.strike();check(not front.alive,"runner dies after two hits")
	game.hero.attack_left=0;game.hero.dash_left=0;game.hero.begin_attack(Vector3.BACK)
	game.hero.action_elapsed=.14;game.hero.attack_left=0;game.hero.begin_attack(Vector3.BACK)
	check(game.hero.action_elapsed<.01 and game.hero.action_remaining>.4,"repeated attack actually restarts animation")
	game.hero.health=100;game.hero.hurt_left=0;game.hero.dash_left=.12
	var runner=game.spawn_actor("runner",game.hero.position+Vector3(0,0,.5));runner.phase="charge";runner.phase_left=.29;runner.target_direction=Vector3.FORWARD
	game.enemy_tick(runner,.016);check(game.hero.health==100,"dodge prevents charge damage")
	game.hero.dash_left=0;game.enemy_tick(runner,.016);check(game.hero.health==100,"one charge cannot re-hit after avoided contact")
	runner.queue_free()
	var brute=game.enemies[2];brute.phase="windup";brute.hurt_left=0;brute.take_hit(10,Vector3.BACK)
	check(brute.phase=="windup","brute resists interruption during windup")
	var q=InputEventKey.new();q.keycode=KEY_Q;q.physical_keycode=KEY_Q;q.pressed=true
	game.paused=false
	for i in range(4):game.flare_cooldown=0;game._unhandled_input(q)
	game.paused=true
	check(game.flares==0,"flare count is limited to three")
	var barrel=game.barrels[0];var rect=barrel.get_meta("nav_rect");var band=barrel.get_child(0)
	check(band.get_parent()==barrel,"barrel bands belong to breakable barrel")
	game.break_barrel(barrel);await wait_frames(3)
	check(not is_instance_valid(barrel),"destroyed barrel disappears with its bands")
	check(not game.obstacles.has(rect),"broken barrel no longer blocks navigation")
	# Real held-key input drives the relay; no mission variables are assigned here.
	game.hero.position=Vector3(-6,.02,-8);game.hero.health=100;game.hero.alive=true;game.hero.hurt_left=0;game.hero.attack_left=0;game.hero.stun=0
	for foe in game.enemies:
		if is_instance_valid(foe):foe.stun=10
	var e=InputEventKey.new();e.physical_keycode=KEY_E;e.keycode=KEY_E;e.pressed=true;Input.parse_input_event(e)
	game.paused=false;await wait_frames(90);game.paused=true;e.pressed=false;Input.parse_input_event(e)
	check(game.mission==1 and game.opened,"held E opens relay and advances mission")
	check(not game.obstacles.has(game.gate_obstacle),"opening removes the actual gate obstacle")
	check(game.obstacles.size()>10,"opening does not erase unrelated props")
	game.paused=false;await wait_frames(45);game.paused=true
	check(game.gate_collider.disabled,"physical door collider opens")
	game.hero.position=Vector3(3.9,.02,-6.8);game.hero.reset_physics_interpolation()
	var target=Vector3(-.5,.65,-5.5);game.camera.position=target+game.camera_offset;game.camera.look_at(target)
	await wait_frames(3);game.check_occlusion();game.update_occlusion(.2)
	var faded=false
	for item in game.occluded.values():
		if item[0].transparency>.8:faded=true
	check(faded,"parallel orthographic ray fades wall hiding hero")
	var basis=game.camera.basis
	game.hero.facing=Vector3.LEFT;game.follow_camera(.016);game.hero.facing=Vector3.RIGHT;game.follow_camera(.016)
	check(game.camera.basis.is_equal_approx(basis),"camera retains angle when hero turns")
	game.hero.position=Vector3(0,.02,7);game.hero.velocity=Vector3.ZERO;game.hero.motion_velocity=Vector2.ZERO;game.hero.knockback=Vector3.ZERO;game.hero.dash_left=0;game.hero.hurt_left=0
	game.hero.take_hit(1,Vector3.RIGHT);var start=game.hero.position
	for i in range(20):game.hero.move_ground(Vector3.ZERO,0,1.0/60.0)
	check(game.hero.position.distance_to(start)<.35,"one hit applies one short knockback, not accumulating impulses")
	game.hero.attack_left=0;game.hero.dash_left=0;game.hero.stun=0
	var click=InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_LEFT;click.pressed=true
	click.position=game.camera.unproject_position(game.hero.position+Vector3.RIGHT+Vector3.UP*.7)
	game.paused=false
	root.push_input(click,true)
	game.paused=true
	check(game.hero.attack_left>0 and game.hero.facing.dot(Vector3.RIGHT)>.99,"mouse strike uses event coordinates rather than stale OS cursor")
	var report={"checks":checks,"failures":failures,"engine":Engine.get_version_info().string,"scope":"2.5D fixtures and real relay input; not a human playtest"}
	var file=FileAccess.open(preload("res://tests/qa_report.gd").path("H:/game/release/gameplay-latest.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("GAMEPLAY_QA ",checks," checks; failures=",failures)
	quit(0 if failures.is_empty() else 1)
