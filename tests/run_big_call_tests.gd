extends SceneTree
## godot --headless --path . --script tests/run_big_call_tests.gd
## The Hub's weekly "one big call" (director 2026-11-03, plan 3a): a due
## coach-arc beat, else the most pressing of the press, an assistant approach,
## a captaincy vacancy, backing a young player, a captaincy review, read from
## real state; one per week, kept through save/load; on in every career.

var _state: Node
var _router: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []

const WC := preload("res://scripts/state/WeekChecklist.gd")
const Tap := preload("res://tests/tap.gd")
const SUITE_SEED := 2027
var BigCalls


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)

const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_router = root.get_node("Router")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://test_big_call.save"
	_state.settings_path = "user://test_big_call.cfg"
	BigCalls = load("res://scripts/state/BigCalls.gd")
	_state.delete_saved_career()
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	await _t("_test_backing_from_state")
	await _t("_test_priority_and_one_per_week")
	await _t("_test_captaincy")
	await _t("_test_arc_beat_first")
	await _t("_test_save_load")
	await _t("_test_hub_row")
	await _t("_test_every_kind_routes")
	_state.delete_saved_career()
	print(Ran.line("Big call", self))
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
	_state.media_conference = {}
	_state.coach_approaches = []


func _next_week() -> void:
	_state.week_checks = {"week": -99, "done": {}, "seen": {}}


func _test_backing_from_state() -> void:
	_fresh()
	# Out of the box no MEL youngster is near the side: no backing call.
	var young: Dictionary = BigCalls.ready_to_back(_state)
	var kid := {}
	for p in _state.club_roster("MEL"):
		if _state.can_back(p):
			kid = p
	_check(not kid.is_empty(), "MEL has a young player who could be backed")
	if kid.is_empty():
		return
	if young.is_empty():
		_check(not BigCalls.candidates(_state).has("backing"), "Nobody ready: no backing call")
		kid["overall"] = 99
		young = BigCalls.ready_to_back(_state)
	_check(str(young.get("id", "")) == str(kid["id"]) or int(young.get("overall", 0)) >= int(kid["overall"]),
			"His form lifts him to the side's level: he is the one ready")
	_check(not young.is_empty(), "A young player ready to hold a spot")
	if young.is_empty():
		return
	_check(_state.can_back(young), "The pick can really be backed")
	var c := WC.big_call(_state)
	_check(str(c.get("kind", "")) == "backing" and str(c.get("route", "")) == "selection",
			"With nothing else due, the call is backing him: %s" % str(c))
	_check(not bool(c.get("done", true)), "Not done before he is backed")
	_state.back_player(str(young["id"]))
	c = WC.big_call(_state)
	_check(str(c.get("kind", "")) == "backing" and bool(c.get("done", false)),
			"Backed: the call is ticked, still this week's")
	for p in _state.club_roster("MEL"):
		if _state.can_back(p):
			p["overall"] = 1
	_check(BigCalls.ready_to_back(_state).is_empty(), "Weak young players are not ready")


func _test_priority_and_one_per_week() -> void:
	_fresh()
	var cid := ""
	for k in _state.coaches:
		if str(_state.coaches[k].get("club", "")) == "MEL":
			cid = str(k)
			break
	_state.coach_approaches = [{"cid": cid, "from_job": "MD", "club": "GEE", "job": "SA",
			"choice": "", "kept": false, "text": ""}]
	_state.media_conference = {"key": "x", "round": 1}
	var c := WC.big_call(_state)
	_check(str(c.get("kind", "")) == "press", "Press first when pending: %s" % str(c))
	_state.media_conference = {}
	c = WC.big_call(_state)
	_check(str(c.get("kind", "")) == "press" and bool(c.get("done", false)),
			"One call all week, ticked when answered")
	_next_week()
	c = WC.big_call(_state)
	_check(str(c.get("kind", "")) == "approach", "Next week: the approach: %s" % str(c))
	_check(str(c.get("text", "")).contains(_db.club_name("GEE")), "Approach call names the club")
	_state.coach_approaches[0]["choice"] = "go"
	_check(bool(WC.big_call(_state).get("done", false)), "Answered approach: ticked")


func _test_captaincy() -> void:
	_fresh()
	if not _state.captaincy.has("MEL"):
		_state._captaincy_refresh()
	var rec: Dictionary = _state.captaincy.get("MEL", {})
	rec["slots"] = []
	rec["seeded"] = true
	_state.captaincy["MEL"] = rec
	_check(BigCalls.candidates(_state).has("captain_vacant"), "No captain: a vacancy call")
	var c := WC.big_call(_state)
	_check(str(c.get("kind", "")) == "captain_vacant" and str(c.get("route", "")) == "list",
			"Vacancy outranks backing: %s" % str(c))
	var roster: Array = _state.club_roster("MEL")
	rec["slots"] = [{"id": str(roster[0]["id"]), "role": "captain"}]
	_check(bool(WC.big_call(_state).get("done", false)), "Captain named: ticked")
	rec["since"] = _state.season_year - 1
	_next_week()
	var live: Dictionary = BigCalls.candidates(_state)
	_check(live.has("captain_review") == (not _state.captaincy_mid_season()),
			"Review only before the season starts")
	if live.has("captain_review"):
		_check(not BigCalls.done(_state, "captain_review", ""), "Review open until the page is opened")
		WC.mark(_state, "captaincy")
		_check(BigCalls.done(_state, "captain_review", ""), "Review ticked once the captaincy page is opened")


func _test_arc_beat_first() -> void:
	_fresh()
	_state.week_events = [{"coach_arc": "hot_seat", "title": "The board wants a word", "resolved": false}]
	var c := WC.big_call(_state)
	_check(str(c.get("text", "")) == "The board wants a word" and c.has("card"),
			"A due arc beat is the call: %s" % str(c))
	_check(not (_state.week_checks as Dictionary).has("big_call"), "An arc beat holds no candidate")
	_state.week_events = []


func _test_save_load() -> void:
	_fresh()
	_state.media_conference = {"key": "x", "round": 1}
	_check(str(WC.big_call(_state).get("kind", "")) == "press", "Press call before save")
	_state.media_conference = {}
	_check(_state.save_career(), "Saved")
	_state.reset()
	_check(_state.load_career(), "Loaded")
	var c := WC.big_call(_state)
	_check(str(c.get("kind", "")) == "press" and bool(c.get("done", false)),
			"After load: the same call, still ticked: %s" % str(c))
	_state.delete_saved_career()


func _test_hub_row() -> void:
	_fresh()
	var rec: Dictionary = _state.captaincy.get("MEL", {})
	rec["slots"] = []
	rec["seeded"] = true
	_state.captaincy["MEL"] = rec
	_router.stack = []
	_router.go("hub")
	for i in range(8):
		await process_frame
	var bc := current_scene.find_child("BigCall", true, false)
	_check(bc != null, "The Hub shows the big call row")
	if bc != null:
		_check(str((bc as Button).tooltip_text) == str(WC.big_call(_state).get("text", "")),
				"The row is this week's call")
		# A real finger on the call reaches its screen (row 51).
		var route := str(WC.big_call(_state).get("route", ""))
		var size := root.size
		root.size = Vector2i(390, 844)
		for i in range(4):
			await process_frame
		var why: String = await Tap.tap(current_scene.find_child("BigCall", true, false) as Control)
		for i in range(8):
			await process_frame
		_check(why == "" and route != "" and _router.current() == route, "Phone: a tap on the big call opens its screen (%s)" % why)
		root.size = size


## Every big-call kind has a route the Router knows, so its Hub row can be tapped.
func _test_every_kind_routes() -> void:
	_fresh()
	var cid := ""
	for k in _state.coaches:
		if str(_state.coaches[k].get("club", "")) == "MEL":
			cid = str(k)
			break
	_state.coach_approaches = [{"cid": cid, "from_job": "MD", "club": "GEE", "job": "SA",
			"choice": "", "kept": false, "text": ""}]
	_state.media_conference = {"key": "x", "round": 1}
	var rec: Dictionary = _state.captaincy.get("MEL", {})
	rec["slots"] = []
	rec["seeded"] = true
	_state.captaincy["MEL"] = rec
	var cands: Dictionary = BigCalls.candidates(_state)
	for kind in ["press", "approach", "captain_vacant"]:
		_check(cands.has(kind), "Candidate %s is live for the route check" % kind)
	for kind in cands:
		var route := str((cands[kind] as Dictionary).get("route", ""))
		_check(route != "" and _router.SCENES.has(route), "Big call %s has a valid route: '%s'" % [kind, route])
	# Kinds not live in this state (backing, captain_review) are still held to it in source.
	var src := FileAccess.get_file_as_string("res://scripts/state/BigCalls.gd")
	_check(not src.contains("\"route\": \"\""), "No big call is built with an empty route")
	for kind in BigCalls.ORDER:
		_check(src.contains("out[\"%s\"]" % kind), "Big call kind %s is built in candidates()" % kind)
