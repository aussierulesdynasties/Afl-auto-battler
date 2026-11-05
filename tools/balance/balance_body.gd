extends RefCounted
## Body of tools/balance/balance_worker.gd (loaded after autoloads are ready).
## Seed i: two real 2026 club lists picked from i, home side alternating, match
## seed 500000 + i. One JSON line per match: score, margin and every team stat,
## plus each side's list strength (Squad.strength), score at each quarter's end (q_score)
## and the shot counts (_shot_counts).
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
	# --tune KEY=V,KEY=V: MatchSim tunables (MatchSim.tune, read through _tv) for
	# sizing a constant before it is written into the code.
	var args := OS.get_cmdline_user_args()
	for i in range(args.size() - 1):
		if str(args[i]) == "--tune":
			for kv in str(args[i + 1]).split(",", false):
				var pair := kv.split("=")
				if pair.size() == 2:
					MatchSim.tune[pair[0].strip_edges()] = float(pair[1])
	var gather := Features.on(GatherRound.SWITCH)
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
		# gather_round on: every match is staged as a Gather Round match (at the
		# host ground, a club's home edge only at its own ground), the per-match
		# effect of the one round a season it applies to.
		var at_home := [true, false]
		if gather:
			var ground: Callable = func(c): return str(GameDB.club(str(c)).get("ground", ""))
			var v := str(GatherRound.venues_for([{"home": h, "away": a}], 500000 + i, ground)[0])
			at_home = [ground.call(h) == v, ground.call(a) == v]
		var sq_h := Squad.new(h, GameDB.club_list(h), bool(at_home[0]), h)
		var sq_a := Squad.new(a, GameDB.club_list(a), bool(at_home[1]), a)
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
		var rosters: Array = sim.rosters()
		var stats: Dictionary = r["players"]
		for side in range(2):
			var t: Dictionary = (r["team"][side] as Dictionary).duplicate()
			t["score"] = int(r["score"][side])
			_shot_counts(t, sim.shot_log, side)
			t["strength"] = snappedf((sq_h if side == 0 else sq_a).strength(), 0.01)
			q_score[side][3] = int(r["score"][side])
			t["q_score"] = q_score[side]
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
		var line := JSON.stringify({"i": i, "home": h, "away": a, "teams": teams, "duels": duels(sim, r)})
		fh.store_line(line)
		if echo:
			print("BAL " + line)
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


## "a=1,b=0.5" -> {"a": 1.0, "b": 0.5}
static func parse_sets(text: String) -> Dictionary:
	var d := {}
	for kv in text.split(",", false):
		var parts := kv.split("=")
		if parts.size() == 2:
			d[parts[0].strip_edges()] = float(parts[1])
	return d


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
