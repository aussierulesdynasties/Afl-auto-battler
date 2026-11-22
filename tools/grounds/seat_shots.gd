extends SceneTree
## QA pictures for tools/grounds/seat_check.gd: a ground as a match lays it (GroundModels.instantiate,
## the model and its seats), with the seats the check flags drawn as red boxes, filmed from
## views round where they are. Run it before and after `seat_check.gd --write`.
##   godot --path . --rendering-driver opengl3 --script tools/grounds/seat_shots.gd -- SPOTS_DIR OUT_DIR TAG [slug ...]
## SPOTS_DIR holds seat_check's --out files (<slug>.json). Saves OUT_DIR/<slug>_<TAG>_<n>.png.
## A TAG starting "after" films the same views without the red boxes (pass the spots from before).

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var spots_dir := str(args[0])
	var out := str(args[1])
	var tag := str(args[2])
	DirAccess.make_dir_recursive_absolute(out)
	root.size = Vector2i(1280, 720)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.62, 0.74, 0.88)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.75, 0.75, 0.78)
	e.ambient_light_energy = 0.6
	env.environment = e
	root.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 30, 0)
	root.add_child(sun)
	var cam := Camera3D.new()
	cam.far = 3000.0
	root.add_child(cam)
	for slug in args.slice(3):
		var ground := GroundModels.instantiate(str(slug))
		root.add_child(ground)
		var marks := []
		var path := spots_dir.path_join("%s.json" % slug)
		if FileAccess.file_exists(path):
			var d = JSON.parse_string(FileAccess.get_file_as_string(path))
			for s in d["spots"]:
				marks.append(Vector3(s[0], s[1], s[2]))
		if not marks.is_empty() and not tag.begins_with("after"):
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			var box := BoxMesh.new()
			box.size = Vector3(0.45, 0.45, 0.45)
			var mat := StandardMaterial3D.new()
			mat.albedo_color = Color(1, 0, 0)
			mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			box.material = mat
			mm.mesh = box
			mm.instance_count = marks.size()
			for i in marks.size():
				mm.set_instance_transform(i, Transform3D(Basis(), marks[i] + Vector3(0, 0.4, 0)))
			var mi := MultiMeshInstance3D.new()
			mi.multimesh = mm
			ground.add_child(mi)
		for v in _views(ground, marks):
			cam.global_position = v[0]
			cam.look_at(v[1], Vector3.UP)
			cam.fov = v[2]
			for i in 4:
				await process_frame
			root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s_%d.png" % [slug, tag, v[3]]))
		ground.queue_free()
		await process_frame
	quit(0)


## Views in the match frame: the whole ground from high, then round the biggest groups of flagged
## seats (one from the field side, one from outside and below), at most 4 groups.
func _views(ground: Node3D, marks: Array) -> Array:
	var v := [[Vector3(90, 170, 190), Vector3.ZERO, 50.0, 0]]
	var groups := {}
	for m in marks:
		var p: Vector3 = ground.global_transform * (m as Vector3)
		var b := int(floor(fposmod(atan2(p.z, p.x), TAU) / TAU * 12.0))
		if not groups.has(b):
			groups[b] = []
		groups[b].append(p)
	var keys := groups.keys()
	keys.sort_custom(func(a, b): return groups[a].size() > groups[b].size())
	var n := 1
	for k in keys.slice(0, 4):
		var c := Vector3.ZERO
		for p in groups[k]:
			c += p
		c /= float(groups[k].size())
		var out := Vector3(c.x, 0, c.z).normalized()
		v.append([c - out * 45.0 + Vector3(0, 12, 0), c, 55.0, n])
		v.append([c + out * 40.0 + Vector3(0, -4 if c.y > 10 else 3, 0) + Vector3(out.z, 0, -out.x) * 15.0, c, 60.0, n + 1])
		n += 2
	return v
