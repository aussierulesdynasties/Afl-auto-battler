extends SceneTree
## Copy voice pass 2 (the hub, director 2026-11-10: option B) captures, phone portrait 390x844, a
## fresh Fremantle career that never touches a real save. One launch writes every hub state whose
## copy the pass changed, so the same script gives the before (on main) and the after:
##   godot --path . --script tools/visual/capture_copy_voice_hub.gd -- --out <prefix> [--only a,b]
## Writes <prefix>_<state>.png for: intro, bye, week_off, knocked_out, season_over, semis, prelims,
## grand_final, approach, rookie_draft, season_wrap, options.

const CLUB := "FRE"
var _out := "copy_voice_hub"
var _only: PackedStringArray = []
var _state: Node
var _db: Node
var _router: Node


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			_out = str(a[i + 1])
		elif str(a[i]) == "--only":
			_only = str(a[i + 1]).split(",")
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_router = root.get_node("Router")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_copy_voice.save"
	_state.settings_path = "user://capture_copy_voice.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(390, 844)
	DisplayServer.window_set_size(Vector2i(390, 844))
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)

	# The first hub visit: the weekly loop sheet.
	if _want("intro"):
		_fresh()
		_state.tutorials = true
		_state.set_setting("seen_weekly_loop_intro", false)
		await _hub(false)
		await _shot("intro")
		_state.set_setting("seen_weekly_loop_intro", true)

	# A bye in the home and away (as tests/run_matchup_tests.gd builds it).
	if _want("bye"):
		_fresh()
		var sea = _state.season
		var r0 := 14
		while not (_plays(sea, r0) and _plays(sea, r0 + 1)):
			r0 += 1
		sea.round_index = r0
		for m in (sea.fixture[r0] as Array).duplicate():
			if m["home"] == CLUB or m["away"] == CLUB:
				(sea.fixture[r0] as Array).erase(m)
		await _hub()
		await _shot("bye")

	# Finals (as tests/run_career_ui_tests.gd's _fre_in_finals_at builds them).
	if _want("week_off"):
		_finals_at(1)
		await _hub()
		await _shot("week_off")

	# Knocked out: lost the wildcard, the elimination finals play on.
	if _want("knocked_out"):
		_finals_at(8)
		_week(2, {"W_WC1": "t6", "L_WC1": "t9", "W_WC2": "t8", "L_WC2": CLUB})
		await _hub()
		await _shot("knocked_out")
	if _want("season_over"):
		_finals_at(14)
		await _hub()
		await _shot("season_over")
	# The finals buttons say the week by name when we are not in it: a week off after a
	# qualifying final win, then out in a semi, then out in a preliminary final.
	if _want("semis"):
		_finals_at(1)
		_week(3, {"W_QF1": CLUB, "L_QF1": "t3", "W_QF2": "t1", "L_QF2": "t2", "W_EF1": "t4", "W_EF2": "t5"})
		await _hub()
		await _shot("semis")
	if _want("prelims"):
		_finals_at(1)
		_week(4, {"L_QF1": CLUB, "W_QF1": "t3", "W_QF2": "t1", "L_QF2": "t2", "W_EF1": "t4", "W_EF2": "t5",
				"L_SF1": CLUB, "W_SF1": "t4", "W_SF2": "t2"})
		await _hub()
		await _shot("prelims")
	if _want("grand_final"):
		_finals_at(1)
		_week(5, {"W_QF1": CLUB, "W_QF2": "t1", "W_SF1": "t4", "W_SF2": "t2", "L_PF1": CLUB, "W_PF1": "t2",
				"W_PF2": "t1"})
		await _hub()
		await _shot("grand_final")

	# A rival's approach for one of our coaches (as capture_coach_promise.gd builds it).
	if _want("approach"):
		_fresh()
		var mid: Dictionary = _state.club_staff(CLUB).get("MID", {})
		mid["since"] = _state.season_year - 6
		_state.coach_approaches = [{"cid": str(mid["cid"]), "from_job": "MID", "club": "WBD", "job": "SA",
				"choice": "", "kept": false, "text": ""}]
		await _hub()
		var card: Control = root.find_child("CoachApproaches", true, false)
		if card != null:
			for sc in root.find_children("*", "ScrollContainer", true, false):
				if (sc as ScrollContainer).is_ancestor_of(card):
					(sc as ScrollContainer).scroll_vertical = int(card.global_position.y - 120.0 + (sc as ScrollContainer).scroll_vertical)
					break
		await _frames(10)
		await _shot("approach")

	# The mid-season rookie draft sheet, opened on the hub.
	if _want("rookie_draft"):
		_fresh()
		_state.season.round_index = 10
		var hub: Node = await _hub()
		hub.call("_show_midseason_pick")
		await _frames(12)
		await _shot("rookie_draft")

	# The off-season wrap before Round 1.
	if _want("season_wrap"):
		_fresh()
		_state.season_wrap = {"year": _state.season_year, "seen": false, "ins": [], "outs": [], "trades": [],
				"staff": [], "league_coaches": []}
		await _hub(false)
		await _shot("season_wrap")

	# Settings, scrolled to the sim setting.
	if _want("options"):
		_fresh()
		var host: Node = await _hub()
		var sheet: Control = load("res://scripts/ui/OptionsSheet.gd").open(host, true)
		await _frames(10)
		var row: Control = sheet.find_child("SettingsSimConfirm", true, false)
		var sc := row.get_parent() if row != null else null
		while sc != null and not (sc is ScrollContainer):
			sc = sc.get_parent()
		if sc != null:
			(sc as ScrollContainer).ensure_control_visible(row)
			await _frames(6)
		await _shot("options")

	quit()


func _want(state: String) -> bool:
	return _only.is_empty() or _only.has(state)


## Moves the finals to `week` with these slots ("tN" is the club N-th in the final ten).
func _week(week: int, slots: Dictionary) -> void:
	var top: Array = _state.season.finals["top"]
	var out := {}
	for k in slots:
		var v := str(slots[k])
		out[k] = top[int(v.substr(1))] if v.begins_with("t") and v.length() <= 2 else v
	_state.season.finals["week"] = week
	_state.season.finals["slots"] = out


func _fresh() -> void:
	_state.reset()
	_state.career_seed = 4402
	_state.replay_seed = 4402
	_state.start_season(CLUB, _db.club_list(CLUB))
	_state.tutorials = false
	_state.week_events = []


func _plays(sea, ri: int) -> bool:
	for m in sea.fixture[ri]:
		if m["home"] == CLUB or m["away"] == CLUB:
			return true
	return false


func _finals_at(rank: int) -> void:
	_fresh()
	var sea = _state.season
	var codes: Array = sea.ladder.keys()
	codes.sort()
	codes.erase(CLUB)
	codes.insert(rank - 1, CLUB)
	for i in range(codes.size()):
		var row: Dictionary = sea.ladder[codes[i]]
		row["w"] = 20 - i
		row["l"] = 3 + i
		row["d"] = 0
		row["p"] = 23
		row["pf"] = 2400 - i * 20
		row["pa"] = 2000
	sea.round_index = sea.fixture.size()
	sea.recalc_ladder()
	sea.start_finals()


## Opens the hub fresh and clears what sits over it (the weekly loop sheet unless `dismiss` is off,
## any week event put off with Later).
func _hub(dismiss := true) -> Node:
	_router.stack = []
	_router.go("main")
	var guard := 0
	while not _on("Main") and guard < 600:
		await process_frame
		guard += 1
	_router.go("hub")
	guard = 0
	while not _on("Hub") and guard < 600:
		await process_frame
		guard += 1
	await _frames(40)
	if dismiss:
		for i in range(3):
			for b in root.find_children("*", "Button", true, false):
				if (b as Button).is_visible_in_tree() and (b as Button).text in ["Got it", "Later"]:
					(b as Button).emit_signal("pressed")
			await _frames(12)
	return current_scene


func _on(scene: String) -> bool:
	return current_scene != null and current_scene.scene_file_path.contains(scene)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png("%s_%s.png" % [_out, name])
	print("wrote %s_%s.png" % [_out, name])
