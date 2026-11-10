extends SceneTree
## godot --headless --path . --script tests/run_league_news_tests.gd
## The AFL knowledge layer (row 76, T5.Q11d): the premiership item in the news
## feed carries one sentence of the club's flag history, computed from the
## save's honour roll and the sourced pre-career flags (data/club_premierships.csv).
## Seeded by design: SUITE_SEED pins the career.

var _state: Node
var _db: Node
var _ln: GDScript
var _nf: GDScript
var _ch: GDScript
var _cs: GDScript
const SUITE_SEED := 2027
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
	_ch = load("res://scripts/core/ClubHistory.gd")
	_cs = load("res://scripts/state/ClubStories.gd")
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://test_league_news.save"
	_state.settings_path = "user://test_league_news.cfg"
	_state.delete_saved_career()
	_t("_test_flag_history")
	_t("_test_premiers_line")
	_t("_test_front_page")
	_t("_test_season_seeded")
	_state.delete_saved_career()
	print(Ran.line("League news", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


func _roll(rows: Array) -> Array:
	var out := []
	for r in rows:
		out.append({"year": r[0], "premier": r[1], "runner_up": r[2]})
	return out


func _test_flag_history() -> void:
	_ch.use({"AAA": {"years": [1990, 2015], "comps": {}, "also": {}, "none": false},
			"BBB": {"years": [2024, 2025], "comps": {}, "also": {}, "none": false},
			"FIT": {"years": [], "comps": {}, "also": {"Fitzroy": [1944]}, "none": true},
			"NON": {"years": [], "comps": {}, "also": {}, "none": true}})
	var y := 2030
	var cases := [
		# Known to have none, before and during the save: the first ever.
		["NON", [], "The club's first premiership."],
		["NON", [[2028, "X", "NON"]], "The club's first premiership."],
		# Flags it carries from another club are not its own.
		["FIT", [], "The club's first premiership."],
		# Not on record: nothing is said, never "first ever".
		["ZZZ", [], ""],
		["AAA", [[2029, "AAA", "X"]], "Back-to-back flags."],
		["AAA", [[2028, "AAA", "X"], [2029, "AAA", "X"]], "Three flags in a row."],
		# The run reads the csv before the save and the honour roll after it: 2024 to 2030 is seven.
		["BBB", [[2026, "BBB", "X"], [2027, "BBB", "X"], [2028, "BBB", "X"], [2029, "BBB", "X"]], "Seven flags in a row."],
		# 2015 to 2030: the wait is 15 years, over DROUGHT_YEARS.
		["AAA", [[2026, "X", "Y"]], "Their first flag since 2015, a 15-year wait."],
		# A flag 5 years ago: not a drought, nothing to say.
		["AAA", [[2025, "AAA", "X"], [2029, "X", "Y"]], ""],
		# A lost Grand Final is not a flag.
		["AAA", [[2029, "X", "AAA"]], "Their first flag since 2015, a 15-year wait."],
		# This season's own entry is already on the roll and never counts.
		["AAA", [[2029, "X", "Y"], [2030, "AAA", "X"]], "Their first flag since 2015, a 15-year wait."],
	]
	var bad := []
	for c in cases:
		var got: String = _ln.flag_history(str(c[0]), y, _roll(c[1]))
		if got != str(c[2]):
			bad.append("%s %s -> '%s'" % [c[0], str(c[1]), got])
	_check(bad.is_empty(), "Every flag-history sentence is the true one (%s)" % " | ".join(PackedStringArray(bad)))
	# The csv's flags count only before the save: a save that began in 2026 owns 2026 on.
	_check(_ln.flag_history("AAA", y, _roll([[2015, "X", "Y"], [2029, "X", "Y"]])) == "Their first flag since 1990, a 40-year wait.",
			"A csv flag in a season the save played says otherwise is not counted")
	_check(_ln.flag_history("AAA", 2025, _roll([])) == "Their first flag since 2015, a 10-year wait.", "Ten years is a drought")
	_check(_ln.flag_history("AAA", 2024, _roll([])) == "", "Nine years is not a drought")
	_ch.reload()


func _test_premiers_line() -> void:
	_ch.use({"AAA": {"years": [1990], "comps": {}, "also": {}, "none": false}})
	var base := "%s are the 2030 premiers." % _db.club_name("AAA")
	_check(_ln.premiers_line("AAA", 2030, []) == base + " Their first flag since 1990, a 40-year wait.",
			"One sentence of history follows (%s)" % _ln.premiers_line("AAA", 2030, []))
	_check(_ln.premiers_line("AAA", 2030, _roll([[2027, "AAA", "X"]])) == base, "Nothing notable: the line stands alone")
	_ch.reload()


func _test_front_page() -> void:
	var stk: String = _db.club_name("STK")
	var with_history := {"year": 2027, "when": "Grand Final", "kind": "premiers",
			"text": "%s are the 2027 premiers. Their first flag since 1966, a 61-year wait." % stk}
	var plain := {"year": 2027, "when": "Grand Final", "kind": "premiers", "text": "%s are the 2027 premiers." % stk}
	var s: Dictionary = _nf.story(with_history, "MEL")
	_check(str(s["headline"]) == "%s are the 2027 premiers" % stk, "The headline is unchanged (%s)" % s["headline"])
	_check(str(s["standfirst"]) == "Their first flag since 1966, a 61-year wait.", "The history is the standfirst (%s)" % s["standfirst"])
	_check(str(s["club"]) == "STK", "In the premiers' colours (%s)" % s["club"])
	var p: Dictionary = _nf.story(plain, "MEL")
	_check(str(p["standfirst"]) == "The flag is theirs." and str(p["headline"]) == str(s["headline"]),
			"Without history the story is exactly as before (%s)" % p["standfirst"])
	var page: Dictionary = _nf.build([with_history], "MEL")
	_check(str(page["lead"]["kind"]) == "premiers" and _nf.all_stories(page).size() == 1,
			"The premiership leads, once: no second item answers the same question")


## Plays the seeded season to its end.
func _play() -> Dictionary:
	_state.replay_seed = SUITE_SEED
	_state.reset()
	_state.career_seed = SUITE_SEED
	_state.replay_seed = SUITE_SEED
	_state.start_season("MEL", _db.club_list("MEL"))
	_state.tutorials = false
	var guard := 0
	while not _state.season.is_season_over() and guard < 40:
		_state.advance()
		guard += 1
	var scores := []
	for rnd in _state.season.results:
		for res in rnd:
			scores.append("%s %s %s" % [res["home"], res["away"], res["score"]])
	var prem := ""
	var others := []
	for it in _state.news:
		if str(it["kind"]) == "premiers":
			prem = str(it["text"])
		else:
			others.append(str(it["text"]))
	return {"scores": scores, "premier": str(_state.premier()), "prem": prem, "others": others,
			"year": int(_state.season_year), "roll": _state.honour_roll.duplicate(true)}


## The expected sentence, worked out here from the csv and the roll on their own.
func _expected(code: String, year: int, roll: Array) -> String:
	var flags := {}
	var save_from := year
	for h in roll:
		if int(h["year"]) < year:
			save_from = mini(save_from, int(h["year"]))
			if str(h["premier"]) == code:
				flags[int(h["year"])] = true
	var rec: Dictionary = _ch.table().get(code, {})
	for y in rec.get("years", []):
		if int(y) < save_from:
			flags[int(y)] = true
	if flags.is_empty():
		return "The club's first premiership." if not rec.is_empty() or _ch.is_new_club(code) else ""
	if flags.has(year - 1):
		var n := 1
		while flags.has(year - n):
			n += 1
		return "Back-to-back flags." if n == 2 else "%s flags in a row." % str(_cs.RUN_WORDS.get(n, str(n)))
	var last := 0
	for y in flags:
		last = maxi(last, int(y))
	# "an 11-year wait", "an 18-year wait", "an 80-year wait": by ear, worked out here on its own.
	var n := year - last
	var art := "an" if n == 8 or n == 11 or n == 18 or (n >= 80 and n <= 89) else "a"
	return "Their first flag since %d, %s %d-year wait." % [last, art, n] if year - last >= _cs.DROUGHT_YEARS else ""


func _test_season_seeded() -> void:
	var on := _play()
	_check(on["premier"] != "" and on["scores"].size() > 0, "The season plays to a premier (%s)" % on["premier"])
	var base := "%s are the %d premiers." % [_db.club_name(str(on["premier"])), int(on["year"])]
	var want := _expected(str(on["premier"]), int(on["year"]), on["roll"])
	_check(on["prem"] == (base if want == "" else base + " " + want), "The premiership item is true (%s, expected '%s')" % [on["prem"], want])
	print("  league news: seed %d, %d premiers: %s" % [SUITE_SEED, int(on["year"]), on["prem"]])
	# Every club, as if it had won this flag: the sentence matches the csv worked out by hand.
	var bad := []
	for code in _db.club_order:
		var got: String = _ln.flag_history(str(code), int(on["year"]), on["roll"])
		if got != _expected(str(code), int(on["year"]), on["roll"]):
			bad.append("%s: %s" % [code, got])
	_check(bad.is_empty(), "Each club's history line agrees with the csv (%s)" % " | ".join(PackedStringArray(bad)))
