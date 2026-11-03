extends SceneTree
## godot --headless --path . --script tests/run_decision_scenes_tests.gd
## TODO row 13: tired, duel, hot, momentum and set shot each open on a scene (DecisionVignette)
## when Features "decision_scenes" and the Vignettes setting are on, and stay the text card
## otherwise. The scene shows the players the call is about, in their own kits and builds,
## with the ball only ever at a palm; the call under it is MatchSim's, and takes a real tap.

const Tap := preload("res://tests/tap.gd")
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
	var original: bool = Features.on("decision_scenes")
	_check(not original, "The decision scenes ship switched off")
	for kind in KINDS:
		await _test_kind(kind)
	await _test_card_without_switch()
	await _test_tap()
	Features.set_on("decision_scenes", original)
	print("Decision scenes tests: %d checks, %d failures" % [_checks, _failures.size()])
	for f in _failures:
		print("  FAIL: ", f)
	quit(1 if _failures.size() > 0 else 0)


## A live match, one quarter in, and the screen showing it.
func _match() -> Dictionary:
	var db = root.get_node("GameDB")
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.start_season("COL", db.club_list("COL"))
	root.size = Vector2i(360, 740)
	_check(_state.prepare_interactive_match(), "A live match is prepared")
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _settle()
	(m.find_child("StartQuarter", true, false) as Button).emit_signal("pressed")
	await _settle()
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
	var m := {"kind": kind, "title": "A call", "text": "Make it.", "options": opts, "q": 2, "min": 50,
			"default": 2}
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
	Features.set_on("decision_scenes", true)
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
	_check(off.is_empty() and card.find_children("Moment_*", "Button", true, false).size() == 3,
			"%s: every option is on screen and thumb-sized (%s)" % [kind, str(off)])
	var said := " ".join(vig.facts)
	_check(not said.contains("%") and not said.to_lower().contains("recommend"), "%s: no stats or advice over the scene" % kind)
	m.queue_free()
	await _settle()


## Switch off, or Vignettes off: the call is the text card it always was.
func _test_card_without_switch() -> void:
	for setting in ["switch", "vignettes"]:
		var ctx := await _match()
		var m: Control = ctx["m"]
		var sim = ctx["sim"]
		var me: int = ctx["me"]
		Features.set_on("decision_scenes", setting != "switch")
		_state.set_vignettes_on(setting != "vignettes")
		sim.moment_side = me
		sim.pending_moment = _moment(sim, me, "momentum")
		m.call("_show_moment")
		await _settle()
		_check(m.find_child("MomentCard", true, false) != null and m.find_child("DecisionVignette", true, false) == null,
				"With %s off the call is the text card" % setting)
		m.queue_free()
		await _settle()
	_state.set_vignettes_on(true)


## A finger on the third choice, after the scene freezes: MatchSim takes the call and the
## match view is back.
func _test_tap() -> void:
	var ctx := await _match()
	var m: Control = ctx["m"]
	var sim = ctx["sim"]
	var me: int = ctx["me"]
	_state.set_vignettes_on(true)
	Features.set_on("decision_scenes", true)
	sim.moment_side = me
	sim.pending_moment = _moment(sim, me, "momentum")
	m.call("_show_moment")
	await _settle()
	var card = m.find_child("MomentCard", true, false)
	var vig = m.find_child("DecisionVignette", true, false)
	var b: Button = card.find_child("Moment_2", true, false) if card != null else null
	_check(vig != null and b != null, "Tap: the scene and its call are up")
	if vig == null or b == null:
		m.queue_free()
		return
	vig.finish_now()
	for i in range(30):
		await process_frame
	var asked: int = sim.moments.size()
	var why: String = await Tap.tap(b)
	_check(why == "", "Tap: a finger on the choice reaches it (%s)" % why)
	_check(sim.moments.size() == asked + 1 and str((sim.moments[-1] as Dictionary).get("kind", "")) == "momentum",
			"Tap: MatchSim takes the call")
	for i in range(40):
		await process_frame
	_check(m.find_child("DecisionVignette", true, false) == null, "Tap: the scene is gone, back to the match")
	m.queue_free()
	await _settle()


func _settle() -> void:
	for i in range(6):
		await process_frame


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)
