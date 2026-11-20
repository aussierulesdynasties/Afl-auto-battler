extends SceneTree
# godot --path tt -s turntable.gd -- IN.glb OUTDIR FRAMES ELEV_DEG DIST_SCALE
var args
var frames := 96
var i := 0
var cam: Camera3D
var centre := Vector3.ZERO
var radius := 300.0
var elev := 22.0
var out := ""
var cams: PackedStringArray = []

func _init():
	args = OS.get_cmdline_user_args()
	out = args[1]
	frames = int(args[2])
	elev = float(args[3])
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_file(args[0], st) != OK:
		push_error("load failed"); quit(1); return
	var scene := doc.generate_scene(st)
	root.add_child(scene)
	# hand-made textures, lit by the measured sun; anisotropic filtering keeps the rows sharp at a glancing angle
	_unshade(scene)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.62, 0.70, 0.80)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.75, 0.78, 0.85)
	e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = e
	root.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 900.0
	sun.light_energy = 1.3
	root.add_child(sun)
	# sun from bearing 301 deg, 28 deg up (measured from the tower shadow). glTF: x east, y up, z = -north
	var az := deg_to_rad(301.0)
	var el := deg_to_rad(28.0)
	var to_sun := Vector3(sin(az) * cos(el), sin(el), -cos(az) * cos(el))
	sun.look_at_from_position(to_sun * 10.0, Vector3.ZERO, Vector3.UP)
	centre = Vector3(20.97, 6.0, -40.0)
	radius = 300.0 * float(args[4])
	cam = Camera3D.new()
	cam.fov = 40.0
	cam.far = 5000.0
	root.add_child(cam)
	root.size = Vector2i(1280, 720)
	DirAccess.make_dir_recursive_absolute(out)
	# TT_CAMS=file: one camera per line, "ex,ey,ez tx,ty,tz" (world metres); one frame per line
	var cf := OS.get_environment("TT_CAMS")
	if cf != "":
		for ln in FileAccess.get_file_as_string(cf).split("\n", false):
			if ln.strip_edges() != "": cams.append(ln.strip_edges())
		frames = cams.size()

func _unshade(n: Node) -> void:
	for h in OS.get_environment("TT_HIDE").split(",", false):
		if n.name.begins_with(h) and n is Node3D:
			(n as Node3D).visible = false
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		for s in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(s)
			if m is BaseMaterial3D:
				var c := (m as BaseMaterial3D).duplicate() as BaseMaterial3D
				c.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
				mi.set_surface_override_material(s, c)
	for ch in n.get_children():
		_unshade(ch)

func _process(_d):
	# the viewport texture read here holds the frame drawn after the previous tick: save it as that tick's frame
	if i >= 4:
		root.get_texture().get_image().save_png("%s/f%03d.png" % [out, i - 4])
	if i >= frames + 3:
		quit(); return true
	var k: int = max(i - 3, 0)
	var a := TAU * float(k) / float(frames)
	var el := deg_to_rad(elev)
	if cams.size() > 0:
		var pr := cams[min(k, cams.size() - 1)].split(" ")
		var e2: PackedFloat64Array = pr[0].split_floats(","); var t2: PackedFloat64Array = pr[1].split_floats(",")
		cam.look_at_from_position(Vector3(e2[0], e2[2], -e2[1]), Vector3(t2[0], t2[2], -t2[1]), Vector3.UP)
	elif args.size() > 5:
		# fixed close-up: EYE and TARGET in world metres (x east, y north, z up) -> glTF (x, z, -y)
		var e: PackedFloat64Array = args[5].split_floats(","); var t: PackedFloat64Array = args[6].split_floats(",")
		cam.look_at_from_position(Vector3(e[0], e[2], -e[1]), Vector3(t[0], t[2], -t[1]), Vector3.UP)
	else:
		cam.look_at_from_position(centre + Vector3(cos(a) * cos(el), sin(el), sin(a) * cos(el)) * radius, centre, Vector3.UP)
	i += 1
	return false
