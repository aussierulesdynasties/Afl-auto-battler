extends SceneTree
## godot --headless --path . --script tests/run_score_clock_tests.gd
## T3.R42 (P-26, C-PC-01): the score and the clock never leave the match
## screen. On a phone held upright (390x844) a live match is walked through
## every match-day state a test can reach - each break panel, a break sheet,
## the stats view, a coach's call, a vignette, live play and full time - and
## in each the two scores and the clock are shown, inside the screen, and
## nothing drawn over the match covers them.
## Match day's bugs (director, 2026-11-12): the clock names each stoppage
## ("Pre-match", "Quarter time", "Half time", "Three-quarter time", "Full time"),
## the play and skip buttons are neither drawn nor tappable under a sheet (real
## taps), and in the stats' player rows no figure, name and Profile tap overlap,
## on a phone (390x844) and a PC (1280x720 units, a 1920x1080 window's canvas).

const Tap := preload("res://tests/tap.gd")
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
	for sz in [PHONE, Vector2i(1280, 720)]:
		await _t("_test_stoppage_clock_and_covered_controls", [sz])
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


## The clock's words at each stoppage, longest first (it takes the first that fits).
const STOPPAGES := [["Pre-match"], ["Quarter time", "Qtr time"], ["Half time"], ["Three-quarter time", "3/4 time"]]
const STOPPAGE_NAMES := ["before the first bounce", "quarter time", "half time", "three-quarter time"]


## One coached match, skipped from break to break with real taps. At every
## stoppage the clock names it, and the play, speed and skip buttons under the
## sheet are not drawn and do nothing when tapped where they sit. While the
## ball is in play the clock counts minutes and the buttons work. The stats'
## player rows are checked at half time and at full time.
func _test_stoppage_clock_and_covered_controls(sz: Vector2i) -> void:
	var db = root.get_node("GameDB")
	var tag := "%dx%d" % [sz.x, sz.y]
	_state.set_vignettes_on(false)
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.start_season("FRE", db.club_list("FRE"))
	root.size = sz
	_state.set_match_way("watch")
	_state.set_vignettes_on(false)
	_check(_state.prepare_interactive_match(), "A live match is prepared (%s)" % tag)
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _settle()
	var sim = _state.pending_sim
	var controls: Control = m.find_child("MatchControls", true, false)
	_check(controls != null, "The match has its play and skip buttons (%s)" % tag)
	if controls == null:
		m.queue_free()
		await _settle()
		return
	var taps := 0
	for q in range(1, 5):
		var at := "%s, %s" % [STOPPAGE_NAMES[q - 1], tag]
		var box: Node = m.find_child("CoachBox", true, false)
		_check(box != null and sim.current_quarter == q, "The break is up (%s)" % at)
		if box == null:
			break
		_check_clock(m, STOPPAGES[q - 1], at)
		taps += await _check_dead_controls(m, controls, at)
		if q == 3:
			m.call("_show_break_stats")
			await _settle()
			var sheet: Node = m.find_child("BreakStatsSheet", true, false)
			_check(sheet != null, "Match stats opens (%s)" % at)
			_check_clock(m, STOPPAGES[q - 1], "match stats, " + at)
			taps += await _check_dead_controls(m, controls, "match stats, " + at)
			if sheet != null:
				_check_player_rows(sheet, "match stats, " + at)
			m.call("handle_back")
			await _settle()
		var why: String = await Tap.tap(m.find_child("StartQuarter", true, false))
		await _settle()
		_check(why == "" and m.find_child("CoachBox", true, false) == null, "A real tap on Start starts the quarter (%s: %s)" % [at, why])
		var clock: Label = m.get("_clock")
		_check(clock.text.begins_with("Q") and clock.text.ends_with("'"),
				"With the ball in play the clock counts minutes (after %s: '%s')" % [at, clock.text])
		# A coach's call that came up in those frames takes its default.
		var g := 0
		while m.get("_moment_overlay") != null and is_instance_valid(m.get("_moment_overlay")) \
				and not sim.pending_moment.is_empty() and g < 20:
			g += 1
			m.call("_on_moment_choice", int(sim.pending_moment.get("default", 0)))
			await _settle()
		var live := []
		for b in controls.find_children("*", "BaseButton", true, false):
			if (b as Control).mouse_filter != Control.MOUSE_FILTER_STOP:
				live.append(str(b.name))
		_check(is_equal_approx(controls.modulate.a, 1.0) and live.is_empty(),
				"With no sheet up the play and skip buttons are drawn and take taps (after %s: alpha %.2f, dead %s)" % [
				at, controls.modulate.a, str(live)])
		var skip: Button = m.find_child("SkipToBreak", true, false)
		if q == 4:
			skip = null
			for b in controls.find_children("*", "Button", true, false):
				if (b as Button).text == "Skip to full time":
					skip = b
		why = await Tap.tap(skip)
		for i in range(4):
			await _settle()
		_check(why == "", "A real tap on %s works while the ball is in play (after %s: %s)" % [
				skip.text if skip != null else "the skip button", at, why])
	_check(bool(m.get("_fulltime_shown")) and m.find_child("FullTime", true, false) != null, "The match reaches full time (%s)" % tag)
	_check_clock(m, ["Full time"], "full time, " + tag)
	taps += await _check_dead_controls(m, controls, "full time, " + tag)
	# Where a tall sheet's own buttons sit over every one of them (a phone's opening
	# break) there is no such spot to tap; across the match there are many.
	_check(taps >= 8, "Covered buttons were tapped where they sit (%s: %d real taps)" % [tag, taps])
	var tab: Button = m.find_child("ReviewTab_stats", true, false)
	var why_tab: String = await Tap.tap(tab)
	await _settle()
	var ft: Node = m.find_child("FullTime", true, false)
	_check(why_tab == "" and ft != null, "A real tap opens full time's Stats tab (%s: %s)" % [tag, why_tab])
	if ft != null:
		_check_player_rows(ft, "full time Stats, " + tag)
	_check_clock(m, ["Full time"], "full time Stats, " + tag)
	m.queue_free()
	_state.pending_sim = null
	await _settle()


## The clock reads one of `words` (the longest that fits) and fits its place between the scores.
func _check_clock(m: Control, words: Array, at: String) -> void:
	var clock: Label = m.get("_clock")
	if clock == null or not is_instance_valid(clock):
		_check(false, "The clock exists (%s)" % at)
		return
	var room := float(clock.get_meta("room", 0.0))
	var font: Font = clock.get_theme_font("font")
	var wide := font.get_string_size(clock.text, HORIZONTAL_ALIGNMENT_LEFT, -1, clock.get_theme_font_size("font_size")).x
	_check(words.has(clock.text), "The clock names the stoppage (%s: '%s', want %s)" % [at, clock.text, str(words)])
	print("stoppage clock %s: '%s' %.0f of %.0f at %d px" % [at, clock.text, wide, room, clock.get_theme_font_size("font_size")])
	_check(wide <= room + 0.5 and clock.get_theme_font_size("font_size") >= 13,
			"The clock's words fit between the scores at a readable size (%s: '%s' is %.0f of %.0f at %d px)" % [
			at, clock.text, wide, room, clock.get_theme_font_size("font_size")])
	# The longest form that fits is the one shown: a shorter form only when the full words do not fit.
	if clock.text != str(words[0]):
		var full := font.get_string_size(str(words[0]), HORIZONTAL_ALIGNMENT_LEFT, -1, 14).x
		_check(full > room, "The short form is used only where the full words do not fit (%s: '%s' is %.0f of %.0f)" % [
				at, str(words[0]), full, room])


## Under a sheet the play, speed and skip buttons are not drawn, and a real tap
## where each one sits presses nothing and changes nothing in the match.
func _check_dead_controls(m: Control, controls: Control, at: String) -> int:
	_check(is_zero_approx(controls.modulate.a), "The play and skip buttons are not drawn under the sheet (%s: alpha %.2f)" % [at, controls.modulate.a])
	var sim = _state.pending_sim
	var pitch = m.get("_pitch")
	var snap := func() -> Array:
		return [sim.current_quarter if sim != null else -1, bool(m.get("_skipping")), bool(m.get("_finished")),
				int(m.get("_playback_event_index")), bool(pitch.playing), float(pitch.speed), int(m.get("_breaks_played")),
				_sheet_names(m)]
	var tapped := 0
	for b in controls.find_children("*", "BaseButton", true, false):
		var btn := b as BaseButton
		if not btn.visible:
			continue
		# A sheet's own button over the same spot is the sheet's business: the tap there
		# is its tap. The finger lands on a part of the button no sheet button is over.
		var spot := Vector2.INF
		for f in [Vector2(0.5, 0.5), Vector2(0.2, 0.5), Vector2(0.8, 0.5), Vector2(0.5, 0.25), Vector2(0.5, 0.75)]:
			if spot == Vector2.INF and not _sheet_button_at(m, btn.get_global_rect().position + btn.size * f):
				spot = btn.size * f
		if spot == Vector2.INF:
			continue
		var before: Array = snap.call()
		var why: String = await Tap.tap_at(btn, spot, false)
		await _settle()
		var after: Array = snap.call()
		tapped += 1
		_check(why != "" and before == after and btn.focus_mode == Control.FOCUS_NONE,
				"A real tap where '%s' sits under the sheet does nothing (%s: pressed %s, match %s -> %s)" % [
				btn.text if btn is Button else str(btn.name), at, str(why == ""), str(before), str(after)])
	return tapped


## The sheets up over the match, by name.
func _sheet_names(m: Control) -> Array:
	var out := []
	var over: Node = m.get("_over")
	for c in over.get_children():
		if not c.is_queued_for_deletion():
			out.append(str(c.name))
	return out


## True when one of the sheets' own buttons is under `point`.
func _sheet_button_at(m: Control, point: Vector2) -> bool:
	var over: Node = m.get("_over")
	for b in over.find_children("*", "BaseButton", true, false):
		if (b as Control).is_visible_in_tree() and (b as Control).get_global_rect().has_point(point):
			return true
	return false


## The stats' player rows: his name, his figure and the Profile tap each keep
## their own room, and the tap stays inside its row.
func _check_player_rows(sheet: Node, at: String) -> void:
	var rows := sheet.find_children("BoxPlayer_*", "Button", true, false)
	var seen := 0
	var bad := []
	for r in rows:
		var b := r as Button
		if not b.is_visible_in_tree():
			continue
		var tap: Control = null
		for c in b.get_children():
			if str(c.name).begins_with("Profile_"):
				tap = c
		var h: Control = b.get_child(0)
		var who: Control = h.get_child(0)
		var fig: Control = h.get_child(1)
		if tap == null:
			bad.append("%s: no Profile tap" % b.name)
			continue
		seen += 1
		var tr := tap.get_global_rect()
		var fr := fig.get_global_rect()
		var wr := who.get_global_rect()
		if fr.intersects(tr):
			bad.append("%s: figure %s over Profile %s" % [b.name, str(fr), str(tr)])
		if wr.intersects(fr) or wr.intersects(tr):
			bad.append("%s: name %s over figure %s or Profile %s" % [b.name, str(wr), str(fr), str(tr)])
		if not b.get_global_rect().grow(0.5).encloses(tr):
			bad.append("%s: Profile %s leaves its row %s" % [b.name, str(tr), str(b.get_global_rect())])
		if wr.size.x < 60.0:
			bad.append("%s: name only %.0f wide" % [b.name, wr.size.x])
	_check(seen >= 4, "The stats show player rows (%s: %d)" % [at, seen])
	_check(bad.is_empty(), "In every player row the name, the figure and Profile keep clear of each other (%s: %s)" % [at, str(bad)])


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
