extends RefCounted
## Back-zone carrying (row 92, T9.Q22, director 2026-11-06): a defender takes
## less of the ball in his own back zone (MatchSim.CARRY_BACK_RETUNED) and a
## midfielder drops back for more of it. Director 2026-11-07 ("Both fixes"):
## the back-zone carrier is picked on his ball use, not his intercepting; the
## rebound 50 is the disposal that takes it out of defensive 50; after a spoil
## the first touch is whoever wins the ground ball. Run through
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
	_t("_test_back_carrier_follows_ball_use")
	_t("_test_rebound_owed_not_credited_at_contest")
	_t("_test_rebound_to_disposer_out_of_d50")
	_t("_test_spoil_goes_to_ground_ball_winner")
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
	_check(is_equal_approx(float(tuned["DEF"]), 3.3), "a defender's back-zone weight on ball use is 3.3 (%s)" % tuned["DEF"])
	for r in [["MID", 1.0], ["RUCK", 0.3], ["FWD", 0.12]]:
		_check(is_equal_approx(float(tuned[r[0]]), float(r[1])), "%s back-zone weight is %s" % r)


## The pinned behaviour: 4,000 back-zone picks for Fremantle (seed 31): a
## defender still has most of the ball (about 60%).
func _test_defender_leads_the_back_zone() -> void:
	var on := _picks(_sim(31), -50.0)
	var d_on := float(on.get("DEF", 0)) / DRAWS
	_check(d_on > 0.5, "defenders still take most of the back zone's ball (%.1f%%)" % (100 * d_on))


## Two defenders, one a ball user (carry and disposal 90, intercept 30) and
## one a spoiler (intercept 90, carry and disposal 30): in the back zone the
## ball goes to the ball user, about (90/30)^2 = 9 to 1; the old intercept
## pick sent it the other way.
func _test_back_carrier_follows_ball_use() -> void:
	var sim := _sim(31)
	var defs := []
	for p in (sim.squads[0] as Squad).ground:
		if str(p["role"]) == "DEF":
			defs.append(p)
	_check(defs.size() >= 2, "Fremantle has two defenders on the ground")
	if defs.size() < 2:
		return
	var user: Dictionary = (defs[0] as Dictionary).duplicate(true)
	var spoiler: Dictionary = (defs[1] as Dictionary).duplicate(true)
	for k in ["carry", "disposal"]:
		user["attr"][k] = 90.0
		spoiler["attr"][k] = 30.0
	user["attr"]["intercept"] = 30.0
	spoiler["attr"]["intercept"] = 90.0
	var to_user := 0
	for i in range(DRAWS):
		if str(sim.pick_carrier(0, -50.0, [user, spoiler])["id"]) == str(user["id"]):
			to_user += 1
	var share := float(to_user) / DRAWS
	_check(share > 0.8, "the back-zone ball goes to the ball user, not the spoiler (%.1f%%)" % (100 * share))
	_check(is_equal_approx(sim._ball_use(user), 0.58 * sim._a(user, "carry") + 0.42 * sim._a(user, "disposal")),
			"ball use is kick_in_taker's carry/disposal blend")


## A failed entry: the defence has it, but the rebound 50 is not credited at
## the contest; it is owed to the defending side (seeded entries).
func _test_rebound_owed_not_credited_at_contest() -> void:
	var turnovers := 0
	var clean := true
	for seed in range(40):
		var sim := _sim(4100 + seed)
		sim.begin_quarter()
		var feeder: Dictionary = (sim.squads[0] as Squad).ground[0]
		var res: Dictionary = sim.resolve_forward50(0, 50.0, feeder)
		if str(res.get("outcome", "")) != "turnover":
			continue
		turnovers += 1
		var pid := str((res["actor"] as Dictionary)["id"])
		clean = clean and float(sim.team_stats[1].get("rebounds", 0.0)) == 0.0 \
				and float(sim.player_stats.get(pid, {}).get("rebounds", 0.0)) == 0.0 \
				and sim._rebound_owed == 1
	_check(turnovers > 0, "some seeded entries are turned over (%d)" % turnovers)
	_check(clean, "a turned-over entry credits no rebound 50 at the contest; it is owed to the defence")


## The owed rebound 50 goes to the player whose kick or handball takes it out
## of defensive 50. The credit draws no dice, so the same seed with nothing
## owed plays the same chain: the difference is that one disposal.
func _test_rebound_to_disposer_out_of_d50() -> void:
	var credited := 0
	var right_man := true
	var f50 := float(Ratings.T["forward50_line"])
	for seed in range(60):
		var with_owed := _chain_from_d50(4300 + seed, true)
		var without := _chain_from_d50(4300 + seed, false)
		var diff := {}
		for id in with_owed["reb"]:
			var d := int(with_owed["reb"][id]) - int((without["reb"] as Dictionary).get(id, 0))
			if d != 0:
				diff[id] = d
		for id in without["reb"]:
			if not (with_owed["reb"] as Dictionary).has(id):
				diff[id] = -int(without["reb"][id])
		if diff.is_empty():
			continue
		credited += 1
		if diff.size() != 1 or int(diff.values()[0]) != 1:
			right_man = false
			continue
		var id: String = diff.keys()[0]
		# He disposed of it from inside his defensive 50 in this chain.
		var from_d50 := false
		for ev in with_owed["events"]:
			if str(ev.get("player_id", "")) == id and int(ev.get("side", -1)) == 1 \
					and str(ev.get("kind", "")) in ["kick", "handball", "mark"] and -float(ev.get("fp", 0.0)) <= f50:
				from_d50 = true
		right_man = right_man and from_d50
	_check(credited > 10, "the owed rebound 50 is credited in most chains out of defence (%d of 60)" % credited)
	_check(right_man, "it goes to one player, once, who disposed of it inside defensive 50")


## Play one chain for side 1 from a ball won back 50 m out from its own goal
## (fp 50, side 0 attacking): the rebound 50s it credits (id -> count) and its events.
func _chain_from_d50(seed: int, owed: bool) -> Dictionary:
	var sim := _sim(seed)
	sim.begin_quarter()
	sim.at_centre = false
	sim.kick_in = false
	sim.boundary_throw_in = false
	sim.fp = 50.0
	sim._prev_end = "turnover"
	sim.next_side = 1
	sim._won_back = {}
	sim._rebound_owed = 1 if owed else -1
	var before := sim.events.size()
	sim._play_one_chain(sim._rates())
	var reb := {}
	for id in sim.player_stats:
		var n := int(sim.player_stats[id].get("rebounds", 0.0))
		if n > 0:
			reb[id] = n
	return {"reb": reb, "events": sim.events.slice(before)}


## A spoiled entry: whoever wins the ground ball has it (the spoiler only some
## of the time), the feed names him, and the next chain's first touch is his.
func _test_spoil_goes_to_ground_ball_winner() -> void:
	var spoils := 0
	var other_man := 0
	var first_touch_ok := true
	var text_ok := true
	for seed in range(200):
		var sim := _sim(4500 + seed)
		sim.begin_quarter()
		var feeder: Dictionary = (sim.squads[0] as Squad).ground[0]
		var res: Dictionary = sim.resolve_forward50(0, 50.0, feeder)
		if str(res.get("outcome", "")) != "turnover":
			continue
		var ev: Dictionary = sim.events[sim.events.size() - 1]
		if not str(ev.get("text", "")).contains("spoils it"):
			continue
		spoils += 1
		var gid := str((res["actor"] as Dictionary)["id"])
		text_ok = text_ok and str(ev.get("kind", "")) == "rebound" and str(ev.get("player_id", "")) == gid \
				and bool(sim._won_back.get("gathered", false)) and not bool(sim._won_back.get("marked", false))
		if not str(ev.get("text", "")).contains("and wins it"):
			other_man += 1
		# The next chain starts from him.
		sim.at_centre = false
		sim.kick_in = false
		sim.boundary_throw_in = false
		sim.fp = float(res["fp"])
		sim._prev_end = "turnover"
		sim.next_side = 1
		var before := sim.events.size()
		sim._play_one_chain(sim._rates())
		for e in sim.events.slice(before):
			if int(e.get("side", -1)) == 1 and str(e.get("player_id", "")) != "":
				first_touch_ok = first_touch_ok and str(e["player_id"]) == gid
				break
	_check(spoils > 5, "some seeded entries are spoiled to the deck (%d)" % spoils)
	_check(text_ok, "the feed names the ground-ball winner as the one who has it, gathered not marked")
	_check(other_man > 0, "the ground ball is not always the spoiler's (%d of %d to someone else)" % [other_man, spoils])
	_check(first_touch_ok, "the next chain's first touch is the ground-ball winner's")
