extends SceneTree
## How the 3D match's main camera frames play (row 202, 2e; Oval3DBroadcast), over a whole match
## at 4x, headless (Richmond v Sydney, seed 42, the match_visual suite's match):
##   godot --headless --path . --script tools/visual/measure_main_camera.gd [-- LEAD_S]
## On the TV picture only (not the wide shot, a cut or a replay) it prints how often the ball is in
## the picture and in its outer 8% band; where the ball sits along its way (the mean, as a share of
## the half-width: below 0 behind the picture's middle, with room ahead of it as real operators
## leave; above 0 ahead of the middle, the camera trailing); and how often the TV picture is each
## width (metres across a 16:9 picture where it aims; real TV, rule 2.111: 19-42 at a contest, up
## to about 60 in open play). LEAD_S tries another lead (seconds ahead the aim leads the ball).

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gdb = root.get_node("GameDB")
	root.get_node("GameState").replay_seed = 2027
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("RIC", gdb.club_list("RIC"), true, "RIC"),
			Squad_.new("SYD", gdb.club_list("SYD"), false, "SYD"), 42).run()
	res["home"] = "RIC"
	res["away"] = "SYD"
	res["label"] = "Round 1"
	var pv = load("res://scripts/ui/PitchView.gd").new()
	pv.size = Vector2(360, 480)
	pv.three_d = true
	root.add_child(pv)
	pv.setup(res)
	var tv = pv._tv
	if OS.get_cmdline_user_args().size() > 0:
		tv.lead_s = float(OS.get_cmdline_user_args()[0])
	var oval = pv._oval3d
	var cam: Camera3D = oval.camera
	pv.set_speed(4.0)
	pv.play()
	var frames := 0
	var inside := 0
	var edge := 0
	var hist := {}
	var moving := 0
	var behind := 0
	var off := 0.0
	var trail := []
	for i in range(12000):
		pv._process(1.0 / 60.0)
		if not pv.playing:
			break
		if tv.replaying or tv._close_who >= 0 or tv.shot != "main" or tv._zoom > 0.0:
			trail.clear()
			continue
		frames += 1
		var vs := Vector2(pv._vp3d.size)
		var bp: Vector3 = oval.ball.global_position
		var at := cam.unproject_position(bp)
		if not cam.is_position_behind(bp) and Rect2(Vector2.ZERO, vs).has_point(at):
			inside += 1
			if not Rect2(vs * 0.08, vs * 0.84).has_point(at):
				edge += 1
		trail.append(bp)
		if trail.size() > 4:
			trail.pop_front()
		var way: Vector3 = bp - (trail[0] as Vector3)
		way.y = 0.0
		if way.length() > 0.5:  # moving at least 7.5 m/s of match time
			moving += 1
			var mid := cam.unproject_position(oval._world(oval._look) + Vector3(0.0, 1.0, 0.0))
			var dir := (cam.unproject_position(bp + way) - at).normalized()
			behind += 1 if (at - mid).dot(dir) <= 0.0 else 0
			off += (at - mid).dot(dir) / (vs.x * 0.5)
		var b := int(float(tv.tv_width) / 4.0) * 4
		hist[b] = int(hist.get(b, 0)) + 1
	print("MAIN CAMERA %d TV frames: ball in the picture %.1f%%, in its outer band %.1f%%" % [frames,
			100.0 * inside / maxf(1.0, frames), 100.0 * edge / maxf(1.0, frames)])
	print("BALL ON ITS WAY %d frames: behind the middle %.0f%%, mean %+.2f of the half-width" % [moving,
			100.0 * behind / maxf(1.0, moving), off / maxf(1.0, moving)])
	var ks := hist.keys()
	ks.sort()
	for k in ks:
		print("WIDTH %d-%d m: %.1f%%" % [k, k + 4, 100.0 * hist[k] / maxf(1.0, frames)])
	quit(0)
