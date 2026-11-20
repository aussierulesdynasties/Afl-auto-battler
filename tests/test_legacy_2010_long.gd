extends RefCounted
## A 2010 career never ends (director 2026-11-13: "campaigns can go for
## eternity"). A seeded career begun at Carlton in 2010 rolls season after
## season past 2027: Gold Coast enter in 2011, GWS in 2012 and Tasmania in 2028
## as the sim's own expansion, every club keeps a full list, and the career is still the one
## begun in 2010. Each off-season runs the drafts as the game does: a man his
## real club delisted goes even from a short list, and the draft fills it
## (#1676), so a rollover with no draft would leave the lists short. About 18
## seasons, so it runs nightly (tools/ci_long_suites.txt). Run through tests/run_legacy_2010_long_tests.gd.

const Ran := preload("res://tests/functions_ran.gd")

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 2010
const CLUB := "CAR"
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


## The off-season's drafts as legacy_2000_long runs them: the National Draft
## (his picks passed), then the Rookie Draft settled, so the list sizes read
## after are the season's own.
func _roll_through_draft() -> bool:
	if not GameState.begin_intake_draft():
		return GameState.start_next_season()
	var draft: Draft = GameState.draft
	var guard := 0
	draft.auto_until_user_turn()
	while not draft.is_finished() and guard < 4000:
		guard += 1
		# His pick: "Pick for me", the player the assistant would take, as a
		# rival takes at the same pick (a coach who passes every pick is no coach).
		if draft.is_user_turn() and draft.pick_for_me():
			draft.auto_until_user_turn()
			continue
		var cand := draft._best_ai_pick(draft.current_club())
		if cand.is_empty() or not draft._draft_pick(draft.current_club(), cand):
			draft._skip_current_pick()
		draft.auto_until_user_turn()
	if not GameState.finish_intake_draft():
		return false
	# The Rookie Draft: he takes the first man left, as each rival does
	# (RookieList._run), while he has a rookie spot to fill.
	var rguard := 0
	while RookieList.waiting(GameState) and rguard < 40:
		rguard += 1
		var left := MidseasonDraft.pool(GameState)
		if left.is_empty() or not RookieList.choose(GameState, str(left[0]["id"])):
			RookieList.choose(GameState, "")
	RookieList.settle(GameState)
	return true


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
		# A sacked coach is never put back in his job (director 2026-11-17: "never
		# reappoint the same coach after sacking"). The test career is one that
		# keeps its job to 2028 on the default board (director: "Pick a lasting
		# career"), so a sacking is a failure, not waved off.
		if GameState.is_sacked():
			sackings.append(from)
		_check(not GameState.is_sacked(), "The Carlton board keeps its coach after %d" % from)
		if not _roll_through_draft():
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
				"%d rolls into %d at Carlton, still the 2010 career (%d, %s, set %s)" % [
					from, from + 1, y, GameState.my_club, GameDB.dataset_id])
		_check(GameState.season.clubs.size() == want_clubs and short.is_empty(),
				"%d: %d clubs with full lists (%d clubs; short: %s)" % [
					y, want_clubs, GameState.season.clubs.size(), ", ".join(short)])
	var left := 0
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			if originals.has(str(p["id"])):
				left += 1
	print("Legacy 2010 long: reached %d; %d of the 2010 players still listed; board sackings in %s"
			% [GameState.season_year, left, str(sackings)])
	_check(GameState.season_year >= PAST, "The 2010 career reaches %d (%d)" % [PAST, GameState.season_year])
	_check(GameState.season.clubs.has("GCS") and GameState.season.clubs.has("GWS")
			and GameState.season.clubs.has("TAS"),
			"Gold Coast, GWS and Tasmania are in the league by %d" % GameState.season_year)
