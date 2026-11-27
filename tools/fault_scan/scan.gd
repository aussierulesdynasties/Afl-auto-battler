extends SceneTree
## The fault scan's Godot half (tools/fault_scan/README.md): a ground built exactly as the ground inspector
## builds it (tools/inspect/ground_inspector.gd _load: Oval3D's light, turf and posts, then the ground model
## with its seats, surrounds and backdrop), so every position is in the inspector's own coordinates
## (x along the ground, y up from the turf, z across it; the C key's numbers).
##
##   godot --path . --script tools/fault_scan/scan.gd -- dump   <slug> <outdir>
##       every visible mesh in world space (verts.f32, nrms.f32, uvs.f32, idx.i32, surfaces.json), every
##       multimesh (mm_<n>.f32 + multimesh.json), every material and texture (tex/<id>.png thumbnails,
##       materials in surfaces.json), the ground's fit and place (ground.json)
##   godot --path . --rendering-method mobile --script tools/fault_scan/scan.gd -- render <slug> <views.txt> <outdir> [W H]
##       one PNG a line of views.txt: "name x y z facing looking fov" (facing and looking as the inspector's
##       C key gives them), or "name x y z facing looking ortho <size>" for a straight-down map tile
## Looks only: nothing here changes a match.

const OVAL3D_PATH := "res://scripts/ui/match/Oval3D.gd"

var oval: Node3D
var camera: Camera3D


func _initialize() -> void:
	_run.call_deferred()
	create_timer(5400.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	if a.size() < 3:
		print("usage: dump <slug> <outdir> | render <slug> <views.txt> <outdir> [W H]")
		quit(2)
		return
	var mode := str(a[0])
	var slug := str(a[1])
	if mode == "render":
		var size := Vector2i(1280, 720)
		if a.size() >= 6:
			size = Vector2i(int(a[4]), int(a[5]))
		root.size = size
		root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
		OS.low_processor_usage_mode = false
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var t0 := Time.get_ticks_msec()
	if not _build(slug):
		print("FAULTSCAN cannot build ", slug)
		quit(1)
		return
	print("FAULTSCAN built %s in %.1f s" % [slug, (Time.get_ticks_msec() - t0) / 1000.0])
	if mode == "dump":
		_dump(slug, str(a[2]))
	elif mode == "render":
		await _render(str(a[2]), str(a[3]))
	quit(0)


## As the inspector's _load does for a match ground.
func _build(slug: String) -> bool:
	var gname := GroundModels.ground_name(slug)
	GroundModels.play_on(slug, GroundModels.field(slug))
	camera = Camera3D.new()
	camera.fov = 70.0
	camera.near = 0.05
	camera.far = 6000.0
	root.add_child(camera)
	camera.make_current()
	oval = load(OVAL3D_PATH).new()
	oval.name = "Oval"
	oval.ground = gname
	root.add_child(oval)
	oval._environment()
	oval._ground()
	oval._posts()
	oval.camera = camera
	var ball := MeshInstance3D.new()
	oval.add_child(ball)
	oval.ball = ball
	# FAULTSCAN_BASE: read the model from another folder (a draft in tools/grounds/<slug>/), as the inspector can.
	oval._ground_model(slug, OS.get_environment("FAULTSCAN_BASE"))
	var g := oval.get_node_or_null("Ground")
	return g != null and g.get_child_count() > 0


# --- dump -----------------------------------------------------------------------------------------

func _dump(slug: String, out: String) -> void:
	DirAccess.make_dir_recursive_absolute(out.path_join("tex"))
	var fv := FileAccess.open(out.path_join("verts.f32"), FileAccess.WRITE)
	var fn := FileAccess.open(out.path_join("nrms.f32"), FileAccess.WRITE)
	var fu := FileAccess.open(out.path_join("uvs.f32"), FileAccess.WRITE)
	var fi := FileAccess.open(out.path_join("idx.i32"), FileAccess.WRITE)
	var surfaces := []
	var textures := {}
	var vbase := 0
	var ibase := 0
	for c in oval.find_children("*", "MeshInstance3D", true, false):
		var mi := c as MeshInstance3D
		if mi.mesh == null or not mi.is_visible_in_tree():
			continue
		var xf := mi.global_transform
		var nb := Transform3D(xf.basis.inverse().transposed(), Vector3.ZERO)
		for s in mi.mesh.get_surface_count():
			if mi.mesh is ArrayMesh and (mi.mesh as ArrayMesh).surface_get_primitive_type(s) != Mesh.PRIMITIVE_TRIANGLES:
				continue
			var arr := mi.mesh.surface_get_arrays(s)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			if v.is_empty():
				continue
			var n = arr[Mesh.ARRAY_NORMAL]
			var uv = arr[Mesh.ARRAY_TEX_UV]
			var ix = arr[Mesh.ARRAY_INDEX]
			var wv: PackedVector3Array = xf * v
			var wn := PackedVector3Array()
			if n is PackedVector3Array and (n as PackedVector3Array).size() == v.size():
				wn = nb * (n as PackedVector3Array)
			else:
				wn.resize(v.size())
			var puv := PackedVector2Array()
			if uv is PackedVector2Array and (uv as PackedVector2Array).size() == v.size():
				puv = uv
			else:
				puv.resize(v.size())
			var pix := PackedInt32Array()
			if ix is PackedInt32Array and not (ix as PackedInt32Array).is_empty():
				pix = ix
			else:
				pix.resize(v.size())
				for k in v.size():
					pix[k] = k
			fv.store_buffer(wv.to_byte_array())
			fn.store_buffer(wn.to_byte_array())
			fu.store_buffer(puv.to_byte_array())
			fi.store_buffer(pix.to_byte_array())
			var mat := mi.get_active_material(s)
			surfaces.append({
				"node": str(oval.get_path_to(mi)), "surface": s, "mesh": mi.mesh.resource_name,
				"vstart": vbase, "vcount": v.size(), "istart": ibase, "icount": pix.size(),
				"det": xf.basis.determinant(), "material": _material(mat, textures, out),
				"vis_begin": mi.visibility_range_begin, "vis_end": mi.visibility_range_end,
				"meta": _metas(mi),
			})
			vbase += v.size()
			ibase += pix.size()
	fv.close()
	fn.close()
	fu.close()
	fi.close()
	var mms := []
	var k := 0
	for c in oval.find_children("*", "MultiMeshInstance3D", true, false):
		var mmi := c as MultiMeshInstance3D
		if mmi.multimesh == null or mmi.multimesh.mesh == null or not mmi.is_visible_in_tree():
			continue
		var mm := mmi.multimesh
		var path := out.path_join("mm_%d.f32" % k)
		var f := FileAccess.open(path, FileAccess.WRITE)
		f.store_buffer(mm.buffer.to_byte_array())
		f.close()
		var fp := FileAccess.open(out.path_join("mm_%d_faces.f32" % k), FileAccess.WRITE)
		fp.store_buffer(mm.mesh.get_faces().to_byte_array())
		fp.close()
		var mat: Material = mmi.material_override
		if mat == null and mm.mesh.get_surface_count() > 0:
			mat = mm.mesh.surface_get_material(0)
		mms.append({
			"node": str(oval.get_path_to(mmi)), "file": path.get_file(), "count": mm.instance_count,
			"colors": mm.use_colors, "custom": mm.use_custom_data, "xform": _xf(mmi.global_transform),
			"aabb": _aabb(mm.mesh.get_aabb()), "material": _material(mat, textures, out),
			"vis_begin": mmi.visibility_range_begin, "vis_end": mmi.visibility_range_end, "meta": _metas(mmi),
		})
		k += 1
	var gname := GroundModels.ground_name(slug)
	var place: Dictionary = Oval3DSunClock.place(gname)
	var info := {
		"slug": slug, "ground": gname, "fence": [GroundModels.match_fence().x, GroundModels.match_fence().y],
		"fence_shape": Array(GroundModels.match_fence_shape(slug)),
		"fit": GroundModels.FIT.get(slug, []), "ground_xform": _xf((oval.get_node("Ground") as Node3D).global_transform),
		"axis": Oval3DSunClock.axis_for(gname), "place": place, "seat_far": GroundModels.SEAT_FAR.has(slug),
		"seat_far_from": GroundModels.SEAT_FAR_FROM,
		"seat_points": _v3s(GroundModels.seat_points(slug, OS.get_environment("FAULTSCAN_BASE"))),
		"goal_x": MatchMotion.GOAL_X, "half_len": MatchMotion.HALF_LEN, "half_wid": MatchMotion.HALF_WID,
		"surrounds": GroundModels.SURROUNDS.get(slug, {}), "has_backdrop": GroundModels.has_backdrop(slug),
	}
	_save_json(out.path_join("ground.json"), info)
	_save_json(out.path_join("surfaces.json"), surfaces)
	_save_json(out.path_join("multimesh.json"), mms)
	_save_json(out.path_join("textures.json"), textures)
	print("FAULTSCAN dumped %d surfaces, %d vertices, %d indices, %d multimeshes, %d textures" % [
			surfaces.size(), vbase, ibase, mms.size(), textures.size()])


func _metas(n: Node) -> Dictionary:
	var m := {}
	for key in n.get_meta_list():
		m[str(key)] = str(n.get_meta(key))
	return m


func _material(mat: Material, textures: Dictionary, out: String) -> Dictionary:
	if mat == null:
		return {"class": "none"}
	var d := {"class": mat.get_class(), "name": mat.resource_name, "path": mat.resource_path}
	if mat is BaseMaterial3D:
		var b := mat as BaseMaterial3D
		d["albedo"] = _col(b.albedo_color)
		d["tex"] = _tex(b.albedo_texture, textures, out)
		d["cull"] = b.cull_mode
		d["transparency"] = b.transparency
		d["shading"] = b.shading_mode
		d["emission_on"] = b.emission_enabled
		d["emission"] = _col(b.emission)
		d["emission_energy"] = b.emission_energy_multiplier
		d["emission_tex"] = _tex(b.emission_texture, textures, out)
		d["roughness"] = b.roughness
		d["metallic"] = b.metallic
		d["uv1_scale"] = [b.uv1_scale.x, b.uv1_scale.y, b.uv1_scale.z]
		d["uv1_offset"] = [b.uv1_offset.x, b.uv1_offset.y]
		d["triplanar"] = b.uv1_triplanar
		d["vertex_colour"] = b.vertex_color_use_as_albedo
	elif mat is ShaderMaterial:
		var sm := mat as ShaderMaterial
		d["shader"] = sm.shader.resource_path if sm.shader != null else ""
		var params := {}
		if sm.shader != null:
			for u in sm.shader.get_shader_uniform_list():
				var v = sm.get_shader_parameter(u["name"])
				if v is Texture2D:
					params[u["name"]] = _tex(v, textures, out)
				elif v is Color:
					params[u["name"]] = _col(v)
				elif v is float or v is int or v is bool:
					params[u["name"]] = v
		d["params"] = params
	return d


## A texture's id; its first sight saves a thumbnail (longest side 256 px) and its size and colour.
func _tex(t: Texture2D, textures: Dictionary, out: String) -> String:
	if t == null:
		return ""
	var id := t.resource_path if t.resource_path != "" else "rid%d" % t.get_rid().get_id()
	if textures.has(id):
		return id
	var key := "t%04d" % textures.size()
	var e := {"key": key, "w": t.get_width(), "h": t.get_height(), "name": t.resource_name}
	var img := t.get_image()
	if img != null:
		if img.is_compressed():
			img.decompress()
		img.convert(Image.FORMAT_RGBA8)
		var w := img.get_width()
		var h := img.get_height()
		var s := minf(1.0, 512.0 / maxf(w, h))
		if s < 1.0:
			img.resize(maxi(1, int(w * s)), maxi(1, int(h * s)), Image.INTERPOLATE_BILINEAR)
		img.save_png(out.path_join("tex/%s.png" % key))
	textures[id] = e
	return id


func _col(c: Color) -> Array:
	return [snappedf(c.r, 0.0001), snappedf(c.g, 0.0001), snappedf(c.b, 0.0001), snappedf(c.a, 0.0001)]


func _xf(t: Transform3D) -> Array:
	return [t.basis.x.x, t.basis.y.x, t.basis.z.x, t.origin.x,
			t.basis.x.y, t.basis.y.y, t.basis.z.y, t.origin.y,
			t.basis.x.z, t.basis.y.z, t.basis.z.z, t.origin.z]


func _aabb(b: AABB) -> Array:
	return [b.position.x, b.position.y, b.position.z, b.size.x, b.size.y, b.size.z]


func _v3s(p: PackedVector3Array) -> Array:
	var out := []
	for v in p:
		out.append([v.x, v.y, v.z])
	return out


func _save_json(path: String, v) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(v))
	f.close()


# --- render ---------------------------------------------------------------------------------------

func _render(views: String, out: String) -> void:
	DirAccess.make_dir_recursive_absolute(out)
	var f := FileAccess.open(views, FileAccess.READ)
	if f == null:
		print("FAULTSCAN cannot read ", views)
		return
	var lines := f.get_as_text().split("\n", false)
	var n := 0
	var far := camera.far
	for line in lines:
		var w := line.strip_edges().split(" ", false)
		if w.size() < 7 or w[0].begins_with("#"):
			continue
		camera.global_position = Vector3(float(w[1]), float(w[2]), float(w[3]))
		var yaw := -deg_to_rad(float(w[4]))
		var pitch := deg_to_rad(float(w[5]))
		camera.global_basis = Basis.from_euler(Vector3(pitch, yaw, 0.0))
		if w[6] == "ortho":
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = float(w[7])
			camera.far = camera.global_position.y + 200.0
		else:
			camera.projection = Camera3D.PROJECTION_PERSPECTIVE
			camera.fov = float(w[6])
			camera.far = far
		for _i in 5:
			await process_frame
		await RenderingServer.frame_post_draw
		root.get_viewport().get_texture().get_image().save_png(out.path_join("%s.png" % w[0]))
		n += 1
		if n % 20 == 0:
			print("FAULTSCAN rendered %d views" % n)
	print("FAULTSCAN rendered %d views" % n)
