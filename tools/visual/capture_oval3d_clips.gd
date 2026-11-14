extends SceneTree
## Look at every move baked into the 3D footballer (row 197): the game's own GLB, each animation.
##   godot --path . --script tools/visual/capture_oval3d_clips.gd -- OUTDIR FRAMES [res://...glb]
## For each animation: samples every bone's world position over the whole clip first, frames the
## camera on that box (side and front, no guessing), then saves FRAMES evenly spaced stills per
## view as <clip>_<view>_<k>.png, and prints per-clip facts: length, hips travel, lowest and
## highest foot, and the largest frame-to-frame jump of any bone (jitter).

const SIZE := Vector2i(480, 640)


func _initialize() -> void:
	_run.call_deferred()
	create_timer(900.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var frames := int(args[1])
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = SIZE
	DisplayServer.window_set_size(SIZE)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.55, 0.62, 0.7)
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.5, 0.5, 0.5)
	root.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 30, 0)
	root.add_child(sun)
	var ground := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(40, 40)
	ground.mesh = pm
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(0.3, 0.55, 0.3)
	ground.material_override = gm
	root.add_child(ground)
	var cam := Camera3D.new()
	cam.fov = 35.0
	root.add_child(cam)
	cam.make_current()
	var path := str(args[2]) if args.size() > 2 else "res://assets/oval3d/player_average.glb"
	var scene: Node3D = (load(path) as PackedScene).instantiate()
	root.add_child(scene)
	var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	for anim_name in ap.get_animation_list():
		ap.play(anim_name)
		var length := ap.current_animation_length
		# Pass 1: every bone's world position at 60 samples per second.
		var lo := Vector3(INF, INF, INF)
		var hi := -lo
		var prev: Array = []
		var jump := 0.0
		var jump_bone := ""
		var jump_t := 0.0
		var foot_lo := INF
		var foot_hi := -INF
		var hips0 := Vector3.ZERO
		var hips1 := Vector3.ZERO
		var n := int(length * 60.0) + 1
		for s in range(n):
			var t := minf(length, s / 60.0)
			ap.seek(t, true)
			var cur: Array = []
			for b in range(sk.get_bone_count()):
				var w: Vector3 = sk.global_transform * sk.get_bone_global_pose(b).origin
				cur.append(w)
				lo = lo.min(w)
				hi = hi.max(w)
				var bn := sk.get_bone_name(b)
				if bn.begins_with("foot_") or bn.begins_with("ball_"):
					foot_lo = minf(foot_lo, w.y)
					foot_hi = maxf(foot_hi, w.y)
				if bn == "pelvis" or bn == "Hips":
					if s == 0:
						hips0 = w
					hips1 = w
				if prev.size() > b and not bn.contains("_0"):
					var d: float = (w - prev[b]).length()
					if d > jump:
						jump = d
						jump_bone = bn
						jump_t = t
			prev = cur
		var base := str(anim_name)
		print("CLIP %s anim=%s len=%.2fs hips_travel=%.2fm (%s) foot_y %.3f..%.3f max_jump %.3fm/frame@60Hz %s t=%.2f box %s..%s" % [
			base, anim_name, length, (hips1 - hips0).length(), str((hips1 - hips0).snapped(Vector3(0.01, 0.01, 0.01))),
			foot_lo, foot_hi, jump, jump_bone, jump_t, str(lo.snapped(Vector3.ONE * 0.01)), str(hi.snapped(Vector3.ONE * 0.01))])
		var mid := (lo + hi) * 0.5
		var ext := (hi - lo)
		for view in [["side", Vector3(1, 0, 0)], ["front", Vector3(0, 0, 1)]]:
			var dir: Vector3 = view[1]
			# Distance so the box's larger screen extent fits the fov with 15% margin.
			var across: float = ext.z if dir.x != 0.0 else ext.x
			var span := maxf(ext.y, across * float(SIZE.y) / SIZE.x) * 1.15
			var dist := span * 0.5 / tan(deg_to_rad(cam.fov * 0.5)) + (ext.x if dir.x != 0.0 else ext.z) * 0.5
			cam.position = mid + dir * dist + Vector3(0, 0.3, 0)
			cam.look_at(mid)
			for f in range(frames):
				ap.seek(length * f / maxf(1, frames - 1), true)
				for i in range(3):
					await process_frame
				await RenderingServer.frame_post_draw
				root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s_%02d.png" % [base, view[0], f]))
		ap.stop()
	print("DONE ", out)
	quit()
