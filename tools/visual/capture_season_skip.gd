extends SceneTree
## Review capture for Skip to next season (director, 2026-11-07), dark: the
## quiet button under the week on the hub, the sheet that says what is decided
## for you, and the season wrap after the skip (the season you skipped, then
## your draft picks and who left). Needs a real renderer:
##   godot --windowed --path . --script tools/visual/capture_season_skip.gd
## Environment: CAP_DIR (default "."), CAP_CLUB (default "FRE"), CAP_W / CAP_H
## (default 390 x 844). Never touches a real save.


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
	print("CAPTURE ", path)


func _scroll_to(scene: Node, target: Control, above := 70) -> void:
	for b in scene.find_children("*", "ScrollContainer", true, false):
		var box := b as ScrollContainer
		if box.is_visible_in_tree() and box.is_ancestor_of(target):
			box.scroll_vertical = maxi(0, int(target.global_position.y - box.global_position.y) - above + box.scroll_vertical)
	await _frames()


func _env(key: String, fallback: String) -> String:
	return OS.get_environment(key) if OS.get_environment(key) != "" else fallback


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
	for i in range(9):
		state.advance()
		state._settle_week_event()
	state.week_events = []
	var hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(12)
	var b: Control = hub.find_child("SkipSeason", true, false)
	if b == null:
		push_error("no SkipSeason")
	else:
		await _scroll_to(hub, b, int(size.y * 0.6))
	await _shot("%s/skip_hub_%dx%d.png" % [dir, size.x, size.y])
	hub.call("_open_skip_confirm")
	await _frames(10)
	await _shot("%s/skip_confirm_%dx%d.png" % [dir, size.x, size.y])
	hub.call("_close_skip_confirm")
	var res: Dictionary = state.skip_season()
	print("skip: ", res, " | facts: ", state.season_wrap.get("skipped", {}))
	hub.queue_free()
	await _frames(2)
	hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(12)
	if hub.find_child("SeasonWrap", true, false) == null:
		hub.call("_show_season_wrap")
		await _frames(8)
	await _shot("%s/skip_wrap_%dx%d.png" % [dir, size.x, size.y])
	var fin: Control = hub.find_child("WrapSkipped_bf", true, false)
	if fin != null:
		await _scroll_to(hub, fin, 120)
		await _shot("%s/skip_wrap_lists_%dx%d.png" % [dir, size.x, size.y])
	quit()
