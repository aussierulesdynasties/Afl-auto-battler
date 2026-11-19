extends SceneTree
## One club's guernsey cut (recut5.py's wrap5_CODE.glb), saved small beside the body for Oval3D to
## swap in when that club's men are built (Oval3D.club_body). The rest of the body stays the one
## shared file (assets/oval3d/player_mh.glb, uncut).
##   godot --headless --path . --script tools/kits/guernsey3d/cut_res.gd -- IN.glb CODE [unwrap_CODE.json]
## With unwrap.py's flat pattern (director 2026-11-19, "Yes, all clubs"), the guernsey's points are split where the
## pattern's pieces part, and each point's place in the pattern is kept (meta <name>_unwrap, two floats a point:
## 1 + its place in the club's atlas cell, 0 for none; Oval3D.club_body puts it in CUSTOM3 for the shader).
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
	var uw := {}
	if args.size() > 2:
		uw = JSON.parse_string(FileAccess.get_file_as_string(str(args[2])))
	for name in KEEP:
		var s := _surface(body, name)
		var ca := body.surface_get_arrays(s)
		var shapes := body.surface_get_blend_shape_arrays(s)
		var place := PackedFloat32Array()
		if not uw.is_empty():
			if name == "ARD_guernsey":
				var r := _unfold(ca, shapes, uw["g"], uw["t"])
				ca = r[0]
				shapes = r[1]
				place = r[2]
			else:
				place = _places(ca, uw["s"])
		_store(out, body, base, name, code, ca, shapes, place)
	root.free()
	base_root.free()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))
	var path := "%s/%s.res" % [OUT_DIR, code]
	var err := ResourceSaver.save(out, path, ResourceSaver.FLAG_COMPRESS)
	print("wrote %s (%d)" % [path, err])
	quit(0 if err == OK else 1)


## Surface name of the cut body, stored against the same surface of the shared body: the points the
## shared surface already has are named by number; only the points the cut added are kept.
func _store(out: ArrayMesh, body: ArrayMesh, base: ArrayMesh, name: String, code: String, ca: Array,
		cshapes: Array, place: PackedFloat32Array) -> void:
	var cs := _surface(body, name)
	var bs := _surface(base, name)
	var ba := base.surface_get_arrays(bs)
	var lookup := {}
	var bv: PackedVector3Array = ba[Mesh.ARRAY_VERTEX]
	for i in range(bv.size()):
		lookup[_key(ba, i)] = i
	var cv: PackedVector3Array = ca[Mesh.ARRAY_VERTEX]
	var remap := PackedInt32Array()
	remap.resize(cv.size())
	var added := PackedInt32Array()
	var taken := {}
	for i in range(cv.size()):
		var k := _key(ca, i)
		# a point split where the pattern's pieces part: the first copy is the shared point, the others added
		if lookup.has(k) and not taken.has(lookup[k]):
			remap[i] = lookup[k]
			taken[lookup[k]] = true
		else:
			remap[i] = bv.size() + added.size()
			added.append(i)
	var index := PackedInt32Array()
	for i in (ca[Mesh.ARRAY_INDEX] as PackedInt32Array):
		index.append(remap[i])
	# Matched points must also carry the shared point's morphs, or the swap would move them.
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
	if place.size() > 0:
		var at := PackedFloat32Array()
		at.resize((bv.size() + added.size()) * 2)
		at.fill(0.0)
		for i in range(cv.size()):
			at[remap[i] * 2] = place[i * 2]
			at[remap[i] * 2 + 1] = place[i * 2 + 1]
		out.set_meta(name + "_unwrap", at)
	print("%s %s: %d points (%d shared, %d added), worst morph gap %.6f m" % [
			code, name, cv.size(), cv.size() - added.size(), added.size(), worst])


## The guernsey surface split into unwrap.py's pattern points g ([x, y, z, u0, v0, U, V], found by place and uv)
## and triangles t (each kept in the cut's own winding): [arrays, morph arrays, places (1 + U, 1 + V a point)].
func _unfold(ca: Array, shapes: Array, g: Array, t: Array) -> Array:
	var cv: PackedVector3Array = ca[Mesh.ARRAY_VERTEX]
	var cu: PackedVector2Array = ca[Mesh.ARRAY_TEX_UV]
	var grid := _grid(cv)
	# each pattern point's possible cut points (a hard edge leaves two cut points at one place and uv)
	var cand := []
	for p in g:
		var c := _near_all(grid, cv, cu, Vector3(p[0], p[1], p[2]), Vector2(p[3], p[4]))
		if c.is_empty():
			push_error("cut_res: pattern point not on the cut %s" % [p])
			return [ca, shapes, PackedFloat32Array()]
		cand.append(c)
	var ci: PackedInt32Array = ca[Mesh.ARRAY_INDEX]
	var tri_of := {}
	for j in range(0, ci.size(), 3):
		for k in range(3):
			if not tri_of.has(ci[j + k]):
				tri_of[ci[j + k]] = PackedInt32Array()
			tri_of[ci[j + k]].append(j)
	# each pattern triangle takes the cut triangle whose corners are its corners, in the cut's winding;
	# each (pattern point, cut point) pair is one point of the result
	var pair := {}
	var src := PackedInt32Array()
	var place := PackedFloat32Array()
	var index := PackedInt32Array()
	var used_tri := {}
	var lost := 0
	for tt in t:
		var pa := [int(tt[0]), int(tt[1]), int(tt[2])]
		var found := -1
		var assign := [-1, -1, -1]
		for c0 in cand[pa[0]]:
			for j in tri_of.get(c0, PackedInt32Array()):
				var taken := [false, false, false]
				var ok := true
				for k in range(3):
					var hit := -1
					for q in range(3):
						if not taken[q] and (cand[pa[q]] as PackedInt32Array).has(ci[j + k]):
							hit = q
							break
					if hit < 0:
						ok = false
						break
					taken[hit] = true
					assign[k] = hit
				if ok:
					found = j
					break
			if found >= 0:
				break
		if found < 0:
			lost += 1
			continue
		used_tri[found] = true
		for k in range(3):
			var pp: int = pa[assign[k]]
			var key := Vector2i(pp, ci[found + k])
			if not pair.has(key):
				pair[key] = src.size()
				src.append(ci[found + k])
				place.append(1.0 + float(g[pp][5]))
				place.append(1.0 + float(g[pp][6]))
			index.append(pair[key])
	var a := _pick(ca, src)
	a[Mesh.ARRAY_INDEX] = index
	print("unfold: %d points (%d before), %d triangles (%d before), pattern triangles not found %d, cut triangles left out %d" % [
			src.size(), cv.size(), index.size() / 3, ci.size() / 3, lost, ci.size() / 3 - used_tri.size()])
	var picked: Array[Array] = []
	for sh in shapes:
		picked.append(_pick(sh, src))
	return [a, picked, place]


## The skin's points that wear the guernsey (unwrap.py's s): their places, 0 for the rest.
func _places(ca: Array, s: Array) -> PackedFloat32Array:
	var cv: PackedVector3Array = ca[Mesh.ARRAY_VERTEX]
	var cu: PackedVector2Array = ca[Mesh.ARRAY_TEX_UV]
	var grid := _grid(cv)
	var out := PackedFloat32Array()
	out.resize(cv.size() * 2)
	out.fill(0.0)
	var hit := 0
	for p in s:
		var i := _nearest(grid, cv, cu, Vector3(p[0], p[1], p[2]), Vector2(p[3], p[4]))
		if i >= 0:
			out[i * 2] = 1.0 + float(p[5])
			out[i * 2 + 1] = 1.0 + float(p[6])
			hit += 1
	print("skin points wearing the pattern: %d of %d" % [hit, s.size()])
	return out


## The points in 1 mm boxes, to find a point by place.
func _grid(cv: PackedVector3Array) -> Dictionary:
	var grid := {}
	for i in range(cv.size()):
		var k := Vector3i((cv[i] * 1000.0).floor())
		if not grid.has(k):
			grid[k] = PackedInt32Array()
		grid[k].append(i)
	return grid


## The cut's point at place v with uv (Godot's import welds equal points and rounds; the pattern was
## measured on the file): the closest within 0.1 mm and 0.0001 uv, or -1.
func _nearest(grid: Dictionary, cv: PackedVector3Array, cu: PackedVector2Array, v: Vector3, uv: Vector2) -> int:
	var k := Vector3i((v * 1000.0).floor())
	var best := -1
	var bd := 1e9
	for dx in range(-1, 2):
		for dy in range(-1, 2):
			for dz in range(-1, 2):
				for i in grid.get(k + Vector3i(dx, dy, dz), PackedInt32Array()):
					var d := cv[i].distance_to(v) + cu[i].distance_to(uv)
					if d < bd:
						bd = d
						best = i
	return best if bd < 2e-4 else -1


## All the cut's points at place v with uv, within the same 0.1 mm and 0.0001 uv as _nearest.
func _near_all(grid: Dictionary, cv: PackedVector3Array, cu: PackedVector2Array, v: Vector3, uv: Vector2) -> PackedInt32Array:
	var k := Vector3i((v * 1000.0).floor())
	var out := PackedInt32Array()
	for dx in range(-1, 2):
		for dy in range(-1, 2):
			for dz in range(-1, 2):
				for i in grid.get(k + Vector3i(dx, dy, dz), PackedInt32Array()):
					if cv[i].distance_to(v) + cu[i].distance_to(uv) < 2e-4:
						out.append(i)
	return out


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
