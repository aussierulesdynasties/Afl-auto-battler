extends SceneTree
## Measure how close two baked animations played together come to passing through each other (a
## speccy's jumper and his stepladder; see render_pair.gd). Each body is a set of capsules on its
## bones, sized to a footballer in kit; a negative clearance is one man's limb inside the other.
##   godot --headless --path . --script tools/oval3d/check_pair.gd -- A.res B.res [HZ]
## Prints CLEAR <frame> <metres> <A part> <B part> per frame, then the worst.

const GLB := "res://assets/oval3d/player_mh.glb"
# (from bone, to bone, radius in metres). The head is a ball, from its bone up along the neck.
const CAPS := [["pelvis", "neck_01", 0.14], ["head", "", 0.11],
	["thigh_l", "calf_l", 0.08], ["thigh_r", "calf_r", 0.08],
	["calf_l", "foot_l", 0.055], ["calf_r", "foot_r", 0.055],
	["foot_l", "ball_l", 0.045], ["foot_r", "ball_r", 0.045],
	["upperarm_l", "lowerarm_l", 0.05], ["upperarm_r", "lowerarm_r", 0.05],
	["lowerarm_l", "hand_l", 0.04], ["lowerarm_r", "hand_r", 0.04]]


func _initialize() -> void:
	_run.call_deferred()


func _body(res_path: String) -> Array:
	var scene: Node3D = (load(GLB) as PackedScene).instantiate()
	root.add_child(scene)
	var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	var lib := AnimationLibrary.new()
	lib.add_animation("clip", load(res_path))
	ap.add_animation_library("pair", lib)
	ap.play("pair/clip")
	return [ap, sk]


static func _p(sk: Skeleton3D, bone: String) -> Vector3:
	return sk.global_transform * sk.get_bone_global_pose(sk.find_bone(bone)).origin


static func _caps(sk: Skeleton3D) -> Array:
	var out := []
	for c in CAPS:
		var a := _p(sk, c[0])
		var b: Vector3
		if c[1] == "":
			# The head's ball: its centre about 9 cm above the head bone, along the neck.
			var up := (a - _p(sk, "neck_01")).normalized()
			a = a + up * 0.09
			b = a
		else:
			b = _p(sk, c[1])
		out.append([a, b, float(c[2]), c[0]])
	return out


static func _seg_dist(p1: Vector3, q1: Vector3, p2: Vector3, q2: Vector3) -> float:
	var best := INF
	# Sampled closely enough (2 cm on a long bone) for a clearance check.
	for i in 21:
		var a := p1.lerp(q1, i / 20.0)
		var c := Geometry3D.get_closest_point_to_segment(a, p2, q2)
		best = minf(best, a.distance_to(c))
	for i in 21:
		var b := p2.lerp(q2, i / 20.0)
		var c := Geometry3D.get_closest_point_to_segment(b, p1, q1)
		best = minf(best, b.distance_to(c))
	return best


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var hz := float(args[2]) if args.size() > 2 else 25.0
	var a := _body(str(args[0]))
	var b := _body(str(args[1]))
	var length: float = (a[0] as AnimationPlayer).current_animation_length
	var n := 0
	var t := 0.0
	var worst := INF
	var worst_n := -1
	while t <= length + 1e-4:
		for p in [a, b]:
			(p[0] as AnimationPlayer).seek(t, true)
		var ca := _caps(a[1])
		var cb := _caps(b[1])
		var low := INF
		var pa := ""
		var pb := ""
		for x in ca:
			for y in cb:
				var d: float = _seg_dist(x[0], x[1], y[0], y[1]) - x[2] - y[2]
				if d < low:
					low = d
					pa = x[3]
					pb = y[3]
		print("CLEAR %d %.3f %s %s" % [n, low, pa, pb])
		if low < worst:
			worst = low
			worst_n = n
		n += 1
		t += 1.0 / hz
	print("WORST %.3f at frame %d of %d" % [worst, worst_n, n])
	quit()
