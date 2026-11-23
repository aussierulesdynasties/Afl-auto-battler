extends SceneTree
## Part two baked animations that pass through each other (a speccy's jumper and his stepladder,
## baked from one pair fit with tools/oval3d/bake_fit.gd). The fit keeps the two men apart, but
## our body's limbs are a little longer than the fit's (about 12% in the legs), so the bake can put
## a shin inside a back. Each frame, the deepest overlap is undone half by each man, by the part
## that overlaps: a leg is swung at the hip and an arm at the shoulder (ball joints, which the
## match's joint limits leave free, up to MAX_TURN), so a knee slides along the back it rests on;
## a trunk or head, or a limb past that, moves the whole man across the ground, and the jumper
## pushed up off the other man's back or shoulders is lifted (he sits on him). The turns and moves are then smoothed over time and the
## parting repeated, so a contact stays a touch and nothing jumps. Capsules as check_pair.gd.
##   godot --headless --path . --script tools/oval3d/settle_pair.gd -- A.res B.res A_OUT.res B_OUT.res [HZ]

const Check := preload("res://tools/oval3d/check_pair.gd")
const GLB := "res://assets/oval3d/player_mh.glb"
const GAP := 0.005    # metres left between kit at a touch
# Which ball joint swings each capsule (check_pair.gd's parts, named by their first bone).
const SWING := {"thigh_l": "thigh_l", "calf_l": "thigh_l", "foot_l": "thigh_l",
		"thigh_r": "thigh_r", "calf_r": "thigh_r", "foot_r": "thigh_r",
		"upperarm_l": "upperarm_l", "lowerarm_l": "upperarm_l",
		"upperarm_r": "upperarm_r", "lowerarm_r": "upperarm_r"}
const JOINTS := ["thigh_l", "thigh_r", "upperarm_l", "upperarm_r"]
const MAX_TURN := 30.0   # deg a limb may be swung from the film's pose


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
	# Held inside a real body's joint limits, as the match plays it.
	ClipLimits.apply(ap, sk)
	ap.play("pair/clip")
	return [ap, sk, anim]


func _track(anim: Animation, bone: String, type: int) -> int:
	for t in anim.get_track_count():
		if anim.track_get_type(t) == type and str(anim.track_get_path(t)).get_slice(":", 1) == bone:
			return t
	return -1


# The pelvis's pose position for a move across the world.
func _local(sk: Skeleton3D, world: Vector3) -> Vector3:
	var ip := sk.find_bone("pelvis")
	var par := sk.get_bone_parent(ip)
	var pb := sk.get_bone_global_pose(par).basis if par >= 0 else Basis.IDENTITY
	return (sk.global_transform.basis * pb).inverse() * world


## One man posed at t, moved by off (world) and each swing joint turned by its rotation vector
## (world axis times angle) about its head.
func _pose(p: Array, t: float, off: Vector3, turns: Dictionary) -> void:
	(p[0] as AnimationPlayer).seek(t, true)
	var sk: Skeleton3D = p[1]
	var ip := sk.find_bone("pelvis")
	sk.set_bone_pose_position(ip, sk.get_bone_pose_position(ip) + _local(sk, off))
	var wb := sk.global_transform.basis.orthonormalized()
	for j in turns:
		var rv: Vector3 = turns[j]
		if rv.length() < 1e-6:
			continue
		var b := sk.find_bone(j)
		var q := Quaternion((wb.inverse() * rv).normalized(), rv.length())
		var par := sk.get_bone_parent(b)
		var pb := sk.get_bone_global_pose(par).basis if par >= 0 else Basis.IDENTITY
		var g := Basis(q) * sk.get_bone_global_pose(b).basis
		sk.set_bone_pose_rotation(b, (pb.inverse() * g).get_rotation_quaternion())


# The deepest overlap between the two bodies: [clearance, direction from B's part to A's,
# A's touching point, B's, A's part, B's part].
func _deepest(a: Skeleton3D, b: Skeleton3D) -> Array:
	var best := [INF, Vector3.UP, Vector3.ZERO, Vector3.ZERO, "", ""]
	for x in Check._caps(a):
		for y in Check._caps(b):
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
			if cl < best[0]:
				var n := (pa - pb).normalized() if d > 1e-4 else Vector3.UP
				best = [cl, n, pa, pb, x[3], y[3]]
	return best


## Move one man's touching point by v: by swinging the limb that holds it, or, for his trunk or
## head, by moving him across the ground.
func _give(sk: Skeleton3D, part: String, at: Vector3, v: Vector3, off: Array, turns: Array, k: int, lift := false) -> void:
	# The jumper on the other man's shoulders or back, pushed upward: he is held up by him.
	if lift and v.y > 0.3 * v.length():
		off[k] += v
		return
	if SWING.has(part):
		var j: String = SWING[part]
		var pivot := Check._p(sk, j)
		var r := at - pivot
		var ax := r.cross(v)
		if ax.length() > 1e-6 and r.length() > 0.05:
			var rv := ax.normalized() * (v.length() / r.length())
			# Compose with this frame's turn so far (small turns: rotation vectors add), up to
			# MAX_TURN; past it the whole man gives way instead (a limb swung further than that
			# reads as a different movement from the film's).
			var tot: Vector3 = (turns[k][j] as Vector3) + rv
			if tot.length() <= deg_to_rad(MAX_TURN):
				turns[k][j] = tot
				return
	off[k] += Vector3(v.x, 0.0, v.z)


func _part(a: Array, b: Array, times: Array, oa: Array, ob: Array, ta: Array, tb: Array) -> float:
	var worst := INF
	for k in times.size():
		for it in 100:
			_pose(a, times[k], oa[k], ta[k])
			_pose(b, times[k], ob[k], tb[k])
			var r := _deepest(a[1], b[1])
			if r[0] >= GAP - 1e-4:
				break
			var push: float = (GAP - r[0]) * 0.5 + 0.002
			var n: Vector3 = r[1]
			_give(a[1], r[4], r[2], n * push, oa, ta, k, r[5] in ["pelvis", "head", "upperarm_l", "upperarm_r"])
			_give(b[1], r[5], r[3], -n * push, ob, tb, k)
		_pose(a, times[k], oa[k], ta[k])
		_pose(b, times[k], ob[k], tb[k])
		worst = minf(worst, _deepest(a[1], b[1])[0])
	return worst


# Gaussian over neighbouring frames (sigma 1.5), keeping each frame at least its own size along
# its own line, so smoothing never brings an overlap back.
func _smooth_v(o: Array) -> Array:
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


func _smooth_t(t: Array) -> Array:
	var out := []
	for k in t.size():
		out.append({})
	for j in JOINTS:
		var col := []
		for k in t.size():
			col.append(t[k][j])
		col = _smooth_v(col)
		for k in t.size():
			out[k][j] = col[k]
	return out


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var hz := float(args[4]) if args.size() > 4 else 25.0
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
	var ta := []
	var tb := []
	for k in times.size():
		oa.append(Vector3.ZERO)
		ob.append(Vector3.ZERO)
		var za := {}
		var zb := {}
		for j in JOINTS:
			za[j] = Vector3.ZERO
			zb[j] = Vector3.ZERO
		ta.append(za)
		tb.append(zb)
	var worst := 0.0
	for round in 4:
		worst = _part(a, b, times, oa, ob, ta, tb)
		print("ROUND %d worst clearance %.3f" % [round, worst])
		oa = _smooth_v(oa)
		ob = _smooth_v(ob)
		ta = _smooth_t(ta)
		tb = _smooth_t(tb)
	worst = _part(a, b, times, oa, ob, ta, tb)
	var most := 0.0
	var turn := 0.0
	var big := ""
	for k in times.size():
		most = maxf(most, maxf((oa[k] as Vector3).length(), (ob[k] as Vector3).length()))
		var tk := 0.0
		for j in JOINTS:
			tk = maxf(tk, maxf((ta[k][j] as Vector3).length(), (tb[k][j] as Vector3).length()))
		turn = maxf(turn, tk)
		if (oa[k] as Vector3).length() > 0.1 or (ob[k] as Vector3).length() > 0.1 or tk > deg_to_rad(15.0):
			big += "%d:%.2f/%.2fm,%.0fdeg " % [k, (oa[k] as Vector3).length(), (ob[k] as Vector3).length(), rad_to_deg(tk)]
	print("FINAL worst clearance %.3f, largest move %.3f m, largest turn %.0f deg" % [worst, most, rad_to_deg(turn)])
	print("MOVES over 10 cm or 15 deg (frame: jumper/stepladder move, turn): ", big)
	# Write each frame's posed pelvis place and swing joints' turns into the keys (one key per
	# frame, as bake_fit.gd writes).
	for pr in [[a, oa, ta, str(args[2])], [b, ob, tb, str(args[3])]]:
		var p: Array = pr[0]
		var anim: Animation = p[2]
		var sk: Skeleton3D = p[1]
		var tp := _track(anim, "pelvis", Animation.TYPE_POSITION_3D)
		var tr := {}
		for j in JOINTS:
			tr[j] = _track(anim, j, Animation.TYPE_ROTATION_3D)
		var poses := []
		for k in times.size():
			_pose(p, times[k], pr[1][k], pr[2][k])
			var row := {"pelvis": sk.get_bone_pose_position(sk.find_bone("pelvis"))}
			for j in JOINTS:
				row[j] = sk.get_bone_pose_rotation(sk.find_bone(j))
			poses.append(row)
		for k in times.size():
			var key := anim.track_find_key(tp, times[k], Animation.FIND_MODE_APPROX)
			anim.track_set_key_value(tp, key, poses[k]["pelvis"])
			for j in JOINTS:
				var kj := anim.track_find_key(tr[j], times[k], Animation.FIND_MODE_APPROX)
				anim.track_set_key_value(tr[j], kj, poses[k][j])
		print("SAVED %s %s" % [pr[3], error_string(ResourceSaver.save(anim, pr[3]))])
	quit()
