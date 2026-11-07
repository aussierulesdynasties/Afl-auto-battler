extends RefCounted
## Row 75: Sir Doug Nicholls Round (SirDougRound).
## A seeded career marks Round 11 as the round, a club with a bye in it marks
## it the next round (2.73), every club has a design slot ("none" until designs
## exist), the record survives a save and reload unchanged, an old save loads,
## and the fixture page and the hub's match card name the round on a phone.
## Run through run_sir_doug_round_tests.gd.

const SEED := 7501
const CLUB := "ESS"

var failures: Array[String] = []
var checks := 0
var root: Window
var _tree: SceneTree
var gs


func _check(ok: bool, msg: String) -> void:
	checks += 1
	if not ok:
		failures.append(msg)
		push_error(msg)


func _settle() -> void:
	for i in 4:
		await _tree.process_frame


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func run(tree: SceneTree) -> void:
	root = tree.root
	_tree = tree
	gs = GameState
	failures.clear()
	checks = 0
	root.size = Vector2i(390, 844)
	GameState.replay_seed = SEED
	_t("_test_round_and_slots")
	_t("_test_bye_next_round")
	_t("_test_back_to_back_byes")
	_t("_test_save_reload_keeps_record")
	_t("_test_old_save")
	_t("_test_new_season")
	_t("_test_round_match_marked")
	await _t("_test_fixture_page")
	await _t("_test_hub_card")
	GameState.replay_seed = 0
	print(Ran.line("Sir Doug Nicholls Round", self))


func _new_career() -> void:
	gs.reset()
	gs.replay_seed = SEED
	gs.start_season(CLUB, GameDB.club_list(CLUB))
	gs.set_setting("seen_weekly_loop_intro", true)
	gs.tutorials = false


func _test_round_and_slots() -> void:
	_new_career()
	_check(SirDougRound.round_of(gs) == 10, "Round 11 is Sir Doug Nicholls Round (%d)" % SirDougRound.round_of(gs))
	var rec: Dictionary = gs.sir_doug
	_check(int(rec.get("year", 0)) == gs.season_year, "The record is for this season (%s)" % str(rec.get("year")))
	var designs: Dictionary = rec.get("designs", {})
	_check(gs.season.clubs.size() >= 18 and designs.size() == gs.season.clubs.size(),
			"Every club has a design slot (%d of %d)" % [designs.size(), gs.season.clubs.size()])
	var all_none := true
	for c in gs.season.clubs:
		all_none = all_none and SirDougRound.design_of(gs, str(c)) == SirDougRound.NO_DESIGN
	_check(all_none, "With no designs in the game, every slot is \"none\"")
	var played: Array = gs.season.fixture[10]
	_check(not played.is_empty(), "Round 11 has matches")
	var marked := true
	for m in played:
		marked = marked and SirDougRound.marks(gs, 10, str(m["home"]), str(m["away"]))
	_check(marked, "Every match of Round 11 is part of the round")
	var other := true
	for m in gs.season.fixture[3]:
		other = other and not SirDougRound.marks(gs, 3, str(m["home"]), str(m["away"]))
	_check(other, "Round 4's matches are not")


## 2.73: a club with a bye in the round marks it the next round.
func _test_bye_next_round() -> void:
	_new_career()
	var r := SirDougRound.round_of(gs)
	# Give two clubs a bye in the round, whatever the seed drew.
	var rnd: Array = gs.season.fixture[r]
	var m: Dictionary = rnd.pop_back()
	var a := str(m["home"])
	var b := str(m["away"])
	_check(SirDougRound.byes_in(gs.season, r).has(a) and SirDougRound.byes_in(gs.season, r).has(b),
			"The two clubs have a bye in Round 11")
	_check(SirDougRound.round_for(gs, a) == r + 1 and SirDougRound.round_for(gs, b) == r + 1,
			"A club with a bye marks the round the next round")
	var late := SirDougRound.after_bye(gs, r + 1)
	_check(late.has(a) and late.has(b), "Round 12 names the clubs marking it after their bye (%s)" % str(late))
	var playing := ""
	for x in gs.season.fixture[r]:
		playing = str(x["home"])
		break
	_check(playing != "" and SirDougRound.round_for(gs, playing) == r, "A club that plays marks it in the round itself")
	var ok12 := false
	for x in gs.season.fixture[r + 1]:
		if str(x["home"]) == a or str(x["away"]) == a:
			ok12 = SirDougRound.marks(gs, r + 1, str(x["home"]), str(x["away"]))
	_check(ok12, "The bye club's Round 12 match is marked")


## At 19 or 21 clubs a club's two byes can fall back to back (Season._level_rounds
## keeps them apart only where the rounds allow it): it marks the round in the
## first round it plays, and Round 12 does not name it.
func _test_back_to_back_byes() -> void:
	_new_career()
	var r := SirDougRound.round_of(gs)
	var rnd: Array = gs.season.fixture[r]
	var a := str((rnd.pop_back() as Dictionary)["home"])
	var nxt: Array = gs.season.fixture[r + 1]
	for i in range(nxt.size() - 1, -1, -1):
		if str(nxt[i]["home"]) == a or str(nxt[i]["away"]) == a:
			nxt.remove_at(i)
	_check(SirDougRound.byes_in(gs.season, r).has(a) and SirDougRound.byes_in(gs.season, r + 1).has(a),
			"The club has byes in Rounds 11 and 12")
	var plays_r2 := not SirDougRound.byes_in(gs.season, r + 2).has(a)
	_check(plays_r2, "...and plays Round 13")
	_check(SirDougRound.round_for(gs, a) == r + 2, "It marks the round in Round 13 (%d)" % SirDougRound.round_for(gs, a))
	_check(not SirDougRound.after_bye(gs, r + 1).has(a), "Round 12 does not name it")
	_check(SirDougRound.after_bye(gs, r + 2).has(a), "Round 13 names it")


## "Store the selected season design in the save so reloading cannot change it."
func _test_save_reload_keeps_record() -> void:
	_new_career()
	# A record written by another build (another round, a stored design id).
	gs.sir_doug = {"year": gs.season_year, "round": 12, "designs": {CLUB: "ess-test-01"}}
	_check(gs.save_career(), "The career saves")
	_check(gs.load_career(), "...and loads")
	_check(SirDougRound.round_of(gs) == 12, "The saved round is read back, not recomputed (%d)" % SirDougRound.round_of(gs))
	_check(SirDougRound.design_of(gs, CLUB) == "ess-test-01", "The saved design id is read back")
	_check(SirDougRound.design_of(gs, "COL") == SirDougRound.NO_DESIGN, "A club missing from the record gets \"none\"")


func _test_old_save() -> void:
	_new_career()
	_check(gs.save_career(), "A career saves")
	# Strip the key, as a save written before row 75 has none.
	var state := CareerSave.read(gs.save_path)
	var meta := CareerSave.read_meta(gs.save_path)
	state.erase("sir_doug")
	_check(CareerSave.write(state, meta, gs.save_path), "The old-style save is written")
	_check(gs.load_career(), "An old save loads")
	_check(gs.sir_doug.is_empty(), "It starts with no record")
	_check(SirDougRound.round_of(gs) == SirDougRound.ROUND, "The round is set for its season on first use")
	_check(gs.save_career() and gs.load_career() and int(gs.sir_doug.get("round", -1)) == SirDougRound.ROUND,
			"...and saved from then on")


func _test_new_season() -> void:
	_new_career()
	gs.sir_doug = {"year": gs.season_year - 1, "round": 4, "designs": {}}
	_check(SirDougRound.round_of(gs) == SirDougRound.ROUND and int(gs.sir_doug["year"]) == gs.season_year,
			"Last season's record is replaced by this season's")


## The round's first fixtured match is marked as in the round.
func _test_round_match_marked() -> void:
	_new_career()
	var m: Dictionary = gs.season.fixture[SirDougRound.ROUND][0]
	_check(SirDougRound.marks(gs, SirDougRound.ROUND, str(m["home"]), str(m["away"])), "The match is in the round")


func _labels(n: Node) -> String:
	var out := PackedStringArray()
	for l in n.find_children("*", "Label", true, false):
		out.append((l as Label).text)
	return "\n".join(out)


func _inside(c: Control, w: int) -> bool:
	var r := c.get_global_rect()
	return r.position.x >= 0.0 and r.end.x <= float(w) + 0.5


## Open the fixture on round `ri` (0-based), as the round picker does.
func _open_fixture(fix, ri: int) -> Control:
	fix.reset()
	fix._stamp = "%d/%d/%d" % [gs.season.round_index, 0, 0]
	fix._page = ri
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	return s


func _test_fixture_page() -> void:
	_new_career()
	var r := SirDougRound.round_of(gs)
	var fix = load("res://scripts/ui/stats/StatsFixture.gd")
	load("res://scripts/ui/StatsHubScene.gd").current = "fixture"
	var s: Control = await _open_fixture(fix, r)
	var picker: Button = s.find_child("RoundPicker", true, false)
	_check(picker != null and picker.text == "Round 11", "The fixture is on Round 11 (%s)" % (picker.text if picker else "-"))
	var name_l: Label = s.find_child("SirDougRoundName", true, false)
	var blurb: Label = s.find_child("SirDougRoundBlurb", true, false)
	_check(name_l != null and name_l.text == "Sir Doug Nicholls Round", "Round 11's fixture page names the round")
	_check(blurb != null and blurb.text.contains("Aboriginal and Torres Strait Islander"), "...with its one factual line")
	_check(name_l != null and blurb != null and _inside(name_l, 390) and _inside(blurb, 390)
			and blurb.get_line_count() >= 2, "Both fit a 390-wide phone, the line wrapped")
	s.queue_free()
	await _settle()
	# Round 4: nothing.
	s = await _open_fixture(fix, 3)
	_check(s.find_child("SirDougRoundName", true, false) == null and not _labels(s).contains("Sir Doug"),
			"Round 4's page says nothing about it")
	s.queue_free()
	await _settle()
	# A club with a bye in Round 11: Round 12's page names it (2.73). The
	# seed's fixture may already rest two clubs there; if not, one match is
	# taken out so two do (as an 18-club bye round has).
	var m := {}
	var resting := SirDougRound.byes_in(gs.season, r)
	if resting.is_empty():
		m = (gs.season.fixture[r] as Array).pop_back()
		resting = [str(m["home"]), str(m["away"])]
	_check(resting.size() == 2, "Two clubs rest in Round 11 (%s)" % str(resting))
	s = await _open_fixture(fix, r + 1)
	var late: Label = s.find_child("SirDougAfterBye", true, false)
	_check(late != null and late.text.begins_with("Sir Doug Nicholls Round after the bye: ") and late.get_line_count() == 1
			and late.text.contains(GameDB.club_short(str(resting[0]))) and late.text.contains(GameDB.club_short(str(resting[1])))
			and late.text.contains(" and "),
			"Round 12's page names the clubs marking it after their bye (%s)" % (late.text if late else "-"))
	_check(late != null and _inside(late, 390), "...within a 390-wide phone")
	s.queue_free()
	await _settle()
	if not m.is_empty():
		(gs.season.fixture[r] as Array).append(m)


func _test_hub_card() -> void:
	_new_career()
	gs.season.round_index = SirDougRound.round_for(gs, CLUB)
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	var name_l: Label = hub.find_child("SirDougContext", true, false)
	_check(name_l != null and name_l.text == "Sir Doug Nicholls Round", "Your match card names the round in its week")
	_check(hub.find_child("SirDougBlurb", true, false) == null and not _labels(hub).contains("Yorta Yorta"),
			"...by name only (the factual line is on the fixture page)")
	_check(name_l != null and _inside(name_l, 390), "It fits a 390-wide phone")
	hub.queue_free()
	await _settle()
	gs.season.round_index = 3
	hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	_check(hub.find_child("SirDougContext", true, false) == null, "Round 4's card says nothing about it")
	hub.queue_free()
	await _settle()
	# Your Round 12 opponent marks it after its bye: your card does not repeat
	# the round (only the club off the bye marks it, 2.73).
	var r := SirDougRound.round_of(gs)
	if SirDougRound.round_for(gs, CLUB) != r:
		return
	var opp := ""
	for x in gs.season.fixture[r + 1]:
		if str(x["home"]) == CLUB:
			opp = str(x["away"])
		elif str(x["away"]) == CLUB:
			opp = str(x["home"])
	var rnd: Array = gs.season.fixture[r]
	for i in range(rnd.size() - 1, -1, -1):
		if (str(rnd[i]["home"]) == opp or str(rnd[i]["away"]) == opp) and not (str(rnd[i]["home"]) == CLUB or str(rnd[i]["away"]) == CLUB):
			rnd.remove_at(i)
	_check(opp != "" and SirDougRound.round_for(gs, opp) == r + 1 and SirDougRound.round_for(gs, CLUB) == r,
			"Your Round 12 opponent (%s) marks it after its Round 11 bye" % opp)
	gs.season.round_index = r + 1
	hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	_check(hub.find_child("SirDougContext", true, false) == null, "Your Round 12 card does not name the round a second week")
	hub.queue_free()
	await _settle()
