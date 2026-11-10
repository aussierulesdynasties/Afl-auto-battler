extends SceneTree
## godot --headless --path . --script tests/run_remembered_tests.gd
## People remembered (row T5.r110): the selection drop says what the club
## remembers about the player you leave out (P-37), and Season stats > Coach
## is your own ledger (P-39): the players you drafted who won your best and
## fairest or made the All-Australian team, and the board's verdict each
## season. Real taps at 390x844; every line from what the career recorded.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 7741

var _checks := 0
var _failures: Array = []
var _gs: Node
var _db: Node
var _router: Node
var _ledger: GDScript
var _remembered: GDScript


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 6) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	await process_frame
	_gs = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_router = root.get_node("Router")
	_ledger = load("res://scripts/sim/CoachLedger.gd")
	_remembered = load("res://scripts/sim/Remembered.gd")
	_gs.autosave_enabled = false
	_gs.event_sheets = false
	_gs.save_path = "user://test_remembered.save"
	_gs.settings_path = "user://test_remembered.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_gs.set_setting("seen_%s_intro" % key, true)
	_gs.show_real_names = false
	_gs.replay_seed = SUITE_SEED
	_t("_test_drop_line_words")
	_t("_test_your_draft_rules")
	_t("_test_goal_line")
	# The ledger first: the team screen's field taps and Back can leave the
	# window's pointer state mid-drag on CI, and a tap after that reaches nothing.
	await _t("_test_coach_ledger_empty")
	await _t("_test_coach_ledger_taps")
	await _t("_test_selection_drop_taps")
	print(Ran.line("Remembered", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(0 if _failures.is_empty() else 1)


func _fresh(club: String) -> void:
	_gs.reset()
	# reset() forgets the first-visit cards; one over the tabs would take the tap.
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_gs.set_setting("seen_%s_intro" % key, true)
	_gs.career_seed = SUITE_SEED
	_gs.replay_seed = SUITE_SEED
	_gs.start_season(club, _db.club_list(club))


## The drop's line names him where the release confirm says "He" or "him".
func _test_drop_line_words() -> void:
	_fresh("FRE")
	var year: int = _gs.season_year
	var p: Dictionary = _gs.my_list[0]
	var id := str(p["id"])
	p["career"] = {"games": 3, "goals": 0, "through": year - 1, "unknown": [], "stints": [["FRE", year - 1, year - 1, 3, 0]]}
	p.erase("firsts")
	p.erase("backed")
	for k in ["injury_weeks", "injury_kind"]:
		p.erase(k)
	_gs.career_facts.erase(id)
	_gs.honour_roll = []
	_check(_remembered.drop_line(p, "Jones", _gs.career_facts, "FRE", _gs.with_us(p), _gs.LEARN_JOBS) == "",
			"Nothing remembered: the drop says nothing")
	var facts = load("res://scripts/sim/CareerFacts.gd")
	facts.add(_gs.career_facts, id, facts.row(year - 1, "Round 3", "injury", "FRE", "", "hamstring"))
	var said: String = _remembered.drop_line(p, "Jones", _gs.career_facts, "FRE", _gs.with_us(p), _gs.LEARN_JOBS)
	_check(said == "Jones came back from a hamstring injury in Round 3, %d." % (year - 1),
			"A 'He' fact takes his name (%s)" % said)
	facts.add(_gs.career_facts, id, facts.row(year - 1, "Round 5", "talk", "FRE", "dropped|promise", "played"))
	said = _remembered.drop_line(p, "Jones", _gs.career_facts, "FRE", _gs.with_us(p), _gs.LEARN_JOBS)
	_check(said == "You promised Jones a game in Round 5, %d, and he played." % (year - 1),
			"A 'You ... him' fact takes his name for 'him' (%s)" % said)


## Who counts as yours: the club that drafted him is the club you coached that
## season, in a draft held in your career.
func _test_your_draft_rules() -> void:
	var roll := [{"year": 2027, "my_club": "FRE"}, {"year": 2028, "my_club": "MEL"}]
	var mine := {"id": "a", "drafted_club": "FRE", "drafted_year": 2027, "drafted_pick": 7, "drafted_type": "national"}
	_check(_ledger.your_draft(mine, roll, "MEL", 2029, 2027, "redraft") == [2027, 7, "national"],
			"Drafted by your club in a season you coached it: yours")
	var other := mine.duplicate()
	other["drafted_club"] = "MEL"
	_check(_ledger.your_draft(other, roll, "MEL", 2029, 2027, "redraft").is_empty(),
			"Drafted by a club you were not coaching that season: not yours")
	var before := mine.duplicate()
	before["drafted_year"] = 2024
	_check(_ledger.your_draft(before, roll, "MEL", 2029, 2027, "redraft").is_empty(),
			"Drafted before your career began: not yours, even at your club")
	var now := {"id": "b", "drafted_club": "MEL", "drafted_year": 2029, "drafted_type": "rookie"}
	_check(_ledger.your_draft(now, roll, "MEL", 2029, 2027, "redraft") == [2029, 0, "rookie"],
			"This season's draft at the club you coach now: yours")
	var redraft := {"id": "D2026_04", "drafted_club": "FRE"}
	_check(_ledger.your_draft(redraft, roll, "MEL", 2029, 2027, "redraft") == [2027, 0, "redraft"],
			"The 2026 class taken in your opening redraft: yours")
	_check(_ledger.your_draft(redraft, roll, "MEL", 2029, 2027, "real").is_empty(),
			"...but not in a real-lists career, where no redraft happened")
	_check(_ledger.your_draft({"id": "c"}, roll, "MEL", 2029, 2027, "redraft").is_empty(),
			"No draft on record: not yours")
	_check(_ledger.draft_words([2027, 7, "national"]) == "Pick 7, 2027 national draft"
			and _ledger.draft_words([2028, 0, "midseason"]) == "2028 mid-season draft"
			and _ledger.draft_words([2026, 0, "redraft"]) == "Taken in your 2026 league redraft",
			"The draft in football words")
	# The season-close snapshot keeps a draftee once he has gone.
	var entry := {"year": 2028, "my_club": "MEL", "my_bf": [{"id": "b"}], "my_aa": ["a", "z"]}
	var find := func(id: String) -> Dictionary:
		return {"a": mine, "b": now}.get(id, {})
	var snap: Dictionary = _ledger.snapshot(entry, find, roll, "MEL", 2029, 2027, "redraft")
	# "a" (2027, your FRE) and "b" (this season's MEL rookie) are yours; "z" is not in the game.
	var got := snap.keys()
	got.sort()
	_check(got == ["a", "b"] and snap["b"] == [2029, 0, "rookie"],
			"The snapshot keeps your draftees among the honoured (%s)" % str(got))


func _test_goal_line() -> void:
	_check(_ledger.goal_line({"goal": "Finish in the top four", "position": 3, "met": true})
			== "Finish in the top four: finished 3rd, goal met.", "A goal met, in words")
	_check(_ledger.goal_line({"goal": "", "position": 0, "met": false}) == "Goal missed.",
			"No goal or place on record: only what is known")


## P-37 by a finger: tap the man on the field, tap one from the list, and the
## line under the note says what the club remembers about the man left out.
func _test_selection_drop_taps() -> void:
	_fresh("FRE")
	var year: int = _gs.season_year
	root.size = Vector2i(390, 844)
	var side: Dictionary = _gs.current_side()
	var star_id := str(side["FWD"][0])
	var star: Dictionary = _gs.list_player(star_id)
	star["career"] = {"games": 12, "goals": 14, "through": year - 1, "unknown": [],
			"stints": [["FRE", year - 2, year - 1, 12, 14]]}
	_gs.honour_roll = [{"year": year - 2, "my_club": "FRE", "premier": "FRE", "my_bf": []}]
	var blank_id := str(side["FWD"][1])
	var blank: Dictionary = _gs.list_player(blank_id)
	blank["career"] = {"games": 0, "goals": 0, "through": year - 1, "unknown": [], "stints": []}
	for q in [star, blank]:
		q.erase("firsts")
		q.erase("backed")
		_gs.career_facts.erase(str(q["id"]))
	_router.go("selection")
	await _settle()
	var ui: Node = current_scene
	var ins := []
	for c in ui.find_child("NotSelected", true, false).get_children():
		if c is Button and load("res://scripts/sim/Ratings.gd").available(_gs.list_player(str(c.get_meta("id")))):
			ins.append(str(c.get_meta("id")))
	_check(ins.size() >= 2, "Two players off the side to bring in (%d)" % ins.size())
	if ins.size() < 2:
		return
	var star_name: String = _db.player_display_name(star)
	var spot := _spot_of(ui, star_id)
	var why_a: String = await Tap.tap(spot) if spot != null else "no spot"
	await _settle()
	var why_b: String = await Tap.tap(_grid_card(ui, ins[0]))
	await _settle()
	ui = current_scene
	var mem := ui.find_child("BuilderRemembered", true, false) as Label
	var hint := ui.find_child("BuilderHint", true, false) as Label
	_check(why_a == "" and why_b == "" and not (_gs.my_selection()["FWD"] as Array).has(star_id),
			"Two taps leave him out (%s, %s)" % [why_a, why_b])
	_check(hint != null and hint.text.ends_with("comes in for %s." % star_name),
			"The note says who came in for him (%s)" % (hint.text if hint != null else "none"))
	_check(mem != null and mem.text == "%s was with you for the %d premiership." % [star_name, year - 2],
			"The line under it says what the club remembers about him (%s)" % (mem.text if mem != null else "none"))
	_check(mem != null and mem.get_global_rect().end.x <= 390.0 + 0.5 and mem.is_visible_in_tree(),
			"...whole on a phone")
	var ui_kit = load("res://scripts/ui/UiKit.gd")
	_check(mem != null and mem.get_theme_color("font_color").is_equal_approx(ui_kit.TEXT),
			"...in plain text, not the note's green: a fact, not a state")
	# A man with nothing remembered: the note alone.
	spot = _spot_of(ui, blank_id)
	await Tap.tap(spot)
	await _settle()
	await Tap.tap(_grid_card(current_scene, ins[1]))
	await _settle()
	_check(current_scene.find_child("BuilderRemembered", true, false) == null,
			"Nothing remembered about the man left out: no line")
	# Two men on the field swapping places drop no one.
	var a := _spot_of(current_scene, str(_gs.current_side()["DEF"][0]))
	var b_id := str(_gs.current_side()["DEF"][1])
	await Tap.tap(a)
	await _settle()
	# The first tap rebuilds the oval: find the second man again.
	await Tap.tap(_spot_of(current_scene, b_id))
	await _settle()
	_check(current_scene.find_child("BuilderRemembered", true, false) == null,
			"A swap on the field leaves no one out: no line")
	_router.handle_back(true)
	await _settle()


func _spot_of(ui: Node, id: String) -> Control:
	for c in ui.find_children("Spot_*", "Button", true, false) + ui.find_children("BenchSpot_*", "Button", true, false):
		if str(c.get_meta("id", "")) == id:
			return c
	return null


func _grid_card(ui: Node, id: String) -> Control:
	for c in ui.find_child("NotSelected", true, false).get_children():
		if str(c.get_meta("id", "")) == id:
			return c
	return null


## A first season: the ledger says plainly that nothing is on it yet.
func _test_coach_ledger_empty() -> void:
	_fresh("MEL")
	root.size = Vector2i(390, 844)
	var s := await _open_coach()
	_check(s.find_child("CoachRecordEmpty", true, false) != null, "No season finished: the record says when it starts")
	_check(s.find_child("DrafteesEmpty", true, false) != null and s.find_child("Draftees", true, false) == null,
			"No draftee honoured yet: an honest line, no rows")
	_check(s.find_child("VerdictsEmpty", true, false) != null, "No verdict yet: the board's first comes at season's end")
	s.queue_free()
	await _settle()


func _open_coach() -> Control:
	# As the stats suite opens it: the hub on its own at a phone's size.
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	var tab := s.find_child("Section_coach", true, false) as Control
	# Measured before the tap: the tap rebuilds the row.
	var end := tab.get_global_rect().end.x if tab != null else 9999.0
	_check(end <= 391.0 and s.find_child("SectionStrip", true, false) == null,
			"Six tabs share one row on a phone, Coach whole (ends at %.1f)" % end)
	await _settle(20)
	tab = s.find_child("Section_coach", true, false) as Control
	var before := "win %s, tab %s, valid %s" % [str(root.size), str(tab.get_global_rect()) if tab != null else "-",
			str(is_instance_valid(tab))]
	var why: String = await Tap.tap(tab) if tab != null else "no Coach tab"
	await _settle()
	if why != "":
		var hov := root.gui_get_hovered_control()
		why += "; %s; hovered %s; dragging %s; tab now valid %s" % [before, hov.get_path() if hov != null else "none",
				str(root.gui_is_dragging()), str(is_instance_valid(tab))]
	_check(why == "" and s.find_child("StatsCoach", true, false) != null, "A finger on Coach opens the ledger (%s)" % why)
	return s


## Three seasons in: your draftees with their honours, the latest first, a
## gone one kept; the board's verdict each season, newest first. A finger on a
## draftee opens his profile.
func _test_coach_ledger_taps() -> void:
	_fresh("MEL")
	var year: int = _gs.season_year
	_gs.my_first_season = year - 3
	var list: Array = _gs.my_list
	var a: Dictionary = list[0]
	var b: Dictionary = list[1]
	var c: Dictionary = list[2]
	var a_id := str(a["id"])
	var b_id := str(b["id"])
	var c_id := str(c["id"])
	a["drafted_club"] = "MEL"
	a["drafted_year"] = year - 3
	a["drafted_pick"] = 7
	a["drafted_type"] = "national"
	b["drafted_club"] = "MEL"
	b["drafted_year"] = year - 6   # before your career: the club's, not yours
	c["drafted_club"] = "CAR"
	c["drafted_year"] = year - 2
	_gs.departed_names["gone_1"] = {"real_name": "", "generic_name": "Sam Kelly", "first": "Sam", "last": "Kelly"}
	_gs.honour_roll = [
		{"year": year - 3, "my_club": "MEL", "premier": "", "my_bf": [], "my_aa": [b_id], "my_record": "12-11-0"},
		# A season closed before the snapshot: read from the players.
		{"year": year - 2, "my_club": "MEL", "premier": "", "my_bf": [{"id": b_id}], "my_aa": [a_id],
				"my_record": "14-9-0"},
		{"year": year - 1, "my_club": "MEL", "premier": "MEL", "my_bf": [{"id": a_id}], "my_aa": ["gone_1", c_id],
				"my_record": "17-6-0", "my_finals": "GF", "my_drafted": {a_id: [year - 3, 7, "national"], "gone_1": [year - 2, 0, "rookie"]}},
	]
	_gs.board["history"] = [
		{"year": year - 3, "goal": "Make the finals", "met": false, "position": 11, "verdict": "The board is losing patience."},
		{"year": year - 2, "goal": "Make the finals", "met": true, "position": 6, "verdict": "The board is delighted."},
		{"year": year - 1, "goal": "Finish in the top four", "met": true, "position": 1, "verdict": "The board is delighted."},
	]
	root.size = Vector2i(390, 844)
	var s := await _open_coach()
	var rows: Array = s.find_child("Draftees", true, false).get_children() if s.find_child("Draftees", true, false) != null else []
	var names: Array = rows.map(func(r): return str(r.name))
	_check(names == ["Draftee_" + a_id, "Draftee_gone_1"],
			"Only your draftees, the latest honour first; not the club's earlier pick or a player drafted elsewhere (%s)" % str(names))
	if rows.size() == 2:
		var won := (rows[0].find_child("Honours", true, false) as Label).text
		var how := (rows[0].find_child("Drafted", true, false) as Label).text
		var medal: String = load("res://scripts/core/BestAndFairest.gd").award_name("MEL")
		_check(won == "%s %d  ·  All-Australian %d" % [medal, year - 1, year - 2],
				"His honours with their years (%s)" % won)
		_check(how == "Pick 7, %d national draft." % (year - 3), "How you drafted him (%s)" % how)
		var gone_name := (rows[1].find_child("Name", true, false) as Label).text
		_check(gone_name == "Sam Kelly" and not (rows[1] is Button),
				"A draftee who has left the game stays, by the name he left with, with no profile to open (%s)" % gone_name)
		for r in rows:
			_check((r as Control).get_global_rect().end.x <= 390.5, "%s fits a phone" % r.name)
		var why: String = await Tap.tap(rows[0])
		await _settle()
		_check(why == "" and s.find_child("PlayerProfile", true, false) != null,
				"A finger on a draftee opens his profile (%s)" % why)
		s.handle_back()
		await _settle()
	var v: Node = s.find_child("Verdicts", true, false)
	var years: Array = v.get_children().map(func(r): return str(r.name)) if v != null else []
	_check(years == ["Verdict_%d" % (year - 1), "Verdict_%d" % (year - 2), "Verdict_%d" % (year - 3)],
			"The board's verdict for every season, newest first (%s)" % str(years))
	if v != null and v.get_child_count() == 3:
		var top: Node = v.get_child(0)
		_check((top.find_child("Said", true, false) as Label).text == "The board is delighted."
				and (top.find_child("Goal", true, false) as Label).text == "Finish in the top four: finished 1st, goal met.",
				"Each verdict says what the board said and the goal it judged")
	var rec := s.find_child("CoachRecordLine", true, false) as Label
	_check(rec != null and rec.text.replace("\u00a0", " ") == "3 seasons  ·  43-26-0  ·  finals once  ·  1 premiership",
			"Your record in one line (%s)" % (rec.text if rec != null else "none"))
	s.queue_free()
	await _settle()
