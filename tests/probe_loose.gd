extends RefCounted
## Scratch probe (never committed): the ball at its logged spot, over several matches.

func run() -> void:
	GameState.replay_seed = 2027
	GameDB.reload()
	var tot_close := 0
	var tot_n := 0
	for seed in [42, 7, 11, 19, 23, 31, 57, 88]:
		var res := MatchSim.new(Squad.new("RIC", GameDB.club_list("RIC"), true, "RIC"),
				Squad.new("SYD", GameDB.club_list("SYD"), false, "SYD"), seed).run()
		res["home"] = "RIC"
		res["away"] = "SYD"
		res["label"] = "Round 1"
		var d := MatchDirector.new()
		d.setup(res, res["events"])
		var guard := 0
		while not d.idle() and guard < 400000:
			guard += 1
			d.advance(1.0 / 60.0 * 4.0)
		var close := 0
		for a in d.arrivals:
			if absf((a["pos"] as Vector2).x - float(a["want_x"])) <= 3.0:
				close += 1
		tot_close += close
		tot_n += d.arrivals.size()
		print("PROBE seed %d: %d of %d (%.2f%%)" % [seed, close, d.arrivals.size(), 100.0 * close / maxf(1.0, d.arrivals.size())])
	print("PROBE all: %d of %d (%.2f%%)" % [tot_close, tot_n, 100.0 * tot_close / maxf(1.0, tot_n)])
