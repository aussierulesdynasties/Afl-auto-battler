extends RefCounted
## Legacy lore (bug bash 2026-11-23): each past season true to its era.
##   - every ground the AFL used carries its name of that season (York Park
##     was Aurora Stadium 2004-16, Manuka Oval StarTrack Oval 2013-15, ...)
##   - a Victorian club's home final is at that year's finals ground (the MCG;
##     the Gabba in 2020), never Victoria Park, Kardinia Park or Docklands
##   - a Legacy start's real players carry their record to the season before
##     the start, so every season of the career counts (it stopped at 1989)
##   - a club moving home or taking a new name gets one story before Round 1
##   - a new club's first senior coach is its real one when he is free
##   - a club's flags "before you" stop at the start (no 1991 flag in 1990)
##   - a save made before the fix gets its records repaired, the missed
##     seasons marked unknown rather than guessed
## Run through tests/run_legacy_lore_tests.gd.

const Ran := preload("res://tests/functions_ran.gd")

var failures: Array[String] = []
var checks := 0


func run() -> void:
	failures.clear()
	checks = 0
	_t("_test_ground_names")
	_t("_test_finals_grounds")
	_t("_test_career_counts_from_the_start")
	_t("_test_old_save_repaired")
	_t("_test_club_change_news")
	_t("_test_foundation_coaches")
	_t("_test_flags_before_the_start")
	GameState.reset()
	print(Ran.line("Legacy lore", self))


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures.append(what)
		push_error(what)


func _test_ground_names() -> void:
	var want := [["York Park", 2003, "York Park"], ["York Park", 2010, "Aurora Stadium"],
			["York Park", 2017, "UTAS Stadium"], ["Bellerive Oval", 2012, "Blundstone Arena"],
			["Bellerive Oval", 2025, "Ninja Stadium"], ["Engie Stadium", 2012, "Škoda Stadium"],
			["Engie Stadium", 2016, "Spotless Stadium"], ["Engie Stadium", 2020, "GIANTS Stadium"],
			["Engie Stadium", 2024, "Engie Stadium"], ["Manuka Oval", 2012, "Manuka Oval"],
			["Manuka Oval", 2014, "StarTrack Oval"], ["Manuka Oval", 2018, "UNSW Canberra Oval"],
			["Sky Stadium", 2014, "Westpac Stadium"], ["Mars Stadium", 2019, "Mars Stadium"],
			["Marrara Oval", 2004, "Marrara Oval"], ["Marrara Oval", 2006, "TIO Stadium"], ["Marrara Oval", 2025, "TIO Stadium"]]
	for w in want:
		var got := GameDB.ground_name(str(w[0]), int(w[1]))
		_check(got == str(w[2]), "%s in %d is %s, not %s" % [w[0], w[1], w[2], got])
	# Today's league keeps the game's own names.
	for g in ["York Park", "Bellerive Oval", "Engie Stadium", "Manuka Oval", "Mars Stadium", "Marrara Oval"]:
		_check(GameDB.ground_name(g, 2026) == g, "%s keeps its name in 2026 (%s)" % [g, GameDB.ground_name(g, 2026)])
	_check(GameDB.ground_renamed_from("York Park", 2004) == "York Park"
			and GameDB.ground_renamed_from("Manuka Oval", 2013) == "Manuka Oval",
			"A rename gets its story the season it happens")


func _test_finals_grounds() -> void:
	# [year, tag, host, away, ground]: where history sent that final (data/legacy/finals.csv).
	var cases := [
		[1990, "SF1", "WCE", "MEL", "Waverley Park"],   # West Coast's semi in Melbourne
		[1990, "EF", "STK", "HAW", "MCG"],
		[1995, "QF1", "COL", "SYD", "MCG"],
		[1995, "QF2", "COL", "SYD", "Waverley Park"],   # Essendon v West Coast at Waverley
		[2000, "EF1", "ESS", "WBD", "Marvel Stadium"],  # Geelong's elimination final at Docklands
		[2004, "PF2", "BRL", "GEE", "MCG"],             # Brisbane brought to the MCG
		[2010, "SF1", "STK", "WBD", "MCG"],
		[2013, "QF2", "GEE", "FRE", "GMHBA Stadium"],   # Geelong at Kardinia Park
		[2013, "QF2", "COL", "FRE", "MCG"],             # only Geelong goes to Geelong's ground
		[2020, "EF1", "STK", "WBD", "The Gabba"],
		[2020, "SF1", "RIC", "STK", "People First Stadium"],
		[2021, "EF1", "SYD", "GWS", "York Park"],       # Sydney's final in Launceston
		[2021, "EF2", "WBD", "ESS", "York Park"],
		[2021, "PF1", "MEL", "GEE", "Optus Stadium"],
	]
	for c in cases:
		GameDB.apply_era(int(c[0]))
		var s := Season.new(GameDB.active_clubs(int(c[0])), {}, 7, int(c[0]))
		var m := {"tag": str(c[1]), "home": str(c[2]), "away": str(c[3])}
		_check(s.finals_venue(m) == str(c[4]), "%d %s: %s host at %s, not %s" % [c[0], c[1], c[2], c[4], s.finals_venue(m)])
		_check(s.finals_at_home(m) == [s.home_ground(str(c[2])) == str(c[4]), s.home_ground(str(c[3])) == str(c[4])],
				"%d %s: only a club at its own ground has the edge" % [c[0], c[1]])
	# An interstate host at home whenever its real final was at home.
	for c in [[1995, "QF2", "WCE", "ESS"], [2010, "SF1", "ADE", "GEE"], [2004, "PF1", "PAD", "STK"],
			[2020, "QF1", "PAD", "GEE"]]:
		GameDB.apply_era(int(c[0]))
		var s := Season.new(GameDB.active_clubs(int(c[0])), {}, 7, int(c[0]))
		var v := s.finals_venue({"tag": str(c[1]), "home": str(c[2]), "away": str(c[3])})
		_check(v == s.home_ground(str(c[2])), "%d %s: %s host at home (%s), not %s" % [c[0], c[1], c[2], s.home_ground(str(c[2])), v])
	# No Victorian club ever hosts at its suburban ground in a real season.
	for y in range(1990, 2026):
		GameDB.apply_era(y)
		var s := Season.new(GameDB.active_clubs(y), {}, 7, y)
		for tag in SeasonRules.tags(s.finals_format()):
			if tag == "GF":
				continue
			for host in ["COL", "ESS", "STK", "WBD", "HAW", "CAR", "NTH"]:
				var v := s.finals_venue({"tag": tag, "home": host, "away": "SYD"})
				_check(v in ["MCG", "Waverley Park", "Marvel Stadium", "The Gabba", "People First Stadium",
						"Adelaide Oval", "Optus Stadium", "York Park"],
						"%d %s: %s never host at %s" % [y, tag, host, v])
	GameDB.apply_era(2026)
	var today := Season.new(GameDB.active_clubs(2026), {}, 7, 2026)
	_check(today.finals_venue({"tag": "QF1", "home": "STK", "away": "ESS"}) == today.home_ground("STK"),
			"The game's league keeps its own finals rule")


func _test_career_counts_from_the_start() -> void:
	for y in ["1990", "2010"]:
		GameState.reset(y)
		GameState.begin_real_lists()
		var start := int(y)
		var seen := 0
		var wrong := 0
		for code in GameState.league_lists:
			for p in GameState.league_lists[code]:
				var c: Dictionary = Career.of(p)
				seen += 1
				# A real record runs to the season before; a new draftee's is empty.
				if int(c.get("through", 0)) != start - 1 and not (int(c.get("through", 0)) == 0 and int(c["games"]) == 0):
					wrong += 1
		_check(seen > 0 and wrong == 0, "%s: every real record runs to %d (%d of %d do not)" % [y, start - 1, wrong, seen])
		var p: Dictionary = {}
		for code in GameState.league_lists:
			for x in GameState.league_lists[code]:
				if p.is_empty() and int(Career.of(x)["games"]) > 50:
					p = x
		var games := int(Career.of(p)["games"])
		_check(Career.add_season(p, start, str(p.get("club", "")), 20, 5) and int(Career.of(p)["games"]) == games + 20,
				"%s: the first season of the career counts" % y)
	GameState.reset()
	_check(Career.before_game() == Career.BEFORE_GAME, "Today's start keeps its records to 2025")


func _test_old_save_repaired() -> void:
	GameState.reset("1990")
	GameState.begin_real_lists()
	var p := {"id": "T1", "career": {"games": 50, "goals": 10, "stints": [["CAR", 1985, 1989, 50, 10]],
			"through": 2025, "unknown": []}}
	var q := {"id": "T2", "career": {"games": 0, "goals": 0, "stints": [], "through": 2025, "unknown": [[0, 2025]]}}
	GameState.free_agents = [p, q]
	GameState.season_year = 1992
	GameState._repair_legacy_careers()
	var c: Dictionary = p["career"]
	_check(int(c["through"]) == 1991 and c["unknown"] == [[1990, 1991]],
			"A broken record runs to the last closed season, the missed ones unknown (%s)" % str(c))
	_check((q["career"] as Dictionary)["unknown"] == [[0, 1989], [1990, 1991]], "An unknown past stays unknown (%s)" % str(q["career"]))
	GameState.reset()


func _test_club_change_news() -> void:
	GameState.reset("1990")
	GameState.replay_seed = 1990
	GameState.career_seed = 1990
	GameState.begin_real_lists()
	GameState.choose_real_club("FIT")
	var texts := func() -> String:
		return " | ".join(PackedStringArray(GameState.news.map(func(n): return str(n.get("text", "")))))
	GameState.season_year = 1992
	GameState.news.clear()
	GameState._club_change_news()
	var t: String = texts.call()
	_check(t.find("Hawthorn have a new home") >= 0 and t.find("Waverley") >= 0 or t.find("AFL Park") >= 0,
			"1992: Hawthorn's move to Waverley Park is told (%s)" % t)
	_check(t.find("Essendon have a new home") >= 0, "1992: Essendon's move to the MCG is told (%s)" % t)
	GameState.news.clear()
	GameState._club_change_news()
	_check(GameState.news.is_empty(), "A move is told once")
	GameState.season_year = 1994
	GameState.news.clear()
	GameState._club_change_news()
	_check(str(texts.call()).find("Fitzroy have a new home") < 0, "1994: Fitzroy's move is the year event's story, not a second one")
	GameState.season_year = 1997
	GameState.news.clear()
	GameState._club_change_news()
	_check(str(texts.call()).find("Footscray take a new name: from Round 1 they are the Western Bulldogs") >= 0,
			"1997: Footscray become the Western Bulldogs (%s)" % texts.call())
	GameState.reset()


func _test_foundation_coaches() -> void:
	var coaches := {}
	CoachMarket.staff_new_clubs(coaches, ["ADE"], "WBD", 1990, 7)
	var sc: Dictionary = coaches.get(str(Coaches.staff(coaches, "ADE").get("SC", "")), {})
	_check(str(sc.get("real_name", "")) == "Graham Cornes", "Adelaide's first coach is Graham Cornes (%s)" % sc.get("real_name", ""))
	# Kevin Sheedy still coaching Essendon in this career: GWS look elsewhere.
	coaches = {"C_kevin_sheedy": {"cid": "C_kevin_sheedy", "real_name": "Kevin Sheedy", "status": "club", "club": "ESS",
			"job": "SC", "skills": Coaches.ERA_SC_SKILLS.duplicate(), "stints": [], "spec": ""}}
	CoachMarket.staff_new_clubs(coaches, ["GWS"], "WBD", 2011, 7)
	sc = coaches.get(str(Coaches.staff(coaches, "GWS").get("SC", "")), {})
	_check(str(sc.get("real_name", "")) != "Kevin Sheedy" and not sc.is_empty(), "A real coach still in a senior job stays in it")
	coaches = {}
	CoachMarket.staff_new_clubs(coaches, ["TAS"], "WBD", 2027, 7)
	_check(not Coaches.staff(coaches, "TAS").is_empty(), "The game's own new clubs hire from the market as before")


func _test_flags_before_the_start() -> void:
	GameState.reset("1990")
	var haw: Dictionary = ClubHistory.before_career("HAW")
	_check(bool(haw["known"]) and (haw["years"] as Array).has(1989) and not (haw["years"] as Array).has(1991)
			and not (haw["years"] as Array).has(2008), "1990: Hawthorn's flags stop at 1989 (%s)" % str(haw["years"]))
	var wce: Dictionary = ClubHistory.before_career("WCE")
	_check(bool(wce["known"]) and (wce["years"] as Array).is_empty(), "1990: West Coast have no flag yet, and that is known")
	GameState.reset()
	_check((ClubHistory.before_career("HAW")["years"] as Array).has(2015), "Today's start keeps every flag to 2025")
