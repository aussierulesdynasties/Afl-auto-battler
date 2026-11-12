extends SceneTree
## Real renderer: godot --path . --rendering-method gl_compatibility --script tools/visual/capture_training_grid.gd
## Environment: CAP_CLUB (default FRE), CAP_W, CAP_H (default 390x844), CAP_OUT (file prefix).
## Saves <prefix>_grid.png (the Training grid, top), <prefix>_grid_scrolled.png, <prefix>_group.png
## (two players selected). Illustrative fixture only; it never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	state.autosave_enabled = false
	state.save_path = "user://capture_training.save"
	state.settings_path = "user://capture_training.cfg"
	db.reload()
	state.reset()
	var club := OS.get_environment("CAP_CLUB") if OS.get_environment("CAP_CLUB") != "" else "FRE"
	state.start_season(club, db.club_list(club))
	var w := int(OS.get_environment("CAP_W")) if OS.get_environment("CAP_W") != "" else 390
	var h := int(OS.get_environment("CAP_H")) if OS.get_environment("CAP_H") != "" else 844
	var prefix := OS.get_environment("CAP_OUT") if OS.get_environment("CAP_OUT") != "" else "training_grid"
	DisplayServer.window_set_size(Vector2i(w, h))
	root.size = Vector2i(w, h)
	var list: Array = state.my_list
	list[0]["generic_name"] = "Alexander Papaioannou-Featherstone"
	list[1]["injury_weeks"] = 3
	state.set_player_plan(str(list[2]["id"]), str(state.plans_for(list[2])[1]) if state.plans_for(list[2]).size() > 1 else "position")
	state.set_setting("seen_training_intro", true)
	router.go("training")
	# The router shows a loading screen first: wait for Training itself.
	for i in range(900):
		await process_frame
		if current_scene != null and current_scene.has_method("_open_player"):
			break
	var scene = current_scene
	if scene == null or not scene.has_method("_open_player"):
		push_error("training scene did not open")
		quit(1)
		return
	for i in range(45):
		await process_frame
	await _drawn()
	root.get_texture().get_image().save_png(prefix + "_grid.png")
	var sc: ScrollContainer = scene.get("_list_scroll")
	sc.scroll_vertical = 600
	for i in range(4):
		await process_frame
	await _drawn()
	root.get_texture().get_image().save_png(prefix + "_grid_scrolled.png")
	sc.scroll_vertical = 0
	var rucks: Array = []
	for pl in list:
		if str(pl.get("role", "")) == "RUCK":
			rucks.append(str(pl["id"]))
	scene.set("_bulk_selected", {rucks[0]: true, rucks[1]: true})
	scene.call("_build")
	for i in range(6):
		await process_frame
	await _drawn()
	root.get_texture().get_image().save_png(prefix + "_group.png")
	print("CAPTURE saved ", prefix, " at ", w, "x", h)
	quit()


## A frame that has been drawn. frame_post_draw never fires when the window is
## covered, so a short timer backs it up and the capture cannot hang.
func _drawn() -> void:
	var done := [false]
	var mark := func(): done[0] = true
	RenderingServer.frame_post_draw.connect(mark, CONNECT_ONE_SHOT)
	var t := create_timer(1.0)
	while not done[0] and t.time_left > 0.0:
		await process_frame
