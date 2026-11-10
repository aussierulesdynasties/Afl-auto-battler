extends RefCounted
## Row 54: the under-18 carnival week and the mid-season rookie draft
## (MidseasonDraft). A seeded career plays to round
## 10 (carnival) and 11 (draft); each beat survives a save and load, the hub
## sheets take a real tap, and Sim the week passes an unmade pick.
## Run through run_midseason_draft_tests.gd.

const Tap := preload("res://tests/tap.gd")
const SEED := 5402

var failures: Array[String] = []
var checks := 0
var root: Window
var _tree: SceneTree
var gs
var reached_end := false


func _check(ok: bool, msg: String) -> void:
	checks += 1
	if not ok:
		failures.append(msg)
		push_error(msg)


func _settle() -> void:
	for i in 4:
		await _tree.process_frame


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func run(tree: SceneTree) -> void:
	root = tree.root
	_tree = tree
	gs = GameState
	failures.clear()
	checks = 0
	root.size = Vector2i(390, 844)
	GameState.replay_seed = SEED
	await _t("_test_carnival_and_draft")
	_check(reached_end, "The carnival-and-draft test ran to its end")
	GameState.replay_seed = 0
	print(Ran.line("Midseason draft", self))


func _new_career() -> void:
	gs.reset()
	gs.start_season("GEE", GameDB.club_list("GEE"))
	gs.set_setting("seen_weekly_loop_intro", true)


func _play_to(round_no: int) -> void:
	var guard := 0
	while gs.season.round_index < round_no and guard < 40:
		gs.advance()
		guard += 1


func _test_carnival_and_draft() -> void:
	_new_career()
	var year: int = gs.season_year
	# One overlooked prospect from last year's class, so the pool has both kinds.
	var class_now: Array = gs.draftee_pool.filter(func(p): return int(p.get("draft_year", year)) == year)
	_check(class_now.size() >= MidseasonDraft.STARS, "This year's class is in the pool (%d)" % class_now.size())
	if class_now.size() < 30:
		return
	# Last year's leftovers: enough passed-over prospects that every club ahead
	# of us can pick and some are left for our turn. The best goes first.
	for i in 25:
		(class_now[class_now.size() - 1 - i] as Dictionary)["draft_year"] = year - 1
	var old: Dictionary = class_now[class_now.size() - 1]
	old["overall"] = 99   # so an AI club is sure to take him
	var old_id := str(old["id"])

	_play_to(MidseasonDraft.CARNIVAL_AFTER)
	var stars: Array = gs.midseason.get("carnival", [])
	_check(stars.size() == MidseasonDraft.STARS, "Carnival names three (%d)" % stars.size())
	for s in stars:
		_check(str(s["id"]) != old_id, "An overlooked prospect is not in the carnival")
		_check(str(s["pos"]) != "" and str(s["state"]) != "", "Each star has a position and a state: %s" % str(s))
	_check(gs.news.any(func(n): return str(n.get("kind", "")) == "carnival") if gs.get("news") is Array else true,
			"The carnival is in the news")

	# Save and load across the carnival.
	_check(gs.save_career(), "Saves after the carnival")
	gs.midseason = {}
	_check(gs.load_career(), "Loads after the carnival")
	_check((gs.midseason.get("carnival", []) as Array).size() == MidseasonDraft.STARS, "The carnival survives a load")
	_check(not MidseasonDraft.carnival_lines(gs).is_empty(), "Unseen after a load, so the hub still shows it")

	# The hub sheet, by a real tap.
	# The week's club cards have already opened over the hub (Later).
	for popped_card in gs.week_events:
		(popped_card as Dictionary)["popped"] = true
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	_check(hub.find_child("CarnivalWeek", true, false) != null, "The hub opens the carnival sheet")
	var done: Control = hub.find_child("CarnivalDone", true, false)
	var why: String = await Tap.tap(done)
	_check(why == "", "Done takes a real tap: %s" % why)
	await _settle()
	_check(MidseasonDraft.carnival_lines(gs).is_empty(), "Seen once closed")
	hub.queue_free()
	await _settle()

	# Room on our list, so we are in the draft.
	while (gs.season.lists["GEE"] as Array).size() >= Contracts.MAX_LIST:
		(gs.season.lists["GEE"] as Array).pop_back()
	var sizes := {}
	for code in gs.season.lists:
		sizes[code] = (gs.season.lists[code] as Array).size()

	_play_to(MidseasonDraft.DRAFT_AFTER)
	var rec: Dictionary = gs.midseason
	var order: Array = rec.get("order", [])
	_check(order.has("GEE"), "We have a list spot, so we pick")
	for code in sizes:
		_check(order.has(code) == (int(sizes[code]) < Contracts.MAX_LIST), "%s in the order only with a list spot" % code)
	var ladder: Array = gs.season.ladder_sorted()
	var by_ladder := []
	for i in range(ladder.size() - 1, -1, -1):
		if order.has(str(ladder[i]["code"])):
			by_ladder.append(str(ladder[i]["code"]))
	_check(by_ladder == order, "Reverse-ladder order")
	_check(MidseasonDraft.waiting(gs), "The draft waits on our pick")
	var picks: Array = rec.get("picks", [])
	for k in picks:
		var club := str(k["club"])
		var p = null
		for q in gs.season.lists[club]:
			if str(q["id"]) == str(k["id"]):
				p = q
		_check(p != null, "%s's pick is on its list" % club)
		if p != null:
			_check(int(p["contract_years"]) == 2, "A rookie deal to the end of next season")
	var best_left := 0
	for q in MidseasonDraft.pool(gs):
		best_left = maxi(best_left, int(q.get("overall", 0)))
	var taken := []
	for k in picks:
		for q in gs.season.lists[str(k["club"])]:
			if str(q["id"]) == str(k["id"]):
				taken.append(int(q.get("overall", 0)))
	_check(taken.all(func(o): return o >= best_left), "Each club ahead of us took a player rated at least as high as any left")

	# Save and load with our pick waiting.
	_check(gs.save_career(), "Saves with our pick waiting")
	var next_before := int(gs.midseason["next"])
	gs.midseason = {}
	_check(gs.load_career(), "Loads with our pick waiting")
	_check(MidseasonDraft.waiting(gs) and int(gs.midseason["next"]) == next_before, "The waiting pick survives a load")

	# Pick by a real tap.
	var before: int = (gs.season.lists["GEE"] as Array).size()
	var left := MidseasonDraft.pool(gs)
	_check(not left.is_empty(), "Players are left for our pick")
	if left.is_empty():
		return
	var top: Dictionary = left[0]
	# The week's club cards have already opened over the hub (Later).
	for popped_card in gs.week_events:
		(popped_card as Dictionary)["popped"] = true
	hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	var pick_btn: Control = hub.find_child("MidseasonPick_%s" % str(top["id"]), true, false)
	why = await Tap.tap(pick_btn)
	_check(why == "", "Pick takes a real tap: %s" % why)
	await _settle()
	_check((gs.season.lists["GEE"] as Array).size() == before + 1, "Our pick joins the list")
	_check(gs.season.lists["GEE"].any(func(q): return str(q["id"]) == str(top["id"])), "The one we tapped")
	_check(bool(gs.midseason.get("done", false)), "The draft finishes after our pick")
	_check(not gs.draftee_pool.has(top) and not gs.free_agents.has(top), "He leaves the pool")
	hub.queue_free()
	await _settle()

	# Sim the week passes an unmade pick.
	_check(gs.load_career(), "Back to the waiting pick")
	_check(MidseasonDraft.waiting(gs), "Waiting again")
	before = (gs.season.lists["GEE"] as Array).size()
	gs.advance()
	_check(bool(gs.midseason.get("done", false)), "Sim the week settles the draft")
	_check(not gs.midseason["picks"].any(func(k): return str(k["club"]) == "GEE"), "Our unmade pick was passed")
	# Nobody left to take: the hub passes the pick itself and opens no card
	# with only Pass on it (director, 2026-11-07); the news says why.
	_check(gs.load_career(), "Back to the waiting pick, once more")
	_check(MidseasonDraft.waiting(gs), "Waiting before the pool empties")
	gs.free_agents.clear()
	gs.draftee_pool = gs.draftee_pool.filter(func(q): return int(q.get("draft_year", gs.season_year)) >= gs.season_year)
	_check(MidseasonDraft.pool(gs).is_empty(), "Nobody left to take")
	# The week's club cards have already opened over the hub (Later).
	for popped_card in gs.week_events:
		(popped_card as Dictionary)["popped"] = true
	hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	_check(hub.find_child("MidseasonDraft", true, false) == null, "No draft card when there is no choice to make")
	_check(not MidseasonDraft.waiting(gs) and bool(gs.midseason.get("done", false)), "The pick passed by itself")
	_check(gs.news.any(func(n): return str(n["text"]) in [MidseasonDraft.NOBODY_LEFT_NEWS, MidseasonDraft.NOBODY_AT_ALL_NEWS]),
			"The news says the pick passed with nobody left")
	_check(not (gs.news.any(func(n): return str(n["text"]) == "Mid-season rookie draft: no club took a player.")
			and gs.news.any(func(n): return str(n["text"]) == MidseasonDraft.NOBODY_LEFT_NEWS)),
			"Never 'no club took a player' and 'nobody was left' side by side")
	hub.queue_free()
	await _settle()
	# Next season the record starts again.
	_check(int(gs.midseason.get("year", 0)) == gs.season_year, "Record is this season's")
	reached_end = true
