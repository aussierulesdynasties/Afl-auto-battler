extends RefCounted
## P-79 "no plan wins everywhere" (T8.87): every game plan against every other,
## and against a side coached the way the AI coaches, across weak, even and
## strong lists. Measurement only: no rule changes.
##
## The 2027 clubs are ranked by Squad.strength at the start of a career: the top
## four are the strong lists, the middle four the even ones and the bottom four
## the weak ones. A fixture spot is two tiers (WW, EE, SS, WE, WS, ES). Side A
## comes from the first tier, side B from the second. Every plan pairing in a
## spot plays the same seeds, the same club pairs and the same home sides, so
## the plan is the only thing that moves.
##
## A fixed plan is held all match (ai_plans off) with the same loose interceptor
## the AI would start. "ai" is an AI-coached side (ai_plans on: its usual plan,
## changed at the breaks from the score and what it has seen, match-ups re-set).
## The weather is whatever MatchSim gives by default, plan_know is empty and
## tactics_exec 1.0: a plan is fully known and executed as written.
##
## Args after the impl name: spot matches seed_base
##   spot        WW, EE, SS, WE, WS or ES (default EE)
##   matches     per plan pairing (default 144)
##   seed_base   default 7000
## One RR line per match, for tools/audit/plan_rr_agg.py:
##   RR spot planA planB clubA clubB A_home seed margin_A
## godot --headless --path . --script tools/audit/run_audit.gd -- plan_rr_impl EE 144 7000

const PLANS := ["balanced", "attacking", "defensive", "contest", "controlled", "ai"]
const FIT_PLANS := ["attacking", "defensive", "contest", "controlled"]
const TIER_SIZE := 4


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var spot := str(args[1]) if args.size() > 1 else "EE"
	var matches := int(args[2]) if args.size() > 2 else 144
	var seed_base := int(args[3]) if args.size() > 3 else 7000
	var tiers := _tiers()
	for t in tiers:
		for code in tiers[t]:
			_print_club(str(t), str(code))
	var a_clubs: Array = tiers[spot.substr(0, 1)]
	var b_clubs: Array = tiers[spot.substr(1, 1)]
	var pairs := []
	for a in a_clubs:
		for b in b_clubs:
			if a != b:
				pairs.append([str(a), str(b)])
	var started := Time.get_ticks_msec()
	var played := 0
	for x in PLANS:
		for y in PLANS:
			for i in range(matches):
				var pair: Array = pairs[i % pairs.size()]
				var a_home := (i / pairs.size()) % 2 == 0
				var seed := seed_base + i
				var margin := _margin(str(pair[0]), str(pair[1]), a_home, str(x), str(y), seed)
				print("RR %s %s %s %s %s %d %d %d" % [spot, x, y, pair[0], pair[1], 1 if a_home else 0, seed, margin])
				played += 1
		print("PROGRESS %s plan %s done, %d matches, %d s" % [spot, x, played, (Time.get_ticks_msec() - started) / 1000])
	print("SUMMARY plan_rr spot %s | %d matches | %d per pairing | seed base %d | %d s" % [
			spot, played, matches, seed_base, (Time.get_ticks_msec() - started) / 1000])


## tier letter -> club codes, by the side's strength at the start of a career.
func _tiers() -> Dictionary:
	var codes: Array = GameDB.active_clubs(2027).duplicate()
	codes = codes.filter(func(c): return not GameDB.club_list(str(c)).is_empty())
	var strength := {}
	for c in codes:
		strength[c] = Squad.new(str(c), GameDB.club_list(str(c)), true, str(c)).strength()
	codes.sort_custom(func(a, b): return float(strength[a]) > float(strength[b]))
	for i in codes.size():
		print("RANK %d %s %.1f" % [i + 1, codes[i], float(strength[codes[i]])])
	var mid := (codes.size() - TIER_SIZE) / 2
	return {"S": codes.slice(0, TIER_SIZE), "E": codes.slice(mid, mid + TIER_SIZE),
			"W": codes.slice(codes.size() - TIER_SIZE)}


func _print_club(tier: String, code: String) -> void:
	var sq := Squad.new(code, GameDB.club_list(code), true, code)
	var bits := PackedStringArray()
	for plan in FIT_PLANS:
		bits.append("%s %.2f" % [plan, PlanFit.fit(sq.ground, str(plan))])
	print("TIER %s %s strength %.1f | fit %s" % [tier, code, sq.strength(), ", ".join(bits)])


## Side A's margin (points) with plan x, against side B with plan y.
func _margin(a: String, b: String, a_home: bool, x: String, y: String, seed: int) -> int:
	var sa := Squad.new(a, GameDB.club_list(a), a_home, a)
	var sb := Squad.new(b, GameDB.club_list(b), not a_home, b)
	var home: Squad = sa if a_home else sb
	var away: Squad = sb if a_home else sa
	var home_plan := x if a_home else y
	var away_plan := y if a_home else x
	home.ai_plans = home_plan == "ai"
	away.ai_plans = away_plan == "ai"
	var sim := MatchSim.new(home, away, seed)
	_fix(sim, 0, home_plan)
	_fix(sim, 1, away_plan)
	var res: Dictionary = sim.run()
	var sc: Array = res["score"]
	var m := int(sc[0]) - int(sc[1])
	return m if a_home else -m


func _fix(sim: MatchSim, side: int, plan: String) -> void:
	if plan == "ai":
		return
	sim.set_tactics(side, {"gameplan": plan, "pep": "steady"})
	var best: Dictionary = sim.loose_pick((sim.squads[side] as Squad).ground, (sim.squads[1 - side] as Squad).ground)
	if not best.is_empty():
		sim.set_interceptor(side, str(best["id"]), false)
