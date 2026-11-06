extends SceneTree
## Real renderer, windowed off screen (override.cfg), through C:/kt/gpu_slot.sh:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_stat_focus.gd
## Environment: CAP_W, CAP_H (default 390x844), CAP_OUT (file prefix, default
## "stat_focus"). Saves <prefix>_open.png (no focus yet), <prefix>_picked.png (a
## stat tapped, Lock in showing) and <prefix>_locked.png: the stat focus panel
## on a player's Training page (row 97). Illustrative
## fixture only; it never touches a real save.

const SEED := 2027


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	# Draw every frame: an unchanged screen would otherwise never post a draw.
	OS.low_processor_usage_mode = false
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture_stat_focus.save"
	state.settings_path = "user://capture_stat_focus.cfg"
	state.show_real_names = false
	state.replay_seed = SEED
	db.reload()
	state.reset()
	state.start_season("COL", db.club_list("COL"))
	var w := int(OS.get_environment("CAP_W")) if OS.get_environment("CAP_W") != "" else 390
	var h := int(OS.get_environment("CAP_H")) if OS.get_environment("CAP_H") != "" else 844
	var prefix := OS.get_environment("CAP_OUT") if OS.get_environment("CAP_OUT") != "" else "stat_focus"
	DisplayServer.window_set_size(Vector2i(w, h))
	root.size = Vector2i(w, h)
	var p: Dictionary = {}
	for q in state.my_list:
		if state.project_job(q) == "" and str(q.get("role", "")) == "MID" and int(q.get("age", 30)) <= 22:
			p = q
			break
	if p.is_empty():
		p = state.my_list[0]
	state.set_setting("seen_training_intro", true)
	router.go("training")
	await _frames(8)
	var scene = current_scene
	scene.call("_open_player", str(p["id"]))
	await _frames(6)
	await _shot(scene, prefix + "_open.png")
	var opts: Array = state.focus_options(p)
	scene.set("_focus_choice", str(opts[min(2, opts.size() - 1)]))
	scene.call("_build")
	await _frames(6)
	await _shot(scene, prefix + "_picked.png")
	var lock: Button = scene.find_child("StatFocusLock", true, false)
	if lock != null:
		lock.emit_signal("pressed")
	await _frames(6)
	await _shot(scene, prefix + "_locked.png")
	print("CAPTURE saved ", prefix, " at ", w, "x", h)
	quit()


## Scroll the player's page so the stat focus panel sits on screen, then save.
func _shot(scene: Node, path: String) -> void:
	var panel: Control = scene.find_child("StatFocus", true, false)
	var sc: ScrollContainer = scene.get("_detail_scroll")
	if panel != null and sc != null:
		# Its head at the top, then Lock in (when showing) brought into view.
		sc.scroll_vertical = maxi(0, int(panel.global_position.y - sc.global_position.y) + sc.scroll_vertical - 8)
		await _frames(2)
		var lock: Control = scene.find_child("StatFocusLock", true, false)
		if lock != null:
			sc.ensure_control_visible(lock)
	await _frames(3)
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(path)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame
