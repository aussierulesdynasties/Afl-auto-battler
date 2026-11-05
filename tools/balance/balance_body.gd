extends RefCounted
## Body of tools/balance/balance_worker.gd (loaded after autoloads are ready).
## Seed i: two real 2026 club lists picked from i, home side alternating, match
## seed 500000 + i. One JSON line per match: score, margin, every team stat and
## the shot counts (_shot_counts).


func play(from: int, count: int, out: String, on: PackedStringArray,
		off: PackedStringArray, weather: String) -> int:
	GameDB.skip_ovr_overrides = true
	GameDB.reload()
	for f in on:
		Features.set_on(f, true)
	for f in off:
		Features.set_on(f, false)
	# --tune KEY=V,KEY=V: MatchSim tunables (MatchSim.tune, read through _tv) for
	# sizing a constant before it is written into the code.
	var args := OS.get_cmdline_user_args()
	for i in range(args.size() - 1):
		if str(args[i]) == "--tune":
			for kv in str(args[i + 1]).split(",", false):
				var pair := kv.split("=")
				if pair.size() == 2:
					MatchSim.tune[pair[0].strip_edges()] = float(pair[1])
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
			_shot_counts(t, sim.shot_log, side)
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
		fh.store_line(JSON.stringify({"i": i, "home": h, "away": a, "teams": teams}))
	fh.close()
	return 0


## Set-shot bands by metres out, as docs/research/SET_SHOT_EVIDENCE.md gives them.
## The pocket (MatchSim SET_BANDS "pocket", 15 m on a tight angle) is its own
## band, "pocket", so it is checked against the wide-angle cells, not straight in front.
const SHOT_BANDS := [[10.0, "0-10"], [20.0, "10-20"], [30.0, "20-30"], [40.0, "30-40"], [50.0, "40-50"], [999.0, "50+"]]


## Shots off MatchSim.shot_log into the team row: set shots and general-play
## shots with their goals and behinds, and set shots by distance band
## ("sshot_<band>_n" shots, "_g" goals, "_b" behinds).
func _shot_counts(t: Dictionary, shots: Array, side: int) -> void:
	for k in ["sshot_n", "sshot_g", "sshot_b", "gshot_n", "gshot_g", "gshot_b"]:
		t[k] = 0
	for band in SHOT_BANDS + [[0.0, "pocket"]]:
		for x in ["_n", "_g", "_b"]:
			t["sshot_" + str(band[1]) + x] = 0
	for s in shots:
		if int(s[0]) != side:
			continue
		var pre := "sshot" if int(s[1]) == 1 else "gshot"
		var res := str(s[3])
		var keys := [pre]
		if pre == "sshot" and s.size() > 4 and str(s[4]) == "pocket":
			keys.append("sshot_pocket")
		elif pre == "sshot":
			for band in SHOT_BANDS:
				if float(s[2]) <= float(band[0]):
					keys.append("sshot_" + str(band[1]))
					break
		for k in keys:
			t[k + "_n"] += 1
			if res == "goal":
				t[k + "_g"] += 1
			elif res == "behind":
				t[k + "_b"] += 1
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
