extends RefCounted
## Bug bash 5, synergies (evidence only). Two modes (env B5_MODE):
##   act - activation: real 2026 lists and drafted leagues (SYN_DRAFTS); per
##         synergy the share of clubs with it on, one short, and on only if the
##         five-trait cap were lifted (carriers who clear the line but lose
##         the trait to the cap). Lists each real club's synergies.
##   eff - SYN_ON forced on for side 0 vs off, same seed, real lists (or
##         drafted with B5_LISTS=drafted), neighbours in strength, both ways.
##         Paired B-A with SE for the margin, win, Q4 margin and the
##         mechanism stats each synergy should move.
##   share - natural play: for every side with a synergy on at the first
##         bounce, the share of the match's chains it stayed on (synergies
##         follow the 18 on the ground since bug bash 5).
## SYN_ON may list several keys (comma-separated): switched on and off
## together (a stacked set). SYN_FORCE: "carriers" (default) picks carriers
## from side 0's starting 18 (natural carriers first, then the trait's roles,
## then its stat) and has the synergy on while they are all on the ground, so
## rotations count as they do for a real side; "always" holds it on all match.
## SYN_POWER=key:value,... tries a power (Traits.power_tune).
## B5_MODE=eff SYN_ON=tall_small SYN_REPS=40 godot --headless --path . --script tools/audit/run_audit.gd -- b5syn_impl

var DRAFTS: Array = _env_ints("SYN_DRAFTS", [21, 22, 23, 24])
var REPS: int = int(OS.get_environment("SYN_REPS")) if OS.get_environment("SYN_REPS") != "" else 8
var lb


static func _env_ints(key: String, fallback: Array) -> Array:
	var v := OS.get_environment(key)
	if v == "":
		return fallback
	var out := []
	for part in v.split(","):
		out.append(int(part))
	return out


func run() -> void:
	lb = load("res://tools/balance/league_balance.gd").new()
	var pw := OS.get_environment("SYN_POWER")
	if pw != "":
		for part in pw.split(","):
			var kv := part.split(":")
			Traits.power_tune[kv[0]] = float(kv[1])
		print("power tune: %s" % str(Traits.power_tune))
	if OS.get_environment("B5_MODE") == "eff":
		_eff(OS.get_environment("SYN_ON"))
	elif OS.get_environment("B5_MODE") == "share":
		_share()
	else:
		_act()


## Synergies held by named carriers for side 0: on while all of them are on
## the ground (SYN_FORCE carriers); side 0's other synergies as normal.
class CarrierSim extends MatchSim:
	var carriers := {}   # key -> [ids]

	func _init(h: Squad, a: Squad, s: int) -> void:
		super(h, a, s)

	func _refresh_synergies(side: int, feed := true) -> void:
		super(side, feed)
		if side != 0:
			return
		var on := {}
		for p in (squads[0] as Squad).ground:
			on[str(p["id"])] = true
		for key in carriers:
			(synergies[0] as Array).erase(key)
			var ok := true
			for id in carriers[key]:
				if not on.has(id):
					ok = false
			if ok:
				(synergies[0] as Array).append(key)


## Carriers for `key` from a starting 18: per trait it needs, natural carriers
## first, then players in a role the trait asks for, then its stat; in the
## synergy's line for a line synergy. Deterministic.
static func _pick_carriers(key: String, ground: Array) -> Array:
	var s: Dictionary = Traits.SYNERGIES[key]
	var line := str(s["line"])
	var out := []
	for t in s["needs"]:
		var d: Dictionary = Traits.DEFS[t]
		var pool := []
		for p in ground:
			if line != "" and str(p.get("role", "")) != line:
				continue
			if out.has(str(p["id"])):
				continue
			var score := float((p.get("attr", {}) as Dictionary).get(str(d["stat"]), 0))
			if (d["roles"] as Array).is_empty() or (d["roles"] as Array).has(str(p.get("role", ""))):
				score += 1000.0
			if Traits.of(p).has(t):
				score += 10000.0
			pool.append([score, str(p["id"])])
		pool.sort_custom(func(x, y): return float(x[0]) > float(y[0]) or (float(x[0]) == float(y[0]) and str(x[1]) < str(y[1])))
		for i in range(mini(int(s["needs"][t]), pool.size())):
			out.append(pool[i][1])
	return out


# --- activation -------------------------------------------------------------

## Traits.of without the five cap: every good trait whose line he clears.
static func _uncapped(p: Dictionary) -> Array:
	var attr: Dictionary = p.get("attr", {})
	var roles := [str(p.get("role", "")), str(p.get("list_tag", ""))] + Traits._positions(p)
	var out := []
	for key in Traits.DEFS:
		var d: Dictionary = Traits.DEFS[key]
		if d.has("max"):
			continue
		var need_roles: Array = d["roles"]
		if not need_roles.is_empty():
			var ok := false
			for r in ([str(p.get("role", ""))] if bool(d.get("own_role", false)) else roles):
				if need_roles.has(r):
					ok = true
			if not ok:
				continue
		if int(attr.get(str(d["stat"]), 0)) < int(d["min"]):
			continue
		if bool(d.get("small", false)) and int(attr.get("marking", 0)) >= 52:
			continue
		out.append(key)
	return out


static func _active_uncapped(ground: Array) -> Array:
	var counts := {"": {}, "RUCK": {}, "MID": {}, "DEF": {}, "FWD": {}}
	for p in ground:
		var line := str(p.get("role", "MID"))
		for t in _uncapped(p):
			counts[""][t] = int(counts[""].get(t, 0)) + 1
			if counts.has(line):
				counts[line][t] = int(counts[line].get(t, 0)) + 1
	var out := []
	for key in Traits.SYNERGIES:
		var s: Dictionary = Traits.SYNERGIES[key]
		var ok := true
		for t in s["needs"]:
			if int((counts[str(s["line"])] as Dictionary).get(t, 0)) < int(s["needs"][t]):
				ok = false
		if ok:
			out.append(key)
	return out


func _act_block(label: String, entries: Array, per_club: bool) -> void:
	var n := 0
	var on := {}
	var short := {}
	var capped := {}
	var lost := {}   # trait -> carriers in the 18 who clear it but lose it to the cap
	var hist := [0, 0, 0, 0]
	for k in Traits.SYNERGIES:
		on[k] = 0
		short[k] = 0
		capped[k] = 0
	for e in entries:
		var lists: Dictionary = e[1]
		for c in lb.clubs():
			var ground: Array = Squad.new(str(c), lists[c], true, str(c)).ground
			n += 1
			var act := Traits.active(ground)
			var unc := _active_uncapped(ground)
			hist[mini(3, act.size())] += 1
			for k in act:
				on[k] += 1
			for k in unc:
				if not act.has(k):
					capped[k] += 1
			for row in Traits.progress(ground):
				if int(row["missing"]) == 1:
					short[row["key"]] += 1
			for p in ground:
				var have := Traits.of(p)
				for t in _uncapped(p):
					if not have.has(t):
						lost[t] = int(lost.get(t, 0)) + 1
			if per_club:
				var names := []
				for k in act:
					names.append(Traits.label(k))
				print("CLUB %s | %s" % [c, ", ".join(names) if not names.is_empty() else "-"])
	print("")
	print("### Activation, %s (%d club sides)" % [label, n])
	print("| synergy | on | one short | off only because of the 5-trait cap |")
	print("|---|---|---|---|")
	for k in Traits.SYNERGIES:
		print("| %s | %.1f%% | %.1f%% | %.1f%% |" % [Traits.label(k), 100.0 * on[k] / n, 100.0 * short[k] / n, 100.0 * capped[k] / n])
	print("synergies on per club 0/1/2/3+: %s" % str(hist))
	print("traits lost to the cap per club (on-ground 18): %s" % _per(lost, n))


func _per(d: Dictionary, n: int) -> String:
	var out := []
	for t in d:
		out.append("%s %.2f" % [t, float(d[t]) / n])
	return ", ".join(out)


func _act() -> void:
	_act_block("real 2026 lists", [[0, lb.real_lists()]], true)
	var drafted := []
	for d in DRAFTS:
		drafted.append([d, lb.drafted_lists(int(d))["lists"]])
	_act_block("drafted leagues %s" % str(DRAFTS), drafted, false)


# --- effect -----------------------------------------------------------------

func _play(lists: Dictionary, a: String, b: String, seed: int, key: String, on: bool) -> Dictionary:
	var keys := key.split(",")
	var sim := CarrierSim.new(Squad.new(a, lists[a], true, a), Squad.new(b, lists[b], false, b), seed)
	var by_carriers := OS.get_environment("SYN_FORCE") != "always"
	for k in keys:
		if on and by_carriers:
			sim.carriers[k] = _pick_carriers(k, (sim.squads[0] as Squad).ground)
		else:
			sim.synergy_forced[0][k] = on
	sim._refresh_synergies(0, false)
	var r := sim.run()
	var share := 0.0
	for k in keys:
		share += float((r.get("synergy_share", [{}, {}])[0] as Dictionary).get(k, 0.0))
	r["_on_share"] = share / keys.size()
	return r


static func _f(d: Dictionary, k: String) -> float:
	return float(d.get(k, 0.0))


static func _ratio(a: float, b: float) -> float:
	return a / b if b > 0.0 else 0.0


## Per-match metrics, side 0's view.
static func _metrics(r: Dictionary) -> Dictionary:
	var t0: Dictionary = r["team"][0]
	var t1: Dictionary = r["team"][1]
	var g0 := float(r["goals"][0])
	var g1 := float(r["goals"][1])
	var b0 := float(r["behinds"][0])
	var b1 := float(r["behinds"][1])
	var m := float(int(r["score"][0]) - int(r["score"][1]))
	var q4 := float(6 * int(r["q_goals"][3][0]) + int(r["q_behinds"][3][0]) - 6 * int(r["q_goals"][3][1]) - int(r["q_behinds"][3][1]))
	var h1 := 0.0
	for q in range(2):
		h1 += float(6 * int(r["q_goals"][q][0]) + int(r["q_behinds"][q][0]) - 6 * int(r["q_goals"][q][1]) - int(r["q_behinds"][q][1]))
	return {
		"margin": m,
		"win": 1.0 if m > 0 else (0.5 if m == 0 else 0.0),
		"first_half_margin": h1,
		"q4_margin": q4,
		"score_us": float(r["score"][0]),
		"score_them": float(r["score"][1]),
		"clearance_share": _ratio(_f(t0, "clearances"), _f(t0, "clearances") + _f(t1, "clearances")),
		"clearances_us": _f(t0, "clearances"),
		"cp_share": _ratio(_f(t0, "contested_possessions"), _f(t0, "contested_possessions") + _f(t1, "contested_possessions")),
		"disposal_share": _ratio(_f(t0, "disposals"), _f(t0, "disposals") + _f(t1, "disposals")),
		"metres_per_disp_us": _ratio(_f(t0, "metres_gained"), _f(t0, "disposals")),
		"metres_us": _f(t0, "metres_gained"),
		"i50_us": _f(t0, "inside50"),
		"i50_them": _f(t1, "inside50"),
		"acc_us": _ratio(g0, g0 + b0),
		"acc_them": _ratio(g1, g1 + b1),
		"goals_per_i50_us": _ratio(g0, _f(t0, "inside50")),
		"goals_per_i50_them": _ratio(g1, _f(t1, "inside50")),
		"goals_us": g0,
		"goals_them": g1,
		"shots_us": g0 + b0,
		"shots_them": g1 + b1,
		"pressure_rating_us": float(MatchSim.pressure_rating(t0, t1)),
		"pressure_acts_us": _f(t0, "pressure_acts"),
		"tackles_us": _f(t0, "tackles"),
		"intercepts_us": _f(t0, "intercepts"),
		"clangers_them": _f(t1, "clangers"),
		"eff_disp_them": _ratio(_f(t1, "effective_disposals"), _f(t1, "disposals")),
		"disposals_them": _f(t1, "disposals"),
		"distance_us": _f(t0, "distance_run"),
		"q4_legs_us": float((r.get("q4_legs", [0.0, 0.0]) as Array)[0]),
		"q4_legs_them": float((r.get("q4_legs", [0.0, 0.0]) as Array)[1]),
		"interchanges_us": float((r.get("interchanges", [0, 0]) as Array)[0]),
		"on_share": float(r.get("_on_share", 0.0)),
	}


func _eff(key: String) -> void:
	for k in key.split(","):
		if not Traits.SYNERGIES.has(k):
			print("SYN_ON must be one of %s" % str(Traits.SYNERGIES.keys()))
			return
	var leagues := []
	if OS.get_environment("B5_LISTS") == "drafted":
		for d in DRAFTS:
			leagues.append([int(d), lb.drafted_lists(int(d))["lists"]])
	else:
		leagues.append([7, lb.real_lists()])
	var diffs := {}
	var base := {}
	var n := 0
	var natural_on := 0
	for lg in leagues:
		var d: int = lg[0]
		var lists: Dictionary = lg[1]
		var codes: Array = lb.clubs()
		var ratings: Dictionary = lb.club_ratings(lists, codes)
		codes.sort_custom(func(x, y): return float(ratings[x]["strength"]) > float(ratings[y]["strength"]))
		for i in range(0, codes.size() - 1, 2):
			for flip in [false, true]:
				var a := str(codes[i + (1 if flip else 0)])
				var b := str(codes[i + (0 if flip else 1)])
				if Traits.active(Squad.new(a, lists[a], true, a).ground).has(key.split(",")[0]):
					natural_on += 1
				for k in range(REPS):
					var seed: int = d * 100003 + i * 1009 + k * 7919 + (31 if flip else 0)
					var mo := _metrics(_play(lists, a, b, seed, key, false))
					var mn := _metrics(_play(lists, a, b, seed, key, true))
					n += 1
					for s in mo:
						if not diffs.has(s):
							diffs[s] = []
							base[s] = 0.0
						diffs[s].append(float(mn[s]) - float(mo[s]))
						base[s] += float(mo[s])
		print("league %d done" % d)
	print("")
	var force := OS.get_environment("SYN_FORCE") if OS.get_environment("SYN_FORCE") != "" else "carriers"
	print("## %s forced on (%s) for side 0: %d paired matches (off vs on, same seed); side 0 had it naturally in %d of %d pairings" % [
			key, force, n, natural_on, leagues.size() * 18])
	print("| metric | off (mean) | on - off | SE | relative |")
	print("|---|---|---|---|---|")
	for s in diffs:
		var mu := _mean(diffs[s])
		var b := float(base[s]) / n
		print("| %s | %.4f | %+.4f | %.4f | %s |" % [s, b, mu, _se(diffs[s]),
				("%+.1f%%" % (100.0 * mu / b)) if absf(b) > 1e-6 else "-"])


## Natural play: each club against its neighbour in strength, SYN_REPS seeds,
## real lists and the drafted leagues; for each side with a synergy on at the
## first bounce, the share of the match's chains it stayed on.
func _share() -> void:
	var leagues := [[7, lb.real_lists()]]
	for d in DRAFTS:
		leagues.append([int(d), lb.drafted_lists(int(d))["lists"]])
	var shares := {}
	var full := {}
	for lg in leagues:
		var lists: Dictionary = lg[1]
		var codes: Array = lb.clubs()
		var ratings: Dictionary = lb.club_ratings(lists, codes)
		codes.sort_custom(func(x, y): return float(ratings[x]["strength"]) > float(ratings[y]["strength"]))
		for i in range(0, codes.size() - 1, 2):
			var a := str(codes[i])
			var b := str(codes[i + 1])
			for k in range(REPS):
				var seed: int = int(lg[0]) * 100003 + i * 1009 + k * 7919
				var sim := MatchSim.new(Squad.new(a, lists[a], true, a), Squad.new(b, lists[b], false, b), seed)
				var start := [(sim.synergies[0] as Array).duplicate(), (sim.synergies[1] as Array).duplicate()]
				var r := sim.run()
				for side in 2:
					for key in start[side]:
						var sh := float((r["synergy_share"][side] as Dictionary).get(key, 0.0))
						if not shares.has(key):
							shares[key] = []
							full[key] = 0
						shares[key].append(sh)
						if sh >= 0.999:
							full[key] += 1
		print("league %d done" % int(lg[0]))
	print("")
	print("## Natural on-share of the match, sides with the synergy on at the first bounce")
	print("| synergy | sides | on-share mean | SE | on all match |")
	print("|---|---|---|---|---|")
	for key in Traits.SYNERGIES:
		if not shares.has(key):
			print("| %s | 0 | - | - | - |" % Traits.label(key))
			continue
		print("| %s | %d | %.3f | %.3f | %.1f%% |" % [Traits.label(key), shares[key].size(), _mean(shares[key]),
				_se(shares[key]), 100.0 * full[key] / shares[key].size()])


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
