extends SceneTree
## godot --headless --path . --script tests/run_combine_screen_tests.gd
## The Combine screen (row 83): reached from the draft room with real taps, the
## day, each test's whole class best first, position and search, a prospect's
## sheet and back to the same place, nobody given a figure he didn't record.
const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")

var _state: Node
var _Combine
var _checks := 0
var _failures: Array[String] = []
var _ui: Control


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_Combine = load("res://scripts/sim/Combine.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://test_combine_screen.save"
	_state.settings_path = "user://test_combine_screen_settings.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(_state.settings_path))
	_state.show_real_names = false
	_state.replay_seed = 8331
	_state.reset()
	_state.start_season("COL", root.get_node("GameDB").club_list("COL"))
	root.size = Vector2i(390, 844)
	await _t("_test_model")
	await _t("_test_entry_and_first_visit")
	await _t("_test_day")
	await _t("_test_board_and_return")
	await _t("_test_filters")
	await _t("_test_missed_never_invented")
	await _t("_test_pick_from_sheet")
	await _t("_test_league_draft_has_none")
	await _t("_test_meeting_door")
	await _t("_test_widths")
	print(Ran.line("CombineScreen", self))
	quit(0 if _failures.is_empty() else 1)


func _open_room(meeting_done := true) -> void:
	if _ui != null:
		_ui.queue_free()
		await _settle()
	var clubs := ["COL", "CAR"]
	var sizes := {"COL": 34, "CAR": 34}
	var counts := {
		"COL": {"RUCK": 2, "MID": 13, "DEF": 9, "FWD": 10},
		"CAR": {"RUCK": 2, "MID": 13, "DEF": 9, "FWD": 10},
	}
	var prospects: Array = load("res://scripts/sim/Prospects.gd").generate_class(_state.season_year + 1, 7331)
	_state.draft = load("res://scripts/sim/Draft.gd").build_intake(prospects, clubs, clubs, 551, sizes, counts)
	_state.draft.start_for_user("COL")
	_state.my_club = "COL"
	_state.draft_meeting_year = _state.season_year if meeting_done else _state.season_year - 1
	_ui = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(_ui)
	await _settle()


func _find(what: String) -> Node:
	return _ui.find_child(what, true, false)


func _tap(what: String, why: String) -> void:
	var b := _find(what) as Button
	_check(b != null, "%s is there" % what)
	if b != null:
		var missed: String = await Tap.tap(b)
		_check(missed == "", "%s takes a finger: %s" % [why, missed])
	await _settle()


## The class's order, ranks, words and day lines, off the same results the sheet shows.
func _test_model() -> void:
	var prospects: Array = load("res://scripts/sim/Prospects.gd").generate_class(_state.season_year + 1, 7331)
	_check(prospects.size() > 40, "A real class to rank")
	for t in _Combine.TESTS:
		var key := str(t[0])
		var rows: Array = _Combine.ranked(prospects, key, 551)
		var missed: Array = _Combine.untested(prospects, 551)
		_check(rows.size() + missed.size() == prospects.size(), "%s: everyone is ranked or missed" % key)
		for i in rows.size() - 1:
			var a := float(rows[i]["result"])
			var b := float(rows[i + 1]["result"])
			if not ((a <= b) if bool(t[3]) else (a >= b)):
				_check(false, "%s: best first at %d" % [key, i])
				break
		for r in rows:
			if float(r["result"]) != _Combine.result(r["p"], key, 551):
				_check(false, "%s: the screen's figure is the sheet's figure" % key)
				break
		var line: String = _Combine.day_line(key, rows, "Next Man")
		_check(line != "", "%s: a day line" % key)
		var gap: float = absf(float(rows[0]["result"]) - float(rows[1]["result"]))
		_check(gap == 0.0 or line.contains(_Combine.text(key, float(rows[1]["result"]))),
				"%s: the day line quotes the real next result: %s" % [key, line])
		_check(_Combine.day_line(key, rows.slice(0, 1), "") == "", "%s: nobody to compare, no line" % key)
	_check(_Combine.top_ten_words(["sprint", "leap"]) == "Top ten in the sprint and the jump", "Two tests read")
	_check(_Combine.top_ten_words(["sprint", "trial", "kick"]) == "Top ten in the sprint, the time trial and the kicking test", "Three tests read")
	for r in _Combine.all_rounders(prospects, 551):
		_check((r["tests"] as Array).size() >= 2, "Turned heads: two tests or more")
	_check(_Combine.ranked([], "sprint", 551).is_empty() and _Combine.middle([]) == -1.0, "No class, no figures")


func _test_entry_and_first_visit() -> void:
	_state.tutorials = true
	_state.set_setting("seen_draft_intro", true)
	_state.set_setting("seen_combine_intro", false)
	await _open_room()
	_check(_find("CombineIntro") == null, "No Combine intro before the Combine is opened")
	var entry := _find("CombineEntry") as Button
	_check(entry != null and entry.size.y >= 44, "The draft room has a thumb-sized way in")
	await _tap("CombineEntry", "Combine in the draft room")
	_check(_find("CombineScreen") != null, "The tap opens the Combine")
	_check(_find("CombineIntro") != null, "First visit explains what testing is")
	var said := ""
	for l in (_find("CombineIntro") as Node).find_children("*", "Label", true, false):
		said += (l as Label).text + " "
	_check(said.contains("every club") and said.contains("tell you he can play") and said.contains("scouts"),
			"It separates what's measured from what's scouted: %s" % said)
	await _tap("CombineIntroOk", "Got it")
	_check(_find("CombineIntro") == null, "Got it closes it, the Combine stays")
	_check(_find("CombineScreen") != null, "...over the board")
	_check(_ui.handle_back(), "Back closes the Combine")
	await _settle()
	_check(_find("CombineScreen") == null, "...and it's gone")
	_check(_find("CombineEntry") != null, "...back in the draft room")
	await _tap("CombineEntry", "Combine, a second time")
	_check(_find("CombineIntro") == null, "The intro shows once")
	await _tap("TopBarBack", "The top bar's back")
	_check(_find("CombineScreen") == null, "The top bar's back closes it too")


func _test_day() -> void:
	await _open_room()
	await _tap("CombineEntry", "Combine")
	_check(_find("CombineTab_day") != null and _find("CombineCount") != null, "It opens on the day")
	_check((_find("CombineCount") as Label).text.contains("prospects tested"), "It says who tested")
	for t in _Combine.TESTS:
		var key := str(t[0])
		_check(_find("Headline_" + key) != null, "%s has a headline" % key)
		_check(_find("DayLine_" + key) != null, "%s has a line about the day" % key)
	var said := ""
	for l in _ui.find_children("*", "Label", true, false):
		said += (l as Label).text + " "
	_check(said.contains("Best in the class"), "The best in each test is named as that")
	for word in ["should", "best pick", "recommend", "take him"]:
		_check(not said.to_lower().contains(word), "The day never says who to take (%s)" % word)
	_check(_find("CombineCaveat") != null, "Testing is one part of it, and it says so")
	await _tap("AllResults_leap", "All results")
	_check(_find("CombineTest") != null and (_find("CombineTest") as Label).text == "Running vertical jump",
			"All results opens that test")
	_ui.handle_back()
	await _settle()


func _test_board_and_return() -> void:
	await _open_room()
	await _tap("CombineEntry", "Combine")
	await _tap("CombineTab_sprint", "Sprint tab")
	var rows := _find("CombineRows")
	_check(rows != null and rows.get_child_count() > 20, "The whole class to scroll")
	_check(_find("CombineMiddle") != null, "It gives the middle of the class to compare to")
	var first := rows.get_child(0) as Button
	var result := first.find_child("Result", true, false) as Label
	_check(result != null and result.text.ends_with(" s"), "Results read in their unit")
	var standing := first.find_child("Standing", true, false) as Label
	_check(standing != null and standing.text == "Best in the class", "Standing in words")
	var scroll := _find("CombineScroll") as ScrollContainer
	scroll.scroll_vertical = 500
	await _settle()
	var at := scroll.scroll_vertical
	_check(at > 0, "The list scrolls")
	var row := rows.get_child(14) as Button
	var id := str(row.name).trim_prefix("Prospect_")
	var missed: String = await Tap.tap(row)
	_check(missed == "", "A row takes a finger: %s" % missed)
	await _settle()
	var sheet := _find("PlayerDetail")
	_check(sheet != null, "A row opens his sheet")
	_check(sheet != null and sheet.get_index() > _find("CombineScreen").get_index(), "...over the Combine")
	_check(_ui._detail_id == id, "...the man tapped")
	_check(_ui.find_child("Combine_*", true, false) != null, "...with the scouts' read on it")
	_check(_ui.handle_back(), "Back closes the sheet")
	await _settle()
	_check(_find("PlayerDetail") == null and _find("CombineScreen") != null, "...not the Combine")
	_check(_find("CombineTest") != null and (_find("CombineTest") as Label).text == "20 m sprint", "Same test")
	_check(scroll.scroll_vertical == at, "Same place in the list")
	_check(_ui.handle_back(), "Back again closes the Combine")
	await _settle()
	await _tap("CombineEntry", "Combine again")
	_check((_find("CombineTest") as Label).text == "20 m sprint", "A later visit comes back to the same test")
	await _settle()
	_check((_find("CombineScroll") as ScrollContainer).scroll_vertical == at, "...and the same place")
	_ui.handle_back()
	await _settle()


func _test_filters() -> void:
	await _open_room()
	await _tap("CombineEntry", "Combine")
	await _tap("CombineTab_kick", "Kick tab")
	await _tap("CombineRole_RUCK", "RUCK filter")
	var rows := _find("CombineRows")
	_check(rows.get_child_count() > 0, "Some rucks in the class")
	for r in rows.get_children():
		var id := str(r.name).trim_prefix("Prospect_").trim_prefix("Missed_")
		if id.begins_with("CombineMore"):
			continue
		_check(str(_ui._player_by_id(id).get("role", "")) == "RUCK", "Only rucks: %s" % id)
	var field := _find("CombineSearch") as LineEdit
	_check(field != null, "A search box")
	field.text = "zzzz"
	field.text_changed.emit("zzzz")
	await _settle()
	_check(_find("CombineNone") != null, "No match says so")
	await _tap("CombineClear", "Clear")
	_check((_find("CombineSearch") as LineEdit).text == "", "Clear empties the search")
	_check(_find("CombineNone") == null, "...and the class is back")
	_check(_find("CombineRows").get_child_count() > 20, "...all of it")
	var more := _find("CombineMore") as Button
	_check(more != null, "A long class pages")
	if more != null:
		var before := _find("CombineRows").get_child_count()
		_check((await Tap.tap(more)) == "", "Show more takes a finger")
		await _settle()
		_check(_find("CombineRows").get_child_count() > before, "Show more shows more")
	_ui.handle_back()
	await _settle()


func _test_missed_never_invented() -> void:
	await _open_room()
	var pool: Array = _state.draft.pool.filter(func(p): return bool(p.get("projected", false)))
	var missed: Array = _Combine.untested(pool, _state.draft.seed)
	_check(not missed.is_empty(), "This class has someone who missed testing")
	await _tap("CombineEntry", "Combine")
	_check((_find("CombineCount") as Label).text.contains("missed testing"), "The day says some missed it")
	await _tap("CombineTab_trial", "2 km tab")
	_ui._combine_place["shown"] = 999
	_ui._combine._fill_rows("trial")
	await _settle()
	var row := _find("Missed_%s" % str(missed[0]["id"]))
	_check(row != null, "He's listed")
	_check(row != null and row.find_child("Result", true, false) == null, "...with no figure")
	_check(row != null and (row.find_child("Standing", true, false) as Label).text == "Did not test", "...and it says why")
	var rows := _find("CombineRows")
	_check(rows.get_child(rows.get_child_count() - 1).name.begins_with("Missed_"), "...below everyone who tested")
	var ranked_x: float = _name_x(rows.get_child(0))
	_check(row != null and is_equal_approx(_name_x(row), ranked_x), "...in the same columns as the ranked rows")
	_ui._combine_place["shown"] = 40
	_ui.handle_back()
	await _settle()


## A pick from a sheet over the Combine lands back on the board; the man's row
## then says where he went.
func _test_pick_from_sheet() -> void:
	await _open_room()
	await _tap("CombineEntry", "Combine")
	await _tap("CombineTab_sprint", "Sprint tab")
	var rows := _find("CombineRows")
	var id := str(rows.get_child(0).name).trim_prefix("Prospect_")
	_check((await Tap.tap(rows.get_child(0) as Button)) == "", "A row takes a finger")
	await _settle()
	await _tap("DetailDraft", "Draft from his sheet")
	_check(_state.draft.has(id), "The pick is made")
	_check(_find("CombineScreen") == null, "...and lands on the board")
	await _settle()
	_ui.call("_finish_night")
	await _settle()
	await _tap("CombineEntry", "Combine after the pick")
	var row := _find("Prospect_" + id)
	_check(row != null, "He's still in the day's results")
	var said := ""
	if row != null:
		for l in row.find_children("*", "Label", true, false):
			said += (l as Label).text + " "
	_check(said.contains("on your list"), "...and it says he's yours: %s" % said)
	# He stays in the draft's pool and joins its picks: still one man, one row.
	await _tap("CombineTab_day", "The day after the pick")
	var class_size := _state.draft.pool.filter(func(p): return bool(p.get("projected", false))).size()
	_check((_find("CombineCount") as Label).text.contains("of %d prospects" % class_size)
			or (_find("CombineCount") as Label).text.begins_with("All %d" % class_size),
			"The class is the same size after a pick: %s" % (_find("CombineCount") as Label).text)
	await _tap("CombineTab_sprint", "Sprint tab after the pick")
	_ui._combine_place["shown"] = 999
	_ui._combine._fill_rows("sprint")
	await _settle()
	var his := 0
	var ids := {}
	var doubled := 0
	for r in _find("CombineRows").get_children():
		var rid := str(r.get_meta("prospect_id", ""))
		if rid == id:
			his += 1
		if rid != "" and ids.has(rid):
			doubled += 1
		ids[rid] = true
	_check(his == 1, "He's on the board once: %d" % his)
	_check(doubled == 0, "Nobody is on the board twice: %d" % doubled)
	_ui._combine_place["shown"] = 40
	_ui.handle_back()
	await _settle()


func _test_league_draft_has_none() -> void:
	if _ui != null:
		_ui.queue_free()
		await _settle()
	var db := root.get_node("GameDB")
	_state.draft = load("res://scripts/sim/Draft.gd").new(db.all_players_sorted() + db.all_draftees_sorted(),
			db.active_clubs(2027).duplicate(), 12345)
	_state.draft.start_for_user("COL")
	_ui = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(_ui)
	await _settle()
	_check(_find("BackToMenu") != null, "The league draft's room is up")
	_check(_find("CombineEntry") == null, "A league draft never had a Combine: no way in")


## Before the draft: the meeting has its own door, and closing the Combine comes
## back to the meeting.
func _test_meeting_door() -> void:
	await _open_room(false)
	_check(_find("DraftMeeting") != null, "The meeting opens first")
	await _tap("MeetingCombine", "See the Combine")
	_check(_find("CombineScreen") != null, "The meeting's door opens the Combine")
	_check(_find("CombineScreen").get_index() > _find("DraftMeeting").get_index(), "...over the meeting")
	await _tap("CombineTab_leap", "A tab over the meeting")
	_check(_find("CombineTest") != null, "The Combine takes the taps, not the meeting under it")
	_check(_ui.handle_back(), "Back closes the Combine")
	await _settle()
	_check(_find("CombineScreen") == null and _find("DraftMeeting") != null, "...back to the meeting")


func _test_widths() -> void:
	for w in [320, 360, 390]:
		root.size = Vector2i(w, 800)
		await _open_room()
		await _tap("CombineEntry", "Combine at %d" % w)
		for view in ["day", "sprint"]:
			await _tap("CombineTab_" + view, "%s at %d" % [view, w])
			var view_rect := Rect2(Vector2.ZERO, root.get_visible_rect().size).grow(1)
			for t in _find("CombineTabs").get_children():
				_check(view_rect.encloses((t as Control).get_global_rect()), "%s fits at %d" % [t.name, w])
				_check((t as Control).size.y >= 44, "%s thumb-sized at %d" % [t.name, w])
			var body := _find("CombineBody") as Control
			var sc := _find("CombineScroll") as Control
			_check(body.size.x <= sc.size.x + 1.0, "%s doesn't run off the side at %d" % [view, w])
		var entry_rect: Rect2 = _find("CombineScreen").get_global_rect()
		_check(view_ok(entry_rect), "The Combine fills the screen at %d" % w)
		_ui.handle_back()
		await _settle()
		var entry := _find("CombineEntry") as Control
		_check(entry != null and Rect2(Vector2.ZERO, root.get_visible_rect().size).grow(1).encloses(entry.get_global_rect()),
				"The way in stays on screen at %d" % w)
	root.size = Vector2i(390, 844)


## Where a row's first column after the rank starts.
func _name_x(row: Node) -> float:
	var rank := row.find_child("Rank", true, false) as Control
	return -1.0 if rank == null else rank.size.x + rank.global_position.x


func view_ok(r: Rect2) -> bool:
	return r.size.x >= root.get_visible_rect().size.x - 1.0 and r.size.y >= root.get_visible_rect().size.y - 1.0


func _settle() -> void:
	for i in range(6):
		await process_frame


func _check(ok: bool, what: String) -> void:
	_checks += 1
	if not ok:
		_failures.append(what)
		push_error(what)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
