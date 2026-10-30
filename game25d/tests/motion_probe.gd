extends SceneTree

func _initialize() -> void:
	run.call_deferred()

func skeleton_in(node: Node) -> Skeleton3D:
	if node is Skeleton3D:return node
	for child in node.get_children():
		var found=skeleton_in(child)
		if found:return found
	return null

func run() -> void:
	var actor=load("res://scripts/actor.gd").new();root.add_child(actor);actor.setup("",load("res://assets/characters/worker.glb"))
	actor.animation_tree.active=false
	var skel=skeleton_in(actor);var foot=skel.find_bone("Foot.L");var hand=skel.find_bone("Palm.R")
	var result={}
	for state in ["Walk","Run","SwordSlash"]:
		actor.animator.play(actor.clips[state],0);actor.animator.advance(0);actor.animator.pause()
		var length=actor.animator.get_animation(actor.clips[state]).length
		var rows=[]
		for i in range(25):
			actor.animator.seek(length*i/24.0,true);actor.animator.advance(0);skel.force_update_all_bone_transforms()
			var f=skel.global_transform*skel.get_bone_global_pose(foot).origin;var h=skel.global_transform*skel.get_bone_global_pose(hand).origin
			rows.append({"t":length*i/24.0,"foot":[f.x,f.y,f.z],"hand":[h.x,h.y,h.z]})
		result[state]=rows
	var file=FileAccess.open("H:/game/release/motion-probe-v33.json",FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));file.close()
	quit()
