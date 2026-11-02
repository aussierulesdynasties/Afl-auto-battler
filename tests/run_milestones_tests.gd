extends SceneTree
## godot --headless --path . --script tests/run_milestones_tests.gd
## Milestone games (plan step 3c, Milestones.gd): each milestone is found at
## the right game, recorded once, recorded by a played week, survives a save,
## and an old save without the record loads with the coach's games counted.

const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 2033
var _state: Node
var _M: GDScript
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _run() -> void:
	await process_frame
	seed(SUITE_SEED)
	_state = root.get_node("GameState")
	_M = load("res://scripts/sim/Milestones.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://test_milestones.save"
	_state.settings_path = "user://test_milestones.cfg"
	_state.delete_saved_career()
	await _t("_test_right_game")
	await _t("_test_no_duplicates")
	await _t("_test_coach")
	await _t("_test_sim_week_records")
	await _t("_test_old_save")
	await _t("_test_switch")
	print(Ran.line("Milestones", self))
	for f in _failures:
		print("  FAIL: " + f)
	_state.delete_saved_career()
	quit(1 if not _failures.is_empty() else 0)


func _fresh() -> void:
	_state.reset()
	_state.start_season("COL", root.get_node("GameDB").club_list("COL"))


## A player on your list whose career is on record in full.
func _complete_player() -> Dictionary:
	for p in _state.my_list:
		if Career.complete(p):
			return p
	return {}


## Sets his tally so that, with this match counted, he has played `games`.
func _set_games(p: Dictionary, games: int) -> void:
	var id := str(p["id"])
	var t: Dictionary = _state.season_tally.get(id, {"club": _state.my_club, "games": 0, "goals": 0,
			"goals_ha": 0, "disposals": 0, "distance_run": 0.0, "influence": 0.0, "votes": 0, "bf": 0,
			"polled": 0, "coaches": 0})
	_state.season_tally[id] = t
	t["games"] = 0
	t["games"] = games - _state.games_played(p)


var _n := 0
func _res(p: Dictionary, goals := 0, won := true, tag := "") -> Dictionary:
	_n += 1
	var r := {"home": _state.my_club, "away": "GEE", "label": "Round %d" % _n, "score": [90, 60] if won else [60, 90],
			"roster": [[{"id": str(p["id"])}], []], "players": {str(p["id"]): {"goals": goals}}}
	if tag != "":
		r["tag"] = tag
	return r


func _kinds(added: Array, who := "player") -> Array:
	var out := []
	for e in added:
		if str(e["who"]) == who:
			out.append("%s%d" % [e["kind"], int(e["value"])])
	return out


func _test_right_game() -> void:
	_fresh()
	var p := _complete_player()
	_check(not p.is_empty(), "(setup) a player with a complete career")
	for g in [49, 50, 51, 99, 100, 300]:
		_set_games(p, g)
		var k := _kinds(_M.record_round(_state, [_res(p)]))
		var want := [] if not _M.PLAYER_GAMES.has(g) else ["games%d" % g]
		_check(k == want, "At %d games he records %s (got %s)" % [g, want, k])
	_set_games(p, 1)
	_check(_kinds(_M.record_round(_state, [_res(p)])) == ["debut1"], "His first game is his debut")
	# Goals: 98 before, three in this match, crosses 100.
	_set_games(p, 7)
	var id := str(p["id"])
	(_state.season_tally[id] as Dictionary)["goals"] = 0
	(_state.season_tally[id] as Dictionary)["goals"] = 101 - _state.career_goals_before(p, 0)
	_check(_kinds(_M.record_round(_state, [_res(p, 3)])) == ["goals100"], "98 then three goals is his 100th")


func _test_no_duplicates() -> void:
	_fresh()
	var p := _complete_player()
	_set_games(p, 100)
	var r := _res(p)
	_check(_M.record_round(_state, [r]).size() >= 1, "(setup) the 100th is recorded")
	_check(_M.record_round(_state, [r]).is_empty(), "The same match recorded twice adds nothing")
	_check(_kinds(_M.record_round(_state, [_res(p)])).is_empty(), "A second match at the same count adds nothing")
	var count := 0
	for e in _state.milestone_log["log"]:
		if str(e["id"]) == str(p["id"]) and int(e["value"]) == 100:
			count += 1
	_check(count == 1, "One 100th game in the record (%d)" % count)


func _test_coach() -> void:
	_fresh()
	var p := _complete_player()
	_set_games(p, 7)
	var c: Dictionary = _state.milestone_log["coach"]
	_check(_kinds(_M.record_round(_state, [_res(p, 0, false)]), "coach").is_empty(), "A first-game loss is no milestone")
	_check(_kinds(_M.record_round(_state, [_res(p, 0, true)]), "coach") == ["first_win1"], "The first win is recorded")
	_check(_kinds(_M.record_round(_state, [_res(p, 0, true)]), "coach").is_empty(), "The second win is not")
	c["games"] = 49
	_check(_kinds(_M.record_round(_state, [_res(p, 0, false)]), "coach") == ["coached50"], "Game 50 as coach")
	_check(int(c["games"]) == 50 and int(c["wins"]) == 2, "Coach counts move on (%s)" % c)
	_check(_kinds(_M.record_round(_state, [_res(p, 0, false, "EF1")]), "coach") == ["first_final1"], "The first final")
	_check(_kinds(_M.record_round(_state, [_res(p, 0, false, "SF1")]), "coach").is_empty(), "Not the second")
	c["games"] = 99
	_check(_kinds(_M.record_round(_state, [_res(p)]), "coach") == ["coached100"], "Game 100 as coach")
	c["games"] = 149
	_check(_kinds(_M.record_round(_state, [_res(p)]), "coach").is_empty(), "Game 150 is not a coach milestone")


func _test_sim_week_records() -> void:
	_fresh()
	# Someone in the side plays his 50th this week.
	var side: Dictionary = _state.current_side()
	var target := {}
	for k in side:
		for id in side[k]:
			var q: Dictionary = _state.list_player(str(id))
			if Career.complete(q) and _state.games_played(q) > 0:
				target = q
				break
		if not target.is_empty():
			break
	_check(not target.is_empty(), "(setup) a player in the side")
	_set_games(target, 49)
	var up: Array = _M.upcoming(_state)
	var flagged := false
	for u in up:
		flagged = flagged or (str(u["id"]) == str(target["id"]) and str(u["key"]) == "games")
	_check(flagged, "The 50th is in the week's milestones before the match")
	_state.advance()
	var c: Dictionary = _state.milestone_log["coach"]
	_check(int(c["games"]) == 1, "A played week counts one game coached (%d)" % int(c["games"]))
	_check(str(_state.milestone_log["last_match"]).begins_with(str(_state.season_year)), "The match is marked recorded")
	var played := false
	for r in (_state.my_last_result() as Dictionary).get("roster", [[], []])[0 if _state.my_last_result()["home"] == _state.my_club else 1]:
		played = played or str(r.get("id", "")) == str(target["id"])
	if played:
		var hit := false
		for e in _state.milestone_log["log"]:
			hit = hit or (str(e["id"]) == str(target["id"]) and int(e["value"]) == 50)
		_check(hit, "Sim the week records his 50th")
		_check(_M.summary_line(_state, _state.my_last_result()).contains("50th"), "The full-time line names it")
	else:
		print("SKIP: the target did not take the field this week")


func _test_old_save() -> void:
	_fresh()
	_state.advance()
	_state.advance()
	_check(_state.save_career(), "(setup) saved")
	var blob := CareerSave.read(_state.save_path)
	blob.erase("milestone_log")
	_check(CareerSave.write(blob, _state._save_meta(), _state.save_path), "(setup) the record removed, as an old save")
	_check(_state.load_career(), "An old save loads")
	var c: Dictionary = _state.milestone_log["coach"]
	_check(int(c["games"]) == 2, "Its coach games come from the ladder (%d)" % int(c["games"]))
	_check(_state.milestone_log["log"] is Array and _state.milestone_log["seen"] is Dictionary, "Its record is whole")
	_state.milestone_log["log"].append({"who": "coach", "kind": "x"})
	_check(_state.save_career() and _state.load_career(), "A new save round-trips")
	_check((_state.milestone_log["log"] as Array).size() == 1, "The record survives the round trip")


func _test_switch() -> void:
	_check(_M.shown() and not Features.KNOWN.has("milestone_games"), "Milestones are live: no switch")
	_fresh()
	var p := _complete_player()
	_state.milestone_log["coach"]["games"] = 49
	_check(_M.upcoming(_state).any(func(u): return str(u["key"]) == "coached"), "The coach's 50th is this week's")
