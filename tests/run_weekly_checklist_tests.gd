extends SceneTree
## godot --headless --path . --script tests/run_weekly_checklist_tests.gd
## The Hub's weekly checklist (WeekChecklist.gd; setting "weekly_checklist",
## off by default; director, 2026-11-03): jobs read from real state, ticked
## when done, one tap to their screen, the big call's slot empty until the
## coach arcs fill it, never a block on Play; off, the Hub is as before.

var _state: Node
var _router: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []

const WC := preload("res://scripts/state/WeekChecklist.gd")
const SIZES := [Vector2i(1280, 720), Vector2i(390, 844)]


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 8) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_router = root.get_node("Router")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://test_weekly_checklist.save"
	_state.settings_path = "user://test_weekly_checklist.cfg"
	_state.delete_saved_career()
	root.size = SIZES[0]
	await _t("_test_off_is_old_hub")
	await _t("_test_items_reflect_state")
	await _t("_test_ticks_on_completion")
	await _t("_test_hub_card_and_note")
	await _t("_test_layout_sizes")
	await _t("_test_intro_text")
	_state.set_setting(WC.SETTING, false)
	print(Ran.line("Weekly checklist", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


func _fresh(on: bool) -> void:
	_state.reset()
	_state.set_setting(WC.SETTING, on)
	_state.start_season("MEL", _db.club_list("MEL"))
	_state.tutorials = false
	_state.week_events = []
	_state.staff_vacancies = []


func _go(key: String) -> void:
	_router.go(key)
	await _settle()


func _hub() -> void:
	_router.stack = []
	_router.go("main")
	await _settle(2)
	await _go("hub")


func _find(n: String) -> Node:
	return current_scene.find_child(n, true, false)


func _mark_text(job: String) -> String:
	var row := _find("WeekJob_" + job)
	if row == null:
		return ""
	return str((row.find_child("Mark", true, false) as Label).text)


func _test_off_is_old_hub() -> void:
	_fresh(false)
	_check(not WC.on(_state) and WC.items(_state).is_empty() and WC.left(_state) == 0,
			"Off by default: no jobs")
	await _hub()
	_check(_find("WeekJobs") == null and _find("JobsLeftNote") == null and _find("PlayMatch") != null,
			"Off: the Hub has no checklist and no note, Play match as before")
	await _go("selection")
	_check(_state.week_checks.is_empty(), "Off: opening Team writes no checklist state")


func _test_items_reflect_state() -> void:
	_fresh(true)
	var keys := []
	for it in WC.items(_state):
		keys.append(str(it["key"]))
	_check(keys == ["team", "training"], "A plain week: look over the side, check training (%s)" % [keys])
	_check(WC.left(_state) == 2, "Both open")
	_check(WC.big_call(_state).is_empty(), "The big call's slot is empty by default")
	_state.staff_vacancies = [{"job": "assistant", "reason": "Test left"}]
	var coaching := {}
	for it in WC.items(_state):
		if str(it["key"]) == "coaching":
			coaching = it
	_check(not coaching.is_empty() and not bool(coaching["done"]) and str(coaching["route"]) == "staff",
			"An open staff job, the one the Coaching button counts, is a job to Staff")
	_state.staff_vacancies = []
	coaching = {}
	for it in WC.items(_state):
		if str(it["key"]) == "coaching":
			coaching = it
	_check(not coaching.is_empty() and bool(coaching["done"]), "Filled, it stays on the week's list, ticked")


func _test_ticks_on_completion() -> void:
	_fresh(true)
	await _hub()
	_check(_mark_text("team") == "To do" and _mark_text("training") == "To do", "Both jobs start open on the Hub")
	var team: Button = _find("WeekJob_team")
	if team != null:
		team.emit_signal("pressed")
		await _settle()
	_check(_router.current() == "selection", "Tapping a job opens its screen")
	await _hub()
	_check(_mark_text("team") == "Done" and _mark_text("training") == "To do", "Opening Team ticks its job")
	await _go("training")
	await _hub()
	_check(_mark_text("training") == "Done" and WC.left(_state) == 0, "Opening Training ticks its job")
	_state.save_career()
	_state.reset()
	_check(_state.load_career() and WC.left(_state) == 0, "The week's ticks survive save and load")
	_state.advance()
	var open := []
	for it in WC.items(_state):
		if not bool(it["done"]):
			open.append(str(it["key"]))
	_check(open.has("team") and open.has("training"), "A new week starts the list again (%s)" % [open])


func _test_hub_card_and_note() -> void:
	_fresh(true)
	await _hub()
	_check(_find("WeekJobs") != null and _find("BigCall") == null, "On: the card shows, the big call's slot shows nothing")
	var note: Label = _find("JobsLeftNote")
	_check(note != null and note.text == "2 jobs left this week", "Play shows a gentle note (%s)" % (note.text if note else "none"))
	var play: Button = _find("PlayMatch")
	_check(play != null and not play.disabled, "Jobs left never block Play match")
	_check(_find("SimRound") != null and not (_find("SimRound") as Button).disabled, "...or Sim the week")
	WC.mark(_state, "team")
	WC.mark(_state, "training")
	await _hub()
	_check(_find("JobsLeftNote") == null and _find("PlayMatch") != null, "No note once the jobs are done")


func _test_layout_sizes() -> void:
	for size in SIZES:
		root.size = size
		await _settle(2)
		_fresh(true)
		await _hub()
		var card: Control = _find("WeekJobs")
		var note: Control = _find("JobsLeftNote")
		var vw: float = float(current_scene.get_viewport_rect().size.x)
		_check(card != null and card.get_global_rect().position.x >= 0.0 and card.get_global_rect().end.x <= vw + 0.5,
				"%dx%d: the card sits inside the screen" % [size.x, size.y])
		_check(note != null and note.get_global_rect().end.x <= vw + 0.5 and note.is_visible_in_tree(),
				"%dx%d: the note sits inside the screen" % [size.x, size.y])
		for job in ["team", "training"]:
			var row: Control = _find("WeekJob_" + job)
			_check(row != null and row.size.y >= 44.0, "%dx%d: %s is a full tap target" % [size.x, size.y, job])
	root.size = SIZES[0]
	await _settle(2)


func _test_intro_text() -> void:
	for on in [false, true]:
		_fresh(on)
		_state.tutorials = true
		_state.set_setting("seen_weekly_loop_intro", false)
		await _hub()
		var intro := _find("WeeklyLoopIntro")
		var text := ""
		if intro != null:
			for l in intro.find_children("*", "Label", true, false):
				text += (l as Label).text + "\n"
		if on:
			_check(intro != null and not text.contains("no weekly checklist") and text.contains("never a gate"),
					"On: the weekly-loop intro tells of the list")
		else:
			_check(intro != null and text.contains("There is no weekly checklist to clear"),
					"Off: the weekly-loop intro is the old one")
		_state.set_setting("seen_weekly_loop_intro", true)
