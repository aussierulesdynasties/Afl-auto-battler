extends SceneTree
## Close-up stills: -- IN.glb OUT.png ex ey ez tx ty tz (Blender metres, z up) of a GLB: godot --windowed --script turntable.gd -- IN.glb OUTDIR FRAMES ELEV_DEG

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	var src := str(a[0])
	var out := str(a[1])
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(1280, 720)
	DisplayServer.window_set_size(root.size)
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_file(src, st) != OK:
		print("LOAD FAILED"); quit(1); return
	var model: Node3D = doc.generate_scene(st)
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(model)
	for im in model.find_children("*", "ImporterMeshInstance3D", true, false):
		var mi := MeshInstance3D.new()
		mi.mesh = im.mesh.get_mesh()
		mi.transform = im.transform
		im.get_parent().add_child(mi)
		im.queue_free()
	var box := AABB()
	var first := true
	for m in model.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		var b: AABB = mi.global_transform * mi.get_aabb()
		box = b if first else box.merge(b)
		first = false
	print("AABB ", box)
	if first:
		quit(1); return
	var c := box.get_center()
	var r := box.size.length() * 0.5
	var env := WorldEnvironment.new()
	var e := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.ground_bottom_color = Color(0.62, 0.66, 0.70)
	sm.ground_horizon_color = Color(0.72, 0.76, 0.80)
	sm.sky_top_color = Color(0.16, 0.38, 0.80)
	sm.sky_horizon_color = Color(0.60, 0.74, 0.90)
	sky.sky_material = sm
	e.sky = sky
	e.background_mode = Environment.BG_SKY
	e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	e.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.environment = e
	world.add_child(env)
	var sun := DirectionalLight3D.new()
	# sun fitted to the roof's shadow edge on the oval in g49: az -12, el 25 in the Blender frame (x, y, z) -> Godot (x, z, -y)
	var saz := deg_to_rad(-12.0); var sel := deg_to_rad(25.0)
	var to_sun := Vector3(cos(saz) * cos(sel), sin(sel), -sin(saz) * cos(sel))
	sun.basis = Basis.looking_at(-to_sun, Vector3.UP)
	sun.shadow_enabled = true
	sun.light_energy = 1.5
	sun.light_color = Color(1.0, 0.97, 0.92)
	world.add_child(sun)
	var cam := Camera3D.new()
	cam.fov = 50.0
	cam.near = 0.1
	cam.far = 3000.0
	world.add_child(cam)
	cam.current = true
	cam.global_position = Vector3(float(a[2]), float(a[4]), -float(a[3]))
	cam.look_at(Vector3(float(a[5]), float(a[7]), -float(a[6])), Vector3.UP)
	for w in range(4):
		await process_frame
	await RenderingServer.frame_post_draw
	root.get_viewport().get_texture().get_image().save_png(out)
	quit(0)
