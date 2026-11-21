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
	# sun from bearing 301 deg, 28 deg up (read off the 1984 aerial shadows). glTF: x east, y up, z = -north
	var az := deg_to_rad(72.0)
	var el := deg_to_rad(39.0)
	var to_sun := Vector3(sin(az) * cos(el), sin(el), -cos(az) * cos(el))
	sun.look_at_from_position(to_sun * 10.0, Vector3.ZERO, Vector3.UP)
	centre = Vector3(6.0, 4.0, -11.0)
	radius = 300.0 * float(args[4])
	cam = Camera3D.new()
	cam.fov = 40.0
	cam.far = 5000.0
	root.add_child(cam)
	root.size = Vector2i(1280, 720)
	DirAccess.make_dir_recursive_absolute(out)

func _unshade(n: Node) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		for s in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(s)
			if m is BaseMaterial3D:
				var c := (m as BaseMaterial3D).duplicate() as BaseMaterial3D
				c.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
				# runtime glTF images arrive without mipmaps: build them, or fine ribs and brick shimmer into moire at range
				if c.albedo_texture != null:
					var img := c.albedo_texture.get_image()
					if img != null and not img.has_mipmaps():
						img.decompress()
						img.generate_mipmaps()
						c.albedo_texture = ImageTexture.create_from_image(img)
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
	cam.look_at_from_position(centre + Vector3(cos(a) * cos(el), sin(el), sin(a) * cos(el)) * radius, centre, Vector3.UP)
	i += 1
	return false
