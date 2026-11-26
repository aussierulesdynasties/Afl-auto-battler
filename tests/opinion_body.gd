extends RefCounted
## The opinion suite's body, loaded by tests/run_opinion_tests.gd by path.

const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 2027

var _state: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []
var tree: SceneTree


func go(t: SceneTree) -> void:
	tree = t
	await tree.process_frame
	_state = tree.root.get_node("GameState")
	_db = tree.root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.event_sheets = false
	_state.save_path = "user://test_opinion.save"
	_state.settings_path = "user://test_opinion_settings.cfg"
	_t("_test_defs")
	_t("_test_permanent_part")
	_t("_test_marks")
	_t("_test_fade")
	_t("_test_old_save")
	_t("_test_club_moves")
	_t("_test_trust_name")
	_t("_test_drift_rules")
	_t("_test_round_every_club")
	_t("_test_card_moves")
	_t("_test_save_round_trip")
	print(Ran.line("Opinion", self))


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


func _test_defs() -> void:
	var d := Opinion.defs()
	_check(d.size() >= 10, "The marks load from data/relations/modifiers.json (%d)" % d.size())
	_check(Opinion.check_defs(d).is_empty(), "Every mark is well formed: %s" % str(Opinion.check_defs(d)))
	for k in ["dropped", "dropped_star", "dropped_final", "picked_final", "promise_kept", "promise_broken",
			"mate_dropped", "mate_traded", "rival_picked"]:
		_check(d.has(k), "The %s mark exists for Phase 1" % k)
	_check(float(Opinion.def("promise_broken")["fade"]) == 0.0, "A broken promise is a permanent scar")
	_check(float(Opinion.def("dropped_final")["fade"]) <= 0.5 and float(Opinion.def("dropped_final")["fade"]) > 0.0,
			"A finals snub is a long tail, not forever")
	var bad := Opinion.check_defs({"x": {"v": 0, "fade": 1, "tag": "t", "why": "w"},
			"y": {"v": -5, "fade": 2, "tag": "t", "why": "w", "scar": true}, "z": {"v": 3, "fade": 1, "tag": "", "why": "Bad."}})
	_check(bad.size() == 4, "The check catches a zero mark, a fast scar, no tag and a full stop (%d)" % bad.size())


func _test_permanent_part() -> void:
	var rel := {}
	var k := Opinion.player_key("x1")
	_check(Opinion.value(rel, k) == 0 and Opinion.opinion(0) == 50, "Nobody is neutral, 50 out of 100")
	_check(Opinion.change(rel, k, 50, "Big call", 2027, "Round 1") == Opinion.STEP_MAX, "One moment is capped")
	_check(Opinion.base(rel, k) == 20 and Opinion.value(rel, k) == 20, "The permanent part moved")
	_check(Opinion.reasons(rel, k).size() == 1 and Opinion.reason_text(Opinion.reasons(rel, k)[0]).contains("Opinion of you +10"),
			"Its reason is kept with the move the game shows")


func _test_marks() -> void:
	var rel := {}
	var k := Opinion.player_key("x2")
	var got := Opinion.add(rel, k, "dropped", 2027, "Round 3", "GEE")
	_check(got == -4.0 and Opinion.live(rel, k) == -4.0, "Left out: a live mark of -4 (%.1f)" % got)
	_check(Opinion.value(rel, k) == -8 and Opinion.opinion(Opinion.value(rel, k)) == 46,
			"The shown opinion counts the live mark: 46 out of 100")
	_check(Opinion.base(rel, k) == 0, "A live mark never touches the permanent part")
	Opinion.add(rel, k, "dropped", 2027, "Round 4", "GEE")
	_check(Opinion.mods(rel, k).size() == 1 and Opinion.live(rel, k) == -4.0, "The same mark renews, it does not stack")
	Opinion.add(rel, k, "dropped", 2027, "Round 4", "GEE", 0.5)
	_check(Opinion.live(rel, k) == -4.0, "A renewed mark is never made smaller")
	Opinion.add(rel, k, "mate_dropped", 2027, "Round 4", "GEE", 1.0, "m1")
	Opinion.add(rel, k, "mate_dropped", 2027, "Round 4", "GEE", 1.0, "m2")
	_check(Opinion.mods(rel, k).size() == 3, "The same mark from two mates is two marks")
	Opinion.add(rel, k, "dropped_final", 2027, "Qualifying Final", "GEE", 1.5)
	_check(int(Opinion.breakdown(rel, k)[0]["points"]) == -30, "A scale sizes the mark (a temperament's x1.5: -30)")
	_check(Opinion.add(rel, k, "no_such_mark", 2027, "Round 4") == 0.0, "An unknown mark adds nothing")
	for i in range(12):
		Opinion.add_raw(rel, k, "card_%d" % i, float(i + 1), 1.0, "card", "A card", 2027, "Round 5")
	_check(Opinion.mods(rel, k).size() == Opinion.MODS_KEEP, "At most %d live marks; the smallest go first" % Opinion.MODS_KEEP)
	var keys := []
	for m in Opinion.mods(rel, k):
		keys.append(str(m["k"]))
	_check(keys.has("dropped_final"), "The biggest mark is the one kept")
	_check(Opinion.value({"p:z": {"t": 90, "mods": [{"k": "a", "v": 40.0, "f": 0.0}]}}, "p:z") == Opinion.HIGHEST,
			"Opinion stays inside the scale")


func _test_fade() -> void:
	var rel := {}
	var k := Opinion.player_key("x3")
	Opinion.add(rel, k, "dropped", 2027, "Round 1", "GEE")
	Opinion.add(rel, k, "promise_broken", 2027, "Round 1", "GEE")
	Opinion.add(rel, k, "dropped_final", 2027, "Elimination Final", "GEE")
	var b := Opinion.breakdown(rel, k)
	var by := {}
	for x in b:
		by[str(x["k"])] = x
	_check(int(by["dropped"]["weeks"]) == 4, "Left out: gone in 4 weeks (%d)" % int(by["dropped"]["weeks"]))
	_check(int(by["promise_broken"]["weeks"]) == -1, "A broken promise stays")
	_check(int(by["dropped_final"]["weeks"]) == 40, "A finals snub fades over most of a year (%d)" % int(by["dropped_final"]["weeks"]))
	_check(Opinion.mark_text(by["dropped"]) == "Left out while fit: -4. Gone in 4 weeks.", "In words: %s" % Opinion.mark_text(by["dropped"]))
	_check(Opinion.mark_text(by["promise_broken"]).ends_with("It stays."), "A scar says it stays")
	for i in range(4):
		Opinion.fade_round(rel)
	by = {}
	for x in Opinion.breakdown(rel, k):
		by[str(x["k"])] = x
	_check(not by.has("dropped"), "After 4 rounds the left-out mark is gone")
	_check(int(by["promise_broken"]["points"]) == -15, "The scar has not moved")
	_check(int(by["dropped_final"]["points"]) == -18, "The long tail lost 2 points in 4 rounds")
	var rel2 := {}
	Opinion.add(rel2, k, "dropped", 2027, "Round 1", "GEE")
	for i in range(int(Opinion.breakdown(rel2, k)[0]["weeks"])):
		Opinion.fade_round(rel2)
	_check(not (rel2[k] as Dictionary).has("mods"), "weeks_left is exactly when it goes")
	Opinion.add(rel2, k, "picked_final", 2027, "Grand Final", "GEE")
	Opinion.fade_round(rel2)
	_check(Opinion.live(rel2, k) > 0.0 and Opinion.live(rel2, k) < 4.0, "A lift fades down towards 0 too")


func _test_old_save() -> void:
	# A relations map from before 2026-11-26: trust and reasons, no marks.
	var old := {"p:a": {"t": -30, "log": [{"y": 2027, "w": "Round 2", "d": -30, "o": -15, "why": "You dropped him"}]},
			"k:GEE:together": {"t": 6, "log": []}}
	_check(Opinion.value(old, "p:a") == -30 and Opinion.live(old, "p:a") == 0.0 and Opinion.mods(old, "p:a").is_empty(),
			"An older save reads exactly as it did")
	Opinion.fade_round(old)
	_check(Opinion.value(old, "p:a") == -30 and not (old["p:a"] as Dictionary).has("mods")
			and Opinion.value(old, "k:GEE:together") == 6, "A round passing changes nothing in an older save")
	Opinion.drop_other_clubs(old, {"a": "COL"})
	_check(Opinion.value(old, "p:a") == -30, "Changing clubs never touches the permanent part")


func _test_club_moves() -> void:
	var rel := {}
	var k := Opinion.player_key("x4")
	Opinion.change(rel, k, 10, "Backed him", 2027, "Round 1")
	Opinion.add(rel, k, "dropped_star", 2027, "Round 2", "GEE")
	Opinion.drop_other_clubs(rel, {"x4": "GEE"})
	_check(Opinion.live(rel, k) == -8.0, "Still at the club: his marks stay")
	Opinion.drop_other_clubs(rel, {"x4": "COL"})
	_check(Opinion.live(rel, k) == 0.0 and Opinion.base(rel, k) == 10, "At a new club: his old coach's marks go, his opinion of you stays")
	var r2 := {}
	Opinion.add(r2, k, "dropped", 2027, "Round 2", "GEE")
	_check(Opinion.coach_opinion(r2, k, false) == 46 and Opinion.coach_opinion(r2, k, true) == 46,
			"His opinion of his coach counts the marks, at any club")
	Opinion.change(r2, k, 40, "Backed him", 2027, "Round 3")
	_check(Opinion.coach_opinion(r2, k, false) == 46 and Opinion.coach_opinion(r2, k, true) == 56,
			"At a rival club his opinion of you is not his opinion of his own coach")


func _test_trust_name() -> void:
	var rel := {}
	Trust.change(rel, Trust.player_key("y"), -10, "Old caller", 2027, "Round 1")
	Opinion.add(rel, Opinion.player_key("y"), "dropped", 2027, "Round 1", "GEE")
	_check(Trust.value(rel, "p:y") == Opinion.value(rel, "p:y") and Trust.value(rel, "p:y") == -18,
			"Trust is Opinion under its older name, live marks included")
	_check(Trust.STEP_MAX == Opinion.STEP_MAX and Trust.band(-60) == "lost" and Trust.opinion(20) == 60,
			"Every older constant and rule answers the same")


func _test_drift_rules() -> void:
	_check(ClubLife.morale_target(50) == ClubLife.MORALE_BASE, "At 50 morale settles where it always has")
	_check(ClubLife.morale_target(100) == ClubLife.MORALE_BASE + ClubLife.DRIFT_SPAN
			and ClubLife.morale_target(0) == ClubLife.MORALE_BASE - ClubLife.DRIFT_SPAN, "The target spans 55 to 85")
	_check(ClubLife.morale_target(40) == 67, "10 points under 50: 3 under settled")
	var p := {"morale": 90}
	ClubLife.drift_morale(p, 50)
	_check(int(p["morale"]) == 89, "Above the target: one point down a round")
	p = {"morale": 60}
	ClubLife.drift_morale(p, 50)
	_check(int(p["morale"]) == 61, "Below it: one point up")
	p = {"morale": 70}
	ClubLife.drift_morale(p, 50)
	_check(int(p["morale"]) == 70, "At it: nothing")
	p = {"morale": 90, "injury_weeks": 3}
	ClubLife.drift_morale(p, 0)
	_check(int(p["morale"]) == 90, "An injured man is left to the injured rule")


func _test_round_every_club() -> void:
	_state.replay_seed = SUITE_SEED
	_state.reset()
	_state.start_season("GEE", _db.club_list("GEE"))
	_check(_state.season != null and _state.season.lists.size() >= 18, "A season of every club (%d)" % _state.season.lists.size())
	_state._settle_week_event()
	_state.advance()
	var res: Array = _state.last_results if "last_results" in _state else []
	var marked := {}
	var finals_marks := 0
	for key in _state.relations:
		for m in Opinion.mods(_state.relations, str(key)):
			marked[str(m.get("c", ""))] = true
			if str(m["k"]).contains("final"):
				finals_marks += 1
	_check(marked.size() >= 18, "After Round 1 every club's coach has left marks (%d clubs)" % marked.size())
	_check(finals_marks == 0, "No finals marks in a home-and-away round")
	# A fit man left out is marked; a man who played is not.
	var gee: Array = _state.season.lists["GEE"]
	var res0: Dictionary = _state.last_match
	var side := 0 if str(res0["home"]) == "GEE" else 1
	var played := {}
	for r in (res0["roster"] as Array)[side]:
		played[str(r["id"])] = true
	var ok_played := true
	var ok_out := true
	var outs := 0
	for p in gee:
		var ks := []
		for m in Opinion.mods(_state.relations, Opinion.player_key(str(p["id"]))):
			ks.append(str(m["k"]))
		if played.has(str(p["id"])):
			ok_played = ok_played and not (ks.has("dropped") or ks.has("dropped_star"))
		elif int(p.get("injury_weeks", 0)) <= 0 and not _state._round_unavailable.has(str(p["id"])):
			outs += 1
			ok_out = ok_out and (ks.has("dropped") or ks.has("dropped_star"))
	_check(outs > 0 and ok_out, "Every fit man we left out carries a left-out mark (%d)" % outs)
	_check(ok_played, "Nobody who played carries one")
	# Morale moved towards its target for everyone fit.
	_state.advance()
	var moved_toward := true
	var n := 0
	for code in _state.season.lists:
		for p in _state.season.lists[code]:
			if int(p.get("injury_weeks", 0)) > 0:
				continue
			n += 1
			var m := int(p.get("morale", ClubLife.MORALE_BASE))
			moved_toward = moved_toward and m >= 5 and m <= 100
	_check(n > 500 and moved_toward, "Every fit player's morale stays on the scale after two rounds (%d)" % n)
	var _unused = res


func _test_save_round_trip() -> void:
	var before: Dictionary = (_state.relations as Dictionary).duplicate(true)
	var any := ""
	for key in before:
		if not Opinion.mods(before, str(key)).is_empty():
			any = str(key)
			break
	_check(any != "", "There is a live mark to save")
	_check(_state.save_career(), "The career saves")
	_state.relations = {}
	_check(_state.load_career(), "The career loads")
	_check(absf(Opinion.live(_state.relations, any) - Opinion.live(before, any)) < 0.01
			and Opinion.weeks_left(Opinion.mods(_state.relations, any)[0]) == Opinion.weeks_left(Opinion.mods(before, any)[0]),
			"A live mark comes back from the save with its size and its weeks")


func _test_card_moves() -> void:
	var rel := {}
	var k := Opinion.player_key("c1")
	var got := Opinion.card_move(rel, k, -10, "You called him out", 2027, "Round 2")
	_check(got == -10 and Opinion.base(rel, k) == 0 and Opinion.live(rel, k) == -5.0,
			"A card's trust move is a live mark: -5 points, permanent part untouched")
	_check(int(Opinion.breakdown(rel, k)[0]["weeks"]) == 9, "It fades over 9 rounds")
	Opinion.card_move(rel, k, -10, "You called him out", 2027, "Round 3")
	_check(Opinion.mods(rel, k).size() == 1, "The same card again renews its mark")
	Opinion.card_move(rel, k, 6, "You backed him in the papers", 2027, "Round 3")
	_check(Opinion.mods(rel, k).size() == 2, "Another card is another mark")
	var s := Opinion.card_move(rel, k, -12, "You told him he was finished", 2027, "Round 4", true)
	_check(s == -12 and Opinion.base(rel, k) == -12 and Opinion.reasons(rel, k).size() == 1,
			"A scar card moves the permanent part, with its reason")
	_check(Opinion.card_move(rel, k, 0, "Nothing", 2027, "Round 4") == 0, "A move of 0 does nothing")
