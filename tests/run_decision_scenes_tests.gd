extends SceneTree
## godot --headless --path . --script tests/run_decision_scenes_tests.gd
## TODO row 13: tired, duel, hot, momentum and set shot each open on a scene (DecisionVignette)
## when the Vignettes setting is on, and stay the text card
## otherwise. The scene shows the players the call is about, in their own kits and builds,
## with the ball only ever at a palm; the call under it is MatchSim's, and takes a real tap.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 2027
const KINDS := ["tired", "duel", "hot", "momentum", "set_shot"]

var _state: Node
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_state.autosave_enabled = false
	_state.save_path = "user://test_career.save"
	_state.settings_path = "user://test_settings.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.replay_seed = SUITE_SEED
	for kind in KINDS:
		await _t("_test_kind", [kind])
	await _t("_test_set_spots")
	await _t("_test_card_without_vignettes")
	for kind in KINDS:
		await _t("_test_tap", [kind])
	await _t("_test_no_chosen_defender")
	await _t("_test_first_call_warmed")
	for size in [Vector2i(390, 844), Vector2i(1920, 1080)]:
		await _t("_test_framing", [size])
	await _t("_test_cast_and_idle")
	await _t("_test_wind_drift")
	print(Ran.line("Decision scenes", self))
	for f in _failures:
		print("  FAIL: ", f)
	quit(1 if _failures.size() > 0 else 0)


## A live match, one quarter in, and the screen showing it. Released: the oval has played
## everything the sim has rolled, as when a call comes up in a match (MatchScene._on_finished),
## so the scoreboard shows the sim's score; otherwise the oval is paused.
func _match(released := false, phone := Vector2i(360, 740)) -> Dictionary:
	var db = root.get_node("GameDB")
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.start_season("COL", db.club_list("COL"))
	root.size = phone
	_check(_state.prepare_interactive_match(), "A live match is prepared")
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _settle()
	(m.find_child("StartQuarter", true, false) as Button).emit_signal("pressed")
	await _settle()
	if released:
		m.set("_skipping", true)
		m.get("_pitch").release_all()
		m.set("_skipping", false)
	else:
		m.get("_pitch").pause()
	var sim = _state.pending_sim
	return {"m": m, "sim": sim, "me": int(m.get("_my_side"))}


## The call MatchSim would ask, built from the real squads (ids the way MatchSim fires them).
func _moment(sim, me: int, kind: String) -> Dictionary:
	var them := 1 - me
	var mine: Array = sim.squads[me].ground
	var theirs: Array = sim.squads[them].ground
	var fwd: Dictionary = theirs.filter(func(p): return str(p["role"]) == "FWD")[0]
	var mid: Dictionary = theirs.filter(func(p): return str(p["role"]) == "MID")[0]
	var dfn: Dictionary = theirs.filter(func(p): return str(p["role"]) == "DEF")[0]
	var mine_def: Dictionary = mine.filter(func(p): return str(p["role"]) == "DEF")[0]
	var star: Dictionary = mine[0]
	var opts := [
		{"key": "a", "label": "First", "detail": "One."},
		{"key": "b", "label": "Second", "detail": "Two."},
		{"key": "none", "label": "Third", "detail": "Three."},
	]
	if kind == "tired":
		opts = opts.slice(0, 2)   # MatchSim offers the tired call two ways
	var m := {"kind": kind, "title": "A call", "text": "Make it.", "options": opts, "q": 2, "min": 50,
			"default": opts.size() - 1}
	match kind:
		"tired":
			m["player_id"] = str(star["id"])
			m["sub_id"] = str(sim.squads[me].bench[0]["id"])
		"duel":
			m["player_id"] = str(fwd["id"])
			sim.duels[me][str(fwd["id"])] = str(mine_def["id"])
		"hot":
			m["player_id"] = str(mid["id"])
		"set_shot":
			m["player_id"] = str(star["id"])
			m["defender_id"] = str(dfn["id"])
	return m


func _test_kind(kind: String) -> void:
	var db = root.get_node("GameDB")
	var ctx := await _match()
	var m: Control = ctx["m"]
	var sim = ctx["sim"]
	var me: int = ctx["me"]
	_state.set_vignettes_on(true)
	sim.moment_side = me
	sim.pending_moment = _moment(sim, me, kind)
	var call: Dictionary = sim.pending_moment
	m.call("_show_moment")
	await _settle()
	var card = m.find_child("MomentCard", true, false)
	var vig = m.find_child("DecisionVignette", true, false)
	_check(card != null and vig != null and m.find_child("StoppageVignette", true, false) == null,
			"%s: the call opens on its scene" % kind)
	if card == null or vig == null:
		m.queue_free()
		return
	var viewport := Rect2(Vector2.ZERO, Vector2(360, 740))
	_check(vig.size.y >= 220.0 and viewport.encloses(vig.get_global_rect()), "%s: the scene fills a phone" % kind)
	# The players are the call's: real ids from this match, in their own looks and clubs.
	var ids := {}
	for side in range(2):
		for p in sim.squads[side].ground + sim.squads[side].bench:
			ids[str(p["id"])] = p
	var real: bool = not vig.tokens.is_empty()
	var looks := true
	for t in vig.tokens:
		real = real and ids.has(str(t["id"]))
		if ids.has(str(t["id"])):
			looks = looks and t["look"] == db.figure_look(ids[str(t["id"])], false)
	_check(real and looks, "%s: every figure is a real player of this match in his own look" % kind)
	var wanted: Array = {"tired": ["tired", "sub"], "duel": ["duel_d", "duel_f"], "hot": ["carrier", "chaser"],
			"momentum": ["wait", "back_to_square"], "set_shot": ["kicker", "on_the_mark"]}[kind]
	var roles: Array = vig.tokens.map(func(t): return str(t["role"]))
	_check(wanted.all(func(r): return roles.has(r)), "%s: the men in the call are on stage (%s)" % [kind, str(roles)])
	var subject_id: String = str(call.get("player_id", ""))
	if subject_id != "":
		_check(vig.tokens.any(func(t): return str(t["id"]) == subject_id), "%s: the call's player is in the scene" % kind)
	if kind == "set_shot":
		_check(vig.tokens.any(func(t): return str(t["id"]) == str(call["defender_id"]) and int(t["side"]) == 1 - me),
				"set_shot: the man on the mark is the opposition defender")
	if kind == "duel":
		var d: Dictionary = vig.token_of("duel_d")
		_check(str(d.get("id", "")) == str(sim.duels[me][str(call["player_id"])]), "duel: your man on him is the match-up")
	# Both clubs' kits.
	var mat := vig.material as ShaderMaterial
	var kits: Array = Array(mat.get_shader_parameter("kit_base")) if mat != null else []
	var mine_g: Dictionary = db.club_guernsey(str(sim.squads[me].code))
	var theirs_g: Dictionary = db.club_guernsey(str(sim.squads[1 - me].code))
	_check(kits.size() == 4 and kits[me] == mine_g["base"] and kits[1 - me] == theirs_g["base"],
			"%s: both clubs' guernseys are on the figures" % kind)
	# The intended sheet, and every frame asked for is inside it (no fallback, no overrun).
	var sheet_ok := Vector2i((vig.FIGURE_SHADE as Texture2D).get_size()) == VignetteFigures.SHEET_SIZE
	for step in range(0, 40):
		vig.set("_t", float(vig.get("_end")) * step / 39.0)
		for t in vig.tokens:
			var pick: Array = vig.call("_frame", t, vig.call("_lift", t), vig.call("_pos", t), bool(t["mine"]))
			var facing: String = str(pick[3]) if pick.size() > 3 else str(t["face"])
			var build: String = vig.call("_body", t)
			if not VignetteFigures.has(build, str(pick[0]), facing):
				build = "average"
			var ok: bool = VignetteFigures.has(build, str(pick[0]), facing)
			if ok:
				var info := VignetteFigures.strip(build, str(pick[0]), facing)
				ok = int(pick[1]) >= 0 and int(pick[1]) < int(info["frames"])
			sheet_ok = sheet_ok and ok
	_check(sheet_ok, "%s: every move the scene plays is in the figure sheet, in range" % kind)
	# It plays in, then freezes for the call; no tap makes the call early.
	vig.set("_t", 0.0)
	vig.set("_frozen", false)
	vig.set("_hold", 0.0)
	var b0: Button = card.find_child("Moment_0", true, false)
	_check(b0 != null and b0.disabled and not vig.is_frozen(), "%s: the call waits for the scene" % kind)
	vig.finish_now()
	await _settle()
	_check(vig.is_frozen() and not b0.disabled, "%s: frozen, the call is live" % kind)
	# The ball is never loose: in a kicker's hands, or met between two men's.
	if kind in ["set_shot", "duel"]:
		vig.set("_hold", 0.4)
		var a: Dictionary = vig.token_of("kicker" if kind == "set_shot" else "duel_d")
		var b: Dictionary = vig.token_of("kicker" if kind == "set_shot" else "duel_f")
		var pa: Vector2 = vig.palm_of(a, 0)
		var pb: Vector2 = vig.palm_of(b, 1)
		_check(pa != Vector2.INF and pb != Vector2.INF and viewport.has_point(pa) and viewport.has_point(pb),
				"%s: the ball has hands to be in, on screen" % kind)
	for i in range(40):
		await process_frame
	var off := []
	for b in card.find_children("Moment_*", "Button", true, false):
		if not viewport.encloses((b as Button).get_global_rect()) or (b as Button).size.y < 44:
			off.append(b.name)
	_check(off.is_empty() and card.find_children("Moment_*", "Button", true, false).size() == (call["options"] as Array).size(),
			"%s: every option is on screen and thumb-sized (%s)" % [kind, str(off)])
	# The big screen, when the scene shows it, shows whole: inside the picture, its writing
	# under the title bar.
	vig.call("_set_camera")
	var sr: Rect2 = load("res://scripts/ui/match/VignetteGround.gd").screen_rect(vig.ground_cam())
	if not bool(vig.call("_screen_board", vig.ground_cam()).get("off", false)) and sr.has_area():
		_check(sr.position.x >= 0.0 and sr.end.x <= vig.size.x and sr.position.y + sr.size.y * 0.15 >= vig.size.y * 0.075,
				"%s: the big screen shows whole (%s)" % [kind, str(sr)])
	var said := " ".join(vig.facts)
	_check(not said.contains("%") and not said.to_lower().contains("recommend"), "%s: no stats or advice over the scene" % kind)
	m.queue_free()
	await _settle()


## Director bug, 2026-11-08: the call said 25 metres out and the scene showed him at the
## 50. Every spot MatchSim names (SET_BANDS_ON) is staged where the call says, through the
## real call (MatchSim._offer_set_shot) on a smaller and a larger phone: the man on the mark
## on the call's metres, the kicker a step behind him on his line to the goals, in the cell of
## the ground the words name. Measured once the scene has frozen and the call has slid all the
## way up: both goal posts in the picture above the call, and no goal or behind post rising
## from behind either man; both men above
## the call with their names clear of the title bar; the man on the mark showing past the
## kicker; the big screen either in full from first frame to last or left out, and showing
## what the scoreboard shows.
var _goal_look := {}


func _test_set_spots() -> void:
	var VG = load("res://scripts/ui/match/VignetteGround.gd")
	var V = load("res://scripts/ui/match/DecisionVignette.gd")
	var MS: GDScript = load("res://scripts/sim/MatchSim.gd")
	_check(str(V.set_spot("")["key"]) == "front" and str(V.set_spot("mystery")["key"]) == "front",
			"set_shot without a spot: straight in front, 35 out")
	var goal_line := float((load("res://scripts/sim/Ratings.gd") as GDScript).get_script_constant_map()["T"]["goal_line"])
	for phone in [Vector2i(360, 740), Vector2i(390, 844)]:
		for band in MS.set_bands(0.34):
			var key := str(band["key"])
			var metres := float(band["metres"])
			var at := "set_shot %s at %dx%d" % [key, phone.x, phone.y]
			_check(V.SET_SPOTS.has(key), "%s: the scene has a spot for it" % at)
			var ctx := await _match(true, phone)
			var m: Control = ctx["m"]
			var sim = ctx["sim"]
			var me: int = ctx["me"]
			_state.set_vignettes_on(true)
			var mine: Array = sim.squads[me].ground
			var shooter: Dictionary = mine.filter(func(p): return str(p["role"]) == "FWD")[0]
			var feeder: Dictionary = mine.filter(func(p): return str(p["role"]) == "MID")[0]
			var defender: Dictionary = (sim.squads[1 - me].ground as Array).filter(func(p): return str(p["role"]) == "DEF")[0]
			sim.pending_moment = {}
			sim.moment_side = me
			sim._offer_set_shot(me, (1.0 if me == 0 else -1.0) * (goal_line - metres), shooter, defender, band, feeder)
			_check(str(sim.pending_moment.get("band_key", "")) == key and str(sim.pending_moment.get("title", "")).ends_with(str(band["spot"])),
					"%s: the real call names the spot" % at)
			m.call("_show_moment")
			await _settle()
			var vig = m.find_child("DecisionVignette", true, false)
			_check(vig != null, "%s: the call opens on its scene" % at)
			if vig == null:
				m.queue_free()
				await _settle()
				continue
			var first_off: bool = bool(vig.call("_screen_board", vig.ground_cam()).get("off", false))
			vig.finish_now()
			_check(await _call_settled(m, vig), "%s: the scene freezes and the call slides all the way up" % at)
			vig.call("_set_camera")
			var goal := Vector2(0.0, float(VG.GOAL_Y))
			var kicker: Vector2 = vig.spot_of(vig.token_of("kicker"))
			var mark: Vector2 = vig.spot_of(vig.token_of("on_the_mark"))
			var out := kicker.distance_to(goal)
			# The kicker walks back from his mark, five to eight metres, as a set shot is taken.
			_check(absf(out - metres - float(V.KICKER_BACK)) <= 0.5 and float(V.KICKER_BACK) >= 5.0 and float(V.KICKER_BACK) <= 8.0,
					"%s: the kicker is %.1f m out, five to eight metres behind the call's %d" % [at, out, int(metres)])
			_check(absf(mark.distance_to(goal) - metres) < 0.5 and mark.distance_to(goal) < out,
					"%s: the man on the mark stands on the call's metres, nearer the goals than the kicker" % at)
			var over := rad_to_deg(absf((mark - kicker).angle_to(goal - kicker)))
			_check(over < 1.0, "%s: the man on the mark is on the kicker's line to the goals (%.1f deg off it)" % [at, over])
			var off_line := func(p: Vector2) -> float:
				return rad_to_deg(atan2(absf(p.x - goal.x), goal.y - p.y))
			var angle: float = off_line.call(kicker)
			_check(absf(float(off_line.call(mark)) - float(V.SET_SPOTS[key])) < 0.5 and (angle > 60.0 if key == "pocket" else angle < 30.0),
					"%s: drawn %.1f deg off the line through the goals: under 30, the straight-in-front cell the sim converts it at; the pocket over 60" % [at, angle])
			_check((mark.distance_to(goal) > 50.0) == (key == "long"), "%s: the 50 m arc is %s his mark" % [at, "in front of" if key == "long" else "behind"])
			# In the picture: both posts and both men between the title bar and the call, with
			# room over each head for his name, and no post hidden behind a man.
			var panel: Control = m.find_child("BounceCall", true, false)
			var bottom: float = vig.size.y
			if panel != null:
				bottom = panel.get_global_rect().position.y - vig.get_global_rect().position.y
			var bar: float = vig.size.y * 0.075
			var cam = vig.ground_cam()
			var men := true
			var body := {}
			for role in ["kicker", "on_the_mark"]:
				var t: Dictionary = vig.token_of(role)
				var feet: Vector3 = vig.call("_project", vig.call("_pos", t), vig.call("_lift", t))
				var head: Vector3 = vig.call("_project", vig.call("_pos", t), float(vig.call("_lift", t)) + float(vig.call("_head_top", t)))
				men = men and feet.y < bottom and head.y > bar + 24.0 and feet.x > 0.0 and feet.x < vig.size.x
				# feet.z is pixels per metre at his distance: half his width with his arms in (x),
				# half his head's (y).
				body[role] = Vector3(feet.x, 0.5 * feet.z, 0.15 * feet.z)
				body[role + "|feet"] = feet
				body[role + "|head"] = head
			_check(men, "%s: both men stand above the call, their names clear of the title bar" % at)
			var posts := true
			var clear := true
			var post_x := []
			for x in [-1.5, -0.5, 0.5, 1.5]:
				var p: Vector3 = cam.oval(Vector2(x * float(VG.GOAL_GAP), goal.y))
				post_x.append(int(p.x))
				if absf(x) < 1.0:
					posts = posts and p.z > 0.0 and p.x > 0.0 and p.x < vig.size.x and p.y > bar and p.y < bottom
				# A post is a fault when it stands beyond a man and tops him: it would rise out of his head.
				var tip: Vector3 = cam.oval(Vector2(x * float(VG.GOAL_GAP), goal.y), float(VG.GOAL_H) if absf(x) < 1.0 else float(VG.BEHIND_H))
				for role in ["kicker", "on_the_mark"]:
					if p.z < (body[role + "|feet"] as Vector3).z and tip.y < (body[role + "|head"] as Vector3).y:
						clear = clear and absf(p.x - (body[role] as Vector3).x) > (body[role] as Vector3).y
			_check(posts, "%s: both goal posts stand in the scene, above the call" % at)
			_check(clear and bool(vig.posts_clear()), "%s: no goal or behind post rises out of a man's head (posts at %s, men %s)" % [at, str(post_x), str(body)])
			var k: Vector3 = body["kicker"]
			var d: Vector3 = body["on_the_mark"]
			# The man on the mark is up the ground from the kicker, as a set shot looks from behind
			# the kicker: between him and the goals across the picture, smaller, his boots higher up
			# it, his head clear of the kicker's. (The old scene stood them shoulder to shoulder, a
			# step apart: director, 2026-11-12, "set shot by real distance and angle".)
			var kf: Vector3 = body["kicker|feet"]
			var df: Vector3 = body["on_the_mark|feet"]
			var goal_x: float = cam.oval(goal).x
			_check(minf(k.x, goal_x) < d.x and d.x < maxf(k.x, goal_x),
					"%s: the man on the mark stands between the kicker and the goals (kicker %d, mark %d, goals %d)" % [at, int(k.x), int(d.x), int(goal_x)])
			_check(df.z < kf.z * 0.85 and df.y < kf.y - 4.0, "%s: the man on the mark is smaller and higher up the picture than the kicker" % at)
			_check(absf(d.x - k.x) > k.z + d.z, "%s: the man on the mark's head is clear of the kicker's" % at)
			# How far and how narrow the goals look follows the spot: the posts as tall on screen
			# as the distance makes them, the gap between them as wide as the angle leaves it.
			var gl: Vector3 = cam.oval(Vector2(-0.5 * float(VG.GOAL_GAP), goal.y))
			var gr: Vector3 = cam.oval(Vector2(0.5 * float(VG.GOAL_GAP), goal.y))
			var gap_px := absf(gr.x - gl.x)
			var tall_px: float = absf(cam.oval(goal, float(VG.GOAL_H)).y - cam.oval(goal).y)
			if not _goal_look.has(phone):
				_goal_look[phone] = {}
			_goal_look[phone][key] = Vector2(gap_px, tall_px)

			# The big screen: decided once for the scene, never popping out mid-scene; when it
			# shows, neither the title bar nor a side of the picture cuts it, from the cut-in to
			# the freeze.
			var shown_off: bool = bool(vig.call("_screen_board", cam).get("off", false))
			var end: float = float(vig.get("_end"))
			var cuts := 0
			for i in range(41):
				cuts += 1 if bool(vig.screen_cut_at(end * float(i) / 40.0, 0.0)) else 0
			for j in range(1, 41):
				cuts += 1 if bool(vig.screen_cut_at(end, 0.01 * float(j))) else 0
			_check(shown_off == first_off, "%s: the big screen is the same at the cut-in as on the freeze" % at)
			_check(shown_off == (cuts > 0), "%s: the big screen is left out only when the title bar or a side would cut it (%d frames)" % [at, cuts])
			var sr: Rect2 = VG.screen_rect(cam)
			if not shown_off and sr.has_area():
				_check(sr.position.x >= 0.0 and sr.end.x <= vig.size.x and sr.position.y + sr.size.y * 0.15 >= bar,
						"%s: the big screen shows whole, inside the picture and its writing under the title bar (%s)" % [at, str(sr)])
			var board: Dictionary = vig.get("_board")
			_check(board.get("goals") == m.get("_shown_goals") and board.get("behinds") == m.get("_shown_behinds"),
					"%s: the big screen shows what the scoreboard shows (%s %s, %s %s)" % [at, str(board.get("goals")),
					str(board.get("behinds")), str(m.get("_shown_goals")), str(m.get("_shown_behinds"))])
			m.queue_free()
			await _settle()
	# From 25 out the goals stand taller than from 35, from 35 than from 55; from the pocket the
	# gap between the posts is far narrower for its height than from straight in front.
	for phone in _goal_look:
		var g: Dictionary = _goal_look[phone]
		_check(g.size() == 5, "every spot's goals were measured at %s" % str(phone))
		if g.size() < 5:
			continue
		_check((g["close"] as Vector2).y > (g["front"] as Vector2).y * 1.15 and (g["front"] as Vector2).y > (g["angle"] as Vector2).y * 1.1
				and (g["angle"] as Vector2).y > (g["long"] as Vector2).y * 1.08,
				"at %s the goals look nearer from 25 than 35 than 45 than 55 (%s)" % [str(phone), str(g)])
		_check((g["pocket"] as Vector2).x / (g["pocket"] as Vector2).y < 0.7 * (g["front"] as Vector2).x / (g["front"] as Vector2).y,
				"at %s the goals look narrow from the pocket (%s)" % [str(phone), str(g)])
	# The big screen's place is the ground's: 30 by 13 m, 30 m up, 40 m past the far fence,
	# and nothing when it is behind the camera.
	var c = VG.Cam.new()
	c.f = 500.0
	c.cx = 180.0
	c.hor = 200.0
	var far := Vector2(0.0, float(VG.L) + float(VG.FENCE) + 40.0)
	var p: Vector3 = c.oval(far, 30.0)
	var r: Rect2 = VG.screen_rect(c)
	_check(p.z > 0.0 and r.get_center().is_equal_approx(Vector2(p.x, p.y)) and r.size.is_equal_approx(Vector2(30.0, 13.0) * p.z),
			"The big screen stands 30 by 13 m, 30 m up past the far fence")
	c.fwd = Vector2(0, -1)
	_check(not VG.screen_rect(c).has_area(), "The big screen behind the camera is not drawn")


## Until the scene has frozen, its last punch done, and the call has slid all the way up
## (MatchScene._show_moment's 0.3 s slide); false if that never comes.
func _call_settled(m: Control, vig) -> bool:
	var panel: Control = m.find_child("BounceCall", true, false)
	var margin: Control = panel.get_parent().get_parent() if panel != null else null
	for i in range(60):
		if float(vig.get("_hold")) >= 0.4 and margin != null and margin.get_theme_constant("margin_bottom") == 0:
			await _settle()
			return true
		await create_timer(0.05).timeout
	return false


## Vignettes off: the call is the text card, for every kind.
func _test_card_without_vignettes() -> void:
	for kind in KINDS:
		var ctx := await _match()
		var m: Control = ctx["m"]
		var sim = ctx["sim"]
		var me: int = ctx["me"]
		_state.set_vignettes_on(false)
		sim.moment_side = me
		sim.pending_moment = _moment(sim, me, kind)
		m.call("_show_moment")
		await _settle()
		_check(m.find_child("MomentCard", true, false) != null and m.find_child("DecisionVignette", true, false) == null,
				"%s with vignettes off: the call is the text card" % kind)
		m.queue_free()
		await _settle()
	_state.set_vignettes_on(true)


## A finger on the last choice, after the scene freezes: MatchSim takes the call and the
## match view is back. Every scene shares the one call layout; each is tapped.
func _test_tap(kind: String) -> void:
	var ctx := await _match()
	var m: Control = ctx["m"]
	var sim = ctx["sim"]
	var me: int = ctx["me"]
	_state.set_vignettes_on(true)
	sim.moment_side = me
	sim.pending_moment = _moment(sim, me, kind)
	var last: int = (sim.pending_moment["options"] as Array).size() - 1
	m.call("_show_moment")
	await _settle()
	var card = m.find_child("MomentCard", true, false)
	var vig = m.find_child("DecisionVignette", true, false)
	var b: Button = card.find_child("Moment_%d" % last, true, false) if card != null else null
	_check(vig != null and b != null, "%s tap: the scene and its call are up" % kind)
	if vig == null or b == null:
		m.queue_free()
		return
	vig.finish_now()
	for i in range(30):
		await process_frame
	var asked: int = sim.moments.size()
	var why: String = await Tap.tap(b)
	_check(why == "", "%s tap: a finger on the choice reaches it (%s)" % [kind, why])
	_check(sim.moments.size() == asked + 1 and str((sim.moments[-1] as Dictionary).get("kind", "")) == kind,
			"%s tap: MatchSim takes the call" % kind)
	for i in range(40):
		await process_frame
	_check(m.find_child("DecisionVignette", true, false) == null, "%s tap: the scene is gone, back to the match" % kind)
	m.queue_free()
	await _settle()


## MatchSim sends no defender when it has none: the scene draws nobody on the mark. With
## no tagger, the chaser is a midfielder or nobody; the scene never invents a man.
func _test_no_chosen_defender() -> void:
	var ctx := await _match()
	var m: Control = ctx["m"]
	var sim = ctx["sim"]
	var me: int = ctx["me"]
	var vig = load("res://scripts/ui/match/DecisionVignette.gd").new()
	m.add_child(vig)
	var shot := _moment(sim, me, "set_shot")
	shot["defender_id"] = ""
	vig.setup_decision(sim, me, shot)
	var roles: Array = vig.tokens.map(func(t): return str(t["role"]))
	_check(roles.has("kicker") and not roles.has("on_the_mark"),
			"set_shot with no defender: nobody is drawn on the mark (%s)" % str(roles))
	sim.tactics[me]["tagger_id"] = ""
	vig.setup_decision(sim, me, _moment(sim, me, "hot"))
	var ch: Dictionary = vig.token_of("chaser")
	var ground: Array = sim.squads[me].ground
	var role := ""
	for p in ground:
		if str(p["id"]) == str(ch.get("id", "")):
			role = str(p["role"])
	_check(ch.is_empty() or role == "MID" or str(ch.get("id", "")) == str((sim.tagger_of(me) as Dictionary).get("id", "")),
			"hot with no named tagger: the chaser is a midfielder, not a default man")
	vig.queue_free()
	m.queue_free()
	await _settle()


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
## TODO row T2.42: the first call of a match froze the oval for about 5 s while the
## call scene painted the ground's crowd and loaded its figures on its first frame. The
## opening break now does that work behind itself (MatchScene._warm_call_scene): by the
## time the coach taps Start, the crowd the call will draw is already painted, the warm
## scene is gone, and the match is exactly where it was.
func _test_first_call_warmed() -> void:
	var db = root.get_node("GameDB")
	var crowd = load("res://scripts/ui/match/VignetteCrowd.gd")
	var ground = load("res://scripts/ui/match/VignetteGround.gd")
	_state.set_vignettes_on(true)
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.start_season("MEL", db.club_list("MEL"))
	root.size = Vector2i(390, 844)
	_check(_state.prepare_interactive_match(), "A live match is prepared")
	var sim = _state.pending_sim
	var minute_was: int = sim.current_minute
	var events_was: int = (sim.events as Array).size()
	(crowd._cache as Dictionary).clear()
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await process_frame
	var holder := m.find_child("CallSceneWarm", true, false) as Control
	_check(holder != null and m.find_child("CoachBox", true, false) != null,
			"the opening break warms the call scene behind it")
	_check(holder != null and holder.size == Vector2.ONE and holder.clip_contents
			and holder.mouse_filter == Control.MOUSE_FILTER_IGNORE,
			"the warm scene shows one pixel at most and takes no taps")
	await _settle()
	var colours := [db.club_colours(str(sim.squads[0].code)), db.club_colours(str(sim.squads[1].code))]
	# One crowd all match: the call scenes seat the replay's (StoppageVignette.CROWD).
	var crowd_seed: int = load("res://scripts/ui/match/StoppageVignette.gd").CROWD
	_check(crowd_seed == 11, "the call scenes seat the same crowd as the replay")
	var key := "seats|%s|%d|%s" % [str(colours), crowd_seed, (ground.seat_colour() as Color).to_html()]
	_check((crowd._cache as Dictionary).has(key), "the first call's crowd (home and away colours) is painted at the break")
	if bool((ground.spec as Dictionary).get("hill", false)):
		var hill := "seats|%s|%d|%s" % [str(colours), crowd_seed + 1, (ground.HILL as Color).to_html()]
		_check((crowd._cache as Dictionary).has(hill), "the ground's hill crowd is painted at the break")
	_check(m.find_child("CallSceneWarm", true, false) == null, "the warm scene is gone before play")
	_check(sim.current_minute == minute_was and (sim.events as Array).size() == events_was,
			"warming the call scene changes nothing in the match")
	m.queue_free()
	await _settle()
	# With the Vignettes setting off there is no call scene to warm.
	_state.set_vignettes_on(false)
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.start_season("MEL", db.club_list("MEL"))
	_check(_state.prepare_interactive_match(), "A live match is prepared")
	m = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await process_frame
	_check(m.find_child("CallSceneWarm", true, false) == null, "vignettes off: nothing is warmed")
	m.queue_free()
	await _settle()
	_state.set_vignettes_on(true)


## One of the scenes, alone, at that size: the centre bounce or a call scene.
func _scene(m: Control, sim, me: int, kind: String, size: Vector2):
	var vig
	if kind == "bounce":
		vig = load("res://scripts/ui/match/StoppageVignette.gd").new()
		m.add_child(vig)
		vig.size = size
		vig.setup(sim, me, "A call")
	else:
		vig = load("res://scripts/ui/match/DecisionVignette.gd").new()
		m.add_child(vig)
		vig.size = size
		vig.setup_decision(sim, me, _moment(sim, me, kind))
	return vig


## Director, 2026-11-12 (visual interview, match day): "tighter cameras": at the freeze the
## turf between the far fence and the bottom of the picture is no more than a third of the
## frame, the stand and the crowd fill the top, the men are big, their heads under the title
## bar, no post rising out of a head, every name pinned by its man's head. Measured from the
## scene's own projection (framing), for each call scene and the centre bounce, on a phone
## and a PC, before the call is up and with it up.
func _test_framing(size: Vector2i) -> void:
	var ctx := await _match(true, size)
	var m: Control = ctx["m"]
	var sim = ctx["sim"]
	var me: int = ctx["me"]
	var wide := size.x > size.y
	var scenes: Array = KINDS + ["bounce"]
	_check(scenes.size() == 6, "five call scenes and the centre bounce are measured")
	for kind in scenes:
		var at := "%s at %dx%d" % [kind, size.x, size.y]
		var vig = _scene(m, sim, me, str(kind), Vector2(size))
		vig.finish_now()
		vig.set("_hold", 0.4)
		var up: float = float(size.y) * (0.3 if wide else 0.4)
		for room in [0.0, up]:
			vig.call_room = room
			var f: Dictionary = vig.shot_numbers()
			var tag := "%s, the call %s" % [at, "up" if room > 0.0 else "down"]
			print("FRAMING %s room=%d %s" % [at, int(room), str(f)])
			_check(float(f["grass_of_frame"]) <= 1.0 / 3.0 + 0.005 and float(f["grass_of_frame"]) > 0.03,
					"%s: the turf is a third of the frame or less (%.2f)" % [tag, float(f["grass_of_frame"])])
			_check(float(f["head"]) >= float(f["bar"]) + 20.0, "%s: every head is under the title bar (%.0f, bar %.0f)" % [tag, float(f["head"]), float(f["bar"])])
			_check(float(f["feet"]) <= float(f["floor"]) + 0.5, "%s: every man's boots are above the call (%.0f, call at %.0f)" % [tag, float(f["feet"]), float(f["floor"])])
			_check(float(f["man_px"]) >= float(size.y) * (0.12 if kind in ["bounce", "momentum"] else 0.18),
					"%s: the men are big (%.0f px of %d)" % [tag, float(f["man_px"]), size.y])
			# (A set shot from long range looks the length of the ground: its stand fills the top
			# once the picture has tilted clear of the call.)
			_check((kind == "set_shot" and room <= 0.0) or float(f["stand_top"]) <= float(f["bar"]) + 0.3 * (float(f["floor"]) - float(f["bar"])),
					"%s: the stand fills the top of the picture (its top at %.0f, bar %.0f)" % [tag, float(f["stand_top"]), float(f["bar"])])
			vig.call("_apply_camera", float(vig.call("_freeze_at")), 0.4)
			_check(bool(vig.posts_clear()), "%s: no goal or behind post rises out of a named man's head" % tag)
		# The names, as drawn with the call up: each on the overlay by its own man's head.
		vig.queue_redraw()
		await _settle()
		var tags: Array = vig.tag_log
		var named: Array = vig.call("_named")
		if kind != "momentum":
			_check(not named.is_empty() and tags.size() == named.size(), "%s: each man the call is about has his name (%d of %d)" % [at, tags.size(), named.size()])
		var near := true
		var bar: float = float(size.y) * 0.075
		for t in tags:
			var box: Rect2 = t["box"]
			var head: Vector2 = t["head"]
			# By his head, or (a man in the air, the ball over him) under his boots: touching him.
			var boots: Vector2 = t["feet"]
			var gap := Vector2(maxf(0.0, maxf(box.position.x - head.x, head.x - box.end.x)),
					maxf(0.0, maxf(box.position.y - head.y, minf(head.y, boots.y) - box.end.y))).length()
			if box.position.y >= boots.y:
				gap = Vector2(maxf(0.0, maxf(box.position.x - boots.x, boots.x - box.end.x)), box.position.y - boots.y).length()
			near = near and gap <= float(size.y) * 0.12 and box.position.y >= bar and box.end.y <= float(size.y) - up + 0.5 \
					and box.position.x >= 0.0 and box.end.x <= float(size.x)
		_check(near, "%s: every name sits by its man's head, under the title bar and above the call (%s)" % [at, str(tags)])
		_check(vig.get("_ui") != vig, "%s: the names and bars draw on the overlay above the grade" % at)
		vig.queue_free()
		await _settle()
	m.queue_free()
	await _settle()


## Director, 2026-11-12: "full sides, umpires and crowd" and "figures that move while the
## coach decides". The rest of both sides and the umpires stand round every call scene
## (VignetteExtras) as real players of this match, never among the men the call is about;
## after the freeze the scene's clock runs on, so a standing man's frame changes; with
## Settings > Reduced motion it holds still. The duel and the centre bounce freeze with men
## and the ball in the air, and stay held.
func _test_cast_and_idle() -> void:
	var ctx := await _match()
	var m: Control = ctx["m"]
	var sim = ctx["sim"]
	var me: int = ctx["me"]
	var db = root.get_node("GameDB")
	var ids := {}
	var side_of := {}
	for side in range(2):
		for p in sim.squads[side].ground:
			ids[str(p["id"])] = p
			side_of[str(p["id"])] = side
	var was_reduced: bool = bool(_state.reduced_motion())
	# Everyone on the ground has a place, the same every time it is asked, and the match's
	# own random numbers are not touched.
	var X = load("res://scripts/ui/match/VignetteExtras.gd")
	var rng_was: int = sim.rng.state
	var all: Array = X.players(sim, me, [], Vector2(10.0, 30.0), false)
	var again: Array = X.players(sim, me, [], Vector2(10.0, 30.0), false)
	_check(all.size() == ids.size() and all.size() >= 30 and str(all) == str(again) and sim.rng.state == rng_was,
			"both sides in full have a place on the ground, the same each time, the match untouched (%d men)" % all.size())
	var inside := true
	var spread := {}
	for e in all:
		var at: Vector2 = e["oval"]
		inside = inside and pow(at.x / 68.0, 2.0) + pow(at.y / 80.0, 2.0) <= 1.0
		spread[Vector2i(at / 2.0)] = true
	_check(inside and spread.size() >= all.size() - 4, "every man stands inside the boundary, in a spot of his own")
	var officials: Array = X.umpires(Vector2(10.0, 30.0))
	var count := {}
	for e in officials:
		count[str(e["ump"])] = int(count.get(str(e["ump"]), 0)) + 1
	_check(count == {"field": 3, "boundary": 2, "goal": 2}, "three field, two boundary and two goal umpires (%s)" % str(count))
	for kind in KINDS + ["bounce"]:
		var vig = _scene(m, sim, me, str(kind), Vector2(360, 740))
		var cast: Array = vig.get("_cast")
		var own := {}
		for t in vig.tokens:
			own[str(t["id"])] = true
		var players := 0
		var umps := {}
		var real := true
		var apart := true
		for e in cast:
			if e.has("ump"):
				umps[str(e["ump"])] = true
				continue
			players += 1
			var id := str(e["id"])
			real = real and ids.has(id) and e["look"] == db.figure_look(ids.get(id, {}), false) and int(e["side"]) == int(side_of.get(id, -1))
			apart = apart and not own.has(id)
		# A long lens on two men shows few others; the centre of the ground shows most of both sides.
		_check(players >= (8 if kind in ["bounce", "momentum"] else 0) and real and not cast.is_empty(),
				"%s: the rest of both sides stand round the scene, each a real player in his own look (%d in the shot)" % [kind, players])
		_check(apart and not vig.tokens.any(func(t): return t.has("extra")), "%s: none of them is counted among the men the call is about" % kind)
		_check(not umps.is_empty(), "%s: the umpires are on the ground (%s)" % [kind, str(umps.keys())])
		# After the freeze the clock runs on.
		_state.set_reduced_motion(false)
		vig.finish_now()
		vig.set("_hold", 0.4)
		var c0: float = vig.clock()
		vig.call("_process", 0.5)
		vig.call("_process", 0.5)
		var moved: bool = float(vig.clock()) > c0 + 0.9
		var held: bool = kind in ["duel", "bounce"]
		_check(moved != held, "%s: %s" % [kind, "frozen in the air, the scene holds" if held else "the scene keeps moving while the coach decides"])
		if moved:
			var changed := false
			var before := []
			for t in vig.tokens:
				before.append(vig.call("_frame", t, vig.call("_lift", t), vig.call("_pos", t), bool(t["mine"])))
			for step in range(8):
				vig.call("_process", 0.11)
				for i in range(vig.tokens.size()):
					var t: Dictionary = vig.tokens[i]
					changed = changed or vig.call("_frame", t, vig.call("_lift", t), vig.call("_pos", t), bool(t["mine"])) != before[i]
			_check(changed, "%s: a standing man shifts his weight after the freeze" % kind)
			var looped := true
			for t in vig.tokens:
				var pick: Array = vig.call("_frame", t, vig.call("_lift", t), vig.call("_pos", t), bool(t["mine"]))
				looped = looped and not (str(pick[0]) in ["idle", "celebrate"])
			_check(looped, "%s: nobody stands on a single held frame" % kind)
			# Reduced motion: held.
			_state.set_reduced_motion(true)
			var c1: float = vig.clock()
			vig.call("_process", 0.5)
			_check(is_equal_approx(float(vig.clock()), c1), "%s: reduced motion holds the frame still" % kind)
		vig.queue_free()
	_state.set_reduced_motion(was_reduced)
	m.queue_free()
	await _settle()


## A kick drifts in the wind and still lands where the match says: no drift at the boot or
## where it lands, most in the middle, none on a calm day.
func _test_wind_drift() -> void:
	var X = load("res://scripts/ui/match/VignetteExtras.gd")
	var W = load("res://scripts/ui/match/VignetteWeather.gd")
	_check(is_zero_approx(float(X.drift(0.0, 1.0))) and is_zero_approx(float(X.drift(1.0, 1.0))) and is_zero_approx(float(X.drift(1.4, 1.0))),
			"the wind moves the ball nothing at the boot and nothing where it lands")
	_check(float(X.drift(0.5, 1.0)) > 1.5 and float(X.drift(0.5, 1.0)) < 4.0 and float(X.drift(0.25, 1.0)) < float(X.drift(0.5, 1.0)),
			"mid-flight it drifts a couple of metres")
	_check(is_zero_approx(float(X.drift(0.5, float(W.wind(""))))), "a calm day: no drift")
	var B = load("res://scripts/ui/match/BroadcastVignette.gd").new()
	B.weather = str(W.WINDY)
	var a := Vector3(0.0, 30.0, 0.6)
	var b := Vector3(2.0, 79.0, 3.0)
	var d0: Vector3 = B.call("_drifted", a, a, b, 0.0)
	var d1: Vector3 = B.call("_drifted", b, a, b, 1.0)
	var mid: Vector3 = B.call("_drifted", a.lerp(b, 0.5), a, b, 0.5)
	_check(d0.is_equal_approx(a) and d1.is_equal_approx(b), "the replay's kick leaves the boot and lands where the match says in the wind")
	_check(Vector2(mid.x, mid.y).distance_to(Vector2(1.0, 54.5)) > 1.5 and is_equal_approx(mid.z, a.lerp(b, 0.5).z),
			"...and bends across its line in between, no higher or lower")
	B.weather = ""
	_check((B.call("_drifted", a.lerp(b, 0.5), a, b, 0.5) as Vector3).is_equal_approx(a.lerp(b, 0.5)), "a calm day: the kick flies straight")
	B.free()


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle() -> void:
	for i in range(6):
		await process_frame


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)
