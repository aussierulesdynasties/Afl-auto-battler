extends RefCounted
## The 2020 Legacy start (TODO row 142): the 18 clubs on their real 2020 lists,
## rated on 2019, with 2020's senior coaches (rated from their records) and
## captains. 2020 is the hub season of shortened games; the career then rolls
## on with no end year (director 2026-11-13: "campaigns can go for eternity").
## Run through tests/run_legacy_start_2020_tests.gd.

const Ran := preload("res://tests/functions_ran.gd")

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2020
const CLUB := "RIC"


func run() -> void:
	_t("_test_the_2020_set")
	_t("_test_a_2020_career_starts_at_richmond")
	_t("_test_the_hub_season_clock")
	_t("_test_the_career_rolls_past_2027")
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
		if str(p.get("name", "")).ends_with("Fyfe") and int(p.get("ovr", 0)) >= 85:
			fyfe = true
	_check(fyfe, "Nat Fyfe, the 2019 Brownlow medallist, is at Fremantle and rated as one")


## A 2020 career at Richmond: your club's real senior coach makes way and
## every other club has its real 2020 coach and captain.
func _test_a_2020_career_starts_at_richmond() -> void:
	_start_2020(CLUB)
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
	_check(int(clarkson.get("tactics", 0)) >= 85, "Clarkson's tactics are rated from his record (%d)" % int(clarkson.get("tactics", 0)))
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
	GameState.reset()


## 2020's games were 16-minute quarters plus time on: the clock says so.
func _test_the_hub_season_clock() -> void:
	_check(EraFootball.clock_minutes(30, 2020) == 24, "A 2020 quarter's clock runs to 24, four-fifths of 30")
	_check(EraFootball.clock_minutes(30, 2019) == 30 and EraFootball.clock_minutes(30, 2021) == 30,
			"2019 and 2021 play full quarters")


## The 2020 season plays out, the career rolls into 2021 on the same set, and
## keeps rolling past 2027: no end year.
func _test_the_career_rolls_past_2027() -> void:
	_start_2020(CLUB)
	var started := Time.get_ticks_msec()
	var years := []
	while GameState.season_year <= 2027:
		var year := GameState.season_year
		var res := GameState.skip_season()
		if not GameState.season.is_season_over():
			failures.append("The %d season plays out (%s)" % [year, str(res)])
			break
		years.append(year)
		if year == 2020:
			var mine: int = GameState.season.club_results(CLUB).size()
			_check(mine >= 17, "Richmond play their 2020 season (%d games)" % mine)
		if not GameState.start_next_season():
			failures.append("The career rolls on from %d" % year)
			break
		checks += 1
		if GameState.season_year == 2021:
			_check(GameState.my_club == CLUB and GameDB.dataset_id == "2020" and GameState.dataset == "2020",
					"It is 2021 at Richmond, still the career begun in 2020")
	_check(GameState.season_year == 2028 and years.size() == 8,
			"The career rolls from 2020 to 2028 with no end year (%d, seasons %s)" % [GameState.season_year, str(years)])
	print("Legacy start 2020: eight seasons in %.0f s" % ((Time.get_ticks_msec() - started) / 1000.0))
	GameState.reset()


## A 2020 career at `club`, as Choose your club starts it.
func _start_2020(club: String) -> void:
	GameState.reset("2020")
	GameState.replay_seed = SUITE_SEED
	GameState.career_seed = SUITE_SEED
	GameState.begin_real_lists()
	GameState.choose_real_club(club)
	var guard := 0
	while GameState.draft != null and not GameState.draft.is_finished() and guard < 400:
		guard += 1
		if GameState.draft.is_user_turn():
			var board: Array = GameState.draft.board("", "", "", "overall", true)
			if board.is_empty() or not GameState.draft.pick(board[0]):
				break
	GameState.finish_intake_draft()
