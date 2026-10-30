extends Control
const CAMPAIGN=preload("res://scripts/campaign.gd")

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var background=ColorRect.new();add_child(background);background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);background.color=Color("14272b")
	label("ПОСЛЕДНИЙ РЕЙС",Vector2(130,100),26,Color("9db5a8"))
	label("Остановки",Vector2(130,155),52,Color("e5d8b8"))
	label("Продолжите кампанию или отправьтесь в отдельную вылазку.",Vector2(133,230),23,Color("a9bab0"))
	card("Больничная ветка","Заросший двор, служебная галерея и путь к убежищу.",Vector2(130,330),"res://hospital.tscn",Color("769781"))
	card("Лесной полустанок","Тихий обход или шумный привод. Открой сигнал и путь назад.",Vector2(990,330),"res://forest.tscn",Color("82955b"))
	card("Грузовой двор","Промытая промплощадка, цистерны и открытые переходы.",Vector2(130,615),"res://wasteland.tscn",Color("aa9567"))
	card("Продолжить кампанию","Вернуться к сохранённой остановке основной истории.",Vector2(990,615),CAMPAIGN.saved_scene(),Color("b49f73"),true)
	label("WASD — движение · ЛКМ — удар · Пробел — уклонение · удерживать E — действие",Vector2(133,967),21,Color("a9bab0"))
	label("Выбор отдельной остановки сохраняет положение кампании. Полная история ещё в разработке.",Vector2(133,1005),19,Color("829b92"))

func label(value: String,pos: Vector2,size: int,color: Color) -> Label:
	var node=Label.new();add_child(node);node.position=pos;node.text=value;node.add_theme_font_size_override("font_size",size);node.add_theme_color_override("font_color",color);return node

func card(title: String,description: String,pos: Vector2,scene: String,color: Color,campaign_mode:=false) -> void:
	var button=Button.new();add_child(button);button.position=pos;button.size=Vector2(800,230);button.mouse_default_cursor_shape=Control.CURSOR_POINTING_HAND
	var normal=StyleBoxFlat.new();normal.bg_color=Color("203a3c");normal.border_color=color.darkened(.3);normal.set_border_width_all(2);normal.set_corner_radius_all(7);button.add_theme_stylebox_override("normal",normal)
	var hover=normal.duplicate();hover.bg_color=Color("2b4947");hover.border_color=color;button.add_theme_stylebox_override("hover",hover);button.add_theme_stylebox_override("focus",hover);button.add_theme_stylebox_override("pressed",hover)
	button.pressed.connect(open_location.bind(scene,campaign_mode))
	var heading=label(title,pos+Vector2(32,33),34,color);heading.mouse_filter=Control.MOUSE_FILTER_IGNORE
	var text=label(description,pos+Vector2(32,98),22,Color("c0cec1"));text.size=Vector2(725,68);text.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;text.mouse_filter=Control.MOUSE_FILTER_IGNORE
	var action=label("Отправиться →",pos+Vector2(32,174),22,Color("e6d6ae"));action.mouse_filter=Control.MOUSE_FILTER_IGNORE

func open_location(scene: String,campaign_mode:=false) -> void:
	get_tree().root.set_meta("campaign_playing",campaign_mode)
	var result=get_tree().change_scene_to_file(scene)
	if result!=OK:push_error("Cannot open location: "+error_string(result))
