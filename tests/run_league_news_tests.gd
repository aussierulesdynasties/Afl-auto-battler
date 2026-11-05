extends SceneTree
## godot --headless --path . --script tests/run_league_news_tests.gd
## The league news layer (row 76, T5.Q11d, switch "league_news"): winning runs
## and a new club on top of the ladder, told only from the save's own results,
## shown on the existing news front page, and never touching the sim.
## Seeded by design: SUITE_SEED pins both careers, so the switch-off and
## switch-on arms play the same matches.

var _state: Node
var _db: Node
var _ln: GDScript
var _nf: GDScript
var _features: GDScript
const SUITE_SEED := 2027
const ROUNDS := 14
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _run() -> void:
	await process_frame
	_ln = load("res://scripts/state/LeagueNews.gd")
	_nf = load("res://scripts/ui/NewsFront.gd")
	_features = load("res://scripts/core/Features.gd")
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://test_league_news.save"
	_state.settings_path = "user://test_league_news.cfg"
	_state.delete_saved_career()
	_t("_test_streaks")
	_t("_test_ladder")
	_t("_test_front_page")
	_t("_test_season_seeded")
	_features.clear("league_news")
	_state.delete_saved_career()
	print(Ran.line("League news", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


func _res(home: String, away: String, hs: int, as_: int, round_n: int) -> Dictionary:
	return {"home": home, "away": away, "score": [hs, as_], "label": "Round %d" % round_n}


## GEE beat a different club each week for `wins` rounds, then lose to `loser_to`
## in the last round when it is set. Everyone else plays out a draw.
func _geelong_run(wins: int, loser_to := "") -> Array:
	var opps := ["SYD", "HAW", "COL", "CAR", "ESS", "RIC", "MEL", "ADE", "PAD", "WCE", "FRE", "BRL"]
	var rounds := []
	for i in range(wins):
		rounds.append([_res("GEE", opps[i % opps.size()], 90, 60, i + 1)])
	if loser_to != "":
		rounds.append([_res("GEE", loser_to, 60, 70, wins + 1)])
	return rounds


func _test_streaks() -> void:
	var gee: String = _db.club_name("GEE")
	_check(_ln.streak_lines(_geelong_run(4)).is_empty(), "Four straight is not news yet")
	var five: Array = _ln.streak_lines(_geelong_run(5))
	_check(five.size() == 1 and str(five[0]) == "%s have won 5 in a row after beating %s." % [gee, _db.club_name("ESS")],
			"The fifth straight win makes the news, naming the side beaten (%s)" % [five])
	_check(_ln.streak_lines(_geelong_run(6)).is_empty(), "Six straight is not told again")
	_check(_ln.streak_lines(_geelong_run(7)).size() == 1, "Seven straight is")
	var ended: Array = _ln.streak_lines(_geelong_run(6, "COL"))
	_check(ended.size() == 1 and str(ended[0]) == "%s's run of 6 straight wins ended against %s." % [gee, _db.club_name("COL")],
			"A run of six ending is news (%s)" % [ended])
	_check(_ln.streak_lines(_geelong_run(4, "COL")).is_empty(), "A run of four ending is not")
	# The loser of the fifth win has a run of none: only Geelong is named.
	var run: Array = _ln.club_run(_geelong_run(5), "GEE")
	_check(run.size() == 5 and _ln.wins_in_a_row(run, run.size()) == 5, "The run is read from the stored results (%d)" % run.size())


func _test_ladder() -> void:
	# GEE and SYD both 2-0 after Round 2, GEE top on percentage (150.0 to 108.5);
	# SYD's 110-point win in Round 3 takes them top (171.2 to 135.9).
	var r1 := [_res("GEE", "COL", 100, 50, 1), _res("SYD", "HAW", 80, 70, 1)]
	var r2 := [_res("GEE", "HAW", 80, 70, 2), _res("SYD", "COL", 61, 60, 2)]
	var r3 := [_res("SYD", "COL", 150, 40, 3), _res("GEE", "HAW", 51, 50, 3)]
	_check(_ln.ladder_line([r1, r2]) == "", "No ladder news before Round 3")
	var line: String = _ln.ladder_line([r1, r2, r3])
	var top: Array = _ln.table([r1, r2, r3])
	var before: Array = _ln.table([r1, r2])
	_check(str(before[0]["code"]) != str(top[0]["code"]), "The test round changes the top of the ladder (%s to %s)" % [before[0]["code"], top[0]["code"]])
	_check(line == "%s are on top of the ladder after Round 3: 3 wins and a percentage of %.1f." % [
			_db.club_name(str(top[0]["code"])), float(top[0]["pct"])], "A new leader is told with his wins and percentage (%s)" % line)
	var r3b := [_res("SYD", "COL", 60, 50, 3), _res("GEE", "HAW", 60, 50, 3)]
	_check(str(top[0]["code"]) == "SYD" and str(_ln.table([r1, r2, r3b])[0]["code"]) == "GEE",
			"The fixture is as built: SYD top after Round 3, GEE when they stay ahead")
	_check(_ln.ladder_line([r1, r2, r3b]) == "", "The same club staying top is not news")


func _test_front_page() -> void:
	var gee: String = _db.club_name("GEE")
	var items := [
		{"year": 2027, "when": "Round 7", "kind": "ladder", "text": "%s are on top of the ladder after Round 7: 6 wins and a percentage of 131.2." % gee},
		{"year": 2027, "when": "Round 7", "kind": "streak", "text": "%s have won 7 in a row after beating %s." % [gee, _db.club_name("SYD")]},
		{"year": 2027, "when": "Round 7", "kind": "streak", "text": "%s's run of 5 straight wins ended against %s." % [_db.club_name("CAR"), _db.club_name("COL")]},
	]
	var heads := {}
	for it in items:
		var s: Dictionary = _nf.story(it, "MEL")
		heads[str(it["text"])] = s
		_check(str(s["club"]) != "", "The story is in its club's colours (%s)" % s["headline"])
		# A brief row or an earlier line takes club ink only for a named story.
		_check(str(s["name"]) == _db.club_name(str(s["club"])), "Its brief line is in the club's ink too (%s)" % s["headline"])
	_check(str(heads[items[0]["text"]]["headline"]) == "%s go top" % gee, "Ladder headline (%s)" % heads[items[0]["text"]]["headline"])
	_check(str(heads[items[1]["text"]]["headline"]) == "%s make it seven straight" % gee, "Streak headline (%s)" % heads[items[1]["text"]]["headline"])
	_check(str(heads[items[2]["text"]]["headline"]) == "%s's winning run ends at five" % _db.club_name("CAR"), "End-of-run headline (%s)" % heads[items[2]["text"]]["headline"])
	var page: Dictionary = _nf.build(items, "MEL")
	_check(_nf.all_stories(page).size() == items.size(), "Every new item is on the front page once")
	_check(str(page["lead"]["kind"]) == "ladder", "A new leader leads a quiet round (%s)" % page["lead"]["kind"])


## Plays the same seeded career twice: with the switch off and on.
func _play(on: bool) -> Dictionary:
	_features.set_on("league_news", on)
	_state.replay_seed = SUITE_SEED
	_state.reset()
	_state.replay_seed = SUITE_SEED
	_state.start_season("MEL", _db.club_list("MEL"))
	_state.tutorials = false
	for i in range(ROUNDS):
		_state.advance()
	var scores := []
	for rnd in _state.season.results:
		for res in rnd:
			scores.append("%s %s %s" % [res["home"], res["away"], res["score"]])
	var ours := []
	for it in _state.news:
		if str(it["kind"]) in ["streak", "ladder"]:
			ours.append(it)
	var others := []
	for it in _state.news:
		if not str(it["kind"]) in ["streak", "ladder"]:
			others.append(str(it["text"]))
	var lad := []
	for row in _state.season.ladder_sorted():
		lad.append("%s %d %.3f" % [row["code"], int(row["pts"]), float(row["pct"])])
	return {"scores": scores, "ours": ours, "others": others, "ladder": lad,
			"results": _state.season.results.duplicate(true), "top": str(_state.season.ladder_sorted()[0]["code"])}


func _round_of(when: String) -> int:
	return int(when.replace("Round ", ""))


func _test_season_seeded() -> void:
	var off := _play(false)
	var on := _play(true)
	_check(off["scores"].size() == on["scores"].size() and off["scores"].size() >= ROUNDS * 8,
			"Both arms played %d rounds (%d and %d results)" % [ROUNDS, off["scores"].size(), on["scores"].size()])
	_check(off["scores"] == on["scores"], "Same seed, same results with the switch on: the sim is untouched")
	_check(off["ladder"] == on["ladder"], "Same ladder with the switch on")
	# The feed keeps its newest MAX_NEWS items, so the new items push the oldest
	# out of a full feed: everything kept is the same, in the same order.
	var kept: Array = (off["others"] as Array).slice(0, (on["others"] as Array).size())
	_check(kept == on["others"] and (on["others"].size() + on["ours"].size() == off["others"].size() or off["others"].size() < _state.MAX_NEWS),
			"The rest of the news feed is unchanged with the switch on (%d and %d items, the feed holds %d)" % [off["others"].size(), on["others"].size(), _state.MAX_NEWS])
	if kept != on["others"]:
		for i in range(kept.size()):
			if kept[i] != on["others"][i]:
				print("  first difference at %d:\n    off: %s\n    on:  %s" % [i, off["others"][i], on["others"][i]])
				break
	_check((off["ours"] as Array).is_empty(), "Switch off: no new items are written")
	var ours: Array = on["ours"]
	_check(not ours.is_empty(), "Switch on: items appear (%d in %d rounds)" % [ours.size(), ROUNDS])
	var results: Array = on["results"]
	_check(str(_ln.table(results)[0]["code"]) == str(on["top"]), "The news table agrees with the game's ladder at the top (%s)" % on["top"])
	var ladders := 0
	var streaks := 0
	for it in ours:
		var text := str(it["text"])
		var r := _round_of(str(it["when"]))
		_check(r >= 1 and r <= results.size(), "The item is dated to a played round (%s)" % it["when"])
		if r < 1 or r > results.size():
			continue
		var upto := results.slice(0, r)
		if str(it["kind"]) == "ladder":
			ladders += 1
			var now: Array = _ln.table(upto)
			var was: Array = _ln.table(results.slice(0, r - 1))
			var club: String = _db.club_name(str(now[0]["code"]))
			_check(text.begins_with(club + " are on top") and str(now[0]["code"]) != str(was[0]["code"]) and r >= 3,
					"Ladder item is true for %s: %s" % [it["when"], text])
		else:
			streaks += 1
			var m := RegEx.create_from_string("^(.+?)(?: have won (\\d+) in a row|'s run of (\\d+) straight)").search(text)
			_check(m != null, "Streak item reads as a run (%s)" % text)
			if m == null:
				continue
			var code := ""
			for c in _db.clubs:
				if _db.club_name(str(c)) == m.get_string(1):
					code = str(c)
			var run: Array = _ln.club_run(upto, code)
			if m.get_string(2) != "":
				_check(_ln.wins_in_a_row(run, run.size()) == int(m.get_string(2)), "Win run is true for %s: %s" % [it["when"], text])
			else:
				_check(str(run[run.size() - 1]["r"]) != "W" and _ln.wins_in_a_row(run, run.size() - 1) == int(m.get_string(3)),
						"Ended run is true for %s: %s" % [it["when"], text])
	print("  league news: %d ladder, %d streak items in %d rounds (seed %d)" % [ladders, streaks, ROUNDS, SUITE_SEED])
	for it in ours:
		print("    %s | %s" % [it["when"], it["text"]])
