extends RefCounted
## Believable comebacks (row 42): the last-quarter margin swing, measured. Measurement only; no
## balance is changed.
##   godot --headless --path . --script tools/audit/run_audit.gd -- comeback_impl <mode> <seed0> <n> [arms]
## mode  ai     both clubs are AI coaches (the league's matches)
##       coach  side 0 is a coach who never changes a call (balanced, steady) and then skips Q4, the
##              way the tester did; side 1 is the AI club. Moments are off (skip takes the default).
## seed0 batch number: match i uses seed seed0 * 100000 + i, pairing and weather from seed0 alone, so
##       the same (seed0, n) is the same set of matches in every arm and in every run.
## arms  comma list of Q4 variants, default base,nomom,fresh,frozen,none. Q1-Q3 are replayed from the
##       same seed in every arm, so every arm starts Q4 from the identical three-quarter-time state;
##       only Q4 changes (its dice then differ, so a paired difference is state-paired, not
##       dice-paired).
##         base    the game as it is
##         nomom   momentum zeroed at the Q4 bounce and its contest edge set to 0
##         fresh   every player's energy restored to his cap at the Q4 bounce (no fatigue gap)
##         frozen  the AI club keeps its Q3 plan and pep in Q4 (no chase, protect, counter or fire up)
##         none    nomom + fresh + frozen together (what is left is the contest itself)
## Output, one line a match and arm:
##   C|arm|mode|seed|home|away|weather|h1|a1|h2|a2|h3|a3|h4|a4|g4h|g4a|plan4h|plan4a|mom3|eh3|ea3
## (hN/aN = score at the end of quarter N; g4 = goals in Q4; mom3 = momentum at the Q4 bounce, after
## the break halving; eh3/ea3 = mean energy on the ground at the Q4 bounce.)

const WEATHERS := ["perfect", "perfect", "perfect", "perfect", "wet", "windy", "hot"]


func _squad(code: String, home: bool, ai: bool) -> Squad:
	var s := Squad.new(code, GameDB.club_list(code), home, code)
	s.ai_plans = ai
	s.assistant = not ai
	return s


func _mean_energy(sim: MatchSim, side: int) -> float:
	var sum := 0.0
	var n := 0
	for p in (sim.squads[side] as Squad).ground:
		sum += float(sim.energy.get(str(p["id"]), 100.0))
		n += 1
	return sum / maxf(1, n)


func _pair(rng: RandomNumberGenerator, codes: Array) -> Array:
	var a: int = rng.randi() % codes.size()
	var b: int = rng.randi() % (codes.size() - 1)
	if b >= a:
		b += 1
	return [codes[a], codes[b]]


func _apply_coach(sim: MatchSim) -> void:
	var t := {"gameplan": "balanced", "pep": "steady", "rotation": "normal"}
	sim.set_tactics(0, t)
	sim.set_rotation_policy(0, "normal")
	sim.set_tactics(1, sim.ai_tactics(1))


func _plan_str(sim: MatchSim, q: int, side: int) -> String:
	var pl: Dictionary = (sim.tactics_history[q - 1]["plans"] as Array)[side]
	return str(pl.get("gameplan", "")) + "/" + str(pl.get("pep", ""))


func _play(arm: String, mode: String, seed: int, pr: Array, weather: String) -> String:
	var coach := mode == "coach"
	var sim := MatchSim.new(_squad(pr[0], true, not coach), _squad(pr[1], false, true), seed)
	sim.weather = weather
	if coach:
		sim.moment_side = 0
		sim.set_tactics(0, {"gameplan": "balanced"})
	var sc := []
	for q in range(1, 4):
		if coach:
			_apply_coach(sim)
		sim.run_quarter()
		sc.append([sim.score(0), sim.score(1)])
	var nomom := arm == "nomom" or arm == "none"
	var fresh := arm == "fresh" or arm == "none"
	var frozen := arm == "frozen" or arm == "none"
	var q3_ai: Dictionary = ((sim.tactics_history[2]["plans"] as Array)[1] as Dictionary).duplicate()
	if nomom:
		sim.momentum = 0.0
		sim.momentum_edge = 0.0
	if fresh:
		for id in sim.energy:
			sim.energy[id] = float(sim.energy_caps.get(id, 100.0))
	if frozen:
		(sim.squads[1] as Squad).ai_plans = false
		sim.set_tactics(1, q3_ai)
	var mom3 := sim.momentum   # end_quarter has already halved it
	var eh := _mean_energy(sim, 0)
	var ea := _mean_energy(sim, 1)
	if coach:
		# MatchScene._simulate_remaining: the kept call for the coach, the AI club's pick as usual.
		var t := {"gameplan": "balanced", "pep": "steady", "rotation": "normal"}
		sim.set_tactics(0, t)
		sim.set_rotation_policy(0, "normal")
		sim.set_tactics(1, q3_ai if frozen else sim.ai_tactics(1))
	sim.run_quarter()
	return "C|%s|%s|%d|%s|%s|%s|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%s|%s|%.2f|%.1f|%.1f" % [
			arm, mode, seed, pr[0], pr[1], weather,
			sc[0][0], sc[0][1], sc[1][0], sc[1][1], sc[2][0], sc[2][1],
			sim.score(0), sim.score(1), int(sim.q_goals[3][0]), int(sim.q_goals[3][1]),
			_plan_str(sim, 4, 0), _plan_str(sim, 4, 1), mom3, eh, ea]


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := str(args[1])
	var seed0 := int(args[2])
	var n := int(args[3])
	var arms: Array = (str(args[4]) if args.size() > 4 else "base,nomom,fresh,frozen,none").split(",")
	var lb = load("res://tools/balance/league_balance.gd").new()
	var codes: Array = lb.clubs()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed0 * 7919 + 13
	for i in range(n):
		var seed := seed0 * 100000 + i
		var pr := _pair(rng, codes)
		var weather: String = WEATHERS[rng.randi() % WEATHERS.size()]
		for arm in arms:
			print(_play(str(arm), mode, seed, pr, weather))
