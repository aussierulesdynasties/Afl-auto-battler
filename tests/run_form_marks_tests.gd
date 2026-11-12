extends SceneTree
## godot --headless --path . --script tests/run_form_marks_tests.gd
## Form marks on Team selection (director, 2026-11-12: "team select should
## highlight the 3 players in the side in the worst form, and the 3 players in
## reserve in the best form"; a reserve's form is "Reserves games"). The
## reserves game (ReservesForm) is seeded and recorded, survives a save, and an
## older save loads without it; the marks pick the right three and three, and a
## real tap at 390x844 opens a marked player's numbers.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 5127

var _checks := 0
var _failures: Array = []
var _gs: Node
var _db: Node
var _router: Node
var _rf: GDScript


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
	_rf = load("res://scripts/sim/ReservesForm.gd")
	_gs.autosave_enabled = false
	_gs.event_sheets = false
	_gs.save_path = "user://test_form_marks.save"
	_gs.settings_path = "user://test_form_marks.cfg"
	_gs.replay_seed = SUITE_SEED
	_t("_test_game_is_seeded")
	_t("_test_marks_pick")
	_t("_test_recorded_and_saved")
	await _t("_test_selection_marks_taps")
	print(Ran.line("FormMarks", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(0 if _failures.is_empty() else 1)


func _fresh(club: String) -> void:
	_gs.reset()
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_gs.set_setting("seen_%s_intro" % key, true)
	_gs.career_seed = SUITE_SEED
	_gs.replay_seed = SUITE_SEED
	_gs.start_season(club, _db.club_list(club))


## The same player, match and career roll the same game; the rating is on the
## senior scale and the words are football's.
func _test_game_is_seeded() -> void:
	var p := {"id": "x", "role": "FWD", "overall": 70}
	var a: Dictionary = _rf.game(p, _rf.seed_for(1, "2026|R1", "x"))
	var b: Dictionary = _rf.game(p, _rf.seed_for(1, "2026|R1", "x"))
	_check(a == b, "One seed, one game (%s, %s)" % [str(a), str(b)])
	var differs := false
	var sum := 0.0
	for i in range(200):
		var g: Dictionary = _rf.game(p, _rf.seed_for(1, "2026|R%d" % i, "x"))
		sum += float(g["pts"])
		if g != a:
			differs = true
	_check(differs, "Another week rolls another game")
	var mean := sum / 200.0
	_check(mean > 40.0 and mean < 140.0, "A forward's twos game rates on the senior scale (mean %.1f)" % mean)
	var ruck: Dictionary = _rf.game({"id": "r", "role": "RUCK", "overall": 72}, 99)
	_check(int(ruck["h"]) >= 10 and _rf.line(ruck).contains("hitouts"), "A ruck's line counts his hitouts (%s)" % _rf.line(ruck))
	var words: String = _rf.line({"pts": 80, "d": 22, "g": 3, "h": 0})
	_check(words == "Kicked 3 and 22 touches in the twos", "The line in football words (%s)" % words)


## The coldest three in the side by their gap to their own season, and the
## hottest three fit reserves who played in the twos at the latest match;
## fewer qualify, fewer marked.
func _test_marks_pick() -> void:
	var form := {
		"a": {"last": [40, 40, 40], "sum": 600, "n": 10},    # -20
		"b": {"last": [50, 50, 50], "sum": 800, "n": 10},    # -30
		"c": {"last": [70, 70, 70], "sum": 600, "n": 10},    # +10: not cold
		"d": {"last": [55, 55, 55], "sum": 600, "n": 10},    # -5
		"e": {"last": [30, 30, 30], "sum": 400, "n": 10},    # -10
		"f": {"last": [10, 10, 10], "sum": 400, "n": 4},     # too few games
	}
	var g := func(pts: int) -> Dictionary: return {"pts": pts, "d": 20, "g": 1, "h": 0}
	var res := {
		"r1": {"last": [g.call(80), g.call(80), g.call(80)], "sum": 350, "n": 5, "key": "K"},    # +10
		"r2": {"last": [g.call(60), g.call(70), g.call(80)], "sum": 300, "n": 5, "key": "K"},    # +10
		"r3": {"last": [g.call(100), g.call(100), g.call(100)], "sum": 300, "n": 5, "key": "OLD"},   # not in the twos last week
		"r4": {"last": [g.call(50), g.call(50), g.call(50)], "sum": 240, "n": 5, "key": "K"},    # +2
		"r5": {"last": [g.call(75), g.call(75), g.call(75)], "sum": 300, "n": 5, "key": "K"},    # +15
		"r6": {"last": [g.call(90), g.call(90), g.call(90)], "sum": 270, "n": 3, "key": "K"},    # too few games
		"r7": {"last": [g.call(40), g.call(40), g.call(40)], "sum": 300, "n": 5, "key": "K"},    # -20: not hot
	}
	var m: Dictionary = _rf.marks(["a", "b", "c", "d", "e", "f"], ["r1", "r2", "r3", "r4", "r5", "r6", "r7"], form, res, "K")
	var cold: Array = (m["cold"] as Dictionary).keys()
	cold.sort()
	_check(cold == ["a", "b", "e"], "The three furthest below their season (%s)" % str(cold))
	var hot: Array = (m["hot"] as Dictionary).keys()
	hot.sort()
	_check(hot == ["r1", "r2", "r5"], "The three furthest above their reserves season, in the twos last week (%s)" % str(hot))
	_check(_rf.cold_short(m["cold"]["b"]) == "Form -30", "The tile says the gap (%s)" % _rf.cold_short(m["cold"]["b"]))
	_check(_rf.hot_short(m["hot"]["r5"]) == "Form +15", "A reserve's card says his gap the same way (%s)" % _rf.hot_short(m["hot"]["r5"]))
	var few: Dictionary = _rf.marks(["c", "d"], ["r3", "r4"], form, res, "K")
	_check((few["cold"] as Dictionary).keys() == ["d"] and (few["hot"] as Dictionary).keys() == ["r4"],
			"Fewer qualify, fewer marked (%s)" % str(few))
	for s in [_rf.cold_full(m["cold"]["a"]), _rf.hot_full(m["hot"]["r2"]), _rf.hot_short(m["hot"]["r2"])]:
		var low := str(s).to_lower()
		for w in ["drop", "bring in", "swap", "should", "recommend"]:
			_check(not low.contains(w), "A mark states facts, not advice: '%s' in %s" % [w, s])


## A season's weeks: every fit player left out plays in the twos, rated and
## remembered; a save keeps it; an older save loads with none; the senior game
## and the XP are those of a career with the record wiped each week.
func _test_recorded_and_saved() -> void:
	_fresh("FRE")
	for i in range(3):
		_gs.advance()
	var rows: Array = _gs.last_training_report.get("rows", [])
	var res_ids := []
	for r in rows:
		if bool(r.get("reserves", false)):
			res_ids.append(str(r["id"]))
	_check(not res_ids.is_empty(), "Some fit players were left out (%d)" % res_ids.size())
	var all_in := true
	var none_in_side := true
	for r in rows:
		var id := str(r["id"])
		var this_week: bool = _gs.reserves_log.has(id) and str(_gs.reserves_log[id]["key"]) == _gs._xp_grant_key
		if bool(r.get("reserves", false)) and not this_week:
			all_in = false
		if (bool(r.get("on_ground", false)) or bool(r.get("on_bench", false))) and this_week:
			none_in_side = false
	_check(all_in, "Every player in the twos this week has a game recorded")
	_check(none_in_side, "A player in the 23 has no twos game that week")
	var one: Dictionary = _gs.reserves_log[res_ids[0]] if not res_ids.is_empty() else {}
	_check(not one.is_empty() and (one["last"] as Array).size() <= _rf.GAMES and int(one["n"]) >= 1,
			"His record keeps the last three games and the count")
	# The same career, replayed: the same twos games.
	var first := _sig(_gs.reserves_log)
	var senior := _senior_sig()
	_fresh("FRE")
	for i in range(3):
		_gs.advance()
	_check(_sig(_gs.reserves_log) == first, "A replay of the career rolls the same twos games")
	_check(_senior_sig() == senior, "...and the same senior games and XP")
	# Wiping the twos each week changes nothing else: it is display only.
	_fresh("FRE")
	for i in range(3):
		_gs.reserves_log = {}
		_gs.advance()
	_check(_senior_sig() == senior, "The twos record moves no senior game, XP or rating")
	_fresh("FRE")
	for i in range(3):
		_gs.advance()
	_check(_gs.save_career(), "The career saves")
	_check(_gs.load_career(), "...and loads")
	_check(_sig(_gs.reserves_log) == first, "The twos record survives a save and load")
	var state: Dictionary = _gs._save_state()
	state.erase("reserves_log")
	_check(_gs._restore_career(state), "An older save, without the twos record, loads")
	_check(_gs.reserves_log.is_empty(), "...with no twos games")
	_check((_gs.form_marks(_gs.current_side())["hot"] as Dictionary).is_empty(), "...and no reserves marks")


func _sig(log: Dictionary) -> String:
	var keys := log.keys()
	keys.sort()
	var parts := []
	for k in keys:
		var f: Dictionary = log[k]
		var pts := []
		for g in f["last"]:
			pts.append("%d/%d/%d/%d" % [int(g["pts"]), int(g["d"]), int(g["g"]), int(g["h"])])
		parts.append("%s:%d:%d:%s" % [k, int(f["sum"]), int(f["n"]), ",".join(pts)])
	return ";".join(parts)


func _senior_sig() -> String:
	var parts := []
	for res in _gs.season.results:
		parts.append(str(str(res).hash()))
	for p in _gs.my_list:
		parts.append("%s:%d:%d" % [str(p["id"]), int(p.get("xp", 0)), int(p.get("overall", 0))])
	return str(hash(str(parts) + JSON.stringify(_gs.form_log, "", true)))


## At 390x844, three tiles in the side carry their form gap and three cards in
## the twos their reserves form; a real tap on a marked tile, then on Profile,
## opens his numbers. No advice anywhere.
func _test_selection_marks_taps() -> void:
	_fresh("FRE")
	for i in range(6):
		_gs.advance()
	root.size = Vector2i(390, 844)
	var side: Dictionary = _gs.current_side()
	var expect: Dictionary = _gs.form_marks(side)
	_check((expect["cold"] as Dictionary).size() == 3, "Six rounds in, three in the side are below their season (%d)" % (expect["cold"] as Dictionary).size())
	_check((expect["hot"] as Dictionary).size() >= 1 and (expect["hot"] as Dictionary).size() <= 3, "...and up to three in the twos are marked (%d)" % (expect["hot"] as Dictionary).size())
	_router.go("selection")
	await _settle(10)
	var scene: Node = current_scene
	var colds: Array = scene.find_children("FormCold_*", "Label", true, false)
	var hots: Array = scene.find_children("FormHot_*", "Label", true, false)
	var cold_ids := colds.map(func(l): return str(l.name).trim_prefix("FormCold_"))
	var hot_ids := hots.map(func(l): return str(l.name).trim_prefix("FormHot_"))
	cold_ids.sort()
	hot_ids.sort()
	var want_cold: Array = (expect["cold"] as Dictionary).keys()
	var want_hot: Array = (expect["hot"] as Dictionary).keys()
	want_cold.sort()
	want_hot.sort()
	_check(cold_ids == want_cold, "The oval marks the three coldest (%s, want %s)" % [str(cold_ids), str(want_cold)])
	_check(hot_ids == want_hot, "The players not picked mark the three hottest in the twos (%s, want %s)" % [str(hot_ids), str(want_hot)])
	var grid: Node = scene.find_child("NotSelected", true, false)
	var lead := []
	for c in (grid.get_children() if grid != null else []):
		if lead.size() < hot_ids.size():
			lead.append(str(c.name).trim_prefix("Card_"))
	lead.sort()
	_check(lead == want_hot, "The three marked in the twos lead the players not picked (%s)" % str(lead))
	for l in colds + hots:
		var low := (l as Label).text.to_lower()
		_check(not low.contains("drop") and not low.contains("bring in") and not low.contains("should")
				and not low.contains("swap"), "A mark is a fact: %s" % (l as Label).text)
	for l in colds:
		_check((l as Label).is_visible_in_tree() and (l as Label).get_global_rect().size.x > 0.0
				and (l as Label).get_parent_control().get_parent_control().get_global_rect().encloses((l as Label).get_global_rect().grow(-1.0)),
				"%s shows inside its tile" % (l as Label).name)
	if colds.is_empty():
		return
	var cid := str((colds[0] as Label).name).trim_prefix("FormCold_")
	var tile: Button = (colds[0] as Label).get_parent().get_parent() as Button
	var why: String = await Tap.tap(tile)
	await _settle()
	_check(why == "", "A real tap reaches the marked tile (%s)" % why)
	var prof: Button = current_scene.find_child("PickedProfile", true, false)
	why = (await Tap.tap(prof)) if prof != null else "missing"
	await _settle()
	_check(why == "", "A real tap on Profile opens him (%s)" % why)
	var form_l: Label = current_scene.find_child("ProfileForm", true, false)
	var r: Dictionary = expect["cold"][cid]
	_check(form_l != null and form_l.is_visible_in_tree()
			and form_l.text.contains("%d a game over his last 3 games" % int(r["recent"]))
			and form_l.text.contains("%d over" % int(r["season"])),
			"His profile gives the mark's numbers: last 3 and the season (%s)" % (form_l.text if form_l else "-"))
	# A reserve's profile carries his twos games.
	var hid: String = want_hot[0] if not want_hot.is_empty() else ""
	if hid != "":
		current_scene.call("_open_profile", hid)
		await _settle()
		var hl: Label = current_scene.find_child("ProfileForm", true, false)
		_check(hl != null and hl.text.contains("Reserves: ") and hl.text.contains("Latest: "),
				"A reserve's profile gives his twos games (%s)" % (hl.text if hl else "-"))
