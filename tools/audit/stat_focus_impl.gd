extends RefCounted
## Stat focus (row 97): what one stat focus a season does to your list's
## development. Paired autopilot careers from the same seeds; only the arm
## differs:
##   off  - the stat_focus switch off (today's game)
##   top  - switch on, every player's focus is the stat his plan weights most
##   low  - switch on, every player's focus is the stat his plan weights least
## Each season start, every player on your list without a focus locked this
## season gets one. Prints one FOCUS line per seed and season: mean OVR change
## (all, and age 23 and under at the season start), mean change in the focus
## stat (or, for off, in the stat the top arm would pick) and the club's finish.
## Args after the impl name: arm seasons club. Env FOCUS_SEEDS=a,b,c (default 301,302,303).

var arm := "off"
var club := "MEL"


func _focus_key(p: Dictionary, highest: bool) -> String:
	var w: Dictionary = GameState.plan_weights(p)
	var best := ""
	for k in GameState.focus_options(p):
		if best == "":
			best = k
		elif highest and float(w.get(k, 0.0)) > float(w.get(best, 0.0)):
			best = k
		elif not highest and float(w.get(k, 0.0)) < float(w.get(best, 0.0)):
			best = k
	return best


func _pick_all() -> Dictionary:
	var keys := {}
	for p in GameState.my_list:
		var k := _focus_key(p, arm != "low")
		keys[str(p["id"])] = k
		if arm != "off" and k != "" and not GameState.focus_locked(p):
			GameState.set_stat_focus(str(p["id"]), k)
	return keys


func run() -> void:
	var args := OS.get_cmdline_user_args()
	arm = str(args[1]) if args.size() > 1 else "off"
	var seasons := int(args[2]) if args.size() > 2 else 3
	club = str(args[3]) if args.size() > 3 else "MEL"
	var seeds_env := OS.get_environment("FOCUS_SEEDS")
	var seeds: Array = (seeds_env if seeds_env != "" else "301,302,303").split(",")
	Features.set_on("stat_focus", arm != "off")
	for s in seeds:
		_career(int(s), seasons)
	Features.clear("stat_focus")


func _career(seed: int, seasons: int) -> void:
	GameState.reset()
	GameState.autosave_enabled = false
	GameState.career_seed = seed
	GameState.replay_seed = seed
	GameState.start_season(club, GameDB.club_list(club))
	for s in range(seasons):
		var keys := _pick_all()
		var start := {}
		for p in GameState.my_list:
			var k := str(keys.get(str(p["id"]), ""))
			start[str(p["id"])] = [int(p["overall"]), float(p.get("age", 25.0)),
					k, int((p.get("attr", {}) as Dictionary).get(k, 0))]
		while not GameState.season.is_season_over():
			GameState.advance()
		var all_d := []
		var young_d := []
		var stat_d := []
		var share := []
		for p in GameState.my_list:
			var id := str(p["id"])
			if not start.has(id):
				continue
			var st: Array = start[id]
			var d := int(p["overall"]) - int(st[0])
			all_d.append(d)
			if float(st[1]) <= 23.0:
				young_d.append(d)
			if str(st[2]) != "":
				stat_d.append(int((p.get("attr", {}) as Dictionary).get(str(st[2]), 0)) - int(st[3]))
			var led := GameState.focus_spent(p)
			if int(led[0]) + int(led[1]) > 0:
				share.append(float(led[0]) / float(int(led[0]) + int(led[1])))
		print("FOCUS arm %s seed %d season %d | OVR all %+.3f (n=%d) young %+.3f (n=%d) | focus stat %+.3f | focus share %.3f (n=%d) | finish %d" % [
				arm, seed, GameState.season_year, _mean(all_d), all_d.size(), _mean(young_d), young_d.size(),
				_mean(stat_d), _mean(share), share.size(), GameState.club_position(club)])
		if s == seasons - 1:
			break
		GameState.open_offseason()
		if GameState.begin_intake_draft():
			_run_draft(GameState.draft)
			GameState.finish_intake_draft()
		else:
			GameState.start_next_season()


func _run_draft(d: Draft) -> void:
	var guard := 0
	while not d.is_finished() and guard < 5000:
		guard += 1
		var c := d._best_ai_pick(d.current_club())
		if c.is_empty() or not d._draft_pick(d.current_club(), c):
			d._skip_current_pick()


func _mean(a: Array) -> float:
	if a.is_empty():
		return 0.0
	var t := 0.0
	for x in a:
		t += float(x)
	return t / float(a.size())
