extends RefCounted
## Former-player coaches (row 71, T5.Q15): what share of the league's coaching
## jobs former players of this league hold as a career runs on. The real
## 32-season career in DESIGN.md reached 102 of 119 jobs (86%) by 2058; the
## aspiration is 60-80%. Measurement only.
## Autopilot as long_career_impl: League Draft, then every season and
## off-season with no user management. After each season, league-wide: jobs
## filled, jobs held by former players (coach records with a
## former_player_id), the same for senior coaches, and how many former players
## have gone into coaching so far (records C_P_*, live or archived).
## Args after the impl name: seed club seasons (default 1 MEL 32: the first season is 2027, so the last rollover is into 2058, the
## DESIGN.md horizon). COACH_SEEDS=a,b,c plays one career per seed.
## godot --headless --path . --script tools/audit/run_audit.gd -- coach_rate_impl 1 MEL 2

var club := "MEL"


func _run_draft(d: Draft) -> void:
	var guard := 0
	while not d.is_finished() and guard < 5000:
		guard += 1
		var c := d._best_ai_pick(d.current_club())
		if c.is_empty() or not d._draft_pick(d.current_club(), c):
			d._skip_current_pick()


## [jobs, former-player jobs, senior coaches, former-player senior coaches,
## former players ever into coaching]
func _count() -> Array:
	var jobs := 0
	var fp := 0
	var sc := 0
	var fp_sc := 0
	for cid in GameState.coaches:
		var c: Dictionary = GameState.coaches[cid]
		if str(c.get("status", "")) != "club":
			continue
		var former := str(c.get("former_player_id", "")) != ""
		jobs += 1
		if former:
			fp += 1
		if str(c.get("job", "")) == "SC":
			sc += 1
			if former:
				fp_sc += 1
	var entered := 0
	for d in [GameState.coaches, GameState.coach_archive]:
		for cid in d:
			if str(cid).begins_with("C_P_"):
				entered += 1
	return [jobs, fp, sc, fp_sc, entered]


func _career(seed: int, seasons: int) -> void:
	GameState.reset()
	GameState.career_seed = seed
	GameState.replay_seed = seed
	GameState.autosave_enabled = false
	var pool: Array = GameDB.all_players_sorted() + GameDB.all_draftees_sorted()
	pool.sort_custom(func(a, b): return a["overall"] > b["overall"])
	GameState.draft = Draft.new(pool, GameDB.active_clubs(GameState.season_year).duplicate(), seed)
	GameState.draft.start_for_user(club)
	_run_draft(GameState.draft)
	GameState.start_season(club, GameState.draft.list())
	var endings := 0
	var last: Array = []
	for s in range(seasons):
		while not GameState.season.is_season_over():
			GameState.advance()
		if s == seasons - 1:
			break
		GameState.open_offseason()
		if GameState.begin_intake_draft():
			_run_draft(GameState.draft)
			GameState.finish_intake_draft()
		else:
			GameState.start_next_season()
		endings += (GameState.intake_summary.get("retired", []) as Array).size()
		last = _count()
		print("COACHRATE seed %d %d | jobs %d | former players %d (%.1f%%) | senior coaches %d of %d | into coaching so far %d (retirements %d; delisted players unsigned also enter)" % [
				seed, GameState.season_year, last[0], last[1], 100.0 * last[1] / maxf(1, last[0]),
				last[3], last[2], last[4], endings])
	if last.is_empty():
		last = _count()
	print("SUMMARY seed %d year %d jobs %d former %d share %.4f sc %d former_sc %d entered %d retirements %d" % [
			seed, GameState.season_year, last[0], last[1], float(last[1]) / maxf(1, last[0]),
			last[2], last[3], last[4], endings])


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seed := int(args[1]) if args.size() > 1 else 1
	club = str(args[2]) if args.size() > 2 else "MEL"
	var seasons := int(args[3]) if args.size() > 3 else 32
	var many := OS.get_environment("COACH_SEEDS")
	if many == "":
		_career(seed, seasons)
		return
	for s in many.split(","):
		_career(int(s), seasons)
