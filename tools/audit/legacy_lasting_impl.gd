extends RefCounted
## Which clubs keep their coach to 2028 in the legacy long careers
## (tests/test_legacy_2000_long.gd, tests/test_legacy_2010_long.gd). The same
## career as those tests, the same seed and the same off-season, at each club
## named: the director chose "Pick a lasting career" (#1744), so the tests start
## at a club whose board keeps its coach. Stops a club at its first sacking.
##
##   gh workflow run audit.yml --ref <branch> -f impl=legacy_lasting_impl \
##       -f env="LASTING_SET=2000 LASTING_CLUBS=GEE,BRL"
##
## LASTING_SET   2000 or 2010 (the seed is the set's year, as in the tests)
## LASTING_CLUBS club codes, comma-separated (default: every club in the set)
## LASTING_PAST  the season to reach (default 2028)

const DEFAULT_PAST := 2028


func run() -> void:
	# As the test runner: no save written each round.
	GameState.autosave_enabled = false
	GameState.save_path = "user://audit_career.save"
	var ds := OS.get_environment("LASTING_SET")
	if ds == "":
		ds = "2000"
	var past := int(OS.get_environment("LASTING_PAST")) if OS.get_environment("LASTING_PAST") != "" else DEFAULT_PAST
	var clubs: Array = []
	if OS.get_environment("LASTING_CLUBS") != "":
		clubs = Array(OS.get_environment("LASTING_CLUBS").split(","))
	else:
		GameState.reset(ds)
		clubs = GameDB.active_clubs(int(ds))
	for club in clubs:
		var t0 := Time.get_ticks_msec()
		var out := _career(ds, str(club), past)
		print("LASTING set %s club %s: %s (%.0f s)" % [ds, club, out, (Time.get_ticks_msec() - t0) / 1000.0])


func _career(ds: String, club: String, past: int) -> String:
	GameState.reset(ds)
	GameState.replay_seed = int(ds)
	GameState.career_seed = int(ds)
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
	var wins := []
	while GameState.season_year < past:
		var from := GameState.season_year
		GameState.skip_season()
		while not GameState.season.is_season_over() and not GameState.is_sacked():
			GameState.advance()
		wins.append(_wins(GameState.my_club))
		if GameState.is_sacked():
			return "sacked after %d (wins by season %s)" % [from, str(wins)]
		if not _roll_through_draft():
			return "stopped rolling into %d" % (from + 1)
		if GameState.my_club != club:
			return "left the club in %d" % GameState.season_year
	return "lasted to %d (wins by season %s)" % [GameState.season_year, str(wins)]


func _wins(code: String) -> int:
	var row: Dictionary = GameState.season.ladder.get(code, {})
	return int(row.get("w", -1))


## As the tests' _roll_through_draft: the National Draft with Pick for me, then
## the Rookie Draft settled.
func _roll_through_draft() -> bool:
	if not GameState.begin_intake_draft():
		return GameState.start_next_season()
	var draft: Draft = GameState.draft
	var guard := 0
	draft.auto_until_user_turn()
	while not draft.is_finished() and guard < 4000:
		guard += 1
		if draft.is_user_turn() and draft.pick_for_me():
			draft.auto_until_user_turn()
			continue
		var cand := draft._best_ai_pick(draft.current_club())
		if cand.is_empty() or not draft._draft_pick(draft.current_club(), cand):
			draft._skip_current_pick()
		draft.auto_until_user_turn()
	if not GameState.finish_intake_draft():
		return false
	var rguard := 0
	while RookieList.waiting(GameState) and rguard < 40:
		rguard += 1
		var left := MidseasonDraft.pool(GameState)
		if left.is_empty() or not RookieList.choose(GameState, str(left[0]["id"])):
			RookieList.choose(GameState, "")
	RookieList.settle(GameState)
	return true
