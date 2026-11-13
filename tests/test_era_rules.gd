extends RefCounted
## Legacy mode season rules by year (row 142, phase L4): list sizes, the
## rookie list (1997 on), Category B, free agency (2012 on), the mid-season
## draft, the interchange bench and the substitute each follow the season
## being played (data/legacy/era_rules.csv, EraRules) and switch at the
## rollover. 2026 on is the game's own rules, unchanged.
## Run through tests/run_era_rules_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 1990


func run() -> void:
	failures.clear()
	checks = 0
	GameDB.reload()
	GameState.replay_seed = SUITE_SEED
	_t("_test_game_values_are_the_constants")
	_t("_test_rule_table")
	_t("_test_today_is_untouched")
	_t("_test_1990_season")
	_t("_test_rollover_1990_to_1991")
	_t("_test_rollover_1993_to_1994")
	_t("_test_rollover_1996_to_1997")
	_t("_test_rollover_2011_to_2012")
	_t("_test_rollover_2025_to_2026")
	_t("_test_tactical_sub_2011")
	_t("_test_medical_sub_2021")
	_t("_test_no_sub_2016")
	GameState.reset()
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	EraRules.year = 0
	EraRules.list_ahead = false
	print(Ran.line("Era rules", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## A career whose first season is `year` (the 1990 lists are not shipped yet,
## so today's lists stand in: the rules are what is under test).
func _career(year: int, club := "GEE") -> void:
	GameState.reset()
	GameState.season_year = year
	GameState.start_season(club, GameDB.club_list(club))


## The season's home-and-away rounds are skipped; the finals are played.
func _to_offseason() -> void:
	GameState.season.round_index = GameState.season.fixture.size()
	GameState.ensure_finals()
	var guard := 0
	while not GameState.season.is_season_over() and guard < 10:
		guard += 1
		GameState.advance()


## The off-season, then the rollover into the next season.
func _roll() -> bool:
	_to_offseason()
	GameState.open_offseason()
	GameState._close_free_agency()
	return GameState.start_next_season()


## Every list in the league is within the season's limits.
func _lists_within(label: String) -> void:
	var over := []
	for code in GameState.season.lists:
		var list: Array = GameState.season.lists[code]
		if list.size() > Contracts.max_list() or RookieList.senior_count(list) > RookieList.senior_spots():
			over.append("%s %d" % [code, list.size()])
	_check(over.is_empty(), "%s: every list within %d (%d senior): %s" % [label, Contracts.max_list(),
			RookieList.senior_spots(), str(over.slice(0, 5))])


## A match of `year` between Geelong and Carlton on `seed`.
func _match(year: int, seed: int) -> MatchSim:
	EraRules.year = year
	EraRules.list_ahead = false
	var sim := MatchSim.new(Squad.new("GEE", GameDB.club_list("GEE"), true, "GEE"),
			Squad.new("CAR", GameDB.club_list("CAR"), false, "CAR"), seed)
	sim.run()
	return sim


## `kind` "substitute": the substitute's own "sub" events, not interchange rotations.
func _events(sim: MatchSim, kind: String) -> Array:
	var out := []
	for e in sim.events:
		if (kind == "substitute" and bool(e.get("substitute", false))) or str(e.get("kind", "")) == kind:
			out.append(e)
	return out


## Today's constants are GAME's values: a 2026 career reads them unchanged.
func _test_game_values_are_the_constants() -> void:
	_check(int(EraRules.GAME["senior_list_max"]) == RookieList.SENIOR_SPOTS
			and int(EraRules.GAME["rookie_list_max"]) == RookieList.CAT_A_SPOTS
			and int(EraRules.GAME["cat_b_rookie"]) == RookieList.CAT_B_SPOTS,
			"GAME's list sizes are RookieList's constants")
	_check(int(EraRules.GAME["senior_list_max"]) + int(EraRules.GAME["rookie_list_max"]) == Contracts.MAX_LIST,
			"GAME's list total is Contracts.MAX_LIST")
	_check(int(EraRules.GAME["interchange"]) == Ratings.INTERCHANGE and int(EraRules.GAME["substitutes"]) == 0,
			"GAME's bench is Ratings.INTERCHANGE with no substitute")


## Each change year reads its own rules from the record.
func _test_rule_table() -> void:
	# year: [bench, subs, medical, senior, cat A, cat B, rookie list, free agency, mid-season draft]
	var rows := {
		1990: [2, 0, false, 52, 0, 0, false, false, true],
		1993: [2, 0, false, 52, 0, 0, false, false, true],
		1994: [3, 0, false, 42, 0, 0, false, false, false],
		1997: [3, 0, false, 42, 6, 0, true, false, false],
		1998: [4, 0, false, 42, 6, 0, true, false, false],
		2001: [4, 0, false, 40, 6, 0, true, false, false],
		2006: [4, 0, false, 40, 6, 2, true, false, false],
		2009: [4, 0, false, 40, 8, 2, true, false, false],
		2011: [3, 1, false, 40, 8, 2, true, false, false],
		2012: [3, 1, false, 40, 8, 2, true, true, false],
		2013: [3, 1, false, 40, 6, 2, true, true, false],
		2016: [4, 0, false, 40, 6, 2, true, true, false],
		2019: [4, 0, false, 40, 6, 2, true, true, true],
		2021: [4, 1, true, 38, 6, 2, true, true, true],
		2025: [4, 1, true, 38, 6, 2, true, true, true],
		2026: [5, 0, false, 38, 6, 2, true, true, true],
		2027: [5, 0, false, 38, 6, 2, true, true, true],
	}
	for y in rows:
		var want: Array = rows[y]
		var got := [EraRules.interchange(y), EraRules.substitutes(y), EraRules.medical_sub(y),
				EraRules.senior_spots(y), EraRules.cat_a_spots(y), EraRules.cat_b_spots(y),
				EraRules.on("rookie_list", y), EraRules.on("free_agency", y), EraRules.on("midseason_draft", y)]
		_check(str(got) == str(want), "%d rules %s, want %s" % [y, str(got), str(want)])
	# Every era season has a list size and a bench of its own in the record.
	for y in range(1990, 2026):
		_check(EraRules.has("senior_list_max", y) and EraRules.has("interchange", y),
				"%d has a senior list size and a bench in era_rules.csv" % y)


## Year 0 and today's seasons read GAME, whatever the record holds.
func _test_today_is_untouched() -> void:
	for y in [0, 2026, 2027, 2040]:
		EraRules.year = y
		EraRules.list_ahead = false
		_check(Ratings.bench() == Ratings.bench_size and Ratings.subs() == 0
				and Contracts.max_list() == Contracts.MAX_LIST
				and RookieList.senior_spots() == RookieList.SENIOR_SPOTS
				and RookieList.cat_a_spots() == RookieList.CAT_A_SPOTS
				and RookieList.cat_b_spots() == RookieList.CAT_B_SPOTS
				and RookieList.in_force() and EraRules.on("free_agency") and EraRules.on("midseason_draft"),
				"%d: bench, lists and switches are the game's" % y)
	_career(GameDB.START_YEAR)
	var sq := Squad.new("GEE", GameState.my_list, true, "GEE")
	_check(sq.bench.size() == Ratings.INTERCHANGE and sq.sub.is_empty(),
			"A %d side names %d on the bench and no substitute" % [GameDB.START_YEAR, sq.bench.size()])


## A 1990 season: two on the bench, a 52-man list, no rookie list.
func _test_1990_season() -> void:
	_career(1990)
	_check(EraRules.year == 1990 and not EraRules.list_ahead, "The season sets the rules year")
	_check(Ratings.bench() == 2 and Ratings.subs() == 0, "1990: two interchange players, no substitute")
	_check(Contracts.max_list() == 52 and RookieList.cat_a_spots() == 0 and not RookieList.in_force(),
			"1990: a 52-man list and no rookie list")
	var sq := Squad.new("GEE", GameState.my_list, true, "GEE")
	_check(sq.ground.size() == 18 and sq.bench.size() == 2 and sq.sub.is_empty(),
			"A 1990 side is 18 and two (%d and %d)" % [sq.ground.size(), sq.bench.size()])


## 1990 to 1991: no rookie draft, no free agency, still two on the bench.
func _test_rollover_1990_to_1991() -> void:
	_career(1990)
	_to_offseason()
	GameState.open_offseason()
	_check(EraRules.list_ahead and Contracts.max_list() == 52, "The 1990 off-season plans 1991's 52-man lists")
	var testing := 0
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			if GameState.tests_market(p, GameState.season.lists[code]):
				testing += 1
	_check(testing == 0, "No 1990 player tests the free-agent market (%d)" % testing)
	GameState._close_free_agency()
	_check(GameState.start_next_season(), "1990 rolls into 1991")
	_check(GameState.season_year == 1991 and EraRules.year == 1991 and not EraRules.list_ahead,
			"The rules year follows the season")
	_check(Ratings.bench() == 2, "1991: still two on the bench")
	var rookies := 0
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			if str(p.get("rookie_list", "")) != "":
				rookies += 1
	_check(rookies == 0, "No rookie list in 1991 (%d listed as rookies)" % rookies)
	_lists_within("1991")


## 1993 to 1994: the list falls from 52 to 42 and a third interchange joins.
func _test_rollover_1993_to_1994() -> void:
	_career(1993)
	_check(Ratings.bench() == 2 and Contracts.max_list() == 52, "1993: two on the bench, 52 on the list")
	_check(_roll(), "1993 rolls into 1994")
	_check(Ratings.bench() == 3 and Contracts.max_list() == 42, "1994: three on the bench, 42 on the list")
	_lists_within("1994")
	print("L4DEBUG keys=%s my=%d year=%d club=%s" % [str(GameState.season.lists.keys()), GameState.my_list.size(), GameState.season_year, GameState.my_club])
	var sq := Squad.new("GEE", GameState.my_list, true, "GEE")
	_check(sq.bench.size() == 3, "A 1994 side names three on the bench (%d)" % sq.bench.size())


## 1996 to 1997: the first rookie lists, filled at the 1996 off-season's draft.
func _test_rollover_1996_to_1997() -> void:
	_career(1996)
	_check(not RookieList.in_force() and RookieList.cat_a_spots() == 0, "1996: no rookie list")
	_to_offseason()
	GameState.open_offseason()
	_check(RookieList.in_force() and RookieList.cat_a_spots() == 6,
			"The 1996 off-season plans 1997's six rookie spots")
	GameState._close_free_agency()
	_check(GameState.start_next_season(), "1996 rolls into 1997")
	_check(GameState.season_year == 1997 and RookieList.in_force(), "1997 has a rookie list")
	_lists_within("1997")


## 2011 to 2012: free agency begins in the 2012 off-season, not before.
func _test_rollover_2011_to_2012() -> void:
	_career(2011)
	_check(Ratings.bench() == 3 and Ratings.subs() == 1 and not EraRules.medical_sub(),
			"2011: three on the bench and a substitute")
	_check(not EraRules.on("free_agency"), "2011: no free agency")
	_check(_roll(), "2011 rolls into 2012")
	_check(EraRules.on("free_agency"), "2012: free agency")
	# Today's lists stand in, so their clubs' tenures postdate 2012: the gate
	# is checked on the players who test the market in a game year.
	_career(GameDB.START_YEAR)
	var testers := []
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			if GameState.tests_market(p, GameState.season.lists[code]):
				testers.append([p, code])
	_check(not testers.is_empty(), "Some %d players test the market (%d)" % [GameDB.START_YEAR, testers.size()])
	var walk := {2011: 0, 2012: 0}
	for y in walk:
		EraRules.year = y
		for t in testers:
			if GameState.tests_market(t[0], GameState.season.lists[t[1]]):
				walk[y] += 1
	EraRules.year = GameState.season_year
	_check(walk[2011] == 0 and walk[2012] == testers.size(),
			"The same players: none test the market under 2011's rules, all under 2012's (%s)" % str(walk))


## 2025 to 2026: the game's own rules take over.
func _test_rollover_2025_to_2026() -> void:
	_career(2025)
	_check(Ratings.bench() == 4 and EraRules.medical_sub(), "2025: four on the bench and a medical substitute")
	_check(_roll(), "2025 rolls into 2026")
	_check(Ratings.bench() == Ratings.INTERCHANGE and Ratings.subs() == 0
			and Contracts.max_list() == Contracts.MAX_LIST,
			"2026: the game's bench of %d, no substitute, lists of %d" % [Ratings.bench(), Contracts.max_list()])
	_lists_within("2026")


## 2011-2015: each side's substitute comes on once (for an injury, or at
## three-quarter time at the latest), and the man he replaces stays off.
func _test_tactical_sub_2011() -> void:
	var sim := _match(2011, 31)
	for side in range(2):
		var on := 0
		for e in _events(sim, "substitute"):
			if int(e.get("side", -1)) == side:
				on += 1
		_check(on == 1, "Side %d brings its substitute on once (%d)" % [side, on])
		var sq: Squad = sim.squads[side]
		var still_on := false
		for p in sim.subbed_off[side]:
			for q in sq.ground + sq.bench:
				if str(q["id"]) == str(p["id"]):
					still_on = true
		_check(not still_on, "Side %d: the man subbed off stays off" % side)
		_check((sim.rosters()[side] as Array).size() <= 23, "Side %d uses at most 22 players" % side)


## 2021-2025: the substitute comes on only for an injured player.
func _test_medical_sub_2021() -> void:
	var seen_injury := false
	for seed in range(1, 40):
		var sim := _match(2021, seed)
		var subs := _events(sim, "substitute")
		var hurt := _events(sim, "injury")
		_check(subs.size() <= hurt.size(), "Seed %d: a 2021 substitute only for an injury (%d subs, %d injuries)"
				% [seed, subs.size(), hurt.size()])
		_check((sim.subbed_off[0] as Array).is_empty() and (sim.subbed_off[1] as Array).is_empty(),
				"Seed %d: nobody is subbed off fit in 2021" % seed)
		if not hurt.is_empty():
			seen_injury = true
			_check(not subs.is_empty(), "Seed %d: the injury brings the substitute on" % seed)
			break
	_check(seen_injury, "Some 2021 match in 40 seeds has an injury")


## 2016-2020: no substitute at all.
func _test_no_sub_2016() -> void:
	var sim := _match(2016, 31)
	_check(_events(sim, "substitute").is_empty() and (sim.squads[0] as Squad).sub.is_empty(),
			"No substitute in 2016")
	_check((sim.squads[0] as Squad).bench.size() == 4, "Four on a 2016 bench")
