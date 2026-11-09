extends SceneTree
## Draft fit (row 127), for the director's look. Needs a real renderer:
##   godot --path . --windowed --script tools/visual/capture_draft_fit.gd -- --out /tmp/df [--club MEL] [--size 390x844]
## Writes <out>_board.png (the board scrolled to the first marked prospect,
## coach on Defence and System + Father Figure), _sheet.png (a marked
## prospect's sheet) and _other.png (the board for Territory and Attack + The
## Gambler: the marks follow the archetype).

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(10)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path, " ", img.get_size())


func _board(state, club: String, held: Dictionary) -> Control:
	state.coach_arch = {"s": {held["s"]: 10.0}, "p": {held["p"]: 10.0}, "held": held,
			"tally": {"plans": {}, "calls": {}}}
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(20)
	# Scroll so the first marked row sits near the top of the pool.
	var lines := ui.find_children("Fit_*", "Label", true, false)
	if not lines.is_empty():
		var first: Control = lines[0]
		var p := first.get_parent()
		while p != null and not (p is ScrollContainer):
			p = p.get_parent()
		if p is ScrollContainer:
			var sc := p as ScrollContainer
			var y := first.get_global_rect().position.y - sc.get_global_rect().position.y + sc.scroll_vertical
			sc.scroll_vertical = maxi(0, int(y) - 150)
	await _frames(10)
	return ui


func _run() -> void:
	var out := "/tmp/df"
	var club := "MEL"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--club":
			club = str(a[i + 1])
		if str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_draft_fit.save"
	state.settings_path = "user://capture_draft_fit_settings.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(state.settings_path))
	state.show_real_names = true
	state.reset()
	state.career_seed = 2031
	state.replay_seed = 2031
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_draft_intro", true)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	var base: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, base)
	layout._update_scale()
	await _frames(10)
	print("canvas ", root.get_visible_rect().size)
	state.start_season(club, db.club_list(club))
	var clubs: Array = db.active_clubs(state.season_year).duplicate()
	var sizes := {}
	var counts := {}
	for c in clubs:
		sizes[c] = 34
		counts[c] = {"RUCK": 2, "MID": 13, "DEF": 9, "FWD": 10}
	var prospects: Array = load("res://scripts/sim/Prospects.gd").generate_class(state.season_year, 7331)
	state.draft = load("res://scripts/sim/Draft.gd").build_intake(prospects, clubs, clubs, 551, sizes, counts)
	state.draft.start_for_user(club)
	state.my_club = club
	state.draft_meeting_year = state.season_year
	var ui := await _board(state, club, {"s": "DS", "p": "FATH"})
	await _shot(out + "_board.png")
	# The sheet of a prospect with the most marks.
	var marks: Dictionary = load("res://scripts/sim/DraftFit.gd").marks(state.draft.pool, state.coach_arch["held"],
			club, state.draft.seed, state.draft.scouting_mult_for(club))
	var best := ""
	for pid in marks:
		if best == "" or (marks[pid] as Array).size() > (marks[best] as Array).size():
			best = str(pid)
	ui.call("_open_player", best)
	await _frames(10)
	await _shot(out + "_sheet.png")
	ui.call("_close_player")
	ui.queue_free()
	await _frames(4)
	ui = await _board(state, club, {"s": "TA", "p": "GAMB"})
	await _shot(out + "_other.png")
	quit(0)
