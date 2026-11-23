extends SceneTree
## The goal umpire's flags on the 3D oval (row 202): after a goal (and after a behind) the goal
## umpire at that end is filmed from the ground in front of his goal through his whole routine
## (Oval3DGoalUmpire), and measured:
##   godot --path . --rendering-method mobile --script tools/visual/capture_goal_flags3d.gd -- OUTDIR [SEED]
## Prints each step of his routine as it starts, every time a flag changes hands or goes back in
## the padding with how far it moved that frame (a pop shows as a jump no hand makes), the
## fastest any flag moved in one frame, and the gap between each stowed flag and the post's
## padding.

const DT := 1.0 / 30.0
const PLAY := 2400.0
const EVERY := 3               # every EVERY-th frame saved
const MOST := 40.0 / DT        # frames filmed at most per routine


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://goal_flags3d"
	var seed := int(args[1]) if args.size() > 1 else 31
	DirAccess.make_dir_recursive_absolute(out)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(960, 720)
	var pv = load("res://scripts/ui/PitchView.gd").new()
	pv.size = Vector2(960, 720)
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
	var goal_umps := []
	for u in oval.umpires:
		if str(u["role"]) == "goal" and (u as Dictionary).has("flag"):
			goal_umps.append(u)
			var f: Dictionary = u["flag"]
			for s in ["r", "l"]:
				var n: Node3D = u["flags"][s]["node"]
				var post := Vector3(n.position.x, 0.0, signf(n.position.z) * 3.2)
				print("FLAGS stowed %s end %+.0f: %.3f m off the post's centre (padding 0.36), %.2f m up, near hand %s" % [
						s, signf(n.position.x), Vector2(n.position.x, n.position.z).distance_to(Vector2(post.x, post.z)),
						n.position.y, f["near"]])
	print("FLAGS goal umpires with flags: %d" % goal_umps.size())
	var want := {"goal": 1, "behind": 1}
	if OS.get_environment("FLAGS_NOFILM") != "":
		want = {}
	var filmed := {}
	var film_u := {}
	var film_n := 0
	var film_tag := ""
	var prev := {}
	var parent := {}
	var step_seen := {}
	var fastest := 0.0
	var worst_change := 0.0
	while d.time < PLAY and pv.playing:
		pv._process(DT)
		for u in goal_umps:
			var key := int(u["k"])
			if (u as Dictionary).has("routine"):
				var r: Dictionary = u["routine"]
				var i := int(r["i"])
				var steps: Array = r["steps"]
				if int(step_seen.get(key, -1)) != i and i < steps.size():
					step_seen[key] = i
					var s: Dictionary = steps[i]
					print("FLAGS k%d %.1f s step %d %s %s" % [key, d.time, i, s["do"], s.get("clip", s.get("for", ""))])
				if film_tag == "" and i == 0:
					var kind := "finish"
					for st in steps:
						var c := str((st as Dictionary).get("clip", ""))
						if c.begins_with("flags_draw"):
							kind = "goal"
						elif c.begins_with("behind_flag") and not (st as Dictionary).has("from"):
							kind = "behind"
					if int(filmed.get(kind, 0)) < int(want.get(kind, 0)):
						filmed[kind] = int(filmed.get(kind, 0)) + 1
						film_tag = "%s_%d" % [kind, int(filmed[kind])]
						film_u = u
						film_n = 0
						DirAccess.make_dir_recursive_absolute(out.path_join(film_tag))
			else:
				step_seen.erase(key)
			# A flag in a hand follows it when the skeleton next updates (a drawn frame); this loop
			# also steps the match without drawing, so bring the hands' attachments up to date.
			(u["skel"] as Skeleton3D).force_update_all_bone_transforms()
			for s in ["r", "l"]:
				(u["flags"][s]["on"] as BoneAttachment3D).on_skeleton_update()
			for s in ["r", "l"]:
				var n: Node3D = u["flags"][s]["node"]
				var at := n.global_position
				var pk := "%d%s" % [key, s]
				var par := str(n.get_parent().name) if n.get_parent() != null else "-"
				if pv._tv.replaying:
					# The replay shows the past (the flags drawn back in the padding); the picture
					# cuts in and out of it, so no frame-to-frame move counts across it.
					prev.erase(pk)
					parent[pk] = par
					continue
				if prev.has(pk):
					var jump: float = (prev[pk] as Vector3).distance_to(at)
					fastest = maxf(fastest, jump / DT)
					if jump / DT > 8.0:
						var rr: Dictionary = u.get("routine", {})
						print("FLAGS k%d flag %s fast %.1f m/s at %.1f s, step %s, anim %s %.2f" % [key, s, jump / DT, d.time,
								rr.get("i", -1), (u["anim"] as AnimationPlayer).current_animation,
								(u["anim"] as AnimationPlayer).current_animation_position])
						print("FLAGS   him at %s rot %.3f oval rot %.2f; flag was %s now %s (%s); him global %s" % [(u["node"] as Node3D).position,
								(u["node"] as Node3D).rotation.y, oval.rotation.y, prev[pk], at, par, (u["node"] as Node3D).global_position])
					if par != str(parent.get(pk, par)):
						worst_change = maxf(worst_change, jump)
						print("FLAGS k%d flag %s %s -> %s at %.1f s: moved %.3f m that frame" % [key, s, parent[pk], par, d.time, jump])
						var un: Node3D = u["node"]
						var fg: Dictionary = u["flag"]
						print("FLAGS   him at %s post %s yaw %.3f want %.3f scale %s anim %s %.2f" % [un.position, fg["post"],
								un.rotation.y, fg["yaw"], un.scale, (u["anim"] as AnimationPlayer).current_animation,
								(u["anim"] as AnimationPlayer).current_animation_position])
				prev[pk] = at
				parent[pk] = par
		if film_tag != "":
			var u: Dictionary = film_u
			var f: Dictionary = u["flag"]
			var end := signf((u["node"] as Node3D).position.x)
			var mid: Vector2 = ((f["post"] as Vector2) + (f["wave"] as Vector2)) * 0.5
			var c := Vector3(mid.x, 1.25, mid.y)
			var eye := c + Vector3(-end * 9.0, 0.5, 0.0)
			cam.global_position = oval.to_global(eye)
			cam.look_at(oval.to_global(c), Vector3.UP)
			cam.current = true
			if film_n % EVERY == 0:
				await RenderingServer.frame_post_draw
				await RenderingServer.frame_post_draw
				pv._vp3d.get_texture().get_image().save_png(out.path_join(film_tag).path_join("f%04d.png" % film_n))
			else:
				await process_frame
			film_n += 1
			if not u.has("routine") or film_n > MOST:
				print("FLAGS filmed %s: %d frames" % [film_tag, film_n])
				film_tag = ""
		if want.is_empty():
			# Unfilmed: still a frame of the engine's own each step, so the hands' attachments
			# are bound and follow as they do in a match.
			await process_frame
		var done := true
		for k in want:
			if int(filmed.get(k, 0)) < int(want[k]):
				done = false
		if done and film_tag == "" and not want.is_empty():
			break
	print("FLAGS fastest a flag moved in a frame: %.1f m/s; largest move on changing hands: %.3f m; %.0f s played" % [
			fastest, worst_change, d.time])
	quit()
