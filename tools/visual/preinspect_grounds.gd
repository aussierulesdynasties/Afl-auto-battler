extends SceneTree
## A pre-inspection pass over every ground with a model in a match (row 202 2b), before the
## director's own fly-through: each ground built exactly as a match builds it (Oval3D), filmed
## from a fixed set of cameras, and measured for faults a machine can see without taste:
##   - anything of the model standing inside the boundary fence (rays down from above the arena),
##   - the fence: a level ray out from the middle every degree, where it first meets the model,
##   - holes to the void just outside the fence (rays down on the ring past the fence),
##   - the seats: one floating above its floor, one with the model through it, one inside the fence,
##   - how far the fit stretches the model (GroundModels.stretch) and how tall it stands.
##   godot --path . --rendering-method mobile --script tools/visual/preinspect_grounds.gd -- OUTDIR [W H] [GROUND ...]
## Saves OUTDIR/<slug>/<shot>.png and OUTDIR/<slug>/measure.json; prints one MEASURE line per ground.
## Looks only: nothing here changes a match.

## The match's fence at the ground being filmed (it plays at its own size: GroundModels.field).
static var FX: float:
	get: return GroundModels.match_fence().x
static var FZ: float:
	get: return GroundModels.match_fence().y


func _shots() -> Array:
	var s := [
		["high", Vector3(60, 170, 150), Vector3(0, 0, 0), 50.0],
		["wing_n", Vector3(0, 30, 80), Vector3(0, 0, 0), 55.0],
		["wing_s", Vector3(0, 30, -80), Vector3(0, 0, 0), 55.0],
		["end_w", Vector3(-82, 24, 0), Vector3(20, 0, 0), 55.0],
		["end_e", Vector3(82, 24, 0), Vector3(-20, 0, 0), 55.0],
		["goals_w", Vector3(-62, 3, 0), Vector3(-MatchMotion.GOAL_X, 5, 0), 60.0],
		["goals_e", Vector3(62, 3, 0), Vector3(MatchMotion.GOAL_X, 5, 0), 60.0],
		["outside_s", Vector3(0, 140, -420), Vector3(0, 0, 0), 45.0],
		["outside_e", Vector3(420, 140, 0), Vector3(0, 0, 0), 45.0],
	]
	# At the fence, 2 m up, looking out at the stand: six round the ground.
	for a in [0, 60, 120, 180, 240, 300]:
		var d := Vector3(cos(deg_to_rad(a)), 0, sin(deg_to_rad(a)))
		var p := Vector3(d.x * FX * 0.86, 2.0, d.z * FZ * 0.86)
		var t := Vector3(d.x * FX * 1.3, 9.0, d.z * FZ * 1.3)
		s.append(["fence_%03d" % a, p, t, 70.0])
	return s


func _initialize() -> void:
	_run.call_deferred()
	create_timer(7200.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var size := Vector2i(960, 540)
	var only := []
	if args.size() >= 3 and str(args[1]).is_valid_int():
		size = Vector2i(int(args[1]), int(args[2]))
		only = args.slice(3)
	else:
		only = args.slice(1)
	root.size = size
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	OS.low_processor_usage_mode = false
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	var grounds: Array = GroundModels.grounds()
	if not only.is_empty():
		grounds = grounds.filter(func(g): return only.has(g) or only.has(GroundModels.slug_for(g)))
	for g in grounds:
		var slug := GroundModels.slug_for(str(g))
		var dir := out.path_join(slug)
		DirAccess.make_dir_recursive_absolute(dir)
		var d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		var oval = load("res://scripts/ui/match/Oval3D.gd").new()
		oval.ground = str(g)
		root.add_child(oval)
		oval.build(d, "FRE", "STK")
		oval.set_process(false)
		var ground := oval.get_node_or_null("Ground") as Node3D
		var m := {"ground": str(g), "slug": slug}
		if ground == null:
			m["error"] = "no Ground node"
		else:
			_collide(ground)
			m.merge(_measure(slug, ground))
		var f := FileAccess.open(dir.path_join("measure.json"), FileAccess.WRITE)
		f.store_string(JSON.stringify(m, "  "))
		f.close()
		print("MEASURE %s %s" % [slug, JSON.stringify(m.get("summary", m))])
		if OS.get_environment("PREINSPECT_NO_SHOTS") != "":
			oval.queue_free()
			await process_frame
			continue
		var cam: Camera3D = oval.camera
		cam.far = 3000.0
		for s in _shots():
			cam.global_position = s[1]
			cam.look_at(s[2], Vector3.UP)
			cam.fov = s[3]
			for i in 6:
				await process_frame
			root.get_viewport().get_texture().get_image().save_png(dir.path_join("%s.png" % s[0]))
		oval.queue_free()
		for i in 3:
			await process_frame
	quit(0)


## Every mesh of the model as a triangle mesh, so rays find its faces (as the fly-through's
## floor drop does; physics colliders missed most faces of the big one-mesh models).
var _tms := []


func _collide(ground: Node3D) -> void:
	_tms.clear()
	for c in ground.find_children("*", "MeshInstance3D", true, false):
		var mi := c as MeshInstance3D
		if mi.mesh == null:
			continue
		var tm := mi.mesh.generate_triangle_mesh()
		if tm == null:
			continue
		_tms.append([mi.global_transform, mi.global_transform.affine_inverse(), tm,
				mi.global_transform * mi.get_aabb()])


## The nearest face from a towards b: {"position": ...} in the ground's metres, {} for none.
func _ray(_space, a: Vector3, b: Vector3) -> Dictionary:
	var best := {}
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
			best = {"position": p}
	return best


## Inside the fence ellipse scaled by k.
func _inside(p: Vector3, k := 1.0) -> bool:
	return pow(p.x / (FX * k), 2) + pow(p.z / (FZ * k), 2) < 1.0


func _measure(slug: String, ground: Node3D) -> Dictionary:
	var space = null
	var r := {}
	var st := GroundModels.stretch(slug)
	r["stretch"] = [snappedf(st.x, 0.001), snappedf(st.y, 0.001)]
	# How big the model stands once laid on the ground.
	var lo := Vector3(INF, INF, INF)
	var hi := -lo
	for c in ground.find_children("*", "MeshInstance3D", true, false):
		var mi := c as MeshInstance3D
		if mi.mesh == null:
			continue
		var box := mi.global_transform * mi.get_aabb()
		lo = lo.min(box.position)
		hi = hi.max(box.end)
	r["bounds"] = [[snappedf(lo.x, 0.1), snappedf(lo.y, 0.1), snappedf(lo.z, 0.1)],
			[snappedf(hi.x, 0.1), snappedf(hi.y, 0.1), snappedf(hi.z, 0.1)]]
	# Inside the fence: rays down on a 1.5 m grid; anything higher than 0.3 m stands on the arena.
	var intr := []
	var rays := 0
	var roofed := 0
	var x := -FX
	while x <= FX:
		var z := -FZ
		while z <= FZ:
			var p := Vector3(x, 0, z)
			if _inside(p, 0.985):
				rays += 1
				# From 12 m down, under any roof over the arena (a roof is counted on its own).
				var h := _ray(space, Vector3(x, 12, z), Vector3(x, -30, z))
				if _ray(space, Vector3(x, 12, z), Vector3(x, 300, z)).size() > 0:
					roofed += 1
				if not h.is_empty() and float(h["position"].y) > 0.3:
					intr.append([snappedf(x, 0.1), snappedf(float(h["position"].y), 0.01), snappedf(z, 0.1)])
			z += 1.5
		x += 1.5
	r["inside_rays"] = rays
	r["inside_hits"] = intr
	r["inside_roofed"] = roofed
	# Model goalposts or anything thin on the goal lines (finer grid there).
	var posts := []
	for gx in [-MatchMotion.GOAL_X, MatchMotion.GOAL_X]:
		for i in range(-80, 81):
			for j in range(-4, 5):
				var px := float(gx) + j * 0.25
				var pz := i * 0.25
				var h := _ray(space, Vector3(px, 30, pz), Vector3(px, -5, pz))
				if not h.is_empty() and float(h["position"].y) > 0.3:
					posts.append([snappedf(px, 0.1), snappedf(float(h["position"].y), 0.01), snappedf(pz, 0.1)])
	r["goal_line_hits"] = posts
	# The fence: a level ray out from the middle every degree, 0.6 m up.
	var fence := []
	for a in 360:
		var d := Vector3(cos(deg_to_rad(a)), 0, sin(deg_to_rad(a)))
		var e := 1.0 / sqrt(pow(d.x / FX, 2) + pow(d.z / FZ, 2))
		var h := _ray(space, Vector3(0, 0.6, 0), d * 600.0 + Vector3(0, 0.6, 0))
		var dist := -1.0 if h.is_empty() else Vector2(h["position"].x, h["position"].z).length()
		fence.append([a, snappedf(e, 0.1), snappedf(dist, 0.1)])
	r["fence_rays"] = fence
	# The ring just past the fence (to 14 m out): rays down; none is a hole to the void.
	var ring := []
	var ring_n := 0
	for a in range(0, 360, 2):
		var d := Vector3(cos(deg_to_rad(a)), 0, sin(deg_to_rad(a)))
		var e := 1.0 / sqrt(pow(d.x / FX, 2) + pow(d.z / FZ, 2))
		for k in [1.0, 4.0, 8.0, 14.0]:
			var p: Vector3 = d * (e + k)
			ring_n += 1
			var h := _ray(space, p + Vector3(0, 120, 0), p + Vector3(0, -60, 0))
			if h.is_empty():
				ring.append([a, k, "none"])
			elif float(h["position"].y) < -3.0:
				ring.append([a, k, snappedf(float(h["position"].y), 0.1)])
	r["ring_rays"] = ring_n
	r["ring_holes"] = ring
	# The seats, in the model's own metres -> the ground.
	var seats := GroundModels.seat_transforms(slug)
	r["seats"] = seats.size()
	var step := maxi(1, seats.size() / 4000)
	var drops := []
	var floating := []
	var buried := []
	var in_fence := []
	var n := 0
	# Probe under the middle of the seat's pan, not at its origin (a kit seat's origin is the back
	# edge of its tread, right on the riser, where a ray slips down the crack).
	var mid := Vector3.ZERO
	var pts := GroundModels.seat_points(slug)
	for q in pts:
		mid += q
	mid = mid / maxf(1.0, pts.size())
	mid.y = 0.0
	for i in range(0, seats.size(), step):
		var t: Transform3D = ground.global_transform * seats[i]
		var p := t * mid
		n += 1
		if _inside(p):
			in_fence.append([snappedf(p.x, 0.1), snappedf(p.y, 0.1), snappedf(p.z, 0.1)])
		var h := _ray(space, p + Vector3(0, 0.25, 0), p + Vector3(0, -4.0, 0))
		var drop := 99.0 if h.is_empty() else p.y - float(h["position"].y)
		drops.append(drop)
		if drop > 0.9:
			floating.append([snappedf(p.x, 0.1), snappedf(p.y, 0.1), snappedf(p.z, 0.1), snappedf(drop, 0.01)])
		var up := _ray(space, p + Vector3(0, 0.3, 0), p + Vector3(0, 1.1, 0))
		if not up.is_empty():
			buried.append([snappedf(p.x, 0.1), snappedf(p.y, 0.1), snappedf(p.z, 0.1),
					snappedf(float(up["position"].y) - p.y, 0.01)])
	drops.sort()
	r["seats_checked"] = n
	r["seat_drop_median"] = snappedf(drops[drops.size() / 2], 0.01) if not drops.is_empty() else null
	r["seats_floating"] = floating
	r["seats_buried"] = buried
	r["seats_in_fence"] = in_fence
	var gaps := fence.filter(func(f): return f[2] < 0 or f[2] > f[1] + 10.0)
	var shorts := fence.filter(func(f): return f[2] >= 0 and f[2] < f[1] - 1.0)
	r["summary"] = {
		"stretch": r["stretch"], "height": snappedf(hi.y, 0.1),
		"inside_hits": intr.size(), "roofed": roofed, "goal_line_hits": posts.size(),
		"fence_far_or_none_deg": gaps.size(), "fence_short_deg": shorts.size(),
		"ring_holes": ring.size(), "seats": seats.size(), "seats_checked": n,
		"seat_drop_median": r["seat_drop_median"], "seats_floating": floating.size(),
		"seats_buried": buried.size(), "seats_in_fence": in_fence.size(),
	}
	return r
