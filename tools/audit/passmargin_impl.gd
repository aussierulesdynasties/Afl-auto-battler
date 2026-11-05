extends RefCounted
## How often a learning-a-position project passes (row 93, T8.Q15: the pass
## margin). Measurement only. Per seed, a League Draft drafted as an AI club
## would, then seasons in which you keep both project places busy (the
## highest-POT eligible player, a new line where he can, as projpair_impl);
## rival clubs run theirs as the game does (_ai_projects).
## Per seed: your verdicts (learned / not taken) and, for each, the gap at the
## verdict (his own rating minus his rating there; he passes when the gap is
## at most GameState.PROJECT_PASS), and every club's verdicts from the career
## facts. Run the same seeds before and after a margin change to pair them.
## Args after the impl name: seeds (comma-separated) club seasons
## Prints a SEED line per seed and a TOTAL line.

var club := "MEL"


func _run_draft(d: Draft) -> void:
	var guard := 0
	while not d.is_finished() and guard < 5000:
		guard += 1
		var c := d._best_ai_pick(d.current_club())
		if c.is_empty() or not d._draft_pick(d.current_club(), c):
			d._skip_current_pick()


func _fill_projects() -> void:
	while GameState.active_projects() < GameState.PROJECT_MAX:
		var best := {}
		var best_jobs := []
		for p in GameState.my_list:
			var jobs: Array = GameState.learnable_jobs(p)
			if not jobs.is_empty() and (best.is_empty() or int(p.get("potential", 0)) > int(best.get("potential", 0))):
				best = p
				best_jobs = jobs
		if best.is_empty():
			return
		var job := str(best_jobs[0])
		var have := Ratings.positions(best)
		for j in best_jobs:
			if str(GameState.LEARN_JOBS[j]["role"]) in ["FWD", "MID", "DEF"] and not have.has(str(GameState.LEARN_JOBS[j]["role"])):
				job = str(j)
				break
		GameState.set_player_plan(str(best["id"]), GameState.LEARN_PREFIX + job)


## One career: {"mine": [[learned, gap], ...], "league": [learned, not taken]}.
func _career(seed: int, seasons: int) -> Dictionary:
	GameState.reset()
	GameState.autosave_enabled = false
	GameState.replay_seed = seed
	var pool: Array = GameDB.all_players_sorted() + GameDB.all_draftees_sorted()
	pool.sort_custom(func(a, b): return a["overall"] > b["overall"])
	GameState.draft = Draft.new(pool, GameDB.active_clubs(GameState.season_year).duplicate(), seed)
	GameState.draft.start_for_user(club)
	_run_draft(GameState.draft)
	GameState.start_season(club, GameState.draft.list())
	var mine := []
	var rivals := []
	for s in range(seasons):
		var seen := {}
		_fill_projects()
		while not GameState.season.is_season_over():
			var before := _learning()
			GameState.advance()
			for r in (GameState.last_training_report.get("projects", []) as Array):
				var key := "%s|%d" % [str(r["id"]), GameState.season_year]
				if not seen.has(key):  # a bye week leaves last week's report
					seen[key] = true
					mine.append([bool(r["learned"]), int(r["own"]) - int(r["there"])])
			_judged(before, rivals)
			_fill_projects()
		if s == seasons - 1:
			break
		GameState.open_offseason()
		if GameState.begin_intake_draft():
			_run_draft(GameState.draft)
			GameState.finish_intake_draft()
		else:
			GameState.start_next_season()
	var league := [0, 0]
	for id in GameState.career_facts:
		for f in CareerFacts.of(GameState.career_facts, str(id), "project"):
			if str(f["out"]) == "learned":
				league[0] += 1
			elif str(f["out"]) == "not taken":
				league[1] += 1
	return {"mine": mine, "league": league, "rivals": rivals}


## Rival players learning a position now: {id: [player, role]}.
func _learning() -> Dictionary:
	var out := {}
	for c in GameState.season.lists:
		if str(c) == club:
			continue
		for p in GameState.season.lists[c]:
			if GameState.project_job(p) != "":
				out[str(p["id"])] = [p, GameState.project_role(p)]
	return out


## Rival projects judged this week (the project is gone): [learned, gap], the
## gap read just after the verdict (training is where both ratings move, and
## the verdict closes that week's training).
func _judged(before: Dictionary, rivals: Array) -> void:
	for id in before:
		var p: Dictionary = before[id][0]
		if GameState.project_job(p) != "":
			continue
		var role := str(before[id][1])
		var gap := int(p.get("overall", 0)) - GameState.rating_as(p, role)
		var learned := Ratings.positions(p).has(role)
		rivals.append([learned, gap])


func _gaps(rows: Array) -> String:
	var h := {}
	for r in rows:
		h[int(r[1])] = int(h.get(int(r[1]), 0)) + 1
	var keys := h.keys()
	keys.sort()
	var parts := []
	for k in keys:
		parts.append("%d:%d" % [k, h[k]])
	return " ".join(parts)


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seeds := (str(args[1]) if args.size() > 1 else "301").split(",")
	club = str(args[2]) if args.size() > 2 else "MEL"
	var seasons := int(args[3]) if args.size() > 3 else 3
	var all_mine := []
	var all_rivals := []
	var lg := [0, 0]
	for s in seeds:
		var r := _career(int(s), seasons)
		var mine: Array = r["mine"]
		var learned := 0
		for m in mine:
			if bool(m[0]):
				learned += 1
		all_mine.append_array(mine)
		all_rivals.append_array(r["rivals"])
		lg[0] += int(r["league"][0])
		lg[1] += int(r["league"][1])
		print("SEED %s %s margin %d | yours %d of %d learned | league %d learned, %d not taken | gap at verdict (own minus there: count) yours %s | rivals %s" % [
				s, club, GameState.PROJECT_PASS, learned, mine.size(), r["league"][0], r["league"][1], _gaps(mine), _gaps(r["rivals"])])
	var learned_all := 0
	for m in all_mine:
		if bool(m[0]):
			learned_all += 1
	print("TOTAL %s margin %d seeds %s seasons %d | yours %d of %d learned | league %d learned, %d not taken | gap at verdict yours %s | rivals %s" % [
			club, GameState.PROJECT_PASS, ",".join(seeds), seasons, learned_all, all_mine.size(), lg[0], lg[1], _gaps(all_mine), _gaps(all_rivals)])
