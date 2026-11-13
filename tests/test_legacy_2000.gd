extends RefCounted
## The 2000 start (Legacy mode, TODO row 142: "then the 2000, 2010 and 2020
## starts"): the 16 clubs' real 2000 lists rated on 1999, the 2000 senior
## coaches rated from their records, the 2000 captains, and a seeded career at
## a real 2000 club that plays the season and rolls into 2001.
## Run through tests/run_legacy_2000_tests.gd.

var failures: Array[String] = []
var checks := 0

const SEED := 2000
const CLUBS_2000 := ["ADE", "BRL", "CAR", "COL", "ESS", "FRE", "GEE", "HAW", "MEL", "NTH", "PAD", "RIC",
		"STK", "SYD", "WBD", "WCE"]


func run() -> void:
	failures.clear()
	checks = 0
	_t("_test_set_loads")
	_t("_test_coaches_and_captains")
	_t("_test_career_rolls_into_2001")
	GameState.reset()
	GameState.delete_saved_career()
	GameDB.reload()
	print(Ran.line("Legacy 2000", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## The person on `club`'s list (players or additions) called `first last`.
func _find(club: String, first: String, last: String) -> Dictionary:
	for p in GameDB.club_list(club) + GameDB.club_additions(club):
		if str(p.get("first", "")) == first and str(p.get("last", "")) == last:
			return p
	return {}


func _test_set_loads() -> void:
	_check(Datasets.ready("2000"), "The 2000 start's files ship")
	_check(Datasets.ready_ids().has("2000") and Datasets.ready_ids().size() > 1,
			"The year step offers 2000 (%s)" % str(Datasets.ready_ids()))
	GameDB.reload("2000")
	_check(GameDB.dataset_id == "2000" and GameDB.DATA_SEASON == 1999 and GameDB.START_YEAR == 2000,
			"The 2000 set loads: data season 1999, first season 2000 (%d, %d)" % [GameDB.DATA_SEASON, GameDB.START_YEAR])
	var clubs: Array = GameDB.active_clubs(2000).duplicate()
	clubs.sort()
	_check(clubs == CLUBS_2000, "2000 has its 16 clubs (%s)" % str(clubs))
	var short := []
	for c in CLUBS_2000:
		var n: int = GameDB.club_list(c).size() + GameDB.club_additions(c).size()
		if n < 40:
			short.append("%s %d" % [c, n])
	_check(short.is_empty(), "Every club has its real 2000 list of 40 or more (%s)" % str(short))
	var buckley := _find("COL", "Nathan", "Buckley")
	var pavlich := _find("FRE", "Matthew", "Pavlich")
	_check(not buckley.is_empty() and int(buckley.get("overall", 0)) >= 85,
			"Nathan Buckley is at Collingwood, rated on his 1999 (%d)" % int(buckley.get("overall", 0)))
	_check(not pavlich.is_empty(), "Matthew Pavlich, the 1999 draftee, is on Fremantle's list")


func _test_coaches_and_captains() -> void:
	GameState.reset("2000")
	var seeded := Coaches.seed("MEL")
	var by := {}
	for cid in seeded:
		by[str(seeded[cid].get("real_name", ""))] = seeded[cid]
	var tactics := func(n: String) -> int: return int(((by.get(n, {}) as Dictionary).get("skills", {}) as Dictionary).get("tactics", -1))
	_check(str((by.get("Kevin Sheedy", {}) as Dictionary).get("club", "")) == "ESS"
			and str((by.get("Mick Malthouse", {}) as Dictionary).get("club", "")) == "COL",
			"Sheedy coaches Essendon and Malthouse Collingwood in 2000")
	_check(tactics.call("Kevin Sheedy") > tactics.call("Peter Schwab") and tactics.call("Peter Schwab") > 0,
			"A record rates a coach: Sheedy (%d) above Schwab, in his first season (%d)" % [
				tactics.call("Kevin Sheedy"), tactics.call("Peter Schwab")])
	_check(str((by.get("Neale Daniher", {}) as Dictionary).get("status", "")) == "free",
			"Your club's 2000 coach, Neale Daniher, makes way")
	GameDB.reload("2000")
	var hird := _find("ESS", "James", "Hird")
	var voss := _find("BRL", "Michael", "Voss")
	_check(Leadership.role_line(hird, 2000) == "Captain" and Leadership.role_line(voss, 2000) == "Captain",
			"James Hird and Michael Voss captain their clubs in 2000 ('%s', '%s')" % [
				Leadership.role_line(hird, 2000), Leadership.role_line(voss, 2000)])
	GameState.reset()


## The seeded career: a real 2000 club, Choose your club as the menu starts
## it, the 2000 season played out, and the roll into 2001 on the same set.
func _test_career_rolls_into_2001() -> void:
	GameState.reset("2000")
	GameState.replay_seed = SEED
	GameState.career_seed = SEED
	GameState.begin_real_lists()
	GameState.choose_real_club("ESS")
	var guard := 0
	while GameState.draft != null and not GameState.draft.is_finished() and guard < 400:
		guard += 1
		if GameState.draft.is_user_turn():
			var board: Array = GameState.draft.board("", "", "", "overall", true)
			if board.is_empty() or not GameState.draft.pick(board[0]):
				break
	GameState.finish_intake_draft()
	_check(GameState.season_year == 2000 and GameState.my_club == "ESS" and GameState.season.clubs.size() == 16,
			"The career starts in 2000 at Essendon among 16 clubs (%d, %s, %d)" % [
				GameState.season_year, GameState.my_club, GameState.season.clubs.size()])
	var names := {}
	for p in (GameState.season.lists["ESS"] as Array):
		names["%s %s" % [str(p.get("first", "")), str(p.get("last", ""))]] = true
	_check(names.has("James Hird") and names.has("Matthew Lloyd"), "Essendon play on their real 2000 list")
	guard = 0
	while not GameState.season.is_season_over() and guard < 60:
		guard += 1
		GameState.advance()
	_check(GameState.season.is_season_over(), "The 2000 season plays out (%d weeks)" % guard)
	_check(GameState.start_next_season(), "The 2000 career rolls on")
	_check(GameState.season_year == 2001 and GameState.my_club == "ESS" and GameDB.dataset_id == "2000"
			and GameState.dataset == "2000",
			"It is 2001 at Essendon, still the career begun in 2000 (%d, %s, set %s)" % [
				GameState.season_year, GameState.my_club, GameDB.dataset_id])
	var no_sc := []
	for club in GameState.season.clubs:
		if club != "ESS" and str(Coaches.staff(GameState.coaches, club).get("SC", "")) == "":
			no_sc.append(club)
	_check(no_sc.is_empty(), "Every other club has a senior coach in 2001 (%s)" % str(no_sc))
	var shown := 0
	for club in GameState.season.clubs:
		for p in (GameState.season.lists[club] as Array):
			if Leadership.role_line(p, GameState.season_year) != "":
				shown += 1
	_check(shown == 0, "The 2000 captains' record is not shown as current in 2001 (%d)" % shown)
	GameState.reset()
