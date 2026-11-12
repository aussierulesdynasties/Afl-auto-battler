extends RefCounted
## Run by tests/run_trainrep_tests.gd (suite "trainrep").
## The monthly training report (TrainingReport.gd, TrainingReportSheet.gd;
## director, 2026-10-14: "A report every 4 rounds"): the block snapshot, a
## known riser and his stats, the retraining list against the Training menu's
## own, an old save, and real taps on a phone and a PC.

var _tree: SceneTree
var checks := 0
var failures: Array[String] = []

const Tap := preload("res://tests/tap.gd")
const SUITE_SEED := 2027
const SIZES := [Vector2i(390, 844), Vector2i(1280, 720)]


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 6) -> void:
	for i in range(n):
		await _tree.process_frame


func _fresh() -> void:
	GameState.reset()
	GameState.start_season("FRE", GameDB.club_list("FRE"))
	GameState.replay_seed = SUITE_SEED
	GameState.tutorials = false
	# The club cards have their own test below: none opens over these unless asked.
	GameState.event_sheets = false
	Router.stack = []


func _rounds(n: int) -> void:
	for i in range(n):
		GameState.advance()


func _boost_potential(n: int) -> void:
	var made := 0
	for p in GameState.my_list:
		if made < n and int(p.get("potential", 0)) < 95:
			p["potential"] = 95
			made += 1


func run(tree: SceneTree) -> void:
	_tree = tree
	await _tree.process_frame
	GameState.autosave_enabled = false
	GameState.save_path = "user://test_trainrep.save"
	GameState.settings_path = "user://test_trainrep.cfg"
	GameState.delete_saved_career()
	_t("_test_snapshot_and_report")
	_t("_test_retrain_list")
	_t("_test_old_save")
	for size in SIZES:
		_tree.root.size = size
		await _settle()
		await _t("_test_taps", [size])
		await _t("_test_retrain_full", [size])
		await _t("_test_after_results", [size])
		await _t("_test_after_event_card", [size])
		await _t("_test_after_results_back", [size])
		await _t("_test_after_press", [size])
		await _t("_test_after_sit_down", [size])
		await _t("_test_after_carnival", [size])
	GameState.delete_saved_career()
	print(Ran.line("Training report", self))
	for f in failures:
		print("  FAIL: " + f)


func _test_snapshot_and_report() -> void:
	_fresh()
	var before := {}
	for p in GameState.my_list:
		before[str(p["id"])] = {"ovr": int(p["overall"]), "attr": (p["attr"] as Dictionary).duplicate()}
	_rounds(1)
	_check(not GameState.training_block.is_empty(), "the block begins with the first game")
	_check(int(GameState.training_block.get("from", 0)) == 1, "the block starts at round 1")
	var snap: Dictionary = GameState.training_block["players"]
	var same := true
	for id in before:
		if not snap.has(id) or int(snap[id]["ovr"]) != int(before[id]["ovr"]):
			same = false
	_check(same, "the block holds every player's rating from before the first game")
	_check(GameState.training_report.is_empty(), "no report before round 4")
	_rounds(3)
	var r: Dictionary = GameState.training_report
	_check(not r.is_empty(), "a report exists after round 4")
	_check(str(r.get("label", "")) == "Rounds 1-4", "it is Rounds 1-4, not %s" % str(r.get("label")))
	_check(GameState.training_block.is_empty(), "the block closes with the report")
	_check(TrainingReport.hub_due(GameState), "the new report is due to open over the hub")
	# The biggest riser by points, worked out here from the raw before and after.
	var best_id := ""
	var best_pts := 0
	for p in GameState.my_list:
		var id := str(p["id"])
		if not before.has(id):
			continue
		var pts := 0
		for row in GameState.TRAIN_STATS:
			var k := str(row[0])
			pts += maxi(0, int(round(float(p["attr"][k]))) - int(round(float(before[id]["attr"][k]))))
		if pts > best_pts:
			best_pts = pts
			best_id = id
	_check(best_id != "", "somebody improved in four rounds")
	var found := {}
	for e in r["risers"]:
		if str(e["id"]) == best_id:
			found = e
	_check(not found.is_empty() or (r["risers"] as Array).size() == TrainingReport.MAX_RISERS, "the biggest riser is in the report")
	if not found.is_empty():
		var ok := true
		for s in found["stats"]:
			var key := ""
			for row in GameState.TRAIN_STATS:
				if str(row[1]) == str(s[0]):
					key = str(row[0])
			var p: Dictionary = GameState.list_player(best_id)
			ok = ok and int(s[1]) == int(round(float(before[best_id]["attr"][key]))) and int(s[2]) == int(round(float(p["attr"][key])))
		_check(ok, "his stats read before to after exactly")
		_check(int(found["ovr0"]) == int(before[best_id]["ovr"]), "his rating before is the block's start")
	_check((r["risers"] as Array).size() <= TrainingReport.MAX_RISERS, "at most eight risers")
	var sorted_ok := true
	for i in range((r["risers"] as Array).size() - 1):
		var a: Dictionary = r["risers"][i]
		var b: Dictionary = r["risers"][i + 1]
		if int(a["ovr1"]) - int(a["ovr0"]) < int(b["ovr1"]) - int(b["ovr0"]):
			sorted_ok = false
	_check(sorted_ok, "most improved first")
	_rounds(1)
	_check(int(GameState.training_block.get("from", 0)) == 5, "the next block starts at round 5")
	_rounds(3)
	_check(str(GameState.training_report.get("label", "")) == "Rounds 5-8", "round 8 brings the next report")
	_check(not bool(GameState.training_report.get("dismissed", true)), "the new report is not dismissed")


func _test_retrain_list() -> void:
	_fresh()
	_boost_potential(3)
	_rounds(4)
	var r: Dictionary = GameState.training_report
	var rt := TrainingReport.retrain_list(GameState, r)
	var menu_ids := []
	for p in GameState.my_list:
		for k in GameState.plans_for(p):
			if str(k).begins_with(GameState.LEARN_PREFIX):
				menu_ids.append(str(p["id"]))
				break
	var ids := []
	for e in rt["entries"]:
		ids.append(str(e["id"]))
	_check(not ids.is_empty(), "somebody can learn a position")
	_check(GameState.active_projects() < GameState.PROJECT_MAX, "the club has a free project")
	var a := ids.duplicate()
	var b := menu_ids.duplicate()
	a.sort()
	b.sort()
	_check(a == b, "the report's list is the Training menu's own: %s vs %s" % [str(a), str(b)])
	_check(not bool(rt["full"]), "a free project: no limit note")
	for e in rt["entries"]:
		var p: Dictionary = GameState.list_player(str(e["id"]))
		var words := []
		for k in GameState.plans_for(p):
			if str(k).begins_with(GameState.LEARN_PREFIX):
				words.append(str(GameState.LEARN_JOBS[str(k).trim_prefix(GameState.LEARN_PREFIX)]["word"]))
		words.sort()
		var mine: Array = (e["jobs"] as Array).duplicate()
		mine.sort()
		_check(words == mine, "his jobs are the menu's: %s vs %s" % [str(mine), str(words)])
	# At the club's limit the menu offers nothing; the report still lists who could, and says why.
	var started := 0
	for p in GameState.my_list:
		if started < 2 and ids.has(str(p["id"])):
			GameState._start_project(p, str(GameState.open_jobs(p)[0]))
			started += 1
	_check(started == 2, "two projects started")
	var capped := TrainingReport.retrain_list(GameState, r)
	_check(bool(capped["full"]), "at the limit the report says so")
	var menu_any := false
	for p in GameState.my_list:
		for k in GameState.plans_for(p):
			if str(k).begins_with(GameState.LEARN_PREFIX) and GameState.project_job(p) == "":
				menu_any = true
	_check(not menu_any, "at the limit the menu offers no new project")
	var left := 0
	for e in capped["entries"]:
		var p: Dictionary = GameState.list_player(str(e["id"]))
		_check(GameState.project_job(p) == "", "nobody already learning is listed")
		left += 1
	_check(left == ids.size() - 2, "everyone else who could is still listed (%d of %d)" % [left, ids.size() - 2])
	var fresh_ok := true
	var seen_old := false
	for e in rt["entries"]:
		if bool(e["new"]) and seen_old:
			fresh_ok = false
		if not bool(e["new"]):
			seen_old = true
	_check(fresh_ok, "those who became available this month come first")


func _test_old_save() -> void:
	# A save from before the report has neither key: it loads with safe defaults.
	_fresh()
	_rounds(2)
	_check(GameState.save_career(), "a save is written")
	# Strip both keys, as a save written before the report has neither.
	var state := CareerSave.read(GameState.save_path)
	var meta := CareerSave.read_meta(GameState.save_path)
	state.erase("training_block")
	state.erase("training_report")
	_check(CareerSave.write(state, meta, GameState.save_path), "an old-style save is written")
	GameState.training_block = {"junk": 1}
	GameState.training_report = {"junk": 1}
	_check(GameState.load_career(), "an old save loads")
	_check(GameState.training_block.is_empty() and GameState.training_report.is_empty(), "absent keys load as empty")
	_rounds(2)
	_check(not GameState.training_report.is_empty(), "and the report carries on from it")
	_check(GameState.save_career(), "a new save is written")
	GameState.training_block = {}
	GameState.training_report = {}
	_check(GameState.load_career(), "the new save loads")
	_check(str(GameState.training_report.get("label", "")) == "Rounds 3-4", "the report round-trips (a save from mid-block starts its first block where it was loaded)")
	GameState.delete_saved_career()


func _on_screen(c: Control, size: Vector2i) -> bool:
	var r := c.get_global_rect()
	return r.position.x >= -0.5 and r.end.x <= size.x + 0.5


func _hub() -> Control:
	Router.stack = ["main"]
	Router.go("hub")
	await _settle(10)
	return _tree.current_scene


## A new report opens over the hub by itself, once; Close and Android Back put
## it away; Training keeps it.
func _test_taps(size: Vector2i) -> void:
	var tag := "%dx%d" % [size.x, size.y]
	_fresh()
	_boost_potential(2)
	_rounds(4)
	GameState.skip_media_conference()
	var hub := await _hub()
	_check(hub.find_child("TrainingReportCard", true, false) == null, "%s: no report line on the hub" % tag)
	var sheet := hub.find_child("TrainingReportSheet", true, false)
	_check(sheet != null, "%s: the new report opens over the hub" % tag)
	if sheet == null:
		return
	_check(not TrainingReport.hub_due(GameState), "%s: it counts as read once it opens" % tag)
	var risers: Array = GameState.training_report["risers"]
	var rid := str(risers[0]["id"]) if not risers.is_empty() else ""
	var name_b: Control = sheet.find_child("Name_" + rid, true, false) if rid != "" else null
	_check(name_b != null, "%s: the top riser is on the sheet" % tag)
	if name_b != null:
		_check(_on_screen(name_b, size), "%s: his name is on screen" % tag)
		_check(await Tap.tap(name_b) == "", "%s: a finger taps his name" % tag)
		await _settle(4)
		_check(hub.find_child("PlayerProfile", true, false) != null, "%s: his profile opens" % tag)
		Router.handle_back()
		await _settle(3)
		_check(hub.find_child("PlayerProfile", true, false) == null, "%s: Back closes the profile" % tag)
		_check(hub.find_child("TrainingReportSheet", true, false) != null, "%s: and leaves the report" % tag)
	var close: Control = hub.find_child("TrainingReportClose", true, false)
	_check(close != null and _on_screen(close, size), "%s: Close is on screen" % tag)
	_check(await Tap.tap(close) == "", "%s: a finger taps Close" % tag)
	await _settle(3)
	_check(hub.find_child("TrainingReportSheet", true, false) == null, "%s: Close closes it" % tag)
	await _settle(6)
	_check(hub.find_child("TrainingReportSheet", true, false) == null, "%s: it does not open again this visit" % tag)
	hub = await _hub()
	_check(hub.find_child("TrainingReportSheet", true, false) == null, "%s: nor on the next visit" % tag)
	# Android Back on an unread one.
	GameState.training_report["dismissed"] = false
	hub = await _hub()
	_check(hub.find_child("TrainingReportSheet", true, false) != null, "%s: an unread report opens" % tag)
	Router.handle_back()
	await _settle(3)
	_check(hub.find_child("TrainingReportSheet", true, false) == null and _tree.current_scene == hub, "%s: Android Back closes the report and stays on the hub" % tag)
	GameState.training_report["dismissed"] = false
	hub = await _hub()
	sheet = hub.find_child("TrainingReportSheet", true, false)
	var rt := TrainingReport.retrain_list(GameState, GameState.training_report)
	var entries: Array = rt["entries"]
	_check(not entries.is_empty(), "%s: somebody can retrain" % tag)
	_check(entries.is_empty() or sheet != null, "%s: the report reopens for the retraining entry" % tag)
	if not entries.is_empty() and sheet != null:
		var id0 := str(entries[0]["id"])
		var key0 := str(entries[0]["keys"][0])
		var word0 := str(entries[0]["jobs"][0])
		var row: Control = sheet.find_child("Retrain_" + id0, true, false)
		# Director, 2026-11-12: "i cant find the button to retrain them". Each
		# position he could learn is a button on the report, worded as the
		# choice it leads to.
		var nb: Control = row.find_child("Name_" + id0, true, false) if row != null else null
		var rb: Button = row.find_child("LearnGo_" + key0, true, false) as Button if row != null else null
		_check(rb != null, "%s: the report has a Learn button beside the player who can learn a position" % tag)
		_check(rb == null or rb.text.begins_with("Learn " + word0), "%s: it reads \"Learn %s\"" % [tag, word0])
		_check(rb == null or rb.size.y >= 44, "%s: it is a thumb tall" % tag)
		var all_have := true
		for e in entries:
			var er: Node = sheet.find_child("Retrain_" + str(e["id"]), true, false)
			for k in e["keys"]:
				if er == null or er.find_child("LearnGo_" + str(k), true, false) == null:
					all_have = false
		_check(all_have, "%s: every player the report names has a Learn button for every position it names" % tag)
		if nb != null:
			_check(await Tap.tap(nb) == "", "%s: a finger taps his name" % tag)
			await _settle(4)
			_check(hub.find_child("PlayerProfile", true, false) != null, "%s: his name opens his profile, as every name on the report does" % tag)
			Router.handle_back()
			await _settle(3)
		if rb != null:
			_check(await Tap.tap(rb) == "", "%s: a finger taps Learn %s" % [tag, word0])
			for i in range(60):
				await _tree.process_frame
			await _settle(6)
			var tr := _tree.current_scene
			_check(Router.current() == "training", "%s: it opens Training" % tag)
			var grid: Node = tr.find_child("PlayerLearn", true, false)
			_check(grid != null, "%s: on his new-position choices" % tag)
			var learn_b: Button = grid.find_child("PlayerLearn_" + GameState.LEARN_PREFIX + key0, false, false) as Button if grid != null else null
			_check(learn_b != null and learn_b.text == "Learn " + word0, "%s: his \"Learn %s\" choice is there" % [tag, word0])
			var cost: Control = tr.find_child("LearnCost", true, false)
			_check(cost != null, "%s: what learning costs is said before the tap" % tag)
			if learn_b != null:
				var r := learn_b.get_global_rect()
				_check(r.position.y >= 0.0 and r.end.y <= float(size.y) + 0.5, "%s: the choice is on screen without scrolling (%.0f-%.0f)" % [tag, r.position.y, r.end.y])
				_check(await Tap.tap(learn_b) == "", "%s: a finger taps Learn %s" % [tag, word0])
				await _settle(4)
				_check(GameState.project_job(GameState.list_player(id0)) == key0, "%s: he starts learning %s" % [tag, word0])
				_check(str(GameState.list_player(id0).get("train_plan", "")) == GameState.LEARN_PREFIX + key0, "%s: and it is his plan" % tag)
	# Training keeps the read report: Back to the list, then its line reopens it.
	if Router.current() != "training":
		Router.go("training")
		await _settle(8)
	var link := _tree.current_scene.find_child("TrainingReportLink", true, false)
	if link == null:
		Router.handle_back()
		await _settle(6)
		link = _tree.current_scene.find_child("TrainingReportLink", true, false)
	_check(link != null, "%s: Training keeps the read report" % tag)
	if link != null:
		_check(_on_screen(link, size), "%s: its line is on screen" % tag)
		_check(await Tap.tap(link) == "", "%s: a finger taps the line" % tag)
		await _settle(4)
		_check(_tree.current_scene.find_child("TrainingReportSheet", true, false) != null, "%s: the line opens the report" % tag)
		Router.handle_back()
		await _settle(3)
		_check(_tree.current_scene.find_child("TrainingReportSheet", true, false) == null, "%s: Back closes it in Training" % tag)


## The club already runs its two projects: the report still names who could
## learn, and his Training page says the same, naming who holds the places,
## instead of showing nothing (the report said yes, Training had no choice).
func _test_retrain_full(size: Vector2i) -> void:
	var tag := "%dx%d full" % [size.x, size.y]
	_fresh()
	_boost_potential(4)
	_rounds(4)
	GameState.skip_media_conference()
	var rt := TrainingReport.retrain_list(GameState, GameState.training_report)
	var entries: Array = rt["entries"]
	_check(entries.size() >= 3, "%s: three or more can learn (%d)" % [tag, entries.size()])
	if entries.size() < 3:
		return
	for i in range(2):
		var e: Dictionary = entries[entries.size() - 1 - i]
		GameState.set_player_plan(str(e["id"]), GameState.LEARN_PREFIX + str(e["keys"][0]))
	_check(GameState.active_projects() == GameState.PROJECT_MAX, "%s: the club runs two projects" % tag)
	rt = TrainingReport.retrain_list(GameState, GameState.training_report)
	entries = rt["entries"]
	_check(bool(rt["full"]) and not entries.is_empty(), "%s: the report says the club is full and still names who could learn" % tag)
	if entries.is_empty():
		return
	GameState.training_report["dismissed"] = false
	var hub := await _hub()
	var sheet := hub.find_child("TrainingReportSheet", true, false)
	_check(sheet != null and sheet.find_child("ReportRetrainFull", true, false) != null, "%s: the report says two are already learning" % tag)
	if sheet == null:
		return
	var id0 := str(entries[0]["id"])
	var rb: Control = sheet.find_child("LearnGo_" + str(entries[0]["keys"][0]), true, false)
	var row: Node = sheet.find_child("Retrain_" + id0, true, false)
	if row != null:
		rb = row.find_child("LearnGo_" + str(entries[0]["keys"][0]), true, false)
	_check(rb != null and await Tap.tap(rb) == "", "%s: a finger taps his Learn button" % tag)
	for i in range(60):
		await _tree.process_frame
	await _settle(6)
	var tr := _tree.current_scene
	_check(Router.current() == "training", "%s: it opens Training" % tag)
	var full: Label = tr.find_child("LearnFull", true, false) as Label
	_check(full != null, "%s: his page says why he cannot start yet" % tag)
	_check(tr.find_child("PlayerLearn", true, false) == null, "%s: and offers no choice it would refuse" % tag)
	if full != null:
		var named := 0
		for q in GameState.my_list:
			if GameState.project_job(q) != "" and full.text.contains(GameDB.player_display_name(q)):
				named += 1
		_check(named == 2, "%s: it names the two learning now (%s)" % [tag, full.text])
		var r := full.get_global_rect()
		_check(r.position.y >= 0.0 and r.end.y <= float(size.y) + 0.5, "%s: on screen without scrolling" % tag)


## The report lands with the round's results: the results come first, the
## report after Continue, never both at once.
func _test_after_results(size: Vector2i) -> void:
	var tag := "%dx%d results" % [size.x, size.y]
	_fresh()
	_rounds(3)
	GameState.skip_media_conference()
	var hub := await _hub()
	_check(hub.find_child("TrainingReportSheet", true, false) == null, "%s: no report before round 4" % tag)
	var sim: Control = hub.find_child("SimRound", true, false)
	_check(sim != null, "%s: Sim the week is there" % tag)
	if sim == null:
		return
	for sc in hub.find_children("*", "ScrollContainer", true, false):
		(sc as ScrollContainer).ensure_control_visible(sim)
	await _settle(2)
	_check(await Tap.tap(sim) == "", "%s: a finger taps Sim the week" % tag)
	await _settle(4)
	var go: Control = hub.find_child("SimConfirmGo", true, false)
	if go != null:
		_check(await Tap.tap(go) == "", "%s: a finger confirms the sim" % tag)
	for i in range(40):
		await _tree.process_frame
	_check(not GameState.training_report.is_empty(), "%s: the round lands the report" % tag)
	_check(hub.find_child("RoundResults", true, false) != null, "%s: the round's results open" % tag)
	_check(hub.find_child("TrainingReportSheet", true, false) == null, "%s: the report waits behind them" % tag)
	GameState.skip_media_conference()
	_check(await Tap.tap(hub.find_child("ResultsContinue", true, false)) == "", "%s: a finger taps Continue" % tag)
	await _settle(6)
	_check(hub.find_child("RoundResults", true, false) == null, "%s: the results close" % tag)
	_check(hub.find_child("TrainingReportSheet", true, false) != null, "%s: then the report opens" % tag)


## A new club card and a new report in the same visit: the card first, the
## report when it closes, never both at once.
func _test_after_event_card(size: Vector2i) -> void:
	var tag := "%dx%d card" % [size.x, size.y]
	_fresh()
	_rounds(4)
	GameState.skip_media_conference()
	GameState.event_sheets = true
	GameState.week_events = [GameState.story_card("members_open_training")]
	var hub := await _hub()
	_check(hub.find_child("EventSheet", true, false) != null, "%s: the new card opens first" % tag)
	_check(hub.find_child("TrainingReportSheet", true, false) == null, "%s: the report waits behind it" % tag)
	_check(TrainingReport.hub_due(GameState), "%s: and is still unread" % tag)
	var later: Control = hub.find_child("EventLater", true, false)
	_check(later != null, "%s: the card offers Later" % tag)
	if later == null:
		return
	_check(await Tap.tap(later) == "", "%s: a finger taps Later" % tag)
	await _settle(4)
	_check(hub.find_child("EventSheet", true, false) == null, "%s: the card closes" % tag)
	_check(hub.find_child("TrainingReportSheet", true, false) != null, "%s: then the report opens" % tag)


## Android Back on the round's results: the report still opens after them.
func _test_after_results_back(size: Vector2i) -> void:
	var tag := "%dx%d results, Back" % [size.x, size.y]
	_fresh()
	_rounds(3)
	GameState.skip_media_conference()
	var hub := await _hub()
	var sim: Control = hub.find_child("SimRound", true, false)
	_check(sim != null, "%s: Sim the week is there" % tag)
	if sim == null:
		return
	for sc in hub.find_children("*", "ScrollContainer", true, false):
		(sc as ScrollContainer).ensure_control_visible(sim)
	await _settle(2)
	_check(await Tap.tap(sim) == "", "%s: a finger taps Sim the week" % tag)
	await _settle(4)
	var go: Control = hub.find_child("SimConfirmGo", true, false)
	if go != null:
		_check(await Tap.tap(go) == "", "%s: a finger confirms the sim" % tag)
	for i in range(40):
		await _tree.process_frame
	_check(hub.find_child("RoundResults", true, false) != null, "%s: the round's results open" % tag)
	_check(hub.find_child("TrainingReportSheet", true, false) == null, "%s: the report waits behind them" % tag)
	GameState.skip_media_conference()
	Router.handle_back()
	await _settle(6)
	_check(_tree.current_scene == hub, "%s: Back stays on the hub" % tag)
	_check(hub.find_child("RoundResults", true, false) == null, "%s: Back closes the results" % tag)
	_check(hub.find_child("TrainingReportSheet", true, false) != null, "%s: then the report opens" % tag)


## The usual way a report lands: a match played, then the press conference on
## its own screen. The report waits for it and opens when the hub comes back.
func _test_after_press(size: Vector2i) -> void:
	var tag := "%dx%d press" % [size.x, size.y]
	_fresh()
	_rounds(4)
	var MC = load("res://scripts/sim/MediaConference.gd")
	GameState.media_conference = MC.pick({"club": "FRE", "opponent_name": "Melbourne", "round": 4,
			"result": {"home": "FRE", "away": "MEL", "score": [55, 101]}}, {})
	_check(GameState.media_conference_pending(), "%s: a question is waiting" % tag)
	var scene := await _hub()
	await _settle(30)
	scene = _tree.current_scene
	_check(scene.find_child("MediaConference", true, false) != null or scene.name == "MediaConference", "%s: the press conference comes first (%s)" % [tag, scene.name])
	_check(TrainingReport.hub_due(GameState), "%s: the report is still unread" % tag)
	var skip: Control = scene.find_child("MediaTopSkip", true, false)
	_check(skip != null, "%s: Skip is there" % tag)
	if skip == null:
		return
	_check(await Tap.tap(skip) == "", "%s: a finger taps Skip" % tag)
	for i in range(60):
		await _tree.process_frame
	await _settle(10)
	var hub := _tree.current_scene
	_check(Router.current() == "hub", "%s: back on the hub (%s)" % [tag, Router.current()])
	var sheet := hub.find_child("TrainingReportSheet", true, false)
	_check(sheet != null, "%s: then the report opens" % tag)
	if sheet != null:
		_check(await Tap.tap(hub.find_child("TrainingReportClose", true, false)) == "", "%s: a finger taps Close" % tag)
		await _settle(3)
		_check(hub.find_child("TrainingReportSheet", true, false) == null, "%s: Close closes it" % tag)


## A sit-down in the same visit: the sit-down first, the report after Done.
func _test_after_sit_down(size: Vector2i) -> void:
	var tag := "%dx%d sit-down" % [size.x, size.y]
	_fresh()
	_rounds(4)
	GameState.skip_media_conference()
	GameState.backing_talk = {"player_id": str(GameState.my_list[0]["id"]), "title": "Sit-down", "lines": ["He took it well."]}
	var hub := await _hub()
	_check(hub.find_child("BackingTalk", true, false) != null, "%s: the sit-down opens first" % tag)
	_check(hub.find_child("TrainingReportSheet", true, false) == null, "%s: the report waits behind it" % tag)
	var done: Control = hub.find_child("BackingTalkDone", true, false)
	if done == null:
		return
	_check(await Tap.tap(done) == "", "%s: a finger taps Done" % tag)
	await _settle(4)
	_check(hub.find_child("BackingTalk", true, false) == null, "%s: the sit-down closes" % tag)
	_check(hub.find_child("TrainingReportSheet", true, false) != null, "%s: then the report opens" % tag)


## The carnival in the same visit: the carnival first, the report after Done.
func _test_after_carnival(size: Vector2i) -> void:
	var tag := "%dx%d carnival" % [size.x, size.y]
	_fresh()
	_rounds(4)
	GameState.skip_media_conference()
	GameState.midseason = {"year": GameState.season_year, "carnival_seen": false,
			"carnival": [{"name": "Riley Bowman", "pos": "midfielder", "state": "Vic Metro"}]}
	var hub := await _hub()
	_check(hub.find_child("CarnivalWeek", true, false) != null, "%s: the carnival opens first" % tag)
	_check(hub.find_child("TrainingReportSheet", true, false) == null, "%s: the report waits behind it" % tag)
	var done: Control = hub.find_child("CarnivalDone", true, false)
	if done == null:
		return
	_check(await Tap.tap(done) == "", "%s: a finger taps Done" % tag)
	await _settle(4)
	_check(hub.find_child("CarnivalWeek", true, false) == null, "%s: the carnival closes" % tag)
	_check(hub.find_child("TrainingReportSheet", true, false) != null, "%s: then the report opens" % tag)
