extends SceneTree
## godot --headless --path . --script tests/run_matchday_breaks_tests.gd
## Every break fits its sheet: three pairings at a PC and a phone size, each
## break of the match. Moved out of tests/run_matchday_tests.gd onto its own
## nightly machine (director 2026-11-18: "Yes, split both"): it was about half
## of matchday's time. The checks are the same; the search for the pairing's
## seed now runs once per pairing instead of once per break.

const Tap := preload("res://tests/tap.gd")
const SUITE_SEED := 2027

var _state: Node
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_state.autosave_enabled = false
	# These tests drive the hub for other things: no club card opens over it
	# (_test_event_card_then_the_week turns it back on for its own case).
	_state.event_sheets = false
	_state.save_path = "user://test_career.save"
	_state.settings_path = "user://test_settings.cfg"
	# Return visits: the first-visit intros (FirstVisitIntro.gd) have their own suite.
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	# Never the clock: every season in this suite starts from a fixed seed, so
	# a run can't pass or fail on which opponent it happened to draw.
	_state.replay_seed = SUITE_SEED
	for pair in [["COL", "CAR"], ["HAW", "STK"], ["FRE", "MEL"]]:
		for sz in [Vector2i(1280, 720), Vector2i(390, 844)]:
			await _t("_test_every_break_fits", [pair[0], pair[1], sz])
	print(Ran.line("Matchday breaks", self))
	quit(0 if _failures.is_empty() else 1)


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


## Quarter, half and three-quarter time all fit their sheet, with all three
## Play through players named (the longest row) and real names on: on a PC
## whichever call is open, a tag on included; on a phone, the break and every
## call row's answer. COL v CAR at half time once needed 615 of 608.
func _test_every_break_fits(club: String, vs: String, sz: Vector2i) -> void:
	var db = root.get_node("GameDB")
	# The seed search below leaves the last seed tried: put the suite's back, so
	# the tests after this one start from the season they were written for.
	var seed_before: int = _state.replay_seed
	root.size = sz
	# The first seed whose first match is club v vs. A season started from the
	# same seeds draws the same match, so the search runs once and each break
	# below starts that season again from the seed it found.
	var found := false
	var hit := 0
	for tries in range(80):
		_state.reset()
		_state.career_seed = 2050 + tries
		_state.replay_seed = 2050 + tries
		_state.set_setting("seen_training_intro", true)
		_state.start_season(club, db.club_list(club))
		_state.prepare_interactive_match()
		var sq = _state.pending_sim.squads
		if str(sq[0].code) == vs or str(sq[1].code) == vs:
			found = true
			hit = 2050 + tries
			break
	for q in [2, 3, 4]:
		_state.reset()
		_state.career_seed = hit
		_state.replay_seed = hit
		_state.set_setting("seen_training_intro", true)
		_state.start_season(club, db.club_list(club))
		_state.prepare_interactive_match()
		var sq0 = _state.pending_sim.squads
		_check(found and (str(sq0[0].code) == vs or str(sq0[1].code) == vs), "(setup) %s draw %s" % [club, vs])
		var sim = _state.pending_sim
		var me := int(sim.moment_side)
		var t: Dictionary = (sim.tactics[me] as Dictionary).duplicate()
		var used := {}
		for slot in load("res://scripts/ui/match/MatchNotes.gd").FOCUS_ORDER:
			for p in sim.squads[me].ground:
				if not used.has(str(p["id"])):
					t[slot] = str(p["id"])
					used[str(p["id"])] = true
					break
		sim.set_tactics(me, t)
		for i in range(q - 1):
			sim.run_quarter()
		var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
		root.add_child(m)
		await _settle()
		await _settle()
		var box: Node = m.find_child("CoachBox", true, false)
		var tag := "%s v %s, %dx%d, break before quarter %d" % [club, vs, sz.x, sz.y, q]
		_check(box != null and box.has_meta("one_line"), "(setup) the one-line break is up (%s)" % tag)
		if box == null:
			m.queue_free()
			await _settle()
			continue
		var tall := []
		var f := _break_fit(box)
		if f[0] > f[1] + 1.0:
			tall.append("break %.0f of %.0f" % [f[0], f[1]])
		var rows: Array = box.find_children("CallRow_*", "Button", true, false)
		for r in rows:
			var inside := (r as Control).get_child(0) as Control
			if inside.get_combined_minimum_size().x > (r as Control).size.x + 1.0:
				tall.append("%s needs %.0f of %.0f wide" % [r.name, inside.get_combined_minimum_size().x, (r as Control).size.x])
		if box.find_child("BreakColumns", true, false) != null:
			for r in rows:
				var w_row: String = await Tap.tap(r)
				await _settle()
				f = _break_fit(box)
				if w_row != "" or f[0] > f[1] + 1.0:
					tall.append("%s %.0f of %.0f %s" % [r.name, f[0], f[1], w_row])
				if str(r.name) == "CallRow_tag":
					for b in box.find_children("TagPickerGrid_*", "Button", true, false):
						if str(b.name) != "TagPickerGrid_":
							(b as Button).emit_signal("pressed")
							break
					await _settle()
					f = _break_fit(box)
					if f[0] > f[1] + 1.0:
						tall.append("tag on %.0f of %.0f" % [f[0], f[1]])
		_check(tall.is_empty(), "The break fits its sheet, nothing scrolls or overruns its row (%s: %s)" % [tag, str(tall)])
		# On a phone what your calls did is one row; a real tap opens the lot.
		var open_did: Button = box.find_child("CallsDidOpen", true, false)
		if open_did != null:
			var w_did: String = await Tap.tap(open_did)
			await _settle()
			var did_sheet: Node = m.find_child("CallSheet_did", true, false)
			var did_list: Node = did_sheet.find_child("CallsDid", true, false) if did_sheet != null else null
			_check(w_did == "" and did_list != null and (did_list as Control).is_visible_in_tree() and did_list.get_child_count() > 0,
					"What our calls did opens in a sheet on a real tap (%s%s)" % [tag, (", " + w_did) if w_did != "" else ""])
			m.call("handle_back")
			await _settle()
		m.queue_free()
		await _settle()
	_state.replay_seed = seed_before


## What the break's list holds against the room it has (a break that fits does not scroll).
func _break_fit(box: Node) -> Array:
	for sc in box.find_children("*", "ScrollContainer", true, false):
		if (sc as ScrollContainer).vertical_scroll_mode == ScrollContainer.SCROLL_MODE_DISABLED:
			continue
		for ch in sc.get_children():
			if ch is Control and not (ch is ScrollBar):
				return [(ch as Control).get_combined_minimum_size().y, (sc as Control).size.y]
	return [INF, 0.0]
