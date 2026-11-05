extends RefCounted
## Back-zone carrying (row 92, T9.Q22, director 2026-11-06): with the switch
## back_carries on, a defender takes less of the ball in his own back zone
## (MatchSim.CARRY_BACK_RETUNED) and a midfielder drops back for more of it;
## the other zones and the switch-off pick are unchanged. Run through
## tests/run_back_carries_tests.gd.
## Seeded by design: every sim takes an explicit match seed.

var failures: Array[String] = []
var checks := 0

const DRAWS := 4000


func run() -> void:
	failures.clear()
	checks = 0
	GameDB.reload()
	_t("_test_switch_is_known_and_read_at_setup")
	_t("_test_weights")
	_t("_test_defender_carries_less_in_the_back_zone")
	_t("_test_other_zones_unchanged")
	Features.clear("back_carries")
	print(Ran.line("Back carries", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _sim(seed: int, on: bool) -> MatchSim:
	Features.set_on("back_carries", on)
	var sim := MatchSim.new(Squad.new("FRE", GameDB.club_list("FRE"), true, "FRE"),
			Squad.new("MEL", GameDB.club_list("MEL"), false, "MEL"), seed)
	Features.clear("back_carries")
	return sim


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


func _test_switch_is_known_and_read_at_setup() -> void:
	_check(Features.KNOWN.has("back_carries"), "back_carries is a known switch")
	_check(_sim(7, true).back_carries_on, "switch on at set-up: the sim reads it")
	_check(not _sim(7, false).back_carries_on, "switch off at set-up: the sim reads it")


func _test_weights() -> void:
	var tuned: Dictionary = MatchSim.CARRY_BACK_RETUNED
	var old: Dictionary = MatchSim.CARRY_ROLES["back"]
	_check(is_equal_approx(float(tuned["DEF"]), 0.55), "a defender's back-zone weight is 0.55 (was %s)" % old["DEF"])
	_check(float(tuned["DEF"]) < float(old["DEF"]), "the retune lowers the defender's back-zone weight")
	for r in ["MID", "RUCK", "FWD"]:
		_check(is_equal_approx(float(tuned[r]), float(old[r])), "%s back-zone weight unchanged" % r)
	_check(is_equal_approx(float(old["DEF"]), 1.0), "switch off: CARRY_ROLES back DEF stays 1.0")


## The pinned behaviour: 4,000 back-zone picks for Fremantle (seed 31), the same
## dice with the switch off and on. Defenders take about 72% off and about 60% on;
## the best-used defender takes fewer; a defender still has most of the ball.
func _test_defender_carries_less_in_the_back_zone() -> void:
	var off := _picks(_sim(31, false), -50.0)
	var on := _picks(_sim(31, true), -50.0)
	var d_off := float(off.get("DEF", 0)) / DRAWS
	var d_on := float(on.get("DEF", 0)) / DRAWS
	var m_off := float(off.get("MID", 0)) / DRAWS
	var m_on := float(on.get("MID", 0)) / DRAWS
	_check(d_on < d_off - 0.07, "defenders' back-zone share falls by more than 7 points (%.1f%% -> %.1f%%)" % [100 * d_off, 100 * d_on])
	_check(d_on > 0.5, "defenders still take most of the back zone's ball (%.1f%%)" % (100 * d_on))
	_check(m_on > m_off + 0.05, "midfielders drop back for more of it (%.1f%% -> %.1f%%)" % [100 * m_off, 100 * m_on])
	# One back-zone defender: his own share of the ball falls.
	var sim := _sim(31, false)
	var top := ""
	for p in (sim.squads[0] as Squad).ground:
		if str(p["role"]) == "DEF" and (top == "" or int((off["ids"] as Dictionary).get(str(p["id"]), 0)) > int((off["ids"] as Dictionary).get(top, 0))):
			top = str(p["id"])
	_check(top != "", "Fremantle field a defender")
	var n_off := int((off["ids"] as Dictionary).get(top, 0))
	var n_on := int((on["ids"] as Dictionary).get(top, 0))
	_check(n_on < n_off, "the busiest defender (%s) carries less: %d -> %d of %d" % [top, n_off, n_on, DRAWS])


## Middle, attack and inside 50: the same dice give the same carriers either way.
func _test_other_zones_unchanged() -> void:
	for fp in [0.0, 30.0, 70.0]:
		var a := _sim(47, false)
		var b := _sim(47, true)
		var same := true
		for i in range(500):
			if str(a.pick_carrier(0, fp)["id"]) != str(b.pick_carrier(0, fp)["id"]):
				same = false
				break
		_check(same, "carrier picks at %.0f m are unchanged by the switch" % fp)
