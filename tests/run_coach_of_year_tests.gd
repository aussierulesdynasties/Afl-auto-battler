extends SceneTree
## godot --headless --path . --script tests/run_coach_of_year_tests.gd
## Coach of the Year (CoachOfYear.gd; director, 2026-11-13): given the week the
## home-and-away season ends, before a final is played, and never changed by
## the finals; drawn by odds, never certain; on the winner's career record.
## The seeded sample plays many seasons of a simple ladder model (club
## strengths that drift year to year, each match won by the stronger side
## more often) so the award's rates are measured over hundreds of seasons in
## seconds; one real season is played through GameState for the timing.
## Classes are reached through load() and autoload nodes (a --script runner
## compiles before the autoloads exist).

var _state: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []

const COY := preload("res://scripts/sim/CoachOfYear.gd")
const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 2026
const SAMPLE_SEASONS := 600
const CLUBS := 18
const FINALISTS := 10
const ROUNDS := 23


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://test_coach_of_year.save"
	_state.settings_path = "user://test_coach_of_year.cfg"
	_state.replay_seed = SUITE_SEED

	await _t("_test_rule_cases")
	await _t("_test_never_certain")
	await _t("_test_streak_and_line")
	await _t("_test_seeded_sample")
	await _t("_test_played_season")

	print(Ran.line("Coach of the Year", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


# ---------------------------------------------------------------------------
# The rule

func _facts(ladder: int, last := 9, expect := 9, streak := 3, goal := false) -> Dictionary:
	return {"ladder": ladder, "last": last, "expect": expect, "streak": streak, "goal_met": goal}


func _test_rule_cases() -> void:
	# Bottom four to top four is the model case.
	_check(COY.bottom_to_top(_facts(3, 16), CLUBS), "16th to 3rd is bottom four to top four")
	_check(not COY.bottom_to_top(_facts(5, 17), CLUBS), "17th to 5th is not top four")
	_check(not COY.bottom_to_top(_facts(2, 14), CLUBS), "14th last year is not the bottom four")
	_check(not COY.bottom_to_top(_facts(2, 0), CLUBS), "No finish last year: no climb claimed")
	# A long run counts only into the finals.
	_check(COY.long_streak(_facts(6, 9, 9, 10), FINALISTS), "A ten-game run into the finals counts")
	_check(not COY.long_streak(_facts(12, 9, 9, 11), FINALISTS), "An eleven-game run that misses the finals does not")
	_check(not COY.long_streak(_facts(6, 9, 9, COY.STREAK_LONG - 1), FINALISTS), "A run short of the mark does not")
	# The model case outscores a minor premier who did what was expected.
	var riser := COY.score(_facts(3, 16, 12), CLUBS, FINALISTS)
	var top := COY.score(_facts(1, 2, 1), CLUBS, FINALISTS)
	_check(riser > top, "Bottom four to top four outscores an expected minor premiership (%.2f vs %.2f)" % [riser, top])
	_check(COY.score(_facts(11, 15, 15), CLUBS, FINALISTS) < COY.score(_facts(8, 9, 9), CLUBS, FINALISTS),
			"Missing the finals costs more than an over-achieving climb earns")
	# Finals results are not an input: the facts hold the home-and-away season only.
	var facts := {"MEL": _facts(1, 4, 3), "WB": _facts(4, 17, 14), "STK": _facts(6, 8, 8, 10)}
	var a := COY.pick(facts, CLUBS, FINALISTS, 77)
	_check(a == COY.pick(facts.duplicate(true), CLUBS, FINALISTS, 77), "The same season names the same coach")


func _test_never_certain() -> void:
	# A season with one standout case: the likely winner, never the sure one.
	var facts := {}
	for i in range(CLUBS):
		facts["C%02d" % i] = _facts(i + 1, i + 1, i + 1)
	facts["C02"] = _facts(3, 17, 15)
	var o := COY.odds(facts, CLUBS, FINALISTS)
	_check(float(o["C02"]) > 0.5 and float(o["C02"]) <= 1.0 - COY.JUDGES_SPREAD * 0.9,
			"The model case is likely but not certain (%.0f%%)" % (100.0 * float(o["C02"])))
	_check(float(o["C00"]) > 0.0, "The minor premier keeps a chance (%.0f%%)" % (100.0 * float(o["C00"])))
	var tot := 0.0
	for k in o:
		tot += float(o[k])
	_check(absf(tot - 1.0) < 1e-6, "The chances add to one")


func _test_streak_and_line() -> void:
	var w := func(h: String, a: String, hs: int, as_: int) -> Dictionary:
		return {"home": h, "away": a, "score": [hs, as_]}
	var rounds := [[w.call("MEL", "WB", 80, 60)], [w.call("WB", "MEL", 50, 70)], [w.call("MEL", "STK", 70, 70)],
			[w.call("MEL", "WB", 90, 60)], [w.call("STK", "MEL", 60, 61)], [w.call("MEL", "STK", 99, 40)]]
	_check(COY.longest_streak(rounds, "MEL") == 3, "A draw ends a run; the longest is kept (%d)" % COY.longest_streak(rounds, "MEL"))
	var final_ := [{"home": "MEL", "away": "WB", "score": [90, 10], "tag": "QF1"}]
	_check(COY.longest_streak(rounds + [final_], "MEL") == 3, "A final never adds to the run")
	var l: String = COY.line(_facts(3, 16), "Western Bulldogs", CLUBS, FINALISTS)
	_check(l == "Took Western Bulldogs from 16th last year to 3rd.", "The model case's line: " + l)
	l = COY.line(_facts(6, 8, 8, 10), "St Kilda", CLUBS, FINALISTS)
	_check(l == "10 straight wins carried St Kilda into the finals.", "The streak's line: " + l)
	l = COY.line(_facts(1, 1, 1), "Melbourne", CLUBS, FINALISTS)
	_check(l == "Melbourne finished on top of the ladder.", "The minor premier's line: " + l)
	for f in [_facts(5, 6, 11), _facts(5, 9, 4), _facts(5, 5, 5)]:
		l = COY.line(f, "Fremantle", CLUBS, FINALISTS)
		_check(not l.contains("score") and not l.contains("%") and l.ends_with("."), "One plain line: " + l)
	# Every line gives a reason (director, 2026-11-13: "add reasoning why he was the best coach of the year").
	l = COY.line(_facts(5, 5, 5, 3, true), "Fremantle", CLUBS, FINALISTS)
	_check(l == "Fremantle finished 5th and met the board's goal.", "The board's goal as the reason: " + l)
	l = COY.line(_facts(5, 5, 5, 7), "Fremantle", CLUBS, FINALISTS)
	_check(l == "Fremantle finished 5th, with a run of 7 straight wins.", "A winning run as the reason: " + l)


# ---------------------------------------------------------------------------
# The seeded sample

## Many seasons of a simple ladder: each club's strength drifts year to year,
## its list ranks on paper by strength with a little noise, and each match goes
## to the stronger side more often, spread as real AFL ladders are (the top
## side about 19 wins of 23, the bottom about 4; 10-game runs about once a
## season). Returns the award's rates by case.
func _sample(seasons: int, seed_: int) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_
	var strength := []
	for i in range(CLUBS):
		strength.append(rng.randfn(0.0, 1.0))
	var last := {}
	var out := {"seasons": 0, "minor": [0, 0], "b2t": [0, 0], "streak": [0, 0],
			"streak_not_minor": [0, 0], "minor_with_streak": [0, 0], "minor_plain": [0, 0],
			"non_finalist": 0, "winner_ladder": {}}
	for year in range(seasons + 1):
		for i in range(CLUBS):
			strength[i] = 0.6 * float(strength[i]) + rng.randfn(0.0, 0.8)
		var paper := []
		for i in range(CLUBS):
			paper.append([i, float(strength[i]) + rng.randfn(0.0, 0.3)])
		paper.sort_custom(func(a, b): return float(a[1]) > float(b[1]))
		var expect := {}
		for r in range(CLUBS):
			expect[int(paper[r][0])] = r + 1
		var wins := []
		var margin := []
		var run := []
		var best := []
		for i in range(CLUBS):
			wins.append(0)
			margin.append(0.0)
			run.append(0)
			best.append(0)
		for _r in range(ROUNDS):
			var order := range(CLUBS)
			for k in range(CLUBS - 1, 0, -1):
				var j := rng.randi_range(0, k)
				var sw = order[k]
				order[k] = order[j]
				order[j] = sw
			for m in range(0, CLUBS, 2):
				var a := int(order[m])
				var b := int(order[m + 1])
				var mg := 14.0 * (float(strength[a]) - float(strength[b])) + rng.randfn(0.0, 32.0)
				margin[a] = float(margin[a]) + mg
				margin[b] = float(margin[b]) - mg
				var winner := a if mg > 0.0 else b
				var loser := b if mg > 0.0 else a
				wins[winner] = int(wins[winner]) + 1
				run[winner] = int(run[winner]) + 1
				best[winner] = maxi(int(best[winner]), int(run[winner]))
				run[loser] = 0
		var table := range(CLUBS)
		table.sort_custom(func(a, b):
			if int(wins[a]) != int(wins[b]):
				return int(wins[a]) > int(wins[b])
			return float(margin[a]) > float(margin[b]))
		var facts := {}
		for pos in range(CLUBS):
			var i := int(table[pos])
			var goal := ClubLife.board_goal(int(expect[i]), int(last.get(i, 0)), CLUBS, FINALISTS)
			facts["C%02d" % i] = {"ladder": pos + 1, "last": int(last.get(i, 0)), "expect": int(expect[i]),
					"streak": int(best[i]), "goal_met": ClubLife.goal_met(goal, pos + 1, int(wins[i]), CLUBS)}
		var had_last := not last.is_empty()
		last = {}
		for pos in range(CLUBS):
			last[int(table[pos])] = pos + 1
		if not had_last:
			continue   # the first season has no last year to climb from
		out["seasons"] = int(out["seasons"]) + 1
		var won := COY.pick(facts, CLUBS, FINALISTS, hash(["coty-sample", seed_, year]))
		var wf: Dictionary = facts[won]
		var wl: Dictionary = out["winner_ladder"]
		wl[int(wf["ladder"])] = int(wl.get(int(wf["ladder"]), 0)) + 1
		if int(wf["ladder"]) > FINALISTS:
			out["non_finalist"] = int(out["non_finalist"]) + 1
		for code in facts:
			var f: Dictionary = facts[code]
			var hit := 1 if code == won else 0
			var minor := int(f["ladder"]) == 1
			var streak := COY.long_streak(f, FINALISTS)
			if minor:
				_tally(out, "minor", hit)
				_tally(out, "minor_with_streak" if streak else "minor_plain", hit)
			if COY.bottom_to_top(f, CLUBS):
				_tally(out, "b2t", hit)
			if streak:
				_tally(out, "streak", hit)
				if not minor:
					_tally(out, "streak_not_minor", hit)
	return out


func _tally(out: Dictionary, key: String, hit: int) -> void:
	var t: Array = out[key]
	t[0] = int(t[0]) + hit
	t[1] = int(t[1]) + 1


func _rate(t: Array) -> float:
	return float(t[0]) / float(maxi(1, int(t[1])))


func _test_seeded_sample() -> void:
	var s := _sample(SAMPLE_SEASONS, SUITE_SEED)
	print("Coach of the Year sample, %d seasons:" % int(s["seasons"]))
	for key in ["minor", "minor_plain", "minor_with_streak", "b2t", "streak", "streak_not_minor"]:
		var t: Array = s[key]
		print("  %-18s won %4d of %4d  (%.0f%%)" % [key, int(t[0]), int(t[1]), 100.0 * _rate(t)])
	print("  non-finalist winners: %d; winners by ladder place: %s" % [int(s["non_finalist"]), str(s["winner_ladder"])])
	# "its not always teh coach whose team finishes first (though often, it is)"
	var minor := _rate(s["minor"])
	_check(minor >= 0.30 and minor <= 0.60, "The minor premier's coach wins often, not always (%.0f%%)" % (100.0 * minor))
	# "if a team goes from bottom four to top four, chances are their coach will win"
	var b2t := _rate(s["b2t"])
	_check(int((s["b2t"] as Array)[1]) >= 20, "The sample holds enough bottom-four-to-top-four seasons (%d)" % int((s["b2t"] as Array)[1]))
	_check(b2t >= 0.55 and b2t <= 0.85, "Bottom four to top four: the likely winner (%.0f%%)" % (100.0 * b2t))
	# "if a team goes on a long winning streak to make finals, their coach will win the award most of the time"
	var streak := _rate(s["streak"])
	_check(streak > 0.5 and streak <= 0.85, "A long run into the finals wins most of the time (%.0f%%)" % (100.0 * streak))
	_check(float(int(s["non_finalist"])) / float(int(s["seasons"])) < 0.05, "A coach who missed the finals wins rarely")


# ---------------------------------------------------------------------------
# One real season

func _test_played_season() -> void:
	_state.reset()
	_state.start_season("MEL", _db.club_list("MEL"))
	var guard := 0
	while not _state.season.is_regular_done() and guard < 40:
		_state.advance()
		guard += 1
	var year := int(_state.season_year)
	var list: Array = _state.coach_of_year
	_check(list.size() == 1, "Given the week the home-and-away season ends (%d)" % list.size())
	if list.is_empty():
		return
	var e: Dictionary = (list[0] as Dictionary).duplicate(true)
	_check(int(e["year"]) == year, "For this season")
	var finals_played := 0
	for week in _state.season.finals.get("weeks", []):
		finals_played += (week as Array).size()
	_check(finals_played == 0, "Before a final is played (%d played)" % finals_played)
	_check(str(e["line"]) != "" and str(e["name"]) != "", "A named winner with one line: %s, %s" % [e["name"], e["line"]])
	var news_hit := false
	for n in _state.news:
		if str(n.get("kind", "")) == "award" and str(n.get("text", "")).contains("Coach of the Year"):
			news_hit = true
	_check(news_hit, "It reaches the coach in the news that week")
	if not bool(e["you"]):
		var c: Dictionary = _state.coaches.get(str(e["cid"]), {})
		_check((c.get("coty", []) as Array).has(year), "On the winner's career record")
		_check(load("res://scripts/ui/CoachSheet.gd").coty_line(c) == "Coach of the Year %d" % year,
				"His profile's line names the year")
	else:
		_check(_state.my_coach_of_year_years() == [year], "On your record")
	var reasons: Dictionary = _state.coach_of_year_reasons("" if bool(e["you"]) else str(e["cid"]))
	_check(str(reasons.get(year, "")) == str(e["line"]), "The profile shows why he won it: " + str(e["line"]))
	# The finals change nothing.
	guard = 0
	while not _state.season.is_season_over() and guard < 10:
		_state.advance()
		guard += 1
	_check(_state.season.is_season_over(), "The finals were played")
	_check(_state.coach_of_year.size() == 1 and (_state.coach_of_year[0] as Dictionary) == e,
			"The finals leave the award as it was")
	var roll: Dictionary = _state.honour_roll[-1] if not _state.honour_roll.is_empty() else {}
	_check((roll.get("coach_of_year", []) as Array).size() == 1
			and str((roll["coach_of_year"][0] as Dictionary).get("club", "")) == str(e["club"]),
			"The honour roll keeps the season's Coach of the Year")
	# A save keeps it.
	var st: Dictionary = _state._save_state()
	if not st.is_empty():
		_check(st.has("coach_of_year"), "The save writes it")
