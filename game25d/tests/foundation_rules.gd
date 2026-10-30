extends SceneTree
var checks:=0
var failures: Array=[]
var game: Node3D
func _initialize() -> void:start.call_deferred()
func check(ok: bool,message: String) -> void:
	checks+=1
	if not ok:failures.append(message);push_error(message)
func frames(n: int) -> void:
	for i in range(n):await physics_frame
func press(code: int) -> void:
	var event=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true;root.push_input(event,true)
	var up=InputEventKey.new();up.keycode=code;up.physical_keycode=code;up.pressed=false;root.push_input(up,true)
func discard() -> void:
	game.set_paused(false);game.queue_free();await frames(3)
func start() -> void:
	var journal_path="user://journal-qa-foundation-rules-v045.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--save-slot="):journal_path="user://journal-"+arg.trim_prefix("--save-slot=").get_file()
	var stale=FileAccess.open(journal_path,FileAccess.WRITE);stale.store_string('[{"scope":"campaign","text":"OLD FUTURE SPOILER"}]');stale.close()
	game=load("res://expedition.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true;await frames(3)
	check(not game.dialogue_book.text_for("campaign").contains("OLD FUTURE SPOILER"),"fresh campaign clears earlier-run knowledge without clearing on scene reload")
	for actor in game.enemies:actor.queue_free()
	game.enemies.clear();await frames(3)
	game.hero.position=Vector3(-8,0,4);game.hero.reset_physics_interpolation()
	var watcher=game.spawn_actor("walker",Vector3(-4,0,4));await frames(3)
	check(not game.visible_between(watcher.position,game.hero.position),"fixture uses real partition between silent hero and foe")
	game.enemy_tick(watcher,.016)
	check(watcher.awareness_left==0 and watcher.path.is_empty(),"silent hidden hero does not cause exact-position pursuit")
	game.emit_noise(game.hero.position,10,4);game.enemy_tick(watcher,.016)
	check(watcher.investigate_left>0 and watcher.investigate_position.distance_to(game.hero.position)<.01,"audible event supplies a concrete investigation point")
	check(not watcher.path.is_empty() and watcher.path[-1].distance_to(game.hero.position)<.7,"sound investigation actually navigates around the wall")
	watcher.investigate_left=0;watcher.repath=0;game.hero.position=Vector3(-4,0,8);game.hero.reset_physics_interpolation();await frames(2);game.enemy_tick(watcher,.016)
	check(watcher.awareness_left>0 and watcher.last_known_position.distance_to(game.hero.position)<.01,"visible hero is acquired")
	var seen=watcher.last_known_position;game.hero.position=Vector3(-8,0,4);game.hero.reset_physics_interpolation();watcher.repath=0;await frames(2);game.enemy_tick(watcher,.016)
	check(watcher.last_known_position==seen,"loss of sight preserves observed location instead of tracking through wall")
	check(not watcher.path.is_empty() and watcher.path[-1].distance_to(seen)<.7,"lost target route ends at last known location")
	watcher.clocks(4);watcher.repath=0;game.enemy_tick(watcher,.016)
	check(watcher.awareness_left==0 and watcher.path.is_empty(),"expired awareness allows return to home")
	game.perform_action("generator");game.open_pharmacy("power");await discard()
	game=load("res://expedition.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true;await frames(3)
	var restored=0
	for actor in game.enemies:
		if actor.has_meta("hears_generator") and actor.home.distance_to(game.GENERATOR)<.01:restored+=1
	check(game.power_on and restored==2,"reload restores both generator-responsive actors as well as the power flag")
	for actor in game.enemies:actor.queue_free()
	game.enemies.clear();await frames(3)
	game.dialogue_queue.clear();game.radio_time=0;game.active_dialogue=""
	game.say("QA · важная информация",2);game.say("QA · получена перевязка",1,0);game.update_dialogue(.01)
	check(game.radio.text=="QA · важная информация","optional pickup cannot overwrite active important message")
	check(game.dialogue_book.text_for(game.dialogue_scope()).contains("QA · получена перевязка"),"queued optional message is retained in journal")
	game.update_dialogue(2.1);check(game.radio.text=="QA · получена перевязка","queued message is shown after active message")
	var interruption=game.spawn_actor("walker",game.hero.position+Vector3(0,0,.8));await frames(2)
	var reading_left=game.radio_time;game.update_dialogue(.6)
	check(not game.radio.visible and game.radio_time==reading_left,"combat hides story text without consuming its reading time")
	interruption.queue_free();game.enemies.clear();await frames(2);game.update_dialogue(.1)
	check(game.radio.visible and absf(game.radio_time-reading_left+.1)<.001,"remaining dialogue resumes after danger clears")
	game.hero.alive=false;game.update_dialogue(.2)
	check(not game.radio.visible,"death does not leave dialogue over retry interface");game.hero.alive=true
	game.say("QA · старая инструкция",2,0);game.say("QA · новая инструкция",2,0)
	check(game.dialogue_queue.size()==1 and game.dialogue_queue[0].text=="QA · новая инструкция","context instructions replace pending stale instructions")
	check(game.dialogue_book.text_for(game.dialogue_scope()).contains("QA · старая инструкция"),"replaced instruction is still retrievable")
	var marker=Node3D.new();game.add_child(marker);game.paused=false
	var tween=game.create_tween();tween.tween_property(marker,"position:x",10.0,1.0);await frames(3)
	press(KEY_ESCAPE);var held_x=marker.position.x;var held_clock=game.clock
	check(game.paused and paused and game.pause_overlay.visible,"Escape opens visible pause and pauses tree")
	await create_timer(.22,true).timeout
	check(absf(marker.position.x-held_x)<.0001 and game.clock==held_clock,"world clock and game-bound tween freeze during pause")
	press(KEY_ESCAPE);await frames(3)
	check(not game.paused and not paused and not game.pause_overlay.visible,"Escape resumes through always-active overlay")
	check(marker.position.x>held_x,"paused tween resumes after leaving pause")
	press(KEY_J);check(paused and game.pause_overlay.journal.text.contains("QA · важная информация"),"J exposes journal while safely pausing world")
	press(KEY_J);check(not paused,"J closes journal and resumes")
	game.preferences.set_volume("SFX",.37)
	check(absf(db_to_linear(AudioServer.get_bus_volume_db(AudioServer.get_bus_index("SFX")))-.37)<.001,"volume setting reaches actual SFX bus")
	game.paused=true;game.hero.position=Vector3(-4,0,0);game.hero.health=100;game.hero.hurt_left=0;game.hero.dash_left=0
	var attacker=game.spawn_actor("walker",Vector3(-4,0,.8));attacker.phase="windup";attacker.phase_left=.001;attacker.target_direction=Vector3.FORWARD;await frames(3)
	game.enemy_tick(attacker,.016)
	check(game.hero.health==100 and attacker.phase=="strike" and attacker.current_clip=="Punch","windup starts attack animation without immediate damage")
	attacker.clocks(.16);attacker.advance_pose(.16);game.enemy_tick(attacker,.16)
	check(game.hero.health==100,"damage waits for active contact phase")
	attacker.clocks(.03);attacker.advance_pose(.03);game.enemy_tick(attacker,.03)
	check(game.hero.health==76 and attacker.phase=="recover" and attacker.action_elapsed>=.18,"contact damage occurs after visible strike begins")
	game.hero.hurt_left=0;attacker.phase="strike";attacker.phase_left=.01;attacker.hurt_left=0;attacker.take_hit(10,Vector3.BACK);game.enemy_tick(attacker,.016)
	check(game.hero.health==76,"interrupted strike cannot apply its deferred hit")
	await discard()
	game=load("res://hospital.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true;await frames(3)
	check(absf(float(game.preferences.values.SFX)-.37)<.001,"preferences survive real scene reconstruction")
	check(game.dialogue_book.text_for("campaign").contains("QA · важная информация"),"journal survives real scene reconstruction")
	game.perform_action("refuge");check(not game.refuge_heard,"early shelter conversation is not post-route confirmation")
	game.perform_action("jumper");game.perform_action("winch");game.perform_action("install")
	check(game.objective_position().distance_to(game.FEED_A)<.01 and game.objective.text.contains("обе ветви"),"owning both tools does not hijack started electrical task")
	game.save_checkpoint();await discard()
	game=load("res://hospital.tscn").instantiate();root.add_child(game);current_scene=game;game.paused=true;await frames(3)
	check(game.work_branch=="power" and game.objective_position().distance_to(game.FEED_A)<.01,"chosen work branch survives reload")
	game.perform_action("feed_a");game.perform_action("feed_b");game.perform_action("test");game.perform_action("drive");game.perform_action("refuge")
	check(game.refuge_heard and not game.objective.text.contains("связаться"),"shelter objective acknowledges completed contact and advances to receiving work")
	var repeatable=false
	for option in game.options():
		if option[0]=="refuge":repeatable=true
	check(not repeatable,"completed shelter contact is not left as mandatory repeated action")
	var before=FileAccess.get_file_as_string(game.save_path);game.perform_action("refuge")
	check(FileAccess.get_file_as_string(game.save_path)==before,"repeated direct contact does not write another checkpoint")
	check(game.preferences.path.contains("qa-") and game.dialogue_book.path.contains("qa-"),"QA runs keep user settings and journal isolated")
	await discard()
	var file=FileAccess.open(preload("res://tests/qa_report.gd").path("H:/game/release/foundation-v045/rules.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures,"scope":"real partitions/save reconstruction and actual Esc/J; staged combat/quest fixtures; not human playtest"},"  "));file.close()
	var until=Time.get_ticks_msec()+500
	while Time.get_ticks_msec()<until:await process_frame
	print("FOUNDATION_RULES ",checks," failures=",failures);quit(0 if failures.is_empty() else 1)
