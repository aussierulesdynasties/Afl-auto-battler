extends RefCounted
## A 2010 career never ends (director 2026-11-13: "campaigns can go for
## eternity"). A seeded career begun at St Kilda in 2010 rolls season after
## season past 2027: Gold Coast enter in 2011, GWS in 2012 and Tasmania in 2028
## as the sim's own expansion, every club keeps a full list, and the career is still the one
## begun in 2010. About 18 seasons (some 7 minutes), so it runs nightly
## (tools/ci_long_suites.txt). Run through tests/run_legacy_2010_long_tests.gd.

const Ran := preload("res://tests/functions_ran.gd")

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2010
const CLUB := "STK"
const PAST := 2028


func run() -> void:
	failures.clear()
	checks = 0
	_t("_test_rolls_past_2027")
	GameState.reset()
	print(Ran.line("Legacy 2010 long", self))


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures.append(what)
		push_error(what)


func _start() -> void:
	GameState.reset("2010")
	GameState.replay_seed = SUITE_SEED
	GameState.career_seed = SUITE_SEED
	GameState.begin_real_lists()
	GameState.choose_real_club(CLUB)
	var guard := 0
	while GameState.draft != null and not GameState.draft.is_finished() and guard < 400:
		guard += 1
		if GameState.draft.is_user_turn():
			var board: Array = GameState.draft.board("", "", "", "overall", true)
			if board.is_empty() or not GameState.draft.pick(board[0]):
				break
	GameState.finish_intake_draft()


func _to_offseason() -> void:
	GameState.season.round_index = GameState.season.fixture.size()
	GameState.ensure_finals()
	while not GameState.season.is_season_over():
		GameState.advance()


func _test_rolls_past_2027() -> void:
	_start()
	_check(GameState.season_year == 2010 and GameDB.dataset_id == "2010",
			"The career begins in 2010 (%d, set %s)" % [GameState.season_year, GameDB.dataset_id])
	var originals := {}
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			originals[str(p["id"])] = true
	var sackings := []
	while GameState.season_year < PAST:
		var from := GameState.season_year
		_to_offseason()
		# The roll is under test, not the coach: a board may sack him with no
		# job to go to (that ends a career), so keep him on and say so.
		if GameState.is_sacked():
			sackings.append(from)
			GameState.board["sacked"] = false
			GameState.board["warned"] = false
		if not GameState.start_next_season():
			_check(false, "%d rolls into %d" % [from, from + 1])
			return
		var y := GameState.season_year
		# Gold Coast enter in 2011, GWS in 2012 and Tasmania in 2028
		# (data/clubs.csv); the league fields exactly the clubs entered by then.
		var want_clubs: int = GameDB.active_clubs(y).size()
		for joined in [["GCS", 2011], ["GWS", 2012], ["TAS", 2028]]:
			if y == joined[1]:
				_check(GameState.season.clubs.has(joined[0]) and GameDB.enter_year(joined[0]) == y,
						"%s enter in %d (entry year %d)" % [joined[0], y, GameDB.enter_year(joined[0])])
		var short := []
		for code in GameState.season.clubs:
			if GameState.season.lists.get(code, []).size() < 30:
				short.append("%s %d" % [code, GameState.season.lists.get(code, []).size()])
		_check(y == from + 1 and GameDB.dataset_id == "2010" and GameState.my_club == CLUB,
				"%d rolls into %d at St Kilda, still the 2010 career (%d, %s, set %s)" % [
					from, from + 1, y, GameState.my_club, GameDB.dataset_id])
		_check(GameState.season.clubs.size() == want_clubs and short.is_empty(),
				"%d: %d clubs with full lists (%d clubs; short: %s)" % [
					y, want_clubs, GameState.season.clubs.size(), ", ".join(short)])
	var left := 0
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			if originals.has(str(p["id"])):
				left += 1
	print("Legacy 2010 long: reached %d; %d of the 2010 players still listed; board sackings waved off in %s"
			% [GameState.season_year, left, str(sackings)])
	_check(GameState.season_year >= PAST, "The 2010 career reaches %d (%d)" % [PAST, GameState.season_year])
	_check(GameState.season.clubs.has("GCS") and GameState.season.clubs.has("GWS")
			and GameState.season.clubs.has("TAS"),
			"Gold Coast, GWS and Tasmania are in the league by %d" % GameState.season_year)
