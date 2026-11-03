extends RefCounted
## Auto-rotations across a season (competent-AI rule, 2026-11-03): seeded
## autopilot seasons, printing ladder spread, injuries, end-of-game energy,
## mean workload and the rotation plans clubs ran. Args: seeds (default
## 301,302,303), club (MEL). Compare runs on two code states by seed.

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seeds := (args[1] if args.size() > 1 else "301,302,303").split(",")
	var club := args[2] if args.size() > 2 else "MEL"
	for s in seeds:
		_season(int(s), club)

func _season(sd: int, club: String) -> void:
	GameState.reset()
	GameState.autosave_enabled = false
	GameState.career_seed = sd
	GameState.replay_seed = sd
	GameState.start_season(club, GameDB.club_list(club))
	var inj := 0
	var games := 0
	var rot := {}
	var energy_sum := 0.0
	var energy_n := 0
	var load_sum := 0.0
	var load_n := 0
	var guard := 0
	while not GameState.season.is_season_over() and guard < 40:
		guard += 1
		GameState.advance()
		for res in GameState.last_results:
			games += 1
			inj += (res.get("injuries", []) as Array).size()
			for th in res.get("tactics_history", []):
				for r in th.get("rotations", []):
					rot[str(r)] = int(rot.get(str(r), 0)) + 1
			var en: Dictionary = res.get("energy", {})
			for id in en:
				energy_sum += float(en[id])
				energy_n += 1
		if not GameState.season.is_regular_done():
			for code in GameState.season.lists:
				for p in GameState.season.lists[code]:
					load_sum += Workload.value(p)
					load_n += 1
	var pts := []
	for row in GameState.season.ladder_sorted():
		pts.append(int(row["pts"]))
	var mean := 0.0
	for v in pts:
		mean += v
	mean /= maxf(1.0, pts.size())
	var var_ := 0.0
	for v in pts:
		var_ += (v - mean) * (v - mean)
	var sdv := sqrt(var_ / maxf(1.0, pts.size()))
	print("ROT seed=%d games=%d ladder_sd=%.2f top=%d bottom=%d injuries=%d inj_per_game=%.3f mean_load=%.2f rotations=%s premier=%s" % [
		sd, games, sdv, pts[0], pts[pts.size() - 1], inj, float(inj) / maxf(1, games),
		load_sum / maxf(1, load_n), str(rot),
		str(GameState.season.finals.get("premier", "?"))])
