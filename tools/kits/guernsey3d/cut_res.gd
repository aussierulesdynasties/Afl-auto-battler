extends SceneTree
## One club's guernsey cut (recut5.py's wrap5_CODE.glb), saved small beside the body for Oval3D to
## swap in when that club's men are built (Oval3D.club_body). The rest of the body stays the one
## shared file (assets/oval3d/player_mh.glb, uncut).
##   godot --headless --path . --script tools/kits/guernsey3d/cut_res.gd -- IN.glb CODE
##
## For each of the two surfaces the cut changes (ARD_skin, ARD_guernsey) the saved mesh holds:
##   a points surface of that name   only the points the cut added, with their morph targets
##   meta <name>_base                the shared body's point count for that surface
##   meta <name>_index               the cut surface's triangles: below <name>_base = a shared point,
##                                   from <name>_base on = the added points in order
## The cut keeps most of the shared points, so storing both surfaces whole (19 morph targets each)
## cost 13.7 MB a club; this way only the added points are stored.

const OUT_DIR := "res://assets/oval3d/cuts"
const BASE := "res://assets/oval3d/player_mh.glb"
const KEEP := ["ARD_skin", "ARD_guernsey"]


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var src := str(args[0])
	var code := str(args[1])
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_file(src, state) != OK:
		push_error("cut_res: cannot read %s" % src)
		quit(1)
		return
	var root := doc.generate_scene(state)
	var body := _biggest(root)
	var base_root: Node = (load(BASE) as PackedScene).instantiate()
	var base := _biggest(base_root)
	var cs := _surface(body, "ARD_skin")
	var bs := _surface(base, "ARD_skin")
	var cg := _surface(body, "ARD_guernsey")
	var ok := cs >= 0 and bs >= 0 and cg >= 0 and body.get_blend_shape_count() == base.get_blend_shape_count()
	if not ok:
		push_error("cut_res: surfaces or morph targets don't match the shared body")
		quit(1)
		return

	var out := ArrayMesh.new()
	out.blend_shape_mode = body.blend_shape_mode
	for b in range(body.get_blend_shape_count()):
		out.add_blend_shape(body.get_blend_shape_name(b))
	for name in KEEP:
		_store(out, body, base, name, code)
	root.free()
	base_root.free()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))
	var path := "%s/%s.res" % [OUT_DIR, code]
	var err := ResourceSaver.save(out, path, ResourceSaver.FLAG_COMPRESS)
	print("wrote %s (%d)" % [path, err])
	quit(0 if err == OK else 1)


## Surface name of the cut body, stored against the same surface of the shared body: the points the
## shared surface already has are named by number; only the points the cut added are kept.
func _store(out: ArrayMesh, body: ArrayMesh, base: ArrayMesh, name: String, code: String) -> void:
	var cs := _surface(body, name)
	var bs := _surface(base, name)
	var ba := base.surface_get_arrays(bs)
	var ca := body.surface_get_arrays(cs)
	var lookup := {}
	var bv: PackedVector3Array = ba[Mesh.ARRAY_VERTEX]
	for i in range(bv.size()):
		lookup[_key(ba, i)] = i
	var cv: PackedVector3Array = ca[Mesh.ARRAY_VERTEX]
	var remap := PackedInt32Array()
	remap.resize(cv.size())
	var added := PackedInt32Array()
	for i in range(cv.size()):
		var k := _key(ca, i)
		if lookup.has(k):
			remap[i] = lookup[k]
		else:
			remap[i] = bv.size() + added.size()
			added.append(i)
	var index := PackedInt32Array()
	for i in (ca[Mesh.ARRAY_INDEX] as PackedInt32Array):
		index.append(remap[i])
	# Matched points must also carry the shared point's morphs, or the swap would move them.
	var cshapes := body.surface_get_blend_shape_arrays(cs)
	var bshapes := base.surface_get_blend_shape_arrays(bs)
	var worst := 0.0
	for b in range(cshapes.size()):
		var cpos: PackedVector3Array = cshapes[b][Mesh.ARRAY_VERTEX]
		var bpos: PackedVector3Array = bshapes[b][Mesh.ARRAY_VERTEX]
		for i in range(cv.size()):
			if remap[i] < bv.size():
				worst = maxf(worst, cpos[i].distance_to(bpos[remap[i]]))
	if added.size() > 0:
		out.add_surface_from_arrays(Mesh.PRIMITIVE_POINTS, _pick(ca, added),
				cshapes.map(func(sh): return _pick(sh, added)), {}, _custom_format(body, cs))
		out.surface_set_name(out.get_surface_count() - 1, name)
	out.set_meta(name + "_base", bv.size())
	out.set_meta(name + "_index", index)
	print("%s %s: %d points (%d shared, %d added), worst morph gap %.6f m" % [
			code, name, cv.size(), cv.size() - added.size(), added.size(), worst])


func _biggest(root: Node) -> ArrayMesh:
	var best: ArrayMesh = null
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var am := (mi as MeshInstance3D).mesh as ArrayMesh
		if am != null and (best == null or am.get_surface_count() > best.get_surface_count()):
			best = am
	return best


func _surface(am: ArrayMesh, name: String) -> int:
	for s in range(am.get_surface_count()):
		var mat := am.surface_get_material(s)
		if mat != null and mat.resource_name == name:
			return s
	return -1


## A point's identity: place and uv to 0.01 mm, and its bones and weights.
func _key(a: Array, i: int) -> String:
	var v: Vector3 = (a[Mesh.ARRAY_VERTEX] as PackedVector3Array)[i]
	var uv: Vector2 = (a[Mesh.ARRAY_TEX_UV] as PackedVector2Array)[i]
	var k := "%d,%d,%d,%d,%d" % [roundi(v.x * 1e5), roundi(v.y * 1e5), roundi(v.z * 1e5),
			roundi(uv.x * 1e5), roundi(uv.y * 1e5)]
	if a[Mesh.ARRAY_BONES] != null:
		var bones: PackedInt32Array = a[Mesh.ARRAY_BONES]
		var w: PackedFloat32Array = a[Mesh.ARRAY_WEIGHTS]
		var n := bones.size() / (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
		for j in range(n):
			k += ";%d:%d" % [bones[i * n + j], roundi(w[i * n + j] * 1000)]
	return k


## The arrays a, keeping only the points in rows (no index).
func _pick(a: Array, rows: PackedInt32Array) -> Array:
	var n := (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()
	var out := []
	out.resize(Mesh.ARRAY_MAX)
	for t in range(Mesh.ARRAY_MAX):
		if t == Mesh.ARRAY_INDEX or a[t] == null:
			continue
		var src = a[t]
		var per: int = src.size() / n
		var dst = src.slice(0, 0)
		for r in rows:
			for j in range(per):
				dst.append(src[r * per + j])
		out[t] = dst
	return out


## Same as Oval3D._custom_format: keep the surface's custom channel formats (the kit edges ride in them).
static func _custom_format(am: ArrayMesh, s: int) -> int:
	var f := am.surface_get_format(s)
	var out := 0
	for c in range(4):
		var shift: int = Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT + c * Mesh.ARRAY_FORMAT_CUSTOM_BITS
		out |= f & (Mesh.ARRAY_FORMAT_CUSTOM_MASK << shift)
	return out
