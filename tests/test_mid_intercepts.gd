extends RefCounted
## Midfield intercepts (row 89, director 2026-11-06, T8.Q8): with mid_intercepts
## on, a general-play kick through the middle with no contest can be taken
## outright by one of the other side's midfielders (MatchSim._mid_kick_intercept),
## lifting midfield intercepts toward Champion Data's 2.5 a game; off, the match
## never rolls it. Run through tests/run_mid_intercepts_tests.gd.
## Seeded by design: every sim takes an explicit match seed.

var failures: Array[String] = []
var checks := 0

const CLUBS := [["FRE", "MEL"], ["GEE", "COL"], ["SYD", "CAR"], ["BRL", "ESS"]]
const SEEDS := 8


func run() -> void:
	failures.clear()
	checks = 0
	GameDB.reload()
	_t("_test_off_never_rolls")
	_t("_test_taker_is_their_midfielder")
	_t("_test_on_lifts_midfield_intercepts")
	Features.clear("mid_intercepts")
	print(Ran.line("Mid intercepts", self))


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


## Intercepts and player-games of the men who filled `role`, both sides.
func _role_ic(res: Dictionary, role: String) -> Vector2:
	var out := Vector2.ZERO
	for side in range(2):
		for pl in (res["roster"][side] as Array):
			var st: Dictionary = (res["players"] as Dictionary).get(str(pl["id"]), {})
			if st.is_empty() or str(pl.get("list_role", pl.get("role", ""))) != role:
				continue
			out += Vector2(float(st.get("intercepts", 0.0)), 1.0)
	return out


## Off, the roll's own dice are never drawn: the match plays as before.
func _test_off_never_rolls() -> void:
	Features.set_on("mid_intercepts", false)
	var sim := _sim("FRE", "MEL", 4242)
	_check(not sim.mid_intercepts_on, "off: the switch reads off")
	var before: int = sim.mid_ic_rng.state
	sim.run()
	_check(sim.mid_ic_rng.state == before, "off: the midfield intercept dice were drawn")


## The taker is one of the other side's midfielders, it counts as his
## intercept, and the ball goes to his side.
func _test_taker_is_their_midfielder() -> void:
	Features.set_on("mid_intercepts", true)
	var sim := _sim("GEE", "COL", 77)
	var before := float(sim.team_stats[1].get("intercepts", 0.0))
	var r: Dictionary = sim._mid_kick_intercept(0, 0.0)
	_check(str(r.get("outcome", "")) == "turnover", "a midfield intercept turns it over")
	var taker = r.get("actor")
	_check(taker != null and str(taker["role"]) == "MID", "the taker is a midfielder")
	var theirs := false
	for p in (sim.squads[1] as Squad).ground:
		if taker != null and str(p["id"]) == str(taker["id"]):
			theirs = true
	_check(theirs, "the taker is on the other side's ground")
	_check(float(sim.team_stats[1].get("intercepts", 0.0)) == before + 1.0, "it is the other side's intercept")


## Same seeds, switch off then on: midfielders intercept more, near the real
## 2.5 a game, and the score stays in a real range.
func _test_on_lifts_midfield_intercepts() -> void:
	var tot := {false: Vector2.ZERO, true: Vector2.ZERO}
	var pts := {false: 0.0, true: 0.0}
	var n := 0
	_check(CLUBS.size() == 4, "four fixtures")
	for on in [false, true]:
		Features.set_on("mid_intercepts", on)
		n = 0
		for c in CLUBS:
			for s in range(SEEDS):
				var sim := _sim(str(c[0]), str(c[1]), 8900 + s)
				var res: Dictionary = sim.run()
				tot[on] += _role_ic(res, "MID")
				pts[on] += float(res["score"][0] + res["score"][1]) / 2.0
				n += 1
	var off_rate: float = tot[false].x / maxf(1.0, tot[false].y)
	var on_rate: float = tot[true].x / maxf(1.0, tot[true].y)
	_check(on_rate > off_rate + 0.4, "midfield intercepts rise: off %.2f, on %.2f a game" % [off_rate, on_rate])
	_check(on_rate > 2.0 and on_rate < 3.0, "on: midfield intercepts %.2f a game (real 2.5)" % on_rate)
	var mean_pts: float = pts[true] / maxf(1.0, float(n))
	_check(mean_pts > 70.0 and mean_pts < 100.0, "on: a team scores %.1f a game" % mean_pts)
