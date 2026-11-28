extends "res://tools/visual/capture_builds3d.gd"
## LOCAL PROTOTYPE, NEVER COMMIT: the same moment of Melbourne v Fremantle (seed 31, first bounce,
## Gawn followed) from the main camera (rule 2.93) and a close-up on Gawn, under each stylised filter.
##   godot --path . --script tools/visual/_proto_filters3d.gd -- OUTDIR SHADER_PATH T1,T2,...

const MODES := ["none", "film", "paint", "ink", "cel"]


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var shader_code := FileAccess.get_file_as_string(str(args[1]))
	var times := []
	for s in str(args[2]).split(","):
		times.append(float(s))
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.use_debanding = true
	var O3 = load("res://scripts/ui/match/Oval3D.gd")
	O3.player_glb = GLB
	O3.loops_glb = GLB
	O3.hair_glb = "res://__no_hair_shells__.glb"
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	_home = "MEL"
	_away = "FRE"
	_follow = "MEL_11"
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new(_home, gdb.club_list(_home), true, _home),
			Squad_.new(_away, gdb.club_list(_away), false, _away), 31).run()
	_make_clouds()
	await _clouds.changed

	var tmax: float = times.max() + 1.0
	# Pass 1: ball and Gawn each step.
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, _home, _away)
	var who := -1
	for i in range(oval.players.size()):
		if str(oval.players[i].get("pid", "")) == _follow:
			who = i
	var balls := []
	var men := []
	var n := 0
	while n <= int(tmax / DT) and not d.idle():
		d.advance(DT)
		oval.sync(DT)
		balls.append(oval.ball.global_position)
		men.append((oval.players[who]["node"] as Node3D).global_position)
		n += 1
	oval.queue_free()
	await process_frame

	var size := Vector2i(1080, 608)
	root.size = size
	DisplayServer.window_set_size(size)
	d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, _home, _away)
	_look(oval, 1.0)
	var cam: Camera3D = oval.camera
	cam.keep_aspect = Camera3D.KEEP_WIDTH
	var sh := Shader.new()
	sh.code = shader_code
	var mat := ShaderMaterial.new()
	mat.shader = sh
	mat.render_priority = 127
	var quad := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(2, 2)
	quad.mesh = qm
	quad.material_override = mat
	quad.extra_cull_margin = 16384.0
	quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	cam.add_child(quad)
	quad.position = Vector3(0, 0, -1)
	n = 0
	if args.size() > 3 and str(args[3]) == "movie":
		# Every 1/30 s from times[0] to times[1]: main and close, current and film.
		var fa := int(times[0] / DT)
		var fb := int(times[1] / DT)
		while n < fa:
			d.advance(DT)
			oval.sync(DT)
			n += 1
		var k := 0
		while n <= fb:
			d.advance(DT)
			oval.sync(DT)
			if (n - fa) % 2 == 0:
				for shot in ["main", "close"]:
					var src: Array = balls if shot == "main" else men
					var a := Vector3.ZERO
					var c := 0
					for g in range(maxi(0, n - 30), mini(src.size() - 1, n + 30) + 1):
						a += src[g]
						c += 1
					a /= float(c)
					a.y = 1.0 if shot == "main" else 1.9
					var eye := Vector3(0.0, 15.0, HALF_WID + 25.0) if shot == "main" else a + Vector3(0.0, 0.3, 7.0)
					cam.near = 20.0 if shot == "main" else 0.05
					cam.global_position = eye
					cam.look_at(a, Vector3.UP)
					cam.fov = rad_to_deg(2.0 * atan((57.0 if shot == "main" else 3.0) * 0.5 / eye.distance_to(a)))
					for m in [0, 1]:
						mat.set_shader_parameter("mode", m)
						mat.set_shader_parameter("frame", float(k))
						await process_frame
						await RenderingServer.frame_post_draw
						root.get_viewport().get_texture().get_image().save_png(
								out.path_join("%s_%s_%04d.png" % [shot, MODES[m], k]))
				k += 1
			n += 1
		print("MOVIE %d frames" % k)
		quit()
		return
	for t in times:
		var f := int(t / DT)
		while n < f:
			d.advance(DT)
			oval.sync(DT)
			n += 1
		for shot in ["main", "close"]:
			var src: Array = balls if shot == "main" else men
			var a := Vector3.ZERO
			var c := 0
			for g in range(maxi(0, f - 30), mini(src.size() - 1, f + 30) + 1):
				a += src[g]
				c += 1
			a /= float(c)
			a.y = 1.0 if shot == "main" else 1.9
			var eye := Vector3(0.0, 15.0, HALF_WID + 25.0) if shot == "main" else a + Vector3(0.0, 0.3, 7.0)
			# Rule 2.101: nobody within 20 m of the main lens is drawn.
			cam.near = 20.0 if shot == "main" else 0.05
			cam.global_position = eye
			cam.look_at(a, Vector3.UP)
			cam.fov = rad_to_deg(2.0 * atan((57.0 if shot == "main" else 3.0) * 0.5 / eye.distance_to(a)))
			for m in range(MODES.size()):
				mat.set_shader_parameter("mode", m)
				for w in range(3):
					await process_frame
				await RenderingServer.frame_post_draw
				root.get_viewport().get_texture().get_image().save_png(
						out.path_join("t%04.1f_%s_%s.png" % [t, shot, MODES[m]]))
				if shot == "main":
					var vp := root.get_viewport().get_viewport_rid()
					RenderingServer.viewport_set_measure_render_time(vp, true)
					var ms := 0.0
					for w in range(30):
						await RenderingServer.frame_post_draw
						if w >= 10:
							ms += RenderingServer.viewport_get_measured_render_time_gpu(vp)
					print("GPU %s %.1f %.3f ms" % [MODES[m], t, ms / 20.0])
		print("MOMENT %.1f done" % t)
	quit()
