extends RefCounted
## Bug bash 5 (game plans): paired seeded matches, measurement only.
## Env: GP_MODE matrix|levers|fit|ai|wet, GP_SEEDS (per pairing, default 20),
## GP_SHARD/GP_SHARDS (split seeds), GP_ARMS (comma list, optional).
## One R line per match: R|mode|arm|opp|pair|seed|margin|win|gf|bf|ga|ba|clangers|opp_clangers|
## press|opp_press|clr|opp_clr|metres|opp_metres|i50|opp_i50|opp_icm|inj|press_broken|opp_press_broken|q4margin_delta

const PAIRS := [["MEL", "CAR"], ["GEE", "COL"], ["SYD", "WCE"], ["BRL", "ADE"], ["HAW", "ESS"],
		["FRE", "STK"], ["GCS", "GWS"], ["NTH", "RIC"], ["PAD", "WBD"]]
const PLANS5 := ["balanced", "attacking", "defensive", "contest", "controlled"]


func _env(k: String, d: String) -> String:
	var v := OS.get_environment(k)
	return v if v != "" else d


func _play(mode: String, arm: String, opp_plan: String, h: String, a: String, seed_: int) -> String:
	var home := Squad.new(h, GameDB.club_list(h), true, h)
	var away := Squad.new(a, GameDB.club_list(a), false, a)
	if mode == "ai":
		away.ai_plans = true
	var t := {"gameplan": "balanced", "pep": "steady"}
	var custom := {}
	var fit_over := -1.0
	var plan := arm
	if arm.ends_with("_fire"):
		t["pep"] = "fire_up"
		plan = arm.trim_suffix("_fire")
	if plan.begins_with("s:"):
		custom = {"name": "", "s": plan.substr(2), "c": ""}
	elif plan.begins_with("c:"):
		custom = {"name": "", "s": "", "c": plan.substr(2)}
	elif plan.begins_with("sc:"):
		var bits := plan.substr(3).split("+")
		custom = {"name": "", "s": bits[0], "c": bits[1]}
	elif plan.find("@") >= 0:
		fit_over = float(plan.split("@")[1])
		plan = plan.split("@")[0]
		t["gameplan"] = plan
	elif plan != "base":
		t["gameplan"] = plan
	if not custom.is_empty():
		t["gameplan"] = "custom"
	var sim := MatchSim.new(home, away, seed_)
	if mode == "wet":
		sim.weather = "wet"
	if not custom.is_empty():
		sim.custom[0] = custom
	if fit_over > 0.0:
		(sim.plan_fit[0] as Dictionary)[plan] = fit_over
	sim.set_tactics(0, t)
	if mode != "ai":
		sim.set_tactics(1, {"gameplan": opp_plan, "pep": "steady"})
	if seed_ == 5100 and h == "MEL" and not custom.is_empty():
		var lv := []
		for k in ["goal", "opp_goal", "clangers", "stoppage", "mid_press", "legs", "reach", "fwd_turnover", "momentum", "pep", "gain", "broken", "inj", "icept"]:
			lv.append("%s=%.3f" % [k, sim._gt(0, k, 0.0 if k == "stoppage" else 1.0)])
		print("GT|%s|%s" % [arm, " ".join(lv)])
	var res: Dictionary = sim.run()
	var sc: Array = res["score"]
	var g: Array = res["goals"]
	var b: Array = res["behinds"]
	var t0: Dictionary = (res["team"] as Array)[0]
	var t1: Dictionary = (res["team"] as Array)[1]
	var inj := 0
	for i in res["injuries"]:
		if int((i as Dictionary).get("side", -1)) == 0:
			inj += 1
	var m := int(sc[0]) - int(sc[1])
	var q: Array = res["quarters"]
	var q4 := 0
	if q.size() >= 4:
		q4 = int(q[3][0]) - int(q[3][1])
	var win := 1.0 if m > 0 else (0.5 if m == 0 else 0.0)
	return "R|%s|%s|%s|%s|%d|%d|%.1f|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d" % [mode, arm, opp_plan,
			h, seed_, m, win, int(g[0]), int(b[0]), int(g[1]), int(b[1]),
			int(t0.get("clangers", 0)), int(t1.get("clangers", 0)),
			int(t0.get("pressure_acts", 0)), int(t1.get("pressure_acts", 0)),
			int(t0.get("clearances", 0)), int(t1.get("clearances", 0)),
			int(t0.get("metres_gained", 0)), int(t1.get("metres_gained", 0)),
			int(t0.get("inside50", 0)), int(t1.get("inside50", 0)),
			int(t1.get("intercept_marks", 0)), inj,
			int(t0.get("press_broken", 0)), int(t1.get("press_broken", 0)), q4]


func run() -> void:
	var mode := _env("GP_MODE", "matrix")
	var seeds := int(_env("GP_SEEDS", "20"))
	var shard := int(_env("GP_SHARD", "0"))
	var shards := int(_env("GP_SHARDS", "1"))
	var arms: Array = []
	var opps: Array = ["balanced"]
	match mode:
		"matrix", "wet":
			arms = PLANS5.duplicate()
			opps = PLANS5.duplicate()
		"ai":
			arms = PLANS5.duplicate()
			opps = ["ai"]
		"levers":
			arms = ["base"]
			for s in CustomPlan.STRENGTH_IDS:
				arms.append("s:" + str(s))
			for c in CustomPlan.COST_IDS:
				arms.append("c:" + str(c))
			arms += ["base_fire", "s:comeback_fire", "c:flat_fire"]
		"fit":
			arms = ["base"]
			for p in ["attacking", "defensive", "contest", "controlled"]:
				for f in [0.45, 1.0, 1.55]:
					arms.append("%s@%s" % [p, str(f)])
	var only := _env("GP_ARMS", "")
	if only != "":
		arms = Array(only.split(","))
	if mode == "fit" or mode == "matrix":
		for pr in PAIRS:
			for c in pr:
				var sq := Squad.new(c, GameDB.club_list(c), true, c)
				var parts := []
				for p in PlanFit.LEAGUE:
					parts.append("%s=%.3f" % [p, PlanFit.fit(sq.ground, p)])
				print("FIT|%s|%s|standing=%s" % [c, "|".join(parts), PlanFit.standing_plan(sq.ground)])
	var t0 := Time.get_ticks_msec()
	var n := 0
	for pr in PAIRS:
		for s in range(seeds):
			if s % shards != shard:
				continue
			for o in opps:
				for arm in arms:
					print(_play(mode, str(arm), str(o), pr[0], pr[1], 5100 + s))
					n += 1
	print("DONE|%d matches|%.1f s" % [n, (Time.get_ticks_msec() - t0) / 1000.0])
