extends RefCounted
## Game-plan traits (PlanTraits.gd, director 2026-11-10): ten traits, each with
## one strength and one cost on a lever the match already has; no trait plays
## the match exactly as before; each trait changes it; the quarter and
## scoreboard gates; the full-time line names the trait; save and reload, an
## older save, and rivals running none.
## Run through tests/run_plan_traits_tests.gd.

var failures: Array[String] = []
var checks := 0
const SUITE_SEED := 2027
const SEEDS := [77, 78, 79, 80, 81, 82]


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	_t("_test_data")
	_t("_test_no_trait_neutral")
	_t("_test_each_changes_the_match")
	_t("_test_gates")
	_t("_test_lever_direction")
	_t("_test_impact_names_trait")
	_t("_test_save_reload")
	_t("_test_old_save_and_rivals")
	GameState.delete_saved_career()
	CoachEffects.table = {}
	CoachEffects.usual = {}
	CoachEffects.my_trait = ""
	GameState.replay_seed = 0
	print(Ran.line("PlanTraits", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## Ten traits, each named, with an upside and a cost that both give a size,
## and two or three levers.
func _test_data() -> void:
	_check(PlanTraits.IDS.size() == 10, "Ten traits (%d)" % PlanTraits.IDS.size())
	var digit := RegEx.create_from_string("[0-9]")
	for id in PlanTraits.IDS:
		_check(PlanTraits.name_of(id) != "", "%s has a name" % id)
		_check(digit.search(str(PlanTraits.UPSIDE.get(id, ""))) != null
				and digit.search(str(PlanTraits.COST.get(id, ""))) != null,
				"%s states the size of its upside and its cost" % id)
		var n := (PlanTraits.LEVERS[id] as Dictionary).size()
		_check(n >= 2 and n <= 3, "%s pulls two or three levers (%d)" % [id, n])
	_check(PlanTraits.valid("nonsense") == "" and PlanTraits.valid("fortress") == "fortress",
			"Only a real trait id is kept")


## No trait: every lever is its neutral value, and an unknown id plays as none.
func _test_no_trait_neutral() -> void:
	var sim := _sim("", 77)
	var neutral := true
	for id in PlanTraits.IDS:
		for key in PlanTraits.LEVERS[id]:
			neutral = neutral and sim._gt(0, key) == 1.0 and sim._gt(1, key, 0.0) == 0.0
	_check(neutral, "With no trait every lever is neutral")
	var a := _play("", 77)
	_check(a == _play("", 77), "The same seed plays the same match")
	_check(a == _play("nonsense", 77), "An unknown trait plays as none")


## Each trait changes the match on at least one of the seeds, run by either
## club (Front-Runners needs the side running it to get well ahead).
func _test_each_changes_the_match() -> void:
	var base := []
	for s in SEEDS:
		base.append(_play("", s))
	for id in PlanTraits.IDS:
		var moved := false
		for i in range(SEEDS.size()):
			for side in range(2):
				moved = moved or _play(id, SEEDS[i], side) != base[i]
		_check(moved, "%s changes the match" % id)


## The quarter gates (Fast Starters) and the scoreboard gates (Front-Runners,
## Never Say Die).
func _test_gates() -> void:
	var sim := _sim("fast_starters", 77)
	sim.current_quarter = 1
	_check(sim._gt(0, "goal") == PlanTraits.FAST_STARTERS_GOAL and sim._gt(0, "legs") == 1.0
			and sim._gt(0, "stoppage", 0.0) == PlanTraits.FAST_STARTERS_STOPPAGE,
			"Fast Starters: first quarter, sharper shots and stoppages, legs as usual")
	sim.current_quarter = 4
	_check(sim._gt(0, "goal") == 1.0 and sim._gt(0, "legs") == PlanTraits.FAST_STARTERS_LEGS,
			"Fast Starters: last quarter, legs go quicker and the shots are as usual")
	var fr := _sim("front_runners", 77)
	fr.team_stats[0]["goals"] = 4.0
	_check(fr._gt(0, "momentum") == 1.0, "Front-Runners: 24 points up is not enough")
	fr.team_stats[0]["goals"] = 5.0
	_check(fr._gt(0, "momentum") == PlanTraits.FRONT_RUNNERS_MOMENTUM, "Front-Runners: 30 points up, the run of play counts more")
	fr.momentum = 0.5
	_check(fr._front_run() == PlanTraits.FRONT_RUNNERS_MOMENTUM, "Front-Runners: their run of play, when well ahead")
	fr.momentum = -0.5
	_check(fr._front_run() == 1.0, "Front-Runners: the other side's run of play is untouched")
	var nsd := _sim("never_say_die", 77)
	_check(nsd._gt(0, "opp_goal") == 1.0, "Never Say Die: level, their shots as usual")
	nsd.team_stats[0]["behinds"] = 1.0
	_check(nsd._gt(0, "opp_goal") == PlanTraits.NEVER_SAY_DIE_OPP_GOAL, "Never Say Die: in front, their shots go through more")


## Over six seeds, a trait's own line moves the way it says.
func _test_lever_direction() -> void:
	var cl := {"": 0.0, "kick_mark": 0.0, "chaos_ball": 0.0}
	var clear := {"": 0.0, "stoppage_kings": 0.0}
	for s in SEEDS:
		for id in cl:
			cl[id] += _stat(id, s, 0, "clangers")
		for id in clear:
			clear[id] += _stat(id, s, 0, "clearances")
	_check(cl["kick_mark"] < cl[""] and cl["chaos_ball"] > cl[""],
			"Kick-Mark Masters give away fewer clangers, Chaos Ball more (%s)" % [cl])
	_check(clear["stoppage_kings"] > clear[""], "Stoppage Kings win more clearances (%s)" % [clear])
	# Long Bombers' cost is per contested kick; how many such kicks there are moves
	# with the longer reach, so the levers are checked, not a six-match total.
	var lb := _sim("long_bombers", 77)
	_check(lb._gt(0, "icept") == PlanTraits.LONG_BOMBERS_ICEPT and lb._gt(1, "icept") == 1.0
			and lb._gt(0, "range", 0.0) == PlanTraits.LONG_BOMBERS_RANGE,
			"Long Bombers: their kicks reach further and are marked by the other side more")


## The full-time "What your calls did" line names the trait.
func _test_impact_names_trait() -> void:
	var lines := CoachReport.impact_lines([{"plan_trait": 1.5}, {"plan_trait": 0.8}], [{}, {}], 0, 0.3,
			["fortress", ""])
	var labels := lines.map(func(l): return str(l["label"]))
	_check(labels.has("Your Fortress (game-plan trait)") and labels.has("Their game-plan trait"),
			"The line names your trait (%s)" % [labels])
	_check(MatchSim.DECISION_CAUSES.has("plan_trait"), "A trait is one of the coach's decisions at full time")
	var sim := _sim("fortress", 77)
	var res: Dictionary = sim.run()
	_check(res.get("plan_traits", []) == ["fortress", ""], "The match result says who ran a trait")
	_check(float((sim.impact[0] as Dictionary).get("plan_trait", 0.0)) != 0.0,
			"Fortress's work is booked to its side")


func _test_save_reload() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState.set_plan_trait("chaos_ball")
	_check(GameState.plan_trait == "chaos_ball" and CoachEffects.my_trait == "chaos_ball", "The trait is set")
	_check(GameState.save_career() and GameState.load_career(), "The career saves and loads")
	_check(GameState.plan_trait == "chaos_ball" and CoachEffects.my_trait == "chaos_ball",
			"The trait survives a reload (%s)" % GameState.plan_trait)
	GameState.set_plan_trait("nonsense")
	_check(GameState.plan_trait == "" and not GameState._save_state().has("plan_trait"),
			"An unknown trait is none, and none is not saved")


## An older save has no trait; your club's match squad carries yours and a
## rival's the one of its usual game (none for Balanced); the scouting report
## says it.
func _test_old_save_and_rivals() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var state: Dictionary = GameState._save_state()
	_check(not state.has("plan_trait"), "A career without a trait saves none")
	GameState.set_plan_trait("fortress")
	state.erase("plan_trait")
	_check(GameState._restore_career(state) and GameState.plan_trait == "" and CoachEffects.my_trait == "",
			"An older save loads with no trait")
	CoachEffects.my_trait = "chaos_ball"
	CoachEffects.usual = {"SYD": "defensive", "STK": "balanced"}
	var mine := Squad.new("Geelong", GameDB.club_list("GEE"), true, "GEE")
	var theirs := Squad.new("Sydney", GameDB.club_list("SYD"), false, "SYD")
	var plain := Squad.new("St Kilda", GameDB.club_list("STK"), false, "STK")
	CoachEffects.apply_row(mine, _row(false))
	CoachEffects.apply_row(theirs, _row(true))
	CoachEffects.apply_row(plain, _row(true))
	_check(mine.plan_trait == "chaos_ball" and theirs.plan_trait == "fortress" and plain.plan_trait == "",
			"Your club runs your trait, a defensive rival Fortress, a balanced one none (%s, %s, %s)"
			% [mine.plan_trait, theirs.plan_trait, plain.plan_trait])
	CoachEffects.usual = {}
	CoachEffects.my_trait = ""
	for plan in PlanTraits.FOR_PLAN:
		var id := PlanTraits.for_plan(str(plan))
		_check(PlanTraits.valid(id) != "" and PlanTraits.rival_line(id).begins_with("Their game-plan trait is")
				and RegEx.create_from_string("[0-9]").search(PlanTraits.rival_line(id)) == null
				and GameState.CLUB_PLANS.has(str(plan)),
				"A %s rival's trait is real and scouted in plain words (%s)" % [plan, id])
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState.rival_plans = {"year": GameState.season_year, "clubs": {}, "usual": {"SYD": "contest"}}
	var report := str(GameState.opponent_report("SYD"))
	_check(report.contains("Their game-plan trait is Stoppage Kings"),
			"The report on a rival names its trait (%s)" % report.left(300))


func _row(ai: bool) -> Dictionary:
	return {"ai": ai, "exec": 1.0, "read": 0.0}


func _sim(id: String, s: int, side := 0) -> MatchSim:
	var h := Squad.new("Geelong", GameDB.club_list("GEE"), true, "GEE")
	var w := Squad.new("Sydney", GameDB.club_list("SYD"), false, "SYD")
	(h if side == 0 else w).plan_trait = id
	return MatchSim.new(h, w, s)


func _play(id: String, s: int, side := 0) -> Array:
	var sim := _sim(id, s, side)
	var res: Dictionary = sim.run()
	return [res.get("score", []), sim.injuries.size(), sim.team_stats[0].get("clangers", 0.0),
			sim.team_stats[1].get("intercept_marks", 0.0), sim.team_stats[0].get("metres_gained", 0.0),
			sim.team_stats[1].get("clangers", 0.0), sim.team_stats[1].get("metres_gained", 0.0)]


func _stat(id: String, s: int, side: int, key: String) -> float:
	var sim := _sim(id, s)
	sim.run()
	return float(sim.team_stats[side].get(key, 0.0))
