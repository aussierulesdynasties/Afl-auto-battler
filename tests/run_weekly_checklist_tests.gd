extends SceneTree
## godot --headless --path . --script tests/run_weekly_checklist_tests.gd
## The Hub's weekly checklist (WeekChecklist.gd; director, 2026-11-03; on in
## every career since TODO row 51): jobs read from real state, ticked when
## done, one tap to their screen, the big call's slot empty until the coach
## arcs fill it, never a block on Play.

var _state: Node
var _router: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []

const WC := preload("res://scripts/state/WeekChecklist.gd")
const Tap := preload("res://tests/tap.gd")
const SUITE_SEED := 2027
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
	await _t("_test_on_in_a_normal_career")
	await _t("_test_items_reflect_state")
	await _t("_test_ticks_on_completion")
	await _t("_test_hub_card_and_note")
	await _t("_test_layout_sizes")
	await _t("_test_intro_text")
	await _t("_test_real_taps_on_a_phone")
	print(Ran.line("Weekly checklist", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


func _fresh() -> void:
	_state.reset()
	_state.career_seed = SUITE_SEED
	_state.replay_seed = SUITE_SEED
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


## No setting to turn on (row 51): a plain new career has the list, the
## Hub card, the Team Confirm side button, and Play match still there.
func _test_on_in_a_normal_career() -> void:
	_fresh()
	_check(not WC.items(_state).is_empty() and WC.left(_state) > 0,
			"A normal career has this week's jobs")
	await _hub()
	_check(_find("WeekJobs") != null and _find("PlayMatch") != null,
			"A normal career: the Hub shows the checklist and Play match")
	await _go("selection")
	_check(_find("ConfirmSide") != null, "A normal career: Team has the Confirm side button")


func _test_items_reflect_state() -> void:
	_fresh()
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
	_fresh()
	await _hub()
	_check(_mark_text("team") == "To do" and _mark_text("training") == "To do", "Both jobs start open on the Hub")
	var team: Button = _find("WeekJob_team")
	if team != null:
		team.emit_signal("pressed")
		await _settle()
	_check(_router.current() == "selection", "Tapping a job opens its screen")
	await _hub()
	_check(_mark_text("team") == "To do", "Merely opening Team does not tick its job")
	await _go("selection")
	var confirm: Button = _find("ConfirmSide")
	_check(confirm != null and not confirm.disabled and confirm.text == "Confirm side", "Team shows Confirm side")
	if confirm != null:
		confirm.emit_signal("pressed")
		await _settle()
	confirm = _find("ConfirmSide")
	_check(confirm != null and confirm.disabled and confirm.text == "Confirmed", "Pressed, it reads Confirmed")
	await _hub()
	_check(_mark_text("team") == "Done" and _mark_text("training") == "To do", "Confirm side ticks its job")
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
	_fresh()
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
		_fresh()
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
		await _go("selection")
		var cb: Control = _find("ConfirmSide")
		var r := cb.get_global_rect() if cb != null else Rect2()
		var vh: float = float(current_scene.get_viewport_rect().size.y)
		_check(cb != null and cb.is_visible_in_tree() and r.size.y >= 44.0 and r.position.x >= 0.0
				and r.end.x <= vw + 0.5 and r.end.y <= vh + 0.5,
				"%dx%d: Confirm side is on screen, a full tap target (%s)" % [size.x, size.y, r])
	root.size = SIZES[0]
	await _settle(2)


func _test_intro_text() -> void:
	_fresh()
	_state.tutorials = true
	_state.set_setting("seen_weekly_loop_intro", false)
	await _hub()
	var intro := _find("WeeklyLoopIntro")
	var text := ""
	if intro != null:
		for l in intro.find_children("*", "Label", true, false):
			text += (l as Label).text + "
"
	_check(intro != null and not text.contains("no weekly checklist") and text.contains("never a gate"),
			"The weekly-loop intro tells of the list")
	_state.set_setting("seen_weekly_loop_intro", true)


## Real taps at a phone's size (row 51): a finger on the Hub's job reaches
## Team, a finger on Confirm side ticks it, and back on the Hub it shows Done.
func _test_real_taps_on_a_phone() -> void:
	_fresh()
	root.size = SIZES[1]
	await _hub()
	# A finger taps a screen that has stopped moving (late cards settle first).
	await Tap.steady(_find("WeekJob_team") as Control)
	var why: String = await Tap.tap(_find("WeekJob_team") as Control)
	await _settle()
	_check(why == "" and _router.current() == "selection", "Phone: a tap on Look over the side opens Team (%s)" % why)
	await Tap.steady(_find("ConfirmSide") as Control)
	var confirm := _find("ConfirmSide") as Control
	var vw := float(current_scene.get_viewport_rect().size.x)
	_check(confirm != null and confirm.get_global_rect().end.x <= vw + 0.5,
			"Phone: Confirm side sits inside the screen's width")
	why = await Tap.tap(confirm)
	await _settle()
	_check(why == "" and WC.is_done(_state, "team"), "Phone: a tap on Confirm side ticks the job (%s)" % why)
	await _hub()
	_check(_mark_text("team") == "Done", "Phone: back on the Hub, Look over the side shows Done")
	await _go("selection")
	var page := _find("SidePage") as Control
	_check(page != null and page.get_global_rect().end.x <= float(current_scene.get_viewport_rect().size.x) + 0.5,
			"Phone: once confirmed, Team still fits the screen's width")
	root.size = SIZES[0]
	await _settle(2)
