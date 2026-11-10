extends RefCounted
## Set shots (row 77, director ruling T8.Q9): a set shot converts by its
## distance (MatchSim.SET_BANDS_ON, the real AFL rates) so a closer one goes in
## more often than a longer one, and the set-shot share of shots sits near the
## real 55%. Run through tests/run_set_shots_tests.gd.
## Seeded by design: every sim takes an explicit match seed.

var failures: Array[String] = []
var checks := 0

const CLUBS := [["FRE", "MEL"], ["GEE", "COL"], ["SYD", "CAR"], ["BRL", "ESS"], ["HAW", "ADE"], ["WBD", "GWS"]]
const MATCHES := 120
const BalanceGate := preload("res://tests/balance_gate.gd")


func run() -> void:
	failures.clear()
	checks = 0
	GameDB.reload()
	_t("_test_marks_go_back_for_the_kick")
	_t("_test_shot_log_matches_the_shots")
	_t("_test_closer_set_shot_converts_more")
	_t("_test_set_share_near_real")
	_t("_test_set_shot_mark_names_its_spot")
	print(Ran.line("Set shots", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _sim(i: int) -> MatchSim:
	var c: Array = CLUBS[i % CLUBS.size()]
	var h := str(c[0])
	var a := str(c[1])
	return MatchSim.new(Squad.new(h, GameDB.club_list(h), true, h),
			Squad.new(a, GameDB.club_list(a), false, a), 770000 + i)


## Plays MATCHES seeded matches: pooled shot_log rows and the total score.
func _play() -> Dictionary:
	var shots := []
	var points := 0
	for i in range(MATCHES):
		var sim := _sim(i)
		var r: Dictionary = sim.run()
		shots.append_array(sim.shot_log)
		points += int(r["score"][0]) + int(r["score"][1])
	return {"shots": shots, "points": points}


func _test_marks_go_back_for_the_kick() -> void:
	var sim := _sim(0)
	# Tuned (director, 2026-11-06) so set shots are 55% of scoring shots, the
	# real rate: at least half the marks inside 50 go back for the kick.
	_check(sim.set_share() >= 0.5,
			"At least half the marks inside 50 go back for the kick (%.2f)" % sim.set_share())


## The balance harness reads MatchSim.shot_log: one row per counted shot.
func _test_shot_log_matches_the_shots() -> void:
	var sim := _sim(1)
	sim.run()
	for side in range(2):
		var n := 0
		var goals := 0
		for s in sim.shot_log:
			if int(s[0]) == side:
				n += 1
				goals += 1 if str(s[3]) == "goal" else 0
		_check(n > 0 and n == int(float((sim.team_stats[side] as Dictionary).get("shots", 0.0))),
				"Side %d: the shot log has every shot (%d against %s)" % [side, n,
				str((sim.team_stats[side] as Dictionary).get("shots", 0.0))])
		_check(goals == sim.goals(side), "Side %d: the shot log has every goal (%d against %d)" % [side, goals, sim.goals(side)])


## A closer set shot goes in more often than a longer one: the bands by their
## real rates, and the shots of 30 matches by distance.
func _test_closer_set_shot_converts_more() -> void:
	var by := {}
	for b in MatchSim.set_bands(MatchSim.SET_REF):
		by[str(b["key"])] = float(b["goal"])
	_check(by["close"] > by["front"] and by["front"] > by["angle"] and by["angle"] > by["long"],
			"From 25, 35, 45 then 55 metres straight in front, the chance falls (%s)" % str(by))
	var res := _play()
	var tally := {"near": [0, 0], "mid": [0, 0], "far": [0, 0]}
	for s in res["shots"]:
		if int(s[1]) != 1:
			continue
		var m := float(s[2])
		var band := "near" if m > 20.0 and m <= 30.0 else ("mid" if m > 40.0 and m <= 50.0 else ("far" if m > 50.0 else ""))
		if band == "":
			continue
		tally[band][0] += 1
		tally[band][1] += 1 if str(s[3]) == "goal" else 0
	var rate := {}
	for k in tally:
		_check(int(tally[k][0]) >= 40, "Enough set shots from %s to compare (%d)" % [k, int(tally[k][0])])
		rate[k] = float(tally[k][1]) / maxf(1.0, float(tally[k][0]))
	_check(BalanceGate.held(rate["near"] > rate["mid"] + 0.15 and rate["mid"] > rate["far"] + 0.10, "set shots: conversion falls with distance"),
			"Set shots from 20-30 m convert more than 40-50 m, and those more than 50+ m (%s)" % str(rate))


## Over 30 seeded matches the set-shot share of shots sits near real AFL, about
## 55% of shots (row 77; SET_SHOT_EVIDENCE.md). SET_SHARE_ON is a different number,
## the share of marks inside 50 that go back and kick, so it is not the aim here.
func _test_set_share_near_real() -> void:
	var res := _play()
	var n := 0
	var set_n := 0
	for s in res["shots"]:
		n += 1
		set_n += int(s[1])
	_check(n > MATCHES * 30, "Shots were played (%d)" % n)
	var share := float(set_n) / maxf(1.0, float(n))
	var aim := 0.55
	_check(BalanceGate.held(absf(share - aim) < 0.04, "set shots: share near real"), "The set-shot share sits near %.2f (%.3f)" % [aim, share])


## T2.24: a mark that goes back for a set shot names its band, and the oval
## stands that mark at the band's metres from the middle of the goal line, so
## the kick is taken from where the coach's call said he marked.
func _test_set_shot_mark_names_its_spot() -> void:
	var sim := _sim(2)
	var r: Dictionary = sim.run()
	var ev: Array = r["events"]
	var keys := {}
	for b in MatchSim.SET_BANDS_ON:
		keys[str(b["key"])] = float(b["metres"])
	var n := 0
	for i in range(1, ev.size()):
		var e: Dictionary = ev[i]
		if bool(e.get("set", false)) and not e.has("from_free") and str((ev[i - 1] as Dictionary).get("kind", "")) == "mark":
			n += 1
			_check(keys.has(str((ev[i - 1] as Dictionary).get("band", ""))),
					"Event %d: the set shot's mark names its band (%s)" % [i - 1, str(ev[i - 1])])
	_check(n > 0, "Some set shots from a mark were played (%d)" % n)
	var md := MatchDirector.new()
	for side in range(2):
		for key in keys:
			for lean in [-1.0, 1.0]:
				var at: Vector2 = md._set_spot(side, key, lean)
				var goal := Vector2(MatchMotion.GOAL_X * (1.0 if side == 0 else -1.0), 0.0)
				_check(absf(at.distance_to(goal) - float(keys[key])) < 0.01,
						"Side %d %s: the oval marks him %.1f m out, the band says %.0f m" % [side, key, at.distance_to(goal), keys[key]])
				_check(absf(at.x) < absf(goal.x), "Side %d %s: marked in front of the goal line" % [side, key])
