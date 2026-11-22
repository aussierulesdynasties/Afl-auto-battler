extends SceneTree
## godot --headless --path . --script tests/run_tipping_tests.gd
## The papers' tipping panel (Tipping.gd, director 2026-11-21): every tip comes
## from the match's facts (strength, ladder, percentage, form, home ground),
## the panel splits only when those facts pull different ways, and the match
## preview shows it under the line against line, readable on a narrow phone.

var _state: Node
var _checks := 0
var _failures: Array[String] = []
const SUITE_SEED := 2031
var T


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	T = load("res://scripts/sim/Tipping.gd")
	_state.autosave_enabled = false
	_state.event_sheets = false
	_state.save_path = "user://test_tipping.save"
	_state.settings_path = "user://test_tipping_settings.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_t("_test_facts_decide")
	_t("_test_split_only_when_close")
	_t("_test_headline")
	await _t("_test_preview_shows_tips", [Vector2i(360, 780)])
	await _t("_test_preview_shows_tips", [Vector2i(412, 915)])
	_state.replay_seed = 0
	print(Ran.line("Tipping", self))
	quit(0 if _failures.is_empty() else 1)


func _side(code: String, strength: float, pos: int, pct: float, form: float, edge: bool, played := 10) -> Dictionary:
	return {"code": code, "strength": strength, "pos": pos, "pct": pct, "played": played, "form": form, "edge": edge}


## The same facts give the same tips; a clearly better side in form at home
## gets all five; reversing every fact reverses every tip; form alone can turn
## a close tip.
func _test_facts_decide() -> void:
	var good := _side("COL", 62.0, 2, 130.0, 0.8, true)
	var poor := _side("WCE", 52.0, 16, 75.0, -0.7, false)
	var a: Array = T.panel(good, poor)
	_check(a == T.panel(good, poor), "The same facts always give the same tips")
	_check(a.size() == 5 and a.all(func(t): return str(t["pick"]) == "COL"), "A strong side in form at home: all five tip it")
	var flip_h := good.duplicate()
	flip_h["edge"] = false
	var flip_a := poor.duplicate()
	flip_a["edge"] = true
	var b: Array = T.panel(flip_a, flip_h)
	_check(b.all(func(t): return str(t["pick"]) == "COL"), "Which side is listed first changes nothing but the ground")
	var big: int = a.map(func(t): return int(t["margin"])).max()
	_check(big >= 25 and big <= int(T.MAX_MARGIN), "A mismatch is tipped by a big margin (%d)" % big)
	# Two even sides on neutral ground: form decides it, both ways.
	var x := _side("ADE", 57.0, 8, 102.0, 0.6, false)
	var y := _side("PAD", 57.0, 9, 101.0, -0.6, false)
	_check(T.panel(x, y).all(func(t): return str(t["pick"]) == "ADE"), "Even sides: the one in form gets the tips")
	x["form"] = -0.6
	y["form"] = 0.6
	_check(T.panel(x, y).all(func(t): return str(t["pick"]) == "PAD"), "Swap the form and the tips swap")
	for t in a:
		_check(str(t["name"]) != "" and str(t["outlet"]) != "", "%s has a name and an outlet" % str(t["journalist"]))


## A close match with the facts pulling two ways splits the panel; the split
## comes from the facts (no randomness: no seed, and the same answer twice).
## Before round 1 the ladder says nothing.
func _test_split_only_when_close() -> void:
	# The better list, out of form, away; the weaker list, hot, at home.
	var hot_home := _side("GEE", 54.0, 6, 112.0, 0.9, true)
	var cold_class := _side("SYD", 59.0, 5, 115.0, -0.8, false)
	var tips: Array = T.panel(hot_home, cold_class)
	var t: Dictionary = T.tally(tips, "GEE", "SYD")
	_check(int(t["GEE"]) > 0 and int(t["SYD"]) > 0,
			"Facts pulling both ways split the panel (%d-%d)" % [int(t["GEE"]), int(t["SYD"])])
	_check(tips == T.panel(hot_home, cold_class), "The split is the same every time")
	# Dev trusts the list, Kev the form and the crowd.
	var by := {}
	for tip in tips:
		by[str(tip["journalist"])] = str(tip["pick"])
	_check(by["stats"] == "SYD" and by["bogan"] == "GEE", "The ratings man takes the list, the radio man the form")
	# Round 1: no games, so the ladder and percentage are ignored.
	var r1a := _side("BRL", 56.0, 18, 0.0, 0.0, false, 0)
	var r1b := _side("CAR", 56.0, 1, 999.0, 0.0, false, 0)
	_check(is_zero_approx(T.lean("muckraker", r1a, r1b)), "Before a game the ladder counts for nothing")
	_check(T.panel(r1a, r1b).all(func(x): return int(x["margin"]) >= 1), "A dead-level tip still has a margin")


func _test_headline() -> void:
	var names := {"COL": "Collingwood", "WCE": "West Coast"}
	var all_col := []
	for i in range(5):
		all_col.append({"pick": "COL"})
	_check(T.headline(all_col, names) == "All five tip Collingwood.", "All five: %s" % T.headline(all_col, names))
	all_col[0] = {"pick": "WCE"}
	all_col[3] = {"pick": "WCE"}
	_check(T.headline(all_col, names) == "Three of five tip Collingwood.", "A split: %s" % T.headline(all_col, names))


## The match preview's comparison carries the panel: the headline matches the
## picks, five rows each naming one of the two clubs, nothing wider than the phone.
func _test_preview_shows_tips(size: Vector2i) -> void:
	var db = root.get_node("GameDB")
	_state.reset()
	_state.career_seed = SUITE_SEED
	_state.replay_seed = SUITE_SEED
	_state.start_season("GWS", db.club_list("GWS"))
	for i in range(4):
		_state.advance()
	root.size = size
	var router = root.get_node("Router")
	router.stack = []
	router.go("preview")
	for i in range(8):
		await process_frame
	var pv: Node = current_scene
	var box: Control = pv.find_child("Tips", true, false) if pv != null else null
	_check(box != null, "The match preview shows the tips at %s" % str(size))
	if box == null:
		return
	var h2h: Control = pv.find_child("HeadToHead", true, false)
	_check(h2h != null and h2h.get_parent() == box.get_parent() and box.get_index() > h2h.get_index(),
			"The tips sit under the line against line, on the same page")
	var m: Dictionary = load("res://scripts/ui/MatchKickoff.gd").upcoming_match()
	var rows := box.find_children("Tip_*", "Control", true, false)
	_check(rows.size() == 5, "Five tips (%d)" % rows.size())
	var count := {}
	var page_w := float(size.x)
	for r in rows:
		var pick := str(r.get_meta("pick"))
		count[pick] = int(count.get(pick, 0)) + 1
		_check(pick == str(m["home"]) or pick == str(m["away"]), "Each tip is one of the two clubs")
		var said: Label = r.find_child("TipPick", true, false)
		_check(said != null and said.text == "%s by %d" % [db.club_short(pick), int(r.get_meta("margin"))],
				"The pick reads like a tipping panel: %s" % (said.text if said != null else "none"))
		var rect: Rect2 = (r as Control).get_global_rect()
		_check(rect.position.x >= 0.0 and rect.end.x <= page_w + 0.5, "A tip row fits the phone (%s)" % str(rect))
		if said != null:
			_check(said.get_global_rect().end.x <= page_w + 0.5 and said.get_line_count() == 1,
					"The pick stays on one line inside the screen")
	var head: Label = box.find_child("TipsHeadline", true, false)
	var top := ""
	for c in count:
		if top == "" or int(count[c]) > int(count[top]):
			top = str(c)
	_check(head != null and head.text.ends_with("tip %s." % db.club_name(top)),
			"The headline names the side most tip (%s)" % (head.text if head != null else "none"))
	pv.queue_free()
	for i in range(3):
		await process_frame


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
