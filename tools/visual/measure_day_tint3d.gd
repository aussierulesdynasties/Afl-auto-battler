extends SceneTree
## What the day look does to colour (rule 2.81's broadcast tone over rule 2.80's sky light): grey
## and green cards, sunlit and shaded, near and far, rendered through a real match's light, sky,
## film and tone, and each card's colour on screen printed with its hue. Neutral grey should come
## out neutral (a touch cool in shade, as daylight shade is), and far land should fade to the
## sky's haze, never to purple.
##   godot --path . --rendering-method mobile --script tools/visual/measure_day_tint3d.gd -- [GROUND] [SLOT] [OUT.png]

const SIZE := Vector2i(1280, 720)
## Each card: [name, albedo, distance m, bearing from the camera's view in degrees, faces the sun].
const CARDS := [
	["grey lit 60 m", Color(0.5, 0.5, 0.5), 60.0, -24.0, true],
	["grey shade 60 m", Color(0.5, 0.5, 0.5), 60.0, -12.0, false],
	["concrete lit 120 m", Color(0.62, 0.6, 0.56), 120.0, 0.0, true],
	["concrete shade 120 m", Color(0.62, 0.6, 0.56), 120.0, 10.0, false],
	["grey lit 1 km", Color(0.5, 0.5, 0.5), 1000.0, 20.0, true],
	["hill green 3 km", Color(0.16, 0.24, 0.1), 3000.0, -6.0, true],
	["hill green 10 km", Color(0.16, 0.24, 0.1), 10000.0, 6.0, true],
	["hill green 25 km", Color(0.16, 0.24, 0.1), 25000.0, 16.0, true],
]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(600.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var ground := str(args[0]) if args.size() > 0 else "MCG"
	var slot := str(args[1]) if args.size() > 1 else "day"
	var out := str(args[2]) if args.size() > 2 else ""
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = SIZE
	DisplayServer.window_set_size(SIZE)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	oval.ground = ground
	oval.quality = "high"
	Oval3DQuality.apply_viewport("high", root.get_viewport())
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	oval.turf.apply("", slot)
	# Hide the stadium so the cards stand in the open, and look out along the ground.
	var g: Node = oval.get_node_or_null("Ground")
	if g != null:
		g.visible = false
	var cam: Camera3D = oval.camera
	cam.far = 40000.0
	var eye := Vector3(0.0, 30.0, 0.0)
	var sun_dir: Vector3 = (oval.turf.sun as DirectionalLight3D).global_basis.z   # towards the sun
	var look := -Vector3(sun_dir.x, 0.0, sun_dir.z).normalized().rotated(Vector3.UP, deg_to_rad(90.0))
	cam.global_position = oval.to_global(eye)
	cam.look_at(cam.global_position + look * 100.0 + Vector3(0, -2.0, 0), Vector3.UP)
	cam.fov = 70.0
	# The cards are painted as a ground model is (Oval3DTurf.light_stands: the stand shader), so
	# they take the light a stand's wall takes. That shader is also lit right by the cloud's
	# software Vulkan, where Godot's own material never gets the sun.
	var cards := Node3D.new()
	root.add_child(cards)
	var pts := []
	for c in CARDS:
		var dir := look.rotated(Vector3.UP, deg_to_rad(-float(c[3])))
		var dist := float(c[2])
		var size := dist * 0.1
		var mi := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(size, size * 0.6, size * 0.05)
		mi.mesh = bm
		var m := StandardMaterial3D.new()
		m.albedo_color = c[1]
		m.roughness = 0.9
		mi.material_override = m
		cards.add_child(mi)
		var at: Vector3 = cam.global_position + dir * dist
		at.y = cam.global_position.y - dist * 0.02
		mi.global_position = at
		# Face the camera, turned 50 degrees towards the sun (lit) or away from it (its own shade).
		var flat_sun := Vector3(sun_dir.x, 0.0, sun_dir.z).normalized()
		var face := (-dir).rotated(Vector3.UP, deg_to_rad(50.0))
		if (face.dot(flat_sun) > (-dir).rotated(Vector3.UP, deg_to_rad(-50.0)).dot(flat_sun)) != bool(c[4]):
			face = (-dir).rotated(Vector3.UP, deg_to_rad(-50.0))
		mi.look_at(at - face, Vector3.UP)
		pts.append(at)
	_lit_like_stands(oval, cards)
	var sky_set := OS.get_environment("SKY")
	if sky_set != "":
		var sm: ShaderMaterial = oval.turf.env.sky.sky_material
		for kv in sky_set.split(";"):
			var p := kv.split("=")
			var v := p[1].split(",")
			sm.set_shader_parameter(p[0], Color(float(v[0]), float(v[1]), float(v[2]), float(v[3]) if v.size() > 3 else 1.0) if v.size() >= 3 else float(v[0]))
		oval.turf._light_stands()
	for i in range(40):
		await process_frame
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	if out != "":
		img.save_png(out)
	print("%s %s: exposure %.2f, ambient %s x %.2f, sun %s x %.2f" % [ground, slot, oval.turf.env.tonemap_exposure,
			oval.turf.env.ambient_light_color, oval.turf.env.ambient_light_energy,
			oval.turf.sun.light_color, oval.turf.sun.light_energy])
	_report("sky above the horizon", img, Vector2i(SIZE.x / 2, 60))
	_report("turf (sunlit)", img, Vector2i(SIZE.x / 2 + 200, SIZE.y - 60))
	for i in CARDS.size():
		var sp := cam.unproject_position(pts[i])
		_report(str(CARDS[i][0]), img, Vector2i(sp))
	quit()


## The cards take the stand shader as a model's surfaces do (material_override, so set per surface).
func _lit_like_stands(oval: Node, cards: Node3D) -> void:
	for mi: MeshInstance3D in cards.get_children():
		var m: StandardMaterial3D = mi.material_override
		mi.material_override = null
		mi.mesh.surface_set_material(0, m)
	oval.turf.light_stands(cards)


func _report(name: String, img: Image, p: Vector2i) -> void:
	if p.x < 3 or p.y < 3 or p.x >= SIZE.x - 3 or p.y >= SIZE.y - 3:
		print("%-24s off screen" % name)
		return
	var s := Color(0, 0, 0)
	for dx in range(-2, 3):
		for dy in range(-2, 3):
			s += img.get_pixel(p.x + dx, p.y + dy)
	s /= 25.0
	print("%-24s rgb %3d %3d %3d  hue %3d  sat %.2f" % [name, int(s.r * 255), int(s.g * 255), int(s.b * 255),
			int(s.h * 360.0), s.s])
