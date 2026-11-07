extends SceneTree
## The full-screen press conference (row 105, item 7), for QC at phone size:
##   godot --path . --resolution 390x844 --windowed --script tools/visual/capture_press_scene.gd -- --out DIR
## Writes DIR/press_muckraker_gate.png (a heavy loss, a fourth answer naming a
## player), DIR/press_stats_gate.png (a close game, the record read on the gate)
## and DIR/press_result.png (the Muckraker answered). Vignettes on, so the room
## shows; each gate is saved once the question is up. Seeded; never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


## Waits for the question to show (the room hands over to it), up to ~6 s.
func _question_up() -> bool:
	for i in range(360):
		await process_frame
		var q: Control = root.find_child("MediaQuestion", true, false)
		if q != null and q.is_visible_in_tree():
			await _frames(20)
			return true
	return false


func _shot(path: String) -> void:
	root.get_viewport().get_texture().get_image().save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "caps"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		if str(a[i]).begins_with("--out="):
			out = str(a[i]).substr(6)
		elif str(a[i]) == "--out" and i + 1 < a.size():
			out = str(a[i + 1])
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	var MC = load("res://scripts/sim/MediaConference.gd")
	var club := "COL"
	state.autosave_enabled = false
	state.save_path = "user://capture_press_scene.save"
	state.settings_path = "user://capture_press_scene.cfg"
	seed(2031)
	state.reset()
	state.career_seed = 2031
	state.replay_seed = 2031
	state.set_setting("seen_weekly_loop_intro", true)
	state.start_season(club, db.club_list(club))
	state.set_vignettes_on(true)
	DisplayServer.window_set_size(Vector2i(390, 844))
	root.size = Vector2i(390, 844)
	await _frames(4)
	# The Muckraker after a heavy loss; the fourth answer names a player.
	var named: Dictionary = state.my_list[3]
	state.media_conference = MC.pick({"club": club, "opponent_name": "Carlton", "round": 8,
			"year": int(state.season_year), "result": {"home": club, "away": "CAR", "score": [55, 101]},
			"named": {"heavy_loss": {"id": str(named["id"]), "name": str(db.player_display_name(named))}}}, {})
	state.media_conference["opp"] = "Carlton"
	router.stack = []
	router.go("press")
	if not await _question_up():
		push_error("capture_press_scene: the Muckraker's question did not show")
		quit(1)
		return
	_shot(out.path_join("press_muckraker_gate.png"))
	# The answer that names him, scrolled into view, then answered for the result screen.
	var ans: Button = root.find_child("MediaAnswer_3", true, false)
	if ans == null:
		push_error("capture_press_scene: no fourth answer")
		quit(1)
		return
	var sc: Node = ans.get_parent()
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		(sc as ScrollContainer).scroll_vertical = 100000
	await _frames(20)
	_shot(out.path_join("press_muckraker_named.png"))
	ans.emit_signal("pressed")
	await _frames(30)
	if root.find_child("MediaOutcomeLine", true, false) == null:
		push_error("capture_press_scene: the result did not show")
		quit(1)
		return
	_shot(out.path_join("press_result.png"))
	# The Stats Geek after a close game, eight games in so the record reads.
	var row: Dictionary = state.season.ladder[club]
	row["w"] = 5
	row["l"] = 3
	row["pct"] = 104.2
	state.media_conference = MC.pick({"club": club, "opponent_name": "Carlton", "round": 9,
			"year": int(state.season_year), "result": {"home": club, "away": "CAR", "score": [80, 83],
			"team": [{"inside50": 54, "clearances": 36}, {"inside50": 41, "clearances": 38}]}}, {})
	state.media_conference["opp"] = "Carlton"
	router.stack = []
	router.go("hub")
	await _frames(10)
	router.stack = []
	router.go("press")
	if not await _question_up():
		push_error("capture_press_scene: the Stats Geek's question did not show")
		quit(1)
		return
	_shot(out.path_join("press_stats_gate.png"))
	state.media_conference = {}
	quit(0)
