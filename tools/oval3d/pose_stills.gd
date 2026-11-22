extends SceneTree
## Stills of one clip's frames on the match body, from the front, side and back, for checking a
## joint tools/oval3d/joint_audit.py flags.
##   godot --path . --rendering-method mobile --script tools/oval3d/pose_stills.gd -- OUT_DIR CLIP T [T...]
## Writes OUT_DIR/<clip>_<t>.png, three views side by side (front, his right, back); with
## CLIP_LIMITS=1 set, as a match plays them (ClipLimits), to <clip>_<t>_limited.png.

const GLB := "res://assets/oval3d/player_mh.glb"
var clip_tag := ""


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	OS.low_processor_usage_mode = false
	create_timer(600.0).timeout.connect(func(): print("TIMEOUT"); quit(1))
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var clip := str(args[1])
	root.size = Vector2i(480, 640)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.55, 0.6, 0.62)
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.5, 0.5, 0.5)
	root.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-40, 30, 0)
	root.add_child(sun)
	var scene: Node3D = (load(GLB) as PackedScene).instantiate()
	root.add_child(scene)
	var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	if OS.get_environment("CLIP_LIMITS") != "":
		ClipLimits.apply(ap, sk)   # as a match plays them
		clip_tag = "_limited"
	var cam := Camera3D.new()
	cam.fov = 30.0
	root.add_child(cam)
	cam.current = true
	DirAccess.make_dir_recursive_absolute(out)
	for k in range(2, args.size()):
		var t := float(args[k])
		ap.play(clip)
		ap.seek(t, true)
		ap.pause()
		var hips := sk.global_transform * sk.get_bone_global_pose(sk.find_bone("pelvis")).origin
		var imgs := []
		for yaw in [0.0, 90.0, 180.0]:
			var d := Vector3(sin(deg_to_rad(yaw)), 0.0, cos(deg_to_rad(yaw)))
			cam.position = hips + d * 5.0 + Vector3.UP * 0.1
			cam.look_at(hips + Vector3.UP * 0.05, Vector3.UP)
			await process_frame
			await process_frame
			await RenderingServer.frame_post_draw
			imgs.append(root.get_texture().get_image())
		var w: int = imgs[0].get_width()
		var h: int = imgs[0].get_height()
		var all := Image.create(w * 3, h, false, imgs[0].get_format())
		for v in range(3):
			all.blit_rect(imgs[v], Rect2i(0, 0, w, h), Vector2i(w * v, 0))
		all.save_png("%s/%s_%.2f%s.png" % [out, clip, t, clip_tag])
	quit()
