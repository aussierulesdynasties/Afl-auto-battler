extends RefCounted
## Team familiarity (TODO row 125): the director's rulings of 2026-11-09 as numbers,
## every way onto a list, every club, the save, and the screens that say it.
## Run through tests/run_team_familiarity_tests.gd.

var failures: Array[String] = []
var checks := 0
var root: Window

const TF := preload("res://scripts/sim/TeamFamiliarity.gd")
const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")


func run(tree_root: Window) -> void:
	failures.clear()
	checks = 0
	root = tree_root
	GameState.replay_seed = 2027
	_t("_test_cut_sizes")
	_t("_test_fade_line")
	_t("_test_team_step")
	_t("_test_reaches_fit")
	_t("_test_plain_lists_unchanged")
	_t("_test_ways_onto_a_list")
	_t("_test_preseason_lift")
	_t("_test_every_club_ticks")
	_t("_test_save_and_old_save")
	_t("_test_career_start_clears")
	await _t("_test_screens")
	GameState.reset()
	print(Ran.line("Team familiarity", self))


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(cond: bool, what: String) -> void:
	checks += 1
	if not cond:
		failures.append(what)
		push_error("FAILED: " + what)


func _near(a: float, b: float) -> bool:
	return absf(a - b) < 0.00001


func _man(fam: float, draftee := false) -> Dictionary:
	var p := {"id": "m%d" % checks, "team_fam": fam}
	if draftee:
		p["team_fam_kind"] = "draftee"
	return p


func _test_cut_sizes() -> void:
	_check(_near(TF.own_cut(_man(70.0)), 0.02), "A new-club man at 70 loses 2%")
	_check(_near(TF.own_cut(_man(50.0)), 0.02 * 50.0 / 30.0) and TF._percent(TF.own_cut(_man(50.0))) == "3.3%", "A new-club man at 50 loses 3.3%")
	_check(_near(TF.own_cut(_man(70.0, true)), 0.01), "A draftee at 70 loses 1%")
	_check(TF._percent(TF.own_cut(_man(50.0, true))) == "1.7%", "A draftee at 50 loses 1.7%")
	_check(_near(TF.own_cut(_man(95.0)), 0.02 / 6.0), "95 is one sixth of the 70 cut")
	_check(_near(TF.own_cut({"id": "x"}), 0.0), "No familiarity on him is 100: no cut")


func _test_fade_line() -> void:
	var p := {"id": "x"}
	TF.arrive_club(p)
	_check(TF.value(p) == 50.0, "A new arrival starts at 50")
	TF.round_one([p])
	_check(TF.value(p) == 70.0, "A full pre-season lifts him to 70")
	for want in [75.0, 80.0, 85.0, 90.0, 95.0]:
		TF.after_game(p, true)
		_check(TF.value(p) == want, "A senior game takes him to %d" % want)
	TF.after_game(p, true)
	_check(not p.has("team_fam") and TF.value(p) == 100.0, "He is at 100 from game 7, and carries nothing")
	var q := {"id": "y"}
	TF.arrive_club(q)
	TF.round_one([q])
	TF.after_game(q, false)
	_check(TF.value(q) == 72.5, "A reserves game counts half")
	var r := {"id": "z"}
	TF.arrive_club(r)
	TF.round_one([r])
	TF.round_one([r])
	TF.after_game(r, true)
	TF.round_one([r])
	_check(TF.value(r) == 75.0, "A second pre-season never takes him backwards")


func _test_team_step() -> void:
	var side := [_man(70.0), _man(70.0), _man(70.0)]
	_check(_near(TF.team_cut(side), 0.0), "Three new-club men cost the side nothing")
	side.append(_man(70.0))
	var four := TF.team_cut(side)
	_check(_near(four, TF.TEAM_CUT_AT_70), "The fourth brings the whole cost at 70")
	for i in range(4):
		side.append(_man(70.0))
	_check(_near(TF.team_cut(side), four), "A flat step: eight men cost what four do")
	var with_kids := [_man(70.0), _man(70.0), _man(70.0), _man(70.0, true), _man(70.0, true),
			{"id": "f", "team_fam": 70.0, "team_fam_first": true}]
	_check(_near(TF.team_cut(with_kids), 0.0), "Draftees and first-gamers do not count towards the four")
	var faded := [_man(95.0), _man(95.0), _man(95.0), _man(95.0)]
	_check(_near(TF.team_cut(faded), four / 6.0), "It fades on the same line: one sixth at 95")
	var hurt := [_man(50.0), _man(50.0), _man(50.0), _man(50.0)]
	_check(_near(TF.team_cut(hurt), four), "Men held at 50 by injury never cost the side more than Round 1")


func _test_reaches_fit() -> void:
	GameDB.skip_ovr_overrides = true
	GameDB.reload()
	var plain_h := Squad.new("MEL", GameDB.club_list("MEL"), true, "MEL")
	var plain_a := Squad.new("FRE", GameDB.club_list("FRE"), false, "FRE")
	var base := MatchSim.new(plain_h, plain_a, 7)
	var men: Array = plain_h.ground.slice(0, 4)
	var other: Dictionary = plain_h.ground[10]
	var rival: Dictionary = plain_a.ground[0]
	var was: float = base.fit(men[0])
	var was_other: float = base.fit(other)
	var was_rival: float = base.fit(rival)
	for p in men:
		TF.arrive_club(p)
		p["team_fam"] = 70.0
	var sim := MatchSim.new(plain_h, plain_a, 7)
	_check(_near(was - sim.fit(men[0]), 0.02 + TF.TEAM_CUT_AT_70), "An arrival plays with his own cut and the side's")
	_check(_near(was_other - sim.fit(other), TF.TEAM_CUT_AT_70), "His settled teammate plays with the side's")
	_check(_near(was_rival - sim.fit(rival), 0.0), "The other club pays nothing")
	for p in men:
		TF.clear(p)


func _test_plain_lists_unchanged() -> void:
	var sim := MatchSim.new(Squad.new("MEL", GameDB.club_list("MEL"), true, "MEL"),
			Squad.new("FRE", GameDB.club_list("FRE"), false, "FRE"), 7)
	_check(sim._fam_cut.is_empty() and sim.team_fam_cut == [0.0, 0.0], "A settled list carries no cut at all")
	# The histories are stamped against the game's own data.
	GameDB.skip_ovr_overrides = false
	GameDB.reload()


func _test_ways_onto_a_list() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var settled := true
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			settled = settled and not p.has("team_fam")
	_check(settled, "Everyone on a list when a career starts begins at 100")
	var moved: Dictionary = GameState.season.lists["FRE"][0]
	GameState.season.lists["FRE"].erase(moved)
	moved["career"] = {"games": 50}
	GameState._join("GEE", moved)
	_check(TF.value(moved) == 50.0 and not TF.is_draftee(moved), "A man moved to a new club starts at 50, at the new-club rate")
	# His own club taking him back is no move.
	moved["team_fam"] = 85.0
	GameState.season.lists["GEE"].erase(moved)
	GameState._join("GEE", moved)
	_check(TF.value(moved) == 85.0, "Re-signing at the same club resets nothing")
	# The mid-season and rookie drafts: a draftee's rate, at 50, whenever he comes.
	for route in [MidseasonDraft, RookieList]:
		var kid: Dictionary = (GameDB.draftees[0] as Dictionary).duplicate(true)
		kid["id"] = "kid_" + str(checks)
		kid.erase("club")
		GameState.draftee_pool.append(kid)
		GameState.midseason = {"picks": [], "round": 1}
		GameState.rookie_draft = {"picks": [], "round": 1}
		route._take(GameState, "GEE", kid)
		_check(TF.value(kid) == 50.0 and TF.is_draftee(kid), "A mid-season pick starts at 50 at the draftee rate")
	var fa: Dictionary = GameState.season.lists["CAR"][0]
	GameState.season.lists["CAR"].erase(fa)
	fa["career"] = {"games": 20}
	fa["club"] = ""
	GameState.free_agents.append(fa)
	MidseasonDraft._take(GameState, "GEE", fa)
	_check(TF.value(fa) == 50.0 and not TF.is_draftee(fa), "A delisted veteran taken mid-season is a new-club man")


func _test_preseason_lift() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState.open_preseason(false)
	var fit_man: Dictionary = GameState.season.lists["FRE"][0]
	var hurt: Dictionary = GameState.season.lists["FRE"][1]
	var mine: Dictionary = GameState.my_list[0]
	for p in [fit_man, hurt, mine]:
		TF.arrive_club(p)
	hurt["injury_weeks"] = 4
	GameState._finish_preseason()
	_check(TF.value(fit_man) == 70.0, "A computer club's arrival reaches 70 by Round 1")
	_check(TF.value(mine) == 70.0, "So does yours")
	_check(TF.value(hurt) == 50.0, "A man who misses the pre-season through injury stays at 50")
	var res := {"home": "FRE", "away": "GEE", "score": [10, 5], "roster": [[hurt], [mine]]}
	GameState._familiarity_after_round([res])
	_check(TF.value(hurt) == 55.0, "He comes on from 50 once he plays")


func _test_every_club_ticks() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var played: Dictionary = GameState.season.lists["FRE"][0]
	var reserves: Dictionary = GameState.season.lists["FRE"][1]
	var injured: Dictionary = GameState.season.lists["FRE"][2]
	var mine: Dictionary = GameState.my_list[0]
	var mine_out: Dictionary = GameState.my_list[1]
	for p in [played, reserves, injured, mine, mine_out]:
		TF.arrive_club(p)
		p["team_fam"] = 70.0
	injured["injury_weeks"] = 3
	GameState._familiarity_after_round([{"home": "FRE", "away": "GEE", "score": [10, 5],
			"roster": [[played], [mine]]}])
	_check(TF.value(played) == 75.0 and TF.value(mine) == 75.0, "Both clubs' men come on 5 for a senior game")
	_check(TF.value(reserves) == 72.5 and TF.value(mine_out) == 72.5, "Both clubs' fit men left out come on 2.5")
	_check(TF.value(injured) == 70.0, "A man in the rooms comes on nothing")


func _test_save_and_old_save() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var id := str(GameState.my_list[0]["id"])
	TF.arrive_draftee(GameState.my_list[0])
	GameState.my_list[0]["team_fam"] = 75.0
	var other_id := str(GameState.my_list[1]["id"])
	TF.arrive_club(GameState.my_list[1], true)
	GameState.save_career()
	GameState.load_career()
	var p: Dictionary = GameState.list_player(id)
	_check(TF.value(p) == 75.0 and TF.is_draftee(p), "Familiarity and its kind survive a save")
	_check(bool(GameState.list_player(other_id).get("team_fam_first", false)), "So does a first-gamer's mark")
	# An older save simply has no field on anyone: everyone is at 100.
	for q in GameState.my_list:
		TF.clear(q)
	GameState.save_career()
	GameState.load_career()
	_check(TF.value(GameState.list_player(id)) == 100.0 and GameState.familiarity_side_line() == "",
			"A save without the field loads with everyone at 100")


func _test_career_start_clears() -> void:
	GameState.reset()
	GameState.replay_seed = 0
	GameState.set_canberra(true)
	var started: bool = GameState.begin_from_history(2030)
	GameState.replay_seed = 2027
	_check(started, "A history starts a career")
	if not started:
		return
	var code: String = str(GameState.draft.clubs[0])
	var list: Array = GameState.league_lists[code] if GameState.league_lists.has(code) else []
	if list.is_empty():
		_check(false, "A history has lists")
		return
	TF.arrive_club(list[0])
	_check(GameState.choose_sim_ahead_club(code), "A club can be taken on")
	_check(TF.value(list[0]) == 100.0, "Everyone on a list when your career starts begins at 100")


func _settle() -> void:
	for i in range(5):
		await root.get_tree().process_frame


func _test_screens() -> void:
	GameState.reset()
	GameState.start_season("FRE", GameDB.club_list("FRE"))
	root.size = Vector2i(390, 844)
	for key in ["list", "selection", "offseason"]:
		GameState.set_setting("seen_%s_intro" % key, true)
	# The list row, and a real tap through to what it does to his footy.
	var p: Dictionary = GameState.my_list[3]
	var id := str(p["id"])
	TF.arrive_club(p)
	p["team_fam"] = 70.0
	var ls: Control = load("res://scenes/ListScene.tscn").instantiate()
	root.add_child(ls)
	await _settle()
	for t in ls.find_children("*", "Button", true, false):
		if (t as Button).text == "Full list":
			_check(await Tap.tap(t) == "", "A finger reaches Full list")
			break
	await _settle()
	var row: Button = ls.find_child("Row_" + id, true, false)
	var tag: Label = row.find_child("RowFamiliarity", true, false) if row != null else null
	_check(tag != null and tag.text == "Familiarity 70%", "His row on My list reads Familiarity 70%")
	if row != null:
		_check(await Tap.tap(row) == "", "A finger's tap on his row reaches it, past the new line")
		await _settle()
		var said: Label = ls.find_child("ProfileFamiliarity", true, false)
		_check(said != null and said.text.contains("2% off his footy"), "His profile says what it costs him")
	ls.queue_free()
	await _settle()
	TF.clear(p)
	# Where the side is picked: silent under three, a warning at three, the cost at four.
	# A Squad names copies: the men themselves are on the list.
	var named: Array = GameState.my_squad().ground.map(func(q): return GameState.list_player(str(q["id"])))
	var ui: Control = load("res://scenes/SelectionScene.tscn").instantiate()
	root.add_child(ui)
	await _settle()
	var note: Label = ui.find_child("TurnoverNote", true, false)
	_check(note != null and not note.visible, "A settled side hears nothing about turnover")
	ui.queue_free()
	await _settle()
	for q in named.slice(0, 3):
		TF.arrive_club(q)
		q["team_fam"] = 70.0
	_check(GameState.familiarity_side_line().begins_with("3 men new") and GameState.familiarity_side_line().contains("about %d points" % TF.TEAM_POINTS_AT_70),
			"At three the coach is told what a fourth would cost")
	TF.arrive_club(named[3])
	named[3]["team_fam"] = 70.0
	ui = load("res://scenes/SelectionScene.tscn").instantiate()
	root.add_child(ui)
	await _settle()
	note = ui.find_child("TurnoverNote", true, false)
	_check(note != null and note.visible and note.text.begins_with("4 men new") and note.text.contains("about %d points" % TF.TEAM_POINTS_AT_70),
			"At four the selection screen states the cost before it bites")
	var keys := GameState.my_week_notes().map(func(n): return str(n.get("key", "")))
	_check(keys.has("own_familiarity"), "The week's notes carry it too")
	ui.queue_free()
	await _settle()
	# The trade screen says the rule once you ask for a man.
	var off: Control = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(off)
	await _settle()
	off.set("_trade_club", "MEL")
	off.set("_theirs", [str(GameState.season.lists["MEL"][0]["id"])])
	var trade := VBoxContainer.new()
	root.add_child(trade)
	off.call("_trade", trade)
	await _settle()
	_check(trade.find_child("TradeFamiliarity", true, false) != null, "The trade screen says what a man traded in costs")
	var agents := VBoxContainer.new()
	root.add_child(agents)
	off.call("_agents", agents)
	await _settle()
	_check(agents.find_child("AgentsFamiliarity", true, false) != null, "So does free agency")
	trade.queue_free()
	agents.queue_free()
	off.queue_free()
	await _settle()
