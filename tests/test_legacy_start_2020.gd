extends RefCounted
## The 2020 Legacy start (TODO row 142): the 18 clubs on their real 2020 lists,
## rated on 2019, with 2020's senior coaches (rated from their records) and
## captains. 2020 is the hub season of shortened games; the career then rolls
## on with no end year (director 2026-11-13: "campaigns can go for eternity").
## Run through tests/run_legacy_start_2020_tests.gd; the career past 2027 is the
## nightly legacy_2020_long suite.

const Ran := preload("res://tests/functions_ran.gd")
const Career := preload("res://tests/legacy_2020_career.gd")

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := Career.SEED
const CLUB := "RIC"


func run() -> void:
	_t("_test_the_2020_set")
	_t("_test_a_2020_career_starts_at_richmond")
	_t("_test_the_hub_season_clock")
	_t("_test_the_career_rolls_into_2021")
	GameState.reset()
	for f in failures:
		print("FAIL: ", f)
	print(Ran.line("Legacy start 2020", self))


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures.append(what)


## The year step offers 2020, and its files load.
func _test_the_2020_set() -> void:
	_check(Datasets.ready("2020") and Datasets.ready_ids().has("2020"), "The year step offers 2020")
	var row := Datasets.get_set("2020")
	_check(int(row.get("data_season", 0)) == 2019 and int(row.get("start_year", 0)) == 2020,
			"2020's lists are rated on 2019 and the career starts in 2020")
	for key in Datasets.FILE_KEYS:
		var path := Datasets.file("2020", key)
		_check(path == "" or FileAccess.file_exists(path), "2020's %s file ships (%s)" % [key, path])
	GameState.reset("2020")
	_check(GameDB.dataset_id == "2020", "A 2020 career loads the 2020 set")
	var clubs := {}
	for p in GameDB.all_players_sorted():
		clubs[str(p.get("club", ""))] = true
	clubs.erase("")
	_check(clubs.size() == 18, "18 clubs have 2020 lists (%d)" % clubs.size())
	var fyfe := false
	for p in GameDB.club_list("FRE"):
		if str(p.get("last", "")) == "Fyfe" and int(p.get("overall", 0)) >= 85:
			fyfe = true
	_check(fyfe, "Nat Fyfe, the 2019 Brownlow medallist, is at Fremantle and rated as one")


## A 2020 career at Richmond: your club's real senior coach makes way and
## every other club has its real 2020 coach and captain.
func _test_a_2020_career_starts_at_richmond() -> void:
	Career.start(CLUB)
	_check(GameState.season_year == 2020 and GameState.my_club == CLUB, "The career starts in 2020 at Richmond")
	var by_name := {}
	for cid in GameState.coaches:
		by_name[str(GameState.coaches[cid].get("real_name", ""))] = GameState.coaches[cid]
	var hardwick: Dictionary = by_name.get("Damien Hardwick", {})
	_check(str(hardwick.get("status", "")) == "free", "Damien Hardwick makes way at Richmond (%s)" % str(hardwick.get("status", "missing")))
	_check(Coaches.staff(GameState.coaches, CLUB).get("SC", "") == "", "Richmond's senior job is yours")
	var real_sc := {"GEE": "Chris Scott", "HAW": "Alastair Clarkson", "SYD": "John Longmire", "BRL": "Chris Fagan"}
	for club in real_sc:
		var sc := str(Coaches.staff(GameState.coaches, club).get("SC", ""))
		var sc_name := str(GameState.coaches.get(sc, {}).get("real_name", ""))
		_check(sc_name == real_sc[club], "%s's senior coach is %s (%s)" % [club, real_sc[club], sc_name])
	var clarkson: Dictionary = by_name.get("Alastair Clarkson", {})
	var tactics := int((clarkson.get("skills", {}) as Dictionary).get("tactics", 0))
	_check(tactics >= 85, "Clarkson's tactics are rated from his record (%d)" % tactics)
	var no_sc := []
	var no_captain := []
	for club in GameState.season.clubs:
		if club != CLUB and str(Coaches.staff(GameState.coaches, club).get("SC", "")) == "":
			no_sc.append(club)
		var has_captain := false
		for p in (GameState.season.lists[club] as Array):
			if Leadership.role_line(p, GameState.season_year).begins_with("Captain") \
					or Leadership.role_line(p, GameState.season_year).begins_with("Co-captain"):
				has_captain = true
		if not has_captain:
			no_captain.append(club)
	_check(no_sc.is_empty(), "Every other club has its senior coach (%s)" % str(no_sc))
	_check(no_captain.is_empty(), "Every club shows its 2020 captain (%s)" % str(no_captain))
	# The career is left as it started: _test_the_career_rolls_into_2021 plays it.


## 2020's games were 16-minute quarters plus time on: the clock says so.
func _test_the_hub_season_clock() -> void:
	_check(EraFootball.clock_minutes(30, 2020) == 24, "A 2020 quarter's clock runs to 24, four-fifths of 30")
	_check(EraFootball.clock_minutes(30, 2019) == 30 and EraFootball.clock_minutes(30, 2021) == 30,
			"2019 and 2021 play full quarters")


## The 2020 season plays out and the career rolls into 2021 on the same set.
## The nightly legacy_2020_long suite carries it on past 2027.
## Its first round is played; the rest of the home and away season is skipped
## (the rollover is under test, not the matches) and the finals are simmed.
func _test_the_career_rolls_into_2021() -> void:
	# The career _test_a_2020_career_starts_at_richmond started, untouched since.
	if GameState.season_year != 2020 or GameState.my_club != CLUB or GameDB.dataset_id != "2020":
		Career.start(CLUB)
	var season: Season = GameState.season
	var fixtured := 0
	for rnd in season.fixture:
		for m in rnd:
			if str(m["home"]) == CLUB or str(m["away"]) == CLUB:
				fixtured += 1
	_check(fixtured >= 17, "Richmond have their 2020 season to play (%d games)" % fixtured)
	GameState.advance()
	var mine: int = season.club_results(CLUB).size()
	_check(season.round_index == 1 and mine == 1, "Richmond play their first 2020 game (%d)" % mine)
	season.round_index = season.fixture.size()
	GameState.ensure_finals()
	GameState.skip_season()
	_check(GameState.season.is_season_over(), "The 2020 season plays out")
	_check(Career.roll_on(), "The career rolls on from 2020 (%s)" % Career.state())
	_check(GameState.season_year == 2021 and GameState.my_club == CLUB and GameDB.dataset_id == "2020"
			and GameState.dataset == "2020",
			"It is 2021 at Richmond, still the career begun in 2020 (%d, %s)" % [GameState.season_year, GameState.my_club])
	GameState.reset()
