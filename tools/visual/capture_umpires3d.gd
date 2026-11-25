extends SceneTree
## The umpires at stoppages on the 3D oval (row 197): a centre bounce, a ball-up and a throw-in,
## each filmed from beside the umpire who takes it, and measured over a seeded match:
##   godot --path . --rendering-method mobile --script tools/visual/capture_umpires3d.gd -- OUTDIR [SEED]
## The match plays through the match view (PitchView, 3D), filmed from a camera of its own.
## Prints, per stoppage kind, how many there were, how many the umpire had the ball for, the
## widest gap between his palms and the ball while he held it, and the fastest the ball moved
## in one frame while it was his (a jump shows as a speed no throw has).

const DT := 1.0 / 30.0
const PLAY := 2400.0         # director seconds at most
var WANT := {"bounce": 2, "throwup": 2, "throwin": 2}
const SEQ := 80              # frames filmed per stoppage, every SEQ_EVERY-th saved
const SEQ_EVERY := 3


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://umpires3d"
	var seed := int(args[1]) if args.size() > 1 else 31
	DirAccess.make_dir_recursive_absolute(out)
	# UMP_ONLY=throwin (or bounce, throwup): film only that kind.
	if OS.get_environment("UMP_ONLY") != "":
		WANT = {OS.get_environment("UMP_ONLY"): 2}
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(960, 720)
	# Through the match view, as a match is watched: goal replays hold the play, and the
	# umpires go to their marks while the picture is away (Oval3D.umpires_after_cut).
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
	# Driven only by this script's steps, never by the engine's frames while it waits on a draw.
	pv.set_process(false)
	var d = pv.director
	var oval = pv._oval3d
	var cam := Camera3D.new()
	cam.fov = 38.0
	oval.add_child(cam)
	var seen := {}       # kind -> count of stoppages
	var had := {}        # kind -> count the umpire had the ball for
	var filmed := {}
	var gap := 0.0
	var fast := 0.0
	var last_kind := ""
	var last_at := Vector2.INF
	var got := false
	var prev := Vector3.INF
	var played := 0.0
	var film_left := 0
	var film_n := 0
	var film_tag := ""
	var film_u := -1
	while d.time < PLAY and pv.playing:
		pv._process(DT)
		played = d.time
		var st: Dictionary = d.stoppage_now()
		var kind := str(st.get("kind", ""))
		if kind != "" and (kind != last_kind or (st["at"] as Vector2).distance_to(last_at) > 1.0):
			seen[kind] = int(seen.get(kind, 0)) + 1
			last_kind = kind
			last_at = st["at"]
			got = false
		if kind == "":
			last_kind = ""
		var held: bool = oval._ump_ball
		if held and kind != "" and not got:
			got = true
			had[kind] = int(had.get(kind, 0)) + 1
			if kind != "bounce" and int(filmed.get(kind, 0)) < int(WANT.get(kind, 0)) and film_left == 0:
				filmed[kind] = int(filmed.get(kind, 0)) + 1
				film_left = SEQ
				film_n = 0
				film_tag = "%s_%d" % [kind, int(filmed[kind])]
				film_u = oval._ump_job
				DirAccess.make_dir_recursive_absolute(out.path_join(film_tag))
		# A bounce is filmed from the start of the umpire's wind-up; a ball-up or throw-in from
		# when he has the ball, its frames thinned while he waits.
		if kind == "bounce" and film_left == 0 and oval._ump_job >= 0 \
				and int(filmed.get(kind, 0)) < int(WANT.get(kind, 0)) \
				and str((oval.umpires[oval._ump_job] as Dictionary).get("clip", {}).get("kind", "")) == "bounce":
			filmed[kind] = int(filmed.get(kind, 0)) + 1
			film_left = SEQ
			film_n = 0
			film_tag = "%s_%d" % [kind, int(filmed[kind])]
			film_u = oval._ump_job
			DirAccess.make_dir_recursive_absolute(out.path_join(film_tag))
		if film_left > 0 and held and not film_tag.begins_with("bounce") and film_left < 30:
			film_left = 30
		if held and oval._ump_pick < 0.0 and oval._ump_job >= 0 and not pv._tv.replaying:
			var u: Dictionary = oval.umpires[oval._ump_job]
			var c: Dictionary = u.get("clip", {})
			if not (str(c.get("kind", "")) == "bounce" and float(c["t"]) >= oval.UMP_T_REL):
				gap = maxf(gap, oval._umpire_hands(u).distance_to(oval.ball.global_position))
				if prev.is_finite():
					var sp: float = prev.distance_to(oval.ball.global_position) / DT
					fast = maxf(fast, sp)
					if sp > 15.0:
						print("UMPIRES fast ball %.1f m/s at %.1f s, %s, clip %s t %.2f" % [sp, d.time, kind, c.get("kind", "-"), float(c.get("t", -1.0))])
		prev = oval.ball.global_position if held and not pv._tv.replaying else Vector3.INF
		if film_left > 0 and OS.get_environment("UMP_TRACE") != "":
			var cu: Dictionary = (oval.umpires[film_u] as Dictionary).get("clip", {}) if film_u >= 0 else {}
			print("TRACE %s f%03d t %.2f st %s in %.2f sure %s clip %s %.2f ball %s held %s" % [film_tag, film_n, d.time,
					kind, float(st.get("in", -1.0)), st.get("sure", "-"), cu.get("kind", "-"), float(cu.get("t", -1.0)),
					d.ball.get("mode", ""), held])
		if film_left > 0:
			var job: int = film_u
			if job >= 0:
				var n: Node3D = oval.umpires[job]["node"]
				var fw := n.transform.basis.z
				var side := fw.cross(Vector3.UP).normalized()
				var c := n.position + fw * 1.2 + Vector3(0, 1.1, 0)
				# From beside him; at a throw-in from the ground behind him (beside him is the fence).
				var eye := c + side * 7.5 + Vector3(0, 0.6, 0)
				if film_tag.begins_with("throwin"):
					# From along the line, side on to his throw (Oval3DCrew.THROW_IN).
					eye = c - fw * 1.2 + side * 4.2 + Vector3(0, 0.0, 0)
				cam.global_position = oval.to_global(eye)
				cam.look_at(oval.to_global(c), Vector3.UP)
				cam.current = true
			var throwing: bool = job >= 0 and str((oval.umpires[job] as Dictionary).get("clip", {}).get("kind", "")) == "throw"
			if film_n % (SEQ_EVERY * (3 if held and not throwing and not film_tag.begins_with("bounce") else 1)) == 0:
				await RenderingServer.frame_post_draw
				await RenderingServer.frame_post_draw
				pv._vp3d.get_texture().get_image().save_png(
						out.path_join(film_tag).path_join("f%03d.png" % film_n))
			else:
				await process_frame
			film_n += 1
			film_left -= 1
		var done := true
		for k in WANT:
			if int(filmed.get(k, 0)) < int(WANT[k]):
				done = false
		if done and film_left == 0:
			break
	for k in ["bounce", "throwup", "throwin"]:
		print("UMPIRES %s: %d stoppages, umpire had the ball at %d" % [k, int(seen.get(k, 0)), int(had.get(k, 0))])
	print("UMPIRES ball in his hands: widest gap %.3f m, fastest %.1f m/s, %.0f s played" % [gap, fast, played])
	quit()
