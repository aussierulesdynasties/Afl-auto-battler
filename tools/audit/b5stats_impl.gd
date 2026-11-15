extends RefCounted
## Bug bash 5, player stats: what one attribute is worth in a match. Paired
## seeded matches between real 2026 lists; arm "base" plays them as they are,
## every other arm plays the same matches with one attribute raised by DELTA
## (capped at 99) for every player on the HOME list. Selection is unchanged
## (OVR is not re-rated), so the arm differs only in that attribute. With
## B5_TRAITS=frozen (default) each player's traits are fixed at his unboosted
## ones, so a trait threshold crossed by the boost does not muddy the number.
## Prints per arm: B-A margin (home minus away points) with its SE, home win
## share B-A, the home side's mean OVR change from the same boost (Ratings
## formula), and B-A of the team stats the attribute should move.
## Env: B5_N (matches, default 300), B5_ARMS (comma list, default all 13),
## B5_DELTA (default 10), B5_TRAITS frozen|follow, AUDIT_SEED (default 9100).
## Arm "all" raises every attribute.

const CLUBS := ["GEE", "COL", "CAR", "SYD", "MEL", "BRL", "HAW", "ESS", "GWS", "FRE", "ADE", "PAD",
		"WBD", "STK", "RIC", "NTH", "WCE", "GCS"]
const ATTRS := ["disposal", "contested", "marking", "pressure", "intercept", "carry", "goalkicking",
		"accuracy", "creating", "ruck", "discipline", "durability", "star"]
const KEYS := ["goals", "behinds", "shots", "inside50", "clearances", "hitouts", "hitouts_adv", "tackles",
		"pressure_acts", "marks", "contested_marks", "intercept_marks", "intercepts", "rebounds", "one_percenters",
		"spoils", "clangers", "frees_for", "frees_against", "disposals", "effective_disposals",
		"contested_possessions", "metres_gained", "goal_assists", "running_bounces", "smothers"]
const OPP_KEYS := ["goals", "inside50", "shots", "clangers", "frees_for", "frees_against", "tackles"]


func _copy(list: Array) -> Array:
	var out := []
	for p in list:
		out.append((p as Dictionary).duplicate(true))
	return out


## An arm is "attr", "all", or "ROLE:attr" (only players whose role is ROLE).
func _boost(list: Array, arm: String, delta: int) -> void:
	var role := ""
	var key := arm
	if arm.contains(":"):
		role = arm.get_slice(":", 0)
		key = arm.get_slice(":", 1)
	for p in list:
		if role != "" and str(p.get("role", "")) != role:
			continue
		var a: Dictionary = p["attr"]
		for k in ATTRS:
			if key == "all" or key == k:
				a[k] = clampi(int(a.get(k, 50)) + delta, 1, 99)


func _play(h: String, a: String, seed: int, arm: String, delta: int, frozen: bool) -> Dictionary:
	var hl := _copy(GameDB.club_list(h))
	var al := _copy(GameDB.club_list(a))
	var traits := {}
	if frozen:
		for p in hl + al:
			traits[str(p["id"])] = Traits.of(p)
	var ovr_d := 0.0
	var applied := 0.0
	var n := 0
	var base_attr := {}
	for p in hl:
		base_attr[str(p["id"])] = (p["attr"] as Dictionary).duplicate()
	if arm != "base":
		_boost(hl, arm, delta)
	var hs := Squad.new(h, hl, true, h)
	var as_ := Squad.new(a, al, false, a)
	for p in hs.ground + hs.bench:
		var old: Dictionary = base_attr[str(p["id"])]
		var role := str(p["role"])
		var gm := float(p.get("gm", 14.0))
		ovr_d += float(Ratings.rate_overall(p["attr"], role, gm) - Ratings.rate_overall(old, role, gm))
		for k in ATTRS:
			applied += float(int(p["attr"][k]) - int(old[k]))
		n += 1
	var sim := MatchSim.new(hs, as_, seed)
	if frozen:
		for id in traits:
			sim._traits[id] = traits[id]
	var r: Dictionary = sim.run()
	var t0: Dictionary = r["team"][0]
	var t1: Dictionary = r["team"][1]
	var out := {"margin": float(int(r["score"][0]) - int(r["score"][1])),
			"win": 1.0 if int(r["score"][0]) > int(r["score"][1]) else (0.5 if int(r["score"][0]) == int(r["score"][1]) else 0.0),
			"ovr_d": ovr_d / maxf(1.0, float(n)), "applied": applied / maxf(1.0, float(n))}
	for k in KEYS:
		out[k] = float(t0.get(k, 0.0))
	for k in OPP_KEYS:
		out["opp_" + k] = float(t1.get(k, 0.0))
	var inj := 0.0
	for ev in r.get("events", []):
		if str(ev.get("kind", "")) == "injury" and int(ev.get("side", -1)) == 0:
			inj += 1.0
	out["injuries"] = inj
	return out


func run() -> void:
	var n := int(OS.get_environment("B5_N")) if OS.get_environment("B5_N") != "" else 300
	var delta := int(OS.get_environment("B5_DELTA")) if OS.get_environment("B5_DELTA") != "" else 10
	var frozen := OS.get_environment("B5_TRAITS") != "follow"
	var arms: Array = ATTRS.duplicate()
	if OS.get_environment("B5_ARMS") != "":
		arms = Array(OS.get_environment("B5_ARMS").split(","))
	var base_seed := int(OS.get_environment("AUDIT_SEED")) if OS.get_environment("AUDIT_SEED") != "" else 9100
	var all_keys: Array = ["margin", "win", "injuries"] + KEYS
	for k in OPP_KEYS:
		all_keys.append("opp_" + k)
	# sums per arm: diff sum, diff sq sum; base sums
	var d_sum := {}
	var d_sq := {}
	var b_sum := {}
	var ovr := {}
	var applied := {}
	for arm in arms:
		d_sum[arm] = {}
		d_sq[arm] = {}
		ovr[arm] = 0.0
		applied[arm] = 0.0
	var t0 := Time.get_ticks_msec()
	for i in range(n):
		var h: String = CLUBS[i % CLUBS.size()]
		var a: String = CLUBS[(i * 7 + 5) % CLUBS.size()]
		if a == h:
			a = CLUBS[(i + 1) % CLUBS.size()]
		var seed := base_seed + i
		var b := _play(h, a, seed, "base", delta, frozen)
		for k in all_keys:
			b_sum[k] = float(b_sum.get(k, 0.0)) + float(b[k])
		for arm in arms:
			var x := _play(h, a, seed, arm, delta, frozen)
			ovr[arm] = float(ovr[arm]) + float(x["ovr_d"])
			applied[arm] = float(applied[arm]) + float(x["applied"])
			for k in all_keys:
				var d := float(x[k]) - float(b[k])
				d_sum[arm][k] = float(d_sum[arm].get(k, 0.0)) + d
				d_sq[arm][k] = float(d_sq[arm].get(k, 0.0)) + d * d
		if i == 0:
			print("B5 TIMING first match set %d ms (%d arms)" % [Time.get_ticks_msec() - t0, arms.size() + 1])
	var fn := float(n)
	print("B5 N %d DELTA %d TRAITS %s SEED %d" % [n, delta, "frozen" if frozen else "follow", base_seed])
	var bl := "B5 BASE"
	for k in all_keys:
		bl += " %s=%.2f" % [k, float(b_sum[k]) / fn]
	print(bl)
	for arm in arms:
		var line := "B5 ARM %s ovr_d=%.2f applied=%.2f" % [arm, float(ovr[arm]) / fn, float(applied[arm]) / fn]
		for k in all_keys:
			var m := float(d_sum[arm][k]) / fn
			var var_ := maxf(0.0, float(d_sq[arm][k]) / fn - m * m)
			var se := sqrt(var_ / maxf(1.0, fn - 1.0))
			line += " %s=%.3f±%.3f" % [k, m, se]
		print(line)
	print("B5 DONE %d ms" % (Time.get_ticks_msec() - t0))
