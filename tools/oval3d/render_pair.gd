extends SceneTree
## Film two baked animations played together on two match bodies (a speccy's jumper and his
## stepladder, from one pair fit: tools/oval3d/mp_fit.py --pair, then bake_fit.gd with a shared
## BAKE_ORIGIN and BAKE_SCALE), from a fixed side, to check the pair by eye beside the footage.
##   godot --path . --rendering-method mobile --script tools/oval3d/render_pair.gd -- OUT_DIR A.res B.res [YAW_DEG] [HZ] [DIST] [hands|pair] [CATCH_S]
## Writes OUT_DIR/f_<n>.png (960 x 720). YAW 0 looks along the fit's own camera (the footage's).
## The second man's kit is darkened so the two read apart. "hands" frames the first man's hands up
## close (a mark's catch) instead of the pair. CATCH_S: from then on a ball sits between the first
## man's palms (60% along each hand bone, as the match holds one), to check his hands are on it.

const GLB := "res://assets/oval3d/player_mh.glb"


func _initialize() -> void:
	_run.call_deferred()


func _body(res_path: String, tint: Color) -> Array:
	var scene: Node3D = (load(GLB) as PackedScene).instantiate()
	root.add_child(scene)
	var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	var lib := AnimationLibrary.new()
	lib.add_animation("clip", load(res_path))
	ap.add_animation_library("pair", lib)
	# Held inside a real body's joint limits, as the match plays it.
	ClipLimits.apply(ap, sk)
	ap.play("pair/clip")
	if tint != Color.WHITE:
		for m in scene.find_children("*", "MeshInstance3D", true, false):
			var mat := StandardMaterial3D.new()
			mat.albedo_color = tint
			(m as MeshInstance3D).material_override = mat
	return [ap, sk]


func _lowest(sk: Skeleton3D) -> float:
	var low := INF
	for b in sk.get_bone_count():
		if sk.get_bone_parent(b) < 0:
			continue    # the root bone stays on the ground under him
		low = minf(low, (sk.global_transform * sk.get_bone_global_pose(b).origin).y)
	return low


func _run() -> void:
	OS.low_processor_usage_mode = false
	create_timer(1200.0).timeout.connect(func(): print("TIMEOUT"); quit(1))
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var yaw := float(args[3]) if args.size() > 3 else 0.0
	var hz := float(args[4]) if args.size() > 4 else 25.0
	var dist := float(args[5]) if args.size() > 5 else 9.0
	var on_hands := args.size() > 6 and str(args[6]) == "hands"
	var catch_s := float(args[7]) if args.size() > 7 else INF
	var ball := MeshInstance3D.new()
	var bm := SphereMesh.new()
	bm.radius = 0.5
	bm.height = 1.0
	ball.mesh = bm
	var bmat := StandardMaterial3D.new()
	bmat.albedo_color = Color(0.95, 0.8, 0.1)
	ball.material_override = bmat
	ball.visible = false
	root.add_child(ball)
	root.size = Vector2i(960, 720)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.32, 0.5, 0.3)
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.55, 0.55, 0.55)
	root.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-45, 30, 0)
	root.add_child(sun)
	var ground := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(40, 40)
	ground.mesh = pm
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.25, 0.42, 0.22)
	ground.material_override = gm
	root.add_child(ground)
	var a := _body(str(args[1]), Color.WHITE)
	var b := _body(str(args[2]), Color(0.25, 0.22, 0.2))
	var cam := Camera3D.new()
	cam.fov = 34.0
	root.add_child(cam)
	cam.current = true
	DirAccess.make_dir_recursive_absolute(out)
	var length: float = (a[0] as AnimationPlayer).current_animation_length
	var d := Vector3(sin(deg_to_rad(yaw)), 0.0, cos(deg_to_rad(yaw)))
	var n := 0
	var t := 0.0
	var aim0 := Vector3.INF
	while t <= length + 1e-4:
		for p in [a, b]:
			(p[0] as AnimationPlayer).seek(t, true)
			(p[0] as AnimationPlayer).pause()
		var ska: Skeleton3D = a[1]
		var skb: Skeleton3D = b[1]
		var ha := ska.global_transform * ska.get_bone_global_pose(ska.find_bone("pelvis")).origin
		var hb := skb.global_transform * skb.get_bone_global_pose(skb.find_bone("pelvis")).origin
		var mid := (ha + hb) * 0.5
		# The camera pans with the pair across the ground, but holds its height, so a leap shows.
		var aim := Vector3(mid.x, 1.2, mid.z)
		if on_hands:
			aim = (ska.global_transform * ska.get_bone_global_pose(ska.find_bone("hand_l")).origin
					+ ska.global_transform * ska.get_bone_global_pose(ska.find_bone("hand_r")).origin) * 0.5
		if t >= catch_s - 1e-4:
			var pa: Array = []
			for side in ["l", "r"]:
				var hbn := ska.find_bone("hand_" + side)
				var g := ska.global_transform * ska.get_bone_global_pose(hbn)
				var hl := 0.0
				for c in ska.get_bone_children(hbn):
					hl += ska.get_bone_rest(c).origin.length()
				hl /= maxf(1.0, ska.get_bone_children(hbn).size())
				pa.append(g.origin + g.basis.y.normalized() * hl * 0.6 * ska.global_transform.basis.get_scale().x)
			var across: Vector3 = (pa[0] - pa[1]).normalized()
			var fore: Vector3 = ((pa[0] + pa[1]) * 0.5 - (ska.global_transform * ska.get_bone_global_pose(ska.find_bone("lowerarm_l")).origin)).normalized()
			var long := across.cross(fore).cross(across).normalized()
			var bx := across
			var by := long.cross(bx).normalized()
			# An AFL ball: about 29 cm long, 18 cm across the middle.
			ball.transform = Transform3D(Basis(bx * 0.18, by * 0.18, long * 0.29), (pa[0] + pa[1]) * 0.5)
			ball.visible = true
		cam.position = aim + d * dist
		cam.look_at(aim, Vector3.UP)
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("%s/f_%04d.png" % [out, n])
		# The lowest point of each body (bone heads; the skin sits about 5-10 cm out): a man
		# through the ground or floating above it shows here.
		print("LOW %d %.2f %.2f" % [n, _lowest(ska), _lowest(skb)])
		n += 1
		t += 1.0 / hz
	print("RENDERED %d frames" % n)
	quit()
