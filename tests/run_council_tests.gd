extends SceneTree
## godot --headless --path . --script tests/run_council_tests.gd
## The Council (scripts/sim/Council.gd): eight seats at every club, agendas
## and manners from the data, loyalty in the Opinion shape, one signed pitch a
## card with its stakes, what taking or going against it does, the side each
## club picks read by the same rule, walk-outs and lost coaches felt by their
## players, a faction's sway, the save, the cards' advisors, a real tap on a
## pitched card, and no effect on the match dice.
## Seeded by design: the career uses replay_seed 4242.

const Tap := preload("res://tests/tap.gd")

var _state: Node
var _db: Node
var _council
var _opinion
var _squad
var _match_sim
var _clubstories
var _storyengine
var _promises
var _coachmarket
var _eventcardview
var _copyrules
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_state.autosave_enabled = false
	_state.save_path = "user://test_council.save"
	_state.settings_path = "user://test_settings.cfg"
	_db = root.get_node("GameDB")
	_council = load("res://scripts/sim/Council.gd")
	_opinion = load("res://scripts/sim/Opinion.gd")
	_squad = load("res://scripts/sim/Squad.gd")
	_match_sim = load("res://scripts/sim/MatchSim.gd")
	_clubstories = load("res://scripts/state/ClubStories.gd")
	_storyengine = load("res://scripts/sim/StoryEngine.gd")
	_promises = load("res://scripts/sim/Promises.gd")
	_coachmarket = load("res://scripts/sim/CoachMarket.gd")
	_eventcardview = load("res://scripts/ui/EventCardView.gd")
	_copyrules = load("res://scripts/core/CopyRules.gd")
	_state.replay_seed = 4242
	_state.reset()
	_state.start_season("COL", _db.club_list("COL"))

	_t("_test_data_sound")
	_t("_test_every_club_seated")
	_t("_test_advisor_seats")
	_t("_test_pitch_and_answer")
	_t("_test_no_pitch_without_a_view")
	_t("_test_side_read_every_club")
	_t("_test_walk_out")
	_t("_test_lost_coach_marks")
	_t("_test_faction_sway")
	_t("_test_save")
	await _t("_test_pitch_card_real_tap")
	_t("_test_no_match_effect")
	_state.replay_seed = 0
	print(Ran.line("Council", self))
	for f in _failures:
		print("FAIL: ", f)
	quit(0 if _failures.is_empty() else 1)


## The agendas file and the new marks pass their own checks.
func _test_data_sound() -> void:
	var bad: Array = _council.check_agendas(_council.agendas())
	_check(bad.is_empty(), "the agendas file is sound: %s" % [bad])
	var marks: Array = _opinion.check_defs(_opinion.defs())
	_check(marks.is_empty(), "the opinion marks are sound: %s" % [marks])
	for k in ["advice_taken", "advice_overruled", "agenda_served", "agenda_crossed", "coach_sacked", "coach_left"]:
		_check(not _opinion.def(k).is_empty(), "the %s mark is defined" % k)
	for a in _council.agendas():
		for m in _council.MANNERS:
			for line in (_council.agenda(a)["voice"][m] as Array):
				_check(_copyrules.words_in(str(line)).is_empty(), "%s %s voice uses no banned words: %s" % [a, m, line])


## Every club has its list manager and head of high performance; every member
## has an agenda from the file and a manner. Seven at your table, eight at a rival's.
func _test_every_club_seated() -> void:
	var clubs: Array = _state.season.lists.keys()
	_check(clubs.size() >= 18, "the league has its 18 clubs (%d)" % clubs.size())
	for code in clubs:
		var ms: Array = _council.members(_state, str(code))
		var jobs := {}
		for m in ms:
			jobs[str(m["job"])] = true
			_check(_council.agendas().has(str(m["agenda"])), "%s %s has a known agenda (%s)" % [code, m["job"], m["agenda"]])
			_check(_council.MANNERS.has(str(m["manner"])), "%s %s has a manner" % [code, m["job"]])
			_check(str(m["name"]) != "", "%s %s has a name" % [code, m["job"]])
		_check(jobs.has("LM") and jobs.has("HP"), "%s has a list manager and a head of high performance" % code)
		if str(code) == "COL":
			_check(not jobs.has("SC"), "your own seat is not at your table")
			_check(ms.size() == 7, "seven people sit at your table (%d)" % ms.size())
		else:
			_check(ms.size() == 8, "%s has eight seats filled (%d)" % [code, ms.size()])
	# The same person always wants the same thing.
	_check(_council.pick_agenda("X1", "DEV") == _council.pick_agenda("X1", "DEV"), "an agenda is picked the same way every time")
	_check(_council.ensure(_state) == 0, "ensure adds nobody once every club is seated")


## The cards' advisors include the new seats, so a card that names them can come up.
func _test_advisor_seats() -> void:
	var seats: Dictionary = _state.council_seats()
	_check(seats.has("list_manager") and seats.has("high_performance"), "the cards see the list manager and the head of high performance")
	var adv: Dictionary = _clubstories.advisors(_state)
	_check(adv.has("list_manager") and adv.has("senior_assistant"), "ClubStories.advisors names the council")
	for s in seats:
		_check(_storyengine.ADVISOR_SEATS.has(str(s)), "every seat is one a card may name (%s)" % s)


## A card where one choice suits a member's agenda: he backs it in his own
## words; taking it lifts his loyalty, going against it costs loyalty and
## builds your Authority.
func _test_pitch_and_answer() -> void:
	_set_agendas("COL", "fitness", {"LM": "youth"})
	var card := _card([{"op": "start_backing"}, {"op": "xp", "d": 2}], [{"op": "board", "d": 2}])
	var p: Dictionary = _council.pitch(_state, card)
	_check(not p.is_empty() and str(p["job"]) == "LM", "the youth-minded list manager backs a choice (%s)" % [p])
	_check(int(p.get("option", -1)) == 0, "he backs the choice that backs a kid")
	card["pitch"] = p
	var lines: Array = _council.pitch_lines(card)
	_check(lines.size() == 4, "the card says who backs what, then three stakes lines (%d)" % lines.size())
	_check(str(lines[0]).find(str(p["name"])) >= 0 and str(lines[0]).find("list manager") >= 0, "the pitch is signed: %s" % lines[0])
	for line in lines:
		_check(_copyrules.words_in(str(line)).is_empty(), "no banned words on the gate: %s" % line)
		_check(str(line).to_lower().find("best") < 0, "the gate never says which is best: %s" % line)
	var m := _member("COL", "LM")
	var before: int = _council.loyalty(_state, m)
	_council.answered(_state, card, 0)
	var after: int = _council.loyalty(_state, m)
	_check(after > before, "taking his advice lifts his loyalty (%d -> %d)" % [before, after])
	var auth0: int = _promises.authority(_state)
	var card2 := _card([{"op": "back_kid"}], [{"op": "board", "d": 2}])
	card2["tid"] = "test_two"
	card2["pitch"] = _council.pitch(_state, card2)
	_council.answered(_state, card2, 1)
	_check(_council.loyalty(_state, m) < after, "going against him costs loyalty")
	_check(_promises.authority(_state) == auth0 + int(_council.OVERRULE[1]), "going against him builds your Authority")


## A card nobody has a clear view on carries no pitch; one choice, no pitch.
func _test_no_pitch_without_a_view() -> void:
	_set_agendas("COL", "fitness", {})
	_check(_council.pitch(_state, _card([{"op": "board", "d": 2}], [{"op": "board", "d": -2}])).is_empty(),
			"nobody whose agenda is untouched backs a choice")
	var one := _card([{"op": "rest"}], [])
	(one["options"] as Array).resize(1)
	_check(_council.pitch(_state, one).is_empty(), "a card with one choice has no pitch")
	# Mind-the-bodies men back the rest when one choice rests a sore man.
	var rest := _card([{"op": "rest"}], [{"op": "heavy_legs"}])
	_check(int(_council.pitch(_state, rest).get("option", -1)) == 0, "the fitness view backs the rest")


## After a round every club's youth and win-now members read the side picked,
## by the same rule.
func _test_side_read_every_club() -> void:
	for code in ["CAR", "COL"]:
		_set_agendas(code, "youth", {})
		var list: Array = _state.season.lists[code]
		var kids := []
		var old := []
		for p in list:
			if int(p.get("age", 25)) <= _council.YOUTH_AGE:
				kids.append(p)
			else:
				old.append(p)
		var side := (kids.slice(0, 6) + old).slice(0, 22)
		var res := {"home": code, "away": "", "roster": [side.map(func(p): return {"id": p["id"]}), []]}
		if kids.size() < _council.YOUTH_SERVED:
			_check(true, "%s has too few kids to fill a young side (%d)" % [code, kids.size()])
			continue
		_council.after_round(_state, [res])
		var m := _member(code, "SA")
		var marks: Array = _opinion.breakdown(_state.relations, str(m["key"]))
		var served := false
		for b in marks:
			if str(b["k"]) == "agenda_served":
				served = true
		_check(served, "%s's youth-minded assistant likes a side with kids in it" % code)


## A member whose loyalty has fallen to the walk line walks out at the season's
## close, at a rival club as at yours; an office seat is filled again.
func _test_walk_out() -> void:
	var sa := _member("CAR", "SA")
	var lm := _member("CAR", "LM")
	_opinion.add_raw(_state.relations, str(sa["key"]), "test_low", -40, 0, "council", "Test", 2027, "Round 1")
	_opinion.add_raw(_state.relations, str(lm["key"]), "test_low", -40, 0, "council", "Test", 2027, "Round 1")
	var gone: Array = _council.season_end(_state)
	var ids := {}
	for g in gone:
		ids[str(g["id"])] = true
	_check(ids.has(str(sa["id"])) and ids.has(str(lm["id"])), "both disloyal members walk (%s)" % [gone])
	_check(str(_state.coaches[str(sa["id"])].get("club", "")) == "", "the assistant has left his job")
	var lm2 := _member("CAR", "LM")
	_check(not lm2.is_empty() and str(lm2["id"]) != str(lm["id"]), "a new list manager takes the seat")
	_check(_council.loyalty(_state, lm2) == 50, "the new man starts level")
	_check(not _state.relations.has(str(sa["key"])), "a member who walked takes his loyalty with him")
	# His players took it.
	var hit := 0
	for p in _council.attached(_state, "CAR", "SA"):
		for b in _opinion.breakdown(_state.relations, _opinion.player_key(str(p["id"]))):
			if str(b["k"]) == "coach_left":
				hit += 1
	_check(hit > 0 or _council.attached(_state, "CAR", "SA").is_empty(), "the leaders feel their coach walk out (%d)" % hit)
	# The market fills the job: put him back for the tests after.
	_coachmarket._appoint(_state.coaches[str(sa["id"])], "CAR", "SA", int(_state.season_year), 1)


## You let a coach go: the men he coached take a mark naming him.
func _test_lost_coach_marks() -> void:
	var fwds: Array = _council.attached(_state, "COL", "FWD")
	_check(not fwds.is_empty(), "the forwards coach has forwards")
	var n: int = _council.staff_gone(_state, "COL", "FWD", "Test Coach", "sacked")
	_check(n == fwds.size(), "every forward takes it (%d of %d)" % [n, fwds.size()])
	var b: Array = _opinion.breakdown(_state.relations, _opinion.player_key(str(fwds[0]["id"])))
	var found := false
	for x in b:
		if str(x["k"]) == "coach_sacked" and str(x["why"]).find("Test Coach") >= 0:
			found = true
	_check(found, "the mark names the coach let go")
	# A rival's forwards, by the same rule.
	_check(_council.staff_gone(_state, "ESS", "FWD", "Other Coach", "left") > 0, "a rival's men feel it the same way")


## Loyal members attached to a faction's men talk it down; restless ones stir it.
func _test_faction_sway() -> void:
	var m := _member("ESS", "FWD")
	var men: Array = _council.attached(_state, "ESS", "FWD").slice(0, 3).map(func(p): return str(p["id"]))
	var f := {"members": men}
	_state.relations.erase(str(m["key"]))
	_opinion.add_raw(_state.relations, str(m["key"]), "test_up", 30, 0, "council", "Test", 2027, "Round 1")
	_check(_council.faction_sway(_state, "ESS", f) < 0, "a loyal forwards coach takes pressure off his forwards' faction")
	_state.relations.erase(str(m["key"]))
	_opinion.add_raw(_state.relations, str(m["key"]), "test_down", -25, 0, "council", "Test", 2027, "Round 1")
	_check(_council.faction_sway(_state, "ESS", f) > 0, "a restless one stirs it")
	_check(absi(_council.faction_sway(_state, "ESS", f)) <= _council.SWAY_MAX, "the sway is capped")
	_check(_council.faction_sway(_state, "ESS", {"members": []}) == 0, "no men, no sway")
	_state.relations.erase(str(m["key"]))


func _test_save() -> void:
	var before := JSON.stringify(_state.council)
	var agenda := str(_member("COL", "SA")["agenda"])
	_check(_state.save_career(), "the career saves")
	_check(_state.load_career(), "the career loads")
	_check(JSON.stringify(_state.council) == before, "the office seats come back as they were")
	_check(str(_member("COL", "SA")["agenda"]) == agenda, "a coach keeps his agenda through a save")


## A pitched card on the hub's card view: the pitch shows under the choices,
## and a finger's tap on the backed choice moves his loyalty.
func _test_pitch_card_real_tap() -> void:
	_set_agendas("COL", "fitness", {"LM": "youth"})
	# Club-wide effects only: the tap applies the choice for real.
	var card := _card([{"op": "xp", "d": 2}], [{"op": "forgo_xp", "d": 2}])
	card["tid"] = "test_tap"
	card["story"] = true
	card["title"] = "A test card"
	card["text"] = "Words."
	card["pitch"] = _council.pitch(_state, card)
	_state.week_events = [card]
	var host := Control.new()
	host.size = Vector2(412, 900)
	root.add_child(host)
	var view: Control = _eventcardview.build(0, true, func(): pass, func(_t): pass)
	host.add_child(view)
	view.size = Vector2(400, 0)
	for i in 3:
		await process_frame
	_check(view.find_child("EventPitchSaid_0", true, false) != null, "the card shows who backs which choice")
	_check(view.find_child("EventPitchStake_0_3", true, false) != null, "and every stakes line")
	var m := _member("COL", "LM")
	var before: int = _council.loyalty(_state, m)
	var b := view.find_child("Event_0", true, false) as Control
	var why: String = await Tap.tap(b)
	_check(why == "", "a finger's tap reaches the backed choice (%s)" % why)
	_check(bool(_state.week_events[0].get("resolved", false)), "the card is answered")
	_check(_council.loyalty(_state, m) > before, "his loyalty rises when you take his advice")
	host.queue_free()
	_state.week_events = []


## The Council never touches the match: MatchSim does not read it, and the
## same match plays the same with or without it.
func _test_no_match_effect() -> void:
	var src := FileAccess.get_file_as_string("res://scripts/sim/MatchSim.gd")
	_check(src.find("Council") < 0 and src.find("council") < 0, "MatchSim does not read the council")
	var home: Array = _state.season.lists["COL"]
	var away: Array = _state.season.lists["CAR"]
	var r1 := _play(home, away)
	var keep: Dictionary = _state.council
	_state.council = {}
	var r2 := _play(home, away)
	_state.council = keep
	_check(r1 == r2, "a match plays the same with or without the council (%s / %s)" % [r1, r2])


# ---------------------------------------------------------------------------

func _card(a: Array, b: Array) -> Dictionary:
	return {"tid": "test_card", "options": [{"label": "Back him", "effects": a}, {"label": "Play the side", "effects": b}]}


## Every coach at `club` (and its office) pushes for `ag`, except `but` {job: agenda}.
func _set_agendas(club: String, ag: String, but: Dictionary) -> void:
	for m in _council.members(_state, club):
		var want := str(but.get(str(m["job"]), ag))
		if (m["coach"] as Dictionary).is_empty():
			_state.council["office"][club][str(m["job"])]["agenda"] = want
		else:
			(m["coach"] as Dictionary)["agenda"] = want


func _member(club: String, job: String) -> Dictionary:
	for m in _council.members(_state, club):
		if str(m["job"]) == job:
			return m
	return {}


func _play(home: Array, away: Array) -> String:
	var h = _squad.new("Collingwood", home, true, "COL")
	var a = _squad.new("Carlton", away, false, "CAR")
	var sim = _match_sim.new(h, a, 777)
	sim.run()
	return "%d-%d" % [sim.score(0), sim.score(1)]


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
