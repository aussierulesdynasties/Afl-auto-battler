extends SceneTree
## Place a speccy's jumper at the right depth from his stepladder. One broadcast camera cannot see
## how far apart two men are along its own line of sight, and the fit's guess put Kozzy in front of
## #50's chest when the footage shows his knees in #50's back. Moving the jumper along the camera's
## line (the fit's z) changes nothing on the footage's screen, so it is free: this finds the shift,
## on the side given, at which the jumper's legs first touch the stepladder's trunk over the contact
## frames, and writes it into every pelvis key (the whole clip, so the run-in keeps its shape).
##   godot --headless --path . --script tools/oval3d/depth_pair.gd -- JUMP.res STEP.res OUT.res SIDE FIRST:LAST [HZ]
## SIDE +1 moves the jumper toward the camera, -1 away. FIRST:LAST are the contact frames.

const Check := preload("res://tools/oval3d/check_pair.gd")
const GLB := "res://assets/oval3d/player_mh.glb"
const LEGS := ["thigh_l", "thigh_r", "calf_l", "calf_r"]


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
	return [ap, sk]


func _local(sk: Skeleton3D, world: Vector3) -> Vector3:
	var ip := sk.find_bone("pelvis")
	var par := sk.get_bone_parent(ip)
	var pb := sk.get_bone_global_pose(par).basis if par >= 0 else Basis.IDENTITY
	return (sk.global_transform.basis * pb).inverse() * world


# Closest the jumper's legs come to the stepladder's trunk and head over the frames, with the
# jumper shifted by dz.
func _gap(j: Array, s: Array, frames: Array, hz: float, dz: float) -> float:
	var low := INF
	for f in frames:
		for p in [j, s]:
			(p[0] as AnimationPlayer).seek(f / hz, true)
		var sk: Skeleton3D = j[1]
		var ip := sk.find_bone("pelvis")
		sk.set_bone_pose_position(ip, sk.get_bone_pose_position(ip) + _local(sk, Vector3(0, 0, dz)))
		for x in Check._caps(j[1]):
			if not (x[3] in LEGS):
				continue
			for y in Check._caps(s[1]):
				if not (y[3] in ["pelvis", "head"]):
					continue
				low = minf(low, Check._seg_dist(x[0], x[1], y[0], y[1]) - x[2] - y[2])
	return low


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var hz := float(args[5]) if args.size() > 5 else 25.0
	var aj: Animation = (load(str(args[0])) as Animation).duplicate(true)
	var j := _body(aj)
	var s := _body(load(str(args[1])))
	var side := float(args[3])
	var fl := str(args[4]).split(":")
	var frames := range(int(fl[0]), int(fl[1]) + 1)
	# Walk out from where the fit put him, on the given side, until his legs reach the trunk.
	var dz := 0.0
	var g0 := _gap(j, s, frames, hz, 0.0)
	print("DEPTH at the fit's guess: legs to trunk %.3f m" % g0)
	var best := 0.0
	var bestg := INF
	for i in 121:
		var z := side * i * 0.01
		var g := _gap(j, s, frames, hz, z)
		if absf(g) < absf(bestg) and (g >= -0.01 or i == 0):
			bestg = g
			best = z
		if g < -0.02 and i > 0 and best != 0.0:
			break
	dz = best
	print("DEPTH shift %.2f m along the camera line, legs to trunk %.3f m" % [dz, bestg])
	var sk: Skeleton3D = j[1]
	var tp := -1
	for t in aj.get_track_count():
		if aj.track_get_type(t) == Animation.TYPE_POSITION_3D and str(aj.track_get_path(t)).get_slice(":", 1) == "pelvis":
			tp = t
	var add := _local(sk, Vector3(0, 0, dz))
	for k in aj.track_get_key_count(tp):
		aj.track_set_key_value(tp, k, (aj.track_get_key_value(tp, k) as Vector3) + add)
	print("SAVED %s %s" % [args[2], error_string(ResourceSaver.save(aj, str(args[2])))])
	quit()
