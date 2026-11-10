extends SceneTree
## Copy voice pass 2 (the hub, director 2026-11-10: option B) captures, phone portrait 390x844, a
## fresh Fremantle career that never touches a real save. One launch writes every hub state whose
## copy the pass changed, so the same script gives the before (on main) and the after:
##   godot --path . --script tools/visual/capture_copy_voice_hub.gd -- --out <prefix>
## Writes <prefix>_<state>.png for: intro, bye, week_off, knocked_out, season_over, semis, prelims,
## grand_final, approach, rookie_draft, season_wrap.

const CLUB := "FRE"
var _out := "copy_voice_hub"
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
	_fresh()
	_state.tutorials = true
	_state.set_setting("seen_weekly_loop_intro", false)
	await _hub(false)
	await _shot("intro")
	_state.set_setting("seen_weekly_loop_intro", true)

	# A bye in the home and away (as tests/run_matchup_tests.gd builds it).
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
	_finals_at(1)
	await _hub()
	await _shot("week_off")
	_finals_at(8)
	_state.season.finals["slots"]["L_WC2"] = CLUB
	await _hub()
	await _shot("knocked_out")
	_finals_at(14)
	await _hub()
	await _shot("season_over")
	var top: Array
	_finals_at(1)
	top = _state.season.finals["top"]
	_state.season.finals["week"] = 3
	_state.season.finals["slots"] = {"L_QF1": CLUB, "W_EF1": top[4], "L_QF2": top[2], "W_EF2": top[5]}
	await _hub()
	await _shot("semis")
	_finals_at(1)
	top = _state.season.finals["top"]
	_state.season.finals["week"] = 4
	_state.season.finals["slots"] = {"W_QF1": CLUB, "W_SF2": top[4], "W_QF2": top[1], "W_SF1": top[2]}
	await _hub()
	await _shot("prelims")
	_finals_at(1)
	top = _state.season.finals["top"]
	_state.season.finals["week"] = 5
	_state.season.finals["slots"] = {"W_PF1": CLUB, "W_PF2": top[1]}
	await _hub()
	await _shot("grand_final")

	# A rival's approach for one of our coaches (as capture_coach_promise.gd builds it).
	_fresh()
	var mid: Dictionary = _state.club_staff(CLUB).get("MID", {})
	mid["since"] = _state.season_year - 6
	_state.coach_approaches = [{"cid": str(mid["cid"]), "from_job": "MID", "club": "WBD", "job": "SA",
			"choice": "", "kept": false, "text": ""}]
	var hub: Node = await _hub()
	var card: Control = root.find_child("CoachApproaches", true, false)
	if card != null:
		for sc in root.find_children("*", "ScrollContainer", true, false):
			if (sc as ScrollContainer).is_ancestor_of(card):
				(sc as ScrollContainer).scroll_vertical = int(card.global_position.y - 120.0 + (sc as ScrollContainer).scroll_vertical)
				break
	await _frames(10)
	await _shot("approach")

	# The mid-season rookie draft sheet, opened on the hub.
	_fresh()
	_state.season.round_index = 10
	hub = await _hub()
	hub.call("_show_midseason_pick")
	await _frames(12)
	await _shot("rookie_draft")

	# The off-season wrap before Round 1.
	_fresh()
	_state.season_wrap = {"year": _state.season_year, "seen": false, "ins": [], "outs": [], "trades": [],
			"staff": [], "league_coaches": []}
	await _hub(false)
	await _shot("season_wrap")
	quit()


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
