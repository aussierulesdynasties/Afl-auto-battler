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
		var rosters: Array = sim.rosters()
		var stats: Dictionary = r["players"]
		for side in range(2):
			var t: Dictionary = (r["team"][side] as Dictionary).duplicate()
			t["score"] = int(r["score"][side])
			t["roles"] = role_lines(rosters[side], r["players"])
			t["carry_zone"] = (sim.carry_log[side] as Dictionary).duplicate()
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
		fh.store_line(JSON.stringify({"i": i, "home": h, "away": a, "teams": teams, "duels": duels(sim, r)}))
	fh.close()
	return 0


## Key forward v key defender (row 94): one row per key forward who had a
## direct opponent, contests from the engine's duel log (what the full-time
## line reads). [contests, marks, most contests against one defender,
## MatchNotes.duel_verdict over the match]. A key forward with none is a 0 row.
func duels(sim: MatchSim, r: Dictionary) -> Array:
	var log: Dictionary = r.get("duels", {})
	var ids := {}
	for side in range(2):
		for fid in (sim.duels[side] as Dictionary):
			ids[str(fid)] = true
	for fid in log:
		ids[str(fid)] = true
	var out := []
	for fid in ids:
		var n := 0
		var won := 0
		var per := {}
		for c in (log.get(fid, {}) as Dictionary).get("contests", []):
			n += 1
			won += 1 if bool(c[2]) else 0
			per[str(c[1])] = int(per.get(str(c[1]), 0)) + 1
		var top := 0
		for d in per:
			top = maxi(top, int(per[d]))
		out.append([n, won, top, MatchNotes.duel_verdict(won, n)])
	return out


## One side's box score by line, grouped by each player's own position
## (list_role, as afl_role_rates.json groups real players): player-games and
## the stats the role reference has, so the report can set them against real.
static func role_lines(roster: Array, players: Dictionary) -> Dictionary:
	var out := {}
	for p in roster:
		var role := str(p.get("list_role", p.get("role", "")))
		if not out.has(role):
			out[role] = {"pg": 0}
		var row: Dictionary = out[role]
		row["pg"] = int(row["pg"]) + 1
		var st: Dictionary = players.get(str(p["id"]), {})
		for k in ROLE_STATS:
			row[k] = float(row.get(k, 0.0)) + float(st.get(k, 0.0))
	return out


const ROLE_STATS := ["disposals", "kicks", "handballs", "marks", "rebounds", "inside50", "clearances", "goals"]
