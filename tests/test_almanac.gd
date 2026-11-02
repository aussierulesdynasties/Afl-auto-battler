extends RefCounted
## Club almanac suite (plan step 1c; Almanac.gd, AlmanacScene), behind the
## switch "club_almanac": a season's page is written at its end from the real
## results, kept across a save and load, an older save loads and shows only
## the seasons it has a record of, and with the switch off nothing is written
## and no way in is shown.
## Run through tests/run_almanac_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2031
const FEATURE := "club_almanac"
const Ran := preload("res://tests/functions_ran.gd")

var _played := false


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	_t("_test_switch_off")
	Features.set_on(FEATURE, true)
	_t("_test_written_at_season_end")
	_t("_test_save_round_trip")
	_t("_test_old_save")
	_t("_test_legends")
	_t("_test_rows_and_coach_record")
	_t("_test_screen")
	Features.clear(FEATURE)
	GameState.reset()
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Almanac", self))


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


func _play_season() -> void:
	GameState.reset()
	GameState.career_seed = SUITE_SEED
	GameState.replay_seed = SUITE_SEED
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var guard := 0
	while not GameState.season.is_season_over() and guard < 40:
		GameState.advance()
		guard += 1


func _hub_has_entry() -> bool:
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	Engine.get_main_loop().root.add_child(hub)
	var found := hub.find_child("HubAlmanac", true, false) != null
	hub.queue_free()
	return found


func _test_switch_off() -> void:
	Features.set_on(FEATURE, false)
	_play_season()
	_check(GameState.honour_roll.size() == 1, "The season is played to its end")
	_check(GameState.almanac.is_empty(), "Switch off: no almanac page is written")
	_check(not _hub_has_entry(), "Switch off: the Hub shows no way into the almanac")
	Features.set_on(FEATURE, true)
	_check(_hub_has_entry(), "Switch on: the Hub shows the way into the almanac")


func _test_written_at_season_end() -> void:
	_play_season()
	_check(GameState.almanac.size() == 1, "One almanac page is written at the season's end")
	var e: Dictionary = GameState.almanac[0]
	var roll: Dictionary = GameState.honour_roll.back()
	_check(int(e["year"]) == GameState.season_year and str(e["club"]) == "GEE", "The page is this season's, for your club")
	_check(int(e["ladder"]) == GameState.my_position() and int(e["ladder"]) == int(roll["my_position"]),
			"Ladder position is the real final ladder")
	_check("%d-%d-%d" % [int(e["w"]), int(e["l"]), int(e["d"])] == GameState.my_record(), "Record is the real one")
	_check(str(e["premier"]) == GameState.premier() and str(e["premier"]) != "", "The premier is the real premier")
	_check(bool(e["flag"]) == (GameState.premier() == "GEE"), "Your flag is marked only if you won it")
	_check(str(e["finals_tag"]) == str(roll.get("my_finals", "")), "The finals result matches the honour roll")
	_check(str(e["finals_text"]) != "", "The finals result is in words")
	var bf_ids := []
	for r in e["bf"]:
		bf_ids.append(str(r["id"]))
	var roll_bf := []
	for r in roll.get("my_bf", []):
		roll_bf.append(str(r["id"]))
	_check(bf_ids == roll_bf and (e["bf"] as Array).size() <= 1, "Club best and fairest is the awarded one")
	_check((e["brownlow"] as Array).size() == 1 and str(e["brownlow"][0].get("name", "")) != "",
			"The Brownlow winner is kept, by name")
	var gk: Dictionary = e["goalkicker"]
	var best := 0
	for id in GameState.season_tally:
		if str(GameState.season_tally[id]["club"]) == "GEE":
			best = maxi(best, int(GameState.season_tally[id]["goals"]))
	_check(not gk.is_empty() and int(gk["goals"]) == best and str(gk["name"]) != "",
			"Leading goalkicker is your club's top goalkicker (%s, best %d)" % [str(gk), best])
	_check((e["records"] as Array).size() >= 1, "A first season sets the league's records")
	_check(e.has(Almanac.STORY_KEY) and str(e[Almanac.STORY_KEY]) == "", "The story-of-the-season slot is there, empty")
	_played = true


func _test_save_round_trip() -> void:
	if not _played:
		_play_season()
	var before: Array = GameState.almanac.duplicate(true)
	_check(GameState.save_career(), "The career saves")
	GameState.reset()
	_check(GameState.almanac.is_empty(), "Reset clears the almanac")
	GameState.load_career()
	_check(GameState.almanac == before, "The almanac survives a save and load")


func _test_old_save() -> void:
	if not _played:
		_play_season()
	GameState.save_career()
	var state := CareerSave.read(GameState.save_path)
	state.erase("almanac")
	CareerSave.write(state, CareerSave.read_meta(GameState.save_path), GameState.save_path)
	_check(GameState.load_career(), "A save from before the almanac loads")
	_check(GameState.almanac.is_empty(), "Nothing is back-filled into an old save's almanac")
	var rows := Almanac.rows(GameState.almanac, GameState.honour_roll)
	_check(rows.size() == GameState.honour_roll.size() and bool(rows[0].get("partial", false)),
			"An old save shows only the seasons the honour roll has, marked partial")
	_check(Almanac.rows([], []).is_empty(), "No record anywhere: no season is shown")


func _test_legends() -> void:
	GameState.almanac = [{"year": int(GameState.season_year), "club": "GEE", "legends": []}]
	var vet := {"id": "V1", "name": "Old Hand", "career": {"games": 210, "goals": 40, "stints": [], "through": 2026, "unknown": []}}
	var kid := {"id": "K1", "name": "Short Stay", "career": {"games": 30, "goals": 5, "stints": [], "through": 2026, "unknown": []}}
	var rival := {"id": "R1", "name": "Their Man", "career": {"games": 300, "goals": 9, "stints": [], "through": 2026, "unknown": []}}
	var retired := [{"id": "V1", "club": "GEE"}, {"id": "K1", "club": "GEE"}, {"id": "R1", "club": "CARL"}]
	Almanac.add_legends(GameState, retired, {"V1": vet, "K1": kid, "R1": rival})
	var legends: Array = GameState.almanac[0]["legends"]
	_check(legends.size() == 1 and str(legends[0]["id"]) == "V1" and int(legends[0]["games"]) == 210,
			"Only your retirees past a legend's mark are kept (%s)" % str(legends))
	GameState.almanac = [{"year": int(GameState.season_year) - 1, "club": "GEE", "legends": []}]
	Almanac.add_legends(GameState, retired, {"V1": vet, "K1": kid, "R1": rival})
	_check((GameState.almanac[0]["legends"] as Array).is_empty(),
			"An older season's page never takes this rollover's legends")


func _test_rows_and_coach_record() -> void:
	var alm := [{"year": 2027, "club": "GEE", "w": 15, "l": 8, "d": 0, "finals_tag": "GF", "finals_w": 3, "finals_l": 0, "flag": true}]
	var roll := [{"year": 2026, "my_club": "GEE", "premier": "CARL", "runner_up": "GEE", "my_position": 2, "my_record": "16-7-0", "my_finals": "GF"},
			{"year": 2027, "my_club": "GEE", "premier": "GEE"}]
	var rows := Almanac.rows(alm, roll)
	_check(rows.size() == 2 and int(rows[0]["year"]) == 2027 and not rows[0].has("partial"), "Newest first; the almanac's own page wins")
	_check(str(rows[1]["finals_text"]) == "Runners-up", "An honour-roll season still says how the finals went")
	var t := Almanac.coach_record(rows)
	_check(t["seasons"] == 2 and t["w"] == 31 and t["l"] == 15 and t["flags"] == 1 and t["finals_years"] == 2 and t["finals_w"] == 3,
			"The coach's record adds up (%s)" % str(t))


func _test_screen() -> void:
	_play_season()
	var scene: Control = load("res://scenes/AlmanacScene.tscn").instantiate()
	Engine.get_main_loop().root.add_child(scene)
	var card := scene.find_child("AlmanacSeason_%d" % GameState.season_year, true, false)
	_check(card != null, "The almanac screen shows this season's page")
	_check(scene.find_child("CoachRecord", true, false) != null, "The almanac screen shows the coach's record")
	_check(card != null and card.find_child("Goalkicker", true, false) != null, "The page names the leading goalkicker")
	scene.queue_free()
