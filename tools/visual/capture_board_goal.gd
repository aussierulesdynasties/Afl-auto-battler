extends SceneTree
## Review capture for row 115 (the board goal said aloud), dark: the Coaching
## board with the goal and where the list ranks on paper, at 18 clubs and with
## three more clubs in the competition (21), and the pre-season briefing's
## "The board expects" lines. Needs a real renderer:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_board_goal.gd
## Environment: CAP_DIR (folder for the pngs, default "."), CAP_CLUB (default
## "GEE"), CAP_W / CAP_H (default 390 x 844). Never touches a real save.


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


func _coaching(state, dir: String, size: Vector2i, tag: String) -> void:
	var cs = load("res://scenes/CoachingScene.tscn").instantiate()
	root.add_child(cs)
	await _frames(10)
	var board: Control = cs.find_child("Board", true, false)
	if board != null:
		await _scroll_to(cs, board, 40)
	var why: Label = cs.find_child("BoardGoalWhy", true, false)
	print(tag, " goal: ", state.board_goal_text(), " | ", why.text if why != null else "(no BoardGoalWhy)")
	await _shot("%s/board_goal_%s_%dx%d.png" % [dir, tag, size.x, size.y])
	cs.queue_free()
	await _frames(2)


func _run() -> void:
	var dir := _env("CAP_DIR", ".")
	var club := _env("CAP_CLUB", "GEE")
	var size := Vector2i(int(_env("CAP_W", "390")), int(_env("CAP_H", "844")))
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_board_goal.save"
	state.settings_path = "user://capture_board_goal.cfg"
	state.reset()
	state.career_seed = 2026
	state.replay_seed = 2026
	state.set_setting("seen_training_intro", true)
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_coaching_intro", true)
	state.start_season(club, db.club_list(club))
	# CAP_RANK: coach the club whose list ranks there instead (a middle-band
	# list shows the goal that scales with the club count).
	var want_rank := int(_env("CAP_RANK", "0"))
	if want_rank > 0:
		for code in state.club_expect:
			if int(state.club_expect[code]) == want_rank:
				club = str(code)
		state.reset()
		state.career_seed = 2026
		state.replay_seed = 2026
		state.start_season(club, db.club_list(club))
	UK.apply_appearance("dark")
	root.size = size
	DisplayServer.window_set_size(size)
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	await _coaching(state, dir, size, "coaching18")
	# Mid-season: the board's "why it moved" line sits under the goal's reason
	# (the state players see all season). The line is the one a lost match
	# writes (ClubLife.match_reason), set here instead of playing rounds.
	var saved_why := str(state.board.get("why", ""))
	state.board["why"] = load("res://scripts/sim/ClubLife.gd").match_reason(
			state.board.get("goal", {}), db.club_name("CAR" if club != "CAR" else "COL"), -14, 2)
	await _coaching(state, dir, size, "coachingmid")
	state.board["why"] = saved_why
	# The pre-season briefing's board lines, from this season's goal.
	state.season_wrap = {"year": state.season_year, "ins": [], "outs": [], "staff": [], "trades": [],
			"league_coaches": [], "goal": state.board_goal_text(), "reason": state.board_goal_reason(), "seen": false}
	var hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(10)
	if hub.find_child("SeasonWrap", true, false) == null:
		hub.call("_show_season_wrap")
		await _frames(6)
	var goal: Control = hub.find_child("WrapGoal", true, false)
	if goal != null:
		await _scroll_to(hub, goal, int(size.y * 0.4))
	await _shot("%s/board_goal_wrap_%dx%d.png" % [dir, size.x, size.y])
	hub.queue_free()
	await _frames(2)
	# Three more clubs in the competition: copies of the three weakest lists,
	# so this list ranks among 21.
	var ranked: Array = []
	for code in state.season.ladder:
		ranked.append(str(code))
	ranked.sort_custom(func(a, b): return int(state.club_expect[a]) > int(state.club_expect[b]))
	for i in range(3):
		var code := "ZZ%d" % i
		state.season.ladder[code] = (state.season.ladder[ranked[i]] as Dictionary).duplicate(true)
		state.season.lists[code] = state.season.lists[ranked[i]]
	state._open_board_season()
	await _coaching(state, dir, size, "coaching21")
	quit()
