extends SceneTree
## Copy voice pass 6 (training, director 2026-11-10: option B) captures, phone portrait 390x844,
## a fresh Fremantle career that never touches a real save. One launch writes every state whose
## copy the pass changed, so the same script gives the before (on the base) and the after:
##   godot --path . --script tools/visual/capture_copy_voice_training.gd -- --out <prefix> [--only a,b]
## Writes <prefix>_<state>.png for: intro, list_no_change, group, player, player_changed,
## player_lifted, stat_focus, stat_locked, learning, reserves, two_traits, and (row 135's second
## pass, 2026-11-15) learn_full, carry_on, potential.

const CLUB := "FRE"
var _out := "copy_voice_training"
var _only: PackedStringArray = []
var _state: Node
var _db: Node
var _router: Node


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			_out = str(a[i + 1])
		elif str(a[i]) == "--only":
			_only = str(a[i + 1]).split(",")
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_router = root.get_node("Router")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_copy_voice.save"
	_state.settings_path = "user://capture_copy_voice.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(390, 844)
	DisplayServer.window_set_size(Vector2i(390, 844))
	var intro_keys: Array = load("res://scripts/ui/FirstVisitIntro.gd").TEXT.keys()

	# The first visit to Training: how it works.
	if _want("intro"):
		_fresh(intro_keys)
		_state.tutorials = true
		_state.set_setting("seen_training_intro", false)
		await _open()
		await _shot("intro")

	# A game played and nobody's rating moved.
	if _want("list_no_change"):
		_fresh(intro_keys)
		_state.last_training_report = {"count": 1, "label": "Round 1"}
		await _open()
		await _shot("list_no_change")

	# Three players held, then one focus given to all of them.
	if _want("group"):
		_fresh(intro_keys)
		var ui: Node = await _open()
		for i in range(3):
			ui.call("_toggle_bulk", str(_state.my_list[i]["id"]))
		ui.call("_apply_bulk_plan", "position")
		await _frames(12)
		await _shot("group")

	# A player's page, then the note after his focus changes.
	if _want("player") or _want("player_changed") or _want("player_lifted") or _want("stat_focus"):
		_fresh(intro_keys)
		var ui2: Node = await _open()
		var pid := str(_best()["id"])
		ui2.call("_open_player", pid)
		await _frames(12)
		await _shot("player")
		ui2.set("_notice", ui2.call("_spend_notice", {}, 70, 70))
		ui2.call("_build")
		await _scroll_to(ui2, "FocusName")
		await _shot("player_changed")
		ui2.set("_notice", ui2.call("_spend_notice", {"marking": 1}, 70, 71))
		ui2.call("_build")
		await _scroll_to(ui2, "FocusName")
		await _shot("player_lifted")
		ui2.set("_notice", "")
		ui2.call("_build")
		await _scroll_to(ui2, "StatFocus")
		await _shot("stat_focus")

	# One stat locked in for the season.
	if _want("stat_locked"):
		_fresh(intro_keys)
		var p: Dictionary = _best()
		var options: Array = _state.focus_options(p)
		print("locked: ", _state.set_stat_focus(str(p["id"]), str(options[0])))
		var ui3: Node = await _open()
		ui3.call("_open_player", str(p["id"]))
		await _scroll_to(ui3, "StatFocus")
		await _shot("stat_locked")

	# A player learning a second position: the standard he is chasing, and the stat focus on hold.
	if _want("learning"):
		_fresh(intro_keys)
		var who := ""
		for q in _state.my_list:
			for key in _state.plans_for(q):
				if str(key).begins_with(_state.LEARN_PREFIX) and who == "":
					who = str(q["id"])
					_state.set_player_plan(who, str(key))
		print("learning: ", who)
		var ui4: Node = await _open()
		ui4.call("_open_player", who)
		await _scroll_to(ui4, "FocusName")
		await _shot("learning")

	# A player who spent the last game in the reserves.
	if _want("reserves"):
		_fresh(intro_keys)
		var r: Dictionary = _state.my_list[_state.my_list.size() - 1]
		_state.last_training_report = {"count": 1, "label": "Round 1",
				"rows": [{"id": str(r["id"]), "reserves": true, "xp": 22}]}
		var ui5: Node = await _open()
		ui5.call("_open_player", str(r["id"]))
		await _scroll_to(ui5, "ReservesLine")
		await _shot("reserves")

	# A player with two traits already, and a focus that grows him toward a third.
	if _want("two_traits"):
		_fresh(intro_keys)
		var found := ""
		var stat := ""
		for q in _state.my_list:
			for key in _state.focus_options(q):
				var ft: Dictionary = _state.focus_trait(q, str(key))
				if found == "" and not ft.is_empty() and bool(ft.get("crowded", false)):
					found = str(q["id"])
					stat = str(key)
		print("two traits: ", found, " ", stat)
		if found != "":
			var ui6: Node = await _open()
			ui6.call("_open_player", found)
			ui6.set("_focus_choice", stat)
			ui6.call("_build")
			await _scroll_to(ui6, "StatFocusTrait")
			await _shot("two_traits")

	# Two players already learning a position: a third who could learn one is told why he waits.
	if _want("learn_full"):
		_fresh(intro_keys)
		var started := 0
		var waiting := ""
		var open: Array = []
		for q in _state.my_list:
			if not _state.open_jobs(q).is_empty():
				open.append(str(q["id"]))
		for qid in open:
			var keys: Array = []
			for key in _state.plans_for(_state.list_player(qid)):
				if str(key).begins_with(_state.LEARN_PREFIX):
					keys.append(str(key))
			if started < 2 and not keys.is_empty():
				_state.set_player_plan(qid, str(keys[0]))
				started += 1
			elif waiting == "" and _state.project_job(_state.list_player(qid)) == "":
				waiting = qid
		print("learn_full: ", started, " ", waiting)
		var ui7: Node = await _open()
		ui7.call("_open_player", waiting)
		await _scroll_to(ui7, "LearnPosition")
		await _shot("learn_full")

	# Last season's stat focus carrying on into a new season, not yet locked in.
	if _want("carry_on"):
		_fresh(intro_keys)
		var c: Dictionary = _best()
		c["train_focus"] = str(_state.focus_options(c)[0])
		c["train_focus_year"] = int(_state.season_year) - 1
		var ui8: Node = await _open()
		ui8.call("_open_player", str(c["id"]))
		await _scroll_to(ui8, "StatFocus")
		await _shot("carry_on")

	# A player past his potential, with the stats open: the potential note.
	if _want("potential"):
		_fresh(intro_keys)
		var t: Dictionary = _best()
		t["potential"] = int(t["overall"]) - 3
		var ui9: Node = await _open()
		ui9.call("_open_player", str(t["id"]))
		ui9.set("_advanced", true)
		ui9.call("_build")
		await _frames(8)
		var pot: Control = null
		for n in ui9.find_children("*", "Label", true, false):
			if (n as Label).text.begins_with("Potential "):
				pot = n
		if pot != null:
			pot.name = "CapturePotential"
		await _scroll_to(ui9, "CapturePotential")
		await _shot("potential")

	quit()


func _want(state: String) -> bool:
	return _only.is_empty() or _only.has(state)


func _best() -> Dictionary:
	var best: Dictionary = _state.my_list[0]
	for q in _state.my_list:
		if int(q.get("overall", 0)) > int(best.get("overall", 0)):
			best = q
	return best


func _fresh(intro_keys: Array) -> void:
	_state.reset()
	_state.career_seed = 4402
	_state.replay_seed = 4402
	_state.start_season(CLUB, _db.club_list(CLUB))
	_state.tutorials = false
	_state.week_events = []
	for key in intro_keys:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.set_setting("seen_training_intro", true)


## Opens Training fresh through the router and waits for it to settle.
func _open() -> Node:
	_router.stack = []
	_router.go("main")
	var guard := 0
	while not _on("Main") and guard < 600:
		await process_frame
		guard += 1
	_router.go("training")
	guard = 0
	while not _on("Training") and guard < 600:
		await process_frame
		guard += 1
	await _frames(40)
	return current_scene


## Scrolls the page so the named part sits near the top.
func _scroll_to(ui: Node, node_name: String) -> void:
	await _frames(8)
	var target: Control = ui.find_child(node_name, true, false)
	if target == null:
		print("missing ", node_name)
		return
	var sc: Node = target.get_parent()
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		(sc as ScrollContainer).scroll_vertical = int(target.global_position.y - (sc as Control).global_position.y
				+ (sc as ScrollContainer).scroll_vertical - 8.0)
	await _frames(8)


func _on(scene: String) -> bool:
	return current_scene != null and current_scene.scene_file_path.contains(scene)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(name: String) -> void:
	await _frames(3)
	var img := root.get_viewport().get_texture().get_image()
	img.save_png("%s_%s.png" % [_out, name])
	print("wrote %s_%s.png" % [_out, name])
