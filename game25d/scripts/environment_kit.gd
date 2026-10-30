extends RefCounted
## Original metric 3D kit. No new external assets; foliage is not collision art.
var game: Node3D
var rng:=RandomNumberGenerator.new()
var grass_points: Array[Vector3]=[]
var foliage_materials: Dictionary={}
var foliage_count:=0

func _init(owner: Node3D,seed_value:=4401) -> void:
	game=owner;rng.seed=seed_value

func leaf_material(color: Color) -> ShaderMaterial:
	var key=str(color)
	if not foliage_materials.has(key):
		var material=ShaderMaterial.new();material.shader=load("res://shaders/foliage.gdshader");material.set_shader_parameter("leaf_color",color);foliage_materials[key]=material
	return foliage_materials[key]

func mesh(shape: Mesh,pos: Vector3,scale_value: Vector3,color: Color,leaves:=false) -> MeshInstance3D:
	var node=MeshInstance3D.new();game.add_child(node);node.mesh=shape;node.position=pos;node.scale=scale_value
	node.material_override=leaf_material(color) if leaves else game.mat(color,.9)
	if leaves:game.occluder_candidates.append(node);foliage_count+=1
	return node

func cone(pos: Vector3,radius: float,height: float,color: Color,leaves:=false) -> MeshInstance3D:
	var shape=CylinderMesh.new();shape.top_radius=radius*.08;shape.bottom_radius=radius;shape.height=height;shape.radial_segments=9
	return mesh(shape,pos,Vector3.ONE,color,leaves)

func stone(pos: Vector3,size: Vector3,color:=Color("65695a"),solid:=false) -> void:
	var shape=SphereMesh.new();shape.radial_segments=7;shape.rings=3
	var node=mesh(shape,pos+Vector3.UP*size.y*.35,size,color);node.rotation.y=rng.randf()*TAU
	if solid:blocker(pos,Vector2(size.x*.75,size.z*.75),size.y)

func blocker(pos: Vector3,footprint: Vector2,height: float) -> void:
	var body=StaticBody3D.new();game.add_child(body);body.position=pos;body.collision_layer=1
	var collision=CollisionShape3D.new();body.add_child(collision);var shape=BoxShape3D.new();shape.size=Vector3(footprint.x,height,footprint.y);collision.shape=shape;collision.position.y=height*.5
	game.obstacles.append(Rect2(Vector2(pos.x,pos.z)-footprint*.5,footprint).grow(.40))

func tree(pos: Vector3,pine:=false,height:=5.3) -> void:
	var bark=Color("544b3b") if pine else Color("b8b5a0")
	var trunk_height=height*.68
	cone(pos+Vector3.UP*trunk_height*.5,.19,trunk_height,bark)
	blocker(pos,Vector2(.40,.40),trunk_height)
	if pine:
		for i in range(3):
			var radius=1.65-i*.38
			cone(pos+Vector3.UP*(height*.47+i*height*.17),radius,height*.43,Color("354b39").lightened(i*.035),true)
	else:
		for i in range(4):
			var direction=Vector3(cos(i*2.4),0,sin(i*2.4))
			game.tube(pos+Vector3.UP*height*.32,pos+direction*.8+Vector3.UP*(height*.64+i*.16),.07,bark)
			var sphere=SphereMesh.new();sphere.radial_segments=9;sphere.rings=5
			mesh(sphere,pos+direction*.65+Vector3.UP*(height*.68+i*.18),Vector3(2.1,1.55,2.0)*rng.randf_range(.83,1.14),Color("526140").lightened(i*.018),true)
		for i in range(4):
			var scar=game.block(pos+Vector3(.0,.65+i*.43,.18),Vector3(.18,.07,.015),Color("55574a"));scar.rotation.y=i*.7
	grass_patch(Vector2(pos.x,pos.z),Vector2(3,3),20)

func bush(pos: Vector3,radius:=.7) -> void:
	for i in range(3):
		var shape=SphereMesh.new();shape.radial_segments=7;shape.rings=3
		mesh(shape,pos+Vector3((i-1)*radius*.45,radius*.45,rng.randf_range(-.25,.25)),Vector3(radius*1.4,radius,radius*1.1),Color("47573a").lightened(i*.025),true)

func grass_patch(center: Vector2,extents: Vector2,count: int) -> void:
	for i in range(count):grass_points.append(Vector3(center.x+rng.randf_range(-extents.x*.5,extents.x*.5),.04,center.y+rng.randf_range(-extents.y*.5,extents.y*.5)))

func finish_grass() -> void:
	if grass_points.is_empty():return
	var surface=SurfaceTool.new();surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(3):
		var a=i*PI/3;var side=Vector3(cos(a),0,sin(a))*.065
		for point in [-side,side,Vector3(.06,.36,.035)]:surface.set_color(Color("8a9670") if point.y>0 else Color("4a5b3b"));surface.add_vertex(point)
	surface.generate_normals()
	var instances=MultiMesh.new();instances.transform_format=MultiMesh.TRANSFORM_3D;instances.mesh=surface.commit();instances.instance_count=grass_points.size()
	for i in grass_points.size():instances.set_instance_transform(i,Transform3D(Basis(Vector3.UP,rng.randf()*TAU).scaled(Vector3.ONE*rng.randf_range(.65,1.5)),grass_points[i]))
	var node=MultiMeshInstance3D.new();game.add_child(node);node.multimesh=instances;node.material_override=leaf_material(Color("6a7850"))

func fence(a: Vector3,b: Vector3) -> void:
	var length=a.distance_to(b);var direction=(b-a).normalized();var count=maxi(1,ceili(length/2))
	for i in range(count+1):
		var p=a.lerp(b,float(i)/count);game.block(p+Vector3.UP*.65,Vector3(.09,1.3,.09),Color("667569"))
	for y in [.45,.98]:game.tube(a+Vector3.UP*y,b+Vector3.UP*y,.025,Color("6d7c72"))
	blocker((a+b)*.5,Vector2(absf(b.x-a.x)+.12,absf(b.z-a.z)+.12),1.3)

func path_strip(a: Vector3,b: Vector3,width:=2.4,color:=Color("8a8972")) -> void:
	var delta=b-a;var shape=PlaneMesh.new();shape.size=Vector2(width,delta.length())
	var node=MeshInstance3D.new();game.add_child(node);node.mesh=shape;node.position=(a+b)*.5+Vector3.UP*.036;node.rotation.y=atan2(delta.x,delta.z);node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material=ShaderMaterial.new();material.shader=load("res://shaders/path_ground.gdshader");material.set_shader_parameter("ground_color",color.darkened(.15));node.material_override=material

func warm_window(pos: Vector3,width:=1.4) -> void:
	game.block(pos,Vector3(.12,1.35,width+.18),Color("34433f"))
	var glass=game.block(pos+Vector3(-.08,0,0),Vector3(.04,1.15,width),Color("d0b879"))
	var material=game.mat(Color("c2aa71"),.45).duplicate();material.emission_enabled=true;material.emission=Color("ba9656");material.emission_energy_multiplier=.65;game.mesh_in(glass).material_override=material
	game.block(pos+Vector3(-.12,0,0),Vector3(.03,1.2,.065),Color("68766a"))
	game.block(pos+Vector3(-.12,0,0),Vector3(.03,.06,width),Color("68766a"))
	game.block(pos+Vector3(-.08,-.72,0),Vector3(.35,.10,width+.3),Color("aaa18b"))

func front_window(pos: Vector3,warm:=true) -> void:
	game.block(pos,Vector3(1.85,1.5,.13),Color("3f5148"))
	var pane=game.block(pos+Vector3(0,0,.09),Vector3(1.6,1.26,.04),Color("ae9a67") if warm else Color("58746d"),false,.35)
	if warm:
		var material=game.mat(Color("b5a476"),.45).duplicate();material.emission_enabled=true;material.emission=Color("ad8f51");material.emission_energy_multiplier=.6;game.mesh_in(pane).material_override=material
	game.block(pos+Vector3(0,0,.13),Vector3(.07,1.32,.05),Color("8a9782"))
	game.block(pos+Vector3(0,.1,.13),Vector3(1.65,.07,.05),Color("8a9782"))
	game.block(pos+Vector3(0,-.8,.10),Vector3(2,.12,.45),Color("aaa48d"))

func ambulance(pos: Vector3) -> void:
	game.block(pos+Vector3.UP*.78,Vector3(2.3,1.15,5.1),Color("c4c5ae"),true,.65)
	game.block(pos+Vector3(0,1.58,-.35),Vector3(2.17,1.0,3.8),Color("d5d4bd"))
	game.block(pos+Vector3(0,1.60,-2.29),Vector3(1.90,.65,.06),Color("4b6b70"),false,.23,.15)
	game.block(pos+Vector3(0,1.18,-2.6),Vector3(2.1,.12,.15),Color("53645f"))
	for x in [-1.16,1.16]:
		game.block(pos+Vector3(x,1.11,.2),Vector3(.035,.22,4.5),Color("9e5c4d"))
		game.block(pos+Vector3(x,1.7,.1),Vector3(.04,.65,.18),Color("ad5145"))
		game.block(pos+Vector3(x,1.7,.1),Vector3(.04,.18,.65),Color("ad5145"))
		for z in [-1.5,1.6]:
			var wheel=game.cylinder(pos+Vector3(x,.42,z),.42,.24,Color("25302c"));wheel.rotation.z=PI*.5
	for x in [-.62,.62]:game.block(pos+Vector3(x,2.16,-1),Vector3(.38,.19,.35),Color("596e8a"),false,.25)

func hut(pos: Vector3,color:=Color("7f8070")) -> void:
	game.block(pos+Vector3(0,1.4,0),Vector3(5,2.8,3.7),color,true)
	game.block(pos+Vector3(0,2.88,0),Vector3(5.6,.20,4.2),Color("3d514b"))
	for x in [-1.5,1.1]:game.block(pos+Vector3(x,1.7,1.88),Vector3(1.1,.9,.045),Color("9d9b78"),false,.28)
	game.block(pos+Vector3(-.2,1.05,1.91),Vector3(.85,2.1,.06),Color("4b5d50"))
	for y in [.35,2.55]:game.block(pos+Vector3(0,y,1.93),Vector3(5,.08,.05),Color("9a9b85"))

func tank(pos: Vector3) -> void:
	var body=game.cylinder(pos+Vector3.UP*1.65,1.15,4.8,Color("785c42"));body.rotation.z=PI*.5
	blocker(pos,Vector2(5.1,2.5),2.8)
	for x in [-1.8,1.8]:
		game.block(pos+Vector3(x,.45,0),Vector3(.4,.9,2.4),Color("5c665a"))
		var ring=game.cylinder(pos+Vector3(x,1.65,0),1.19,.12,Color("3d5048"));ring.rotation.z=PI*.5
	game.tube(pos+Vector3(-2.4,1.65,0),pos+Vector3(-3.2,1.65,0),.13,Color("667466"))

func hospital() -> void:
	# Backdrop is outside the playable rectangle; existing objective positions stay clear.
	game.block(Vector3(48.5,2.0,3),Vector3(4.0,4,15),Color("817e6a"),true)
	game.block(Vector3(37,3.5,-14.2),Vector3(18.5,7,3.8),Color("84816d"),true)
	for y in [1.9,4.9]:
		for x in [30,34,39,43]:front_window(Vector3(x,y,-12.23),x==39 or y<2)
	game.block(Vector3(37,7.05,-14.1),Vector3(19,.22,4.1),Color("485f50"))
	game.block(Vector3(37,3.35,-11.6),Vector3(5,.22,2.7),Color("4d6958"))
	game.block(Vector3(37,1.25,-12.2),Vector3(1.8,2.5,.1),Color("38584c"))
	game.block(Vector3(37,5.4,-12.1),Vector3(1.1,.23,.09),Color("d1c3a4"))
	game.block(Vector3(37,5.4,-12.1),Vector3(.23,1.1,.09),Color("d1c3a4"))
	for z in [0,5,9]:warm_window(Vector3(46.42,1.8,z),1.7)
	game.block(Vector3(46.25,3.4,-3),Vector3(.8,.22,5.7),Color("435c51"))
	game.block(Vector3(46.25,2.1,-3),Vector3(.08,.9,2.8),Color("496759"))
	var cross=game.block(Vector3(46.1,5.8,-3),Vector3(.08,.28,1.3),Color("d1c4a0"))
	game.block(Vector3(46.1,5.8,-3),Vector3(.08,1.3,.28),Color("d1c4a0"))
	game.label_world("ПРИЁМНОЕ",Vector3(43,2.7,-3),.008)
	game.block(Vector3(-26,2.0,-37.2),Vector3(14,4,1.7),Color("717969"),true)
	for x in [-30,-26,-22]:game.block(Vector3(x,2.2,-36.3),Vector3(1.8,1.3,.06),Color("4c6a68"),false,.35)
	game.block(Vector3(-26,4.12,-37.2),Vector3(14.5,.23,2.3),Color("42594d"))
	for p in [Vector3(-32.8,0,11),Vector3(-33,0,-2),Vector3(-4.7,0,10),Vector3(5,0,11.8),Vector3(27,0,11),Vector3(43,0,10.8),Vector3(50,0,-16),Vector3(26,0,-34)]:tree(p,false,rng.randf_range(4.5,5.6))
	for p in [Vector3(-31,0,10.5),Vector3(-30,0,12),Vector3(-6,0,8),Vector3(-3,0,11),Vector3(4,0,12),Vector3(27,0,8),Vector3(45,0,10),Vector3(48,0,-12),Vector3(-11,0,-34)]:bush(p,.65)
	ambulance(Vector3(15,0,10))
	path_strip(Vector3(-22,0,17),Vector3(-22,0,-8),2.3)
	path_strip(Vector3(-4,0,-1),Vector3(26,0,-1),2.5)
	path_strip(Vector3(29,0,-3),Vector3(42,0,-3),2.7)
	for z in [2.5,4.0,5.5,7.0]:game.block(Vector3(-23,.04,z),Vector3(4,.04,.35),Color("b9b497"))
	fence(Vector3(-5,0,10.8),Vector3(5,0,10.8))
	for p in [Vector3(-33,0,23),Vector3(-10,0,12),Vector3(30,0,-10)]:
		stone(p,Vector3(1.6,.55,1.1));grass_patch(Vector2(p.x,p.z),Vector2(4,4),35)
	for p in [Vector2(-30,11),Vector2(1,12),Vector2(44,4),Vector2(25,-34),Vector2(-14,-34)]:grass_patch(p,Vector2(7,2),65)
	for a in [[Vector3(-31,.06,-10),Vector3(-9,.06,-10)],[Vector3(-30,.07,-33),Vector3(-13,.07,-33)]]:game.tube(a[0],a[1],.035,Color("a18a55"))
	game.bench(Vector3(39,0,4));game.bench(Vector3(-30,0,-8))
	for p in [Vector3(31,0,-8),Vector3(31,0,5)]:
		game.block(p+Vector3.UP*.35,Vector3(2.8,.7,1.4),Color("77745e"),true)
		bush(p+Vector3.UP*.7,.72)
	for x in [39.5,40.5]:
		game.cylinder(Vector3(x,.4,1),.32,.8,Color("49635b"))
		game.cylinder(Vector3(x,.82,1),.35,.06,Color("87917a"))
	finish_grass()
