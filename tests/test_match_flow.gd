extends RefCounted
## Match flow (row 11, director 2026-10-10): a stoppage comes from a contest
## that locks up, never from a won ball (after an intercept or a free the winner
## plays on), chains are shorter and more numerous, and a ball-up in play is how
## its chain ended. Run through tests/run_match_flow_tests.gd.
## Seeded by design: every sim takes an explicit match seed.

var failures: Array[String] = []
var checks := 0

const CLUBS := [["FRE", "MEL"], ["GEE", "COL"], ["SYD", "CAR"], ["BRL", "ESS"]]
const SEEDS := 5


func run() -> void:
	failures.clear()
	checks = 0
	GameDB.reload()
	_t("_test_won_ball_is_played_on")
	_t("_test_scores_stay_realistic")
	_t("_test_flow_keys_exist_in_calibration")
	_t("_test_tackle_spill_is_a_tuned_lever")
	_t("_test_lockups_make_ball_ups_in_play")
	_t("_test_rushed_kick_intercept_mark")
	_t("_test_rotation_cadence_scales_with_chains")
	MatchSim.tune = {}
	print(Ran.line("Match flow", self))


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


## Plays the sample; returns the chain starts by key
## (MatchSim.audit_chains), the games played and the total points.
func _play() -> Dictionary:
	MatchSim.audit_chains_on = true
	MatchSim.audit_chains = {}
	var games := 0
	var points := 0.0
	for pair in CLUBS:
		for s in range(SEEDS):
			var res := _sim(pair[0], pair[1], 700 + s).run()
			games += 1
			points += float(res["score"][0]) + float(res["score"][1])
	MatchSim.audit_chains_on = false
	var chains: Dictionary = MatchSim.audit_chains.duplicate()
	MatchSim.audit_chains = {}
	return {"chains": chains, "games": games, "points": points}


func _count(chains: Dictionary, prefix: String) -> int:
	var n := 0
	for k in chains:
		if str(k).begins_with(prefix):
			n += int(chains[k])
	return n


func _total(chains: Dictionary) -> int:
	var n := 0
	for k in chains:
		n += int(chains[k])
	return n


func _test_won_ball_is_played_on() -> void:
	var r := _play()
	var ch: Dictionary = r["chains"]
	_check(_total(ch) > 0, "no chains were recorded")
	_check(_count(ch, "stoppage <- turnover") == 0, "a ball-up opened after a turnover")
	_check(_count(ch, "stoppage <- free") == 0, "a ball-up opened after a free")
	_check(_count(ch, "stoppage <- stoppage") > 0, "no ball-up was called in play (a contest that locked up)")


func _test_scores_stay_realistic() -> void:
	var r := _play()
	var per := float(r["points"]) / float(r["games"])
	_check(per > 130.0 and per < 230.0, "match points %.0f out of a plausible range" % per)


## Plays the sample with `tuning` applied; returns the chain starts, the
## "spills free" tackle lines and the games played.
func _play_tuned(tuning: Dictionary) -> Dictionary:
	MatchSim.tune = tuning
	MatchSim.audit_chains_on = true
	MatchSim.audit_chains = {}
	var spills := 0
	var games := 0
	for pair in CLUBS:
		for s in range(SEEDS):
			var sim := _sim(pair[0], pair[1], 700 + s)
			sim.run()
			games += 1
			for ev in sim.events:
				if str(ev["text"]).ends_with("it spills free"):
					spills += 1
	MatchSim.audit_chains_on = false
	var chains: Dictionary = MatchSim.audit_chains.duplicate()
	MatchSim.audit_chains = {}
	MatchSim.tune = {}
	return {"chains": chains, "spills": spills, "games": games}


## Every FLOW key replaces a calibrated T key; a key that T lost would turn the
## override into a new, uncalibrated rate.
func _test_flow_keys_exist_in_calibration() -> void:
	for k in Ratings.FLOW:
		_check(Ratings.T.has(k), "Ratings.FLOW key %s is not in Ratings.T" % k)
	var sim := _sim("FRE", "MEL", 3)
	for k in Ratings.FLOW:
		_check(is_equal_approx(float(sim._rates()[k]), float(Ratings.FLOW[k])),
				"a match did not apply Ratings.FLOW[%s]" % k)


func _test_tackle_spill_is_a_tuned_lever() -> void:
	var never := _play_tuned({"TACKLE_SPILL": 0.0})
	var always := _play_tuned({"TACKLE_SPILL": 1.0})
	_check(int(never["spills"]) == 0, "a tackle spilled with TACKLE_SPILL at 0")
	_check(int(always["spills"]) > 0, "no tackle spilled with TACKLE_SPILL at 1")


func _test_lockups_make_ball_ups_in_play() -> void:
	var base := {"LOCKUP_PRESS": 0.0, "LOCKUP_SPOIL": 0.0}
	var none := _count(_play_tuned(base)["chains"], "stoppage <- stoppage")
	var press := _count(_play_tuned({"LOCKUP_PRESS": 1.0, "LOCKUP_SPOIL": 0.0})["chains"], "stoppage <- stoppage")
	var pocket := _count(_play_tuned({"LOCKUP_PRESS": 0.0, "LOCKUP_SPOIL": 1.0})["chains"], "stoppage <- stoppage")
	_check(press > none, "the press lockup added no ball-ups in play (%d vs %d)" % [press, none])
	_check(pocket > none, "the pocket lockup added no ball-ups in play (%d vs %d)" % [pocket, none])


func _test_rushed_kick_intercept_mark() -> void:
	var sim := _sim("FRE", "MEL", 3)
	var taker: Dictionary = (sim.squads[1] as Squad).ground[0]
	var before := float(sim.team_stats[1].get("intercept_marks", 0.0))
	sim._kick_marked(1, taker, 10.0, false)
	_check(float(sim.team_stats[1].get("intercept_marks", 0.0)) == before, "an unmarked kick counted an intercept mark")
	sim._kick_marked(1, taker, 10.0, true)
	_check(float(sim.team_stats[1].get("intercept_marks", 0.0)) == before + 1.0, "a marked kick did not count one intercept mark")
	_check(float(sim.team_stats[1].get("marks", 0.0)) >= 1.0, "an intercept mark was not also a mark")


func _test_rotation_cadence_scales_with_chains() -> void:
	var on := _sim("FRE", "MEL", 3)
	var want := roundi(3.0 * float(Ratings.FLOW["chains_per_game"]) / MatchSim.CADENCE_CHAINS)
	_check(on._chains_for(3) == want and want > 3, "rotation cadence %d did not scale with more chains" % on._chains_for(3))
	_check(on._chains_for(0) >= 1, "a call length of zero chains")
