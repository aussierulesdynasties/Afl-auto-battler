extends RefCounted
## The bug bash's body (play3d.gd loads it once the autoloads are up).

const TELE := 13.0       # m/s of match time a body may run (a sprint is about 9)
const HIPS_OFF := 3.5    # m his hips may sit off the engine's spot (a tackle clip carries him up to 3)
const BALL_HANDS := 1.2  # m the held ball may be from its holder
const STALL_S := 20.0    # real s of play with the director's clock still
const MAX_PER_KIND := 6

var _counts := {}
var _ctx: Array = []


func fault(kind: String, f: int, detail: String) -> void:
	var n := int(_counts.get(kind, 0)) + 1
	_counts[kind] = n
	if n <= MAX_PER_KIND:
		print("FAULT %s %d %s" % [kind, f, detail])
		if n <= 4 and (kind.begins_with("ball") or kind == "stall"):
			for c in _ctx:
				print(c)


static func _finite(v: Vector3) -> bool:
	return is_finite(v.x) and is_finite(v.y) and is_finite(v.z)


var root: Window
var tree: SceneTree


func run(p_tree: SceneTree) -> void:
	tree = p_tree
	root = tree.root
	OS.low_processor_usage_mode = false
	var club := "FRE"
	var seed := 7
	var ground := ""
	var weather := ""
	var tod := ""
	var quality := "high"
	var speed := 4.0
	var max_frames := 200000
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--club": club = str(a[i + 1])
			"--seed": seed = int(a[i + 1])
			"--ground": ground = str(a[i + 1])
			"--weather": weather = str(a[i + 1])
			"--time": tod = str(a[i + 1])
			"--quality": quality = str(a[i + 1])
			"--speed": speed = float(a[i + 1])
			"--frames": max_frames = int(a[i + 1])
	await tree.process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://bugbash3d.save"
	state.settings_path = "user://bugbash3d.cfg"
	state.reset()
	state.career_seed = seed
	state.replay_seed = seed
	state.set_setting("seen_training_intro", true)
	state.set_vignettes_on(false)
	state.set_match_3d_on(true)
	if state.has_method("set_graphics_quality"):
		state.set_graphics_quality(quality)
	state.start_season(club, db.club_list(club))
	if not state.prepare_interactive_match():
		print("FAULT setup 0 no match to play")
		tree.quit(1)
		return
	if ground != "":
		state.pending_match["venue"] = ground
	if weather != "" and state.pending_sim != null and "weather" in state.pending_sim:
		state.pending_sim.weather = weather
	root.size = Vector2i(540, 1200)
	var scene = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(scene)
	for i in 5:
		await tree.process_frame
	var pitch = scene._pitch
	if pitch._oval3d == null:
		print("FAULT setup 0 no 3D oval on the match screen")
		tree.quit(1)
		return
	if pitch.graphics != quality:
		pitch._oval3d.quality = quality
		Oval3DQuality.apply_viewport(quality, pitch._vp3d)
	var w: String = weather if weather != "" else str(pitch.result.get("weather", ""))
	if tod != "":
		pitch.time_override = tod
	if weather != "" or tod != "":
		pitch._oval3d.turf.apply(w, pitch.time_of_day(w))
	print("START club=%s seed=%d ground=%s (%s) weather=%s time=%s quality=%s home=%s away=%s" % [club, seed,
			pitch._oval3d.ground, GroundModels.slug_for(pitch._oval3d.ground), w, pitch.time_of_day(w),
			pitch._oval3d.quality, pitch.home_code, pitch.away_code])
	var last := {}        # i -> local Vector3 last live frame
	var last_tok := {}
	var last_ump := {}
	var last_ball := Vector3.INF
	var last_dt := -1.0
	var still := 0.0
	var off_screen := 0
	var off_worst := 0
	var hover := 0
	var prev_shot := ""
	var prev_period := 1
	var prev_rot := 0.0
	var worst_ms := 0
	var slow := 0
	var f := 0
	var moments := 0
	var starts := 0
	while f < max_frames:
		f += 1
		var t0 := Time.get_ticks_msec()
		await tree.process_frame
		var ms := Time.get_ticks_msec() - t0
		if f > 30:
			worst_ms = maxi(worst_ms, ms)
			if ms > 250:
				slow += 1
				if slow <= 3:
					print("SLOW %d %d ms" % [f, ms])
		if scene._finished:
			break
		var go = scene.find_child("StartQuarter", true, false)
		if go != null and go.is_visible_in_tree():
			starts += 1
			go.pressed.emit()
			continue
		var sim = state.pending_sim
		if sim != null and not sim.pending_moment.is_empty():
			var card = scene.find_child("MomentCard", true, false)
			if card != null and is_instance_valid(card):
				moments += 1
				scene.call("_on_moment_choice", int(sim.pending_moment.get("default", 0)))
				continue
		if pitch.speed != speed:
			pitch.set_speed(speed)
		if not pitch.playing:
			continue
		var oval: Oval3D = pitch._oval3d
		if oval != null:
			var hh := int(pitch.director.ball.get("holder", -1))
			_ctx.append("  ctx %d t=%.2f dmode=%s bmode=%s holder=%d bpos=%s h=%.2f ball3d=%s period=%d emitted=%d shot=%s ump_ball=%s gone=%s st=%s job=%d in_hands=%s drop_t=%.2f off_t=%.2f pick=%.2f sting=%.2f" % [f,
					pitch.director.time, pitch.director.mode, pitch.director.ball.get("mode", ""), hh, pitch.director.ball["pos"],
					float(pitch.director.ball.get("h", 0.0)), oval.to_local(oval.ball.global_position), pitch.period, pitch.director.emitted,
					pitch._tv.shot, oval._ump_ball, oval._ump_gone, pitch.director.stoppage_now(), oval._ump_job, oval._in_hands, oval._drop_t, oval._ump_off_t, oval._ump_pick, pitch._tv.sting()])
			if _ctx.size() > 3:
				_ctx.pop_front()
		if oval == null:
			fault("oval_gone", f, "the 3D oval went away mid-match")
			break
		var tv = pitch._tv
		var d: MatchDirector = pitch.director
		var shot: String = "replay" if tv.replaying else ("close" if tv._close_who >= 0 else ("incident" if not tv._inc.is_empty() else tv.shot))
		var cut: bool = shot != prev_shot or pitch.period != prev_period or not is_equal_approx(oval.rotation.y, prev_rot) or tv.sting() >= 0.0
		prev_shot = shot
		prev_period = pitch.period
		prev_rot = oval.rotation.y
		# The director's clock: a stall is play that never moves on.
		var dt_now := float(d.time)
		var ddt := maxf(0.0, dt_now - last_dt) if last_dt >= 0.0 else 0.0
		if is_equal_approx(dt_now, last_dt) and not tv.replaying:
			still += 1.0 / 30.0
			if still > STALL_S:
				fault("stall", f, "director clock stuck at %.1f, mode %s, emitted %d/%d" % [dt_now, d.mode, d.emitted, d.events.size()])
				still = -1e9
		else:
			still = 0.0
		last_dt = dt_now
		# The camera.
		var cam: Camera3D = oval.camera
		if not _finite(cam.global_position):
			fault("camera_nan", f, "camera at %s" % cam.global_position)
		elif cam.global_position.y < 0.5:
			fault("camera_low", f, "camera %.2f m up on %s" % [cam.global_position.y, shot])
		var bg: Vector3 = oval.ball.global_position
		if not _finite(bg):
			fault("ball_nan", f, "ball at %s" % bg)
			continue
		if shot == "main" and not tv.replaying:
			if not cam.is_position_in_frustum(bg):
				off_screen += 1
				off_worst = maxi(off_worst, off_screen)
				if off_screen == 45:
					fault("ball_off_screen", f, "main camera lost the ball for 1.5 s (ball %s, mode %s)" % [oval.to_local(bg), d.ball.get("mode", "")])
			else:
				off_screen = 0
		if tv.replaying:
			last.clear()
			last_ump.clear()
			last_ball = Vector3.INF
			continue
		# The ball.
		var bl: Vector3 = oval.to_local(bg)
		var mode := str(d.ball.get("mode", ""))
		if bl.y < -0.05:
			fault("ball_under_turf", f, "ball %.2f m under the turf, mode %s" % [bl.y, mode])
		if mode == "held":
			hover = 0
		elif mode == "carry" and not oval._ump_ball and not oval._in_hands and tv.sting() < 0.0 and absf(bl.y - 1.2) < 0.02:
			fault("ball_glides", f, "ball carried %.2f m up with nobody holding it, director mode %s" % [bl.y, d.mode])
		elif mode != "flight" and oval._drop_t < 0.0 and not oval._ump_ball and not oval._in_hands and bl.y > 0.6:
			hover += 1
			if hover == 6:
				fault("ball_hovers", f, "ball %.2f m up, mode %s, nobody holding it, director mode %s" % [bl.y, mode, d.mode])
		else:
			hover = 0
		if last_ball != Vector3.INF and not cut and bl.distance_to(last_ball) > 70.0 * ddt + 1.0:
			fault("ball_jump", f, "ball jumped %.1f m in %.2f s, mode %s" % [bl.distance_to(last_ball), ddt, mode])
			if int(_counts.get("ball_jump", 0)) <= 3:
				print("  beat ", d._beat.get("kind", ""), " k=", d._beat.get("k", -1), " pi=", d._pi, " phase=", d._phases[d._pi] if d._pi < d._phases.size() else {}, " prev=", d._phases[d._pi - 1] if d._pi > 0 and d._pi - 1 < d._phases.size() else {})
				var hj := int(d.ball.get("holder", -1))
				if hj >= 0:
					var pj: Dictionary = oval.players[hj]
					var sj: Skeleton3D = pj["skel"]
					print("  holder node ", (pj["node"] as Node3D).position, " token ", d.tokens[hj]["pos"], " hips ",
							oval.to_local(sj.global_transform * sj.get_bone_global_pose(oval._pelvis(pj)).origin), " clip ",
							(pj["anim"] as AnimationPlayer).current_animation)
				for e in range(maxi(0, d.emitted - 2), mini(d.events.size(), d.emitted + 2)):
					print("  ev ", e, " ", d.events[e])
		last_ball = bl
		# The players.
		for i in range(oval.players.size()):
			var p: Dictionary = oval.players[i]
			var node: Node3D = p["node"]
			if not _finite(node.position):
				fault("player_nan", f, "player %d at %s" % [i, node.position])
				continue
			var skel: Skeleton3D = p["skel"]
			var hips := oval.to_local(skel.global_transform * skel.get_bone_global_pose(oval._pelvis(p)).origin)
			var clip := (p["anim"] as AnimationPlayer).current_animation
			var tok: Vector2 = d.tokens[i]["pos"]
			var lp := Vector3(hips.x, 0.0, hips.z)
			if last.has(i) and not cut:
				var jump := lp.distance_to(last[i])
				if jump > TELE * ddt + 0.6:
					var tj := tok.distance_to(last_tok[i])
					fault("player_teleport", f, "player %d (%s) drawn %.1f m in %.2f s (engine token %.1f m), mode %s ball %s clip %s" % [i,
							d.tokens[i].get("pid", ""), jump, ddt, tj, d.mode, mode, clip])
			last[i] = lp
			last_tok[i] = tok
			var off := Vector2(hips.x - tok.x, hips.z - tok.y).length()
			if off > HIPS_OFF:
				fault("hips_off_spot", f, "player %d's hips %.1f m off the engine's spot, clip %s" % [i, off, clip])
			if hips.y < 0.12:
				fault("hips_in_turf", f, "player %d's hips %.2f m up, clip %s" % [i, hips.y, clip])
			elif hips.y > 2.6:
				fault("hips_high", f, "player %d's hips %.2f m up, clip %s" % [i, hips.y, clip])
			if absf(lp.x) > MatchMotion.HALF_LEN + 12.0 or absf(lp.z) > MatchMotion.HALF_WID + 12.0:
				fault("player_off_ground", f, "player %d at %s, outside the fence" % [i, lp])
			if mode == "held" and i == int(d.ball.get("holder", -1)) and not oval._ump_ball:
				var gap := Vector2(bl.x - hips.x, bl.z - hips.z).length()
				if gap > BALL_HANDS:
					fault("ball_off_holder", f, "held ball %.1f m from its holder %d's hips (%s), clip %s" % [gap, i, d.tokens[i].get("pid", ""), clip])
		for k in range(oval.umpires.size()):
			var un: Node3D = oval.umpires[k]["node"]
			if not _finite(un.position):
				fault("umpire_nan", f, "umpire %d" % k)
				continue
			if last_ump.has(k) and not cut and un.position.distance_to(last_ump[k]) > TELE * ddt + 0.6 and not oval._ump_cut:
				fault("umpire_teleport", f, "umpire %d (%s) moved %.1f m in a frame" % [k, oval.umpires[k]["role"], un.position.distance_to(last_ump[k])])
			last_ump[k] = un.position
	var final: bool = scene._finished
	print("DONE frames=%d final=%s starts=%d moments=%d worst_ms=%d slow=%d off_screen_worst=%d score=%s" % [f, final, starts, moments,
			worst_ms, slow, off_worst, str(scene._res.get("score", ""))])
	for k in _counts:
		print("COUNT %s %d" % [k, _counts[k]])
	if not final:
		print("FAULT unfinished %d match did not reach full time in %d frames" % [f, f])
	tree.quit(0)
