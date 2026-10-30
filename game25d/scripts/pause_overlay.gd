extends Control
var game: Node3D
var journal: RichTextLabel
var resume: Button

func _init(owner: Node3D) -> void:game=owner

func _ready() -> void:
	process_mode=Node.PROCESS_MODE_ALWAYS;z_index=100
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);mouse_filter=Control.MOUSE_FILTER_STOP
	var shade=ColorRect.new();add_child(shade);shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);shade.color=Color(.025,.06,.065,.94)
	panel(Rect2(110,100,730,885));panel(Rect2(890,100,920,885))
	label("Пауза",Vector2(155,135),42,Color("e6d6b3"))
	label("Мир ждёт. Esc или J — продолжить.",Vector2(158,197),21,Color("9fb5a5"))
	resume=button("Продолжить",Vector2(155,265),func():game.set_paused(false))
	button("Повторить контрольную точку",Vector2(155,350),func():game.set_paused(false);game.get_tree().reload_current_scene())
	label("Громкость",Vector2(158,465),27,Color("d9cfb3"))
	var names={"Master":"Общая","SFX":"Действия и угрозы","Ambience":"Окружение","Voice":"Голоса"}
	var row=0
	for bus in names:
		label(names[bus],Vector2(160,522+row*70),20,Color("b5c3b3"))
		var slider=HSlider.new();add_child(slider);slider.position=Vector2(415,526+row*70);slider.size=Vector2(240,28);slider.min_value=0;slider.max_value=100;slider.step=1;slider.value=float(game.preferences.values[bus])*100
		var amount=label(str(int(slider.value))+"%",Vector2(680,522+row*70),20,Color("d9cfb3"))
		slider.value_changed.connect(volume_changed.bind(bus,amount));row+=1
	button("Выбрать остановку",Vector2(155,840),func():game.set_paused(false);game.get_tree().change_scene_to_file("res://locations.tscn"))
	label("Журнал",Vector2(935,138),36,Color("e6d6b3"))
	journal=RichTextLabel.new();add_child(journal);journal.position=Vector2(935,215);journal.size=Vector2(825,710);journal.bbcode_enabled=false;journal.selection_enabled=true;journal.add_theme_font_size_override("normal_font_size",23);journal.add_theme_color_override("default_color",Color("d6dccb"));journal.scroll_active=true
	visible=false

func panel(rect: Rect2) -> void:
	var box=Panel.new();add_child(box);box.position=rect.position;box.size=rect.size
	var style=StyleBoxFlat.new();style.bg_color=Color("1d3335");style.border_color=Color("62776a");style.set_border_width_all(1);style.set_corner_radius_all(7);box.add_theme_stylebox_override("panel",style)

func label(text: String,pos: Vector2,size: int,color: Color) -> Label:
	var node=Label.new();add_child(node);node.position=pos;node.text=text;node.add_theme_font_size_override("font_size",size);node.add_theme_color_override("font_color",color);node.mouse_filter=Control.MOUSE_FILTER_IGNORE;return node

func button(text: String,pos: Vector2,action: Callable) -> Button:
	var node=Button.new();add_child(node);node.position=pos;node.size=Vector2(640,62);node.text=text;node.add_theme_font_size_override("font_size",23);node.pressed.connect(action)
	var style=StyleBoxFlat.new();style.bg_color=Color("304c46");style.set_corner_radius_all(5);node.add_theme_stylebox_override("normal",style)
	return node

func volume_changed(value: float,bus: String,amount: Label) -> void:
	game.preferences.set_volume(bus,value/100);amount.text=str(int(value))+"%"

func show_book() -> void:
	journal.text=game.dialogue_book.text_for(game.dialogue_scope());visible=true;resume.grab_focus()

func _unhandled_input(event: InputEvent) -> void:
	if not game.paused:return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode==KEY_ESCAPE or event.keycode==KEY_J or event.physical_keycode==KEY_J:
			get_viewport().set_input_as_handled();game.set_paused(false)
		elif event.keycode==KEY_F2:
			get_viewport().set_input_as_handled();game.set_paused(false);get_tree().change_scene_to_file("res://locations.tscn")
