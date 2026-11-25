extends SceneTree
## Keep a falling jumper with his stepladder. Where the footage loses the two men in a tangle (Jurrah
## going headfirst over his teammate), the fit drifts the jumper a metre away from him; in the
## footage he comes down at the man's feet. Over FROM:TO (eased in and out over EASE frames) the
## jumper is drawn across the ground until his hips are within R metres of the stepladder's,
## the draw smoothed over neighbouring frames. Run settle_pair.gd (SETTLE_TURN=0) after it.
##   godot --headless --path . --script tools/oval3d/pull_pair.gd -- JUMP.res STEP.res OUT.res FROM:TO R [EASE] [HZ]

const Check := preload("res://tools/oval3d/check_pair.gd")
const GLB := "res://assets/oval3d/player_mh.glb"


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


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var ft := str(args[3]).split(":")
	var a := int(ft[0])
	var b := int(ft[1])
	var r := float(args[4])
	var ease := int(args[5]) if args.size() > 5 else 8
	var hz := float(args[6]) if args.size() > 6 else 25.0
	var aj: Animation = (load(str(args[0])) as Animation).duplicate(true)
	var j := _body(aj)
	var s := _body(load(str(args[1])))
	var n := int(round(aj.length * hz)) + 1
	var raw := []
	for k in n:
		var v := Vector3.ZERO
		if k >= a - ease and k <= b + ease:
			for p in [j, s]:
				(p[0] as AnimationPlayer).seek(k / hz, true)
			var d: Vector3 = Check._p(j[1], "pelvis") - Check._p(s[1], "pelvis")
			d.y = 0.0
			if d.length() > r:
				v = -d.normalized() * (d.length() - r)
			var w := 1.0
			if k < a:
				w = smoothstep(float(a - ease), float(a), float(k))
			elif k > b:
				w = 1.0 - smoothstep(float(b), float(b + ease), float(k))
			v *= w
		raw.append(v)
	# Smoothed (Gaussian, sigma 2 frames) so the draw never jerks.
	var sm := []
	for k in n:
		var acc := Vector3.ZERO
		var ws := 0.0
		for i in range(maxi(0, k - 6), mini(n, k + 7)):
			var g := exp(-0.5 * pow((i - k) / 2.0, 2))
			acc += raw[i] * g
			ws += g
		sm.append(acc / ws)
	var sk: Skeleton3D = j[1]
	var tp := -1
	for t in aj.get_track_count():
		if aj.track_get_type(t) == Animation.TYPE_POSITION_3D and str(aj.track_get_path(t)).get_slice(":", 1) == "pelvis":
			tp = t
	var most := 0.0
	for k in n:
		var key := aj.track_find_key(tp, k / hz, Animation.FIND_MODE_APPROX)
		aj.track_set_key_value(tp, key, (aj.track_get_key_value(tp, key) as Vector3) + _local(sk, sm[k]))
		most = maxf(most, (sm[k] as Vector3).length())
	print("PULL largest draw %.2f m" % most)
	print("SAVED %s %s" % [args[2], error_string(ResourceSaver.save(aj, str(args[2])))])
	quit()
