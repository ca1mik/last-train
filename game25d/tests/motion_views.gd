extends SceneTree
func _initialize() -> void:start.call_deferred()
func start() -> void:
	var game=load("res://tests/motion_world.gd").new();root.add_child(game);game.paused=true
	for foe in game.enemies:foe.queue_free()
	game.enemies.clear();game.radio.visible=false;game.hero.review_motion=true;game.camera.size=5.5
	var center=game.hero.position+Vector3.UP*.8;game.camera.position=center+game.camera_offset
	var output="H:/game/release/motion-v038/views";DirAccess.make_dir_recursive_absolute(output)
	var definitions=[["idle","Idle",.4,1.0],["run","Run",.15,1.0],["dodge-early","Dodge",.13,game.hero.animator.get_animation(game.hero.clips.Dodge).length/.52],["dodge-mid","Dodge",.26,game.hero.animator.get_animation(game.hero.clips.Dodge).length/.52],["hurt","Hurt",.12,1.2],["attack","SwordSlash",.18,2.4],["death-end","Death",2.05,1.2]]
	for angle in range(0,360,45):
		for definition in definitions:
			# Rebuild only the fixture's graph so every direction samples the same
			# phase. Idle/locomotion clocks otherwise continue between staged shots.
			game.hero.animation_tree.active=false;game.hero.animation_tree.queue_free()
			if game.hero.animator.has_animation_library("rail"):game.hero.animator.remove_animation_library("rail")
			game.hero.build_animation_tree();game.hero.current_clip=""
			game.hero.face(Vector3(sin(deg_to_rad(angle)),0,cos(deg_to_rad(angle))),.016,true)
			game.hero.action_weight=0;game.hero.action_remaining=0;game.hero.locomotion_weight=0;game.hero.animation_speed=0
			game.hero.animation_tree.set("parameters/action_blend/blend_amount",0.0)
			game.hero.animation_tree.set("parameters/movement/blend_amount",0.0)
			game.hero.play(definition[1],definition[3],true)
			if definition[1]=="Run":game.hero.locomotion_weight=1;game.hero.update_motion(.2)
			game.hero.animation_tree.advance(0);game.hero.advance_pose(definition[2])
			game.objective.text="Pose fixture · "+str(angle)+"° · "+definition[0]
			for i in range(2):await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(output.path_join("%03d-%s.png"%[angle,definition[0]]))
	print("MOTION_VIEWS 56 fixture frames captured")
	game.queue_free();await process_frame;await process_frame;quit()
