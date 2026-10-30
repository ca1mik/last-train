extends Control
var game: Node3D
func point(p: Vector3) -> Vector2:
	return Vector2(24+(p.x+28)/56*(size.x-48),42+(p.z+26)/50*(size.y-72))
func _draw() -> void:
	if not is_instance_valid(game) or not is_instance_valid(game.hero):return
	var style=StyleBoxFlat.new();style.bg_color=Color(.055,.1,.085,.94);style.border_color=Color("7b8971");style.set_border_width_all(1)
	draw_style_box(style,Rect2(Vector2.ZERO,size))
	var font=ThemeDB.fallback_font
	draw_string(font,Vector2(16,25),"СХЕМА ПУТЕЙ · M",HORIZONTAL_ALIGNMENT_LEFT,-1,17,Color("c6c9a7"))
	var paths=[[game.start_point,Vector3(-15,0,3),game.goals[0],Vector3(1,0,-19),game.goals[1]],[game.start_point,game.GENERATOR,Vector3(0,0,-7),game.goals[1]],[game.goals[1],Vector3(15,0,8),game.CACHE,game.start_point]]
	for path in paths:
		for i in range(path.size()-1):draw_line(point(path[i]),point(path[i+1]),Color("6b7d63"),3)
	draw_line(point(Vector3(-10,0,4)),point(Vector3(-2.2,0,4)),Color("ae9672"),3)
	draw_line(point(Vector3(2.2,0,4)),point(Vector3(11,0,4)),Color("ae9672"),3)
	if not game.trial_open:draw_line(point(Vector3(-2.2,0,4)),point(Vector3(2.2,0,4)),Color("d98868"),4)
	for landmark in [[game.start_point,"ПОЕЗД"],[game.goals[0],"БУДКА"],[game.goals[1],"СИГНАЛ"],[game.GENERATOR,"МОТОР"]]:
		var pos=point(landmark[0]);draw_circle(pos,4,Color("c4b583"));draw_string(font,pos+Vector2(7,-6),landmark[1],HORIZONTAL_ALIGNMENT_LEFT,-1,15 if game.map_large else 11,Color("dbd1ac"))
	if game.note_read or game.hero.position.distance_to(game.CACHE)<10:draw_circle(point(game.CACHE),4,Color("91b899"))
	draw_circle(point(game.hero.position),5,Color("fff0c6"));draw_arc(point(game.hero.position),8,0,TAU,16,Color("b7c3a5"),1)
