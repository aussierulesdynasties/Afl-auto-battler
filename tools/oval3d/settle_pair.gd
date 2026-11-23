extends SceneTree
## Part two baked animations that pass through each other (a speccy's jumper and his stepladder,
## baked from one pair fit with tools/oval3d/bake_fit.gd). The fit keeps the two men apart, but
## our body's limbs are a little longer than the fit's, so the bake can put a knee inside a back.
## Each frame the two are moved apart by the overlap, half each, along the line between the
## deepest touching parts: the stepladder only across the ground, the jumper also upward (never
## down). The moves are then smoothed over time and the parting repeated, so a contact stays a
## touch and nothing jumps. Capsules as tools/oval3d/check_pair.gd.
##   godot --headless --path . --script tools/oval3d/settle_pair.gd -- A.res B.res A_OUT.res B_OUT.res [HZ]

const Check := preload("res://tools/oval3d/check_pair.gd")
const GLB := "res://assets/oval3d/player_mh.glb"
const GAP := 0.005    # metres left between kit at a touch


func _initialize() -> void:
	_run.call_deferred()


func _body(anim: Animation) -> Array:
	var scene: Node3D = (load(GLB) as PackedScene).instantiate()
	root.add_child(scene)
	var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	var lib := AnimationLibrary.new()
	lib.add_animation("clip", anim)
	ap.add_animation_library("pair", lib)
	ap.play("pair/clip")
	return [ap, sk, anim]


func _pos_track(anim: Animation) -> int:
	for t in anim.get_track_count():
		if anim.track_get_type(t) == Animation.TYPE_POSITION_3D and str(anim.track_get_path(t)).ends_with(":pelvis"):
			return t
	return -1


# The pelvis's pose position for a move across the world.
func _local(sk: Skeleton3D, world: Vector3) -> Vector3:
	var ip := sk.find_bone("pelvis")
	var par := sk.get_bone_parent(ip)
	var pb := sk.get_bone_global_pose(par).basis if par >= 0 else Basis.IDENTITY
	return (sk.global_transform.basis * pb).inverse() * world


func _pose(p: Array, t: float, off: Vector3) -> void:
	(p[0] as AnimationPlayer).seek(t, true)
	var sk: Skeleton3D = p[1]
	var ip := sk.find_bone("pelvis")
	sk.set_bone_pose_position(ip, sk.get_bone_pose_position(ip) + _local(sk, off))


# The deepest overlap between the two bodies: [clearance, direction from B's part to A's].
func _deepest(ck, a: Skeleton3D, b: Skeleton3D) -> Array:
	var best := INF
	var dir := Vector3.ZERO
	for x in ck._caps(a):
		for y in ck._caps(b):
			var pa: Vector3 = x[0]
			var pb: Vector3 = y[0]
			var d := INF
			for i in 21:
				var q: Vector3 = (x[0] as Vector3).lerp(x[1], i / 20.0)
				var c := Geometry3D.get_closest_point_to_segment(q, y[0], y[1])
				if q.distance_to(c) < d:
					d = q.distance_to(c)
					pa = q
					pb = c
			for i in 21:
				var q: Vector3 = (y[0] as Vector3).lerp(y[1], i / 20.0)
				var c := Geometry3D.get_closest_point_to_segment(q, x[0], x[1])
				if q.distance_to(c) < d:
					d = q.distance_to(c)
					pa = c
					pb = q
			var cl: float = d - x[2] - y[2]
			if cl < best:
				best = cl
				dir = (pa - pb).normalized() if d > 1e-4 else Vector3(0, 1, 0)
	return [best, dir]


func _part(ck, a: Array, b: Array, times: Array, oa: Array, ob: Array) -> float:
	var worst := INF
	for k in times.size():
		for it in 30:
			_pose(a, times[k], oa[k])
			_pose(b, times[k], ob[k])
			var r := _deepest(ck, a[1], b[1])
			if r[0] >= GAP - 1e-4:
				break
			var push: float = (GAP - r[0]) * 0.5 + 0.002
			var n: Vector3 = r[1]
			var nh := Vector3(n.x, 0.0, n.z)
			# The stepladder stays on the ground; the jumper may be lifted, never pushed down.
			var ma := Vector3(n.x, maxf(0.0, n.y), n.z)
			if nh.length() > 0.2:
				oa[k] += ma.normalized() * push
				ob[k] -= nh.normalized() * push
			else:
				# Straight down onto him: the jumper is lifted the whole way.
				oa[k] += Vector3(0, 1, 0) * push * 2.0
		_pose(a, times[k], oa[k])
		_pose(b, times[k], ob[k])
		worst = minf(worst, _deepest(ck, a[1], b[1])[0])
	return worst


func _smooth(o: Array) -> Array:
	# Gaussian over neighbouring frames (sigma 1.5), keeping each frame at least its own push's
	# size along the same line, so smoothing never brings an overlap back.
	var out := []
	for k in o.size():
		var s := Vector3.ZERO
		var w := 0.0
		for j in range(maxi(0, k - 5), mini(o.size(), k + 6)):
			var g := exp(-0.5 * pow((j - k) / 1.5, 2))
			s += o[j] * g
			w += g
		var v: Vector3 = s / w
		var own: Vector3 = o[k]
		if own.length() > 1e-6 and v.dot(own.normalized()) < own.length():
			v += own.normalized() * (own.length() - v.dot(own.normalized()))
		out.append(v)
	return out


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var hz := float(args[4]) if args.size() > 4 else 25.0
	var ck = Check
	var aa: Animation = (load(str(args[0])) as Animation).duplicate(true)
	var ab: Animation = (load(str(args[1])) as Animation).duplicate(true)
	var a := _body(aa)
	var b := _body(ab)
	var times := []
	var t := 0.0
	while t <= aa.length + 1e-4:
		times.append(t)
		t += 1.0 / hz
	var oa := []
	var ob := []
	for k in times.size():
		oa.append(Vector3.ZERO)
		ob.append(Vector3.ZERO)
	var worst := 0.0
	for round in 4:
		worst = _part(ck, a, b, times, oa, ob)
		print("ROUND %d worst clearance %.3f" % [round, worst])
		oa = _smooth(oa)
		ob = _smooth(ob)
	worst = _part(ck, a, b, times, oa, ob)
	var most := 0.0
	for k in times.size():
		most = maxf(most, maxf((oa[k] as Vector3).length(), (ob[k] as Vector3).length()))
	print("FINAL worst clearance %.3f, largest move %.3f m" % [worst, most])
	# Write the moves into each pelvis track's keys (one key per frame, as bake_fit.gd writes).
	for pr in [[a, oa, str(args[2])], [b, ob, str(args[3])]]:
		var p: Array = pr[0]
		var anim: Animation = p[2]
		var sk: Skeleton3D = p[1]
		var tr := _pos_track(anim)
		for key in anim.track_get_key_count(tr):
			var kt := anim.track_get_key_time(tr, key)
			var k := clampi(int(round(kt * hz)), 0, times.size() - 1)
			(p[0] as AnimationPlayer).seek(kt, true)
			var v: Vector3 = anim.track_get_key_value(tr, key)
			anim.track_set_key_value(tr, key, v + _local(sk, pr[1][k]))
		print("SAVED %s %s" % [pr[2], error_string(ResourceSaver.save(anim, pr[2]))])
	quit()
