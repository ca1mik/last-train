extends Control
var game: Node3D
func point(p: Vector3) -> Vector2:
	return Vector2(18 + (p.x - game.bounds.position.x) / game.bounds.size.x * (size.x - 36), 40 + (p.z - game.bounds.position.y) / game.bounds.size.y * (size.y - 65))
func _draw() -> void:
	if not is_instance_valid(game) or not is_instance_valid(game.hero): return
	var style = StyleBoxFlat.new()
	style.bg_color = Color(.04, .075, .08, .94)
	style.border_color = Color("738779")
	style.set_border_width_all(1)
	draw_style_box(style, Rect2(Vector2.ZERO, size))
	var font = ThemeDB.fallback_font
	draw_string(font, Vector2(14, 25), "СХЕМА · M", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color("d1c7a7"))
	for rect in game.obstacles:
		var a = point(Vector3(rect.position.x, 0, rect.position.y))
		var b = point(Vector3(rect.end.x, 0, rect.end.y))
		draw_rect(Rect2(a, b-a), Color("435854"))
	var train = point(game.start_point)
	draw_circle(train, 5, Color("d8b57e"))
	if game.map_large: draw_string(font, train + Vector2(7,-6), "ПОЕЗД", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color("d8b57e"))
	for option in game.get_options():
		var marker = point(option[1])
		draw_arc(marker, 4, 0, TAU, 12, Color("b2c2a2"), 2)
		if game.map_large: draw_string(font, marker + Vector2(6, -5), String(option[2]).left(45), HORIZONTAL_ALIGNMENT_LEFT, 330, 14, Color("cbd5bc"))
	for id in game.people: draw_circle(point(game.people[id].position), 3, Color("9faed4"))
	draw_circle(point(game.hero.position), 5, Color("fff0c6"))
