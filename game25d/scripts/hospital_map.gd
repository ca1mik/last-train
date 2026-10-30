extends Control
var game: Node3D

func _draw() -> void:
	if not is_instance_valid(game):return
	var box=StyleBoxFlat.new();box.bg_color=Color(.04,.09,.11,.88);box.border_color=Color("52625d");box.set_border_width_all(1);draw_style_box(box,Rect2(Vector2.ZERO,size))
	var factor=minf((size.x-24)/88.0,(size.y-38)/70.0)
	for zone in game.zones:
		var rect: Rect2=zone.rect
		draw_rect(Rect2(point(rect.position,factor),rect.size*factor),Color("6b7466") if game.visited.has(zone.id) else Color("354448"))
	draw_circle(point(Vector2(game.hero.position.x,game.hero.position.z),factor),4,Color("eee0b5"))
	var target: Vector3=game.objective_position();draw_arc(point(Vector2(target.x,target.z),factor),5,0,TAU,16,Color("db9a55"),2)
	if game.mission==0 and not game.has_winch and not game.has_jumper:draw_arc(point(Vector2(game.WINCH.x,game.WINCH.z),factor),5,0,TAU,16,Color("8dbcb3"),2)

func point(p: Vector2,factor: float) -> Vector2:return (p+Vector2(40,37))*factor+Vector2(12,20)
