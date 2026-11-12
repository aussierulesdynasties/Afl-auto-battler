extends SceneTree
## godot --headless --path . --script tests/run_score_clock_tests.gd
## T3.R42 (P-26, C-PC-01): the score and the clock never leave the match
## screen. On a phone held upright (390x844) a live match is walked through
## every match-day state a test can reach - each break panel, a break sheet,
## the stats view, a coach's call, a vignette, live play and full time - and
## in each the two scores and the clock are shown, inside the screen, and
## nothing drawn over the match covers them.

const SUITE_SEED := 2027
const PHONE := Vector2i(390, 844)

var _state: Node
var _checks := 0
var _failures: Array[String] = []
var _seen := {}      # state -> true, every state the walk checked


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
	await _t("_test_score_and_clock_stay")
	print(Ran.line("Score and clock", self))
	quit(0 if _failures.is_empty() else 1)


## One match, start to finish, checked in every state it passes through.
func _test_score_and_clock_stay() -> void:
	var db = root.get_node("GameDB")
	_state.set_vignettes_on(true)
	_state.set_bounce_scene_every_match(true)
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.start_season("COL", db.club_list("COL"))
	root.size = PHONE
	_state.set_match_way("watch")
	_check(_state.prepare_interactive_match(), "A live match is prepared")
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _settle()

	var breaks := ["before the first ball-up", "quarter time", "half time", "three-quarter time"]
	var at_break := 0
	var guard := 0
	while not bool(m.get("_fulltime_shown")) and guard < 60000:
		guard += 1
		var box: Node = m.find_child("CoachBox", true, false)
		if box != null:
			var name := str(breaks[mini(at_break, breaks.size() - 1)])
			_assert_shown(m, "the break, " + name)
			# The stats view, opened from the break.
			var stats: Button = box.find_child("BreakStats", true, false)
			if stats != null and stats.is_visible_in_tree():
				await _open_stats(m, stats, name)
			# A call's sheet over the break (Best so far, from quarter time),
			# and the stats view from its links.
			var best: Button = box.find_child("BestSoFarOpen", true, false)
			if best != null and best.is_visible_in_tree():
				best.emit_signal("pressed")
				await _settle()
				var sheet: Node = m.find_child("CallSheet_best", true, false)
				_check(sheet != null, "Best so far opens at %s" % name)
				_assert_shown(m, "Best so far at " + name)
				stats = sheet.find_child("BreakStats", true, false) if sheet != null else null
				if stats != null and stats.is_visible_in_tree():
					await _open_stats(m, stats, name)
				m.call("handle_back")
				await _settle()
			var start: Button = box.find_child("StartQuarter", true, false)
			_check(start != null, "The break at %s can be left" % name)
			if start == null:
				break
			start.emit_signal("pressed")
			await _settle()
			at_break += 1
			if at_break == 1:
				_assert_shown(m, "live play")
			continue
		var card: Node = m.find_child("MomentCard", true, false)
		if card != null:
			var scene := card.has_meta("scene")
			var pick: Button = card.find_child("Moment_0", true, false)
			if pick != null and not pick.disabled and pick.is_visible_in_tree():
				_assert_shown(m, "a coach's call (%s)" % ("over its scene" if scene else "card"))
				pick.emit_signal("pressed")
				await _settle()
				continue
		var replay: Node = m.find_child("BroadcastVignetteOverlay", true, false)
		if replay != null:
			# Two frames in, the replay is drawing; then it is cut short.
			await process_frame
			await process_frame
			_assert_shown(m, "a vignette (replay)")
			m.call("_finish_broadcast")
			await _settle()
			continue
		var pitch = m.get("_pitch")
		if pitch != null and pitch.playing:
			pitch._process(0.25)
		await process_frame
	_check(bool(m.get("_fulltime_shown")), "The match reaches full time")
	await _settle()
	_assert_shown(m, "full time")
	var tab: Button = m.find_child("ReviewTab_stats", true, false)
	_check(tab != null, "Full time has a Stats tab")
	if tab != null:
		tab.emit_signal("pressed")
		await _settle()
		_assert_shown(m, "full time, Stats")
	for s in ["the break, before the first ball-up", "the break, quarter time", "the break, half time",
			"the break, three-quarter time", "match stats at quarter time", "Best so far at quarter time",
			"live play", "full time", "full time, Stats"]:
		_check(_seen.has(s), "The walk reached %s" % s)
	var call_seen := false
	var vignette_seen := false
	for s in _seen:
		call_seen = call_seen or str(s).begins_with("a coach's call")
		vignette_seen = vignette_seen or str(s) == "a vignette (replay)" or str(s) == "a coach's call (over its scene)"
	_check(call_seen, "The walk reached a coach's call (%s)" % str(_seen.keys()))
	_check(vignette_seen, "The walk reached a vignette (%s)" % str(_seen.keys()))
	m.queue_free()
	await _settle()


func _open_stats(m: Control, stats: Button, name: String) -> void:
	stats.emit_signal("pressed")
	await _settle()
	_check(m.find_child("BreakStatsSheet", true, false) != null, "Match stats opens at %s" % name)
	_assert_shown(m, "match stats at " + name)
	m.call("handle_back")
	await _settle()


## The two scores and the clock: visible, inside the screen, and clear of
## everything drawn over the match.
func _assert_shown(m: Control, state: String) -> void:
	_seen[state] = true
	var screen := Rect2(Vector2.ZERO, Vector2(PHONE))
	var parts := {"home score": m.get("_score_home"), "away score": m.get("_score_away"), "clock": m.get("_clock")}
	var covers := _covers(m)
	for what in parts:
		var l: Label = parts[what]
		if l == null or not is_instance_valid(l):
			_check(false, "The %s exists (%s)" % [what, state])
			continue
		var r := l.get_global_rect()
		_check(l.is_visible_in_tree() and l.text.strip_edges() != "" and r.size.x > 4.0 and r.size.y > 4.0,
				"The %s is shown (%s: '%s', %s)" % [what, state, l.text, str(r)])
		_check(screen.encloses(r), "The %s is inside the screen (%s: %s)" % [what, state, str(r)])
		var over := []
		for c in covers:
			if (c as Control).get_global_rect().intersects(r):
				over.append(str((c as Node).name))
		_check(over.is_empty(), "Nothing covers the %s (%s: under %s)" % [what, state, str(over)])


## Everything drawn over the match screen: what the scene holds beside its
## own layout (sheets, cards, scenes), and anything on the root above it.
func _covers(m: Control) -> Array:
	var out := []
	var layout: Node = m.get("_margin")
	for c in m.get_children():
		if c == layout or not (c is Control) or not (c as Control).visible:
			continue
		# A host that holds the overlays draws nothing itself: its children do.
		if (c as Control).mouse_filter == Control.MOUSE_FILTER_IGNORE and not (c is ColorRect) \
				and c.get_script() == null and c.get_child_count() > 0:
			for k in c.get_children():
				if k is Control and (k as Control).visible:
					out.append(k)
			continue
		if (c as Control).mouse_filter == Control.MOUSE_FILTER_IGNORE and c.get_child_count() == 0:
			continue
		out.append(c)
	var after := false
	for c in root.get_children():
		if c == m:
			after = true
			continue
		if not after:
			continue
		if c is Control and (c as Control).visible:
			out.append(c)
		elif c is CanvasLayer and (c as CanvasLayer).visible:
			for k in c.get_children():
				if k is Control and (k as Control).visible:
					out.append(k)
	return out


func _settle() -> void:
	for i in range(6):
		await process_frame


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
