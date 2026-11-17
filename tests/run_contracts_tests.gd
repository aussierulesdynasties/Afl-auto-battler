extends SceneTree
## godot --headless --path . --script tests/run_contracts_tests.gd
## Run a headless editor import first on a fresh clone to register global classes.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_isolate_saves()
	# A suite that fails to compile must fail the run, not hang it.
	var script = load("res://tests/test_contracts.gd")
	if script == null or not script.can_instantiate():
		push_error("Could not load res://tests/test_contracts.gd")
		quit(1)
		return
	var suite = script.new()
	suite.run()
	var tap_fail := await _tap_career_end_card()
	if tap_fail != "":
		push_error(tap_fail)
	else:
		print("Contracts: real taps ask him to retire, he refuses, and the second card delists him")
	quit(0 if suite.failures.is_empty() and tap_fail == "" else 1)


const Tap := preload("res://tests/tap.gd")


## The end-of-career card on the hub (CareerEnd), answered with real taps:
## Ask him to retire (he refuses), Done, then Delist him on the second card.
func _tap_career_end_card() -> String:
	var CareerEnd = load("res://scripts/state/CareerEnd.gd")
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	gs.reset()
	gs.start_season("GEE", db.club_list("GEE"))
	gs.set_setting("seen_weekly_loop_intro", true)
	gs.media_conference = {}
	var p: Dictionary = gs.my_list[0]
	p["age"] = 24.0
	p["real_last"] = gs.season_year - 1
	p["injury_weeks"] = 0
	p["morale"] = 80
	gs.season_tally[str(p["id"])] = {"games": 20}
	var year: int = gs.season_year + 1
	var seed := 1
	while seed < 5000:
		var rng := RandomNumberGenerator.new()
		rng.seed = hash("career_end|%s|%d|%d" % [str(p["id"]), year, seed])
		if rng.randf() < 0.4:
			break
		seed += 1
	gs.career_seed = seed
	gs.week_events = [CareerEnd.card(gs, p)]
	router.go("hub")
	var sheet: Node = await _sheet()
	if sheet == null:
		return "The end-of-career card does not open on the hub (scene %s)" % str(current_scene)
	var why: String = await Tap.tap(sheet.find_child("Event_0", true, false))
	for i in range(4):
		await process_frame
	var done: Button = sheet.find_child("EventDone", true, false)
	if why != "" or done == null:
		return "A real tap on Ask him to retire did not answer the card (tap: %s)" % why
	why = await Tap.tap(done)
	for i in range(4):
		await process_frame
	sheet = await _sheet()
	if sheet == null or gs.week_events.size() < 2:
		return "After he refused, the second card did not open (%d cards, tap: %s)" % [gs.week_events.size(), why]
	why = await Tap.tap(sheet.find_child("Event_0", true, false))
	for i in range(4):
		await process_frame
	var talk: Dictionary = p.get("end_talk", {})
	if why != "" or str(talk.get("call", "")) != "delist" or not bool(gs.week_events[1].get("resolved", false)):
		return "A real tap on Delist him did not delist him (tap: %s, call %s)" % [why, str(talk.get("call", ""))]
	return ""


## The open card sheet on the hub, once it has loaded (null if none opens).
func _sheet() -> Node:
	for i in range(900):
		await process_frame
		if current_scene != null:
			var s: Node = current_scene.find_child("EventSheet", true, false)
			if s != null:
				for j in range(10):
					await process_frame
				return s
	return null


## Never touch a real career save or settings file from a test run.
func _isolate_saves() -> void:
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://test_career.save"
	gs.settings_path = "user://test_settings.cfg"
