extends RefCounted
## Analytic two-bone arm contact. World targets; local pose rotations only.
var skeleton: Skeleton3D
var weight := 0.0
var last_targets: Dictionary = {}
var errors: Dictionary = {}
var tools: Array = []

func find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D:return node
	for child in node.get_children():
		var result=find_skeleton(child)
		if result:return result
	return null

func find_tools(node: Node) -> void:
	if node is Node3D and "key" in String(node.name).to_lower():tools.append(node)
	for child in node.get_children():find_tools(child)

func position(index: int) -> Vector3:
	return skeleton.global_transform*skeleton.get_bone_global_pose(index).origin

func world_rotation(index: int,desired: Basis,influence: float) -> void:
	var skeleton_basis=skeleton.global_basis.orthonormalized()
	var desired_global=skeleton_basis.inverse()*desired.orthonormalized()
	var parent=skeleton.get_bone_parent(index)
	var parent_basis=skeleton.get_bone_global_pose(parent).basis.orthonormalized() if parent>=0 else Basis.IDENTITY
	# Godot 4 pose rotation is the full local rotation relative to the parent,
	# not a delta multiplied after rest (the old Godot 3 convention).
	var local=parent_basis.inverse()*desired_global
	var original=skeleton.get_bone_pose_rotation(index)
	skeleton.set_bone_pose_rotation(index,original.slerp(local.get_rotation_quaternion().normalized(),influence))
	skeleton.force_update_all_bone_transforms()

func solve_arm(side: String,target: Vector3,pole: Vector3,influence: float) -> void:
	var upper=skeleton.find_bone("UpperArm."+side);var lower=skeleton.find_bone("LowerArm."+side);var hand=skeleton.find_bone("Palm."+side)
	if upper<0 or lower<0 or hand<0:return
	var shoulder=position(upper);var elbow=position(lower);var wrist=position(hand)
	var length_a=shoulder.distance_to(elbow);var length_b=elbow.distance_to(wrist)
	var difference=target-shoulder;var distance=clampf(difference.length(),absf(length_a-length_b)+.002,length_a+length_b-.002)
	if difference.length()<.001:return
	var direction=difference.normalized();var sideways=pole-shoulder
	sideways=(sideways-direction*sideways.dot(direction)).normalized()
	if sideways.length()<.01:sideways=direction.cross(Vector3.UP).normalized()
	var along=(length_a*length_a-length_b*length_b+distance*distance)/(2*distance)
	var height=sqrt(maxf(0,length_a*length_a-along*along))
	var elbow_target=shoulder+direction*along+sideways*height
	var upper_basis=(skeleton.global_transform*skeleton.get_bone_global_pose(upper)).basis.orthonormalized()
	var upper_swing=Quaternion((elbow-shoulder).normalized(),(elbow_target-shoulder).normalized())
	world_rotation(upper,Basis(upper_swing)*upper_basis,influence)
	elbow=position(lower);wrist=position(hand)
	var lower_basis=(skeleton.global_transform*skeleton.get_bone_global_pose(lower)).basis.orthonormalized()
	var lower_swing=Quaternion((wrist-elbow).normalized(),(target-elbow).normalized())
	world_rotation(lower,Basis(lower_swing)*lower_basis,influence)
	errors[side]=position(hand).distance_to(target)

func apply(actor: Node3D,cart: Node3D,active: bool,delta: float) -> void:
	if not is_instance_valid(skeleton):skeleton=find_skeleton(actor);find_tools(actor)
	if not skeleton:return
	weight=move_toward(weight,1.0 if active else 0.0,delta*6)
	for mesh in tools:
		if is_instance_valid(mesh):mesh.visible=weight<.05
	if weight<=0:return
	skeleton.force_update_all_bone_transforms()
	# Locomotion may lean the chest into a sprint. Pulling handles behind the
	# body needs an upright chest so the near hand remains within arm reach on
	# turns. Keep bone lengths and the lower-body gait unchanged.
	var torso=skeleton.find_bone("Torso")
	if torso>=0:
		var upright=skeleton.global_basis.orthonormalized()*skeleton.get_bone_global_rest(torso).basis.orthonormalized()
		world_rotation(torso,upright,weight)
	if active:
		var leader_local=cart.to_local(actor.global_position)
		var end=1.55 if leader_local.z>=0 else -1.55
		for side in ["L","R"]:
			var shoulder=position(skeleton.find_bone("UpperArm."+side))
			var lateral=.40 if cart.to_local(shoulder).x>=0 else -.40
			last_targets[side]=cart.to_global(Vector3(lateral,1.06,end))
	for side in last_targets:
		var side_sign=1 if side=="L" else -1
		var pole=actor.global_position+actor.global_basis.x*side_sign*.65+Vector3.UP*.8
		solve_arm(side,last_targets[side],pole,weight)
	# A holding left hand, matching the authored right grip. No length scaling.
	for pair in [["MiddleHand.L",.2],["Fingers.L",1.6]]:
		var index=skeleton.find_bone(pair[0])
		if index>=0:
			var pose=skeleton.get_bone_rest(index).basis.get_rotation_quaternion()*Quaternion(Vector3.RIGHT,pair[1])
			skeleton.set_bone_pose_rotation(index,skeleton.get_bone_pose_rotation(index).slerp(pose,weight))
	skeleton.force_update_all_bone_transforms()
