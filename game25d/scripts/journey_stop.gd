extends "res://scripts/environment_trial.gd"
## Shared mechanics for authored campaign stops. Art remains a production blockout.
const CAMPAIGN = preload("res://scripts/campaign.gd")
const PERSON = preload("res://scripts/escort_actor.gd")
var stop_id := "journey"
var title_text := "Линия"
var intro_text := ""
var next_chapter := 1
var state: Dictionary = {}
var campaign_data: Dictionary = {}
var people: Dictionary = {}
var person_labels: Dictionary = {}
var person_moved: Dictionary = {}
var gates: Dictionary = {}
var train_node: Node3D
var save_path := ""
var save_error := ""
var action_target := ""
var action_log: Array = []
var completed := false
var departing := false
var route_label: Label
var map_view: Control
var map_large := false
var checkpoint_position := Vector3.ZERO

func configure() -> void: pass
func build_content() -> void: pass
func spawn_encounters() -> void: pass
func get_options() -> Array: return []
func act(_action: String) -> bool: return false
func apply_state() -> void: pass
func task_text() -> String: return title_text
func tick_story(_delta: float) -> void: pass

func _ready() -> void:
	configure()
	campaign_data = CAMPAIGN.read().duplicate(true)
	if campaign_data.get("outcomes") is Dictionary:
		campaign_data.merge(campaign_data.outcomes, true)
	var legacy = "user://" + stop_id + "-v049.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--save-slot="):
			var slot = arg.trim_prefix("--save-slot=").get_file()
			if slot.begins_with("qa-"): legacy = "user://" + stop_id + "-" + slot
		if arg.begins_with("--capture="): capture_dir = arg.trim_prefix("--capture=")
	save_path = CAMPAIGN.checkpoint_path(stop_id, legacy)
	kit = preload("res://scripts/environment_kit.gd").new(self, 4900 + stop_id.hash() % 100)
	setup_world()
	build_station()
	setup_navigation()
	hero = spawn_actor("", start_point)
	checkpoint_position = start_point
	spawn_encounters()
	setup_camera()
	setup_ui()
	load_checkpoint()
	apply_state()
	refresh_nav()
	update_task()
	if intro_text != "" and not state.get("introduced", false):
		say(intro_text, 8)
		state.introduced = true
		save_checkpoint()
	print("JOURNEY_READY stop=", stop_id, " save=", save_path)

func build_station() -> void:
	var middle = Vector3(bounds.get_center().x, 0, bounds.get_center().y)
	block(middle + Vector3(0, -.55, 0), Vector3(bounds.size.x + 25, .5, bounds.size.y + 25), Color("253b3d"))
	var floor_node = block(middle + Vector3(0, -.14, 0), Vector3(bounds.size.x, .28, bounds.size.y), Color("586260"), true)
	var shader = ShaderMaterial.new()
	shader.shader = load("res://shaders/expedition_floor.gdshader")
	shader.set_shader_parameter("base_color", Color("515d57"))
	shader.set_shader_parameter("tile_size", 1.6)
	mesh_in(floor_node).material_override = shader
	for x in [bounds.position.x - .15, bounds.end.x + .15]:
		block(Vector3(x, .4, middle.z), Vector3(.3, .8, bounds.size.y), Color("3a5050"), true)
	for z in [bounds.position.y - .15, bounds.end.y + .15]:
		block(Vector3(middle.x, .4, z), Vector3(bounds.size.x, .8, .3), Color("3a5050"), true)
	train_node = Node3D.new()
	train_node.name = "RefugeTrain"
	add_child(train_node)
	train_node.position = start_point + Vector3(-4.5, 0, 0)
	block(Vector3(0, .3, 0), Vector3(2.5, .5, 12), Color("233637"), false, .6, .3, train_node)
	block(Vector3(-1.2, 1.5, 0), Vector3(.15, 2.6, 12), Color("304e48"), false, .5, .3, train_node)
	block(Vector3(0, 2.9, 0), Vector3(2.7, .2, 12), Color("273d3c"), false, .5, .3, train_node)
	for z in [-4.5, -1.5, 1.5, 4.5]:
		block(Vector3(-1.1, 1.75, z), Vector3(.03, .85, 1.7), Color("b8a77d"), false, .7, 0, train_node)
		block(Vector3(.5, .6, z), Vector3(.7, .35, 1.2), Color("7b7560"), false, .8, 0, train_node)
	label_world("ПОЕЗД · УБЕЖИЩЕ", start_point + Vector3(0, 2.1, 0), .007)
	lamp(start_point + Vector3(-1.5, 0, 2))
	build_content()
	kit.finish_grass()

func setup_navigation() -> void:
	nav.region = Rect2i(Vector2i(floori(bounds.position.x * 2) - 2, floori(bounds.position.y * 2) - 2), Vector2i(ceili(bounds.size.x * 2) + 4, ceili(bounds.size.y * 2) + 4))
	nav.cell_size = Vector2(.5, .5)
	nav.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	nav.update()
	refresh_nav()

func add_gate(id: String, pos: Vector3, size: Vector3, color: Color = Color("66765a")) -> Node3D:
	var panel = block(pos, size, color)
	var body = StaticBody3D.new()
	panel.add_child(body)
	var shape = CollisionShape3D.new()
	body.add_child(shape)
	var box = BoxShape3D.new()
	box.size = size
	shape.shape = box
	var rect = Rect2(Vector2(pos.x - size.x * .5, pos.z - size.z * .5), Vector2(size.x, size.z)).grow(.38)
	obstacles.append(rect)
	gates[id] = {"node": panel, "shape": shape, "rect": rect, "position": pos, "open": false}
	return panel

func set_gate_open(id: String, value: bool) -> void:
	if not gates.has(id): return
	var entry = gates[id]
	if entry.open == value: return
	entry.open = value
	entry.shape.set_deferred("disabled", value)
	entry.node.position.y = entry.position.y + (3.2 if value else 0.0)
	if value: obstacles.erase(entry.rect)
	elif not obstacles.has(entry.rect): obstacles.append(entry.rect)
	if nav.region.has_area(): refresh_nav()

func add_person(id: String, pos: Vector3, height: float = 1.72) -> Node3D:
	var actor = PERSON.new()
	add_child(actor)
	actor.setup(id, "res://assets/characters/patient.glb", height, 4.805)
	actor.position = pos
	# Companions keep world collision but do not form an immovable queue in doors.
	actor.collision_mask = 1
	actor.collision_layer = 8
	actor.reset_physics_interpolation()
	people[id] = actor
	var names = {"nina":"НИНА", "lida":"ЛИДА", "pavel":"ПАВЕЛ", "valentina":"ВАЛЕНТИНА", "mikhail":"МИХАИЛ", "raisa":"РАИСА", "neighbour_a":"ЖИТЕЛЬ", "neighbour_b":"ЖИТЕЛЬ", "fourth":"ПАЦИЕНТ"}
	var tag = label_world(names.get(id, id.to_upper()), Vector3(0, height + .25, 0), .005)
	world_labels.erase(tag)
	tag.reparent(actor, false)
	person_labels[id] = tag
	return actor

func move_person(id: String, target: Vector3, speed: float, delta: float) -> bool:
	if not people.has(id): return false
	var actor = people[id]
	person_moved[id] = true
	if actor.position.distance_to(target) < .42:
		actor.move_direction(Vector3.ZERO, 0, delta)
		return true
	actor.repath -= delta
	if actor.repath <= 0 or actor.last_target.distance_to(target) > .7:
		actor.path = route(actor.position, target)
		actor.repath = .4
		actor.last_target = target
	while not actor.path.is_empty() and actor.position.distance_to(actor.path[0]) < .3:
		actor.path.remove_at(0)
	var direction = Vector3.ZERO
	if not actor.path.is_empty(): direction = (actor.path[0] - actor.position).normalized()
	actor.move_direction(direction, speed, delta)
	return actor.position.distance_to(target) < .42

func setup_ui() -> void:
	super.setup_ui()
	landmark.text = title_text.to_upper()
	objective.size = Vector2(1420, 78)
	objective.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	landmark.position.y = 145
	route_label = make_label("M — схема  ·  J — журнал  ·  Esc — пауза", Vector2(42, 183), 18, Color("aabbab"))
	map_view = load("res://scripts/journey_map.gd").new()
	map_view.game = self
	ui.add_child(map_view)
	map_view.position = Vector2(1595, 28)
	map_view.size = Vector2(295, 280)
	map_view.mouse_filter = Control.MOUSE_FILTER_IGNORE

func update_task() -> void:
	if not is_instance_valid(objective): return
	objective.text = task_text()
	if save_error != "": route_label.text = save_error

func interactions(delta: float) -> void:
	help.text = ""
	work_bar.visible = false
	if departing: return
	person_moved.clear()
	tick_story(delta)
	for id in people:
		if not person_moved.has(id): people[id].move_direction(Vector3.ZERO, 0, delta)
		person_labels[id].visible = people[id].position.distance_to(hero.position) < 8
	if not hero.alive: return
	map_view.queue_redraw()
	update_task()
	if not Input.is_physical_key_pressed(KEY_E): input_latched = false
	var nearest = 1.65
	var candidate = ""
	var caption = ""
	for option in get_options():
		var distance = hero.position.distance_to(option[1])
		if distance < nearest:
			nearest = distance
			candidate = option[0]
			caption = option[2]
	if candidate == "":
		work = 0
		action_target = ""
		return
	help.text = "E · " + caption
	if input_latched or not Input.is_physical_key_pressed(KEY_E) or hero.ground_speed > .15 or hero.attack_left > 0 or hero.dash_left > 0 or hero.stun > 0:
		work = 0
		return
	if candidate != action_target:
		action_target = candidate
		work = 0
	work += delta
	work_bar.visible = true
	work_bar.value = work / .5 * 100
	if work >= .5:
		work = 0
		input_latched = true
		if act(candidate):
			action_log.append({"action":candidate, "seconds":clock})
			apply_state()
			save_checkpoint()
			update_task()

func save_checkpoint() -> void:
	if not is_instance_valid(hero) or not hero.alive: return
	var actors: Array = []
	for foe in enemies:
		if not is_instance_valid(foe):
			actors.append({"alive":false})
			continue
		actors.append({"alive":foe.alive, "health":foe.health, "position":[foe.position.x, foe.position.z]})
	var residents = {}
	for id in people:
		var person = people[id]
		residents[id] = {"position":[person.position.x, person.position.y, person.position.z], "yaw":person.rotation.y}
	var data = {"version":1, "stop":stop_id, "state":state, "hero":[hero.position.x, hero.position.z], "health":hero.health, "flares":flares, "enemies":actors, "people":residents, "actions":action_log}
	var file = FileAccess.open(save_path + ".tmp", FileAccess.WRITE)
	if not file:
		save_error = "Ошибка сохранения. Прогресс этой остановки пока не записан."
		return
	file.store_string(JSON.stringify(data))
	file.flush()
	var error = file.get_error()
	file.close()
	if error == OK: error = DirAccess.rename_absolute(save_path + ".tmp", save_path)
	save_error = "" if error == OK else "Ошибка сохранения · " + error_string(error)
	checkpoint_position = hero.position

func load_checkpoint() -> void:
	if not FileAccess.file_exists(save_path): return
	var data = JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if not data is Dictionary or data.get("version", 0) != 1 or data.get("stop", "") != stop_id: return
	if not data.get("state") is Dictionary or not data.get("hero") is Array or data.hero.size() != 2: return
	var point = Vector3(float(data.hero[0]), 0, float(data.hero[1]))
	if not point.is_finite() or not bounds.grow(-.3).has_point(Vector2(point.x, point.z)): return
	state.merge(data.state, true)
	hero.position = point
	hero.health = clampf(float(data.get("health", 100)), 1, 100)
	flares = clampi(int(data.get("flares", 3)), 0, 5)
	hero.reset_physics_interpolation()
	checkpoint_position = point
	var actors = data.get("enemies", [])
	if actors is Array:
		for i in mini(actors.size(), enemies.size()):
			if not actors[i] is Dictionary: continue
			var saved = actors[i]
			var foe = enemies[i]
			if not saved.get("alive", true):
				foe.alive = false
				foe.collision_layer = 0
				foe.hide()
			else:
				foe.health = clampf(float(saved.get("health", foe.health)), 1, foe.health)
				if saved.get("position") is Array and saved.position.size() == 2:
					foe.position = Vector3(float(saved.position[0]), 0, float(saved.position[1]))
					foe.reset_physics_interpolation()
	var residents = data.get("people", {})
	if residents is Dictionary:
		for id in residents:
			if not people.has(id) or not residents[id] is Dictionary: continue
			var saved = residents[id]
			if saved.get("position") is Array and saved.position.size() == 3:
				people[id].position = Vector3(saved.position[0], saved.position[1], saved.position[2])
				people[id].rotation.y = float(saved.get("yaw", 0))
				people[id].reset_physics_interpolation()
	if data.get("actions") is Array: action_log = data.actions

func depart(outcomes: Dictionary = {}) -> void:
	if departing: return
	save_checkpoint()
	var result = CAMPAIGN.mark_departure(next_chapter, outcomes)
	if result != OK:
		save_error = "Отправление не сохранено · " + error_string(result)
		return
	departing = true
	get_tree().root.set_meta("campaign_playing", true)
	get_tree().change_scene_to_file.call_deferred(CAMPAIGN.saved_scene())

func finish_campaign(outcome: String) -> void:
	if departing: return
	save_checkpoint()
	var result = CAMPAIGN.finish(outcome, state)
	if result != OK:
		save_error = "Результат не сохранён · " + error_string(result)
		return
	departing = true
	get_tree().change_scene_to_file.call_deferred("res://epilogue.tscn")

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_R:
			if player_down: get_tree().reload_current_scene()
			return
		if event.keycode == KEY_M and not paused:
			map_large = not map_large
			map_view.position = Vector2(465, 220) if map_large else Vector2(1595, 28)
			map_view.size = Vector2(990, 640) if map_large else Vector2(295, 280)
			map_view.queue_redraw()
			return
	super._unhandled_input(event)
