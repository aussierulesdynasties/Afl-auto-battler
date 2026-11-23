extends SceneTree
## Bake a fitted film (tools/oval3d/mp_fit.py) onto the match body as an animation.
##   godot --headless --path . --script tools/oval3d/bake_fit.gd -- FIT.json OUT.res
## Each frame: the pelvis turned and placed so his hips and the line up his trunk match the fit's,
## the three spine bones sharing the turn from hips to shoulders, then the upper arms, forearms,
## thighs and shins each swung (shortest arc, so their twist stays the rest pose's) to point where
## the fit's joints do; the head and neck turned to the fit's ears and nose, the feet to its heels
## and toes. Hands keep the rest pose. The match holds the result
## inside a real body's limits as it loads it (ClipLimits).
## BAKE_FLOOR=y: the ground's height in the fit's units; he is set on it (or above it by the fit's
## leap) frame by frame.
## BAKE_SCALE=k: his travel times k (our body's size over the fit's).
## BAKE_ORIGIN=x,y,z: the spot (fit units) his travel is measured from; a pair's two bakes share it.

const GLB := "res://assets/oval3d/player_mh.glb"
const LIMBS := [["upperarm_l", "shoulder_l", "elbow_l"], ["lowerarm_l", "elbow_l", "wrist_l"],
		["upperarm_r", "shoulder_r", "elbow_r"], ["lowerarm_r", "elbow_r", "wrist_r"],
		["thigh_l", "hip_l", "knee_l"], ["calf_l", "knee_l", "ankle_l"],
		["thigh_r", "hip_r", "knee_r"], ["calf_r", "knee_r", "ankle_r"]]
const SPINE := ["spine_01", "spine_02", "spine_03"]
# Where the tracker's ears and nose sit against our head bone, and its heel and toe against our
# foot bone (as a turn from the bone's frame, built the same way from bone positions, to the
# landmarks' frame). Measured on our own body standing in its rest pose, filmed from in front and
# from 35 deg (tools/oval3d/render_clip.gd, track_broadcast.py, mp_fit.py, 2026-11-23): the head's
# two readings agree within 4 deg; the feet's within 30 (the tracker reads a foot's depth poorly),
# so the feet take their mean and the match's joint limits (ClipLimits) hold them in.
const HEAD_C := Quaternion(0.60129, 0.02535, 0.0235, 0.79828)
const FOOT_C := Quaternion(-0.09665, -0.03503, -0.02746, 0.99432)
var sk: Skeleton3D


func _initialize() -> void:
	_run.call_deferred()


func _v(a) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


## A frame from a left-to-right line and an up line (up kept, the across made square to it).
func _frame(across: Vector3, up: Vector3) -> Basis:
	var y := up.normalized()
	var x := (across - y * across.dot(y)).normalized()
	return Basis(x, y, x.cross(y))


func _gpos(b: int) -> Vector3:
	return sk.get_bone_global_pose(b).origin


func _set_global_basis(b: int, want: Basis) -> void:
	var p := sk.get_bone_parent(b)
	var pb := sk.get_bone_global_pose(p).basis if p >= 0 else Basis.IDENTITY
	sk.set_bone_pose_rotation(b, (pb.inverse() * want).get_rotation_quaternion())


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var fit: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(str(args[0])))
	var out := str(args[1])
	var scene: Node3D = (load(GLB) as PackedScene).instantiate()
	root.add_child(scene)
	sk = scene.find_children("*", "Skeleton3D", true, false)[0]
	var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
	var skpath := str(ap.get_node(ap.root_node).get_path_to(sk))
	# The fit is in the world (y up); the skeleton's own space may be turned (the GLB's root).
	var to_sk := sk.global_transform.basis.inverse()
	sk.reset_bone_poses()
	var ip := sk.find_bone("pelvis")
	var hl := sk.find_bone("thigh_l")
	var hr := sk.find_bone("thigh_r")
	var sl := sk.find_bone("upperarm_l")
	var sr := sk.find_bone("upperarm_r")
	var hip0 := (_gpos(hl) + _gpos(hr)) * 0.5
	var sho0 := (_gpos(sl) + _gpos(sr)) * 0.5
	var F0 := _frame(_gpos(hl) - _gpos(hr), sho0 - hip0)
	var C0 := _frame(_gpos(sl) - _gpos(sr), sho0 - hip0)
	var pelvis0 := sk.get_bone_global_pose(ip)
	var spine0 := {}
	for n in SPINE:
		spine0[n] = sk.get_bone_global_pose(sk.find_bone(n)).basis
	var ineck := sk.find_bone("neck_01")
	var ihead := sk.find_bone("head")
	var head_rest := _frame(_gpos(sl) - _gpos(sr), _gpos(ihead) - _gpos(ineck))
	var neck_g0 := sk.get_bone_global_pose(ineck).basis
	var head_g0 := sk.get_bone_global_pose(ihead).basis
	var foot_rest := {}
	var foot_g0 := {}
	for side in ["l", "r"]:
		var f_b := sk.find_bone("foot_" + side)
		foot_rest[side] = _frame(_gpos(sk.find_bone("calf_" + side)) - _gpos(f_b), _gpos(sk.find_bone("ball_" + side)) - _gpos(f_b))
		foot_g0[side] = sk.get_bone_global_pose(f_b).basis
	var hz := float(fit["hz"])
	var frames: Array = fit["frames"]
	var anim := Animation.new()
	anim.length = (frames.size() - 1) / hz
	var rot_tracks := {}
	for n in ["pelvis"] + SPINE + LIMBS.map(func(l): return l[0]) + ["neck_01", "head", "foot_l", "foot_r"]:
		var t := anim.add_track(Animation.TYPE_ROTATION_3D)
		anim.track_set_path(t, "%s:%s" % [skpath, n])
		rot_tracks[n] = t
	var pos_track := anim.add_track(Animation.TYPE_POSITION_3D)
	anim.track_set_path(pos_track, "%s:pelvis" % skpath)
	var start := Vector3.INF
	# BAKE_SCALE: our body's size against the fit's (broadcast fits come out smaller than life;
	# a pair shares one scale so they keep their places).
	var floor_y := float(OS.get_environment("BAKE_FLOOR")) if OS.get_environment("BAKE_FLOOR") != "" else INF
	var travel := float(OS.get_environment("BAKE_SCALE")) if OS.get_environment("BAKE_SCALE") != "" else 1.0
	for k in range(frames.size()):
		var f = frames[k]
		if f == null:
			continue
		var J := {}
		for key in (f as Dictionary):
			J[key] = to_sk * _v(f[key])
		sk.reset_bone_poses()
		var hip: Vector3 = (J["hip_l"] + J["hip_r"]) * 0.5
		var sho: Vector3 = (J["shoulder_l"] + J["shoulder_r"]) * 0.5
		var F1 := _frame(J["hip_l"] - J["hip_r"], sho - hip)
		var C1 := _frame(J["shoulder_l"] - J["shoulder_r"], sho - hip)
		var Rp := F1 * F0.inverse()
		var Rc := C1 * C0.inverse()
		# The pelvis: turned as his hips are, placed by them (from the first frame's spot, so the
		# clip carries him as the film does).
		if start == Vector3.INF:
			start = hip
			# BAKE_ORIGIN=x,y,z (the fit's own units): carry him from that spot instead, so two men
			# baked from one pair fit (mp_fit.py --pair) keep where they stand against each other.
			if OS.get_environment("BAKE_ORIGIN") != "":
				var o := OS.get_environment("BAKE_ORIGIN").split(",")
				start = to_sk * Vector3(float(o[0]), float(o[1]), float(o[2]))
		var pg := Transform3D(Rp * pelvis0.basis, pelvis0.origin + Rp * (pelvis0.origin - hip0) - (pelvis0.origin - hip0) + (hip - start) * travel)
		var parent := sk.get_bone_parent(ip)
		var parent_g := sk.get_bone_global_pose(parent) if parent >= 0 else Transform3D.IDENTITY
		var local := parent_g.affine_inverse() * pg
		sk.set_bone_pose_rotation(ip, local.basis.get_rotation_quaternion())
		sk.set_bone_pose_position(ip, local.origin)
		# The spine shares the turn from his hips to his shoulders.
		var qp := Rp.get_rotation_quaternion()
		var qc := Rc.get_rotation_quaternion()
		for i in range(SPINE.size()):
			var q := qp.slerp(qc, float(i + 1) / SPINE.size())
			_set_global_basis(sk.find_bone(SPINE[i]), Basis(q) * spine0[SPINE[i]])
		# The limbs, each pointed where the fit's next joint is.
		for l in LIMBS:
			var b := sk.find_bone(l[0])
			var c := b + 1
			for ch in range(sk.get_bone_count()):
				if sk.get_bone_parent(ch) == b:
					c = ch
					break
			var now := (_gpos(c) - _gpos(b)).normalized()
			var want: Vector3 = (J[l[2]] - J[l[1]]).normalized()
			var g := sk.get_bone_global_pose(b).basis
			var axis := now.cross(want)
			var q := Quaternion.IDENTITY
			if axis.length() > 1e-6:
				q = Quaternion(axis.normalized(), now.angle_to(want))
			_set_global_basis(b, Basis(q) * g)
		# The head turned as the fit's ears and nose are, the neck taking half the turn from his
		# chest; each foot pointed as the fit's heel and toe are.
		if J.has("nose") and J.has("ear_l") and J.has("ear_r"):
			var em: Vector3 = (J["ear_l"] + J["ear_r"]) * 0.5
			var lh := _frame(J["ear_l"] - J["ear_r"], J["nose"] - em)
			var dq := (lh * Basis(HEAD_C).inverse() * head_rest.inverse()).get_rotation_quaternion()
			_set_global_basis(ineck, Basis(qc.slerp(dq, 0.5)) * neck_g0)
			_set_global_basis(ihead, Basis(dq) * head_g0)
		for side in ["l", "r"]:
			if not (J.has("toe_" + side) and J.has("heel_" + side)):
				continue
			var lf := _frame(J["knee_" + side] - J["ankle_" + side], J["toe_" + side] - J["heel_" + side])
			var fq := (lf * Basis(FOOT_C).inverse() * (foot_rest[side] as Basis).inverse()).get_rotation_quaternion()
			_set_global_basis(sk.find_bone("foot_" + side), Basis(fq) * (foot_g0[side] as Basis))
		# BAKE_FLOOR=y (the fit's units, its ground under him): put him on the ground. The fit's
		# hips cannot place him by height (a runner's bent knees lift our straight-legged rest
		# pose's feet), so his lowest point is set to the height the fit gives his lowest joint
		# above that floor: 0 standing or lying, the leap's height in the air.
		if floor_y != INF:
			var fit_low := INF
			for key in J:
				fit_low = minf(fit_low, (sk.global_transform.basis * J[key]).y)
			var want := maxf(0.0, (fit_low - floor_y) * travel)
			var low := INF
			for b in sk.get_bone_count():
				if sk.get_bone_parent(b) < 0:
					continue
				var nm := sk.get_bone_name(b)
				# Skin below the bone: a foot's sole is close, a back or a hip is not.
				var skin := 0.04 if (nm.begins_with("foot") or nm.begins_with("ball")) else 0.10
				low = minf(low, (sk.global_transform * sk.get_bone_global_pose(b).origin).y - skin)
			var lift := sk.global_transform.basis.inverse() * Vector3(0, want - low, 0)
			var par := sk.get_bone_parent(ip)
			var pb := sk.get_bone_global_pose(par).basis if par >= 0 else Basis.IDENTITY
			sk.set_bone_pose_position(ip, sk.get_bone_pose_position(ip) + pb.inverse() * lift)
		var t := k / hz
		for n in rot_tracks:
			anim.rotation_track_insert_key(rot_tracks[n], t, sk.get_bone_pose_rotation(sk.find_bone(n)))
		anim.position_track_insert_key(pos_track, t, sk.get_bone_pose_position(ip))
	var err := ResourceSaver.save(anim, out)
	print("BAKED %d frames -> %s (%s)" % [frames.size(), out, error_string(err)])
	quit()
