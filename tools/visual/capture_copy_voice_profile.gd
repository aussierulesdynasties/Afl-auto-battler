extends SceneTree
## Copy voice pass 9 (the player profile, director 2026-11-10: option B) captures, phone portrait
## 390x844, a fresh Fremantle career that never touches a real save. One launch writes every state
## whose copy the pass changed, so the same script gives the before (on the base) and the after:
##   godot --headless --path . --script tools/visual/capture_copy_voice_profile.gd -- --out <prefix> [--only a,b]
## Writes <prefix>_<state>.png for: top, injured, why, development, beyond, nickname, rival.

const CLUB := "FRE"
var _out := "copy_voice_profile"
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

	# Our best player's profile, top: who he is, his state, his numbers.
	if _want("top"):
		_fresh(intro_keys)
		var p := _best()
		_season(p)
		await _sheet(p)
		await _shot("top")

	# An injured player: how long he is out and with what.
	if _want("injured"):
		_fresh(intro_keys)
		var p2 := _best()
		p2["injury_weeks"] = 3
		p2["injury_kind"] = "hamstring"
		await _sheet(p2)
		await _shot("injured")

	# Why: the rule behind his opinion of the coach.
	if _want("why"):
		_fresh(intro_keys)
		var p3 := _best()
		var sheet: Control = await _sheet(p3)
		var why: Button = sheet.find_child("TrustWhy", true, false)
		if why != null:
			why.emit_signal("pressed")
		await _scroll_to(sheet, "ProfileTrust")
		await _shot("why")

	# OVR, POT, how far he has to go, and his development focus; then his season.
	if _want("development"):
		_fresh(intro_keys)
		var p4 := _young()
		_season(p4)
		var sheet4: Control = await _sheet(p4)
		await _scroll_to(sheet4, "ProfileOVR")
		await _shot("development")

	# A player rated above his potential.
	if _want("beyond"):
		_fresh(intro_keys)
		var p5 := _best()
		p5["potential"] = int(p5["overall"]) - 2
		var sheet5: Control = await _sheet(p5)
		await _scroll_to(sheet5, "ProfileOVR")
		await _shot("beyond")

	# The nickname field open at the foot of the sheet.
	if _want("nickname"):
		_fresh(intro_keys)
		var p6: Dictionary = {}
		for q in _state.my_list:
			if p6.is_empty() and load("res://scripts/core/FictionalIdentity.gd").nickname(q) == "":
				p6 = q
		var sheet6: Control = await _sheet(p6)
		var edit: Button = sheet6.find_child("NicknameEdit", true, false)
		if edit != null:
			edit.emit_signal("pressed")
		await _scroll_to(sheet6, "NicknameField")
		await _shot("nickname")

	# A rival's profile: no mood or load, POT as a range.
	if _want("rival"):
		_fresh(intro_keys)
		var other: Dictionary = _db.club_list("MEL")[0]
		var sheet7: Control = await _sheet(other)
		await _scroll_to(sheet7, "ProfileOVR")
		await _shot("rival")

	quit()


func _want(state: String) -> bool:
	return _only.is_empty() or _only.has(state)


func _best() -> Dictionary:
	var best: Dictionary = _state.my_list[0]
	for q in _state.my_list:
		if int(q.get("overall", 0)) > int(best.get("overall", 0)):
			best = q
	return best


## The youngest player with room to grow.
func _young() -> Dictionary:
	var pick: Dictionary = _state.my_list[0]
	for q in _state.my_list:
		if int(q.get("potential", 0)) - int(q.get("overall", 0)) >= 3 and float(q.get("age", 99)) < float(pick.get("age", 99)):
			pick = q
	return pick


## A few games on his record this season, so the season lines show.
func _season(p: Dictionary) -> void:
	_state.season_tally[str(p["id"])] = {"games": 3, "goals": 4, "distance_run": 39600.0}


func _fresh(intro_keys: Array) -> void:
	_state.reset()
	_state.career_seed = 4402
	_state.replay_seed = 4402
	_state.start_season(CLUB, _db.club_list(CLUB))
	_state.tutorials = false
	_state.week_events = []
	for key in intro_keys:
		_state.set_setting("seen_%s_intro" % key, true)


## Opens My list through the router, then the player's profile over it.
func _sheet(p: Dictionary) -> Control:
	_router.stack = []
	_router.go("main")
	var guard := 0
	while not _on("Main") and guard < 600:
		await process_frame
		guard += 1
	_router.go("list")
	guard = 0
	while not _on("List") and guard < 600:
		await process_frame
		guard += 1
	await _frames(30)
	var sheet: Control = load("res://scripts/ui/PlayerSheet.gd").open(current_scene, p)
	await _frames(20)
	return sheet


## Scrolls the sheet so the named part sits near the top.
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
