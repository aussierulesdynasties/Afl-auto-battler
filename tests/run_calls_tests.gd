extends SceneTree
## godot --headless --path . --script tests/run_calls_tests.gd
## The match calls (director, 2026-10-14; 2026-11-03 cuts): old calls with
## main ruck, play-through or rotation load cleanly and are ignored, the
## Defensive set-up reads its shape, the coach's tagger stays on the ground while his tag is on,
## and anyone who can play midfield can be tagged. Split from the matchday suite
## to keep it under its time limit.

const Tap := preload("res://tests/tap.gd")
const SUITE_SEED := 2027

var _state: Node
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_state.autosave_enabled = false
	_state.save_path = "user://test_career.save"
	_state.settings_path = "user://test_settings.cfg"
	_state.show_real_names = false
	_state.replay_seed = SUITE_SEED
	await _t("_test_old_calls_load_and_rotations_are_automatic")
	await _t("_test_defence_setup_keys")
	await _t("_test_tag_is_permanent")
	_state.autosave_enabled = true
	print(Ran.line("Match calls", self))
	for f in _failures:
		print("ERROR: " + f)
	quit(0 if _failures.is_empty() else 1)


func _settle() -> void:
	for i in range(6):
		await process_frame


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
## Old calls (director, 2026-11-03 cuts): a saved set of calls that still
## carries main_ruck, focus_* or rotation loads cleanly; Start sends none of
## them to the engine, and the rotations are the automatic ones.
func _test_old_calls_load_and_rotations_are_automatic() -> void:
	var db = root.get_node("GameDB")
	root.size = Vector2i(420, 860)
	_state.reset()
	_state.start_season("MEL", db.club_list("MEL"))
	_check(_state.prepare_interactive_match(), "A match is prepared for the old-calls check")
	var sim = _state.pending_sim
	var me := int(sim.moment_side)
	var anyone := str(sim.squads[me].ground[0]["id"])
	var m: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(m)
	await _settle()
	m.set("_last_tactics", {"main_ruck": anyone, "focus_mid": anyone, "focus_fwd": anyone, "focus_id": anyone, "rotation": "stars"})
	var box: Node = m.find_child("CoachBox", true, false)
	for gone in ["MainRuckPicker", "RotationPicker", "FocusPicker_focus_mid", "InterceptorPicker", "SpareMinderPicker"]:
		_check(m.find_child(gone, true, false) == null, "No %s at the break any more" % gone)
	_check(m.find_child("DefenceSetupPicker", true, false) != null, "One Defensive set-up call in its place")
	var gw: String = await Tap.tap(box.find_child("StartQuarter", true, false))
	await _settle()
	var t: Dictionary = sim.tactics[me]
	_check(gw == "" and not t.has("main_ruck") and not t.has("rotation") and not t.has("focus_mid"),
			"Start sends no main ruck, rotation or play-through call (%s)" % str(t.keys()))
	_check(str(sim.rotation_policy[me]) == sim.auto_rotation(me, _state.fitness_plan(str(_state.my_club))),
			"The rotations are the automatic ones (%s)" % str(sim.rotation_policy[me]))
	m.queue_free()
	await _settle()


## The Defensive set-up answers read the shape, and the four shapes map onto
## the loose defender and the forward on their loose man.
func _test_defence_setup_keys() -> void:
	var MN = load("res://scripts/ui/match/MatchNotes.gd")
	_check(MN.defence_key(false, false) == "man" and MN.defence_key(true, false) == "loose"
			and MN.defence_key(false, true) == "cover" and MN.defence_key(true, true) == "both",
			"Old loose and minder picks map onto one Defensive set-up")
	for o in MN.DEFENCE_SETUPS:
		_check(MN.defence_answer(str(o[0])) == str(o[1]), "The break row reads %s" % str(o[1]))
	_check(MN.defence_setup_line("man", "", "", "") != "", "Man on man says what it means")


## True when any button or label under a node says the text.
func _any_text(node: Node, text: String) -> bool:
	for n in node.find_children("*", "Control", true, false):
		if (n is Button or n is Label) and str(n.text).contains(text):
			return true
	return false


## The tag is the coach's call all match (director, 2026-10-14): a named
## tagger is not rotated off while his tag is on, and a mid/forward can be tagged.
func _test_tag_is_permanent() -> void:
	var db = root.get_node("GameDB")
	var Ms = load("res://scripts/sim/MatchSim.gd")
	_state.reset()
	_state.start_season("MEL", db.club_list("MEL"))
	_check(_state.prepare_interactive_match(), "A match is prepared for the tagger check")
	var sim = _state.pending_sim
	var me := int(sim.moment_side)
	var mids: Array = (sim.squads[me].ground as Array).filter(func(p): return Ms.midfielder_on_ground(p))
	var theirs := ""
	for p in sim.squads[1 - me].ground:
		if sim.tag_target_ok(1 - me, str(p["id"])):
			theirs = str(p["id"])
			break
	_check(mids.size() >= 2 and theirs != "", "(setup) midfielders to tag with and a target")
	if mids.size() < 2 or theirs == "":
		return
	var tagger_id := str(mids[0]["id"])
	var t: Dictionary = (sim.tactics[me] as Dictionary).duplicate()
	t["tag_id"] = theirs
	t["tagger_id"] = tagger_id
	sim.set_tactics(me, t)
	sim.energy[tagger_id] = 5.0
	for i in 40:
		sim._auto_rotate(me)
	var still := false
	for p in sim.squads[me].ground:
		if str(p["id"]) == tagger_id:
			still = true
	_check(still, "The named tagger stays on the ground with the tag on, however tired")
	var t2: Dictionary = (sim.tactics[me] as Dictionary).duplicate()
	t2["tag_id"] = ""
	sim.set_tactics(me, t2)
	for i in 3:
		sim._auto_rotate(me)
	var off := true
	for p in sim.squads[me].ground:
		if str(p["id"]) == tagger_id:
			off = false
	_check(off, "With no tag, the tired man is rotated off as before")
	# A mid/forward is a valid tag target; a pure forward or ruck is not.
	var mf := {}
	var plain := {}
	# Loaded, not named: the autoloads are not there when this script compiles.
	var Rt = load("res://scripts/sim/Ratings.gd")
	for p in sim.squads[1 - me].ground:
		var pos: Array = Rt.positions(p)
		if pos.has("MID") and str(p["role"]) != "MID":
			mf = p
		elif not pos.has("MID"):
			plain = p
	if not mf.is_empty():
		_check(sim.tag_target_ok(1 - me, str(mf["id"])), "A player who can play midfield is a tag target in a forward slot")
	if not plain.is_empty():
		_check(not sim.tag_target_ok(1 - me, str(plain["id"])), "A player with no midfield position is not a tag target")
	var fake := {"role": "FWD", "own_role": "FWD", "role2": "MID", "id": "x", "attr": {}}
	_check(Ms.can_be_tagged(fake) and not Ms.can_be_tagged({"role": "MID", "own_role": "RUCK", "role2": ""}),
			"Mid/forward can be tagged; a ruck in a midfield slot cannot")


