extends SceneTree
## Film one clip on the match body from a fixed side, frame by frame, with the true joints of
## every frame beside it: the ground truth for proving a video-to-motion tracker
## (tools/oval3d/mp_roundtrip.py) on our own motion before it is trusted on broadcast footage.
##   godot --path . --rendering-method mobile --script tools/oval3d/render_clip.gd -- OUT_DIR CLIP [YAW_DEG] [HZ]
## (RENDER_ANIM=<file.res> films a baked animation under the name CLIP.)
## Writes OUT_DIR/f_<n>.png (720 x 960) and OUT_DIR/joints.json: per frame, each joint's world
## position (metres, y up). The camera stands 6 m off at YAW degrees round him (0: in front of
## him as the clip starts, 90: his right side), at hip height, panning with his hips.

const GLB := "res://assets/oval3d/player_mh.glb"
const JOINTS := ["head", "neck_01", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r",
		"lowerarm_l", "lowerarm_r", "hand_l", "hand_r", "pelvis", "thigh_l", "thigh_r",
		"calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r"]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	OS.low_processor_usage_mode = false
	create_timer(1200.0).timeout.connect(func(): print("TIMEOUT"); quit(1))
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var clip := str(args[1])
	var yaw := float(args[2]) if args.size() > 2 else 90.0
	var hz := float(args[3]) if args.size() > 3 else 30.0
	root.size = Vector2i(720, 960)
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
	var scene: Node3D = (load(GLB) as PackedScene).instantiate()
	root.add_child(scene)
	var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	# RENDER_ANIM=<file.res>: film that animation (tools/oval3d/bake_fit.gd) instead, the CLIP
	# argument naming it.
	if OS.get_environment("RENDER_ANIM") != "":
		var lib := AnimationLibrary.new()
		lib.add_animation(clip, load(OS.get_environment("RENDER_ANIM")))
		ap.add_animation_library("fit", lib)
		clip = "fit/" + clip
	var cam := Camera3D.new()
	cam.fov = 34.0
	root.add_child(cam)
	cam.current = true
	DirAccess.make_dir_recursive_absolute(out)
	ap.play(clip)
	var length := ap.current_animation_length
	var d := Vector3(sin(deg_to_rad(yaw)), 0.0, cos(deg_to_rad(yaw)))
	var frames := []
	var n := 0
	var t := 0.0
	while t <= length + 1e-4:
		ap.seek(t, true)
		ap.pause()
		var hips := sk.global_transform * sk.get_bone_global_pose(sk.find_bone("pelvis")).origin
		var aim := Vector3(hips.x, 1.0, hips.z)
		cam.position = aim + d * 6.0
		cam.look_at(aim, Vector3.UP)
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("%s/f_%04d.png" % [out, n])
		var row := {"t": t}
		for j in JOINTS:
			var b := sk.find_bone(j)
			var p := sk.global_transform * sk.get_bone_global_pose(b).origin
			row[j] = [p.x, p.y, p.z]
		frames.append(row)
		n += 1
		t += 1.0 / hz
	var f := FileAccess.open(out + "/joints.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"clip": clip, "yaw": yaw, "hz": hz, "cam_dir": [d.x, d.y, d.z], "frames": frames}))
	f.close()
	print("RENDERED %d frames of %s" % [n, clip])
	quit()
