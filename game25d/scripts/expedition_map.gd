extends Control
## A diagram of the actual walkable rectangles, not a substitute for scene depth.
var game: Node3D

func _draw() -> void:
	if not is_instance_valid(game):return
	draw_style_box(panel(),Rect2(Vector2.ZERO,size))
	var scale_factor=minf((size.x-24)/98.0,(size.y-38)/90.0)
	var offset=Vector2(40,43)
	for zone in game.zones:
		var rect: Rect2=zone.rect
		draw_rect(Rect2((rect.position+offset)*scale_factor+Vector2(12,20),rect.size*scale_factor),Color("5b6c6b") if game.visited.has(zone.id) else Color("354448"))
	var player_point=(Vector2(game.hero.position.x,game.hero.position.z)+offset)*scale_factor+Vector2(12,20)
	draw_circle(player_point,4,Color("eee0b5"))
	var target: Vector3=game.objective_position()
	var target_point=(Vector2(target.x,target.z)+offset)*scale_factor+Vector2(12,20)
	draw_arc(target_point,5,0,TAU,16,Color("db9a55"),2)
	if game.mission==0 and not game.has_stopper and not game.power_on:
		var alternative=(Vector2(game.GENERATOR.x,game.GENERATOR.z)+offset)*scale_factor+Vector2(12,20)
		draw_arc(alternative,5,0,TAU,16,Color("8dbcb3"),2)
	if game.cart_loaded and game.mission<3:
		var cart_point=(Vector2(game.cart.position.x,game.cart.position.z)+offset)*scale_factor+Vector2(12,20)
		draw_rect(Rect2(cart_point-Vector2(3,3),Vector2(6,6)),Color("8dceba"))

func panel() -> StyleBoxFlat:
	var box=StyleBoxFlat.new();box.bg_color=Color(.04,.09,.11,.88)
	box.border_color=Color("52625d");box.set_border_width_all(1);box.set_corner_radius_all(5)
	return box
