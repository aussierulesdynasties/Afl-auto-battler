extends SceneTree
## godot --headless --path . --script tests/run_league_stories_tests.gd
## The round's league stories (LeagueStories.gd; director 2026-11-10: "use
## procedural stories in the news too to highlight big comebacks, huge margins,
## injury stories etc"). Each trigger fires on the match's facts and stays
## silent without them; the round is capped, biggest first; the same round
## always reads the same; your own result's headline is never said again; the
## stories never change a result; and on a phone a real tap opens a front page
## that shows them.

const Tap := preload("res://tests/tap.gd")
const SUITE_SEED := 2027

var _state: Node
var _router: Node
var _db: Node
var _ls: GDScript
var _nf: GDScript
var _hl: GDScript
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


func _settle(n := 6) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	await process_frame
	_ls = load("res://scripts/core/LeagueStories.gd")
	_nf = load("res://scripts/ui/NewsFront.gd")
	_hl = load("res://scripts/core/Headlines.gd")
	_state = root.get_node("GameState")
	_router = root.get_node("Router")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.event_sheets = false
	_state.save_path = "user://test_league_stories.save"
	_state.settings_path = "user://test_league_stories.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.delete_saved_career()
	_t("_test_bank")
	_t("_test_comeback")
	_t("_test_blown")
	_t("_test_held_on")
	_t("_test_huge")
	_t("_test_close")
	_t("_test_ordinary_silent")
	_t("_test_quarters_must_add_up")
	_t("_test_injury")
	_t("_test_cap")
	_t("_test_determinism")
	_t("_test_own_headline")
	_t("_test_reads_only")
	_t("_test_ladder")
	_t("_test_front_page_item")
	_t("_test_career")
	await _t("_test_phone", [Vector2i(390, 844)])
	_state.delete_saved_career()
	print(Ran.line("League stories", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


# ---------------------------------------------------------------------------
# Building a result
# ---------------------------------------------------------------------------
## A result from each side's [goals, behinds] per quarter. Goals are kicked by
## "<home>_k1" / "<away>_k1" unless `kickers` names them per quarter and side.
func _res(home: String, away: String, hq: Array, aq: Array, kickers := {}) -> Dictionary:
	var qg := []
	var qb := []
	var quarters := []
	var events := []
	var scoring := []
	var sc := [0, 0]
	for q in range(hq.size()):
		qg.append([int(hq[q][0]), int(aq[q][0])])
		qb.append([int(hq[q][1]), int(aq[q][1])])
		quarters.append([int(hq[q][0]) * 6 + int(hq[q][1]), int(aq[q][0]) * 6 + int(aq[q][1])])
		# Alternate the sides' scores through the quarter, goals before behinds.
		var left := [[int(hq[q][0]), int(hq[q][1])], [int(aq[q][0]), int(aq[q][1])]]
		var minute := q * 30 + 1
		while left[0][0] + left[0][1] + left[1][0] + left[1][1] > 0:
			for sd in 2:
				var goal := int(left[sd][0]) > 0
				if not goal and int(left[sd][1]) == 0:
					continue
				if goal:
					left[sd][0] -= 1
					sc[sd] += 6
				else:
					left[sd][1] -= 1
					sc[sd] += 1
				var code: String = home if sd == 0 else away
				var who := str(kickers.get("%d|%d" % [q + 1, sd], "%s_k1" % code))
				events.append({"kind": "goal" if goal else "behind", "side": sd, "q": q + 1, "min": minute,
						"player_id": who, "score": sc.duplicate()})
				scoring.append([q + 1, minute, sd, 1 if goal else 0, who, 0])
				minute += 1
	var g := [0, 0]
	var b := [0, 0]
	for q in range(qg.size()):
		for sd in 2:
			g[sd] += int(qg[q][sd])
			b[sd] += int(qb[q][sd])
	return {"home": home, "away": away, "label": "Round 5", "round": 5,
			"score": [g[0] * 6 + b[0], g[1] * 6 + b[1]], "goals": g, "behinds": b,
			"quarters": quarters, "q_goals": qg, "q_behinds": qb, "scoring": scoring, "events": events,
			"injuries": []}


## A player lookup for the tests: "<code>_k<n>" is a named forward, overall 80.
func _ctx(extra := {}) -> Dictionary:
	var ctx := {"seed": 7, "year": 2027, "my_club": "", "ladder": {}, "injuries": [], "named": {},
			"player": func(id): return {"id": id, "name": "Kicker " + str(id).to_upper(), "overall": 80}}
	ctx.merge(extra, true)
	return ctx


func _one(res: Dictionary, extra := {}) -> Dictionary:
	var out: Array = _ls.round_stories([res], _ctx(extra))
	return out[0] if not out.is_empty() else {}


func _all_text(st: Dictionary) -> String:
	return "" if st.is_empty() else _ls.text(st)


# ---------------------------------------------------------------------------
# The bank
# ---------------------------------------------------------------------------
func _test_bank() -> void:
	var bank: Dictionary = _ls.bank()
	_check(not bank.is_empty(), "the league phrase bank loads")
	var probs: Array = _ls.validate(bank)
	_check(probs.is_empty(), "the league phrase bank is sound: %s" % [probs])
	# The validator catches a bad phrase.
	var bad := {"x": {"slots": ["a"], "news": ["{a} and {b}"]}}
	_check(not (_ls.validate(bad) as Array).is_empty(), "an undeclared slot is caught")
	# No phrase says what the headline over your own result says (Headlines.gd).
	for a in bank:
		for ph in bank[a]["news"]:
			var low := str(ph).to_lower()
			for banned in ["points down at", "} down at", "from {deficit}", "made that interesting", "room to breathe",
					"nothing between them", "a kick the difference", "neighbours heard"]:
				_check(not low.contains(banned), "%s: \"%s\" repeats a result headline" % [a, ph])
			_check(not low.contains("!"), "%s: no exclamation in the news desk's voice" % a)


# ---------------------------------------------------------------------------
# Triggers: fire on the facts, silent without them
# ---------------------------------------------------------------------------
func _test_comeback() -> void:
	# Melbourne trail St Kilda by 26 at half-time (5.4 to 9.6 = 34 v 60) and win by 10.
	var res := _res("MEL", "STK", [[2, 2], [3, 2], [6, 2], [5, 2]], [[5, 3], [4, 3], [2, 1], [1, 2]])
	var st := _one(res)
	_check(str(st.get("angle", "")) == "comeback", "a 26-point half-time deficit turned into a win is a comeback (%s)" % [st])
	var txt := _all_text(st)
	_check(txt.contains("26 points") and txt.contains("half-time"), "the comeback names the deficit and the break: %s" % txt)
	_check(txt.contains("11.4 to 3.3"), "the run home is the winner's goals and behinds after the break: %s" % txt)
	_check(txt.contains("Melbourne 16.8 (104) beat St Kilda 12.9 (81)"), "the scoreline is stated: %s" % txt)
	_check(str(st["club"]) == "MEL", "a comeback is the winner's story")
	# Down 23 at the break: not enough.
	var near := _res("MEL", "STK", [[2, 2], [3, 3], [6, 2], [5, 2]], [[5, 3], [4, 0], [2, 1], [1, 2]])
	var lead := 0
	var t := [0, 0]
	for q in range(2):
		t[0] += int(near["quarters"][q][0])
		t[1] += int(near["quarters"][q][1])
	lead = t[1] - t[0]
	_check(lead < 24, "the near-miss fixture trails by under 24 (%d)" % lead)
	_check(str(_one(near).get("angle", "")) != "comeback", "a %d-point deficit is not a comeback" % lead)


func _test_blown() -> void:
	# Carlton lead Essendon by 33 at three-quarter time (12.6 to 6.3) and lose.
	var res := _res("CAR", "ESS", [[4, 2], [4, 2], [4, 2], [0, 1]], [[2, 1], [2, 1], [3, 1], [6, 0]])
	var st := _one(res)
	_check(str(st.get("angle", "")) == "blown", "a 33-point three-quarter-time lead lost is a blown lead (%s)" % [st])
	var txt := _all_text(st)
	_check(txt.contains("33 points") and txt.contains("three-quarter time"), "the blown lead names the lead and the break: %s" % txt)
	_check(str(st["club"]) == "CAR", "a blown lead is the loser's story")
	_check(txt.contains("6.0 to 0.1"), "the last quarter's run is stated: %s" % txt)


func _test_held_on() -> void:
	# Geelong lead Hawthorn by 34 at half-time, win by 9.
	var res := _res("GEE", "HAW", [[5, 2], [4, 2], [1, 1], [1, 2]], [[1, 1], [2, 5], [4, 2], [3, 2]])
	var st := _one(res)
	_check(str(st.get("angle", "")) == "held_on", "a 34-point lead cut to a 3-point win is held on (%s)" % [st])
	_check(_all_text(st).contains("34 points"), "it names the lead: %s" % _all_text(st))
	# The same lead, won by 30: no story about holding on.
	var easy := _res("GEE", "HAW", [[5, 2], [4, 2], [3, 1], [3, 2]], [[1, 1], [2, 1], [3, 2], [3, 1]])
	_check(str(_one(easy).get("angle", "")) != "held_on", "a comfortable win is not held on")


func _test_huge() -> void:
	# Sydney beat West Coast by exactly 60.
	var res := _res("SYD", "WCE", [[4, 3], [4, 3], [3, 3], [3, 3]], [[1, 3], [1, 3], [1, 3], [1, 3]])
	var m := int(res["score"][0]) - int(res["score"][1])
	_check(m == 60, "the thrashing fixture is 60 points (%d)" % m)
	var st := _one(res)
	_check(str(st.get("angle", "")) == "huge", "a 60-point win is a thrashing (%s)" % [st])
	var txt := _all_text(st)
	_check(txt.contains("60 points"), "it names the margin: %s" % txt)
	_check(txt.contains("Kicker SYD_K1") and txt.contains("14 goals"), "its top kicker is named with his goals: %s" % txt)
	_check(txt.contains("four goals"), "West Coast's four goals all day are stated: %s" % txt)
	# 59: no story.
	var less := _res("SYD", "WCE", [[4, 3], [4, 3], [3, 3], [3, 2]], [[1, 3], [1, 3], [1, 3], [1, 3]])
	_check(_one(less).is_empty(), "a 59-point win is not a story")


func _test_close() -> void:
	# Fremantle by 5.
	var res := _res("FRE", "WBD", [[3, 2], [3, 2], [3, 2], [3, 2]], [[3, 1], [3, 1], [3, 1], [3, 0]])
	var m := int(res["score"][0]) - int(res["score"][1])
	var st := _one(res)
	_check(m == 5 and str(st.get("angle", "")) == "close", "a 5-point win is a close finish (%s)" % [st])
	_check(_all_text(st).contains("5 points"), "it names the margin: %s" % _all_text(st))
	# A last-quarter go-ahead goal is credited to its kicker.
	var late := _res("FRE", "WBD", [[2, 2], [2, 2], [2, 2], [3, 0]], [[3, 1], [3, 1], [3, 1], [0, 0]],
			{"4|0": "FRE_k9"})
	var ls := _one(late)
	_check(_all_text(ls).contains("Kicker FRE_K9"), "the last quarter's go-ahead kicker is named: %s" % _all_text(ls))
	# Won the lead in the first quarter and never lost it: no "winner" line.
	_check(not _all_text(st).contains("in front for good"), "no late winner is claimed when the lead came early: %s" % _all_text(st))
	# 7: no story.
	var seven := _res("FRE", "WBD", [[3, 2], [3, 2], [3, 2], [3, 4]], [[3, 1], [3, 1], [3, 1], [3, 0]])
	_check(_one(seven).is_empty(), "a 7-point win is not a close finish")
	# A draw.
	var draw := _res("FRE", "WBD", [[3, 1], [3, 1], [3, 1], [3, 1]], [[3, 1], [3, 1], [3, 1], [3, 1]])
	var ds := _one(draw)
	_check(str(ds.get("angle", "")) == "close" and _all_text(ds).contains("drew with"), "a draw is told: %s" % _all_text(ds))


func _test_ordinary_silent() -> void:
	# A 25-point win, never more than 20 either way at a break.
	var res := _res("ADE", "BRL", [[3, 2], [3, 2], [2, 2], [3, 3]], [[2, 2], [2, 2], [2, 2], [2, 0]])
	_check(_one(res).is_empty(), "an ordinary win has no story")


func _test_quarters_must_add_up() -> void:
	# A comeback whose quarters don't add up to the score (a corrupt result) is not claimed.
	var res := _res("MEL", "STK", [[2, 2], [3, 2], [6, 2], [5, 2]], [[5, 3], [4, 3], [2, 1], [1, 2]])
	res["score"] = [int(res["score"][0]) + 1, int(res["score"][1])]
	var st := _one(res)
	_check(str(st.get("angle", "")) != "comeback", "no break claims when the quarters don't add up (%s)" % [st])


func _test_injury() -> void:
	var res := _res("ADE", "BRL", [[3, 2], [3, 2], [2, 2], [3, 3]], [[2, 2], [2, 2], [2, 2], [2, 0]])
	res["injuries"] = [{"side": 1, "id": "BRL_x", "q": 2, "weeks": 6, "kind": "hamstring"}]
	var inj := [{"id": "BRL_x", "club": "BRL", "weeks": 6, "kind": "hamstring"}]
	var out: Array = _ls.round_stories([res], _ctx({"injuries": inj}))
	_check(out.size() == 1 and str(out[0]["angle"]) == "injury", "a six-week injury to a good player is a story (%s)" % [out])
	if out.size() == 1:
		var txt: String = _ls.text(out[0])
		_check(txt.contains("Kicker BRL_X") and txt.contains("six weeks") and txt.contains("hamstring strain"),
				"it says who, what and how long: %s" % txt)
		_check(txt.contains("second quarter") and txt.contains("Adelaide") and txt.contains("loss"),
				"it says where it happened: %s" % txt)
		_check(str(out[0]["club"]) == "BRL" and str(out[0]["id"]) == "BRL_x", "it is his club's story")
	var short := [{"id": "BRL_x", "club": "BRL", "weeks": 3, "kind": "hamstring"}]
	_check((_ls.round_stories([res], _ctx({"injuries": short})) as Array).is_empty(), "three weeks is not a story")
	var low := _ctx({"injuries": inj, "player": func(id): return {"id": id, "name": "Depth", "overall": 71}})
	_check((_ls.round_stories([res], low) as Array).is_empty(), "a player under 72 is not a story")


func _test_cap() -> void:
	var results := []
	var codes := ["ADE", "BRL", "CAR", "COL", "ESS", "FRE", "GEE", "GCS", "GWS", "HAW", "MEL", "NTH",
			"PAD", "RIC", "STK", "SYD"]
	for i in range(8):
		# Thrashings of 60 + 6i points.
		var extra := i
		results.append(_res(codes[2 * i], codes[2 * i + 1], [[4, 3], [4, 3], [4, 3], [4 + extra, 3]],
				[[1, 2], [1, 1], [1, 1], [1, 2]]))
	var out: Array = _ls.round_stories(results, _ctx())
	_check(out.size() == _ls.MAX_STORIES, "eight big wins make %d stories, not more (%d)" % [_ls.MAX_STORIES, out.size()])
	var sorted := true
	for i in range(1, out.size()):
		if int(out[i]["weight"]) > int(out[i - 1]["weight"]):
			sorted = false
	_check(sorted, "biggest first")
	_check(out.size() > 0 and _ls.text(out[0]).contains("120 points"), "the biggest margin leads: %s" % [_ls.text(out[0]) if out.size() > 0 else ""])


func _test_determinism() -> void:
	var res := _res("MEL", "STK", [[2, 2], [3, 2], [6, 2], [5, 2]], [[5, 3], [4, 3], [2, 1], [1, 2]])
	var a := _all_text(_one(res))
	var b := _all_text(_one(res.duplicate(true)))
	_check(a != "" and a == b, "the same match reads the same every time")
	# Across seeds the wording varies (the same facts, different words).
	var seen := {}
	for s in range(12):
		seen[_all_text(_one(res, {"seed": s}))] = true
	_check(seen.size() >= 3, "the same event reads differently across careers (%d variants)" % seen.size())


func _test_own_headline() -> void:
	# Your own comeback: the headline over your result is "From 26 points down at half-time."
	var res := _res("MEL", "STK", [[2, 2], [3, 2], [6, 2], [5, 2]], [[5, 3], [4, 3], [2, 1], [1, 2]])
	var head: String = _hl.for_match(res, 0)
	_check(head.begins_with("From 26 points down"), "the fixture has your own headline (%s)" % head)
	for s in range(20):
		var st := _one(res, {"seed": s, "my_club": "MEL"})
		_check(not _all_text(st).to_lower().contains(head.trim_suffix(".").to_lower()),
				"seed %d: the story never repeats your headline: %s" % [s, _all_text(st)])


func _test_reads_only() -> void:
	var res := _res("CAR", "ESS", [[4, 2], [4, 2], [4, 2], [0, 1]], [[2, 1], [2, 1], [2, 1], [8, 2]])
	res["injuries"] = [{"side": 0, "id": "CAR_x", "q": 3, "weeks": 5, "kind": "knee"}]
	var ladder := {"CAR": {"code": "CAR", "pts": 8, "pf": 400, "pa": 380}, "ESS": {"code": "ESS", "pts": 4, "pf": 350, "pa": 390}}
	var ctx := _ctx({"ladder": ladder, "injuries": [{"id": "CAR_x", "club": "CAR", "weeks": 5, "kind": "knee"}]})
	var before := var_to_bytes([res, ladder, ctx["injuries"]])
	_ls.round_stories([res], ctx)
	_check(var_to_bytes([res, ladder, ctx["injuries"]]) == before, "telling the stories changes no result, ladder or injury")


func _test_ladder() -> void:
	# Melbourne were 11th; the win (4 points, a big percentage) takes them 9th: into the ten.
	var res := _res("MEL", "STK", [[4, 3], [4, 3], [3, 3], [3, 3]], [[1, 3], [1, 3], [1, 3], [1, 3]])
	var codes := ["ADE", "BRL", "CAR", "COL", "ESS", "FRE", "GEE", "GCS", "GWS", "HAW", "MEL", "STK"]
	var ladder := {}
	for i in range(codes.size()):
		ladder[codes[i]] = {"code": codes[i], "pts": 40 - 2 * i, "pf": 1000, "pa": 1000}
	# The ladder after the round: Melbourne's win and St Kilda's loss on it.
	ladder["MEL"]["pts"] = 24
	ladder["MEL"]["pf"] = 1000 + int(res["score"][0])
	ladder["MEL"]["pa"] = 1000 + int(res["score"][1])
	ladder["STK"]["pf"] = 1000 + int(res["score"][1])
	ladder["STK"]["pa"] = 1000 + int(res["score"][0])
	var txt := _all_text(_one(res, {"ladder": ladder}))
	_check(txt.contains("Melbourne") and txt.contains("ninth") and txt.contains("the ten"),
			"from 11th to ninth is told as into the ten: %s" % txt)
	# In a final there is no ladder line.
	res["tag"] = "QF1"
	var fin := _all_text(_one(res, {"ladder": ladder}))
	_check(not fin.contains("ladder") and not fin.contains("the ten"), "no ladder line in a final: %s" % fin)


func _test_front_page_item() -> void:
	var item := {"year": 2027, "when": "Round 5", "kind": "league_story", "text": "X. A. B.",
			"headline": "Demons storm home from 26 points down", "beats": ["St Kilda led by 26 points at half-time.",
			"From there Melbourne kicked 11.4 to 3.3."], "club": "MEL", "weight": 64, "angle": "comeback"}
	var st: Dictionary = _nf.story(item, "FRE")
	_check(str(st["headline"]) == "Demons storm home from 26 points down" and str(st["club"]) == "MEL",
			"the front page reads a story's headline and club")
	_check(str(st["standfirst"]).contains("led by 26") and str(st["standfirst"]).contains("11.4 to 3.3"),
			"the front page tells every beat")
	_check(str(st["short"]) == "St Kilda led by 26 points at half-time.", "the hub card's short form is the first beat")
	_check(int(st["weight"]) >= _nf.SECONDARY_MIN, "a story is big enough for a secondary headline")
	var inj := item.duplicate()
	inj["angle"] = "injury"
	_check(str(_nf.story(inj, "FRE")["group"]) == "injuries", "an injury story sits with the injuries")
	_check(bool(_nf.story(item, "MEL")["mine"]), "your club's story is marked yours")


## A seeded career: stories appear in the news, every one from that round, and
## two plays of the same seed give the same stories and the same results.
func _test_career() -> void:
	var a := _play_rounds(6)
	var b := _play_rounds(6)
	_check(a["results"] == b["results"], "the same seed gives the same results")
	_check(a["stories"] == b["stories"], "the same seed gives the same stories")
	_check((a["stories"] as Array).size() > 0, "six rounds produce at least one league story (%d)" % (a["stories"] as Array).size())
	var per_round := {}
	for s in a["stories"]:
		per_round[str(s["when"])] = int(per_round.get(str(s["when"]), 0)) + 1
	for r in per_round:
		_check(int(per_round[r]) <= _ls.MAX_STORIES, "%s has at most %d stories (%d)" % [r, _ls.MAX_STORIES, per_round[r]])
	# An injury told as a story is not also a plain line.
	for s in a["stories"]:
		if str(s["angle"]) != "injury":
			continue
		var dupes := 0
		for it in a["news"]:
			if str(it.get("kind", "")) == "injury" and str(it.get("when", "")) == str(s["when"]) \
					and str(it.get("text", "")).begins_with(str(s["headline"]).get_slice(" out", 0)):
				dupes += 1
		_check(dupes == 0, "%s: the injury story is not repeated as a plain line" % s["headline"])
	# Grammar a real round has caught: "a 32 points lead", "a 11-point loss", "Final score: X beat Y".
	var bad := RegEx.create_from_string("\\d+ points? (lead|deficit)|\\ba (8|11|18|8\\d)-point|Final score: .* (beat|drew)")
	for s in a["stories"]:
		var all := "%s. %s" % [s["headline"], " ".join(s["beats"])]
		_check(bad.search(all) == null, "reads as English: %s" % all)
	_check(_ls._an(8) == "an" and _ls._an(11) == "an" and _ls._an(84) == "an" and _ls._an(12) == "a"
			and _ls._an(1) == "a", "the article before a margin")


func _play_rounds(n: int) -> Dictionary:
	_state.replay_seed = SUITE_SEED
	_state.reset()
	_state.career_seed = SUITE_SEED
	_state.replay_seed = SUITE_SEED
	_state.start_season("FRE", _db.club_list("FRE"))
	_state.tutorials = false
	_state.event_sheets = false
	for i in range(n):
		_state.advance()
	var results := []
	for rnd in _state.season.results:
		for res in rnd:
			results.append([str(res["home"]), str(res["away"]), str(res["score"])])
	var stories := []
	for it in _state.news:
		if str(it.get("kind", "")) == "league_story":
			stories.append({"when": it["when"], "headline": it["headline"], "beats": it["beats"], "angle": it["angle"]})
	return {"results": results, "stories": stories, "news": _state.news.duplicate(true)}


## A real tap on the hub's news card opens the front page, and a league story is on it.
func _test_phone(size: Vector2i) -> void:
	var tag := "%dx%d" % [size.x, size.y]
	_state.reset()
	_state.start_season("MEL", _db.club_list("MEL"))
	_state.tutorials = false
	_state.replay_seed = SUITE_SEED
	var res := _res("FRE", "STK", [[2, 2], [3, 2], [6, 2], [5, 2]], [[5, 3], [4, 3], [2, 1], [1, 2]])
	var st := _one(res)
	_state.news = [{"year": 2027, "when": "Round 5", "kind": "league_story", "text": _ls.text(st),
			"headline": st["headline"], "beats": st["beats"], "club": st["club"], "weight": st["weight"],
			"angle": st["angle"]},
			{"year": 2027, "when": "Round 5", "kind": "injury", "text": "Josh Battle (Hawthorn) is out for 8 weeks with a hand injury."}]
	root.size = size
	_router.stack = []
	_router.go("main")
	await _settle()
	_router.go("hub")
	await _settle(10)
	var hub: Node = current_scene
	var more: Button = hub.find_child("NewsMore", true, false)
	var why: String = await Tap.tap(more) if more != null else "missing"
	await _settle(8)
	var feed: Control = hub.find_child("NewsFeed", true, false)
	_check(why == "" and feed != null, "%s: a real tap on the news card opens the front page (%s)" % [tag, why])
	if feed == null:
		return
	var texts: Array = []
	_texts(feed, texts)
	# NameInk keeps a name on one line with no-break spaces ("St Kilda"): read them as spaces.
	var blob := "\n".join(texts).replace(String.chr(0x00A0), " ")
	_check(blob.contains(str(st["headline"])), "%s: the story's headline is on the front page" % tag)
	for b in st["beats"]:
		_check(blob.contains(str(b)), "%s: the beat \"%s\" is on the front page" % [tag, b])
	var lead := feed.find_child("LeadStory", true, false) as Control
	_check(lead != null and Rect2(Vector2.ZERO, Vector2(size)).encloses(lead.get_global_rect()),
			"%s: the lead story fits on screen" % tag)


func _texts(node: Node, out: Array) -> void:
	if node is Label:
		out.append((node as Label).text)
	elif node is RichTextLabel:
		out.append((node as RichTextLabel).get_parsed_text())
	for c in node.get_children():
		_texts(c, out)
