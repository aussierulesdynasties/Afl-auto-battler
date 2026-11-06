extends RefCounted
## Kick range (row 10, director 2026-11-03): a kick's receiver must be within
## the kicker's reach (MatchSim.kick_range), better kickers reach further, and
## every match path (watched, Sim the week, AI v AI) picks the receiver through
## the one MatchSim.kick_receiver. Run through tests/run_kick_range_tests.gd.
## Seeded by design: every sim takes an explicit match seed.

var failures: Array[String] = []
var checks := 0

const CLUBS := [["FRE", "MEL"], ["GEE", "COL"], ["SYD", "CAR"], ["BRL", "ESS"]]
const SEEDS := 6


func run() -> void:
	failures.clear()
	checks = 0
	GameDB.reload()
	_t("_test_out_of_range_never_chosen")
	_t("_test_longer_kicker_reaches_further")
	_t("_test_no_one_in_range_falls_back")
	_t("_test_paths_pick_the_same_receiver")
	_t("_test_scores_stay_realistic")
	print(Ran.line("Kick range", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _sim(home: String, away: String, seed: int) -> MatchSim:
	return MatchSim.new(Squad.new(home, GameDB.club_list(home), true, home),
			Squad.new(away, GameDB.club_list(away), false, away), seed)


## A copy of an on-ground player of `role` with his kicking rating set.
func _kicker(sim: MatchSim, role: String, disposal: float) -> Dictionary:
	for p in (sim.squads[0] as Squad).ground:
		if str(p["role"]) == role:
			var k: Dictionary = p.duplicate(true)
			k["attr"]["disposal"] = disposal
			return k
	return {}


func _roles(pool: Array) -> Array:
	var out := []
	for p in pool:
		out.append(str(p["role"]))
	return out


func _test_out_of_range_never_chosen() -> void:
	var sim := _sim("FRE", "MEL", 11)
	var k := _kicker(sim, "DEF", 40.0)   # reach 44 m
	# Deep in his back pocket (70 m from the centre): forwards at half-forward
	# are 120 m away.
	_check(not _roles(sim.kick_targets(0, -70.0, k)).has("FWD"),
			"a forward 120 m away is offered to a 44 m kicker")
	for i in range(400):
		var r = sim.kick_receiver(0, -70.0, -55.0, k)
		var d := absf(float(MatchSim.LINE_HOME[str(r["role"])]) - (-70.0))
		_check(d <= MatchSim.kick_range(k), "receiver %s %.0f m away, reach %.0f" % [r["role"], d, MatchSim.kick_range(k)])
		_check(str(r["id"]) != str(k["id"]), "the kicker received his own kick")
		if failures.size() > 0:
			return
	# The away side kicks the other way: same rule mirrored.
	var k1: Dictionary = (sim.squads[1] as Squad).ground[0].duplicate(true)
	k1["role"] = "DEF"
	k1["attr"]["disposal"] = 40.0
	_check(not _roles(sim.kick_targets(1, 70.0, k1)).has("FWD"), "mirrored: away forward offered out of range")


func _test_longer_kicker_reaches_further() -> void:
	var sim := _sim("GEE", "COL", 12)
	_check(MatchSim.kick_range(_kicker(sim, "MID", 90.0)) > MatchSim.kick_range(_kicker(sim, "MID", 40.0)),
			"a 90 kicker does not out-reach a 40 kicker")
	# 5 m inside his own half: forwards are 55 m away.
	var weak := sim.kick_targets(0, -5.0, _kicker(sim, "MID", 40.0))   # 44 m
	var strong := sim.kick_targets(0, -5.0, _kicker(sim, "MID", 90.0))  # 61.5 m
	_check(not _roles(weak).has("FWD"), "a 44 m kicker reaches forwards 55 m away")
	_check(_roles(strong).has("FWD"), "a 61.5 m kicker cannot reach forwards 55 m away")
	_check(strong.size() > weak.size(), "the longer kicker has no more targets (%d v %d)" % [strong.size(), weak.size()])


func _test_no_one_in_range_falls_back() -> void:
	var sim := _sim("SYD", "CAR", 13)
	var k := _kicker(sim, "MID", 0.0)   # 30 m reach
	k["role"] = "DEF"
	# 85 m out: every line home is beyond 30 m; the nearest (defenders) is the option.
	var pool := sim.kick_targets(0, -85.0, k)
	_check(pool.size() == 1, "no one in range should leave exactly the nearest teammate, got %d" % pool.size())
	_check(pool.size() == 1 and str(pool[0]["role"]) == "DEF", "fallback is not the nearest teammate")
	_check(sim.kick_receiver(0, -85.0, -80.0, k) != null, "no receiver when nobody is in range")


## The watched match (GameState.pending_sim) and Sim the week / AI v AI
## (Season.match_sim) are both a MatchSim; given the same state and seed the
## one kick_receiver gives the same receiver, and whole matches play the same.
func _test_paths_pick_the_same_receiver() -> void:
	var watched := _sim("BRL", "ESS", 77)
	var simmed := _sim("BRL", "ESS", 77)
	var k := _kicker(watched, "MID", 65.0)
	for i in range(200):
		var fp := -60.0 + float(i % 12) * 10.0
		var a = watched.kick_receiver(0, fp, fp + 15.0, k)
		var b = simmed.kick_receiver(0, fp, fp + 15.0, k)
		_check(str(a["id"]) == str(b["id"]), "paths differ at pick %d" % i)
		if failures.size() > 0:
			return
	var ra := _sim("BRL", "ESS", 78).run()
	var rb := _sim("BRL", "ESS", 78).run()
	var ea: Array = ra["events"]
	var eb: Array = rb["events"]
	_check(ea.size() == eb.size(), "same seed, different event counts")
	var same := true
	for i in range(mini(ea.size(), eb.size())):
		if str(ea[i].get("player_id", "")) != str(eb[i].get("player_id", "")):
			same = false
			break
	_check(same, "same seed, different actors")


## Realistic AFL scores; prints the average.
func _test_scores_stay_realistic() -> void:
	var total := 0.0
	var n := 0
	for pair in CLUBS:
		for s in range(SEEDS):
			var res := _sim(pair[0], pair[1], 500 + s).run()
			for side in range(2):
				total += float(res["score"][side]) if res.has("score") else 0.0
				n += 1
	var avg := total / float(n)
	print("Kick range: mean team score %.1f (%d team games)" % [avg, CLUBS.size() * SEEDS * 2])
	_check(avg >= 60.0 and avg <= 105.0, "mean team score %.1f outside 60-105" % avg)
