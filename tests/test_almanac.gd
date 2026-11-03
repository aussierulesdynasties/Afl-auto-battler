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
	_t("_test_club_records")
	_t("_test_story_with_match_story")
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
	_check(GameState.club_records.is_empty(), "Switch off: no club records are kept")
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
	var story := str(e.get(Almanac.STORY_KEY, ""))
	var n := story.count(". ") + 1
	_check(story != "" and n >= 2 and n <= 5, "The story of the season is up to 5 sentences: %s" % story)
	_check(str((e[Almanac.PARTS_KEY] as Dictionary).get("arc", "x")) == "", "The coach-arc slot is there, empty, for 1a")
	_trace(story, e, GameState.match_story_digest.get(str(int(e["year"])), {}))
	_check(GameState.news.any(func(x): return str(x["kind"]) == "almanac_story" and story.begins_with(str(x["text"]))),
			"The wrap's front item carries the story's first sentence")
	_check(GameState.club_records.size() >= 18, "Club records are kept for every club (%d)" % GameState.club_records.size())
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
	GameState.almanac = [{"year": int(GameState.season_year), "club": "GEE", "legends": [],
			Almanac.PARTS_KEY: {"result": "A.", "hero": "B.", "match": "C."}}]
	var vet := {"id": "V1", "name": "Old Hand", "career": {"games": 210, "goals": 40, "stints": [["GEE", 2010, 2026, 210, 40]], "through": 2026, "unknown": []}}
	# 250 career games but only 150 for your club: not a club legend on games.
	var kid := {"id": "K1", "name": "Short Stay", "career": {"games": 250, "goals": 5, "stints": [["CARL", 2010, 2015, 100, 2], ["GEE", 2016, 2026, 150, 3]], "through": 2026, "unknown": []}}
	var rival := {"id": "R1", "name": "Their Man", "career": {"games": 300, "goals": 9, "stints": [["CARL", 2010, 2026, 300, 9]], "through": 2026, "unknown": []}}
	var medal := {"id": "M1", "name": "Medallist", "honours": {"brownlow": 1}, "career": {"games": 60, "goals": 10, "stints": [["GEE", 2020, 2026, 60, 10]], "through": 2026, "unknown": []}}
	var skipper := {"id": "S1", "name": "Skipper", "honours": {"captain": {"GEE": 8}}, "career": {"games": 180, "goals": 10, "stints": [["GEE", 2018, 2026, 180, 10]], "through": 2026, "unknown": []}}
	var retired := [{"id": "V1", "club": "GEE"}, {"id": "K1", "club": "GEE"}, {"id": "R1", "club": "CARL"},
			{"id": "M1", "club": "GEE"}, {"id": "S1", "club": "GEE"}]
	Almanac.add_legends(GameState, retired, {"V1": vet, "K1": kid, "R1": rival, "M1": medal, "S1": skipper})
	var legends: Array = GameState.almanac[0]["legends"]
	var ids := legends.map(func(l): return str(l["id"]))
	_check(ids == ["V1", "M1", "S1"] and int(legends[0]["games"]) == 210,
			"Legends: 200 club games, a Brownlow, 8 seasons as captain; not 150 club games (%s)" % str(legends))
	_check(str(GameState.almanac[0].get(Almanac.STORY_KEY, "")).contains("Old Hand"), "The legends are added to the story")
	var hon := {"career": {"stints": []}, "honours": {"bf": {"GEE": 3}}}
	_check(not Almanac.legend_marks(hon, "GEE").is_empty(), "Three club best and fairests make a legend")
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
	_check(card != null and card.find_child("StoryOfTheSeason", true, false) != null, "The page tells the story of the season")
	_check(scene.find_child("ClubRecords", true, false) != null, "The almanac shows the club records")
	scene.queue_free()
	GameState.almanac[-1]["legends"] = [{"id": "L1", "name": "Legend One", "games": 220, "goals": 12, "why": ["220 games"]}]
	GameState.almanac.append({"year": int(GameState.season_year) + 1, "club": "GEE",
			"legends": [{"id": "L2", "name": "Legend Two", "games": 90, "goals": 410, "why": ["410 goals"]}]})
	scene = load("res://scenes/AlmanacScene.tscn").instantiate()
	Engine.get_main_loop().root.add_child(scene)
	var lc := scene.find_child("LegendsCard", true, false)
	_check(lc != null and lc.find_child("LegendRow_L1", true, false) != null and lc.find_child("LegendRow_L2", true, false) != null,
			"The legends card lists every legend")
	scene.queue_free()
	GameState.almanac.pop_back()


## Club records move only when beaten, are kept per club and survive a save.
func _test_club_records() -> void:
	GameState.club_records = {}
	var res := {"home": "GEE", "away": "CARL", "score": [100, 60], "label": "Round 1",
			"roster": [[{"id": "a", "name": "A"}], [{"id": "b", "name": "B"}]],
			"players": {"a": {"goals": 5, "disposals": 30}, "b": {"goals": 2, "disposals": 20}}}
	Almanac.update_club_records(GameState, [res])
	var g: Dictionary = GameState.club_records.get("GEE", {})
	_check(int(g.get("biggest_win", {}).get("value", 0)) == 40 and int(g.get("longest_win_streak", {}).get("value", 0)) == 1,
			"The first match sets your club's records (%s)" % str(g))
	_check(GameState.club_records.has("CARL"), "Every club's records are kept")
	var lower := res.duplicate(true)
	lower["score"] = [80, 60]
	lower["label"] = "Round 2"
	Almanac.update_club_records(GameState, [lower])
	_check(str(g.get("biggest_win", {}).get("label", "")).begins_with("Round 1"), "A record missed does not move")
	_check(int(g.get("longest_win_streak", {}).get("value", 0)) == 2, "Two wins running set the winning-run record")
	var higher := res.duplicate(true)
	higher["score"] = [150, 50]
	higher["label"] = "Round 3"
	Almanac.update_club_records(GameState, [higher])
	_check(int(g.get("biggest_win", {}).get("value", 0)) == 100, "A record beaten moves")
	var before := JSON.stringify(GameState.club_records)
	GameState.save_career()
	GameState.load_career()
	_check(JSON.stringify(GameState.club_records) == before, "Club records survive a save and load")


## With the match story on: the season hero is a named award on the honour
## roll and the almanac, and the story names him; every number traces.
func _test_story_with_match_story() -> void:
	Features.set_on("match_story", true)
	_play_season()
	var roll: Dictionary = GameState.honour_roll.back()
	var e: Dictionary = GameState.almanac.back()
	var d: Dictionary = GameState.match_story_digest.get(str(int(e["year"])), {})
	var sh: Array = roll.get("season_hero", [])
	_check(sh.size() == 1 and int(sh[0]["count"]) >= 1, "The honour roll names the season hero (%s)" % str(sh))
	if sh.size() == 1:
		var most := 0
		for id in d.get("heroes", {}):
			most = maxi(most, int(d["heroes"][id]["count"]))
		_check(int(sh[0]["count"]) == most, "The season hero has the most hero matches")
		_check(str(e[Almanac.STORY_KEY]).contains(str(sh[0]["name"])), "The story names the season hero")
	_check(e.get("season_hero", []) == sh, "The almanac page carries the season hero")
	var story := str(e[Almanac.STORY_KEY])
	print("  story %d: %s" % [int(e["year"]), story])
	_trace(story, e, d)
	Features.clear("match_story")


## Every number in the story appears in the entry or the digest.
func _trace(story: String, e: Dictionary, d: Dictionary) -> void:
	var src := e.duplicate(true)
	src.erase(Almanac.STORY_KEY)
	src.erase(Almanac.PARTS_KEY)
	var nums := {}
	for m in RegEx.create_from_string("\\d+").search_all(JSON.stringify(src) + " " + JSON.stringify(d)):
		nums[str(int(m.get_string()))] = true
	for m in RegEx.create_from_string("\\d+").search_all(story):
		_check(nums.has(str(int(m.get_string()))), "The story's %s traces to the entry or digest" % m.get_string())
