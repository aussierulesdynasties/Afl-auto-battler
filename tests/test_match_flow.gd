extends RefCounted
## Match flow (row 11, director 2026-10-10): with the match_flow switch on, a
## stoppage comes from a contest that locks up, never from a won ball (after an
## intercept or a free the winner plays on), chains are shorter and more
## numerous, and a ball-up in play is how its chain ended. With the switch off a
## match is as before. Run through tests/run_match_flow_tests.gd.
## Seeded by design: every sim takes an explicit match seed.

var failures: Array[String] = []
var checks := 0

const CLUBS := [["FRE", "MEL"], ["GEE", "COL"], ["SYD", "CAR"], ["BRL", "ESS"]]
const SEEDS := 5


func run() -> void:
	failures.clear()
	checks = 0
	GameDB.reload()
	_t("_test_off_by_default")
	_t("_test_won_ball_is_played_on")
	_t("_test_off_still_stops_after_a_won_ball")
	_t("_test_chains_are_shorter_and_more")
	_t("_test_scores_stay_realistic")
	Features.clear("match_flow")
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


## Plays the sample with the switch `on`; returns the chain starts by key
## (MatchSim.audit_chains), the games played and the total points.
func _play(on: bool) -> Dictionary:
	Features.set_on("match_flow", on)
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
	Features.clear("match_flow")
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


func _test_off_by_default() -> void:
	Features.clear("match_flow")
	_check(not Features.on("match_flow"), "match_flow is on without being asked")
	_check(Features.KNOWN.has("match_flow"), "match_flow is not a known switch")
	var sim := _sim("FRE", "MEL", 3)
	_check(int(sim._rates()["chains_per_game"]) == int(Ratings.T["chains_per_game"]),
			"a match without the switch does not play the calibrated chain count")


func _test_won_ball_is_played_on() -> void:
	var r := _play(true)
	var ch: Dictionary = r["chains"]
	_check(_total(ch) > 0, "no chains were recorded")
	_check(_count(ch, "stoppage <- turnover") == 0, "a ball-up opened after a turnover with match_flow on")
	_check(_count(ch, "stoppage <- free") == 0, "a ball-up opened after a free with match_flow on")
	_check(_count(ch, "stoppage <- stoppage") > 0, "no ball-up was called in play (a contest that locked up)")


func _test_off_still_stops_after_a_won_ball() -> void:
	var r := _play(false)
	var ch: Dictionary = r["chains"]
	_check(_count(ch, "stoppage <- turnover") + _count(ch, "stoppage <- free") > 0,
			"with the switch off, no ball-up ever follows a won ball: the old behaviour changed")


func _test_chains_are_shorter_and_more() -> void:
	var off := _play(false)
	var on := _play(true)
	var per_off := float(_total(off["chains"])) / float(off["games"])
	var per_on := float(_total(on["chains"])) / float(on["games"])
	_check(per_on > per_off * 1.2, "match_flow chains a game %.0f not clearly above %.0f" % [per_on, per_off])


func _test_scores_stay_realistic() -> void:
	for on in [false, true]:
		var r := _play(on)
		var per := float(r["points"]) / float(r["games"])
		_check(per > 130.0 and per < 230.0, "match points %.0f (flow %s) out of a plausible range" % [per, on])
