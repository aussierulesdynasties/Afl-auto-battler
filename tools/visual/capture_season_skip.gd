extends SceneTree
## Review capture for the season skip, dark (director, 2026-11-07; 2026-11-12:
## the skips are long presses of the week's button at the bottom right, not
## lines on the hub). The hub in the home and away, the hold cue mid-press, the
## survey and sheet a hold opens there; then the same in the finals. The press is
## a real touch at the button's place on screen. Needs a real renderer:
##   godot --windowed --path . --script tools/visual/capture_season_skip.gd
## Environment: CAP_DIR (default "."), CAP_CLUB (default "FRE"), CAP_W / CAP_H
## (default 390 x 844). Never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _frames(n := 8) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String, settle := 8) -> void:
	await _frames(settle)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("CAPTURE ", path)


func _env(key: String, fallback: String) -> String:
	return OS.get_environment(key) if OS.get_environment(key) != "" else fallback


func _touch(at: Vector2, down: bool) -> void:
	var t := InputEventScreenTouch.new()
	t.index = 0
	t.position = at
	t.pressed = down
	Input.parse_input_event(t)
	Input.flush_buffered_events()


func _held_button(hub: Node) -> Button:
	for n in hub.find_children("*", "Button", true, false):
		if (n as Button).has_meta("bulk_skip") and (n as Button).is_visible_in_tree():
			return n as Button
	return null


func _hub(state: Node) -> Node:
	state.week_events = []
	state.media_conference = {}
	var hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(12)
	load("res://scripts/ui/TrainingReportSheet.gd").close_top(hub)
	await _frames(4)
	return hub


## On a wide screen (PC): the hub and the cue mid-press on the bottom-right week button.
func _wide(state: Node, dir: String, phone: Vector2i) -> void:
	var size := Vector2i(1280, 720)
	root.size = size
	DisplayServer.window_set_size(size)
	await _frames(4)
	var hub = await _hub(state)
	var b := _held_button(hub)
	if b == null:
		push_error("wide: no button holds the skip")
	else:
		print("wide: %s holds %s at %s" % [b.name, str(b.get_meta("bulk_skip")), str(b.get_global_rect())])
		var win := b.get_window()
		var units := win.get_visible_rect().size
		var at: Vector2 = (b.get_screen_transform() * (b.size * 0.5)) * (Vector2(win.size) / units)
		_touch(at, true)
		await create_timer(0.3).timeout
		await _shot("%s/wide_hold_cue_%dx%d.png" % [dir, size.x, size.y], 2)
		_touch(at, false)
		await _frames(6)
		hub.call("_close_skip_confirm")
	hub.queue_free()
	await _frames(2)
	root.size = phone
	DisplayServer.window_set_size(phone)
	await _frames(4)


## The hub, the cue mid-press, then the survey's first question and the sheet
## the hold opens. `tag` names the season's phase.
func _phase(hub: Node, tag: String, dir: String, size: Vector2i) -> void:
	await _shot("%s/%s_hub_%dx%d.png" % [dir, tag, size.x, size.y])
	var b := _held_button(hub)
	if b == null:
		push_error("%s: no button holds the skip" % tag)
		return
	print("%s: %s holds %s at %s" % [tag, b.name, str(b.get_meta("bulk_skip")), str(b.get_global_rect())])
	# A finger lands in window pixels: the UI may be drawn scaled (ScreenLayout).
	var win := b.get_window()
	var units := win.get_visible_rect().size
	var at: Vector2 = (b.get_screen_transform() * (b.size * 0.5)) * (Vector2(win.size) / units)
	_touch(at, true)
	await create_timer(0.24).timeout
	await _shot("%s/%s_hold_cue_%dx%d.png" % [dir, tag, size.x, size.y], 2)
	print("%s: cue %.2f, words '%s'" % [tag, float(b.get_node("HoldCue").get("progress")), b.text])
	await create_timer(0.5).timeout
	_touch(at, false)
	await _frames(10)
	if hub.find_child("SkipChoice", true, false) != null:
		# In the home and away the hold asks how far: the choice, then the
		# home and away's own survey as a finger on its answer opens it.
		await _shot("%s/%s_opens_choice_%dx%d.png" % [dir, tag, size.x, size.y])
		hub.call("_open_skip_confirm", "home_away")
		await _frames(10)
	await _shot("%s/%s_opens_q1_%dx%d.png" % [dir, tag, size.x, size.y])
	var n := _question_count(hub)
	hub.call("_skip_show", n)
	await _frames(10)
	await _shot("%s/%s_opens_confirm_%dx%d.png" % [dir, tag, size.x, size.y])
	hub.call("_close_skip_confirm")
	await _frames(4)


func _question_count(hub: Node) -> int:
	return (root.get_node("GameState").call("skip_questions", str(hub.get("_skip_to"))) as Array).size()


func _run() -> void:
	var dir := _env("CAP_DIR", ".")
	var club := _env("CAP_CLUB", "FRE")
	var size := Vector2i(int(_env("CAP_W", "390")), int(_env("CAP_H", "844")))
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_season_skip.save"
	state.settings_path = "user://capture_season_skip.cfg"
	state.reset()
	state.career_seed = 2026
	state.replay_seed = 2026
	state.set_setting("seen_training_intro", true)
	state.set_setting("seen_weekly_loop_intro", true)
	state.start_season(club, db.club_list(club))
	UK.apply_appearance("dark")
	root.size = size
	DisplayServer.window_set_size(size)
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	# A match week in the home and away (round 10).
	for i in range(9):
		state.advance()
		state._settle_week_event()
	var hub = await _hub(state)
	await _phase(hub, "homeaway", dir, size)
	hub.queue_free()
	await _frames(2)
	await _wide(state, dir, size)
	# The finals: the home and away played out, the first week of finals next.
	print("skip home and away: ", state.skip_season({}, "home_away"))
	state._settle_week_event()
	hub = await _hub(state)
	var card: Button = hub.find_child("CarnivalDone", true, false)
	if card != null:
		card.pressed.emit()
		await _frames(12)
	# The finals' first training report opens over the hub: closed, as a coach would.
	load("res://scripts/ui/TrainingReportSheet.gd").close_top(hub)
	await _frames(6)
	await _phase(hub, "finals", dir, size)
	quit()
