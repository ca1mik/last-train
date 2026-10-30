extends SceneTree

var game: Node3D
var elapsed := 0.0
var previous_segment := -1
var previous_action := -1
var fixed_basis: Basis
var max_camera_rotation := 0.0
var max_turn := 0.0
var previous_turn := 0.0
var count := 0
var sample: Array = []
var bone: Skeleton3D
var previous_hand := Vector3.ZERO
var first := true
var evidence_dir := "H:/game/release/capability-audit/motion-frames"
var report_path := "H:/game/release/capability-audit/motion-review.json"

func _initialize() -> void:start.call_deferred()

func skeleton_in(node: Node) -> Skeleton3D:
	if node is Skeleton3D:return node
	for child in node.get_children():
		var found=skeleton_in(child)
		if found:return found
	return null

func start() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps=0
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--motion-dir="):evidence_dir=arg.trim_prefix("--motion-dir=")
		if arg.begins_with("--motion-report="):report_path=arg.trim_prefix("--motion-report=")
	game=load("res://main.tscn").instantiate();root.add_child(game);game.paused=true
	for foe in game.enemies:foe.queue_free()
	game.enemies.clear();bone=skeleton_in(game.hero)
	physics_frame.connect(tick);process_frame.connect(render_tick)
	print("MOTION_REVIEW: 60 FPS, isolated movement fixture, fixed and following camera")

func reset_segment(segment: int) -> void:
	game.hero.position=Vector3(-5,.02,-6.8);game.hero.velocity=Vector3.ZERO;game.hero.motion_velocity=Vector2.ZERO;game.hero.knockback=Vector3.ZERO;game.hero.dash_left=0;game.hero.attack_left=0;game.hero.animation_speed=0
	game.hero.facing=Vector3.RIGHT;game.hero.visual.rotation.y=PI*.5;game.hero.reset_physics_interpolation();previous_turn=PI*.5
	var target=Vector3(-.5,.65,-5.5) if segment==0 else game.hero.position+Vector3(0,.65,0)
	game.camera.position=target+game.camera_offset;game.camera.look_at(target);fixed_basis=game.camera.global_basis
	game.objective.text="Проверка движения · "+("неподвижная камера" if segment==0 else "следящая камера")
	game.radio.visible=false;game.help.text="";game.work_bar.visible=false
	for label in game.world_labels:label.visible=false
	previous_action=-1

func tick() -> void:
	var delta=1.0/60.0;elapsed+=delta
	var segment=int(elapsed/14.0);var t=fmod(elapsed,14.0)
	if segment>=2:finish();return
	if segment!=previous_segment:previous_segment=segment;reset_segment(segment)
	var actor=game.hero;actor.clocks(delta)
	var direction=Vector3.ZERO;var speed=0.0;var label="Покой"
	if t>=.8 and t<2.0:direction=Vector3.RIGHT;speed=1.72;label="Ходьба → бег"
	elif t>=2.0 and t<3.2:direction=Vector3.RIGHT;speed=3.8;label="Бег"
	elif t>=3.2 and t<3.6:direction=Vector3.RIGHT;speed=5.7;label="Спринт → остановка"
	elif t>=4.3 and t<5.8:direction=Vector3.LEFT;speed=3.8;label="Разворот на 180°"
	elif t>=5.8 and t<6.8:direction=Vector3(-.707,0,.707);speed=3.8;label="Переход на диагональ"
	elif t>=7.5 and t<10.0:
		label="Повторные удары · ноги продолжают шаг"
		var action=int((t-7.5)/.57)
		if action!=previous_action:actor.begin_attack(Vector3.RIGHT);previous_action=action
		if t>8.5:direction=Vector3.RIGHT;speed=1.6
	elif t>=10.4 and t<11.1:
		label="Уклонение → остановка"
		if previous_action<20:actor.dash_left=.18;actor.dash_direction=Vector3.RIGHT;previous_action=20
	elif t>=11.7:
		label="Плавный поворот"
		direction=Vector3(sin((t-11.7)*2.0),0,cos((t-11.7)*2.0));speed=1.72
	if actor.dash_left>0:direction=actor.dash_direction;speed=11;actor.dash_left=maxf(0,actor.dash_left-delta)
	actor.move_ground(direction,speed,delta);actor.advance_pose(delta)
	var turn=actor.visual.rotation.y;max_turn=maxf(max_turn,absf(angle_difference(previous_turn,turn)));previous_turn=turn
	game.status.text=label
	var hand=bone.get_bone_global_pose(bone.find_bone("Palm.R")).origin
	if not first and t>.2:sample.append({"t":elapsed,"hand_delta":hand.distance_to(previous_hand),"speed":actor.ground_speed,"action":actor.attack_left>0})
	first=false;previous_hand=hand
	if count%30==0:frame_capture.call_deferred(count)
	count+=1

func render_tick() -> void:
	if previous_segment<0:return
	if previous_segment==1:game.follow_camera(root.get_process_delta_time())
	game.check_occlusion();game.update_occlusion(root.get_process_delta_time())
	if not game.camera.global_basis.is_equal_approx(fixed_basis):max_camera_rotation=maxf(max_camera_rotation,game.camera.global_basis.get_rotation_quaternion().angle_to(fixed_basis.get_rotation_quaternion()))

func frame_capture(index: int) -> void:
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(evidence_dir)
	root.get_texture().get_image().save_png(evidence_dir.path_join("%04d.png"%index))

func finish() -> void:
	physics_frame.disconnect(tick);process_frame.disconnect(render_tick)
	var report={"fps":60,"seconds":elapsed,"camera_angle_drift_degrees":rad_to_deg(max_camera_rotation),"max_turn_step_degrees":rad_to_deg(max_turn),"fixture":true,"samples":sample}
	var file=FileAccess.open(report_path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("MOTION_RESULT camera_drift=",report.camera_angle_drift_degrees," max turn step=",report.max_turn_step_degrees)
	quit()
