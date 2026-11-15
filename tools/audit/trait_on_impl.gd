extends RefCounted
## Bug bash 5 (traits): each player trait's measured effect, one player at a
## time. The real 2026 lists, neighbours in strength, paired seeds: each match
## twice from the same seed, side 0's chosen carrier with the trait removed
## from MatchSim's trait cache and with it added. Nothing else changes (his
## stats, the synergies worked out at kick-off, the opposition), so the
## difference is the trait's own effect at every MatchSim._trait site. Sites
## that call Traits.has/of directly (Matchups.mark_shift, interceptor_score,
## minder_candidates, _roam_drag) still see his natural traits in both arms.
##
## MODE=prev prints how common each trait is on the real lists instead.
## Env: TRAITS (comma list of variants, default all), TRAIT_REPS (seeds per
## pairing, default 6). A variant is a trait key, optionally @LINE for the
## carrier's line, +wet for a wet day, +finals for finals_mode.

const PSTATS := ["disposals", "clearances", "hitouts", "marks", "contested_marks", "goals", "behinds",
		"shots", "spoils", "one_percenters", "intercept_marks", "intercepts", "clangers", "frees_against",
		"fifties_against", "tackles", "inside50", "goal_assists", "ground_ball_gets", "contested_possessions"]
const TSTATS := ["goals", "behinds", "hitouts", "clearances", "disposals", "marks", "clangers", "frees_against",
		"inside50", "contested_marks", "metres_gained"]
const ALL := ["ball_magnet", "bull", "ruck_king", "aerial", "crumber", "sharpshooter", "playmaker",
		"interceptor", "lockdown@DEF", "lockdown@MID", "engine", "big_game", "big_game+finals", "hothead",
		"wet_weather+wet", "wet_weather"]


func _env(k: String, d: String) -> String:
	var v := OS.get_environment(k)
	return v if v != "" else d


func run() -> void:
	var lb = load("res://tools/balance/league_balance.gd").new()
	var lists: Dictionary = lb.real_lists()
	if _env("MODE", "pair") == "prev":
		_prevalence(lists)
		return
	if _env("MODE", "pair") == "slot":
		_slot(lists)
		return
	var reps := int(_env("TRAIT_REPS", "6"))
	var variants: Array = _env("TRAITS", ",".join(ALL)).split(",")
	var codes: Array = lb.clubs()
	var ratings: Dictionary = lb.club_ratings(lists, codes)
	codes.sort_custom(func(x, y): return float(ratings[x]["strength"]) > float(ratings[y]["strength"]))
	for v in variants:
		_variant(str(v), lists, codes, reps)


func _parse(v: String) -> Dictionary:
	var out := {"key": v, "line": "", "wet": false, "finals": false}
	var parts := v.split("+")
	out["key"] = parts[0]
	for i in range(1, parts.size()):
		out[parts[i]] = true
	if str(out["key"]).contains("@"):
		var kl := str(out["key"]).split("@")
		out["key"] = kl[0]
		out["line"] = kl[1]
	return out


## The side's carrier for a trait: the best by the trait's stat among the
## lines it counts for (a named line first).
func _carrier(ground: Array, cfg: Dictionary) -> Dictionary:
	var key := str(cfg["key"])
	var stat := ""
	var roles: Array = []
	if key == "wet_weather":
		stat = "contested"
		roles = ["MID"]
	else:
		var d: Dictionary = Traits.DEFS[key]
		stat = str(d["stat"])
		roles = d["roles"]
	if str(cfg["line"]) != "":
		roles = [str(cfg["line"])]
	var best: Dictionary = {}
	var best_v := -INF
	for p in ground:
		if not roles.is_empty() and not roles.has(str(p["role"])):
			continue
		var v := float((p["attr"] as Dictionary).get(stat, 0))
		if key == "hothead":
			v = -v
		if key == "crumber" and int((p["attr"] as Dictionary).get("marking", 0)) >= 52:
			v -= 1000.0
		if v > best_v:
			best_v = v
			best = p
	return best


func _play(lists: Dictionary, a: String, b: String, seed: int, cfg: Dictionary, on: bool) -> Array:
	var sim := MatchSim.new(Squad.new(a, lists[a], true, a), Squad.new(b, lists[b], false, b), seed)
	if bool(cfg["wet"]):
		sim.set_day("wet")
	if bool(cfg["finals"]):
		sim.finals_mode = true
	var c := _carrier((sim.squads[0] as Squad).ground, cfg)
	var key := str(cfg["key"])
	var tr: Array = Traits.of(c).duplicate()
	var natural := tr.has(key)
	tr.erase(key)
	if on:
		tr.append(key)
	sim._traits[str(c["id"])] = tr
	return [sim.run(), str(c["id"]), natural]


func _variant(v: String, lists: Dictionary, codes: Array, reps: int) -> void:
	var cfg := _parse(v)
	var d := {}
	var base := {}
	var n := 0
	var nat := 0
	var add := func(k: String, off: float, on: float) -> void:
		if not d.has(k):
			d[k] = []
			base[k] = 0.0
		(d[k] as Array).append(on - off)
		base[k] = float(base[k]) + off
	for i in range(0, codes.size() - 1, 2):
		for flip in [false, true]:
			var a := str(codes[i + (1 if flip else 0)])
			var b := str(codes[i + (0 if flip else 1)])
			for k in range(reps):
				var seed: int = 7001 + i * 1009 + k * 7919 + (31 if flip else 0)
				var r0 := _play(lists, a, b, seed, cfg, false)
				var r1 := _play(lists, a, b, seed, cfg, true)
				var off: Dictionary = r0[0]
				var on: Dictionary = r1[0]
				var id := str(r0[1])
				n += 1
				if bool(r0[2]):
					nat += 1
				var po: Dictionary = (off["players"] as Dictionary).get(id, {})
				var pn: Dictionary = (on["players"] as Dictionary).get(id, {})
				for s in PSTATS:
					add.call("P." + s, float(po.get(s, 0.0)), float(pn.get(s, 0.0)))
				for s in TSTATS:
					add.call("T." + s, float((off["team"][0] as Dictionary).get(s, 0.0)), float((on["team"][0] as Dictionary).get(s, 0.0)))
					add.call("O." + s, float((off["team"][1] as Dictionary).get(s, 0.0)), float((on["team"][1] as Dictionary).get(s, 0.0)))
				var mo := float(off["score"][0]) - float(off["score"][1])
				var mn := float(on["score"][0]) - float(on["score"][1])
				add.call("margin", mo, mn)
				add.call("win", 1.0 if mo > 0 else (0.5 if mo == 0 else 0.0), 1.0 if mn > 0 else (0.5 if mn == 0 else 0.0))
				var q4o: float = 6 * int(off["q_goals"][3][0]) + int(off["q_behinds"][3][0]) - 6 * int(off["q_goals"][3][1]) - int(off["q_behinds"][3][1])
				var q4n: float = 6 * int(on["q_goals"][3][0]) + int(on["q_behinds"][3][0]) - 6 * int(on["q_goals"][3][1]) - int(on["q_behinds"][3][1])
				add.call("q4margin", q4o, q4n)
				var pq_o: float = 6 * int(off["q_goals"][3][0]) + int(off["q_behinds"][3][0])
				var pq_n: float = 6 * int(on["q_goals"][3][0]) + int(on["q_behinds"][3][0])
				add.call("q4score", pq_o, pq_n)
	print("")
	print("VARIANT %s | pairs %d | carrier naturally has it %d/%d" % [v, n, nat, n])
	var keys := d.keys()
	keys.sort()
	for k in keys:
		var xs: Array = d[k]
		var m := _mean(xs)
		var se := _se(xs)
		var b0 := float(base[k]) / maxf(1.0, n)
		if absf(m) < 1e-9 and se < 1e-9:
			continue
		print("ROW %s | %s | base %.3f | diff %+.4f | se %.4f | rel %+.1f%% | z %+.1f" % [v, k, b0, m, se,
				100.0 * m / b0 if absf(b0) > 1e-9 else 0.0, m / se if se > 1e-9 else 0.0])


func _prevalence(lists: Dictionary) -> void:
	var n := 0
	var have := {}
	var qual := {}
	var dropped := {}
	var by_count := {}
	var fwd := 0
	var fwd_df := 0
	var role_via_other := {}
	var near_miss := 0
	for c in lists:
		for p in lists[c]:
			n += 1
			var tr: Array = Traits.of(p)
			for t in tr:
				have[t] = int(have.get(t, 0)) + 1
			# Every good trait he clears, uncapped (Traits.of's rule without MAX_GOOD).
			var attr: Dictionary = p.get("attr", {})
			var roles := [str(p.get("role", "")), str(p.get("list_tag", ""))] + Traits.positions_of(p)
			var q := 0
			for key in Traits.DEFS:
				var d: Dictionary = Traits.DEFS[key]
				if d.has("max"):
					continue
				var need: Array = d["roles"]
				if not need.is_empty():
					var ok := false
					for r in ([str(p.get("role", ""))] if bool(d.get("own_role", false)) else roles):
						if need.has(r):
							ok = true
					if not ok:
						continue
				if int(attr.get(str(d["stat"]), 0)) < int(d["min"]):
					continue
				if bool(d.get("small", false)) and int(attr.get("marking", 0)) >= 52:
					continue
				q += 1
				qual[key] = int(qual.get(key, 0)) + 1
				if not need.is_empty() and not need.has(str(p.get("role", ""))):
					role_via_other[key] = int(role_via_other.get(key, 0)) + 1
				if not tr.has(key):
					dropped[key] = int(dropped.get(key, 0)) + 1
			by_count[q] = int(by_count.get(q, 0)) + 1
			if str(p.get("role", "")) == "FWD":
				fwd += 1
				if tr.has("def_forward"):
					fwd_df += 1
			# Training's "near" list against Traits.of's role rule.
			for r in Traits.near(p):
				if tr.has(str(r["key"])):
					near_miss += 1
	print("PREV players %d" % n)
	var keys := qual.keys() + have.keys()
	var seen := {}
	for k in keys:
		if seen.has(k):
			continue
		seen[k] = true
		print("PREV %s | carries %d (%.1f%%) | clears the line %d | dropped by the five-cap %d | clears it only via a non-own position %d" % [
				k, int(have.get(k, 0)), 100.0 * int(have.get(k, 0)) / n, int(qual.get(k, 0)), int(dropped.get(k, 0)),
				int(role_via_other.get(k, 0))])
	var ks := by_count.keys()
	ks.sort()
	var parts := []
	for k in ks:
		parts.append("%d: %d" % [k, int(by_count[k])])
	print("PREV good traits cleared per player (uncapped) | %s" % ", ".join(parts))
	print("PREV forwards %d | with Defensive forward %d (%.1f%%)" % [fwd, fwd_df, 100.0 * fwd_df / maxi(1, fwd)])
	print("PREV near() rows naming a trait he already has: %d" % near_miss)


func _mean(xs: Array) -> float:
	var t := 0.0
	for x in xs:
		t += x
	return t / maxf(1.0, xs.size())


func _se(xs: Array) -> float:
	var m := _mean(xs)
	var v := 0.0
	for x in xs:
		v += (x - m) * (x - m)
	return sqrt(v / maxf(1.0, xs.size() - 1)) / sqrt(maxf(1.0, xs.size()))


## Traits on match day (the slot copy) against the list player's (the profile).
func _slot(lists: Dictionary) -> void:
	var gained := {}
	var lost := {}
	var n := 0
	var near_df := 0
	var cross_df := 0
	for c in lists:
		for p in lists[c]:
			if str(p.get("role", "")) != "FWD" and str(p.get("role2", "")) == "FWD":
				var pr := int((p["attr"] as Dictionary).get("pressure", 0))
				if pr >= 38 and pr < 44:
					near_df += 1
				if pr >= 44:
					cross_df += 1
		var sq := Squad.new(str(c), lists[c], true, str(c))
		var by_id := {}
		for p in lists[c]:
			by_id[str(p["id"])] = p
		for g in sq.ground + sq.bench:
			n += 1
			var prof: Array = Traits.of(by_id[str(g["id"])])
			var day: Array = Traits.of(g)
			for t in day:
				if not prof.has(t):
					gained[t] = int(gained.get(t, 0)) + 1
					print("SLOTGAIN %s | %s %s | own %s slot %s | %s" % [c, g.get("first", ""), g.get("last", ""), str(g.get("own_role", "")), str(g.get("role", "")), t])
			for t in prof:
				if not day.has(t):
					lost[t] = int(lost.get(t, 0)) + 1
					print("SLOTLOSS %s | %s %s | own %s slot %s | %s" % [c, g.get("first", ""), g.get("last", ""), str(g.get("own_role", "")), str(g.get("role", "")), t])
	var mids := 0
	var mids_df := 0
	for c in lists:
		for p in lists[c]:
			if str(p.get("role", "")) in ["MID", "DEF"] and int((p["attr"] as Dictionary).get("pressure", 0)) >= 44:
				mids += 1
				if Traits.of(Ratings._for_slot(p, "FWD")).has("def_forward") and not Traits.of(p).has("def_forward"):
					mids_df += 1
	print("SLOT midfielders/defenders with Pressure 44+: %d | picked in a FWD slot they carry Defensive forward: %d" % [mids, mids_df])
	print("SLOT selected %d | gained on match day %s | lost on match day %s" % [n, str(gained), str(lost)])
	print("SLOT non-forwards with second position FWD: Pressure 38-43 (Training shows Defensive forward near) %d, Pressure 44+ (cleared, never earn it) %d" % [near_df, cross_df])
