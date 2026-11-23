extends SceneTree
## Key a speccy's contact by hand, over a fit that cannot see it. The broadcast camera loses the
## jumper's legs behind the stepladder, so the fit leaves them hanging straight; in the footage
## his near knee rides up into the stepladder's back and the other tucks up beside it, and the
## stepladder is bent forward under him. Over the contact frames (eased in and out) this:
##   - bends the stepladder forward at the spine by BEND degrees;
##   - puts the jumper's near knee on the stepladder's upper back (moving the jumper a little if
##     his hip is out of a thigh's reach), with the shin hanging down the back; the knee bends
##     only on its hinge and the thigh twists within a hip's range, so the joint limits keep it;
##   - tucks the other knee up in front of him.
## Shapes are from the footage (Kozzy 2023, frames 50-62). Run after depth_pair.gd.
##   godot --headless --path . --script tools/oval3d/contact_pair.gd -- JUMP.res STEP.res JUMP_OUT.res STEP_OUT.res FROM:IN:OUT:TO [BEND] [HZ]

const Check := preload("res://tools/oval3d/check_pair.gd")
const GLB := "res://assets/oval3d/player_mh.glb"
const SPINE := ["spine_01", "spine_02", "spine_03"]
const HINGE := Vector3(1.0, 0.0, 0.0)
const MOVE_MAX := 0.35   # m the jumper may be moved to bring his knee to the back
const KNEE_OFF := 0.22   # m from the stepladder's spine line to the knee's centre (trunk + knee)
# The stepladder's legs through the contact: the camera loses them behind the pack and the fit
# throws one up in a kick; in the footage he stays braced on both feet. They are held at their
# pose as the contact begins.
const S_LEGS := ["thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r"]


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
	ClipLimits.apply(ap, sk)
	ap.play("pair/clip")
	return [ap, sk, anim]


func _track(anim: Animation, bone: String, type: int) -> int:
	for t in anim.get_track_count():
		if anim.track_get_type(t) == type and str(anim.track_get_path(t)).get_slice(":", 1) == bone:
			return t
	return -1


func _w(f: float, r: Array) -> float:
	if f <= r[0] or f >= r[3]:
		return 0.0
	if f < r[1]:
		return smoothstep(r[0], r[1], f)
	if f > r[2]:
		return 1.0 - smoothstep(r[2], r[3], f)
	return 1.0


# Skeleton space <-> world.
func _ws(sk: Skeleton3D, p: Vector3) -> Vector3:
	return sk.global_transform.affine_inverse() * p


func _wp(sk: Skeleton3D, bone: String) -> Vector3:
	return Check._p(sk, bone)


# Turn a bone (in world terms) by q about its head.
func _turn(sk: Skeleton3D, bone: String, q: Quaternion) -> void:
	var b := sk.find_bone(bone)
	var wb := sk.global_transform.basis.orthonormalized()
	var qs := Quaternion(wb.inverse() * q.get_axis().normalized(), q.get_angle()) if q.get_angle() > 1e-6 else Quaternion.IDENTITY
	var par := sk.get_bone_parent(b)
	var pb := sk.get_bone_global_pose(par).basis if par >= 0 else Basis.IDENTITY
	var g := Basis(qs) * sk.get_bone_global_pose(b).basis
	sk.set_bone_pose_rotation(b, (pb.inverse() * g).get_rotation_quaternion())
	sk.force_update_all_bone_transforms()


func _local(sk: Skeleton3D, world: Vector3) -> Vector3:
	var ip := sk.find_bone("pelvis")
	var par := sk.get_bone_parent(ip)
	var pb := sk.get_bone_global_pose(par).basis if par >= 0 else Basis.IDENTITY
	return (sk.global_transform.basis * pb).inverse() * world


## One leg to a knee and an ankle target: thigh swung to the knee, then the thigh's twist (within
## +-45 deg) and the knee's bend on its hinge chosen so the ankle comes nearest its target.
## The last frame's answer for each leg ([twist, bend]); a frame's answer is kept near it, so the
## leg cannot flip between two far-apart ways of reaching the same spot.
var _prev := {}


func _leg(sk: Skeleton3D, side: String, knee: Vector3, ankle: Vector3) -> float:
	var th := "thigh_" + side
	var ca := "calf_" + side
	var hip := _wp(sk, th)
	var kn := _wp(sk, ca)
	_turn(sk, th, Quaternion((kn - hip).normalized(), (knee - hip).normalized()))
	var axis := (_wp(sk, ca) - _wp(sk, th)).normalized()
	var ic := sk.find_bone(ca)
	var rest := sk.get_bone_rest(ic).basis.get_rotation_quaternion()
	var it := sk.find_bone(th)
	var base_th := sk.get_bone_pose_rotation(it)
	var pv: Array = _prev.get(side, [])
	var best := [INF, 0.0, 0.0, INF]
	for pass_i in 2:
		var c_phi: float = best[1]
		var c_th: float = best[2]
		var span_phi := 45.0 if pass_i == 0 else 6.0
		var span_th := 75.0 if pass_i == 0 else 6.0
		var step := 5.0 if pass_i == 0 else 1.0
		var phi := -span_phi
		while phi <= span_phi + 1e-3:
			var p: float = (c_phi if pass_i == 1 else 0.0) + phi
			sk.set_bone_pose_rotation(it, base_th)
			sk.force_update_all_bone_transforms()
			_turn(sk, th, Quaternion(axis, deg_to_rad(p)))
			var tt := -span_th
			while tt <= span_th + 1e-3:
				var bend: float = (c_th if pass_i == 1 else 75.0) + tt
				sk.set_bone_pose_rotation(ic, rest * Quaternion(HINGE, deg_to_rad(bend)))
				sk.force_update_all_bone_transforms()
				var miss := _wp(sk, "foot_" + side).distance_to(ankle)
				# 1 cm of miss is worth 2.5 deg of change from the last frame.
				var cost := miss
				if not pv.is_empty():
					cost += 0.004 * (absf(p - pv[0]) + absf(bend - pv[1]))
				if cost < best[3]:
					best = [miss, p, bend, cost]
				tt += step
			phi += step
	sk.set_bone_pose_rotation(it, base_th)
	sk.force_update_all_bone_transforms()
	_turn(sk, th, Quaternion(axis, deg_to_rad(best[1])))
	sk.set_bone_pose_rotation(ic, rest * Quaternion(HINGE, deg_to_rad(best[2])))
	sk.force_update_all_bone_transforms()
	_prev[side] = [best[1], best[2]]
	return best[0]


# The deepest overlap between the two bodies: [clearance, direction from B's part to A's,
# A's point, B's point, A's part, B's part] (as settle_pair.gd).
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


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var r := []
	for x in str(args[4]).split(":"):
		r.append(float(x))
	var bend := float(args[5]) if args.size() > 5 else 35.0
	var hz := float(args[6]) if args.size() > 6 else 25.0
	var aj: Animation = (load(str(args[0])) as Animation).duplicate(true)
	var as_: Animation = (load(str(args[1])) as Animation).duplicate(true)
	var j := _body(aj)
	var s := _body(as_)
	var skj: Skeleton3D = j[1]
	var sks: Skeleton3D = s[1]
	var n := int(round(aj.length * hz)) + 1
	# Which leg goes into the back: the one whose knee is nearer the stepladder's upper back at the
	# middle of the contact.
	var mid: float = (r[1] + r[2]) * 0.5 / hz
	for p in [j, s]:
		(p[0] as AnimationPlayer).seek(mid, true)
	var back0 := _wp(sks, "spine_03").lerp(_wp(sks, "neck_01"), 0.6)
	var near := "l" if _wp(skj, "calf_l").distance_to(back0) < _wp(skj, "calf_r").distance_to(back0) else "r"
	var far := "r" if near == "l" else "l"
	print("CONTACT near knee %s, window %s, bend %.0f" % [near, str(r), bend])
	var braced := {}
	(s[0] as AnimationPlayer).seek(r[0] / hz, true)
	for b in S_LEGS:
		braced[b] = sks.get_bone_pose_rotation(sks.find_bone(b))
	var rows := []
	for k in n:
		var t := k / hz
		var w := _w(float(k), r)
		for p in [j, s]:
			(p[0] as AnimationPlayer).seek(t, true)
		var row := {}
		if w <= 0.0:
			rows.append(row)
			continue
		for b in S_LEGS:
			var ib := sks.find_bone(b)
			sks.set_bone_pose_rotation(ib, sks.get_bone_pose_rotation(ib).slerp(braced[b], w))
			row["s_" + b] = sks.get_bone_pose_rotation(ib)
		sks.force_update_all_bone_transforms()
		# The stepladder bent forward at the spine. His back: away from where his chest faces.
		var lat := (_wp(sks, "upperarm_r") - _wp(sks, "upperarm_l")).normalized()
		var back := lat.cross(Vector3.UP).normalized()
		var neck0 := _wp(sks, "neck_01")
		var sgn := 1.0
		_turn(sks, "spine_01", Quaternion(lat, deg_to_rad(10.0)))
		if (_wp(sks, "neck_01") - neck0).dot(back) > 0.0:
			sgn = -1.0
		_turn(sks, "spine_01", Quaternion(lat, deg_to_rad(-10.0)))
		for b in SPINE:
			_turn(sks, b, Quaternion(lat, sgn * deg_to_rad(bend * w / SPINE.size())))
		# The head comes back up a little, to keep his eyes on the ball.
		_turn(sks, "neck_01", Quaternion(lat, -sgn * deg_to_rad(0.4 * bend * w)))
		for b in SPINE + ["neck_01"]:
			row["s_" + b] = sks.get_bone_pose_rotation(sks.find_bone(b))
		# The upper back's outward line, with the bend.
		var sp := _wp(sks, "spine_03")
		var nk := _wp(sks, "neck_01")
		var up_s := (nk - sp).normalized()
		var out_n := (back - up_s * back.dot(up_s)).normalized()
		# The knee high on the back, at the shoulders, and the shin down and out from it.
		var knee_t := sp.lerp(nk, 0.85) + out_n * KNEE_OFF
		var ankle_t := knee_t + (-up_s * 0.7 + out_n * 0.7).normalized() * 0.44
		# The jumper moved, if need be, so his hip is a thigh's length from that knee.
		var hip := _wp(skj, "thigh_" + near)
		var thigh := hip.distance_to(_wp(skj, "calf_" + near))
		var want := knee_t + (hip - knee_t).normalized() * thigh
		var move := (want - hip)
		if move.length() > MOVE_MAX:
			move = move.normalized() * MOVE_MAX
		move *= w
		var ip := skj.find_bone("pelvis")
		skj.set_bone_pose_position(ip, skj.get_bone_pose_position(ip) + _local(skj, move))
		skj.force_update_all_bone_transforms()
		# The knee goes as near the back as the thigh reaches.
		hip = _wp(skj, "thigh_" + near)
		var kt := hip + (knee_t - hip).normalized() * thigh
		var orig := {}
		for b in ["thigh_l", "thigh_r", "calf_l", "calf_r"]:
			orig[b] = skj.get_bone_pose_rotation(skj.find_bone(b))
		var hip2 := _wp(skj, "thigh_" + far)
		var fwd := -out_n
		var side_v := (hip2 - hip).normalized()
		var k2 := hip2 + (fwd * 0.7 + Vector3.UP * 0.45 + side_v * 0.15).normalized() * thigh
		var a2 := k2 + (-Vector3.UP * 0.8 - fwd * 0.6).normalized() * 0.44
		# Eased in by w as places, not as turns: each knee and ankle travels from where the film has
		# it to its contact spot, so the leg never sweeps through the other man on the way.
		var targets := {near: [_wp(skj, "calf_" + near).lerp(kt, w), _wp(skj, "foot_" + near).lerp(ankle_t, w)],
				far: [_wp(skj, "calf_" + far).lerp(k2, w), _wp(skj, "foot_" + far).lerp(a2, w)]}
		var miss := 0.0
		var miss2 := 0.0
		var deep := 0.0
		var last := -INF
		var body := Vector3.ZERO
		# Solved, eased in by w, and checked against the stepladder's body: where a leg of his
		# passes into it, that leg's knee or ankle target is moved out by the overlap and the
		# leg solved again (the leg gives way, not the whole man).
		for it in 14:
			for b in orig:
				skj.set_bone_pose_rotation(skj.find_bone(b), orig[b])
			skj.force_update_all_bone_transforms()
			miss = _leg(skj, near, targets[near][0], targets[near][1])
			miss2 = _leg(skj, far, targets[far][0], targets[far][1])
			# At the window's ends the solved leg is blended back into the film's own turns, so the
			# leg leaves and rejoins the film without a jump.
			var wr := smoothstep(0.0, 0.3, w)
			if wr < 1.0:
				for b in orig:
					var ib := skj.find_bone(b)
					skj.set_bone_pose_rotation(ib, (orig[b] as Quaternion).slerp(skj.get_bone_pose_rotation(ib), wr))
				skj.force_update_all_bone_transforms()
			var d := _deepest(skj, sks)
			if OS.get_environment("CDEBUG") != "":
				print("  it %d %.3f %s %s" % [it, d[0], d[4], d[5]])
			deep = d[0]
			if d[0] >= -0.005:
				break
			# A leg that has stopped giving way (its target out of reach): the jumper himself is
			# moved off, a few centimetres, as a man riding up a back is.
			if d[0] - last < 0.002 and body.length() < 0.15:
				var b_mv: Vector3 = d[1] * (0.01 - d[0])
				body += b_mv
				skj.set_bone_pose_position(ip, skj.get_bone_pose_position(ip) + _local(skj, b_mv))
				skj.force_update_all_bone_transforms()
				last = d[0]
				continue
			last = d[0]
			var part: String = d[4]
			var sd := part.right(1)
			if not (part.begins_with("thigh") or part.begins_with("calf") or part.begins_with("foot")) or not targets.has(sd):
				break
			# Eased in by w, the leg moves only w of the way, so the target moves 1/w as far.
			var push: Vector3 = d[1] * (0.01 - d[0])
			var slot := 0 if part.begins_with("thigh") else 1
			targets[sd][slot] += push
			if slot == 0:
				targets[sd][1] += push
		for b in orig:
			row["j_" + b] = skj.get_bone_pose_rotation(skj.find_bone(b))
		row["j_pelvis"] = skj.get_bone_pose_position(ip)
		print("F %d w %.2f moved %.2f m (+%.2f off him), knee off target %.2f m, ankles off %.2f / %.2f m, deepest %.3f" % [k, w, move.length(), body.length(), _wp(skj, "calf_" + near).distance_to(knee_t), miss, miss2, deep])
		rows.append(row)
	for pr in [[aj, "j_", str(args[2])], [as_, "s_", str(args[3])]]:
		var anim: Animation = pr[0]
		for k in n:
			var row: Dictionary = rows[k]
			for key in row:
				if not str(key).begins_with(pr[1]):
					continue
				var bone := str(key).substr(2)
				var typ := Animation.TYPE_POSITION_3D if bone == "pelvis" else Animation.TYPE_ROTATION_3D
				var tr := _track(anim, bone, typ)
				if tr < 0:
					print("NO TRACK ", bone)
					continue
				var kk := anim.track_find_key(tr, k / hz, Animation.FIND_MODE_APPROX)
				anim.track_set_key_value(tr, kk, row[key])
		print("SAVED %s %s" % [pr[2], error_string(ResourceSaver.save(anim, pr[2]))])
	quit()
