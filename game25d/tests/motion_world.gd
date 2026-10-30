extends "res://scripts/main.gd"
## Isolated capture ground, not a new campaign location or finished environment.
func build_station() -> void:
	var floor_node=block(Vector3(0,-.15,0),Vector3(200,.3,200),Color("607069"),true)
	var material=ShaderMaterial.new();material.shader=load("res://shaders/expedition_floor.gdshader");material.set_shader_parameter("base_color",Color("607069"));material.set_shader_parameter("tile_size",1.0);mesh_in(floor_node).material_override=material

func setup_navigation() -> void:
	nav.region=Rect2i(-100,-100,200,200);nav.cell_size=Vector2(.5,.5);nav.update()

func setup_world() -> void:
	super.setup_world()
	for node in get_children():
		if node is WorldEnvironment:node.environment.ambient_light_energy=.52;node.environment.fog_density=.002

func interactions(_delta: float) -> void:
	help.text="";work_bar.visible=false

func follow_camera(delta: float) -> void:
	# The legacy arena camera is clamped to its 22x24-metre room. This capture
	# ground must use the actual expedition's unrestricted follow behaviour.
	var target=hero.get_global_transform_interpolated().origin+Vector3.UP*.8
	camera.position=camera.position.lerp(target+camera_offset,1-exp(-7*minf(delta,.1)));update_occlusion(delta)
