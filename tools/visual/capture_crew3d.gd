extends SceneTree
## The match crew on the 3D oval (row 202): every umpire, trainer and runner in his clothes,
## filmed close, then the crew at work in a seeded match: a trainer's drink run while a set shot
## is lined up, a runner on after a goal, and a goal umpire's signal.
##   godot --path . --rendering-method mobile --script tools/visual/capture_crew3d.gd -- OUTDIR [SEED] [portraits]
## Saves OUTDIR/role_<role>_<k>_<view>.png (front, side, back, from 3.2 m) and
## OUTDIR/<drinks|runner>_<n>/fNNN.png, and prints where each crew member stood or ran.

const DT := 1.0 / 30.0
const PLAY := 2400.0


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
	var out := str(args[0]) if args.size() > 0 else "user://crew3d"
	var seed := int(args[1]) if args.size() > 1 else 31
	DirAccess.make_dir_recursive_absolute(out)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(900, 900)
	var pv = load("res://scripts/ui/PitchView.gd").new()
	pv.size = Vector2(900, 900)
	pv.three_d = true
	root.add_child(pv)
	res["home"] = "FRE"
	res["away"] = "STK"
	res["label"] = "Round 1"
	res["venue"] = "Alan Ray Oval"
	pv.setup(res)
	pv.set_speed(1.0)
	pv.play()
	pv.set_process(false)
	var d = pv.director
	var oval = pv._oval3d
	var cam := Camera3D.new()
	cam.fov = 34.0
	oval.add_child(cam)
	for i in range(10):
		pv._process(DT)
	# Every role close: one of each, from the front, the side and the back.
	var people := []
	for u in oval.umpires:
		people.append(u)
	for c in oval.crew.crew:
		people.append(c)
	var done := {}
	for p in people:
		var role := str(p["role"])
		var key := role + ("_%d" % int(p.get("side", 0)) if p.has("side") else "")
		if done.has(key):
			continue
		done[key] = true
		var n: Node3D = p["node"]
		print("CREW %s at (%.1f, %.1f)" % [key, n.position.x, n.position.z])
		var fw := n.global_transform.basis.z
		var side := fw.cross(Vector3.UP).normalized()
		var mid := n.global_position + Vector3(0, 1.0, 0)
		for v in [["front", fw], ["side", side], ["back", fw]]:
			# His back from the ground side: he is turned round for it (behind a trainer or a
			# boundary umpire is the fence).
			if v[0] == "back":
				n.rotate_y(PI)
			cam.global_position = mid + (v[1] as Vector3) * 3.6 + Vector3(0, 0.15, 0)
			cam.look_at(mid, Vector3.UP)
			cam.current = true
			await _shot(pv, out, "role_%s_%s" % [key, v[0]])
			if v[0] == "back":
				# And his back close, for its print (a trainer's vest).
				cam.global_position = mid + fw * 1.5 + Vector3(0, 0.35, 0)
				cam.look_at(mid + Vector3(0, 0.3, 0), Vector3.UP)
				await _shot(pv, out, "role_%s_back_close" % key)
				n.rotate_y(PI)
		# His head and shoulders, three-quarter.
		cam.global_position = mid + (fw + side * 0.6).normalized() * 1.4 + Vector3(0, 0.55, 0)
		cam.look_at(mid + Vector3(0, 0.5, 0), Vector3.UP)
		await _shot(pv, out, "role_%s_close" % key)
		# A trainer's bottle hand, close: the bottle gripped in a closed fist.
		if p.has("bottle"):
			var sk: Skeleton3D = p["skel"]
			var hand := sk.global_transform * sk.get_bone_global_pose(sk.find_bone("hand_r"))
			var at := hand * Vector3(0, 0.07, 0)
			for hv in [["out", side], ["front", fw]]:
				cam.global_position = at + (hv[1] as Vector3) * 0.55 + Vector3(0, 0.08, 0)
				cam.look_at(at, Vector3.UP)
				await _shot(pv, out, "role_%s_hand_%s" % [key, hv[0]])
	if args.size() > 2 and str(args[2]) == "portraits":
		quit()
		return
	# The crew at work.
	var films := {"drinks": 0, "runner": 0, "signal": 0}
	var left := 0
	var tag := ""
	var n_f := 0
	var who: Dictionary = {}
	var close := false
	while d.time < PLAY and pv.playing:
		pv._process(DT)
		if left == 0 and int(films["signal"]) < 2:
			# A goal umpire signalling a score.
			for u in oval.umpires:
				if not (u as Dictionary).has("clip") or str(u["clip"].get("kind", "")) != "signal" \
						or float(u["clip"]["t"]) > 0.1:
					continue
				films["signal"] = int(films["signal"]) + 1
				tag = "signal_%d" % int(films["signal"])
				DirAccess.make_dir_recursive_absolute(out.path_join(tag))
				left = 90
				n_f = 0
				who = u
				close = true
				print("CREW " + tag + ": goal umpire at (%.1f, %.1f), %s at %.0f s" % [u["node"].position.x,
						u["node"].position.z, u["anim"].current_animation, d.time])
				break
		if left == 0:
			for c in oval.crew.crew:
				if int(c["job"]) < 0:
					continue
				var kind := "drinks" if str(c["role"]) == "trainer" else "runner"
				if int(films[kind]) >= 1:
					continue
				films[kind] = int(films[kind]) + 1
				tag = "%s_%d" % [kind, int(films[kind])]
				DirAccess.make_dir_recursive_absolute(out.path_join(tag))
				left = 150
				n_f = 0
				who = c
				close = false
				print("CREW %s: %s from (%.1f, %.1f) to man %d at %.0f s" % [tag, str(c["role"]),
						c["home"].x, c["home"].y, int(c["job"]), d.time])
				break
		if left > 0:
			var n: Node3D = who["node"]
			var mid := n.global_position + Vector3(0, 1.0, 0)
			var to_field := -Vector3(n.position.x, 0, n.position.z).normalized()
			if close:
				# The goal umpire from up the ground, a little off his line, at his height.
				cam.global_position = mid + to_field * 6.0 + to_field.cross(Vector3.UP) * 2.0 + Vector3(0, 0.4, 0)
			else:
				# From the ground's side of him (behind him is the fence).
				cam.global_position = mid + to_field * 10.0 + to_field.cross(Vector3.UP) * 4.0 + Vector3(0, 2.5, 0)
			cam.look_at(mid + Vector3(0, 0.3 if close else 0.0, 0), Vector3.UP)
			cam.current = true
			if n_f % (3 if close else 6) == 0:
				await _shot(pv, out.path_join(tag), "f%03d" % n_f)
			else:
				await process_frame
			n_f += 1
			left -= 1
			if left == 0:
				print("CREW %s: ended at (%.1f, %.1f), job %d" % [tag, n.position.x, n.position.z, int(who.get("job", -1))])
		if int(films["drinks"]) >= 1 and int(films["runner"]) >= 1 and int(films["signal"]) >= 2 and left == 0:
			break
	print("CREW films: drinks %d, runner %d, signal %d, %.0f s played" % [int(films["drinks"]),
			int(films["runner"]), int(films["signal"]), d.time])
	quit()
