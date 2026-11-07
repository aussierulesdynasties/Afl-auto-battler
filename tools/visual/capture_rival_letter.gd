extends SceneTree
## Review capture for row 112 (other clubs come calling), dark: the Hub with a
## rival board's letter open (the facts, the risk and both answers), then the hub
## after he takes the job and after he turns it down. Needs a real renderer
## and a window (keep it off screen with an override.cfg):
##   godot --path . --script tools/visual/capture_rival_letter.gd
## Environment: CAP_DIR (default "."), CAP_W / CAP_H (default 390 x 844).
## Never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _frames(n := 8) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames()
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)


func _scroll_to(scene: Node, target: Control, above := 70) -> void:
	var boxes := scene.find_children("*", "ScrollContainer", true, false)
	for b in boxes:
		var box := b as ScrollContainer
		if box.is_visible_in_tree() and box.is_ancestor_of(target):
			box.scroll_vertical = maxi(0, int(target.global_position.y - box.global_position.y) - above + box.scroll_vertical)
	await _frames()


func _env(key: String, fallback: String) -> String:
	return OS.get_environment(key) if OS.get_environment(key) != "" else fallback


var _state
var _db
var _dir := "."
var _size := Vector2i(390, 844)


## A season played out at Fremantle, finals reached and the board's goal met,
## and the rival board's letter written at the close.
func _season_with_letter() -> void:
	var arcs = load("res://scripts/sim/CoachArcs.gd")
	var moves = load("res://scripts/state/ClubMoves.gd")
	_state.reset()
	_state.career_seed = 4411
	_state.replay_seed = 4411
	_state.start_season("FRE", _db.club_list("FRE"))
	var guard := 0
	while not _state.season.is_season_over() and guard < 40:
		guard += 1
		_state.week_events = []
		_state.advance()
	_state.coach_arcs = arcs.ensure(_state.coach_arcs)
	var st: Dictionary = _state.coach_arcs
	var year := int(_state.season_year)
	_state.board["sacked"] = false
	st["move"] = {}
	st["letter"] = {}
	st["active"].erase("poached")
	st["done"].erase("poached")
	var hist: Array = _state.board.get("history", [])
	if hist.is_empty() or int(hist[-1].get("year", 0)) != year:
		hist.append({"year": year})
		_state.board["history"] = hist
	hist[-1]["met"] = true
	if _state.honour_roll.is_empty() or int(_state.honour_roll[-1].get("year", 0)) != year:
		_state.honour_roll.append({"year": year, "my_club": "FRE"})
	_state.honour_roll[-1]["my_club"] = "FRE"
	_state.honour_roll[-1]["my_finals"] = "Qualifying final"
	moves._rival_letter(_state, st)
	# The carnival sheet is its own capture: seen, so it does not cover the letter.
	_state.midseason["carnival_seen"] = true
	_state.week_events = []
	print("letter: ", moves.letter(_state))


func _hub():
	var hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(12)
	return hub


func _done(hub) -> void:
	hub.queue_free()
	await _frames(2)


func _name(tag: String) -> String:
	return "%s/letter_%s_%dx%d.png" % [_dir, tag, _size.x, _size.y]


func _at(hub, node: String, above: int, tag: String) -> void:
	var target: Control = hub.find_child(node, true, false)
	if target != null:
		await _scroll_to(hub, target, above)
	else:
		print("missing ", node)
	await _shot(_name(tag))


func _run() -> void:
	_dir = _env("CAP_DIR", ".")
	_size = Vector2i(int(_env("CAP_W", "390")), int(_env("CAP_H", "844")))
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	var moves = load("res://scripts/state/ClubMoves.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_rival_letter.save"
	_state.settings_path = "user://capture_rival_letter.cfg"
	_state.set_setting("seen_training_intro", true)
	_state.set_setting("seen_weekly_loop_intro", true)
	UK.apply_appearance("dark")
	root.size = _size
	DisplayServer.window_set_size(_size)
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)

	# 1: the letter, its risk and the two answers.
	_season_with_letter()
	var hub = await _hub()
	await _at(hub, "RivalLetter", 10, "1_open")
	await _done(hub)
	# 3: taken.
	_season_with_letter()
	moves.accept_letter(_state)
	hub = await _hub()
	await _at(hub, "RivalLetter", int(_size.y * 0.35), "3_taken")
	await _done(hub)
	# 4: turned down.
	_season_with_letter()
	moves.decline_letter(_state)
	hub = await _hub()
	await _at(hub, "RivalLetter", int(_size.y * 0.35), "4_declined")
	await _done(hub)
	quit()
