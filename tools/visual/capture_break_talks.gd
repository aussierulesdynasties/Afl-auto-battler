extends SceneTree
## Review capture for the quarter-break talks (BreakTalks, director 2026-11-21):
## at quarter time the break's rows with "Sit down with a player", its sheet
## with a player picked (the gate), then the dice landed; at half time the
## speech's sheet before and after the roll. Needs a real renderer:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_break_talks.gd
## Environment: CAP_DIR (default "."), CAP_CLUB (default "COL"), CAP_W / CAP_H
## (default 390 x 844). Never touches a real save.

const Tap := preload("res://tests/tap.gd")


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


func _env(key: String, fallback: String) -> String:
	return OS.get_environment(key) if OS.get_environment(key) != "" else fallback


## The sheet's scroll brought down to `target`, so the gate and the dice show.
func _scroll_to(target: Control) -> void:
	var p := target.get_parent()
	while p != null:
		if p is ScrollContainer:
			(p as ScrollContainer).ensure_control_visible(target)
		p = p.get_parent()
	await _frames()


func _run() -> void:
	var dir := _env("CAP_DIR", ".")
	var club := _env("CAP_CLUB", "COL")
	var size := Vector2i(int(_env("CAP_W", "390")), int(_env("CAP_H", "844")))
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.event_sheets = false
	state.save_path = "user://capture_break_talks.save"
	state.settings_path = "user://capture_break_talks.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.reset()
	state.replay_seed = 2027
	state.start_season(club, db.club_list(club))
	state.set_setting("seen_weekly_loop_intro", true)
	root.size = size
	root.get_node("Router").stack = ["hub"]
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames()
	state.set_vignettes_on(false)
	hub.call("_on_play_match")
	await _frames()
	var wait := 0
	while (current_scene == null or current_scene.name != "MatchScene") and wait < 600:
		wait += 1
		await process_frame
	var m: Node = current_scene
	print("scene: ", m.name if m != null else "none")
	var guard := 0
	while m != null and not bool(m.get("_finished")) and guard < 20000:
		guard += 1
		var box = m.get("_coach_overlay")
		var mo = m.get("_moment_overlay")
		if box != null and is_instance_valid(box):
			var sim = state.pending_sim
			var q: int = sim.current_quarter
			if q == 2 or q == 3:
				var tag := "qt" if q == 2 else "ht"
				await _shot("%s/talks_%s_rows.png" % [dir, tag])
				var grid: Node = m.find_child("SitPickerGrid", true, false)
				var first: Button = null
				for b in grid.get_children():
					if b is Button and not str(b.name).ends_with("Other") and not str(b.name).ends_with("Grid_"):
						first = b
						break
				await Tap.tap(first)
				await _frames()
				var go: Control = m.find_child("SitDown", true, false)
				await _scroll_to(go)
				await _shot("%s/talks_%s_sit_gate.png" % [dir, tag])
				await Tap.tap(go)
				await _frames(80)
				await _scroll_to(m.find_child("SitResult", true, false))
				await _shot("%s/talks_%s_sit_rolled.png" % [dir, tag])
				var done: Control = m.find_child("CallDone", true, false)
				await Tap.tap(done)
				await _frames()
				if q == 3:
					var sp: Control = m.find_child("GiveSpeech", true, false)
					await Tap.tap(m.find_child("CallRow_speech", true, false))
					await _frames()
					await _scroll_to(sp)
					await _shot("%s/talks_ht_speech_gate.png" % dir)
					await Tap.tap(sp)
					await _frames(80)
					await _scroll_to(m.find_child("SpeechResult", true, false))
					await _shot("%s/talks_ht_speech_rolled.png" % dir)
					m.call("_close_break_sheets")
					await _frames()
					await _shot("%s/talks_ht_rows_after.png" % dir)
					break
			await Tap.tap(m.find_child("StartQuarter", true, false))
			await _frames()
		elif mo != null and is_instance_valid(mo) and not state.pending_sim.pending_moment.is_empty():
			m.call("_on_moment_choice", int(state.pending_sim.pending_moment.get("default", 0)))
			await process_frame
		elif int(m.get("_breaks_played")) < 3 and not bool(m.get("_skipping")):
			m.call("_on_skip_to_break")
			await _frames()
		else:
			await process_frame
	quit()
