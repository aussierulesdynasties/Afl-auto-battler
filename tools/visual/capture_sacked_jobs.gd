extends SceneTree
## Review capture for row 111 (sacked is not the end), dark: the Hub's sacked
## card with three clubs offering a job (top and bottom), the retire sheet,
## the card once he has retired, the card when his career is over, and the
## board's final-warning card with the second-chance line. Needs a real
## renderer and a window (keep it off screen with an override.cfg):
##   godot --path . --script tools/visual/capture_sacked_jobs.gd
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


func _sacked(offers: bool) -> void:
	var arcs = load("res://scripts/sim/CoachArcs.gd")
	var moves = load("res://scripts/state/ClubMoves.gd")
	_state.reset()
	_state.career_seed = 4403
	_state.replay_seed = 4403
	_state.start_season("FRE", _db.club_list("FRE"))
	# The season played out to its end, where a sacking comes, so the ladder
	# and this season's line on the record are real.
	var guard := 0
	while not _state.season.is_season_over() and guard < 40:
		guard += 1
		_state.week_events = []
		_state.advance()
	_state.coach_arcs = arcs.ensure(_state.coach_arcs)
	var st: Dictionary = _state.coach_arcs
	var year := int(_state.season_year)
	# Two earlier seasons at the club, so the read-out has something to say
	# (this season's line is already on the honour roll).
	st["coach"]["start"] = year - 2
	for h in st["coach"]["clubs"]:
		h["from"] = year - 2
	_state.honour_roll.push_front({"year": year - 1, "my_club": "FRE", "my_record": "8-15-0", "premier": "BRL"})
	_state.honour_roll.push_front({"year": year - 2, "my_club": "FRE", "my_record": "13-10-0", "my_finals": "Elimination final", "premier": "GEE"})
	_state.board["sacked"] = true
	st["sack"] = {"from": "FRE", "year": year, "heir": ""}
	st["offers"] = moves._jobs_after_sack(_state, st) if offers else []
	if not offers:
		st["coach"]["reprieves"] = 0
	_state.week_events = []


func _hub():
	var hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(12)
	return hub


func _done(hub) -> void:
	hub.queue_free()
	await _frames(2)


func _name(tag: String) -> String:
	return "%s/sacked_%s_%dx%d.png" % [_dir, tag, _size.x, _size.y]


func _run() -> void:
	_dir = _env("CAP_DIR", ".")
	_size = Vector2i(int(_env("CAP_W", "390")), int(_env("CAP_H", "844")))
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_sacked_jobs.save"
	_state.settings_path = "user://capture_sacked_jobs.cfg"
	_state.set_setting("seen_training_intro", true)
	_state.set_setting("seen_weekly_loop_intro", true)
	UK.apply_appearance("dark")
	root.size = _size
	DisplayServer.window_set_size(_size)
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)

	# 1-2: sacked, three clubs offering a job; then the foot of the card.
	_sacked(true)
	var hub = await _hub()
	var card: Control = hub.find_child("SackedCard", true, false)
	if card != null:
		await _scroll_to(hub, card, 10)
	await _shot(_name("1_offers_top"))
	var retire: Control = hub.find_child("RetireCoach", true, false)
	if retire != null:
		await _scroll_to(hub, retire, int(_size.y * 0.55) if _size.y > _size.x else 150)
	await _shot(_name("2_offers_foot"))
	# 3: the retire sheet, record read out first.
	hub.call("_confirm_retire")
	await _frames(8)
	await _shot(_name("3_retire_sheet"))
	var sheet: Node = root.find_child("RetireSheet", true, false)
	if sheet != null:
		sheet.queue_free()
	await _done(hub)

	# 4: retired.
	_sacked(true)
	load("res://scripts/state/ClubMoves.gd").retire_coach(_state)
	hub = await _hub()
	card = hub.find_child("SackedCard", true, false)
	if card != null:
		await _scroll_to(hub, card, 10)
	await _shot(_name("4_retired"))
	await _done(hub)

	# 5: sacked with no second chance left: the career is over.
	_sacked(false)
	hub = await _hub()
	card = hub.find_child("SackedCard", true, false)
	if card != null:
		await _scroll_to(hub, card, 10)
	await _shot(_name("5_career_over"))
	await _done(hub)

	# 6: the board's final warning, with what a sacking would mean.
	_state.reset()
	_state.career_seed = 4403
	_state.replay_seed = 4403
	_state.start_season("FRE", _db.club_list("FRE"))
	_state.coach_arcs = load("res://scripts/sim/CoachArcs.gd").ensure(_state.coach_arcs)
	_state.board["warned"] = true
	_state.board["confidence"] = 30
	_state.week_events = []
	hub = await _hub()
	var rep: Control = hub.find_child("ReprieveLine", true, false)
	print("reprieve line: ", (rep as Label).text if rep is Label else "(none)")
	if rep != null:
		await _scroll_to(hub, rep, int(_size.y * 0.4) if _size.y > _size.x else 100)
	await _shot(_name("6_final_warning"))
	await _done(hub)
	quit()
