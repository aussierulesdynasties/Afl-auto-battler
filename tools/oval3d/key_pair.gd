extends SceneTree
## Hand-keyed animation for two men in contact (a speccy's jumper and his stepladder), written on
## the match body. The broadcast footage sets only the timing, the path and the key moments; every
## pose is keyed here, because a tracker's guess from one blurry replay twitches, slides and loses
## the men where they overlap (the person, 2026-11-23: the solver-made speccies were "still
## incredibly bad"; real games key contact moves by hand or capture them in a studio).
##
## The spec (JSON) gives each man a list of keys. A key sets any of these channels at its time:
##   pos    the pelvis (a place, below), "air": true makes the hips fly to the next pos key on a
##          gravity arc (9.81 m/s^2), the ground moving at a steady speed;
##   yaw, pitch, roll   the body's facing (deg; yaw 0 faces +z, the camera; pitch leans forward);
##   chest  [bend forward, lean right, turn left] of the chest from the hips, spread up the spine;
##   head   [nod down, turn left] of the head from the chest;
##   foot_l, foot_r, hand_l, hand_r   where the ankle or wrist is (a place), solved by a two-bone
##          reach that bends the knee and elbow only on their hinges (the match's joint limits);
##   knee_l, knee_r, elbow_l, elbow_r  which way the knee or elbow points ([right, up, forward]
##          in the body's own frame);
##   foot_l_mode, foot_r_mode  "flat" (sole on the ground, facing his way) or "free";
##   hand_mode  "open" or "catch" (fingers closed round the ball).
## A place is [x, y, z] in metres (y up), {"body": [right, up, forward]} from his own hips, or
## {"on": MAN, "bone": B, "off": [right, up, forward]} from the other man's bone in that man's
## own frame (a knee on a back, hips on shoulders). Each channel is a smooth curve through its
## own keys that never overshoots them (monotone cubic), so a foot keyed in the same spot twice
## stays planted between.
##   godot --headless --path . --script tools/oval3d/key_pair.gd -- SPEC.json OUT_DIR
## Writes OUT_DIR/<man>.res for each man.

const GLB := "res://assets/oval3d/player_mh.glb"
const SKPATH := "average_rig_001/Skeleton3D"
const HINGE := Vector3(1.0, 0.0, 0.0)
const G := 9.81
const BONES := ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
	"clavicle_l", "upperarm_l", "lowerarm_l", "hand_l", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
	"thigh_l", "calf_l", "foot_l", "ball_l", "thigh_r", "calf_r", "foot_r", "ball_r"]
const SPINE := ["spine_01", "spine_02", "spine_03"]
# Finger curl (deg, about each joint's hinge) for a hand closed round a ball.
const CURL := {"01": 25.0, "02": 35.0, "03": 25.0}

var men := {}      # name -> {"sk": Skeleton3D, "keys": [...], "R": Basis this frame}
var order := []


func _initialize() -> void:
	_run.call_deferred()


func _body() -> Skeleton3D:
	var scene: Node3D = (load(GLB) as PackedScene).instantiate()
	root.add_child(scene)
	return scene.find_children("*", "Skeleton3D", true, false)[0]


# ---------------------------------------------------------------- curves

static func _mono(ts: Array, vs: Array, t: float) -> float:
	var n := ts.size()
	if n == 1 or t <= ts[0]:
		return vs[0]
	if t >= ts[n - 1]:
		return vs[n - 1]
	var d := []
	for i in n - 1:
		d.append((vs[i + 1] - vs[i]) / (ts[i + 1] - ts[i]))
	var m := []
	for i in n:
		if i == 0:
			m.append(d[0])
		elif i == n - 1:
			m.append(d[n - 2])
		elif d[i - 1] * d[i] <= 0.0:
			m.append(0.0)
		else:
			m.append((d[i - 1] + d[i]) * 0.5)
	for i in n - 1:
		if absf(d[i]) < 1e-9:
			m[i] = 0.0
			m[i + 1] = 0.0
			continue
		var a: float = m[i] / d[i]
		var b: float = m[i + 1] / d[i]
		var s := a * a + b * b
		if s > 9.0:
			var tau := 3.0 / sqrt(s)
			m[i] = tau * a * d[i]
			m[i + 1] = tau * b * d[i]
	var k := 0
	while t > ts[k + 1]:
		k += 1
	var h: float = ts[k + 1] - ts[k]
	var x: float = (t - ts[k]) / h
	var h00 := 2 * x * x * x - 3 * x * x + 1
	var h10 := x * x * x - 2 * x * x + x
	var h01 := -2 * x * x * x + 3 * x * x
	var h11 := x * x * x - x * x
	return h00 * vs[k] + h10 * h * m[k] + h01 * vs[k + 1] + h11 * h * m[k + 1]


# The keys that set a channel: [times, keys].
func _chan(keys: Array, c: String) -> Array:
	var ts := []
	var ks := []
	for k in keys:
		if k.has(c):
			ts.append(float(k["t"]))
			ks.append(k)
	return [ts, ks]


func _num(keys: Array, c: String, t: float, dflt: float) -> float:
	var ch := _chan(keys, c)
	if ch[0].is_empty():
		return dflt
	var vs := []
	for k in ch[1]:
		vs.append(float(k[c]))
	return _mono(ch[0], vs, t)


func _vec(keys: Array, c: String, t: float, dflt: Vector3, who: String) -> Vector3:
	var ch := _chan(keys, c)
	if ch[0].is_empty():
		return dflt
	var vs := []
	for k in ch[1]:
		vs.append(_place(k[c], who))
	var out := Vector3.ZERO
	for i in 3:
		var comp := []
		for v in vs:
			comp.append((v as Vector3)[i])
		out[i] = _mono(ch[0], comp, t)
	return out


func _step(keys: Array, c: String, t: float, dflt: String) -> String:
	var v := dflt
	for k in keys:
		if k.has(c) and float(k["t"]) <= t + 1e-6:
			v = str(k[c])
	return v


# ---------------------------------------------------------------- places

static func _frame(yaw: float, pitch: float, roll: float) -> Basis:
	return Basis(Vector3.UP, deg_to_rad(yaw)) * Basis(Vector3.RIGHT, deg_to_rad(pitch)) * Basis(Vector3.BACK, deg_to_rad(roll))


# Body-frame [right, up, forward] to a world direction (the rest body faces +z, its left is +x).
static func _dir(R: Basis, v: Array) -> Vector3:
	return R * Vector3(-float(v[0]), float(v[1]), float(v[2]))


func _place(p, who: String) -> Vector3:
	if p is Array:
		return Vector3(float(p[0]), float(p[1]), float(p[2]))
	var d: Dictionary = p
	if d.has("body"):
		var m: Dictionary = men[who]
		return _bp(m["sk"], "pelvis") + _dir(m["R"], d["body"])
	var o: Dictionary = men[str(d["on"])]
	return _bp(o["sk"], str(d["bone"])) + _dir(o["R"], d.get("off", [0, 0, 0]))


static func _bp(sk: Skeleton3D, bone: String) -> Vector3:
	return sk.get_bone_global_pose(sk.find_bone(bone)).origin


# ---------------------------------------------------------------- posing

static func _set_global(sk: Skeleton3D, bone: String, g: Basis) -> void:
	var b := sk.find_bone(bone)
	var par := sk.get_bone_parent(b)
	var pg := sk.get_bone_global_pose(par).basis if par >= 0 else Basis.IDENTITY
	sk.set_bone_pose_rotation(b, (pg.orthonormalized().inverse() * g.orthonormalized()).get_rotation_quaternion())
	sk.force_update_all_bone_transforms()


static func _rest_g(sk: Skeleton3D, bone: String) -> Basis:
	return sk.get_bone_global_rest(sk.find_bone(bone)).basis.orthonormalized()


## Two bones reaching for a place: the upper bone aimed so the lower bends on its hinge only.
static func _reach(sk: Skeleton3D, upper: String, lower: String, end: String, target: Vector3, pole: Vector3) -> float:
	var iu := sk.find_bone(upper)
	var il := sk.find_bone(lower)
	var ie := sk.find_bone(end)
	var o1 := sk.get_bone_rest(il).origin
	var o2 := sk.get_bone_rest(ie).origin
	var a := o1.length()
	var b := o2.length()
	var H := sk.get_bone_global_pose(iu).origin
	var to := target - H
	var d := clampf(to.length(), absf(a - b) + 0.01, a + b - 0.002)
	var u := to.normalized()
	var p := (pole - u * pole.dot(u))
	if p.length() < 1e-4:
		p = u.cross(Vector3.RIGHT)
	p = p.normalized()
	var x := (a * a - b * b + d * d) / (2.0 * d)
	var y := sqrt(maxf(a * a - x * x, 0.0))
	var K := H + u * x + p * y
	var T := H + u * d
	var uk := (K - H).normalized()
	var ul := (T - K).normalized()
	var M0 := sk.get_bone_rest(il).basis.get_rotation_quaternion()
	var d0 := o1.normalized()
	var h0 := (M0 * HINGE).normalized()
	var h0p := (h0 - d0 * h0.dot(d0)).normalized()
	var A := Basis(d0, h0p, d0.cross(h0p))
	var par := sk.get_bone_parent(iu)
	var pg := sk.get_bone_global_pose(par).basis.orthonormalized()
	var n := uk.cross(ul)
	if n.length() < 1e-4:
		n = p.cross(u)
	n = n.normalized()
	# Which way round: the one whose knee bends the way a knee bends (more than its rest does).
	var best := [-INF, Quaternion.IDENTITY, 0.0]
	var flexsign := _flex_sign(M0, d0, h0, o2.normalized())
	for sgn in [1.0, -1.0]:
		var nn: Vector3 = n * sgn
		var B := Basis(uk, nn, uk.cross(nn))
		var gu := B * A.transposed()
		var ql := (pg.inverse() * gu).get_rotation_quaternion()
		var hw := (gu * h0).normalized()
		var s0 := (gu * (M0 * o2.normalized())).normalized()
		var a0 := s0 - hw * s0.dot(hw)
		var a1 := ul - hw * ul.dot(hw)
		var th := atan2(hw.dot(a0.cross(a1)), a0.dot(a1))
		if th * flexsign > best[0]:
			best = [th * flexsign, ql, th]
	sk.set_bone_pose_rotation(iu, best[1])
	sk.force_update_all_bone_transforms()
	sk.set_bone_pose_rotation(il, M0 * Quaternion(HINGE, best[2]))
	sk.force_update_all_bone_transforms()
	return sk.get_bone_global_pose(ie).origin.distance_to(target)


# +1 if turning the lower bone by +theta about its hinge bends the joint further.
static func _flex_sign(M0: Quaternion, d0: Vector3, h0: Vector3, e0: Vector3) -> float:
	var straight := func(th: float) -> float:
		var dl: Vector3 = Quaternion(h0, th) * (M0 * e0)
		return d0.angle_to(dl)
	return 1.0 if straight.call(0.2) > straight.call(-0.2) else -1.0


func _pose(name: String, t: float) -> void:
	var m: Dictionary = men[name]
	var sk: Skeleton3D = m["sk"]
	var keys: Array = m["keys"]
	for i in sk.get_bone_count():
		sk.set_bone_pose_rotation(i, sk.get_bone_rest(i).basis.get_rotation_quaternion())
		sk.set_bone_pose_position(i, sk.get_bone_rest(i).origin)
	sk.force_update_all_bone_transforms()
	var yaw := _num(keys, "yaw", t, 0.0)
	var R := _frame(yaw, _num(keys, "pitch", t, 0.0), _num(keys, "roll", t, 0.0))
	m["R"] = R
	# The hips: a curve through the pos keys, or a gravity arc across an "air" span.
	var pos := _vec(keys, "pos", t, Vector3(0, 0.99, 0), name)
	var ch := _chan(keys, "pos")
	for i in ch[0].size() - 1:
		var k0: Dictionary = ch[1][i]
		if k0.get("air", false) and t >= ch[0][i] and t <= ch[0][i + 1]:
			var p0 := _place(k0["pos"], name)
			var p1 := _place(ch[1][i + 1]["pos"], name)
			var T: float = ch[0][i + 1] - ch[0][i]
			var s: float = t - ch[0][i]
			var v0 := (p1.y - p0.y) / T + 0.5 * G * T
			pos = p0.lerp(p1, s / T)
			pos.y = p0.y + v0 * s - 0.5 * G * s * s
	var ip := sk.find_bone("pelvis")
	var rootg := sk.get_bone_global_pose(sk.get_bone_parent(ip))
	sk.set_bone_pose_position(ip, rootg.affine_inverse() * pos)
	_set_global(sk, "pelvis", R * _rest_g(sk, "pelvis"))
	var c := _vec_raw(keys, "chest", t, Vector3.ZERO)
	var Rc := R * _frame(c[2], c[0], c[1])
	var qb := R.get_rotation_quaternion()
	var qc := Rc.get_rotation_quaternion()
	for i in SPINE.size():
		_set_global(sk, SPINE[i], Basis(qb.slerp(qc, (i + 1.0) / SPINE.size())) * _rest_g(sk, SPINE[i]))
	var hd := _vec_raw(keys, "head", t, Vector3.ZERO)
	var Rh := Rc * _frame(hd[1], hd[0], 0.0)
	_set_global(sk, "neck_01", Basis(qc.slerp(Rh.get_rotation_quaternion(), 0.5)) * _rest_g(sk, "neck_01"))
	_set_global(sk, "head", Rh * _rest_g(sk, "head"))
	for side in ["l", "r"]:
		_set_global(sk, "clavicle_" + side, Rc * _rest_g(sk, "clavicle_" + side))
		_set_global(sk, "upperarm_" + side, Rc * _rest_g(sk, "upperarm_" + side))
		_set_global(sk, "thigh_" + side, R * _rest_g(sk, "thigh_" + side))
		if not _chan(keys, "foot_" + side)[0].is_empty():
			var ft := _vec(keys, "foot_" + side, t, Vector3.ZERO, name)
			var kp := _dir(R, _vec_raw(keys, "knee_" + side, t, Vector3(0, 0, 1)))
			_reach(sk, "thigh_" + side, "calf_" + side, "foot_" + side, ft, kp)
		if _step(keys, "foot_" + side + "_mode", t, "free") == "flat":
			_set_global(sk, "foot_" + side, Basis(Vector3.UP, deg_to_rad(yaw)) * _rest_g(sk, "foot_" + side))
		if not _chan(keys, "hand_" + side)[0].is_empty():
			var ht := _vec(keys, "hand_" + side, t, Vector3.ZERO, name)
			var ep := _dir(R, _vec_raw(keys, "elbow_" + side, t, Vector3(0, -1, -1)))
			_reach(sk, "upperarm_" + side, "lowerarm_" + side, "hand_" + side, ht, ep)
		if _step(keys, "hand_mode", t, "open") == "catch":
			for f in ["index", "middle", "ring", "pinky"]:
				for j in ["01", "02", "03"]:
					var bi := sk.find_bone("%s_%s_%s" % [f, j, side])
					if bi >= 0:
						sk.set_bone_pose_rotation(bi, sk.get_bone_rest(bi).basis.get_rotation_quaternion() * Quaternion(Vector3(0, 0, 1), deg_to_rad(CURL[j])))
			sk.force_update_all_bone_transforms()


# A body-frame direction channel (not a place).
func _vec_raw(keys: Array, c: String, t: float, dflt: Vector3) -> Array:
	var ch := _chan(keys, c)
	if ch[0].is_empty():
		return [dflt.x, dflt.y, dflt.z]
	var out := [0.0, 0.0, 0.0]
	for i in 3:
		var comp := []
		for k in ch[1]:
			comp.append(float(k[c][i]) if i < (k[c] as Array).size() else 0.0)
		out[i] = _mono(ch[0], comp, t)
	return out


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(str(args[0])))
	var out := str(args[1])
	DirAccess.make_dir_recursive_absolute(out)
	var hz := float(spec.get("hz", 25))
	var length := float(spec["length"])
	for name in spec["order"]:
		men[name] = {"sk": _body(), "keys": spec["men"][name]["keys"], "R": Basis.IDENTITY}
	var n := int(round(length * hz)) + 1
	var anims := {}
	for name in men:
		var a := Animation.new()
		a.length = length
		var sk: Skeleton3D = men[name]["sk"]
		var tracks := {}
		for b in BONES:
			var tr := a.add_track(Animation.TYPE_ROTATION_3D)
			a.track_set_path(tr, NodePath("%s:%s" % [SKPATH, b]))
			tracks[b] = tr
		for side in ["l", "r"]:
			for f in ["index", "middle", "ring", "pinky"]:
				for j in ["01", "02", "03"]:
					var bn := "%s_%s_%s" % [f, j, side]
					if sk.find_bone(bn) >= 0:
						var tr2 := a.add_track(Animation.TYPE_ROTATION_3D)
						a.track_set_path(tr2, NodePath("%s:%s" % [SKPATH, bn]))
						tracks[bn] = tr2
		var tp := a.add_track(Animation.TYPE_POSITION_3D)
		a.track_set_path(tp, NodePath("%s:pelvis" % SKPATH))
		tracks["@pos"] = tp
		anims[name] = [a, tracks]
	for k in n:
		var t := k / hz
		for name in spec["order"]:
			_pose(name, t)
			var sk: Skeleton3D = men[name]["sk"]
			var a: Animation = anims[name][0]
			var tracks: Dictionary = anims[name][1]
			for b in tracks:
				if b == "@pos":
					a.position_track_insert_key(tracks[b], t, sk.get_bone_pose_position(sk.find_bone("pelvis")))
				else:
					a.rotation_track_insert_key(tracks[b], t, sk.get_bone_pose_rotation(sk.find_bone(b)))
	for name in anims:
		var path := "%s/%s.res" % [out, name]
		print("SAVED %s %s" % [path, error_string(ResourceSaver.save(anims[name][0], path))])
	quit()
