extends RefCounted
## Run by tests/run_picture_truth_tests.gd.
## T8.85 (P-76): the picture and the truth never disagree. One seeded match is
## played start to finish through the real match screen on a phone, at 8x, and
## at every tick it draws five things are checked:
##   1. no disc moves faster than a footballer runs, and none jumps;
##   2. the ball is with a player or on its way, never hanging in the air,
##      and never crossing the ground faster than a kick;
##   3. there are 36 discs, 18 a side, all on the ground and on the screen;
##   4. the feed, the scoreboard and the match's own score agree;
##   5. every figure drawn comes from its intended sheet, never a fallback.
## The other motion suites cap speed at 1x and 4x and watch jumps for a quarter;
## this one is the whole match at the fastest speed the coach can pick.

const SUITE_SEED := 2027
const CLUB := "FRE"
const PHONE := Vector2i(390, 844)
## A phone under load draws 30 frames a second: the biggest step a disc takes.
const FRAME := 1.0 / 30.0
const SPEED := 8.0
const SV := preload("res://scripts/ui/match/StoppageVignette.gd")
const BV := preload("res://scripts/ui/match/BroadcastVignette.gd")
const DV := preload("res://scripts/ui/match/DecisionVignette.gd")
const Truth := preload("res://tests/picture_truth.gd")

var _tree: SceneTree
var root: Window
var _state: Node
var _db: Node
var checks := 0
var failures: Array[String] = []
var _said := {}            # check name -> failures printed (the first few of each)
var _stats := {}

# What the last tick drew, to measure this one against.
var _prev_tok := PackedVector2Array()
var _prev_disc := PackedVector2Array()
var _prev_ball := {}
var _prev_period := -1
var _still := 0.0          # match seconds the ball has lain still out of hands
var _context := "start"
var _prev_w2s := PackedVector2Array()   # the discs' own places, before any nudge
var _prev_scale := 0.0
var _prev_size := Vector2.ZERO          # the ground's part of the screen

# The score, counted here from the events the screen has played.
var _goals := [0, 0]
var _behinds := [0, 0]
var _events := 0
var _scores := 0
var _m: Control
var _vignettes := {}       # instance id -> true, each scene checked once


## `tree` is the running SceneTree (the runner's own).
func run(tree: SceneTree) -> void:
	_tree = tree
	root = tree.root
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	# The first match a device watches adds a line under the momentum meter, and
	# the ground gives up 21 px to it in one frame. The setting is saved, so only
	# a run on a clean machine (CI) saw it: disc 12 "moved" 8.40 m at tick 237.
	_state.set_setting("seen_momentum_intro", true)
	_t("_test_the_measures_catch_a_fault")
	await _t("_test_a_full_match_at_8x")
	print(Ran.line("Picture truth", self))


# ---------------------------------------------------------------------------
# The measures themselves: each one goes red on a made-up fault
# ---------------------------------------------------------------------------
func _test_the_measures_catch_a_fault() -> void:
	var h := FRAME * SPEED * MatchDirector.TEMPO
	var a := PackedVector2Array([Vector2(0, 0), Vector2(10, 0)])
	var run := PackedVector2Array([Vector2(MatchMotion.SPRINT * h, 0), Vector2(10, 0)])
	var jump := PackedVector2Array([Vector2(0, 0), Vector2(10, MatchMotion.SPRINT * h * 1.2)])
	_check(Truth.speed_fault(a, run, 1.0, MatchMotion.SPRINT * h) == "", "A disc at a flat sprint passes")
	_check(Truth.speed_fault(a, jump, 1.0, MatchMotion.SPRINT * h) != "", "A disc a fifth faster than a sprint is caught")
	_check(Truth.speed_fault(a, PackedVector2Array([Vector2.ZERO]), 1.0, 1.0) != "", "A disc that vanishes between frames is caught")

	var toks := _made_tokens()
	var held := {"mode": "held", "holder": 3, "pos": (toks[3]["pos"] as Vector2) + Vector2(0.6, 0), "h": 1.0}
	_check(Truth.ball_fault(held, held, toks, h, 0.0) == "", "A ball in a player's hands passes")
	var away := held.duplicate()
	away["pos"] = (toks[3]["pos"] as Vector2) + Vector2(4.0, 0)
	_check(Truth.ball_fault(away, held, toks, h, 0.0) != "", "A held ball four metres from its holder is caught")
	var nobody := held.duplicate()
	nobody["holder"] = 99
	_check(Truth.ball_fault(nobody, held, toks, h, 0.0) != "", "A ball held by nobody is caught")
	var hang := {"mode": "dead", "holder": -1, "pos": Vector2(20, 5), "h": 3.0}
	_check(Truth.ball_fault(hang, hang, toks, h, 0.0) != "", "A ball hanging three metres up, still, is caught")
	var fall := hang.duplicate()
	fall["h"] = 1.5
	_check(Truth.ball_fault(fall, hang, toks, h, 0.0) == "", "A ball dropping to the ground passes")
	var fly := {"mode": "flight", "holder": -1, "pos": Vector2(30, 5), "h": 6.0}
	_check(Truth.ball_fault(fly, hang, toks, h, 0.0) == "", "A ball in flight passes")
	var ground := {"mode": "dead", "holder": -1, "pos": Vector2(20, 5), "h": 0.0}
	_check(Truth.ball_fault(ground, ground, toks, h, 1.0) == "", "A ball on the ground for a second passes")
	_check(Truth.ball_fault(ground, ground, toks, h, Truth.LYING_LIMIT + 1.0) != "", "A ball nobody goes to is caught")
	var far := fly.duplicate()
	far["pos"] = Vector2(20.0 + Truth.KICK_SPEED * h, 5)
	_check(Truth.ball_speed_fault(far, hang, h) == "", "A ball at the hardest kick's speed passes")
	far["pos"] = Vector2(20.0 + 42.0, 5)
	_check(Truth.ball_speed_fault(far, hang, h) != "", "A ball that crosses 42 metres in a tick is caught")
	_check(Truth.ball_speed_fault(far, {}, h) == "", "The first frame's ball has nothing to be measured against")
	var out := fly.duplicate()
	out["pos"] = Vector2(MatchMotion.HALF_LEN + 30.0, 0)
	_check(Truth.ball_fault(out, fly, toks, h, 0.0) != "", "A ball thirty metres over the fence is caught")
	var nan := fly.duplicate()
	nan["pos"] = Vector2(NAN, 0)
	_check(Truth.ball_fault(nan, fly, toks, h, 0.0) != "", "A ball with no place is caught")

	var discs := PackedVector2Array()
	for t in toks:
		discs.append((t["pos"] as Vector2) + Vector2(150, 200))
	var view := Rect2(0, 0, 390, 500)
	_check(Truth.disc_fault(toks, discs, range(36), view, 9.0) == "", "Thirty-six discs on the screen pass")
	_check(Truth.disc_fault(toks.slice(0, 35), discs.slice(0, 35), range(35), view, 9.0) != "", "Thirty-five discs are caught")
	var lopsided := toks.duplicate(true)
	lopsided[0]["side"] = 1
	_check(Truth.disc_fault(lopsided, discs, range(36), view, 9.0) != "", "Seventeen against nineteen is caught")
	var off := discs.duplicate()
	off[5] = Vector2(-80, 40)
	_check(Truth.disc_fault(toks, off, range(36), view, 9.0) != "", "A disc off the screen is caught")
	var twice := range(36)
	twice[4] = 5
	_check(Truth.disc_fault(toks, discs, twice, view, 9.0) != "", "A disc drawn twice and one not at all is caught")
	var twins := toks.duplicate(true)
	twins[1]["num"] = twins[0]["num"]
	_check(Truth.disc_fault(twins, discs, range(36), view, 9.0) != "", "Two men in the same number are caught")

	_check(Truth.score_fault([3, 2], [4, 1], [3, 2], [4, 1], "3.4 (22)", "2.1 (13)") == "", "A score that agrees passes")
	_check(Truth.score_fault([3, 2], [4, 1], [3, 2], [4, 1], "3.3 (21)", "2.1 (13)") != "", "A scoreboard a point short is caught")
	_check(Truth.score_fault([3, 2], [4, 1], [3, 3], [4, 1], "3.4 (22)", "2.1 (13)") != "", "A match a goal ahead of the feed is caught")
	_check(Truth.goal_row_fault("Q2 4'  ·  FRE 3.4 (22)  SYD 2.1 (13)", [3, 2], [4, 1]) == "", "A goal line with the score passes")
	_check(Truth.goal_row_fault("Q2 4'  ·  FRE 2.4 (16)  SYD 2.1 (13)", [3, 2], [4, 1]) != "", "A goal line a goal short is caught")

	var idle := VignetteFigures.strip("average", "idle", "front")
	var good := {"anim": "idle", "facing": "front", "frames": int(idle["frames"]), "wanted": 0, "info": idle}
	_check(Truth.frame_fault(good) == "", "A frame from its own strip passes")
	var past := good.duplicate()
	past["wanted"] = int(idle["frames"])
	_check(Truth.frame_fault(past) != "", "A frame past the end of its move is caught")
	var other := good.duplicate()
	other["anim"] = "jog"
	other["facing"] = "side_l"
	_check(Truth.frame_fault(other) != "", "A move drawn from another move's strip is caught")
	var none := good.duplicate()
	none["anim"] = "moonwalk"
	_check(Truth.frame_fault(none) != "", "A move the sheet does not hold is caught")
	_check(Truth.slot_fault({"anim": "jog", "facing": "side_l", "fallback": false,
			"info": VignetteFigures.strip("average", "jog", "side_l"), "frame": 0}) == "", "A figure in its own move passes")
	_check(Truth.slot_fault({"anim": "idle", "facing": "front", "fallback": true,
			"info": idle, "frame": 0}) != "", "A figure standing in for a missing move is caught")
	_check(Truth.kit_fault("FRE", {"design": "plain"}, "chevrons", _db.GUERNSEY_DESIGNS) != "", "A plain guernsey on a club with a design is caught")
	_check(Truth.kit_fault("FRE", {"design": "tartan"}, "tartan", _db.GUERNSEY_DESIGNS) != "", "A design the sheet does not hold is caught")


func _made_tokens() -> Array:
	var out := []
	for i in range(36):
		out.append({"id": i, "side": 0 if i < 18 else 1, "num": 1 + (i % 18), "pid": "p%d" % i,
				"pos": Vector2(-60.0 + 7.0 * (i % 18), -20.0 if i < 18 else 20.0), "vel": Vector2.ZERO})
	return out


# ---------------------------------------------------------------------------
# One match, every tick
# ---------------------------------------------------------------------------
## The game caps itself at 60 frames a second and sleeps between frames
## (project.godot), so every awaited frame here cost a sixtieth of a second
## of waiting. The ticks drive the picture themselves (FRAME each, the pitch's
## own processing off), so the cap only slowed the watching: it is lifted for
## this match and put back after.
func _test_a_full_match_at_8x() -> void:
	var fps := Engine.max_fps
	var low := OS.low_processor_usage_mode
	Engine.max_fps = 0
	OS.low_processor_usage_mode = false
	await _watch_a_full_match()
	Engine.max_fps = fps
	OS.low_processor_usage_mode = low


func _watch_a_full_match() -> void:
	_state.set_vignettes_on(true)
	_state.set_bounce_scene_every_match(true)
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.start_season(CLUB, _db.club_list(CLUB))
	root.size = PHONE
	_state.set_match_way("watch")
	_check(_state.prepare_interactive_match(), "A live match is prepared")
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	_m = m
	root.add_child(m)
	await _settle()
	var pitch = m.get("_pitch")
	_check(pitch != null, "The match screen has its ground")
	if pitch == null:
		return
	# Only this suite's ticks move the picture, each one a thirtieth of a second.
	pitch.process_mode = Node.PROCESS_MODE_DISABLED
	pitch.event_played.connect(_on_event)
	m.call("_on_speed", SPEED)
	_check(is_equal_approx(float(pitch.speed), SPEED), "The match plays at 8x (%.2f)" % float(pitch.speed))
	_check(bool(pitch.upright) and not bool(pitch.camera_enabled),
			"The phone's ground stands upright and still (the drawn speed is the discs' own)")
	_check_kits(pitch, m)
	SV.log_frames = true

	var at_break := 0
	var guard := 0
	var ticks := 0
	while not bool(m.get("_fulltime_shown")) and guard < 400000:
		guard += 1
		var box: Node = m.find_child("CoachBox", true, false)
		if box != null:
			await _check_scenes(m)
			if at_break > 0:
				_check_engine(m, "the break after quarter %d" % at_break)
			var start: Button = box.find_child("StartQuarter", true, false)
			_check(start != null, "The break can be left (%d)" % at_break)
			if start == null:
				break
			start.emit_signal("pressed")
			await _settle()
			at_break += 1
			_context = "after the break"
			continue
		var card: Node = m.find_child("MomentCard", true, false)
		if card != null:
			await _check_scenes(m)
			var pick: Button = card.find_child("Moment_0", true, false)
			if pick != null and not pick.disabled and pick.is_visible_in_tree():
				pick.emit_signal("pressed")
				await _settle()
				_context = "after a call"
				continue
		var replay: Node = m.find_child("BroadcastVignetteOverlay", true, false)
		if replay != null:
			await _check_scenes(m)
			m.call("_finish_broadcast")
			await _settle()
			_context = "after a replay"
			continue
		if pitch.playing:
			_tick(pitch, m)
			ticks += 1
		await _tree.process_frame
	SV.log_frames = false
	_check(bool(m.get("_fulltime_shown")), "The match reaches full time (%d ticks)" % ticks)
	await _settle()
	_check_engine(m, "full time")
	_check(at_break == 4, "All four quarters were played (%d breaks left)" % at_break)
	_check(ticks > 600, "The match was watched tick by tick (%d ticks)" % ticks)
	_check(_scores >= 20, "The match had its scores (%d scoring events, %d events)" % [_scores, _events])
	_check(int(_stats.get("scenes", 0)) >= 2, "Scenes were drawn and checked (%d)" % int(_stats.get("scenes", 0)))
	_check(int(_stats.get("held", 0)) > 100 and int(_stats.get("flight", 0)) > 100,
			"The ball was seen in hands and in flight (%s)" % str(_stats))
	print("Picture truth measured: %s" % str(_stats))
	m.queue_free()
	await _settle()


## One tick of the picture: move it a thirtieth of a second at 8x, then check it.
func _tick(pitch, m: Control) -> void:
	var period_before := int(pitch.period)
	pitch._process(FRAME)
	var d: MatchDirector = pitch.director
	var h := FRAME * float(pitch.speed) * MatchDirector.TEMPO
	_ok("speed set", is_equal_approx(float(pitch.speed), SPEED), "The match is still at 8x (%.2f)" % float(pitch.speed))

	# 1. Nobody outruns a footballer, on the ground or on the screen.
	var tok := PackedVector2Array()
	for t in d.tokens:
		tok.append(t["pos"])
	var disc: PackedVector2Array = pitch.disc_positions().duplicate()
	var scale := float(pitch._scale())
	if _prev_tok.size() > 0:
		var fault := Truth.speed_fault(_prev_tok, tok, 1.0, MatchMotion.SPRINT * h)
		_peak("tok_ratio", Truth.fastest(_prev_tok, tok) / (MatchMotion.SPRINT * h))
		_ok("player speed", fault == "", "No player moves faster than a sprint (%s; %s)" % [fault, _where(d)])
		if int(pitch.period) == period_before and _prev_period == period_before:
			fault = Truth.speed_fault(_prev_disc, disc, scale, (MatchMotion.SPRINT + MatchMotion.WALK) * h)
			_peak("disc_ratio", Truth.fastest(_prev_disc, disc) / scale / ((MatchMotion.SPRINT + MatchMotion.WALK) * h))
			if fault != "":
				fault += "; " + _disc_detail(pitch, tok, disc, scale)
			_ok("disc speed", fault == "", "No disc moves faster than a footballer or jumps (%s; %s)" % [fault, _where(d)])
		else:
			_count("flip frames")

	var view := Rect2(Vector2.ZERO, pitch.size)
	# 2. The ball is with a player or on its way.
	var ball: Dictionary = d.ball.duplicate()
	if not _prev_ball.is_empty() and Truth.lying(ball, _prev_ball):
		_still += h
	else:
		_still = 0.0
	_peak("lying_secs", _still)
	_count(str(ball.get("mode", "?")))
	# The ball never crosses the ground faster than a kick (a free kick's ball
	# once flew any distance to the mark in 0.4 s: 52 m in one tick at 8x).
	var bs := Truth.ball_speed_fault(ball, _prev_ball, h)
	if not _prev_ball.is_empty():
		_peak("ball_ratio", (ball["pos"] as Vector2).distance_to(_prev_ball["pos"]) / (Truth.KICK_SPEED * h))
	_ok("ball speed", bs == "", "The ball moves no faster than a kick (%s; %s)" % [bs, _where(d)])
	_prev_w2s = PackedVector2Array()
	for t in d.tokens:
		_prev_w2s.append(pitch._w2s(t["pos"]))
	_prev_scale = scale
	_prev_size = pitch.size
	var bf := Truth.ball_fault(ball, _prev_ball, d.tokens, h, _still)
	_ok("ball", bf == "", "The ball is with a player or on its way (%s; %s)" % [bf, _where(d)])
	var at: Vector2 = pitch.ball_point()
	_ok("ball drawn", view.grow(2.0).has_point(at), "The ball is drawn on the ground's part of the screen (%s in %s)" % [str(at), str(view)])
	if str(ball.get("mode", "")) == "held":
		var holder := int(ball.get("holder", -1))
		if holder >= 0 and holder < disc.size():
			var gap := at.distance_to(disc[holder])
			_peak("held_px", gap)
			_ok("ball in hands", gap <= Truth.HELD_REACH * scale + 0.5,
					"A held ball is drawn at its holder's disc (%.1f px off; %s)" % [gap, _where(d)])

	# 3. Thirty-six discs, 18 a side, on the screen.
	var df := Truth.disc_fault(d.tokens, disc, pitch.draw_order(), view, float(pitch.token_radius()))
	_ok("discs", df == "", "36 discs, 18 a side, all on the screen (%s; %s)" % [df, _where(d)])

	# 4. The scoreboard shows the score the events have told.
	_check_score(m, {}, "tick")

	# 5. The figures near the ball come from their own moves.
	for s in pitch._figure_slots(float(pitch.token_radius())):
		var sf := Truth.slot_fault(s)
		_ok("figures", sf == "", "A figure on the ground is drawn from its own move (%s)" % sf)
		_count("figure slots")

	_prev_tok = tok
	_prev_disc = disc
	_prev_ball = ball
	_prev_period = int(pitch.period)
	_context = "play"
	_count("ticks")


## Every event the screen plays: count the score, and hold the scoreboard, the
## feed and the match's own running score to it.
func _on_event(ev: Dictionary) -> void:
	_events += 1
	var kind := str(ev.get("kind", ""))
	var side := int(ev.get("side", 0))
	if kind == "goal":
		_goals[side] += 1
		_scores += 1
	elif kind == "behind":
		_behinds[side] += 1
		_scores += 1
	_check_score(_m, ev, "the %s at event %d" % [kind, _events])
	if kind == "goal":
		var feed: Node = _m.get("_feed")
		var row: Node = null
		if feed != null:
			for c in feed.get_children():
				if str(c.get_meta("feed_kind", "")) == "goal" and not c.is_queued_for_deletion():
					row = c
		_ok("goal line", row != null, "A goal puts its line in the feed (event %d)" % _events)
		if row != null:
			var gf := Truth.goal_row_fault(Truth.text_of(row), _goals, _behinds)
			_ok("goal line score", gf == "", "The feed's goal line carries the score (%s)" % gf)


func _check_score(m: Control, ev: Dictionary, when: String) -> void:
	var home: Label = m.get("_score_home")
	var away: Label = m.get("_score_away")
	if home == null or away == null:
		_ok("scoreboard", false, "The scoreboard exists (%s)" % when)
		return
	var eg: Array = ev.get("goals", _goals)
	var eb: Array = ev.get("behinds", _behinds)
	var f := Truth.score_fault(_goals, _behinds, eg, eb, home.text, away.text)
	_ok("score", f == "", "The feed, the scoreboard and the match agree at %s (%s)" % [when, f])
	_ok("score shown", home.is_visible_in_tree() and away.is_visible_in_tree(), "A score is on the screen at %s" % when)


## The match's own score against what the screen has told, at a break.
func _check_engine(m: Control, when: String) -> void:
	var sim = _state.pending_sim
	if sim == null:
		var res: Dictionary = m.get("_res")
		var g: Array = res.get("goals", [])
		var b: Array = res.get("behinds", [])
		_check(g.size() == 2 and b.size() == 2, "The finished match has its score (%s)" % when)
		if g.size() == 2 and b.size() == 2:
			_check(Truth.score_fault(_goals, _behinds, g, b, (m.get("_score_home") as Label).text,
					(m.get("_score_away") as Label).text) == "",
					"The result, the scoreboard and the feed agree at %s (%s %s against %s %s)" % [when, str(g), str(b), str(_goals), str(_behinds)])
		return
	var eg := [int(sim.goals(0)), int(sim.goals(1))]
	var eb := [int(sim.behinds(0)), int(sim.behinds(1))]
	var f := Truth.score_fault(_goals, _behinds, eg, eb, (m.get("_score_home") as Label).text, (m.get("_score_away") as Label).text)
	_check(f == "", "The match engine, the scoreboard and the feed agree at %s (%s)" % [when, f])
	_check(int(sim.score(0)) == _goals[0] * 6 + _behinds[0] and int(sim.score(1)) == _goals[1] * 6 + _behinds[1],
			"The engine's points are the feed's at %s" % when)


## The discs' guernseys are each club's own design, and the figure sheets are
## the real ones at their real size.
func _check_kits(pitch, m: Control) -> void:
	var res: Dictionary = m.get("_res")
	var codes := [str(res.get("home", "")), str(res.get("away", ""))]
	var kits: Array = pitch.get("_kits")
	_check(kits.size() == 2, "Both sides are dressed")
	for side in range(mini(2, kits.size())):
		var declared := str(_db.clubs.get(codes[side], {}).get("guernsey", "")).split(":")[0]
		var kf := Truth.kit_fault(codes[side], kits[side], declared, _db.GUERNSEY_DESIGNS)
		_check(kf == "", "%s's discs wear the club's own guernsey (%s)" % [codes[side], kf])
	var sheet := Vector2i(VignetteFigures.SHEET_SIZE)
	_check(Vector2i(SV.FIGURE_SHADE.get_size()) == sheet and Vector2i(SV.FIGURE_MASK.get_size()) == sheet,
			"The figure sheet loaded at its own size (%s, %s)" % [str(SV.FIGURE_SHADE.get_size()), str(sheet)])


## Each scene on the screen (the bounce, a call's scene, a replay), once, on its
## first frames: drawn from the figure sheet, in both clubs' guernseys, every
## figure from the move it asked for.
func _check_scenes(m: Control) -> void:
	var found := []
	for n in m.find_children("*", "Control", true, false):
		var s = n.get_script()
		if (s == SV or s == BV or s == DV) and not _vignettes.has(n.get_instance_id()):
			found.append(n)
	for n in found:
		_vignettes[n.get_instance_id()] = true
		SV.frame_log.clear()
		SV.hair_log.clear()
		(n as Control).queue_redraw()
		await _tree.process_frame
		await _tree.process_frame
		if not is_instance_valid(n):
			continue
		var what := "%s %s" % [str(n.name), str(n.get("kind")) if n.get("kind") != null else ""]
		_count("scenes")
		_count("scene " + what.strip_edges())
		var mat := (n as Control).material as ShaderMaterial
		_check(mat != null and mat.shader == SV.FIGURE_SHADER and mat.get_shader_parameter("mask_tex") == SV.FIGURE_MASK
				and mat.get_shader_parameter("design_tex") == SV.FIGURE_DESIGN,
				"The %s draws from the figure sheet" % what)
		var kits = n.get("_kits")
		var res: Dictionary = m.get("_res")
		var codes := [str(res.get("home", "")), str(res.get("away", ""))]
		_check(kits is Array and (kits as Array).size() >= 2, "The %s dresses both sides" % what)
		if kits is Array and (kits as Array).size() >= 2:
			for side in range(2):
				var declared := str(_db.clubs.get(codes[side], {}).get("guernsey", "")).split(":")[0]
				var kf := Truth.kit_fault(codes[side], kits[side], declared, _db.GUERNSEY_DESIGNS)
				_check(kf == "", "The %s has %s in the club's own guernsey (%s)" % [what, codes[side], kf])
		if n.get_script() == BV and str(n.get("kind")) == BV.SPECCY_FRONT:
			_check(BV._sf_ready(), "The front-on speccy plays its own shot, not the earlier one")
		var log: Array = SV.frame_log.duplicate()
		_peak("scene frames", float(log.size()))
		_check(not log.is_empty(), "The %s draws its footballers on its first frames" % what)
		var bad := []
		for e in log:
			var ff := Truth.frame_fault(e)
			if ff != "":
				bad.append(ff)
		_check(bad.is_empty(), "Every figure in the %s comes from its intended strip: %s" % [what, str(bad.slice(0, 3))])
		var looks: Array = VignetteFigures.HAIR_TEXTURES + VignetteLooks.LOOK_TEXTURES
		var stray := SV.hair_log.filter(func(e): return not looks.has(e["texture"]))
		_check(stray.is_empty(), "The %s draws hair from the hair sheets (%d strays)" % [what, stray.size()])


## What made a disc's step: his own run, the nudge clear of another disc, or
## the ground itself changing size on the screen.
func _disc_detail(pitch, tok: PackedVector2Array, disc: PackedVector2Array, scale: float) -> String:
	for i in range(mini(disc.size(), _prev_w2s.size())):
		var step := _prev_disc[i].distance_to(disc[i]) / scale
		if step > (MatchMotion.SPRINT + MatchMotion.WALK) * FRAME * SPEED * MatchDirector.TEMPO * 1.001:
			var before: Vector2 = _prev_disc[i] - _prev_w2s[i]
			var after: Vector2 = disc[i] - pitch._w2s(tok[i])
			return "disc %d: he ran %.2f m, the nudge moved %.2f m, the ground was %.3f px a metre in %s and is %.3f in %s" % [i,
					_prev_tok[i].distance_to(tok[i]), before.distance_to(after) / scale, _prev_scale, str(_prev_size),
					scale, str(pitch.size)]
	return ""


func _where(d: MatchDirector) -> String:
	return "%s, %s, tick %d, event %d" % [_context, str(d.mode), int(_stats.get("ticks", 0)), _events]


func _count(key: String) -> void:
	_stats[key] = int(_stats.get(key, 0)) + 1


func _peak(key: String, v: float) -> void:
	if v > float(_stats.get(key, -1.0)):
		_stats[key] = snappedf(v, 0.001)


func _settle() -> void:
	for i in range(6):
		await _tree.process_frame


## A check made every tick: each one counts, and the first few failures of a
## kind are printed (a fault that lasts a quarter would print thousands).
func _ok(kind: String, condition: bool, message: String) -> void:
	checks += 1
	if condition:
		return
	var n := int(_said.get(kind, 0)) + 1
	_said[kind] = n
	if n <= 5:
		failures.append(message)
		push_error(message)
	elif n == 6:
		push_error("More failures of '%s' follow; only the first five are printed" % kind)


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
