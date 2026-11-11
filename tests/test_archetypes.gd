extends RefCounted
## The coach's two archetypes (Archetypes.gd, row 119): the appointment
## interview's totals and tie rule, the drift cases from the spec, the match
## levers, save and reload, and an older save earning its way in.
## Run through tests/run_archetypes_tests.gd.

var failures: Array[String] = []
var checks := 0
const SUITE_SEED := 2027


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	_t("_test_interview_totals")
	_t("_test_tie_rule")
	_t("_test_drift_cases")
	_t("_test_season_end")
	_t("_test_levers")
	_t("_test_ballup_calls_tally")
	_t("_test_gambler_swing")
	_t("_test_rivals")
	_t("_test_match_neutral")
	_t("_test_save_reload")
	_t("_test_old_save")
	GameState.delete_saved_career()
	CoachEffects.table = {}
	CoachEffects.usual = {}
	CoachEffects.my_arch = {}
	GameState.replay_seed = 0
	print(Ran.line("Archetypes", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## Every path through the interview: each set's questions weigh 10, every
## archetype is reachable, and every path holds one of each set.
func _test_interview_totals() -> void:
	var w := {"s": 0, "p": 0}
	for q in Archetypes.QUESTIONS:
		w[str(q["set"])] += int(q["w"])
		var ids := {}
		for a in q["answers"]:
			ids[str(a[0])] = true
		var want: Array = Archetypes.STRATEGIC if str(q["set"]) == "s" else Archetypes.PHILOSOPHICAL
		_check(ids.size() == 4 and want.all(func(x): return ids.has(x)),
				"Every answer of a question scores a different archetype of its set")
	_check(w["s"] == 10 and w["p"] == 10, "Both sets weigh 10 (%d, %d)" % [w["s"], w["p"]])
	var held := {}
	var paths := 0
	for n in range(16384):
		var picks := []
		var k := n
		for i in range(7):
			picks.append(k % 4)
			k /= 4
		var out := Archetypes.score_interview(picks)
		var hs := str(out["held"]["s"])
		var hp := str(out["held"]["p"])
		held[hs] = int(held.get(hs, 0)) + 1
		held[hp] = int(held.get(hp, 0)) + 1
		var total := 0.0
		for set_key in ["s", "p"]:
			for id in out[set_key]:
				total += float(out[set_key][id])
		if Archetypes.STRATEGIC.has(hs) and Archetypes.PHILOSOPHICAL.has(hp) and is_equal_approx(total, 20.0):
			paths += 1
	_check(paths == 16384, "Every one of the 16,384 paths holds one of each set, 20 points in all (%d)" % paths)
	for id in Archetypes.STRATEGIC + Archetypes.PHILOSOPHICAL:
		_check(int(held.get(id, 0)) > 0, "%s can be reached" % id)


## A tie goes to the answer given last among those tied.
func _test_tie_rule() -> void:
	# Q1 DS 4, Q2 CC 2, Q5 PC 4: DS 4 v PC 4, PC answered later.
	var out := Archetypes.score_interview([0, 2, 0, 0, 3, 0, 0])
	_check(str(out["held"]["s"]) == "PC", "DS 4 v PC 4: the later answer wins (%s)" % out["held"]["s"])
	# Q3 HARD 2, Q4 HARD 3 = 5 v Q6 GAMB 3, Q7 GAMB 2 = 5.
	out = Archetypes.score_interview([0, 0, 0, 0, 0, 3, 3])
	_check(str(out["held"]["p"]) == "GAMB", "HARD 5 v GAMB 5, Gambler answered last (%s)" % out["held"]["p"])
	# Q3 GAMB 2, Q4 GAMB 3 = 5 v Q6 HARD 3, Q7 HARD 2 = 5.
	out = Archetypes.score_interview([0, 0, 3, 3, 0, 0, 0])
	_check(str(out["held"]["p"]) == "HARD", "GAMB 5 v HARD 5, Hardline answered last (%s)" % out["held"]["p"])


func _seasons_to_change(start: Dictionary, held: String, other: String, share_other: float, max_s := 8) -> int:
	var sc := start.duplicate()
	for s in range(1, max_s + 1):
		var shares := {other: share_other}
		if share_other < 1.0:
			shares[held] = 1.0 - share_other
		sc = Archetypes.drift(sc, shares)
		var now := Archetypes.held_after(sc, held)
		if now != held:
			return s
	return -1


## The spec's cases: all the other way changes in season 3, 75% in season 5,
## 50% never in eight; a split interview changes in one.
func _test_drift_cases() -> void:
	var sc := Archetypes.drift({"A": 10.0, "B": 0.0}, {"B": 1.0})
	_check(is_equal_approx(sc["A"], 8.0) and is_equal_approx(sc["B"], 2.5), "One season: 10v0 becomes 8.0v2.5")
	_check(_seasons_to_change({"A": 10.0, "B": 0.0}, "A", "B", 1.0) == 3, "All the other way: changes in season 3")
	_check(_seasons_to_change({"A": 10.0, "B": 0.0}, "A", "B", 0.75) == 5, "75% the other way: changes in season 5")
	_check(_seasons_to_change({"A": 10.0, "B": 0.0}, "A", "B", 0.5) == -1, "50%: never in eight seasons")
	_check(_seasons_to_change({"A": 6.0, "B": 4.0}, "A", "B", 1.0) == 1, "A 6v4 interview changes in season 1")
	_check(_seasons_to_change({"A": 4.0, "B": 3.0}, "A", "B", 1.0) == 1, "A 4v3 interview changes in season 1")
	_check(Archetypes.held_after({"A": 5.0, "B": 5.0}, "A") == "A", "A level score keeps what he holds")


## The tally turns into drift at season end; Balanced quarters earn nothing.
func _test_season_end() -> void:
	var a := Archetypes.score_interview([0, 0, 0, 0, 0, 0, 0])
	_check(str(a["held"]["s"]) == "DS" and str(a["held"]["p"]) == "HARD", "All first answers: DS and Hardline")
	for i in range(3):
		var r := Archetypes.season_end(_season(a, "attacking", "back"))
		a = r["arch"]
		_check((r["changed"] as Array).size() == (2 if i == 2 else 0), "Season %d changes %s" % [i + 1, r["changed"]])
	_check(str(a["held"]["s"]) == "TA" and str(a["held"]["p"]) == "FATH",
			"Three seasons of Attack Corridor and backing them: TA and Father Figure")
	var b := Archetypes.score_interview([0, 0, 0, 0, 0, 0, 0])
	b = Archetypes.season_end(_season(b, "balanced", ""))["arch"]
	_check(is_equal_approx(float(b["s"]["DS"]), 8.0) and str(b["held"]["s"]) == "DS", "A Balanced season only decays")


func _season(a: Dictionary, plan: String, press: String) -> Dictionary:
	for i in range(88):
		Archetypes.tally_plan(a, plan)
	if press != "":
		for i in range(10):
			Archetypes.tally_press(a, press)
	return a


## Row 151: the late centre ball-up still counts toward the Philosophical
## drift. Push numbers forward is the Gambler's call (as Stack the stoppage,
## which the gate no longer offers, was); Flood behind the ball earns nothing.
func _test_ballup_calls_tally() -> void:
	var a := Archetypes.blank()
	Archetypes.tally_call(a, "push")
	_check(int((a["tally"]["calls"] as Dictionary).get("GAMB", 0)) == 1, "Push numbers forward counts toward the Gambler")
	Archetypes.tally_call(a, "flood")
	Archetypes.tally_call(a, "none")
	_check((a["tally"]["calls"] as Dictionary) == {"GAMB": 1}, "Flood behind the ball and no call count toward nothing (%s)" % [a["tally"]["calls"]])
	Archetypes.tally_call(a, "stack")
	_check(int(a["tally"]["calls"]["GAMB"]) == 2, "Stack the centre bounce (the goal-run gate) still counts")
	var known := true
	for k in Archetypes.CALL_KEY:
		known = known and MatchSim.BURSTS.has(str(k))
	_check(known and Archetypes.CALL_KEY.size() >= 2, "Every call that earns points is a call the match knows")
	# Through the match record, as the season reads it: your answer at the gate.
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState.coach_arch = Archetypes.blank()
	GameState._note_coach_arch([{"home": "GEE", "away": "COL", "moments": [
			{"kind": "bounce", "side": 0, "call": "push"}, {"kind": "bounce", "side": 0, "call": "none"},
			{"kind": "bounce", "side": 1, "call": "push"}]}])
	_check((GameState.coach_arch["tally"]["calls"] as Dictionary) == {"GAMB": 1},
			"A match where you pushed numbers forward tallies one Gambler call, an unanswered card none (%s)" % [GameState.coach_arch["tally"]["calls"]])


func _test_levers() -> void:
	var l := Archetypes.levers("TA", "GAMB")
	_check(str(l["fplan"]) == "attacking" and is_equal_approx(l["scost"], 2.0), "Territory's cost is doubled")
	_check(is_equal_approx(l["goal"], 1.025) and is_equal_approx(l["exposed"], 1.06)
			and is_equal_approx(l["clangers"], 1.03), "The Gambler's sizes")
	var f := Archetypes.levers("PC", "FATH")
	_check(is_equal_approx(f["morale"], 10.0) and is_equal_approx(f["clangers"], 1.06)
			and is_equal_approx(f["fifty"], 1.2), "Father Figure's sizes")
	_check(Archetypes.levers("", "").is_empty(), "No archetypes, no levers")
	var sq := Squad.new("Geelong", GameDB.club_list("GEE"), true, "GEE")
	CoachEffects.table = {"GEE": {"exec": 1.0, "read": 0.0, "ai": true, "assistant": false,
			"style": "balanced", "arch_p": "ANA"}}
	CoachEffects.usual = {"GEE": "contest"}
	CoachEffects.apply(sq)
	_check(str(sq.arch.get("fplan", "")) == "contest" and is_equal_approx(sq.tactics_exec, 1.125),
			"A rival on Win Contest with an Analytical coach: CC, exec x1.125")
	CoachEffects.table = {}
	CoachEffects.usual = {}


## The Gambler's swing is symmetric (director 2026-11-10): +2 after a win,
## -2 after a loss, on top of what a player who played gets anyway.
func _test_gambler_swing() -> void:
	_check(Archetypes.SWING_WIN == 2 and Archetypes.SWING_LOSS == -2, "swing +2 / -2")
	for won in [true, false]:
		var plain := [{"id": "a", "morale": 50, "overall": 70}]
		var gamb := [{"id": "a", "morale": 50, "overall": 70}]
		ClubLife.morale_after_match(plain, {"a": true}, won)
		ClubLife.morale_after_match(gamb, {"a": true}, won, {}, 0.0, {}, "GAMB")
		var gap := ClubLife.morale(gamb[0]) - ClubLife.morale(plain[0])
		_check(gap == (2 if won else -2), "Gambler %s: %+d on a plain coach (got %+d)" % ["win" if won else "loss", 2 if won else -2, gap])


func _test_rivals() -> void:
	_check(Archetypes.rival_philosophical("reactive", {}) == "ANA", "Reactive: Analytical")
	_check(Archetypes.rival_philosophical("stubborn", {}) == "HARD", "Stubborn: Hardline")
	_check(Archetypes.rival_philosophical("cautious", {}) == "FATH", "Cautious: Father Figure")
	_check(Archetypes.rival_philosophical("gambler", {}) == "GAMB", "Gambler: The Gambler")
	_check(Archetypes.rival_philosophical("balanced", {"tactics": 80, "manage": 85}) == "ANA", "Balanced and sharp: Analytical")
	_check(Archetypes.rival_philosophical("balanced", {"tactics": 70, "manage": 82}) == "FATH", "Balanced man-manager: Father Figure")
	_check(Archetypes.strategic_for_plan("balanced") == "", "Balanced has no Strategic archetype")


## A match with no archetypes plays the same each time; archetypes change it.
func _test_match_neutral() -> void:
	var a := _play({})
	_check(a == _play({}), "The same seed plays the same match")
	var c := _play(Archetypes.levers("CC", "HARD"))
	_check(c != a, "Archetypes change the match (%s v %s)" % [a, c])


func _play(arch: Dictionary) -> Array:
	var h := Squad.new("Geelong", GameDB.club_list("GEE"), true, "GEE")
	var w := Squad.new("Sydney", GameDB.club_list("SYD"), false, "SYD")
	h.arch = arch
	var sim := MatchSim.new(h, w, 77)
	sim.tactics[0] = {"gameplan": "contest"}
	var res: Dictionary = sim.run()
	return [res.get("score", []), sim.injuries.size()]


func _test_save_reload() -> void:
	GameState.reset()
	GameState.interview_due = true
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	GameState.coach_name = "Pat Keane"
	GameState.finish_interview([1, 0, 1, 1, 1, 1, 1])
	_check(not GameState.interview_due, "The interview is sat once")
	Archetypes.tally_press(GameState.coach_arch, "back")
	var before: Dictionary = GameState.coach_arch.duplicate(true)
	_check(GameState.save_career() and GameState.load_career(), "The career saves and loads")
	_check(GameState.coach_name == "Pat Keane" and GameState.coach_arch == before,
			"Name, archetypes and tally survive a reload")
	_check(str(GameState.coach_arch["held"]["s"]) == "TA" and str(GameState.coach_arch["held"]["p"]) == "ANA",
			"TA and Analytical held (%s)" % [GameState.coach_arch.get("held")])
	GameState._refresh_coach_tactics()
	_check(CoachEffects.arch_of("GEE") == ["TA", "ANA"], "Your matches carry your archetypes (%s)" % [CoachEffects.arch_of("GEE")])


## An older save: no name, no archetypes, no interview; his coaching earns
## them by drift.
func _test_old_save() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	_check(not GameState._save_state().has("coach_arch") and not GameState.interview_due,
			"A career without archetypes saves none and has no interview due")
	_season(GameState.coach_arch, "defensive", "criticise")
	GameState._coach_arch_season_end()
	_check(str(GameState.coach_arch["held"]["s"]) == "DS" and str(GameState.coach_arch["held"]["p"]) == "HARD",
			"One season of Defensive Press and criticism earns DS and Hardline (%s)" % [GameState.coach_arch.get("held")])
