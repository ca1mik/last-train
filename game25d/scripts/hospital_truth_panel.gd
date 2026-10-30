extends Control
var transport: RefCounted
var body: Label
var choices: Array=[]
var close_button: Button
func _init(owner: RefCounted) -> void:transport=owner
func _ready() -> void:
	process_mode=Node.PROCESS_MODE_ALWAYS;z_index=150;set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var shade=ColorRect.new();add_child(shade);shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);shade.color=Color(.025,.06,.065,.96)
	var title=Label.new();add_child(title);title.position=Vector2(245,180);title.text="В вагоне";title.add_theme_font_size_override("font_size",40)
	body=Label.new();add_child(body);body.position=Vector2(245,260);body.size=Vector2(1430,280);body.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;body.add_theme_font_size_override("font_size",28)
	for i in range(2):
		var button=Button.new();add_child(button);button.position=Vector2(245,590+i*95);button.size=Vector2(1430,74);button.add_theme_font_size_override("font_size",25);button.pressed.connect(select.bind(i));choices.append(button)
	close_button=Button.new();add_child(close_button);close_button.position=Vector2(245,815);close_button.size=Vector2(480,65);close_button.text="Вернуться · Esc";close_button.add_theme_font_size_override("font_size",25);close_button.pressed.connect(close)
	visible=false
func open() -> void:
	if visible or transport.truth!="":return
	transport.game.set_paused(true);transport.game.pause_overlay.hide();visible=true
	body.text="Нина: Ты сказал: «Если выйдем». Ты уже тогда знал, что сюда можно вернуться?\nАртём: Нет.\nНина: Я не про сегодня."
	choices[0].text="1 · Я видел платформу. И не остановился."
	choices[1].text="2 · Я боялся, что состав смоет вместе со всеми."
	for button in choices:button.show()
	choices[0].grab_focus()
func select(index: int) -> void:transport.choose("admit" if index==0 else "defend")
func show_reply(text: String) -> void:
	body.text=text
	for button in choices:button.hide()
	close_button.grab_focus()
func close() -> void:
	visible=false;transport.game.set_paused(false)
func _input(event: InputEvent) -> void:
	if not visible:return
	if event is InputEventKey and event.pressed and not event.echo:
		var code=event.physical_keycode if event.physical_keycode!=0 else event.keycode
		if code in [KEY_1,KEY_2] and transport.truth=="":select(0 if code==KEY_1 else 1)
		elif code==KEY_ESCAPE:close()
		get_viewport().set_input_as_handled()
