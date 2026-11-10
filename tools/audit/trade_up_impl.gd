extends RefCounted
## Row 67 (4.Q11): can a coach who wants an upgrade and has spare assets get
## one? Seeded League Draft careers on autopilot; at each off-season, for every
## rival, the players who would walk into your side next season (3 points or
## more over your 22nd best, 30 or under) and whether a package of your spare
## assets alone (picks, players outside your best 26 who are not kids still
## growing; up to three pieces) gets a yes. Measurement only.
## Args: seeds (comma list, default 301) seasons (default 3).
## Prints one UPGRADE line per off-season: rivals, rivals holding an upgrade,
## rivals with a deal on spare assets, how many such players, and the
## refusal codes for the cheapest spare package tried on each target.

var dyn = load("res://tools/balance/dynasty.gd").new()


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seeds := str(args[1]) if args.size() > 1 else "301"
	var seasons := int(args[2]) if args.size() > 2 else 3
	for sd in seeds.split(",", false):
		_career(int(sd), seasons)


func _career(seed: int, seasons: int) -> void:
	var gs := GameDB.get_tree().root.get_node("GameState")
	gs.autosave_enabled = false
	gs.reset()
	gs.career_seed = seed
	gs.replay_seed = seed
	var d: Draft = dyn.make_upside_draft(seed, 5)
	var user := d.user_club if d.user_club != "" else str(d.draft_order[0])
	gs.draft = d
	gs.start_season(user, [])
	for y in range(seasons):
		while not gs.season.is_season_over():
			dyn._play_week(gs, user, false)
		gs.open_offseason()
		if OS.get_environment("TU_MODE") == "search":
			_probe(gs, seed, user)
		else:
			_ask(gs, seed, user)
		if y == seasons - 1:
			break
		gs.set_selection({})
		var mgmt := {"resigned": 0, "released": 0, "signed": 0, "trades": 0, "trade_in": [], "trade_out": 0}
		if not dyn._offseason(gs, user, mgmt):
			return


func _probe(gs, seed: int, user: String) -> void:
	var t0 := Time.get_ticks_msec()
	var line22: float = dyn.nth_value(gs.my_list, 21)
	var line26: float = dyn.nth_value(gs.my_list, 25)
	var spare := []
	for pk in gs.club_picks(user):
		spare.append(str(pk["id"]))
	for q in gs.my_list:
		if dyn._spare(q, line26):
			spare.append(str(q["id"]))
	var rivals := 0
	var holding := 0
	var dealt := 0
	var targets := 0
	var workable := 0
	var codes := {}
	gs._freeze_league(true)
	for club in GameDB.active_clubs(gs.season_year):
		if str(club) == user:
			continue
		rivals += 1
		var ups := []
		for q in gs.season.lists.get(club, []):
			if dyn.expected_overall(q, 1) >= line22 + 3.0 and float(q.get("age", 30.0)) <= 30.0:
				ups.append(q)
		if ups.is_empty():
			continue
		holding += 1
		var any := false
		for q in ups:
			targets += 1
			var ok := false
			var last := ""
			for pkg in _packages(spare):
				var v: Dictionary = gs.evaluate_trade(str(club), pkg, [str(q["id"])])
				if bool(v.get("ok", false)):
					ok = true
					break
				last = str(v.get("code", ""))
			if ok:
				workable += 1
				any = true
			else:
				codes[last] = int(codes.get(last, 0)) + 1
		if any:
			dealt += 1
	gs._freeze_league(false)
	print("UPGRADE seed %d year %d rivals %d holding %d dealt %d targets %d workable %d spare %d ms %d codes %s" % [
			seed, gs.season_year, rivals, holding, dealt, targets, workable, spare.size(),
			Time.get_ticks_msec() - t0, str(codes)])


## The coach who asks: for each rival, the players who would walk into his
## side, best first; he asks their price (GameState.ask_price) and agrees
## when everything asked is spare (a pick, or a player outside his best 26
## who is not a kid). At most two trades an off-season, one per rival.
func _ask(gs, seed: int, user: String) -> void:
	var t0 := Time.get_ticks_msec()
	var made := 0
	var asked := 0
	var priced := 0
	var log := []
	for club in GameDB.active_clubs(gs.season_year):
		if str(club) == user or made >= 2:
			continue
		var line22: float = dyn.nth_value(gs.my_list, 21)
		var line26: float = dyn.nth_value(gs.my_list, 25)
		var ups := (gs.season.lists.get(club, []) as Array).filter(func(q):
			return dyn.expected_overall(q, 1) >= line22 + 3.0 and float(q.get("age", 30.0)) <= 30.0)
		ups.sort_custom(func(a, b): return dyn.expected_overall(a, 1) > dyn.expected_overall(b, 1))
		for q in ups:
			asked += 1
			var r: Dictionary = gs.ask_price(str(club), str(q["id"]))
			if not bool(r["ok"]):
				continue
			priced += 1
			var spare := true
			for id in r["mine"]:
				if str(id).begins_with("pick:"):
					continue
				var p: Dictionary = gs.list_player(str(id))
				spare = spare and not p.is_empty() and dyn._spare(p, line26)
			if not spare:
				continue
			if bool(gs.make_trade(str(club), r["mine"], r["theirs"]).get("ok", false)):
				made += 1
				log.append("%s %d/%d for %s" % [club, int(q["overall"]), int(q.get("potential", 0)), ",".join(r["mine"])])
				break
	print("ASK seed %d year %d asked %d priced %d trades %d ms %d %s" % [seed, gs.season_year, asked, priced, made,
			Time.get_ticks_msec() - t0, " | ".join(log)])


## Every package of one to three of `ids`.
func _packages(ids: Array) -> Array:
	var out := []
	for i in range(ids.size()):
		out.append([ids[i]])
	for i in range(ids.size()):
		for j in range(i + 1, ids.size()):
			out.append([ids[i], ids[j]])
	for i in range(ids.size()):
		for j in range(i + 1, ids.size()):
			for k in range(j + 1, ids.size()):
				out.append([ids[i], ids[j], ids[k]])
	return out
