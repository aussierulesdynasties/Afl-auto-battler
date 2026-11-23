extends SceneTree
## An in-match injury on the 3D oval (row 202 2e), filmed close: the hurt man goes down, his
## trainers come out, he gets up and walks off to the interchange gate, and his replacement runs
## on. Seeded match, RIC v SYD (tools/oval3d/injury/probe_timing.gd lists each seed's injuries).
##   godot --path . --rendering-method mobile --script tools/visual/capture_injury3d.gd -- OUTDIR [SEED] [EVERY]
## Saves OUTDIR/fNNNN.png every EVERY frames (30 a second of picture) and prints, per frame,
## INJ lines: stage, clip, where his hips are and how high, and any jump of his hips between
## frames over JUMP metres (a slide or a pop the eye would catch).

const DT := 1.0 / 30.0
const JUMP := 0.12


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _shot(pv, out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	pv._vp3d.get_texture().get_image().save_png(out.path_join(name + ".png"))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://injury3d"
	var seed := int(args[1]) if args.size() > 1 else 2
	var every := int(args[2]) if args.size() > 2 else 3
	DirAccess.make_dir_recursive_absolute(out)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("RIC", gdb.club_list("RIC"), true, "RIC"),
			Squad_.new("SYD", gdb.club_list("SYD"), false, "SYD"), seed).run()
	for r in res.get("injuries", []):
		print("INJ record ", r)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(960, 540)
	var pv = load("res://scripts/ui/PitchView.gd").new()
	pv.size = Vector2(960, 540)
	pv.three_d = true
	root.add_child(pv)
	res["home"] = "RIC"
	res["away"] = "SYD"
	res["label"] = "Round 1"
	res["venue"] = "MCG"
	pv.setup(res)
	pv.set_speed(1.0)
	pv.play()
	pv.set_process(false)
	var d = pv.director
	var oval = pv._oval3d
	var cam := Camera3D.new()
	cam.fov = 30.0
	oval.add_child(cam)
	# Fast to the first hurt man (no pictures drawn on the way).
	var guard := 0
	while d.hurt.is_empty() and pv.playing and guard < 400000:
		guard += 1
		pv._process(DT)
	if d.hurt.is_empty():
		print("INJ none in this match")
		quit(1)
		return
	var id := int(d.hurt.keys()[0])
	var r: Dictionary = d.hurt[id]
	print("INJ start: %s, %s, token %d at (%.1f, %.1f), %.0f s, gate (%.1f, %.1f)" % [r["pid"], r["kind"], id,
			(r["at"] as Vector2).x, (r["at"] as Vector2).y, d.time, d.gate.x, d.gate.y])
	var n := 0
	var last := Vector3.INF
	var jumps := 0
	var low := INF
	var sc: Dictionary = {}
	var cam_at := Vector3.INF
	while pv.playing and n < 30 * 120:
		pv._process(DT)
		if sc.is_empty():
			sc = oval.injury._scene_of_pid(str(r["pid"]))
			if sc.is_empty():
				await process_frame
				continue
		if not oval.injury.scenes.has(sc):
			print("INJ scene over at frame %d, %.0f s; hips jumps over %.2f m: %d" % [n, d.time, JUMP, jumps])
			break
		var p: Dictionary = sc["p"]
		var sk: Skeleton3D = p["skel"]
		var hips := sk.global_transform * sk.get_bone_global_pose(sk.find_bone("pelvis")).origin
		var head := sk.global_transform * sk.get_bone_global_pose(sk.find_bone("head")).origin
		if last != Vector3.INF and hips.distance_to(last) > JUMP:
			jumps += 1
			var dv := hips - last
			print("INJ JUMP frame %d %.2f m (%.2f, %.2f, %.2f) (%s %s ct %.2f)" % [n, hips.distance_to(last), dv.x, dv.y, dv.z,
					sc["stage"], sc["clip"], float(sc["ct"])])
		last = hips
		low = minf(low, hips.y)
		if n % 15 == 0:
			var tr := ""
			for c in sc["trainers"]:
				tr += " T(%.1f,%.1f)" % [(c["node"] as Node3D).position.x, (c["node"] as Node3D).position.z]
			print("INJ f%04d t %.1f %s %s ct %.2f slot %d hips (%.2f, %.2f, %.2f) head y %.2f%s" % [n, d.time,
					sc["stage"], sc["clip"], float(sc["ct"]), int(sc["slot"]), hips.x, hips.y, hips.z, head.y, tr])
		# A broadcast-like close shot: 9 m off him, 3 m up, eased.
		var want := hips + Vector3(0, 0, 9.0).rotated(Vector3.UP, 0.6) + Vector3(0, 3.0, 0)
		cam_at = want if cam_at == Vector3.INF else cam_at.lerp(want, 0.08)
		cam.global_position = cam_at
		cam.look_at(hips + Vector3(0, 0.4, 0), Vector3.UP)
		cam.current = true
		if n % every == 0:
			await _shot(pv, out, "f%04d" % n)
		else:
			await process_frame
		n += 1
	print("INJ lowest hips %.2f m, frames %d" % [low, n])
	quit()
