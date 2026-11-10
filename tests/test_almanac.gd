extends RefCounted
## Club almanac suite (plan step 1c; Almanac.gd, AlmanacScene): a season's
## page is written at its end from the real results, kept across a save and
## load, an older save loads and shows only the seasons it has a record of,
## and the Hub shows the way in.
## Run through tests/run_almanac_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2031
const Ran := preload("res://tests/functions_ran.gd")

var _played := false


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	_t("_test_hub_entry")
	_t("_test_written_at_season_end")
	_t("_test_save_round_trip")
	_t("_test_old_save")
	_t("_test_legends")
	_t("_test_rows_and_coach_record")
	_t("_test_screen")
	_t("_test_club_records")
	_t("_test_story_finals_result")
	_t("_test_story_with_match_story")
	_t("_test_arc_bank_is_sound")
	_t("_test_arc_season_shapes")
	_t("_test_arc_old_page")
	_t("_test_challenge_goal_marked")
	_t("_test_homegrown_flag")
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


func _test_hub_entry() -> void:
	_play_season()
	_check(GameState.honour_roll.size() == 1, "The season is played to its end")
	_check(_hub_has_entry(), "The Hub shows the way into the almanac")


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
	# Row 145: the season's shape, from the record the page keeps.
	var arc: Dictionary = e.get(Almanac.ARC_KEY, {})
	var form := ""
	_check(GameState.season.results.size() >= 20, "The season's rounds are there to read (%d)" % GameState.season.results.size())
	for rnd in GameState.season.results:
		for res in rnd:
			if GameState.is_my_match(res):
				var mine := 0 if str(res["home"]) == "GEE" else 1
				var diff := int(res["score"][mine]) - int(res["score"][1 - mine])
				form += "W" if diff > 0 else ("L" if diff < 0 else "D")
	_check(str(arc.get("form", "")) == form and form != "", "The page keeps your results in order (%s)" % str(arc.get("form", "")))
	_check(form.count("W") == int(e["w"]) and form.count("L") == int(e["l"]) and form.count("D") == int(e["d"]),
			"The kept results add up to the ladder's record (%s, %s)" % [form, GameState.my_record()])
	_check((arc.get("rounds", []) as Array).size() == form.length(), "Each kept result has its round")
	var fin := str(arc.get("finals", ""))
	_check(fin.count("W") == int(e["finals_w"]) and fin.count("L") == int(e["finals_l"]), "The kept finals match the finals record (%s)" % fin)
	var said := str((e[Almanac.PARTS_KEY] as Dictionary).get("arc", "x"))
	_check(said == SeasonTale.sentence(arc, int(e["year"]), "GEE"), "The arc sentence is written from the kept facts: %s" % said)
	_check((said == "") == (str(arc.get("angle", "")) == ""), "A sentence only when the season has a shape")
	_arc_true(arc, said, bool(e["flag"]))
	_check(said == "" or story.contains(said), "The story carries the arc sentence")
	print("  arc %d: %s [finals %s] %s" % [int(e["year"]), form, fin if fin != "" else "none", said if said != "" else "(nothing said)"])
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
	var medals := Almanac.legend_marks({"career": {"stints": []}, "honours": {"brownlow": 2, "norm_smith": 1}}, "GEE")
	_check(medals.has("2 Brownlows") and medals.has("1 Norm Smith"), "Medal counts read as plurals past one (%s)" % str(medals))
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
	var bfr := card.find_child("BestAndFairest", true, false) if card != null else null
	var bfl := str((bfr.get_child(0) as Label).text) if bfr != null else ""
	_check(bfr != null and bfl == BestAndFairest.award_name("GEE"), "The best and fairest row carries the medal's name (%s)" % bfl)
	_check(BestAndFairest.award_name("GEE") == "Carji Greeves Medal", "Geelong's medal is the Carji Greeves Medal")
	scene.queue_free()
	GameState.almanac[-1]["legends"] = [{"id": "L1", "name": "Legend One", "games": 220, "goals": 12, "why": ["220 games"]}]
	GameState.almanac.append({"year": int(GameState.season_year) + 1, "club": "GEE",
			"legends": [{"id": "L2", "name": "Legend Two", "games": 90, "goals": 410, "why": ["410 goals"]}]})
	scene = load("res://scenes/AlmanacScene.tscn").instantiate()
	Engine.get_main_loop().root.add_child(scene)
	var lc := scene.find_child("LegendsCard", true, false)
	_check(lc != null and lc.find_child("LegendRow_L1", true, false) != null and lc.find_child("LegendRow_L2", true, false) != null,
			"The legends card lists every legend")
	var AS = load("res://scripts/ui/AlmanacScene.gd")
	_check(AS.games_goals(250, 1) == "250 games, 1 goal" and AS.games_goals(1, 0) == "1 game, 0 goals",
			"A legend's career line counts in the singular at one")
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


## The match story: the season hero is a named award on the honour
## roll and the almanac, and the story names him; every number traces.
func _test_story_with_match_story() -> void:
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


## The story's result sentence follows the club's own finals: a club that
## played no final is never said to have played one; one that did is told
## the week it went out.
func _test_story_finals_result() -> void:
	var base := {"year": 2030, "club": "GEE", "ladder": 11, "of": 18, "w": 10, "l": 13, "d": 0, "flag": false}
	var miss := base.duplicate()
	miss["finals_tag"] = ""
	miss["finals_text"] = Almanac.finals_text("", false, false)
	var r := str(Almanac.story_parts(miss, {})["result"])
	_check(r.contains("missed the finals") and not r.contains("went out"), "A non-finalist missed the finals: %s" % r)
	for tag in ["WC1", "EF2", "SF1", "PF1"]:
		var e := base.duplicate()
		e["ladder"] = 7
		e["finals_tag"] = tag
		e["finals_text"] = Almanac.finals_text(tag, false, false)
		var t := str(Almanac.story_parts(e, {})["result"])
		_check(t.contains("went out in " + str(e["finals_text"]).trim_prefix("Out in ")) and not t.contains("in the finals."),
				"A finalist is told the week he went out (%s): %s" % [tag, t])
	for e in GameState.almanac:
		var played := str(e.get("finals_tag", "")) != ""
		var story := str(e.get(Almanac.STORY_KEY, ""))
		if not played and story != "":
			_check(not story.contains("went out") and not story.contains("Grand Final") or bool(e.get("flag", false)),
					"A season without a final never says it played one: %s" % story)


## Row 114: Your goal is marked in the annual, once, on the season it is met;
## the coach card says where it stands; a save keeps it; a save from before
## challenges loads with none.
func _test_challenge_goal_marked() -> void:
	GameState.reset()
	GameState.career_seed = SUITE_SEED
	GameState.replay_seed = SUITE_SEED
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState.challenge = {"kind": "goal", "goal": "coach_300", "met_year": 0}
	# 290 games already coached: this season takes him past 300.
	GameState.almanac = [{"year": GameState.season_year - 1, "club": "GEE", "w": 200, "l": 90, "d": 0}]
	_check(Challenge.status_line(GameState) == "Coach 300 games. 290 so far.",
			"Before it is met, the coach card says how far along it is (%s)" % Challenge.status_line(GameState))
	var guard := 0
	while not GameState.season.is_season_over() and guard < 40:
		GameState.advance()
		guard += 1
	var year := GameState.season_year
	var page: Dictionary = GameState.almanac[-1]
	_check(int(page.get("year", 0)) == year and str(page.get("challenge_met", "")) == "Coach 300 games",
			"The season the goal is met, its page marks it (%s)" % str(page.get("challenge_met", "")))
	_check(int(GameState.challenge.get("met_year", 0)) == year, "The goal remembers the year it was met")
	_check(Challenge.status_line(GameState) == "Coach 300 games. Met in %d." % year,
			"The coach card says it was met, and when (%s)" % Challenge.status_line(GameState))
	var next := {"year": year + 1, "club": "GEE", "w": 15, "l": 8, "d": 0}
	Challenge.mark_season(GameState, next)
	_check(not next.has("challenge_met"), "A goal already met is never marked again")
	var scene: Control = load("res://scenes/AlmanacScene.tscn").instantiate()
	Engine.get_main_loop().root.add_child(scene)
	var card := scene.find_child("AlmanacSeason_%d" % year, true, false)
	_check(card != null and card.find_child("ChallengeMet", true, false) != null, "The annual's page for that season shows the goal met")
	_check(scene.find_child("CoachGoal", true, false) != null, "The coach card shows your goal")
	scene.queue_free()
	_check(GameState.save_career() and GameState.load_career(), "(setup) the career saves and loads")
	_check(str(GameState.challenge.get("kind", "")) == "goal" and int(GameState.challenge.get("met_year", 0)) == year,
			"The challenge survives a save (%s)" % str(GameState.challenge))
	var state := CareerSave.read(GameState.save_path)
	state.erase("challenge")
	CareerSave.write(state, CareerSave.read_meta(GameState.save_path), GameState.save_path)
	_check(GameState.load_career() and GameState.challenge.is_empty() and Challenge.kind(GameState) == "",
			"A save from before challenge starts loads with none")
	# A flag is not met without a Grand Final side drafted by your club, and a
	# season without a flag never meets it.
	GameState.challenge = {"kind": "goal", "goal": "flag_homegrown", "met_year": 0}
	var plain := {"year": year, "club": "GEE", "flag": false}
	Challenge.mark_season(GameState, plain)
	_check(not plain.has("challenge_met"), "No flag: the home-grown flag goal is not met")
	GameState.challenge = {}


## Row 114: the home-grown flag is met when every player your club sent out
## in the Grand Final was first drafted by your club, home side or away, and
## not when one of them came from elsewhere.
func _test_homegrown_flag() -> void:
	GameState.reset()
	GameState.career_seed = SUITE_SEED
	GameState.replay_seed = SUITE_SEED
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var side := []
	for p in GameState.my_list.slice(0, 23):
		p["drafted_club"] = "GEE"
		side.append({"id": str(p["id"])})
	var theirs := []
	for p in (GameState.season.lists["COL"] as Array).slice(0, 23):
		theirs.append({"id": str(p["id"])})
	var finals_was: Dictionary = GameState.season.finals
	GameState.season.finals = {"weeks": [[{"tag": "GF", "home": "GEE", "away": "COL", "roster": [side, theirs]}]]}
	GameState.challenge = {"kind": "goal", "goal": "flag_homegrown", "met_year": 0}
	_check(Challenge.homegrown_flag(GameState), "A Grand Final side all drafted by your club is home-grown")
	var page := {"year": GameState.season_year, "club": "GEE", "flag": true}
	Challenge.mark_season(GameState, page)
	_check(str(page.get("challenge_met", "")) == "Win a flag with a home-grown 22",
			"A flag with that side meets the goal (%s)" % str(page.get("challenge_met", "")))
	GameState.challenge = {"kind": "goal", "goal": "flag_homegrown", "met_year": 0}
	GameState.season.finals = {"weeks": [[{"tag": "GF", "home": "COL", "away": "GEE", "roster": [theirs, side]}]]}
	_check(Challenge.homegrown_flag(GameState), "As the away side too")
	GameState.my_list[5]["drafted_club"] = "COL"
	_check(not Challenge.homegrown_flag(GameState), "One player first drafted elsewhere and it is not home-grown")
	GameState.my_list[5].erase("drafted_club")
	_check(not Challenge.homegrown_flag(GameState), "A player with no drafting club (a save from before) is not home-grown")
	GameState.season.finals = {"weeks": [[{"tag": "GF", "home": "COL", "away": "RIC", "roster": [theirs, theirs]}]]}
	_check(not Challenge.homegrown_flag(GameState), "A Grand Final you were not in never counts")
	GameState.season.finals = finals_was
	GameState.challenge = {}
	# Real players carry the club that drafted them: the first club of their
	# AFL career (Jordan Dawson, Adelaide's #12, was drafted by Sydney).
	var dawson := GameDB.club_list("ADE").filter(func(q): return str(q["id"]) == "ADE_12")
	_check(not dawson.is_empty() and str(dawson[0].get("drafted_club", "")) == "SYD",
			"A real player's drafting club is his first AFL club (%s)" % (str(dawson[0].get("drafted_club", "")) if not dawson.is_empty() else "-"))


# ---------------------------------------------------------------------------
# Row 145: the season's shape in one sentence (SeasonTale.gd)
# ---------------------------------------------------------------------------
## Every angle has phrases, and no phrase uses a slot its angle does not declare.
func _test_arc_bank_is_sound() -> void:
	var bank := SeasonTale.bank()
	_check(CareerTale.validate(bank).is_empty(), "The season phrase bank is sound: %s" % str(CareerTale.validate(bank)))
	_check(SeasonTale.WEIGHT.size() == 8, "Eight angles are weighed (%d)" % SeasonTale.WEIGHT.size())
	for a in SeasonTale.WEIGHT:
		_check(bank.has(a), "The bank has phrases for %s" % a)
	for a in bank:
		_check(SeasonTale.WEIGHT.has(a), "No phrase without an angle that can be told: %s" % a)
		for ph in bank[a]["coach"]:
			_check(RegEx.create_from_string("\\d").search(str(ph)) == null, "No number is written into a phrase: %s" % str(ph))


## A season's rounds in Season.results' shape from one letter a round ("-" is
## your bye), with seeded scores and another match beside yours each round.
func _arc_rounds(form: String, rng: RandomNumberGenerator) -> Array:
	var out := []
	for i in form.length():
		var rnd := [{"home": "FRE", "away": "MEL", "score": [60 + rng.randi() % 60, 60 + rng.randi() % 60]}]
		if form[i] != "-":
			var low := 40 + rng.randi() % 60
			var high := low + (0 if form[i] == "D" else 1 + rng.randi() % 50)
			var home := rng.randi() % 2 == 0
			var mine := high if form[i] == "W" else low
			var theirs := low if form[i] == "W" else high
			rnd.append({"home": "GEE" if home else "STK", "away": "STK" if home else "GEE",
					"score": [mine, theirs] if home else [theirs, mine]})
		out.append(rnd)
	return out


## A hand-built page for a season of the given shape, as the season's close writes it.
func _arc_page(year: int, form: String, finals: String, flag: bool) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = SUITE_SEED + year
	var weeks := _arc_rounds(finals, rng)
	var rec := SeasonTale.record(_arc_rounds(form, rng), weeks, "GEE")
	var tag := "GF" if flag else ("" if finals == "" else "EF1")
	var e := {"year": year, "club": "GEE", "ladder": 1 if flag else 12, "of": 18,
			"w": form.count("W"), "l": form.count("L"), "d": form.count("D"), "flag": flag,
			"finals_tag": tag, "finals_text": Almanac.finals_text(tag, flag, false), "legends": []}
	_check(str(rec["form"]) == form.replace("-", "") and str(rec["finals"]) == finals,
			"%d: the record reads the results back in order (%s)" % [year, str(rec["form"])])
	e[Almanac.ARC_KEY] = SeasonTale.tell(rec, flag)
	e[Almanac.PARTS_KEY] = Almanac.story_parts(e, {})
	e[Almanac.STORY_KEY] = Almanac.compose(e[Almanac.PARTS_KEY])
	return e


## The kept facts are true of the kept results, counted again here another way,
## and every number in the sentence is one of those facts.
func _arc_true(arc: Dictionary, said: String, flag: bool) -> void:
	var angle := str(arc.get("angle", ""))
	var f: Dictionary = arc.get("facts", {})
	var form := str(arc.get("form", ""))
	var rounds: Array = arc.get("rounds", [])
	var all := form + str(arc.get("finals", ""))
	_check(angle != "" or f.is_empty(), "No facts without an angle")
	if angle in ["surge", "fade"]:
		var half := int(form.length() / 2.0)
		var first := form.left(half)
		var late := form.right(form.length() - half)
		_check(int(f["first_w"]) == first.count("W") and int(f["first_l"]) == first.count("L")
				and int(f["first_d"]) == first.count("D"), "%s: the first half's record is counted from the results" % angle)
		_check(int(f["late_w"]) == late.count("W") and int(f["late_n"]) == late.length(),
				"%s: the second half's wins are counted from the results" % angle)
		_check(int(f["split_round"]) == int(rounds[half - 1]), "%s: the split is the round of the last first-half game" % angle)
		var before := float(first.count("W")) / first.length()
		var after := float(late.count("W")) / late.length()
		_check((after > before) == (angle == "surge") and absf(after - before) >= 0.29,
				"%s: the win rate moved that way (%.2f to %.2f)" % [angle, before, after])
	elif angle != "":
		var c := "W" if angle in ["run_to_flag", "won_first", "win_run"] else "L"
		var run := int(f["run"])
		_check(run >= SeasonTale.RUN and all.contains(c.repeat(run)) and not all.contains(c.repeat(run + 1)),
				"%s: %d on end is the longest run in the results (%s)" % [angle, run, all])
		if angle in ["won_first", "lost_first"]:
			_check(all.begins_with(c.repeat(run)), "%s: the run opens the season" % angle)
		if angle in ["run_to_flag", "lost_last"]:
			_check(all.ends_with(c.repeat(run)), "%s: the run closes the season" % angle)
		if angle == "run_to_flag":
			_check(flag, "run_to_flag: only in a premiership season")
		if angle in ["win_run", "lose_run"]:
			_check(int(f["from_round"]) == int(rounds[all.find(c.repeat(run))]), "%s: the run starts in the round said" % angle)
	var nums := {}
	for k in f:
		nums[str(int(f[k]))] = true
	for m in RegEx.create_from_string("\\d+").search_all(said):
		_check(nums.has(m.get_string()), "The arc's %s is a kept fact (%s; %s)" % [m.get_string(), said, str(f)])


## Seeded seasons of each shape: a flag, a wooden spoon, a late surge, a fade, a
## run after the bye, and a mid-table year that has no shape and says nothing.
## Each sentence is pinned, traced to its facts, and kept across a save and load.
func _test_arc_season_shapes() -> void:
	# [form, finals, flag, angle, facts, what the sentence must say]
	var shapes := [
		["WLWWLWWWLWWW-WLWWWWWWWWW", "WWW", true, "run_to_flag", {"run": 12},
				["We won our last 12 games, the Grand Final the last of them."]],
		["LLLLLLLLWLLL-LLWLLLLDLLL", "", false, "lost_first", {"run": 8}, ["We lost our first 8 games."]],
		["LLWLLLWLLWLW-WWLWWWLWWLW", "", false, "surge",
				{"first_w": 3, "first_l": 8, "first_d": 0, "split_round": 11, "late_w": 9, "late_n": 12},
				["3-8 after Round 11", "won 9 of the next 12."]],
		["WWLWWWWDWWWL-LWLLDLLWLLL", "", false, "fade",
				{"first_w": 9, "first_l": 1, "first_d": 1, "split_round": 11, "late_w": 2, "late_n": 12},
				["We were 9-1-1 after Round 11", "won 2 of the next 12."]],
		["WWLWWLWLWLWL-WWWWWWLLWLL", "L", false, "win_run", {"run": 6, "from_round": 14},
				["We won 6 in a row from Round 14."]],
		["WLWLLWWLWLWL-WWLLWLWWLLW", "", false, "", {}, []],
	]
	var pages := []
	for i in shapes.size():
		var sh: Array = shapes[i]
		var e := _arc_page(2040 + i, sh[0], sh[1], sh[2])
		var arc: Dictionary = e[Almanac.ARC_KEY]
		var said := str(e[Almanac.PARTS_KEY]["arc"])
		var name := str(sh[3]) if str(sh[3]) != "" else "no shape"
		_check(str(arc.get("angle", "")) == str(sh[3]), "%s tells %s (told %s)" % [sh[0], name, str(arc.get("angle", ""))])
		_check(arc.get("facts", {}) == sh[4], "%s keeps the facts %s (kept %s)" % [name, str(sh[4]), str(arc.get("facts", {}))])
		for want in sh[5]:
			_check(said.contains(str(want)), "%s says \"%s\": %s" % [name, want, said])
		if str(sh[3]) == "":
			_check(said == "" and not arc.has("facts"), "A season with no shape says nothing: %s" % said)
			_check(not str(e[Almanac.STORY_KEY]).contains("We "), "Its story has no arc sentence: %s" % str(e[Almanac.STORY_KEY]))
		else:
			_check(said.ends_with(".") and said.count(". ") == 0, "One sentence: %s" % said)
			_check(str(e[Almanac.STORY_KEY]).ends_with(said), "The story ends on the arc sentence: %s" % str(e[Almanac.STORY_KEY]))
		_arc_true(arc, said, bool(sh[2]))
		_check(str(Almanac.story_parts(e, {})["arc"]) == said, "The same season reads the same every time")
		print("  arc shape %s: %s" % [name, str(e[Almanac.STORY_KEY])])
		pages.append(e)
	# A season too short to have a shape, and a record that does not line up.
	_check(SeasonTale.beats({"form": "WWWWWWWWW", "rounds": [1, 2, 3, 4, 5, 6, 7, 8, 9], "finals": ""}, false).is_empty(),
			"Nine games is too short a season to tell")
	_check(SeasonTale.beats({"form": "WWWWWWWWWWWW", "rounds": [1, 2], "finals": ""}, false).is_empty(),
			"Results without their rounds tell nothing")
	# Kept across a save and load, and still written from what was kept.
	var own: Array = GameState.almanac.duplicate(true)
	GameState.almanac.append_array(pages)
	var before: Array = GameState.almanac.duplicate(true)
	_check(GameState.save_career(), "The career saves with the arc pages")
	GameState.reset()
	GameState.load_career()
	_check(GameState.almanac == before, "Every page's arc survives a save and load")
	_check(GameState.almanac.size() == own.size() + shapes.size(), "Every shape's page came back (%d)" % GameState.almanac.size())
	for e in GameState.almanac.slice(own.size()):
		var said := SeasonTale.sentence(e.get(Almanac.ARC_KEY, {}), int(e["year"]), str(e["club"]))
		_check(said == str(e[Almanac.PARTS_KEY]["arc"]), "After the load the sentence is still its kept facts: %s" % said)
		_arc_true(e.get(Almanac.ARC_KEY, {}), said, bool(e["flag"]))
	GameState.almanac = own


## A page written before the arc was kept: the save loads, the page reads as it
## did, and nothing is invented for it.
func _test_arc_old_page() -> void:
	var own: Array = GameState.almanac.duplicate(true)
	var old := _arc_page(2050, "LLWLLLWLLWLW-WWLWWWLWWLW", "", false)
	old.erase(Almanac.ARC_KEY)
	old[Almanac.PARTS_KEY] = Almanac.story_parts(old, {})
	old[Almanac.STORY_KEY] = Almanac.compose(old[Almanac.PARTS_KEY])
	var story := str(old[Almanac.STORY_KEY])
	_check(str(old[Almanac.PARTS_KEY]["arc"]) == "" and story != "", "A page without the kept record has no arc sentence")
	GameState.almanac.append(old.duplicate(true))
	_check(GameState.save_career(), "The career saves with the older page")
	GameState.reset()
	_check(GameState.load_career(), "A save with a page from before the arc loads")
	var back: Dictionary = GameState.almanac.back()
	_check(not back.has(Almanac.ARC_KEY) and str(back[Almanac.STORY_KEY]) == story, "The older page reads as it did: %s" % str(back.get(Almanac.STORY_KEY, "")))
	_check(str(Almanac.story_parts(back, {})["arc"]) == "", "Nothing is back-filled into an older page")
	_check(SeasonTale.sentence({}, 2050, "GEE") == "" and SeasonTale.sentence({"angle": "surge"}, 2050, "GEE") != "",
			"An empty arc says nothing, and a part-kept one never breaks the page")
	var scene: Control = load("res://scenes/AlmanacScene.tscn").instantiate()
	Engine.get_main_loop().root.add_child(scene)
	_check(scene.find_children("StoryOfTheSeason", "", true, false).size() >= 1, "The almanac screen still draws its stories")
	scene.queue_free()
	GameState.almanac = own
