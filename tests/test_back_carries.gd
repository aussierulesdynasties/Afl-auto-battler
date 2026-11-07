extends RefCounted
## Back-zone carrying (row 92, T9.Q22, director 2026-11-06): a defender takes
## less of the ball in his own back zone (MatchSim.CARRY_BACK_RETUNED) and a
## midfielder drops back for more of it. Run through
## tests/run_back_carries_tests.gd.
## Seeded by design: every sim takes an explicit match seed.

var failures: Array[String] = []
var checks := 0

const DRAWS := 4000


func run() -> void:
	failures.clear()
	checks = 0
	GameDB.reload()
	_t("_test_weights")
	_t("_test_defender_leads_the_back_zone")
	print(Ran.line("Back carries", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _sim(seed: int) -> MatchSim:
	return MatchSim.new(Squad.new("FRE", GameDB.club_list("FRE"), true, "FRE"),
			Squad.new("MEL", GameDB.club_list("MEL"), false, "MEL"), seed)


## Who the home side's carrier picks go to at field position fp: role -> count,
## plus "ids" (id -> count).
func _picks(sim: MatchSim, fp: float) -> Dictionary:
	var out := {"ids": {}}
	for i in range(DRAWS):
		var p = sim.pick_carrier(0, fp)
		var r := str(p["role"])
		out[r] = int(out.get(r, 0)) + 1
		out["ids"][str(p["id"])] = int((out["ids"] as Dictionary).get(str(p["id"]), 0)) + 1
	return out


func _test_weights() -> void:
	var tuned: Dictionary = MatchSim.CARRY_BACK_RETUNED
	_check(is_equal_approx(float(tuned["DEF"]), 0.55), "a defender's back-zone weight is 0.55 (%s)" % tuned["DEF"])
	for r in [["MID", 1.0], ["RUCK", 0.3], ["FWD", 0.12]]:
		_check(is_equal_approx(float(tuned[r[0]]), float(r[1])), "%s back-zone weight is %s" % r)


## The pinned behaviour: 4,000 back-zone picks for Fremantle (seed 31): a
## defender still has most of the ball (about 60%).
func _test_defender_leads_the_back_zone() -> void:
	var on := _picks(_sim(31), -50.0)
	var d_on := float(on.get("DEF", 0)) / DRAWS
	_check(d_on > 0.5, "defenders still take most of the back zone's ball (%.1f%%)" % (100 * d_on))
