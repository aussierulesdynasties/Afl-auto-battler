extends RefCounted
## Row 88: the rookie list (RookieList, switch `rookie_list`). A seeded career
## rolls over through the National Draft, which now fills the senior list
## only; the Rookie Draft follows and fills the rookie spots. A rookie is
## upgraded to the senior list (refused while it is full), an old save loads
## with everyone on the senior list, the list screen shows both lists and
## the Rookie Draft sheet and the upgrade take real taps.
## Run through run_rookie_list_tests.gd.

const Tap := preload("res://tests/tap.gd")
const SEED := 8801
const CLUB := "ADE"

var failures: Array[String] = []
var checks := 0
var root: Window
var _tree: SceneTree
var gs


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
	_t("_test_switch_off")
	_t("_test_rollover_on")
	_t("_test_upgrade")
	_t("_test_old_save")
	await _t("_test_rookie_draft_tap")
	await _t("_test_list_screen_and_upgrade_tap")
	_t("_test_release_and_resign")
	_t("_test_entering_club_seat")
	_t("_test_midseason_fills_rookie_spots")
	_t("_test_real_lists_start")
	Features.set_on(RookieList.SWITCH, false)
	GameState.replay_seed = 0
	print(Ran.line("Rookie list", self))


func _new_career() -> void:
	gs.reset()
	gs.start_season(CLUB, GameDB.club_list(CLUB))
	gs.set_setting("seen_weekly_loop_intro", true)
	gs.tutorials = false


## A career at the end of its first home-and-away, through the National Draft
## (every pick made the way a rival makes it) and the rollover.
func _rollover() -> Draft:
	_new_career()
	gs.season.round_index = gs.season.fixture.size()
	if not gs.begin_intake_draft():
		return null
	var draft: Draft = gs.draft
	while not draft.is_finished():
		var candidate := draft._best_ai_pick(draft.current_club())
		if candidate.is_empty() or not draft._draft_pick(draft.current_club(), candidate):
			draft._skip_current_pick()
	if not gs.finish_intake_draft():
		return null
	return draft


func _test_switch_off() -> void:
	Features.set_on(RookieList.SWITCH, false)
	var draft := _rollover()
	_check(draft != null, "Switch off: the rollover commits")
	if draft == null:
		return
	_check(draft.senior_cap == 0, "Switch off: the National Draft fills the whole list")
	_check(gs.rookie_draft.is_empty(), "Switch off: no Rookie Draft is written (%s)" % str(gs.rookie_draft))
	var keyed := 0
	for code in gs.league_lists:
		for p in gs.league_lists[code]:
			if p.has("rookie_list"):
				keyed += 1
	_check(keyed == 0, "Switch off: nobody is put on a rookie list (%d)" % keyed)
	_check(not RookieList.waiting(gs), "Switch off: no pick waits")
	_check(gs.save_career() and gs.load_career() and gs.rookie_draft.is_empty(),
			"Switch off: a save and load writes no Rookie Draft")


func _test_rollover_on() -> void:
	Features.set_on(RookieList.SWITCH, true)
	var draft := _rollover()
	_check(draft != null, "The rollover commits with the rookie list on")
	if draft == null:
		return
	_check(draft.senior_cap == RookieList.SENIOR_SPOTS, "The National Draft fills the senior list (38)")
	# No club's National Draft took it past 38 seniors.
	var clubs := 0
	for code in draft.existing_sizes:
		clubs += 1
		var before := int(draft.existing_sizes[code])
		var took := draft.count_for(str(code))
		_check(took == 0 or before + took <= RookieList.SENIOR_SPOTS,
				"%s: the National Draft stops at a full senior list (%d kept + %d picks)" % [code, before, took])
	_check(clubs >= 18, "Every club was in the National Draft (%d)" % clubs)
	var rec: Dictionary = gs.rookie_draft
	_check(int(rec.get("year", 0)) == gs.season_year and gs.season_year == 2028,
			"The Rookie Draft opens after the National Draft, for the new season (%s)" % str(rec.get("year")))
	_check(gs.draft == null, "The National Draft is over when the Rookie Draft runs")
	_check(RookieList.waiting(gs), "Your first rookie pick waits for you")
	_check((rec.get("order", []) as Array).size() >= 18, "Every club is in the Rookie Draft order")
	var pool := MidseasonDraft.pool(gs)
	_check(not pool.is_empty(), "There are players left to take (%d)" % pool.size())
	if pool.is_empty():
		return
	var pid := str(pool[0]["id"])
	_check(RookieList.choose(gs, pid), "Your pick is taken")
	var mine := RookieList._find(gs.my_list, pid)
	_check(not mine.is_empty() and RookieList.is_rookie(mine), "He joins your rookie list")
	_check(int(mine.get("salary", 0)) == RookieList.wage(gs.season_year), "He is paid the rookie wage")
	_check(int(mine.get("contract_years", 0)) == RookieList.deal_years(mine)
			and int(mine.get("contract_years", 0)) in [1, 2], "A one- or two-season rookie deal")
	if RookieList.waiting(gs):
		_check(RookieList.choose(gs, ""), "A pass is taken")
	_check(not RookieList.waiting(gs) and bool(gs.rookie_draft.get("done", false)),
			"After a pass the Rookie Draft runs to its end")
	_check(RookieList.rookie_count(gs.my_list) == 1, "Your pass ended your draft at one rookie")
	var picks: Array = gs.rookie_draft.get("picks", [])
	_check(picks.size() > 1, "Rivals took rookies too (%d picks)" % picks.size())
	for code in gs.league_lists:
		var arr: Array = gs.league_lists[code]
		_check(RookieList.rookie_count(arr) <= RookieList.CAT_A_SPOTS, "%s: at most six rookies" % code)
		_check(arr.size() <= Contracts.MAX_LIST, "%s: at most 44 on both lists" % code)
	for k in picks:
		var p := RookieList._find(gs.league_lists.get(str(k["club"]), []), str(k["id"]))
		_check(RookieList.is_rookie(p) and int(p.get("salary", 0)) == RookieList.wage(gs.season_year),
				"Every Rookie Draft pick is on a rookie list on the rookie wage (%s)" % str(k["id"]))
		_check(not gs.free_agents.has(p) and not gs.draftee_pool.has(p), "A pick leaves the pool (%s)" % str(k["id"]))
	_check(gs.news.any(func(n): return str(n.get("text", "")).begins_with("Rookie Draft")),
			"The news reports the Rookie Draft")
	_check(gs.save_career() and gs.load_career() and int(gs.rookie_draft.get("year", 0)) == 2028
			and RookieList.rookie_count(gs.my_list) == 1,
			"A save and load keeps the Rookie Draft and the rookie list")
	var n := (gs.rookie_draft.get("picks", []) as Array).size()
	RookieList.open_draft(gs, gs.intake_order())
	_check((gs.rookie_draft.get("picks", []) as Array).size() == n, "The Rookie Draft opens once a season")


func _test_upgrade() -> void:
	Features.set_on(RookieList.SWITCH, true)
	_new_career()
	var list: Array = gs.my_list
	_check(list.size() >= RookieList.SENIOR_SPOTS, "A full list to start (%d)" % list.size())
	var rk: Dictionary = list[list.size() - 1]
	rk["rookie_list"] = "A"
	rk["salary"] = RookieList.wage(gs.season_year)
	var id := str(rk["id"])
	var senior_id := str(list[0]["id"])
	_check(RookieList.upgrade_block(gs, CLUB, senior_id) == "He is already on the senior list.",
			"A senior player cannot be upgraded")
	# Fill the senior list to 38 with stand-ins, so the upgrade has no spot.
	var n := 0
	while RookieList.senior_count(list) < RookieList.SENIOR_SPOTS:
		var extra: Dictionary = (list[0] as Dictionary).duplicate(true)
		extra["id"] = "%s_extra%d" % [str(extra["id"]), n]
		n += 1
		list.append(extra)
	_check(RookieList.upgrade_block(gs, CLUB, id).begins_with("The senior list is full"),
			"The upgrade is refused while the senior list is full")
	_check(not RookieList.upgrade(gs, CLUB, id) and RookieList.is_rookie(rk), "...and nothing moves")
	# Make room: delist seniors until one spot is free.
	while RookieList.senior_count(list) >= RookieList.SENIOR_SPOTS:
		for i in list.size():
			if not RookieList.is_rookie(list[i]):
				list.remove_at(i)
				break
	_check(RookieList.upgrade_block(gs, CLUB, id) == "", "A free senior spot allows the upgrade")
	_check(RookieList.upgrade(gs, CLUB, id), "The rookie is upgraded")
	_check(not RookieList.is_rookie(rk) and not rk.has("rookie_list"), "He is on the senior list")
	_check(int(rk["salary"]) >= RookieList.senior_wage(gs.season_year), "His wage rises to the senior minimum")
	_check(RookieList.senior_count(list) == RookieList.SENIOR_SPOTS, "He took the free senior spot")
	# A rival with a free senior spot upgrades its best rookie the same way.
	var rl: Array = gs.season.lists["GEE"]
	while RookieList.senior_count(rl) >= RookieList.SENIOR_SPOTS:
		rl.remove_at(0)
	var r1: Dictionary = rl[rl.size() - 1]
	r1["rookie_list"] = "A"
	var done := RookieList.ai_upgrades(gs)
	_check(done.any(func(d): return str(d["id"]) == str(r1["id"])) and not RookieList.is_rookie(r1),
			"A rival upgrades a rookie into a free senior spot")
	_check(not done.any(func(d): return str(d["club"]) == CLUB), "Your club is never upgraded for you")
	# A rookie who moves club lands on his new club's senior list.
	var mover: Dictionary = rl[0]
	mover["rookie_list"] = "A"
	gs._release("GEE", mover, false, false)
	gs._join("COL", mover)
	_check(not RookieList.is_rookie(mover) and str(mover["club"]) == "COL",
			"A rookie who changes club joins its senior list")
	Features.set_on(RookieList.SWITCH, false)
	_check(RookieList.upgrade_block(gs, CLUB, id) == "There is no rookie list.", "Switch off: no upgrade")


func _test_old_save() -> void:
	Features.set_on(RookieList.SWITCH, false)
	_new_career()
	_check(gs.save_career(), "An old-style career saves")
	Features.set_on(RookieList.SWITCH, true)
	_check(gs.load_career(), "...and loads with the rookie list on")
	_check(RookieList.rookie_count(gs.my_list) == 0 and RookieList.senior_count(gs.my_list) == gs.my_list.size(),
			"Every existing player is on the senior list")
	_check(gs.rookie_draft.is_empty() and not RookieList.waiting(gs), "No Rookie Draft waits in an old save")


## The Rookie Draft sheet over the pre-season (or the hub): a real tap on Pick.
func _test_rookie_draft_tap() -> void:
	Features.set_on(RookieList.SWITCH, true)
	var draft := _rollover()
	_check(draft != null and RookieList.waiting(gs), "A rookie pick waits after the rollover")
	if not RookieList.waiting(gs):
		return
	if gs.needs_season_wrap():
		gs.begin_season_from_wrap()
	var scene_path := "res://scenes/PreSeasonScene.tscn" if gs.preseason_active() else "res://scenes/HubScene.tscn"
	var scene: Control = load(scene_path).instantiate()
	root.add_child(scene)
	await _settle()
	var sheet := scene.get_node_or_null(RookieDraftSheet.NAME)
	_check(sheet != null, "The Rookie Draft sheet opens on %s" % scene_path.get_file())
	var want: String = RookieDraftSheet.PASS_PRESEASON if gs.preseason_active() else RookieDraftSheet.PASS_HUB
	var said := sheet != null and sheet.find_children("*", "Label", true, false).any(
			func(l): return (l as Label).text.contains(want))
	_check(said, "The sheet names the action on this screen that passes: %s" % want)
	var pool := MidseasonDraft.pool(gs)
	if sheet == null or pool.is_empty():
		scene.queue_free()
		return
	var pid := str(pool[0]["id"])
	var btn := sheet.find_child("RookiePick_%s" % pid, true, false) as Button
	_check(btn != null, "The best player left has a Pick button")
	var why: String = await Tap.tap(btn)
	_check(why == "", "A real tap on Pick reaches it (%s)" % why)
	await _settle()
	_check(RookieList.is_rookie(RookieList._find(gs.my_list, pid)), "The tapped player joins your rookie list")
	# Your next round's pick opens straight away; Pass ends it.
	if RookieList.waiting(gs):
		var again := scene.get_node_or_null(RookieDraftSheet.NAME)
		var pass_btn: Button = again.find_child("RookiePass", true, false) as Button if again != null else null
		_check(pass_btn != null, "The next round's sheet opens with Pass")
		var why2: String = await Tap.tap(pass_btn)
		_check(why2 == "", "A real tap on Pass reaches it (%s)" % why2)
		await _settle()
	_check(not RookieList.waiting(gs), "Your Rookie Draft is over")
	_check(scene.get_node_or_null(RookieDraftSheet.NAME) == null, "The sheet is gone")
	scene.queue_free()
	await _settle()


## The list screen shows both lists, and a rookie's profile offers the upgrade.
func _test_list_screen_and_upgrade_tap() -> void:
	Features.set_on(RookieList.SWITCH, true)
	_new_career()
	var list: Array = gs.my_list
	while RookieList.senior_count(list) >= RookieList.SENIOR_SPOTS:
		list.remove_at(0)
	var rk: Dictionary = list[list.size() - 1]
	rk["rookie_list"] = "A"
	var id := str(rk["id"])
	var scene: Control = load("res://scenes/ListScene.tscn").instantiate()
	scene.set("_pane", "list")
	root.add_child(scene)
	await _settle()
	var sh := scene.find_child("SeniorListHead", true, false) as Label
	var rh := scene.find_child("RookieListHead", true, false) as Label
	_check(sh != null and sh.text.contains("/ 38"), "The senior list shows its spots (%s)" % (sh.text if sh else "none"))
	_check(rh != null and rh.text.contains("1 / 6"), "The rookie list shows its spots (%s)" % (rh.text if rh else "none"))
	scene.call("_open_profile", id)
	await _settle()
	var up := scene.find_child("Upgrade", true, false) as Button
	_check(up != null and not up.disabled, "A rookie's profile offers the upgrade")
	if up != null:
		var why: String = await Tap.tap(up)
		_check(why == "", "A real tap on the upgrade reaches it (%s)" % why)
		await _settle()
	_check(not RookieList.is_rookie(RookieList._find(gs.my_list, id)), "The tapped upgrade moves him to the senior list")
	var rh2 := scene.find_child("RookieListHead", true, false) as Label
	_check(rh2 != null and rh2.text.contains("0 / 6"), "The rookie list count drops (%s)" % (rh2.text if rh2 else "none"))
	scene.queue_free()
	await _settle()


## A delisted rookie is a free agent; whoever signs him, his old club too,
## puts him on its senior list.
func _test_release_and_resign() -> void:
	Features.set_on(RookieList.SWITCH, true)
	_new_career()
	var rl: Array = gs.season.lists["GEE"]
	var p: Dictionary = rl[rl.size() - 1]
	p["rookie_list"] = "A"
	var before := RookieList.rookie_count(rl)
	gs._release("GEE", p, false, false)
	_check(not RookieList.is_rookie(p) and gs.free_agents.has(p), "A delisted rookie is a free agent off the rookie list")
	gs._sign_fa(p, "GEE", RookieList.senior_wage(gs.season_year), 1)
	_check(rl.has(p) and not RookieList.is_rookie(p), "Signed back by his old club, he is on its senior list")
	_check(RookieList.rookie_count(rl) == before - 1, "The rookie list lost him (%d)" % RookieList.rookie_count(rl))


## A club on no ladder yet (in its first season) still gets a Rookie Draft
## seat, at the end of the order.
func _test_entering_club_seat() -> void:
	Features.set_on(RookieList.SWITCH, true)
	_new_career()
	var order: Array = gs.intake_order()
	_check(order.has("WCE") and order.size() >= 18, "(setup) WCE is on the ladder (%d clubs)" % order.size())
	order.erase("WCE")
	gs.rookie_draft = {}
	RookieList.open_draft(gs, order)
	var seats: Array = gs.rookie_draft.get("order", [])
	_check(seats.has("WCE") and str(seats[seats.size() - 1]) == "WCE",
			"A club missing from the National Draft order sits last in the Rookie Draft (%s)" % str(seats))
	_check(seats.size() == order.size() + 1, "Every other club keeps its seat once (%d)" % seats.size())
	RookieList.settle(gs)
	_check(not RookieList.waiting(gs), "(cleanup) your pick is passed")


## The mid-season rookie draft fills rookie spots: a club with six rookies is
## left out, a club with a free rookie spot is in, and every pick is a rookie.
func _test_midseason_fills_rookie_spots() -> void:
	Features.set_on(RookieList.SWITCH, true)
	Features.set_on(MidseasonDraft.SWITCH, true)
	_new_career()
	var year: int = gs.season_year
	var cls: Array = gs.draftee_pool.filter(func(q): return int(q.get("draft_year", year)) == year)
	_check(cls.size() >= 30, "(setup) a class to pass over (%d)" % cls.size())
	for i in mini(30, cls.size()):
		(cls[i] as Dictionary)["draft_year"] = year - 1
	var full: Array = gs.season.lists["GEE"]
	for i in RookieList.CAT_A_SPOTS:
		(full[full.size() - 1 - i] as Dictionary)["rookie_list"] = "A"
	var open: Array = gs.season.lists["COL"]
	while open.size() >= Contracts.MAX_LIST:
		open.pop_back()
	_check(RookieList.rookie_spot_free(open) and not RookieList.rookie_spot_free(full),
			"(setup) COL has a rookie spot, GEE has none")
	MidseasonDraft._record(gs)
	MidseasonDraft._open_draft(gs)
	var order: Array = gs.midseason.get("order", [])
	_check(not order.has("GEE"), "A club with six rookies is out of the mid-season draft")
	_check(order.has("COL"), "A club with a free rookie spot is in it")
	# Your pick is passed; the rivals' picks run to the end.
	MidseasonDraft.settle(gs)
	_check(not MidseasonDraft.waiting(gs), "Your pick is passed and the draft ends")
	var picks: Array = gs.midseason.get("picks", [])
	_check(not picks.is_empty(), "Rivals took players (%d)" % picks.size())
	for k in picks:
		var p := RookieList._find(gs.season.lists.get(str(k["club"]), []), str(k["id"]))
		_check(RookieList.is_rookie(p), "A mid-season pick lands on the rookie list (%s)" % str(k["id"]))
	Features.set_on(MidseasonDraft.SWITCH, false)


## A real-lists career with the switch on: the starting lists split into
## senior and rookie lists, the opening National Draft fills the senior list
## and the Rookie Draft follows it.
func _test_real_lists_start() -> void:
	Features.set_on(RookieList.SWITCH, true)
	gs.reset()
	gs.begin_real_lists()
	var draft: Draft = gs.draft
	_check(draft != null and draft.senior_cap == RookieList.SENIOR_SPOTS,
			"The opening National Draft fills the senior list (38)")
	if draft == null:
		return
	var clubs := 0
	var marked := 0
	for code in gs.league_lists:
		clubs += 1
		var arr: Array = gs.league_lists[code]
		_check(RookieList.rookie_count(arr) <= RookieList.CAT_A_SPOTS, "%s starts with at most six rookies" % code)
		_check(RookieList.rookie_count(arr) == RookieList.CAT_A_SPOTS or RookieList.senior_count(arr) <= RookieList.SENIOR_SPOTS,
				"%s: over 38 seniors only once its rookie list is full" % code)
		_check(int(draft.existing_sizes.get(code, -1)) == RookieList.senior_count(arr),
				"%s: the draft counts the senior list" % code)
		for p in arr:
			if str(p.get("list_type", "")) == "rookie" and RookieList.is_rookie(p):
				marked += 1
	_check(clubs >= 18, "Every club has a list (%d)" % clubs)
	_check(marked > 0, "The club lists' rookies start on the rookie list (%d)" % marked)
	gs.choose_real_club(CLUB)
	while not draft.is_finished():
		var candidate := draft._best_ai_pick(draft.current_club())
		if candidate.is_empty() or not draft._draft_pick(draft.current_club(), candidate):
			draft._skip_current_pick()
	for code in draft.existing_sizes:
		var before := int(draft.existing_sizes[code])
		var took := draft.count_for(str(code))
		_check(took == 0 or before + took <= RookieList.SENIOR_SPOTS,
				"%s: the opening draft stops at a full senior list (%d kept + %d picks)" % [code, before, took])
	_check(gs.finish_intake_draft(), "The opening National Draft commits")
	_check(int(gs.rookie_draft.get("year", 0)) == GameDB.START_YEAR and gs.season_year == GameDB.START_YEAR,
			"The Rookie Draft follows the opening National Draft (%s)" % str(gs.rookie_draft.get("year")))
	_check((gs.rookie_draft.get("order", []) as Array).size() >= 18, "Every club has a Rookie Draft seat")
	RookieList.settle(gs)
	_check(bool(gs.rookie_draft.get("done", false)), "Passing ends your Rookie Draft and it runs to its end")
	for code in gs.season.lists:
		_check(RookieList.rookie_count(gs.season.lists[code]) <= RookieList.CAT_A_SPOTS,
				"%s: at most six rookies after it" % code)
