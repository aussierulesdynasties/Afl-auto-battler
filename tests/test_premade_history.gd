extends RefCounted
## Pre-made histories (row 137): every shipped file is fresh against the save
## format and the real lists, starts the right years, works for whichever club
## is picked, keeps the career's own choices, and plays on and reloads.
## Run through tests/run_premade_history_tests.gd.

var failures: Array[String] = []
var checks := 0

const REGEN := "stale: run tools/histories/regen.sh and commit data/histories"


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = 0
	_t("_test_fresh")
	_t("_test_refuses")
	_t("_test_any_club")
	_t("_test_keeps_choices")
	_t("_test_tasmania")
	_t("_test_plays_on_and_reloads")
	GameState.reset()
	print(Ran.line("Premade history", self))


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


func _test_fresh() -> void:
	GameDB.reload()
	var now := PremadeHistory.stamps()
	for first in PremadeHistory.STARTS:
		for n in PremadeHistory.COUNT:
			var p := PremadeHistory.path_for(first, n)
			_check(FileAccess.file_exists(p), "%s is missing: %s" % [p, REGEN])
			var meta := CareerSave.read_packed_meta(p)
			for key in ["save_version", "career_version", "list_stamp", "list_files"]:
				_check(str(meta.get(key, "")) == str(now[key]), "%s %s is %s" % [p, key, REGEN])
			_check(int(meta.get("first_season", 0)) == first, "%s holds the start its name says" % p)
			# Tuning moves too fast for every sim PR to carry binaries, so a
			# build is what stops on this one (tools/export_builds.sh).
			if str(meta.get("sim_code", "")) != str(now["sim_code"]):
				print("NOTE: %s is behind the sim code; regenerate before a build" % p)


func _test_refuses() -> void:
	var meta := PremadeHistory.stamps()
	_check(PremadeHistory.problem(meta) == "", "A fresh header passes")
	var old := meta.duplicate()
	old["save_version"] = CareerSave.VERSION - 1
	_check(PremadeHistory.problem(old) == "save format", "An older save format is refused")
	var lists := meta.duplicate()
	lists["list_stamp"] = "x"
	_check(PremadeHistory.problem(lists) == "real lists", "Changed real lists are refused")
	GameState.reset()
	GameState.custom_prospect_id = "C1"
	_check(not GameState.begin_from_history(2030), "A forged prospect plays the years live")
	GameState.reset()
	GameState.replay_seed = 7
	_check(not GameState.begin_from_history(2030), "A seeded run plays the years live")
	GameState.replay_seed = 0
	_check(not GameState.begin_from_history(2031), "A start with no history plays live")


func _start(first: int) -> bool:
	GameState.reset()
	GameState.set_canberra(first == GameState.SIM_AHEAD_TO)
	return GameState.begin_from_history(first)


## A 2030 history, then `code` chosen at its draft.
func _any_club(code: String) -> void:
	_check(_start(2030), "A history starts the 2030 career")
	_check(GameState.choosing_club() and GameState.season_year == 2029 and not GameState.has_career(),
			"Choose your club opens at the 2029 draft, nothing saved")
	_check(GameState.draft.user_club == "" and GameState.draft.pick_index == 0, "No pick is made before you")
	_check(GameState.canberra_on and GameState.draft.clubs.has("CANB"), "Canberra are in the draft")
	_check(GameState.choose_sim_ahead_club(code), "%s can be chosen" % code)
	_check(GameState.my_club == code and GameState.draft.user_club == code and not GameState.sim_ahead,
			"The career is %s's" % code)
	_check(not GameState.my_list.is_empty() or ExpansionBuild.has_package(GameState, code),
			"%s has a list or a build" % code)
	for p in GameState.my_list:
		_check(str(p.get("club", code)) == code, "%s's player %s is on the list he plays for" % [code, p.get("id")])
		break


## The two new clubs here; a club of today's league (Collingwood) is chosen
## the same way by _test_plays_on_and_reloads's 2030 start, which plays on
## from there (each start costs a reset and a history load).
func _test_any_club() -> void:
	for code in ["TAS", "CANB"]:
		_any_club(code)


func _test_keeps_choices() -> void:
	GameState.reset()
	GameState.set_canberra(true)
	GameState.board_patience = "ruthless"
	GameState.rival_recruiting = "cutthroat"
	GameState.tutorials = false
	GameState.challenge = {"kind": "youth"}
	_check(GameState.begin_from_history(2030), "History with choices")
	var history_seeds := []
	for n in PremadeHistory.COUNT:
		history_seeds.append(int(CareerSave.read_packed(PremadeHistory.path_for(2030, n)).get("career_seed", 0)))
	_check(GameState.career_seed > 0 and not history_seeds.has(GameState.career_seed), "The career has its own seed")
	_check(GameState.board_patience == "ruthless" and GameState.rival_recruiting == "cutthroat", "The dials stay")
	_check(not GameState.tutorials, "Tips stay off")
	_check(GameState.challenge.is_empty(), "The challenge waits for the club")
	GameState.choose_sim_ahead_club("GEE")
	_check(str(GameState.challenge.get("kind", "")) == "youth", "The challenge starts with the club")


func _test_tasmania() -> void:
	_check(_start(2028), "A history starts Tasmania's 2028")
	_check(GameState.choosing_club() and GameState.season_year == 2027 and GameState.sim_ahead_to == 2028,
			"Choose opens at the 2027 draft")
	_check(not GameState.canberra_on and not GameState.draft.clubs.has("CANB"), "Canberra stay out")
	_check(GameState.draft.clubs.has("TAS") and ExpansionBuild.has_package(GameState, "TAS"), "Tasmania have their build")
	_check(GameState.choose_sim_ahead_club("TAS") and GameState.my_club == "TAS", "Tasmania are yours")
	var picks: Array = GameState.draft.upcoming_picks("TAS", 0)
	_check(picks.size() > 0, "Tasmania have picks")


func _test_plays_on_and_reloads() -> void:
	for first in PremadeHistory.STARTS:
		var code := "TAS" if first == 2028 else "COL"
		if first == 2030:
			_any_club(code)
		else:
			_check(_start(first), "History %d" % first)
			GameState.choose_sim_ahead_club(code)
		var draft: Draft = GameState.draft
		var guard := 0
		while not draft.is_finished() and guard < 500:
			guard += 1
			draft.auto_until_user_turn()
			if draft.is_user_turn():
				draft.pick_for_me()
		GameState.finish_intake_draft()
		_check(GameState.season_year == first and GameState.season.lists.has(code),
				"%d: the first season opens with %s in it (%d)" % [first, code, GameState.season_year])
		GameState.advance()
		_check(GameState.season.round_index >= 1, "%d: a week is played" % first)
		_check(GameState.save_career(), "%d: the career saves" % first)
		var rnd: int = GameState.season.round_index
		var ids := []
		for p in GameState.my_list:
			ids.append(p["id"])
		_check(GameState.load_career(), "%d: the career reloads" % first)
		var after := []
		for p in GameState.my_list:
			after.append(p["id"])
		_check(GameState.my_club == code and GameState.season.round_index == rnd and after == ids,
				"%d: the reload is the same career" % first)
		_check(not GameState.sim_ahead, "%d: a reloaded career is a career" % first)
		GameState.advance()
		_check(GameState.season.round_index == rnd + 1, "%d: and plays on" % first)
		GameState.delete_saved_career()
