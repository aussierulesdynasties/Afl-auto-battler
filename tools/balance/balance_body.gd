extends RefCounted
## Body of tools/balance/balance_worker.gd (loaded after autoloads are ready).
## Seed i: two real 2026 club lists picked from i, home side alternating, match
## seed 500000 + i. One JSON line per match: score, margin and every team stat,
## plus each side's list strength (Squad.strength) and score at each quarter's end (q_score).
## `sets` puts values on each MatchSim's own vars (--set name=value,...) to
## screen a tuning knob without editing the sim; a name the sim lacks fails.
## `echo` also prints each line as "BAL <json>" (tools/audit/balance_match_impl.gd).


func play(from: int, count: int, out: String, on: PackedStringArray,
		off: PackedStringArray, weather: String, sets: Dictionary = {}, echo := false) -> int:
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
		var sq_h := Squad.new(h, GameDB.club_list(h), true, h)
		var sq_a := Squad.new(a, GameDB.club_list(a), false, a)
		var sim := MatchSim.new(sq_h, sq_a, 500000 + i)
		sim.weather = weather
		for k in sets:
			if not str(k) in sim:
				push_error("balance: MatchSim has no var " + str(k))
				return 1
			sim.set(str(k), float(sets[k]))
		var r: Dictionary = sim.run()
		# Each side's score at the end of each quarter (for comebacks), from the
		# running score every event carries.
		var q_score := [[0, 0, 0, 0], [0, 0, 0, 0]]
		for ev in r["events"]:
			var sc = (ev as Dictionary).get("score", null)
			var q := int((ev as Dictionary).get("q", 0))
			if sc is Array and (sc as Array).size() == 2 and q >= 1:
				for k in range(clampi(q, 1, 4) - 1, 4):
					q_score[0][k] = int(sc[0])
					q_score[1][k] = int(sc[1])
		var teams := []
		var stats: Dictionary = r["players"]
		for side in range(2):
			var t: Dictionary = (r["team"][side] as Dictionary).duplicate()
			t["score"] = int(r["score"][side])
			t["strength"] = snappedf((sq_h if side == 0 else sq_a).strength(), 0.01)
			q_score[side][3] = int(r["score"][side])
			t["q_score"] = q_score[side]
			# Intercepts by each man's listed position (DEF, MID, FWD, RUCK), as
			# tools/audit/intercept_impl.gd counts them: "ic_MID" intercepts and
			# "pg_MID" player-games (every man who played and has a stat line).
			for pl in (r["roster"][side] as Array):
				var st: Dictionary = stats.get(str(pl["id"]), {})
				if st.is_empty():
					continue
				var role := str(pl.get("list_role", pl.get("role", "")))
				t["ic_" + role] = float(t.get("ic_" + role, 0.0)) + float(st.get("intercepts", 0.0))
				t["pg_" + role] = int(t.get("pg_" + role, 0)) + 1
			teams.append(t)
		var line := JSON.stringify({"i": i, "home": h, "away": a, "teams": teams})
		fh.store_line(line)
		if echo:
			print("BAL " + line)
	fh.close()
	return 0


## "a=1,b=0.5" -> {"a": 1.0, "b": 0.5}
static func parse_sets(text: String) -> Dictionary:
	var d := {}
	for kv in text.split(",", false):
		var parts := kv.split("=")
		if parts.size() == 2:
			d[parts[0].strip_edges()] = float(parts[1])
	return d
