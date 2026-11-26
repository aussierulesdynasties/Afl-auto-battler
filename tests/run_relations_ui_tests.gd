extends SceneTree
## godot --headless --path . --script tests/run_relations_ui_tests.gd
## The relationship overhaul's Phase 1 screens (RelationsView): the profile's
## temperament, opinion breakdown (fading, scars, memory) and bonds, and Team
## selection's read-only preview of what leaving a man out costs. Real taps at
## phone size. A part whose system has not landed yet (Opinion, Temperament,
## Bonds, Promises) prints one SKIP line and checks what still shows.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 20261126

var _gs: Node
var _db: Node
var _router: Node
var _sheet_s: Script
var _view: Script
var _trust: Script
var _checks := 0
var _failures: Array[String] = []


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
	_sheet_s = load("res://scripts/ui/PlayerSheet.gd")
	_view = load("res://scripts/ui/RelationsView.gd")
	_trust = load("res://scripts/sim/Trust.gd")
	_gs.autosave_enabled = false
	_gs.event_sheets = false
	_gs.save_path = "user://test_relations_ui.save"
	_gs.settings_path = "user://test_relations_ui.cfg"
	_gs.replay_seed = SUITE_SEED
	root.size = Vector2i(390, 844)
	await _t("_test_profile_relations")
	await _t("_test_rival_profile")
	await _t("_test_drop_preview")
	_gs.replay_seed = 0
	print(Ran.line("RelationsUi", self))
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


func _has_script(name: String) -> bool:
	return ResourceLoader.exists("res://scripts/sim/%s.gd" % name)


func _close_sheets() -> void:
	for c in current_scene.get_children():
		if c.name.begins_with("PlayerProfile"):
			c.free()


## Your player's profile: temperament named, the opinion line, and a real tap
## on Why opens what fades (with weeks left), the scars apart from it, and
## what he remembers. A real tap on a mate's name opens the mate.
func _test_profile_relations() -> void:
	_fresh("COL")
	_router.go("list")
	await _settle(10)
	var p: Dictionary = _gs.my_list[0]
	var id := str(p["id"])
	var key: String = _trust.player_key(id)
	var opinion_ready := _has_script("Opinion")
	if opinion_ready:
		var op: Script = load("res://scripts/sim/Opinion.gd")
		op.call("add", _gs.relations, key, "dropped", _gs.season_year, "Round 3", str(p["club"]))
		op.call("add", _gs.relations, key, "dropped_final", _gs.season_year, "Qualifying final", str(p["club"]))
	else:
		print("SKIP: Opinion.gd not in this tree, so no fading marks or scars to show")
	_trust.change(_gs.relations, key, 10, "You gave him his chance", _gs.season_year, "Round 1")
	var rel_before: Dictionary = _gs.relations.duplicate(true)
	var sheet: Control = _sheet_s.open(current_scene, p)
	await _settle()
	var block: Control = sheet.find_child("ProfileRelations", true, false)
	_check(block != null, "The profile has its relationships block")
	var words: Label = sheet.find_child("TrustWords", true, false)
	var shown := int(_view.opinion(_gs.relations, id)["shown"])
	_check(words != null and words.text.replace(String.chr(0xA0), " ").ends_with(": %d out of 100." % shown),
			"The opinion line is his whole opinion, live marks included (%s, %d)" % [words.text if words else "-", shown])
	var why: Button = sheet.find_child("TrustWhy", true, false)
	var list: Control = sheet.find_child("TrustReasons", true, false)
	var tap: String = await Tap.tap(why) if why != null else "missing"
	await _settle()
	_check(tap == "" and list != null and list.visible and why.size.y >= 44, "A real tap on Why opens the breakdown (%s)" % tap)
	var memory: Control = list.find_child("OpinionMemory", true, false) if list else null
	_check(memory != null and (memory.get_child(1) as Label).text.begins_with("Round 1, "),
			"What he remembers is listed, with when")
	if opinion_ready:
		var fading: Control = list.find_child("OpinionMarks", true, false)
		_check(fading != null and _text(fading).contains("Gone ") and _text(fading).contains(": -"),
				"What fades says its size and the weeks it has left (%s)" % _text(fading))
		var scars: Control = list.find_child("OpinionScars", true, false)
		var marks: Array = _view.opinion(_gs.relations, id)["marks"]
		var has_scar := marks.any(func(m): return int(m["weeks"]) < 0)
		_check((scars != null) == has_scar, "Scars get their own list exactly when he carries one")
		if scars != null:
			_check(_text(scars).contains("It stays."), "A scar says it stays")
		var all := _text(list).to_lower()
		_check(not all.contains("modifier"), "No engine words in the breakdown")
	if _has_script("Temperament"):
		var tw: Label = sheet.find_child("TemperamentWords", true, false)
		_check(tw != null and tw.text.length() > 3, "His temperament is named (%s)" % (tw.text if tw else "-"))
	else:
		print("SKIP: Temperament.gd not in this tree")
	if _gs.has_method("bond_ties"):
		var ties: Array = _view.bonds(_gs, id)
		var bonds: Control = sheet.find_child("ProfileBonds", true, false)
		_check((bonds != null) == (not ties.is_empty()), "His bonds are listed exactly when he has some")
		if not ties.is_empty():
			var name_l: Label = bonds.get_child(0).find_child("BondName", true, false)
			var bt: String = await Tap.tap(name_l)
			await _settle()
			var top: Label = null
			for c in current_scene.get_children():
				if c.name.begins_with("PlayerProfile") and c != sheet:
					top = c.find_child("ProfileName", true, false)
			_check(bt == "" and top != null and top.text == str(ties[0]["name"]),
					"A real tap on a mate's name opens his profile (%s, %s)" % [bt, top.text if top else "-"])
	else:
		print("SKIP: bonds not in this tree")
	_check(_gs.relations == rel_before, "Looking at the profile changes nothing")
	_close_sheets()


## Another club's man: his temperament and bonds are public, his opinion of
## you is not on the sheet.
func _test_rival_profile() -> void:
	var rival: Dictionary = {}
	for code in _gs.season.lists:
		if str(code) != _gs.my_club:
			rival = _gs.season.lists[code][0]
			break
	var sheet: Control = _sheet_s.open(current_scene, rival)
	await _settle()
	_check(sheet.find_child("TrustWords", true, false) == null, "A rival's sheet has no opinion of you")
	if _has_script("Temperament"):
		_check(sheet.find_child("TemperamentWords", true, false) != null, "A rival's temperament is shown")
	_close_sheets()


## Team selection: a real tap on a picked man's tile, then Profile, shows what
## leaving him out would cost, and it is a preview: nothing changes.
func _test_drop_preview() -> void:
	_fresh("COL")
	_router.go("selection")
	await _settle(10)
	var scene: Node = current_scene
	var side: Dictionary = _gs.current_side()
	var pid := ""
	for line in ["MID", "DEF", "FWD"]:
		for x in side.get(line, []):
			if pid == "" and int(_gs.list_player(str(x)).get("injury_weeks", 0)) <= 0:
				pid = str(x)
	var p: Dictionary = _gs.list_player(pid)
	var rel_before: Dictionary = _gs.relations.duplicate(true)
	var stand_before = _gs.get("coach_standing")
	stand_before = (stand_before as Dictionary).duplicate(true) if stand_before is Dictionary else null
	var strip: Control = scene.find_child("Condition_" + pid, true, false)
	var tile: Control = strip.get_parent().get_parent() as Control if strip != null else null
	var tap: String = await Tap.tap(tile) if tile != null else "no tile"
	await _settle()
	var prof: Button = scene.find_child("PickedProfile", true, false)
	var tap2: String = (await Tap.tap(prof)) if prof != null else "no Profile"
	await _settle()
	_check(tap == "" and tap2 == "", "Real taps on his tile and Profile open him (%s, %s)" % [tap, tap2])
	var prev: Control = scene.find_child("DropPreview", true, false)
	_check(prev != null and prev.is_visible_in_tree(), "His profile shows what leaving him out costs")
	if prev == null:
		return
	var state: Control = prev.get_parent().find_child("ProfileReadiness", false, false)
	if state == null:
		state = prev.get_parent().find_child("ProfileState", false, false)
	_check(state != null and prev.get_index() == state.get_index() + 1, "The cost sits right under how he is now")
	var cost: Dictionary = _view.drop_preview(_gs, p, _gs.relations, false)
	if _has_script("Opinion"):
		var ol: Label = prev.find_child("DropOpinion", true, false)
		_check(int(cost["opinion"]) < 0 and ol != null and ol.text.ends_with("%+d." % int(cost["opinion"])),
				"Being left out costs his opinion of you (%s)" % (ol.text if ol else "-"))
	if _gs.has_method("bond_fallout"):
		_check(prev.find_children("DropFallout_*", "", true, false).size() == (cost["fallout"] as Array).size(),
				"Each mate or rival who takes it has a line")
	var all := _text(prev)
	_check(not all.to_lower().contains("modifier") and not all.to_lower().contains("best"), "Facts, no verdicts (%s)" % all)
	_check(_gs.relations == rel_before, "The preview changes no opinion")
	var stand_now = _gs.get("coach_standing")
	_check(stand_before == null or stand_now == stand_before, "The preview changes no standing")
	# A man not in the side has no drop to preview.
	var out_id := ""
	for q in _gs.my_list:
		if not _gs.in_current_side(q):
			out_id = str(q["id"])
			break
	_check(load("res://scripts/ui/SelectionScene.gd").drop_preview(_gs.list_player(out_id)) == null,
			"A man not picked has no drop preview")
	_close_sheets()


func _text(n: Node) -> String:
	if n == null:
		return ""
	var out := ""
	if n is Label:
		out += (n as Label).text + "\n"
	for c in n.get_children():
		out += _text(c)
	return out
