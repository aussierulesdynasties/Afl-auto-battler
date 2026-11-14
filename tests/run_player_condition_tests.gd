extends SceneTree
## godot --headless --path . --script tests/run_player_condition_tests.gd
## Fatigue, morale and form as numbers (TODO row 183; director, 2026-11-14:
## team selection "should show a numerical value of their fatigue level", and
## "also need somewhere to display player morale and form as a number too").
## Each number on a selection card and on the player sheet equals the value
## the game keeps (Workload.value, ClubLife.morale, the form log), for two
## players with different loads, morale and form; a real tap at 390x844 opens
## the sheet; a rival's cards show none; the PC cards name each number.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 5183

var _checks := 0
var _failures: Array = []
var _gs: Node
var _db: Node
var _router: Node
var _workload: GDScript
var _club_life: GDScript


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
	_workload = load("res://scripts/sim/Workload.gd")
	_club_life = load("res://scripts/sim/ClubLife.gd")
	_gs.autosave_enabled = false
	_gs.event_sheets = false
	_gs.save_path = "user://test_player_condition.save"
	_gs.settings_path = "user://test_player_condition.cfg"
	_gs.replay_seed = SUITE_SEED
	await _t("_test_numbers_match_the_sim")
	await _t("_test_rival_shows_none")
	await _t("_test_pc_cards_name_them")
	print(Ran.line("PlayerCondition", self))
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


## The form the game keeps for him: his last senior games' rating a game, or
## his twos games when he has no senior game. -1 when neither.
func _kept_form(id: String) -> int:
	var f: Dictionary = _gs.form_log.get(id, {})
	if int(f.get("n", 0)) > 0:
		var t := 0.0
		for x in f["last"]:
			t += float(x)
		return int(round(t / float((f["last"] as Array).size())))
	var r: Dictionary = _gs.reserves_log.get(id, {})
	if int(r.get("n", 0)) > 0:
		var t := 0.0
		for g in r["last"]:
			t += float((g as Dictionary).get("pts", 0))
		return int(round(t / float((r["last"] as Array).size())))
	return -1


func _shown(scene: Node, word: String, id: String) -> Label:
	return scene.find_child("%s_%s" % [word, id], true, false) as Label


## Two players in the side, one carrying a heavy load and flat, one fresh and
## flying, after six rounds of real football (so their form logs differ).
func _two_players() -> Array:
	var side: Dictionary = _gs.current_side()
	var ids: Array = []
	for line in ["MID", "DEF", "FWD"]:
		for id in side.get(line, []):
			var f := _kept_form(str(id))
			if ids.size() < 2 and f >= 0 and (ids.is_empty() or f != _kept_form(str(ids[0]))):
				ids.append(str(id))
	var a: Dictionary = _gs.list_player(ids[0])
	var b: Dictionary = _gs.list_player(ids[1])
	a["workload"] = 61.4
	a["morale"] = 36
	b["workload"] = 7.0
	b["morale"] = 91
	return [a, b]


func _test_numbers_match_the_sim() -> void:
	_fresh("FRE")
	for i in range(6):
		_gs.advance()
	var pair := _two_players()
	_check(_kept_form(str(pair[0]["id"])) != _kept_form(str(pair[1]["id"])), "The two players' form differs")
	root.size = Vector2i(390, 844)
	_router.go("selection")
	await _settle(10)
	var scene: Node = current_scene
	_check(scene.find_child("ConditionKey", true, false) != null, "The key names the three numbers under each name")
	for p in pair:
		var id := str(p["id"])
		var fat := _shown(scene, "Fatigue", id)
		var mor := _shown(scene, "Morale", id)
		var frm := _shown(scene, "Form", id)
		_check(fat != null and fat.text == str(int(round(_workload.value(p)))),
				"Fatigue on the card is his load (%s, want %d)" % [fat.text if fat else "-", int(round(_workload.value(p)))])
		_check(mor != null and mor.text == str(_club_life.morale(p)),
				"Morale on the card is his morale (%s, want %d)" % [mor.text if mor else "-", _club_life.morale(p)])
		_check(frm != null and frm.text == str(_kept_form(id)),
				"Form on the card is his last games' rating (%s, want %d)" % [frm.text if frm else "-", _kept_form(id)])
		# The strip sits inside its tile on a 390 px phone.
		var strip: Control = scene.find_child("Condition_" + id, true, false)
		var tile: Control = strip.get_parent().get_parent() if strip != null else null
		_check(strip != null and tile is Button and (tile as Control).get_global_rect().grow(0.5).encloses(strip.get_global_rect()),
				"The numbers sit inside %s's tile" % id)
		_check(strip != null and strip.get_global_rect().end.x <= 390.0, "...and on the screen")
	_check(_shown(scene, "Fatigue", str(pair[0]["id"])).get_theme_color("font_color") == load("res://scripts/ui/UiKit.gd").BAD,
			"A load past Needs a break shows in the bad colour")
	_check(_shown(scene, "Morale", str(pair[1]["id"])).get_theme_color("font_color") == load("res://scripts/ui/UiKit.gd").GOOD,
			"Morale of 85 or more shows in the good colour")
	# A real tap on the first one's tile, then on Profile: the sheet's numbers are the same.
	var a := pair[0] as Dictionary
	var aid := str(a["id"])
	var strip_a: Control = scene.find_child("Condition_" + aid, true, false)
	var why: String = await Tap.tap(strip_a.get_parent().get_parent() as Control)
	await _settle()
	_check(why == "", "A real tap reaches his tile (%s)" % why)
	var prof: Button = current_scene.find_child("PickedProfile", true, false)
	why = (await Tap.tap(prof)) if prof != null else "missing"
	await _settle()
	_check(why == "", "A real tap on Profile opens him (%s)" % why)
	for pair_v in [["Fatigue", str(int(round(_workload.value(a))))], ["Morale", str(_club_life.morale(a))],
			["Form", str(_kept_form(aid))]]:
		var l := current_scene.find_child("Sheet%s_%s" % [pair_v[0], aid], true, false) as Label
		_check(l != null and l.is_visible_in_tree() and l.text == str(pair_v[1]),
				"His sheet's %s is %s (%s)" % [pair_v[0], pair_v[1], l.text if l else "-"])
	# The second player's sheet, opened as the screen does.
	var b := pair[1] as Dictionary
	var bid := str(b["id"])
	current_scene.call("_open_profile", bid)
	await _settle()
	for pair_v in [["Fatigue", str(int(round(_workload.value(b))))], ["Morale", str(_club_life.morale(b))],
			["Form", str(_kept_form(bid))]]:
		var l := current_scene.find_child("Sheet%s_%s" % [pair_v[0], bid], true, false) as Label
		_check(l != null and l.text == str(pair_v[1]), "%s's sheet: %s %s (%s)" % [bid, pair_v[0], pair_v[1], l.text if l else "-"])
	# A move rebuilds the cards from the same numbers: change his load and look again.
	a["workload"] = 22.0
	current_scene.call("_build")
	await _settle()
	var fat2 := _shown(current_scene, "Fatigue", aid)
	_check(fat2 != null and fat2.text == "22", "The card follows his load (%s)" % (fat2.text if fat2 else "-"))


## Their side, read-only: his load and mood are his club's business.
func _test_rival_shows_none() -> void:
	var scene: Node = current_scene
	scene.set("_view", "opp")
	scene.call("_build")
	await _settle()
	_check(scene.find_children("Condition_*", "", true, false).is_empty(), "A rival's cards show no fatigue, morale or form")
	_check(scene.find_child("ConditionKey", true, false) == null, "...and no key")
	scene.set("_view", "mine")
	scene.call("_build")
	await _settle()


func _test_pc_cards_name_them() -> void:
	root.size = Vector2i(1920, 1080)
	await _settle(8)
	var scene: Node = current_scene
	var grid: Node = scene.find_child("NotSelected", true, false)
	_check(grid != null and grid.get_child_count() > 0, "PC: the players not picked are listed")
	if grid == null or grid.get_child_count() == 0:
		return
	var card: Control = grid.get_child(0)
	var id := str(card.name).trim_prefix("Card_")
	var strip: Control = card.find_child("Condition_" + id, true, false)
	var words: Array = []
	if strip != null:
		for l in strip.find_children("*", "Label", true, false):
			words.append((l as Label).text)
	_check(words.has("Fatigue") and words.has("Morale") and words.has("Form"), "PC: a card names each number (%s)" % str(words))
	_check(strip != null and card.get_global_rect().grow(0.5).encloses(strip.get_global_rect()), "PC: the numbers sit inside the card")
	var fat := _shown(card, "Fatigue", id)
	var p: Dictionary = _gs.list_player(id)
	_check(fat != null and fat.text == str(int(round(_workload.value(p)))), "PC: the card's fatigue is his load")
