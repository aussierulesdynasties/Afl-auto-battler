extends SceneTree
## godot --headless --path . --script tests/run_scouting_list_tests.gd
## The scouting list (row 130): add and remove a prospect, the cap, a listed
## prospect's read narrowing faster than one off the list on a pinned seed,
## rival clubs keeping lists of their own, nothing true about the prospect
## changed, and the screen reached from My list and worked with real taps.
const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")

var _state: Node
var SL
var DS
var _router: Node
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	SL = load("res://scripts/state/ScoutingList.gd")
	DS = load("res://scripts/sim/DraftScouting.gd")
	_router = root.get_node("Router")
	_state.autosave_enabled = false
	_state.save_path = "user://test_scouting_list.save"
	_state.settings_path = "user://test_scouting_list_settings.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(_state.settings_path))
	# Return visits: the first-visit intros (FirstVisitIntro.gd) have their own suite,
	# and My list's intro would take the tap on the way in.
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.show_real_names = false
	_state.tutorials = false
	_state.replay_seed = 1301
	_state.reset()
	_state.start_season("FRE", root.get_node("GameDB").club_list("FRE"))
	root.size = Vector2i(390, 844)
	await _t("_test_add_remove_and_cap")
	await _t("_test_listed_read_narrows_faster")
	await _t("_test_save_round_trip")
	await _t("_test_screen_real_taps")
	print(Ran.line("ScoutingList", self))
	quit(0 if _failures.is_empty() else 1)


func _class() -> Array:
	return SL.pool(_state)


func _test_add_remove_and_cap() -> void:
	_state.scouting_list = []
	var pool := _class()
	_check(pool.size() > SL.LIMIT, "A draft class to scout (%d)" % pool.size())
	if pool.size() <= SL.LIMIT:
		return
	var id := str(pool[0]["id"])
	_check(SL.add(_state, id), "A prospect goes on the list")
	_check(SL.has(_state, id), "He is on it")
	_check(not SL.add(_state, id), "Not twice")
	var e: Dictionary = _state.scouting_list[0]
	_check((e["first"]["potential"] as Array).size() == 2, "His read is noted when he goes on")
	_check(not SL.add(_state, "nobody_by_this_id"), "Nobody outside the class")
	for i in range(1, SL.LIMIT):
		SL.add(_state, str(pool[i]["id"]))
	_check(SL.full(_state), "Full at %d" % SL.LIMIT)
	_check(not SL.add(_state, str(pool[SL.LIMIT]["id"])), "No room past the limit")
	_check(SL.remove(_state, id), "Taken off")
	_check(not SL.has(_state, id) and not SL.full(_state), "Off, and room again")
	_check(not SL.remove(_state, id), "Nothing to take off twice")
	_state.scouting_list = []


## Two prospects with the same pinned seed and recruiting: one listed, one not.
## After a run of weeks the listed one's read is tighter than it was, and
## tighter than the one off the list, whose read has not moved. The truth
## underneath stays the same, and rivals keep lists of their own.
func _test_listed_read_narrows_faster() -> void:
	_state.scouting_list = []
	var pool := _class()
	if pool.size() < 2:
		_check(false, "A class of two or more")
		return
	var on: Dictionary = pool[0]
	var off: Dictionary = pool[1]
	for p in [on, off]:
		p.erase("watch")
		p.erase("seen")
	var club: String = _state.my_club
	var truth := [int(on["overall"]), int(on["potential"]), (on.get("attr", {}) as Dictionary).duplicate()]
	var before: Dictionary = _state.prospect_reads([on, off])
	SL.add(_state, str(on["id"]))
	for w in range(17):
		SL.week(_state)
	var after: Dictionary = _state.prospect_reads([on, off])
	var width := func(r: Dictionary, k: String) -> int: return int(r[k][1]) - int(r[k][0])
	var on_b: Dictionary = before[str(on["id"])]
	var on_a: Dictionary = after[str(on["id"])]
	var off_b: Dictionary = before[str(off["id"])]
	var off_a: Dictionary = after[str(off["id"])]
	_check(int(on["watch"][club]) == 17, "Seventeen weeks watched")
	_check(not (off.get("watch", {}) as Dictionary).has(club), "Nobody off the list is watched")
	_check(is_equal_approx(DS.focus_mult(on, club), DS.FOCUS_FLOOR),
			"The read is at its tightest after seventeen weeks")
	_check(DS.focus_mult(on, club) < DS.focus_mult(off, club), "Listed reads tighter than unlisted")
	_check(width.call(on_a, "potential") < width.call(on_b, "potential"),
			"His POT range narrowed: %s -> %s" % [on_b["potential"], on_a["potential"]])
	_check(width.call(on_a, "overall") <= width.call(on_b, "overall"), "His OVR range never widens")
	_check(width.call(on_a, "potential") + width.call(on_a, "overall") < width.call(off_a, "potential") + width.call(off_a, "overall")
			or width.call(on_b, "potential") + width.call(on_b, "overall") > width.call(off_b, "potential") + width.call(off_b, "overall"),
			"Narrowed more than the player off the list")
	_check(off_a["overall"] == off_b["overall"] and off_a["potential"] == off_b["potential"],
			"The read off the list has not moved")
	_check(int(on["overall"]) == truth[0] and int(on["potential"]) == truth[1] and on.get("attr", {}) == truth[2],
			"Nothing true about him changed")
	var moved: String = SL.change_text(_state.scouting_list[0], on_a)
	_check(moved.begins_with("Listed before Round 1: ") and moved.contains(DS.range_text(on_b["potential"])),
			"The row says how the read moved: %s" % moved)
	var rivals := 0
	for p in pool:
		for c in (p.get("watch", {}) as Dictionary):
			if str(c) != club:
				rivals += 1
				break
	_check(rivals >= SL.LIMIT, "Rival scouts keep lists too (%d prospects watched)" % rivals)
	_state.scouting_list = []


func _test_save_round_trip() -> void:
	_state.scouting_list = []
	var id := str(_class()[2]["id"])
	SL.add(_state, id)
	_check(_state.save_career(), "The career saves")
	_state.scouting_list = []
	_check(_state.load_career(), "The career loads")
	_check(SL.has(_state, id), "The list survives a save")
	_state.scouting_list = []


func _test_screen_real_taps() -> void:
	_state.scouting_list = []
	var ls: Control = load("res://scenes/ListScene.tscn").instantiate()
	root.add_child(ls)
	await _settle()
	var open := ls.find_child("ScoutingOpen", true, false) as Button
	_check(open != null and open.size.y >= 44, "My list has a thumb-sized way to the scouting list")
	if open == null:
		return
	_check(open.tooltip_text.begins_with("0 of %d" % SL.LIMIT), "It says how many are on it: %s" % open.tooltip_text)
	var missed: String = await Tap.tap(open)
	_check(missed == "", "Scouting list takes a finger: %s" % missed)
	await _settle()
	_check(_router.current() == "scouting", "The tap opens the scouting list (%s)" % _router.current())
	if is_instance_valid(ls):
		ls.queue_free()
	if current_scene != null:
		current_scene.visible = false
	var sc: Control = load("res://scenes/ScoutingScene.tscn").instantiate()
	root.add_child(sc)
	await _settle()
	_check(sc.find_child("ScoutListEmpty", true, false) != null, "An empty list says so")
	var id := str(_class()[0]["id"])
	var add := sc.find_child("ClassAdd_" + id, true, false) as Button
	_check(add != null and add.size.y >= 44, "Each prospect in the class has a thumb-sized Add")
	if add == null:
		return
	missed = await Tap.tap(add)
	_check(missed == "", "Add takes a finger: %s" % missed)
	await _settle()
	_check(SL.has(_state, id), "A real tap puts him on the list")
	_check(sc.find_child("ScoutRow_" + id, true, false) != null, "He shows on your list")
	_check(sc.find_child("ClassRow_" + id, true, false) == null, "And no longer in the class below")
	var change := sc.find_child("ScoutChange_" + id, true, false) as Label
	_check(change != null and change.text.contains("Listed before Round 1"), "His row says when he was listed")
	var rem := sc.find_child("ScoutRemove_" + id, true, false) as Button
	_check(rem != null, "A listed prospect has Remove")
	if rem == null:
		return
	missed = await Tap.tap(rem)
	_check(missed == "", "Remove takes a finger: %s" % missed)
	await _settle()
	_check(not SL.has(_state, id), "A real tap takes him off")
	_check(sc.find_child("ClassRow_" + id, true, false) != null, "He is back in the class")
	_check(_no_bad_words(sc), "No best, target or should on the screen")


## The no-recommendation rule: the screen never says who to take.
func _no_bad_words(n: Node) -> bool:
	if n is Label or n is Button:
		var t := str(n.text).to_lower()
		for w in [" best", "target", "should", "recommend"]:
			if t.contains(w):
				push_error("Recommendation wording: %s" % n.text)
				return false
	for c in n.get_children():
		if not _no_bad_words(c):
			return false
	return true


func _settle() -> void:
	for i in range(8):
		await process_frame


func _check(ok: bool, what: String) -> void:
	_checks += 1
	if not ok:
		_failures.append(what)
		push_error(what)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
