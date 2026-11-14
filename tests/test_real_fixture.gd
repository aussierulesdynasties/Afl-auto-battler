extends RefCounted
## Real fixtures (Legacy mode phase L6, TODO row 142): the loader reads
## data/legacy/fixtures.csv, a season whose clubs are the year's real clubs
## plays its real rounds at their real grounds, a season whose clubs differ
## (Fitzroy surviving, a club missing) draws its own, every 2026 career plays
## the real 2026 (25 rounds, the Opening Round; director 2026-11-13: "Real for
## 2026 too"), and the game's league after 2026 is the same seeded fixture as
## before (golden digest).
## Run through tests/run_real_fixture_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2027
const Golden := preload("res://tests/season_golden.gd")
## tests/test_season_rules.gd's fixture digest of the game's league (seeds 1,
## 2, 3, 2027, 90210), recorded before season rules and real fixtures.
const GOLDEN_FIXTURE := {
	1: "88379d64dfcfdf22f88fcc1bbcc1bab4",
	2: "15aab1f43b8c605b37bc9eef32c73406",
	3: "928bc55d620e04e745cf7adb88b56ae8",
	2027: "57bffb38d600d4036767ef691d623a80",
	90210: "1734a8fcc9068e3e444e293a25f944b4",
}
## [year, clubs, rounds, games] as data/legacy/fixtures.csv holds them.
const SHAPES := [[1990, 14, 22, 154], [1991, 15, 24, 165], [1993, 15, 22, 150], [1996, 16, 22, 176],
		[1997, 16, 22, 176], [2011, 17, 24, 187], [2015, 18, 23, 198], [2020, 18, 18, 153],
		[2024, 18, 25, 207], [2025, 18, 25, 207], [2026, 18, 25, 207]]


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	_t("_test_loader_years")
	_t("_test_first_match_1990")
	_t("_test_real_season_plays_real_rounds")
	_t("_test_real_venue")
	_t("_test_real_gather_round")
	_t("_test_differing_clubs_draw")
	_t("_test_real_2026")
	_t("_test_opening_round_names")
	_t("_test_after_2026_unchanged")
	_t("_test_real_season_played_and_saved")
	_t("_test_career_rolls_into_real_years")
	_t("_test_career_with_other_clubs_draws")
	GameState.replay_seed = 0
	print(Ran.line("Real fixture", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _season(year: int, codes: Array, sd := 11) -> Season:
	return Season.new(codes, Golden.lists(codes), sd, year)


func _games(rounds: Array) -> int:
	var n := 0
	for r in rounds:
		n += (r as Array).size()
	return n


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
## Every real season 1990-2026 is in the table with its clubs, rounds and games.
func _test_loader_years() -> void:
	var missing := []
	for y in range(1990, 2027):
		if not RealFixture.has_year(y):
			missing.append(y)
	_check(missing.is_empty(), "Every season 1990-2026 has a real fixture (missing %s)" % [missing])
	_check(not RealFixture.has_year(1989) and not RealFixture.has_year(2027), "No real fixture before 1990 or after 2026")
	_check(SHAPES.size() == 11, "Every shape case is listed")
	for c in SHAPES:
		var y := int(c[0])
		var clubs := RealFixture.clubs_for(y)
		var rounds := RealFixture.for_season(y, clubs)
		_check(clubs.size() == int(c[1]) and rounds.size() == int(c[2]) and _games(rounds) == int(c[3]),
				"%d: %d clubs, %d rounds, %d games (%d, %d, %d)" % [y, c[1], c[2], c[3], clubs.size(), rounds.size(), _games(rounds)])
	_check(RealFixture.clubs_for(1996).has("FIT") and not RealFixture.clubs_for(1997).has("FIT"),
			"Fitzroy plays in 1996, not 1997")
	_check(RealFixture.clubs_for(1990).has("BRL") and RealFixture.clubs_for(1990).has("WBD"),
			"The Bears and Footscray carry their clubs' one code (BRL, WBD)")


## The first match of 1990 as AFL Tables records it.
func _test_first_match_1990() -> void:
	var rounds := RealFixture.for_season(1990, RealFixture.clubs_for(1990))
	_check(rounds.size() == 22, "1990: 22 rounds")
	var m: Dictionary = rounds[0][0]
	_check(str(m["home"]) == "CAR" and str(m["away"]) == "SYD" and str(m["ground"]) == "Ikon Park"
			and str(m["date"]) == "1990-03-31", "1990 round 1: Carlton v Sydney at Princes Park, 31 March (%s)" % [m])


## A season of a real year's clubs is that year's fixture, match for match,
## whatever the season's seed.
func _test_real_season_plays_real_rounds() -> void:
	for y in [1990, 1996, 2015, 2024]:
		var clubs := RealFixture.clubs_for(y)
		var want := RealFixture.for_season(y, clubs)
		for sd in [3, 19]:
			var s := _season(y, clubs, sd)
			_check(s.is_real_fixture(), "%d seed %d: the real fixture" % [y, sd])
			var same: bool = s.fixture.size() == want.size()
			if same:
				for ri in range(want.size()):
					var a := (s.fixture[ri] as Array).map(func(m): return [m["home"], m["away"], m["ground"]])
					var b := (want[ri] as Array).map(func(m): return [m["home"], m["away"], m["ground"]])
					if a != b:
						same = false
			_check(same, "%d seed %d: every round as it was played" % [y, sd])
	# The club order a caller passes does not matter.
	var rev := RealFixture.clubs_for(2015)
	rev.reverse()
	_check(_season(2015, rev).is_real_fixture(), "2015 in any club order: the real fixture")


## A real match is at the ground it was played at, not the home club's.
func _test_real_venue() -> void:
	var s := _season(1990, RealFixture.clubs_for(1990))
	_check(s.round_venue(0, "CAR", "SYD") == "Ikon Park", "1990 round 1: Carlton v Sydney at Princes Park (%s)" % s.round_venue(0, "CAR", "SYD"))
	# 2015 round 14: Adelaide v Geelong, fixtured and never played, is in the season.
	var t := _season(2015, RealFixture.clubs_for(2015))
	_check(t.round_venue(13, "ADE", "GEE") == "Adelaide Oval", "2015 round 14: Adelaide v Geelong at Adelaide Oval")
	var away := 0
	for ri in range(t.fixture.size()):
		for m in t.fixture[ri]:
			if t.round_venue(ri, str(m["home"]), str(m["away"])) != str(m["ground"]):
				away += 1
	_check(away == 0, "2015: every match's venue is its real ground (%d differ)" % away)
	# York Park: a real ground no club calls home.
	var tas := 0
	var h := _season(2010, RealFixture.clubs_for(2010))
	for ri in range(h.fixture.size()):
		for m in h.fixture[ri]:
			if h.round_venue(ri, str(m["home"]), str(m["away"])) == "York Park":
				tas += 1
	_check(tas > 0, "2010: Hawthorn's Tasmanian games at York Park (%d)" % tas)


## A real season's Gather Round is the round really played in Adelaide; none before 2023.
func _test_real_gather_round() -> void:
	var cases := {2015: -1, 2022: -1, 2023: 4, 2024: 4, 2025: 5}
	for y in cases:
		var s := _season(int(y), RealFixture.clubs_for(int(y)))
		_check(s.gather_round() == int(cases[y]), "%d: Gather Round %d (%d)" % [y, int(cases[y]), s.gather_round()])
	var g := _season(2024, RealFixture.clubs_for(2024))
	var gr := g.gather_round()
	var edge := 0
	for m in g.fixture[gr]:
		var at: Array = g.round_at_home(gr, str(m["home"]), str(m["away"]))
		if bool(at[0]) or bool(at[1]):
			edge += 1
		var v := g.round_venue(gr, str(m["home"]), str(m["away"]))
		_check(v in ["Adelaide Oval", "Norwood Oval", "Barossa Park"], "2024 Gather Round: %s v %s in Adelaide (%s)" % [m["home"], m["away"], v])
	_check(edge > 0 and edge < (g.fixture[gr] as Array).size(), "2024 Gather Round: only the Adelaide clubs have a home edge (%d matches)" % edge)


## Clubs that differ from history draw their own fixture: Fitzroy surviving
## into 1997, a club missing, a year with no table.
func _test_differing_clubs_draw() -> void:
	var with_fitzroy := RealFixture.clubs_for(1997)
	with_fitzroy.append("FIT")
	var a := _season(1997, with_fitzroy, 5)
	_check(not a.is_real_fixture() and a.fixture.size() == a.regular_rounds(),
			"1997 with Fitzroy: a drawn fixture of %d rounds (%d)" % [a.regular_rounds(), a.fixture.size()])
	var b := _season(1997, with_fitzroy, 5)
	_check(Golden.fixture_text(a) == Golden.fixture_text(b), "1997 with Fitzroy: the same seed draws the same fixture")
	var short := RealFixture.clubs_for(2015)
	short.erase("GEE")
	_check(not _season(2015, short).is_real_fixture(), "2015 without Geelong: a drawn fixture")
	_check(not _season(0, RealFixture.clubs_for(2015)).is_real_fixture(), "A season with no year: a drawn fixture")


## Every 2026 career plays the real 2026: 25 rounds, the Opening Round first
## (director, 2026-11-13: "Real for 2026 too"). A 2026 season with a club that
## did not play it (a created club) is drawn in the game's own shape: the same
## seeded fixture as before.
func _test_real_2026() -> void:
	var clubs := RealFixture.clubs_for(2026)
	_check(clubs.size() == 18, "2026: the 18 clubs (%d)" % clubs.size())
	var s := _season(2026, clubs)
	_check(s.is_real_fixture() and s.regular_rounds() == 25 and s.fixture.size() == 25,
			"2026: the real fixture, 25 rounds (%d, %d)" % [s.regular_rounds(), s.fixture.size()])
	var opening := (s.fixture[0] as Array).size()
	_check(opening > 0 and opening < 9, "2026: the Opening Round is a short round (%d matches)" % opening)
	var created := clubs.duplicate()
	created[17] = "TAS"
	var c := Season.new(created, Golden.lists(created), 11, 2026)
	_check(not c.is_real_fixture() and c.regular_rounds() == Season.REGULAR_ROUNDS and c.fixture.size() == Season.REGULAR_ROUNDS,
			"2026 with a created club: drawn, %d rounds (%d)" % [Season.REGULAR_ROUNDS, c.fixture.size()])
	var codes: Array = GameDB.active_clubs(2027).duplicate()
	codes[17] = "TAS"
	var l := Golden.lists(codes)
	for sd in GOLDEN_FIXTURE:
		var d := Season.new(codes.duplicate(), l, int(sd), 2026)
		var e := Season.new(codes.duplicate(), l, int(sd), 2027)
		_check(Golden.fixture_text(d) == Golden.fixture_text(e), "2026 with a created club, seed %d: the game's own draw" % sd)


## A season with the AFL's Opening Round (a real 2024 on) names its rounds as
## the AFL does: "Opening Round", then Round 1 to Round 24; a label reads back
## to the round it names. Every other season counts from Round 1.
func _test_opening_round_names() -> void:
	var s := _season(2026, RealFixture.clubs_for(2026))
	_check(s.has_opening_round(), "2026: an Opening Round")
	_check(s.round_name(0) == "Opening Round" and s.round_name(1) == "Round 1" and s.round_name(24) == "Round 24",
			"2026: Opening Round, Round 1 ... Round 24 (%s, %s, %s)" % [s.round_name(0), s.round_name(1), s.round_name(24)])
	_check(s.round_progress(0) == "Opening Round" and s.round_progress(3) == "Round 3 of 24",
			"2026: Opening Round, then Round 3 of 24 (%s)" % s.round_progress(3))
	_check(s.round_of_label("Opening Round") == 1 and s.round_of_label("Round 1") == 2
			and s.round_of_label("Round 24") == 25 and s.round_of_label("Grand Final") == 0,
			"2026: a label reads back to the round it names")
	# The real Gather Rounds were Round 4 (2024) and Round 5 (2025).
	for c in [[2024, "Round 4 · Gather Round"], [2025, "Round 5 · Gather Round"]]:
		var g := _season(int(c[0]), RealFixture.clubs_for(int(c[0])))
		var got := g.round_label(g.gather_round())
		_check(got == str(c[1]), "%d: the Gather Round is %s (%s)" % [c[0], c[1], got])
	for y in [2023, 1990]:
		var o := _season(y, RealFixture.clubs_for(y))
		_check(not o.has_opening_round() and o.round_name(0) == "Round 1" and o.round_of_label("Round 1") == 1,
				"%d: no Opening Round, Round 1 first" % y)
	var created := RealFixture.clubs_for(2026)
	created[17] = "TAS"
	var c26 := Season.new(created, Golden.lists(created), 11, 2026)
	_check(not c26.has_opening_round() and c26.round_progress(0) == "Round 1 of 24",
			"2026 with a created club: Round 1 of 24 (%s)" % c26.round_progress(0))


## The game's league after 2026 is the same seeded fixture as before real
## fixtures existed.
func _test_after_2026_unchanged() -> void:
	_check(GOLDEN_FIXTURE.size() == Golden.FIXTURE_SEEDS.size(), "The golden digest covers every seed")
	var codes: Array = GameDB.active_clubs(2027).duplicate()
	var l := Golden.lists(codes)
	for y in [2027]:
		for sd in GOLDEN_FIXTURE:
			var s := Season.new(codes.duplicate(), l, int(sd), y)
			_check(not s.is_real_fixture(), "%d seed %d: drawn" % [y, sd])
			var got := Golden.fixture_text(s).md5_text()
			_check(got == str(GOLDEN_FIXTURE[sd]), "%d seed %d: the fixture is unchanged (%s)" % [y, sd, got])


## A real season plays through on its real fixture and a save keeps it.
func _test_real_season_played_and_saved() -> void:
	var s := _season(2015, RealFixture.clubs_for(2015), 9)
	var first := s.play_round()
	_check(first.size() == 9 and str(first[0]["home"]) == "CAR" and str(first[0]["away"]) == "RIC"
			and s.round_venue(0, "CAR", "RIC") == "MCG", "2015 round 1: nine games, Carlton v Richmond first, at the MCG")
	var sv := CareerSave.object_vars(s)
	sv.erase("rules")
	sv = JSON.parse_string(JSON.stringify(sv))
	var back := Season.new(sv["clubs"], s.lists, int(sv["seed"]), int(sv.get("year", 0)))
	CareerSave.apply_vars(back, sv)
	_check(back.is_real_fixture() and back.round_index == 1 and back.round_venue(0, "CAR", "RIC") == "MCG",
			"A saved 2015 season reloads on its real fixture")
	# The rest of the season goes through play_round too, with stand-in
	# results handed over as if the week's matches had run early (start_week):
	# the fixture and the ladder are under test here, not the match sim.
	while not s.is_regular_done():
		var out := []
		for m in s.fixture[s.round_index]:
			out.append({"res": {"home": m["home"], "away": m["away"], "score": [60, 50]}})
		s._early = {"week": "r%d" % s.round_index, "threads": [], "out": out}
		s.play_round()
	var p := 0
	var short := []
	for row in s.ladder_sorted():
		p += int(row["p"])
		if int(row["p"]) != 22:
			short.append("%s %d" % [row["code"], int(row["p"])])
	_check(p == 18 * 22 and short.is_empty() and s.results.size() == 23,
			"2015: all 198 real games on the ladder, 22 a club (%d club-games, %s)" % [p, str(short)])


## The first round's pairs, "HOME-AWAY", in order.
func _pairs(rounds: Array) -> Array:
	var out := []
	if rounds.is_empty():
		return out
	for m in rounds[0]:
		out.append("%s-%s" % [m["home"], m["away"]])
	return out


## Take a career's season to its end without playing it, then roll it on: the
## rollover is the career's own (GameState.start_next_season).
func _roll(year: int) -> bool:
	GameState.season.round_index = GameState.season.fixture.size()
	var ok: bool = GameState.start_next_season()
	_check(ok and GameState.season_year == year + 1 and int(GameState.season.year) == year + 1,
			"The career rolls from %d to %d" % [year, year + 1])
	return ok


## A 1990 start is the first season of a campaign (director 2026-11-13): each
## rollover picks up the next year's real fixture as clubs join and leave. One
## real rollover (1990 to 1991, Adelaide join) proves the career's own path;
## the rollover builds next year's season from GameDB.active_clubs(next year)
## (GameState._start_next_season), so the years after it are that same season
## built directly, without six more off-seasons.
func _test_career_rolls_into_real_years() -> void:
	GameState.reset("1990")
	GameState.replay_seed = SUITE_SEED
	GameState.tutorials = false
	GameState.start_season("CAR", GameDB.club_list("CAR"))
	var counts := {1990: 14, 1991: 15, 1994: 15, 1995: 16, 1996: 16, 1997: 16}
	for y in range(1990, 1998):
		if y == 1991 and not _roll(1990):
			break
		var s: Season = GameState.season if y <= 1991 else Season.new(
				GameDB.active_clubs(y).duplicate(), GameState.season.lists, SUITE_SEED + y, y)
		var clubs: Array = s.clubs.duplicate()
		var real := RealFixture.for_season(y, clubs)
		_check(int(s.year) == y and not real.is_empty() and s.is_real_fixture()
				and s.fixture.size() == real.size() and _pairs(s.fixture) == _pairs(real),
				"%d: the career plays the real %d fixture (%d rounds)" % [y, y, s.fixture.size()])
		if counts.has(y):
			_check(clubs.size() == counts[y], "%d: %d clubs (%d)" % [y, counts[y], clubs.size()])
		if y == 1990:
			_check(not clubs.has("ADE") and clubs.has("FIT"), "1990: Fitzroy play, Adelaide not yet")
		if y == 1991:
			_check(clubs.has("ADE"), "1991: Adelaide join the league")
		if y == 1995:
			_check(clubs.has("FRE"), "1995: Fremantle join the league")
		if y == 1997:
			_check(not clubs.has("FIT") and clubs.has("PAD"), "1997: Fitzroy are gone after 1996; Port Adelaide join")
	GameState.reset()


## A career whose clubs part from history (it left Adelaide out) draws its own
## season the year they part, and every club plays its games. The rollover
## builds next year's season from GameDB.active_clubs(next year)
## (GameState._start_next_season), and _test_career_rolls_into_real_years
## proves that path with a real off-season; here that same season is built
## directly, with the career's own club years, without a second off-season.
func _test_career_with_other_clubs_draws() -> void:
	GameState.reset("1990")
	GameState.replay_seed = SUITE_SEED
	GameState.tutorials = false
	GameDB.set_enter_year("ADE", 9999)
	GameState.start_season("CAR", GameDB.club_list("CAR"))
	_check(GameState.season.is_real_fixture(), "1990 is still the real 1990 (Adelaide had not joined)")
	var s := Season.new(GameDB.active_clubs(1991).duplicate(), GameState.season.lists, SUITE_SEED + 1991, 1991)
	_check(s.clubs.size() == 14 and not s.clubs.has("ADE") and not s.is_real_fixture()
			and RealFixture.for_season(1991, s.clubs).is_empty(),
			"1991 without Adelaide: the clubs differ from history, so the season is drawn")
	var games := {}
	for r in s.fixture:
		for m in r:
			for c in [m["home"], m["away"]]:
				games[c] = int(games.get(c, 0)) + 1
	var even := games.size() == 14
	for c in games:
		even = even and abs(int(games[c]) - int(games[s.clubs[0]])) <= 0
	_check(even and s.fixture.size() > 0,
			"The drawn 1991 gives all 14 clubs the same number of games (%s)" % str(games.values()))
	GameState.reset()
