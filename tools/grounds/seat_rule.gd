extends RefCounted
## The seat rule every ground's instanced seats (assets/grounds/<slug>/seats_*.bin) are held to,
## shared by tools/grounds/seat_check.gd (which applies it) and tests/run_ground_seats_tests.gd (which
## keeps it applied). Every ground's seats come from its own build (kit/build.py, the MCG's and
## Adelaide's own generators, Riverway's ...), and none of them checked the model the seats sit in.
## Looks only: nothing reads back into play.
##
## A seat stays when all of these hold (measured at the middle of the seat's pan, in the model's
## own metres):
##   - FLOOR: the model has a floor under it, no further below than the ground's usual seat sits
##     above its tread plus FLOAT_SLACK (rows past the back of a tier, seats over a stair void).
##   - HEADROOM: nothing of the model (a roof, the tier above, a box floor, an aisle stair) within
##     HEADROOM of that floor (a seated supporter's head through a roof or a tier's underside).
##   - FIELD: it is outside the boundary fence once the model is laid on the match ground.
##   - COMPANY: after the rules above it still has a neighbour within NEIGHBOUR m (no lone
##     seats left behind on a stair or a ledge).

## How far below the ground's usual drop (median seat-to-floor) a floor may be before a seat floats.
const FLOAT_SLACK := 0.6
## Clear height over a seat's floor (m): stadium guides ask about 2.1 m over a seating tier; a
## seated supporter's head stands about 1.3 m above the tread.
const HEADROOM := 2.0
## A kept seat needs another kept seat this close (m); seats are 0.5 m apart, rows 0.8-0.9 m.
const NEIGHBOUR := 1.0
## How far down the floor ray looks (m).
const LOOK_DOWN := 6.0

var _tms := []


## Every ground folder with instanced seats.
static func grounds() -> Array:
	var out := []
	for f in DirAccess.get_directories_at(GroundModels.DIR):
		if not _seat_files(GroundModels.DIR + f + "/").is_empty():
			out.append(f)
	return out


static func _seat_files(dir: String) -> Array:
	return Array(DirAccess.get_files_at(dir)).filter(func(n): return n.begins_with("seats_") and n.ends_with(".bin"))


## Every mesh of the model as a triangle mesh in the model's own metres (no fit), so rays find
## its faces; the seats are MultiMeshes and are not part of it.
func _collide(model: Node3D) -> void:
	_tms.clear()
	for c in model.find_children("*", "MeshInstance3D", true, false):
		var mi := c as MeshInstance3D
		if mi.mesh == null:
			continue
		var tm := mi.mesh.generate_triangle_mesh()
		if tm == null:
			continue
		var xf := model.global_transform.affine_inverse() * mi.global_transform
		_tms.append([xf, xf.affine_inverse(), tm, xf * mi.get_aabb()])


## The nearest face from a towards b: its point, or null for none.
func _ray(a: Vector3, b: Vector3):
	var best = null
	var bd := INF
	for t in _tms:
		if not (t[3] as AABB).grow(0.05).intersects_segment(a, b):
			continue
		var inv: Transform3D = t[1]
		var h: Dictionary = (t[2] as TriangleMesh).intersect_segment(inv * a, inv * b)
		if h.is_empty():
			continue
		var p: Vector3 = (t[0] as Transform3D) * Vector3(h["position"])
		if a.distance_to(p) < bd:
			bd = a.distance_to(p)
			best = p
	return best


## Checks every seat of `slug` (its model built under `parent` and freed after); `write` takes the
## failing seats out of the files. Returns {seats, removed, usual_drop, why: {rule: n}, spots:
## [[x, y, z, rule, drop, clear], ...] for each failing seat in the model's own metres}.
func check(slug: String, parent: Node, write := false) -> Dictionary:
	var dir := GroundModels.DIR + slug + "/"
	var model := Node3D.new()
	parent.add_child(model)
	for path in GroundModels.files(slug, dir):
		var m := GroundModels.load_glb(path)
		if m != null:
			model.add_child(m)
	_collide(model)
	# The middle of the seat's pan (the template's points round its origin, at its origin's height).
	var mid := Vector3.ZERO
	var pts := GroundModels.seat_points(slug)
	for q in pts:
		mid += q
	mid = mid / maxf(1.0, pts.size())
	mid.y = 0.0
	# Every match is played on the model's own field (#1949), so the fence is the model's own.
	MatchMotion.use_field(GroundModels.field(slug))
	var fit := GroundModels.fit_transform(slug)
	var fx := GroundModels.match_fence().x
	var fz := GroundModels.match_fence().y
	# Every seat file, every seat: its spot, its floor and what stands over it.
	var files := _seat_files(dir)
	var bufs := {}
	var spots := []   # [file, index, p, drop, clear, in_field]
	for f in files:
		var buf := FileAccess.get_file_as_bytes(dir + f).to_float32_array()
		bufs[f] = buf
		for i in range(0, buf.size() - 11, 12):
			var t := Transform3D(Basis(Vector3(buf[i], buf[i + 4], buf[i + 8]),
					Vector3(buf[i + 1], buf[i + 5], buf[i + 9]), Vector3(buf[i + 2], buf[i + 6], buf[i + 10])),
					Vector3(buf[i + 3], buf[i + 7], buf[i + 11]))
			var p := t * mid
			var fl = _ray(p + Vector3(0, 0.25, 0), p - Vector3(0, LOOK_DOWN, 0))
			var drop := INF if fl == null else p.y - float(fl.y)
			var base := p.y - 0.3 if fl == null else float(fl.y)
			var up = _ray(Vector3(p.x, maxf(base, p.y) + 0.05, p.z), Vector3(p.x, base + HEADROOM + 0.05, p.z))
			var clear := INF if up == null else float(up.y) - base
			var g := fit * p
			var in_field := pow(g.x / fx, 2) + pow(g.z / fz, 2) < 1.0
			spots.append([f, i / 12, p, drop, clear, in_field])
	# The ground's usual drop from the pan's middle to the tread (its seat's own height).
	var drops := []
	for s in spots:
		if s[3] < INF:
			drops.append(s[3])
	drops.sort()
	var usual := float(drops[drops.size() / 2]) if not drops.is_empty() else 0.5
	var why := {"floor": 0, "headroom": 0, "field": 0, "company": 0}
	var keep := []
	keep.resize(spots.size())
	for k in spots.size():
		var s: Array = spots[k]
		var reason := ""
		if s[3] > usual + FLOAT_SLACK:
			reason = "floor"
		elif s[4] < HEADROOM:
			reason = "headroom"
		elif s[5]:
			reason = "field"
		keep[k] = reason == ""
		if reason != "":
			why[reason] += 1
			s.append(reason)
	# Company: a grid of kept seats; a seat with no kept seat within NEIGHBOUR goes.
	var grid := {}
	for k in spots.size():
		if keep[k]:
			var p: Vector3 = spots[k][2]
			var key := Vector3i(floori(p.x / NEIGHBOUR), floori(p.y / NEIGHBOUR), floori(p.z / NEIGHBOUR))
			if not grid.has(key):
				grid[key] = []
			grid[key].append(k)
	var lonely := []
	for k in spots.size():
		if not keep[k]:
			continue
		var p: Vector3 = spots[k][2]
		var c := Vector3i(floori(p.x / NEIGHBOUR), floori(p.y / NEIGHBOUR), floori(p.z / NEIGHBOUR))
		var found := false
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				for dz in [-1, 0, 1]:
					for j in grid.get(c + Vector3i(dx, dy, dz), []):
						if j != k and (spots[j][2] as Vector3).distance_to(p) <= NEIGHBOUR:
							found = true
							break
					if found:
						break
				if found:
					break
			if found:
				break
		if not found:
			lonely.append(k)
	for k in lonely:
		keep[k] = false
		why["company"] += 1
		spots[k].append("company")
	# Write the kept seats back, each file in its own order.
	var removed := spots.size() - keep.count(true)
	if write and removed > 0:
		var kept := {}
		for f in files:
			kept[f] = PackedFloat32Array()
		for k in spots.size():
			if keep[k]:
				var s: Array = spots[k]
				kept[s[0]].append_array((bufs[s[0]] as PackedFloat32Array).slice(int(s[1]) * 12, int(s[1]) * 12 + 12))
		for f in files:
			var path := ProjectSettings.globalize_path(dir + f)
			if (kept[f] as PackedFloat32Array).is_empty():
				DirAccess.remove_absolute(path)
				continue
			var fh := FileAccess.open(path, FileAccess.WRITE)
			fh.store_buffer((kept[f] as PackedFloat32Array).to_byte_array())
			fh.close()
	var out_spots := []
	for k in spots.size():
		if not keep[k]:
			var s: Array = spots[k]
			var p: Vector3 = s[2]
			out_spots.append([snappedf(p.x, 0.1), snappedf(p.y, 0.1), snappedf(p.z, 0.1), s[s.size() - 1],
					snappedf(minf(float(s[3]), 99.0), 0.01), snappedf(minf(float(s[4]), 99.0), 0.01)])
	model.queue_free()
	return {"seats": spots.size(), "removed": removed, "usual_drop": snappedf(usual, 0.01),
			"why": why, "spots": out_spots}
