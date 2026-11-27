extends SceneTree
## Film the gait loops (gait_clips.glb) on the match body, carried across the turf at each loop's
## own pace and heading, with the turf marked every 0.5 m: a planted foot that slides, sinks or
## hovers shows against the lines. Also measures it: per clip, while a foot is down (its ball
## bone under FOOT_DOWN), how far it moves over the turf (it should not), and the lowest and
## highest any foot point goes.
##   godot --path . --rendering-method mobile --script tools/oval3d/gaits/film_gaits.gd -- OUT_DIR [YAW_DEG] [CLIP ...]
## Writes OUT_DIR/<clip>_<yaw>_<n>.png (480 x 640, 15 a second over two cycles) and prints
## GAIT lines. --headless measures only.

const GLB := "res://assets/oval3d/player_mh.glb"
const CLIPS := "res://assets/oval3d/gait_clips.glb"
const FOOT_DOWN := 0.045   # m: a ball bone this low is on the turf


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	OS.low_processor_usage_mode = false
	create_timer(1200.0).timeout.connect(func(): print("TIMEOUT"); quit(1))
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var yaw := float(args[1]) if args.size() > 1 else 90.0
	var only := args.slice(2)
	var draw := DisplayServer.get_name() != "headless"
	print("FILM start, display ", DisplayServer.get_name())
	root.size = Vector2i(480, 640)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.55, 0.62, 0.7)
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.6, 0.6, 0.6)
	root.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 30, 0)
	root.add_child(sun)
	var turf := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(60, 60)
	turf.mesh = pm
	var tm := StandardMaterial3D.new()
	tm.albedo_color = Color(0.25, 0.45, 0.22)
	turf.material_override = tm
	root.add_child(turf)
	var lm := StandardMaterial3D.new()
	lm.albedo_color = Color(0.95, 0.95, 0.95)
	lm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for k in range(-60, 61):
		for across in [false, true]:
			var l := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = Vector3(0.012, 0.002, 60.0) if not across else Vector3(60.0, 0.002, 0.012)
			l.mesh = bm
			l.material_override = lm
			l.position = Vector3(k * 0.5, 0.001, 0.0) if not across else Vector3(0.0, 0.001, k * 0.5)
			root.add_child(l)
	var scene: Node3D = (load(GLB) as PackedScene).instantiate()
	root.add_child(scene)
	var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	var key := str(ap.get_node(ap.root_node).get_path_to(sk))
	var src_scene: Node = (load(CLIPS) as PackedScene).instantiate()
	var src: AnimationPlayer = src_scene.find_children("*", "AnimationPlayer", true, false)[0]
	var lib := AnimationLibrary.new()
	var names := []
	for name in src.get_animation_list():
		if not only.is_empty() and not only.has(str(name)):
			continue
		var a: Animation = src.get_animation(name).duplicate(true)
		for t in range(a.get_track_count()):
			var path := a.track_get_path(t)
			var bone := path.get_concatenated_subnames()
			if bone == "":
				bone = str(path.get_name(path.get_name_count() - 1))
			a.track_set_path(t, NodePath(key + ":" + bone))
		a.loop_mode = Animation.LOOP_LINEAR
		lib.add_animation(name, a)
		names.append(str(name))
	ap.add_animation_library("g", lib)
	var cam := Camera3D.new()
	cam.fov = 30.0
	root.add_child(cam)
	cam.current = true
	DirAccess.make_dir_recursive_absolute(out)
	var feet := ["ball_l", "ball_r", "foot_l", "foot_r"]
	for name in names:
		print("FILM clip ", name)
		ap.play("g/" + name)
		var a: Animation = lib.get_animation(name)
		var length := a.length
		# Its pace and heading as the retarget measured them (the glTF extras are not kept, so
		# they are read from the feet: the stance ball bone's travel back under the hips).
		var pace_v := _pace(ap, sk, length)
		var hz := 15.0 if draw else 60.0
		var n := 0
		var t := 0.0
		var down := {}    # foot -> where it was planted (INF: up)
		var slides := []
		var lo := INF
		var hi := -INF
		while t <= 2.0 * length + 1e-4:
			ap.seek(fmod(t, length), true)
			ap.pause()
			scene.position = Vector3(pace_v.x, 0.0, pace_v.y) * t
			for f in ["ball_l", "ball_r"]:
				var p := sk.global_transform * sk.get_bone_global_pose(sk.find_bone(f)).origin
				lo = minf(lo, p.y)
				if p.y < FOOT_DOWN:
					if not down.has(f):
						down[f] = p
					else:
						slides.append(Vector2(p.x - (down[f] as Vector3).x, p.z - (down[f] as Vector3).z).length())
				else:
					down.erase(f)
			if draw:
				var hips := sk.global_transform * sk.get_bone_global_pose(sk.find_bone("pelvis")).origin
				var d := Vector3(sin(deg_to_rad(yaw)), 0.0, cos(deg_to_rad(yaw)))
				var aim := Vector3(hips.x, 0.85, hips.z)
				cam.position = aim + d * 5.0 + Vector3(0, 0.6, 0)
				cam.look_at(aim, Vector3.UP)
				await process_frame
				await process_frame
				await RenderingServer.frame_post_draw
				root.get_texture().get_image().save_png("%s/%s_%d_%03d.png" % [out, name, int(yaw), n])
			n += 1
			t += 1.0 / hz
		slides.sort()
		var med := 0.0 if slides.is_empty() else float(slides[slides.size() / 2])
		var worst := 0.0 if slides.is_empty() else float(slides[-1])
		print("GAIT %-11s %.2f s, pace %.2f m/s heading %+4.0f deg, planted-foot drift median %.3f m worst %.3f m, ball bone lowest %+.3f m"
				% [name, length, pace_v.length(), rad_to_deg(atan2(pace_v.x, -pace_v.y)), med, worst, lo])
	src_scene.free()
	quit()


## The loop's pace and heading on the turf (x, z m/s): how fast, and which way, the planted ball
## bone travels back under him (the loops are in place), the opposite way.
func _pace(ap: AnimationPlayer, sk: Skeleton3D, length: float) -> Vector2:
	var vs := []
	var n := 120
	for f in ["ball_l", "ball_r"]:
		var b := sk.find_bone(f)
		var prev := Vector3.INF
		for k in range(n + 1):
			ap.seek(length * k / n, true)
			var p := sk.global_transform * sk.get_bone_global_pose(b).origin
			if prev != Vector3.INF and p.y < 0.045 and prev.y < 0.045:
				vs.append(Vector2(prev.x - p.x, prev.z - p.z) / (length / n))
			prev = p
	if vs.is_empty():
		return Vector2.ZERO
	var sum := Vector2.ZERO
	for v in vs:
		sum += v
	return sum / vs.size()
