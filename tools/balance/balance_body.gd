extends RefCounted
## Body of tools/balance/balance_worker.gd (loaded after autoloads are ready).
## Seed i: two real 2026 club lists picked from i, home side alternating, match
## seed 500000 + i. One JSON line per match: score, margin and every team stat.


func play(from: int, count: int, out: String, on: PackedStringArray,
		off: PackedStringArray, weather: String) -> int:
	GameDB.skip_ovr_overrides = true
	GameDB.reload()
	for f in on:
		Features.set_on(f, true)
	for f in off:
		Features.set_on(f, false)
	var codes: Array = GameDB.active_clubs(2026).duplicate()
	var pairs := []
	for a in range(codes.size()):
		for b in range(a + 1, codes.size()):
			pairs.append([codes[a], codes[b]])
	var fh := FileAccess.open(out, FileAccess.WRITE)
	if fh == null:
		push_error("balance: cannot write " + out)
		return 1
	for i in range(from, from + count):
		var p: Array = pairs[i % pairs.size()]
		var flip := (i / pairs.size()) % 2 == 1
		var h := str(p[1] if flip else p[0])
		var a := str(p[0] if flip else p[1])
		var sim := MatchSim.new(Squad.new(h, GameDB.club_list(h), true, h),
				Squad.new(a, GameDB.club_list(a), false, a), 500000 + i)
		sim.weather = weather
		var r: Dictionary = sim.run()
		var teams := []
		for side in range(2):
			var t: Dictionary = (r["team"][side] as Dictionary).duplicate()
			t["score"] = int(r["score"][side])
			teams.append(t)
		fh.store_line(JSON.stringify({"i": i, "home": h, "away": a, "teams": teams}))
	fh.close()
	return 0
