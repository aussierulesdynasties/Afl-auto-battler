extends SceneTree
## Copy voice pass 5 (the team builder and coaching, director 2026-11-10: option B) captures, phone
## portrait 390x844, a fresh Fremantle career that never touches a real save. One launch writes
## every state whose copy the pass changed, so the same script gives the before (on main) and the
## after:
##   godot --path . --script tools/visual/capture_copy_voice_team.gd -- --out <prefix> [--only a,b]
## Writes <prefix>_<state>.png for: team_intro, team, team_hint, team_menu, team_dual, team_one_ruck,
## team_saved, team_undo, team_rest, team_no_best23, team_opp, team_back, coaching_intro,
## coaching, coaching_trait, coaching_cap, sim_orders.

const CLUB := "FRE"
var _out := "copy_voice_team"
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

	# The first visit to Team: the intro sheet.
	if _want("team_intro"):
		_fresh(intro_keys)
		_state.tutorials = true
		_state.set_setting("seen_selection_intro", false)
		await _open("selection", "Selection")
		await _shot("team_intro")

	# The side as Auto-pick picks it: the hint under the interchange.
	if _want("team"):
		_fresh(intro_keys)
		await _open("selection", "Selection")
		await _shot("team")
		await _raise()
		await _shot("team_hint")
	if _want("team_menu"):
		_fresh(intro_keys)
		var ui: Node = await _open("selection", "Selection")
		(ui.find_child("AutoPick", true, false) as MenuButton).show_popup()
		await _frames(12)
		await _shot("team_menu")
		(ui.find_child("AutoPick", true, false) as MenuButton).get_popup().hide()
	# Dual ruck on, then off: the two notices.
	if _want("team_dual") or _want("team_one_ruck"):
		_fresh(intro_keys)
		var ui2: Node = await _open("selection", "Selection")
		(ui2.find_child("AutoPick", true, false) as MenuButton).get_popup().id_pressed.emit(100)
		await _raise()
		await _shot("team_dual")
		(ui2.find_child("AutoPick", true, false) as MenuButton).get_popup().id_pressed.emit(100)
		await _raise()
		await _shot("team_one_ruck")
	if _want("team_no_best23"):
		_fresh(intro_keys)
		var ui3: Node = await _open("selection", "Selection")
		ui3.call("_apply_strategy", "mine")
		await _raise()
		await _shot("team_no_best23")
	if _want("team_saved"):
		_fresh(intro_keys)
		var ui4: Node = await _open("selection", "Selection")
		(ui4.find_child("SaveBest23", true, false) as BaseButton).emit_signal("pressed")
		await _raise()
		await _shot("team_saved")
	# An Auto-pick, its note, then Undo.
	if _want("team_rest") or _want("team_undo"):
		_fresh(intro_keys)
		var ui5: Node = await _open("selection", "Selection")
		ui5.call("_apply_strategy", "rest")
		await _raise()
		await _shot("team_rest")
		var undo: BaseButton = ui5.find_child("UndoPick", true, false)
		if undo != null:
			undo.emit_signal("pressed")
		await _raise()
		await _shot("team_undo")
	if _want("team_youth"):
		_fresh(intro_keys)
		# Nobody young near a senior spot: every player 21 or under is well short.
		for p in _state.my_list:
			if _state.is_young(p):
				p["overall"] = 40
		var ui6: Node = await _open("selection", "Selection")
		ui6.call("_apply_strategy", "youth")
		await _raise()
		await _shot("team_youth")
	# Their side on the oval.
	if _want("team_opp"):
		_fresh(intro_keys)
		var ui7: Node = await _open("selection", "Selection")
		ui7.set("_view", "opp")
		ui7.call("_build")
		await _frames(12)
		await _shot("team_opp")
	# A young player's sheet: the Back for three games action.
	if _want("team_back"):
		_fresh(intro_keys)
		var kid := {}
		for p in _state.my_list:
			if _state.can_back(p) and (kid.is_empty() or int(p["overall"]) > int(kid["overall"])):
				kid = p
		var ui8: Node = await _open("selection", "Selection")
		if not kid.is_empty():
			ui8.call("_open_profile", str(kid["id"]))
			await _frames(16)
			var act: Control = root.find_child("BackRun", true, false)
			var sc: Node = act.get_parent() if act != null else null
			while sc != null and not (sc is ScrollContainer):
				sc = sc.get_parent()
			if sc != null:
				(sc as ScrollContainer).ensure_control_visible(act)
				await _frames(6)
		await _shot("team_back")

	# The first visit to Coaching: the intro sheet.
	if _want("coaching_intro"):
		_fresh(intro_keys)
		_state.tutorials = true
		_state.set_setting("seen_coaching_intro", false)
		await _open("coaching", "Coaching")
		await _shot("coaching_intro")
	if _want("coaching"):
		_fresh(intro_keys)
		await _open("coaching", "Coaching")
		await _shot("coaching")
	for part in [["coaching_plan", "ListProfile"], ["coaching_trait", "PlanTraitSection"], ["coaching_cap", "ListAndCap"]]:
		if _want(str(part[0])):
			_fresh(intro_keys)
			var ui9: Node = await _open("coaching", "Coaching")
			await _scroll_to(ui9, str(part[1]))
			await _shot(str(part[0]))
	# Ten games in with nothing standing out: the quiet lines under How we win.
	if _want("coaching_quiet"):
		_fresh(intro_keys)
		var ui10: Node = await _open("coaching", "Coaching")
		var hwp: Control = ui10.find_child("HowWePlay", true, false)
		var script: Script = ui10.get_script()
		var at := hwp.get_child_count() - 1
		for part in ["win", "beaten"]:
			var l := Label.new()
			l.text = str(script.call("_quiet_line", part, 12))
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			hwp.add_child(l)
		await _scroll_to(ui10, "ListProfile")
		await _frames(4)
		print("quiet lines added after child %d" % at)
		await _shot("coaching_quiet")

	# When I sim the week: who gets picked.
	if _want("sim_orders"):
		_fresh(intro_keys)
		var ui11: Node = await _open("coaching", "Coaching")
		var sheet: Control = load("res://scripts/ui/SimOrdersSheet.gd").open(ui11)
		await _frames(12)
		var row: Control = sheet.find_child("SimOrderWrap_youth_kids", true, false)
		var sc2: Node = row.get_parent() if row != null else null
		while sc2 != null and not (sc2 is ScrollContainer):
			sc2 = sc2.get_parent()
		if sc2 != null:
			(sc2 as ScrollContainer).ensure_control_visible(row)
			await _frames(6)
		await _shot("sim_orders")

	quit()


func _want(state: String) -> bool:
	return _only.is_empty() or _only.has(state)


func _fresh(intro_keys: Array) -> void:
	_state.reset()
	_state.career_seed = 4402
	_state.replay_seed = 4402
	_state.start_season(CLUB, _db.club_list(CLUB))
	_state.tutorials = false
	_state.week_events = []
	for key in intro_keys:
		_state.set_setting("seen_%s_intro" % key, true)


## Opens a screen fresh through the router and waits for it to settle.
func _open(route: String, scene: String) -> Node:
	_router.stack = []
	_router.go("main")
	var guard := 0
	while not _on("Main") and guard < 600:
		await process_frame
		guard += 1
	_router.go(route)
	guard = 0
	while not _on(scene) and guard < 600:
		await process_frame
		guard += 1
	await _frames(40)
	return current_scene


## Scrolls the page so the named section sits near the top.
func _scroll_to(ui: Node, node_name: String) -> void:
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


## The phone's list pulled up over the oval, so the line under the interchange is in the frame.
func _raise() -> void:
	await _frames(12)
	var builder: Node = current_scene.find_child("TeamBuilder", true, false)
	if builder != null:
		builder.call("set_raised", true, false)
	await _frames(12)


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
