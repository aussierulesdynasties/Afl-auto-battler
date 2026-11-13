extends RefCounted
## A 2020 Legacy career driven as a coach would drive it, shared by the
## legacy_start_2020 suite (the start and its first rollover) and the nightly
## legacy_2020_long suite (the career past 2027).

const SEED := 2020


## A 2020 career at `club`, as Choose your club starts it.
static func start(club: String) -> void:
	GameState.reset("2020")
	GameState.replay_seed = SEED
	GameState.career_seed = SEED
	GameState.begin_real_lists()
	GameState.choose_real_club(club)
	finish_draft()
	GameState.finish_intake_draft()


## The off-season as the season review plays it (SeasonReviewScene
## _start_intake_draft): the intake draft opens, the coach takes the best player
## on the board at each of his picks, and the draft's end starts the next
## season; with no draft to run, the next season starts directly. True once
## the year has moved on.
static func roll_on() -> bool:
	var year: int = GameState.season_year
	if GameState.begin_intake_draft():
		finish_draft()
		GameState.finish_intake_draft()
	else:
		GameState.start_next_season()
	return GameState.season_year > year


static func finish_draft() -> void:
	var guard := 0
	while GameState.draft != null and not GameState.draft.is_finished() and guard < 400:
		guard += 1
		if GameState.draft.is_user_turn():
			var board: Array = GameState.draft.board("", "", "", "overall", true)
			if board.is_empty() or not GameState.draft.pick(board[0]):
				break
		else:
			GameState.draft.auto_until_user_turn()


## Why a rollover stopped, for a failure line.
static func state() -> String:
	var d := "none"
	if GameState.draft != null:
		d = "%s%s" % ["intake " if GameState.draft.intake_mode else "", "finished" if GameState.draft.is_finished() else "open"]
	return "sacked %s, draft %s, over %s" % [str(GameState.is_sacked()), d, str(GameState.season.is_season_over())]
