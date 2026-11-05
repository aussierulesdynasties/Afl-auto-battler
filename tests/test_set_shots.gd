extends RefCounted
## Set shots (row 77, director ruling T8.Q9): with the set_shots switch on, a
## set shot converts by its distance (MatchSim.SET_BANDS_ON, the real AFL rates)
## so a closer one goes in more often than a longer one, the set-shot share of
## shots rises toward the real 55%, and total scoring holds. Off, the old bands
## and share stand. Run through tests/run_set_shots_tests.gd. Seeded by design:
## every sim takes an explicit match seed.

var failures: Array[String] = []
var checks := 0

const CLUBS := [["FRE", "MEL"], ["GEE", "COL"], ["SYD", "CAR"], ["BRL", "ESS"], ["HAW", "ADE"], ["WBD", "GWS"]]
const MATCHES := 30


func run() -> void:
	failures.clear()
	checks = 0
	GameDB.reload()
	_t("_test_off_keeps_the_old_bands")
	_t("_test_shot_log_matches_the_shots")
	_t("_test_closer_set_shot_converts_more")
	_t("_test_switch_raises_set_share")
	Features.clear("set_shots")
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


## Plays MATCHES seeded matches with the switch as given: pooled shot_log rows
## and the total score.
func _play(on: bool) -> Dictionary:
	Features.set_on("set_shots", on)
	var shots := []
	var points := 0
	for i in range(MATCHES):
		var sim := _sim(i)
		var r: Dictionary = sim.run()
		shots.append_array(sim.shot_log)
		points += int(r["score"][0]) + int(r["score"][1])
	return {"shots": shots, "points": points}


func _test_off_keeps_the_old_bands() -> void:
	Features.set_on("set_shots", false)
	var sim := _sim(0)
	_check(not sim.set_shots_on and is_equal_approx(sim.set_share(), MatchSim.SET_SHOT_SHARE),
			"Off, a mark inside 50 is a set shot at the old share (%.2f)" % sim.set_share())
	var old := MatchSim.set_bands(MatchSim.SET_REF)
	_check(old.size() == MatchSim.SET_BANDS.size(), "Off, the old five bands")
	for i in range(old.size()):
		_check(is_equal_approx(float(old[i]["goal"]), clampf(float(MatchSim.SET_BANDS[i]["acc"]), 0.03, 0.97)),
				"Off, band %s converts at its old rate" % str(old[i]["key"]))
	Features.set_on("set_shots", true)
	var on := _sim(0)
	_check(on.set_shots_on and on.set_share() > MatchSim.SET_SHOT_SHARE,
			"On, more marks inside 50 go back for the kick (%.2f)" % on.set_share())


## The balance harness reads MatchSim.shot_log: one row per counted shot.
func _test_shot_log_matches_the_shots() -> void:
	Features.set_on("set_shots", false)
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
	for b in MatchSim.set_bands(MatchSim.SET_REF, true):
		by[str(b["key"])] = float(b["goal"])
	_check(by["close"] > by["front"] and by["front"] > by["angle"] and by["angle"] > by["long"],
			"From 25, 35, 45 then 55 metres straight in front, the chance falls (%s)" % str(by))
	var res := _play(true)
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
	_check(rate["near"] > rate["mid"] + 0.15 and rate["mid"] > rate["far"] + 0.10,
			"Set shots from 20-30 m convert more than 40-50 m, and those more than 50+ m (%s)" % str(rate))


## On the same seeds, the switch raises the set-shot share of shots and holds
## the total score.
func _test_switch_raises_set_share() -> void:
	var share := {}
	var points := {}
	for on in [false, true]:
		var res := _play(on)
		var n := 0
		var set_n := 0
		for s in res["shots"]:
			n += 1
			set_n += int(s[1])
		_check(n > MATCHES * 30, "Shots were played with the switch %s (%d)" % ["on" if on else "off", n])
		share[on] = float(set_n) / maxf(1.0, float(n))
		points[on] = float(res["points"]) / (2.0 * MATCHES)
	_check(share[true] > share[false] + 0.03 and share[true] > 0.52 and share[true] < 0.60,
			"The switch raises the set-shot share toward 55%% (off %.3f, on %.3f)" % [share[false], share[true]])
	_check(absf(points[true] - points[false]) < 6.0,
			"The score a team holds within 6 points (off %.1f, on %.1f)" % [points[false], points[true]])
