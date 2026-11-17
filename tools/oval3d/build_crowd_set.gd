extends SceneTree
## Bakes the 3D view's crowd (Oval3DCrowdSet) from the crowd bodies' vertex-animation bakes.
##   godot --windowed --path . --script tools/oval3d/build_crowd_set.gd -- BAKES_DIR [OUT.res]
## BAKES_DIR holds one folder per body, vat_<name> (meta.json, mesh.bin, pos.bin, nrm.bin), as
## tools/oval3d/bake_crowd_vat.py writes them from a Mixamo body and the four sitting clips.
## Windowed, not headless: the cards' atlas is drawn by the renderer.

const OUT := "res://assets/oval3d/crowd_set.res"
## Each body's part of the seats (Bible 2.87: men and women 62/38 of the adults, 10 in 100
## children): two men, four women, a boy and a girl.
const SHARES := {"remy": 0.279, "brian": 0.279, "megan": 0.0855, "kate": 0.0855,
		"jody": 0.0855, "sophie": 0.0855, "boy": 0.05, "girl": 0.05}
const IDLE := "sit_idle"
const CHEER := "cheer"
const CELL := Vector2i(64, 128)


func _init() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	# Draw every frame (the project idles in low-processor mode, and the atlas waits on draws).
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	var args := OS.get_cmdline_user_args()
	var src := str(args[0])
	var out := str(args[1]) if args.size() > 1 else OUT
	var cs := Oval3DCrowdSet.new()
	var mn := Vector3.INF
	var mx := -Vector3.INF
	var mats := []
	for name in SHARES:
		var b := _load_body(src.path_join("vat_" + name))
		b["name"] = name
		b["share"] = SHARES[name]
		mn = mn.min(b["mn"])
		mx = mx.max(b["mx"])
		mats.append(b["mat"])
		b.erase("mn")
		b.erase("mx")
		b.erase("mat")
		cs.bodies.append(b)
	# The cards' atlas: each body from the front, slightly above, as an orthographic picture.
	var tall := (mx.y - mn.y) * 1.06
	var cx := (mn.x + mx.x) * 0.5
	var cy := (mn.y + mx.y) * 0.5
	var vp := SubViewport.new()
	vp.size = CELL
	vp.transparent_bg = true
	vp.own_world_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(vp)
	var mi := MeshInstance3D.new()
	vp.add_child(mi)
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = tall
	vp.add_child(cam)
	var e := deg_to_rad(10.0)
	cam.position = Vector3(cx, cy, 0.0) + Vector3(0.0, sin(e), cos(e)) * 10.0
	cam.look_at(Vector3(cx, cy, 0.0), Vector3.UP)
	cam.current = true
	var atlas := Image.create(CELL.x * 16, CELL.y * cs.bodies.size(), false, Image.FORMAT_RGBA8)
	for bi in range(cs.bodies.size()):
		var b: Dictionary = cs.bodies[bi]
		mi.mesh = b["mesh"]
		var am: ShaderMaterial = mats[bi]
		am.set_shader_parameter("mode", 1)
		mi.material_override = am
		for col in range(16):
			var c: Vector2i = b["idle"] if col < 8 else b["cheer"]
			am.set_shader_parameter("atlas_row", c.x + int(floor(float(col % 8) * float(c.y) / 8.0)))
			for w in range(2):
				await process_frame
			await RenderingServer.frame_post_draw
			var img := vp.get_texture().get_image()
			img.convert(Image.FORMAT_RGBA8)
			atlas.blit_rect(img, Rect2i(Vector2i.ZERO, CELL), Vector2i(col * CELL.x, bi * CELL.y))
	vp.queue_free()
	atlas.generate_mipmaps()
	cs.atlas = ImageTexture.create_from_image(atlas)
	cs.card_w = tall * 0.5
	cs.card_h = tall
	cs.card_x0 = cx
	cs.card_y0 = cy - tall * 0.5
	var ch: Vector2i = cs.bodies[0]["cheer"]
	cs.cheer_s = float(ch.y) / float(cs.bodies[0]["fps"])
	var err := ResourceSaver.save(cs, out, ResourceSaver.FLAG_COMPRESS)
	print("CROWD SET %s: %d bodies, error %d" % [out, cs.bodies.size(), err])
	quit(err)


## One bake: its mesh (each vertex's column in UV.x and its part in the colour), its tables as
## half-float textures, its clips. A temporary material draws it into the atlas.
func _load_body(dir: String) -> Dictionary:
	var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join("meta.json")))
	var f := FileAccess.open(dir.path_join("mesh.bin"), FileAccess.READ)
	var nv := f.get_32()
	var ni := f.get_32()
	var roles := f.get_buffer(nv * 4)
	var idx := f.get_buffer(ni * 4).to_int32_array()
	# Blender's front faces wind anticlockwise, Godot's clockwise.
	for t in range(0, ni, 3):
		var k := idx[t + 1]
		idx[t + 1] = idx[t + 2]
		idx[t + 2] = k
	var rows := int(meta["rows"])
	var pb := FileAccess.get_file_as_bytes(dir.path_join("pos.bin"))
	var nb := FileAccess.get_file_as_bytes(dir.path_join("nrm.bin"))
	var pimg := Image.create_from_data(nv, rows, false, Image.FORMAT_RGBF, pb)
	var nimg := Image.create_from_data(nv, rows, false, Image.FORMAT_RGBF, nb)
	pimg.convert(Image.FORMAT_RGBH)
	nimg.convert(Image.FORMAT_RGBH)
	var p0 := pb.slice(0, nv * 12).to_float32_array()
	var n0 := nb.slice(0, nv * 12).to_float32_array()
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	for i in range(nv):
		verts.append(Vector3(p0[i * 3], p0[i * 3 + 1], p0[i * 3 + 2]))
		norms.append(Vector3(n0[i * 3], n0[i * 3 + 1], n0[i * 3 + 2]))
		uvs.append(Vector2(float(i) + 0.5, 0.0))
		cols.append(Color(roles[i * 4] / 255.0, roles[i * 4 + 1] / 255.0, roles[i * 4 + 2] / 255.0, roles[i * 4 + 3] / 255.0))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = norms
	arr[Mesh.ARRAY_TEX_UV] = uvs
	arr[Mesh.ARRAY_COLOR] = cols
	arr[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mn := Vector3(meta["min"][0], meta["min"][1], meta["min"][2])
	var mx := Vector3(meta["max"][0], meta["max"][1], meta["max"][2])
	mesh.custom_aabb = AABB(mn - Vector3.ONE * 0.3, mx - mn + Vector3.ONE * 0.6)
	var clips := {}
	for c in meta["clips"]:
		clips[str(c["name"])] = Vector2i(int(c["row"]), int(c["frames"]))
	var pos_tex := ImageTexture.create_from_image(pimg)
	var nrm_tex := ImageTexture.create_from_image(nimg)
	var mat := ShaderMaterial.new()
	mat.shader = load("res://scripts/ui/match/oval3d_crowd_people.gdshader")
	mat.set_shader_parameter("pos_tex", pos_tex)
	mat.set_shader_parameter("nrm_tex", nrm_tex)
	print("BODY %s: %d verts, %d tris, %.2f m tall" % [dir.get_file(), nv, ni / 3, mx.y - mn.y])
	return {"mesh": mesh, "pos_tex": pos_tex, "nrm_tex": nrm_tex, "fps": float(meta["clips"][0]["fps"]),
			"idle": clips[IDLE], "cheer": clips[CHEER], "mn": mn, "mx": mx, "mat": mat}
