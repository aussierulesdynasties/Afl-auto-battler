extends SceneTree
## The Combine screen (row 83), for the director's look. Needs a real renderer:
##   godot --path . --windowed --script tools/visual/capture_combine.gd -- --out /tmp/cb [--club COL] [--size 390x844]
## Writes <out>_room.png, _intro.png, _day.png, _day_end.png, _test.png,
## _test_end.png, _filtered.png, _sheet.png, _postseason.png.

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


func _run() -> void:
	var out := "/tmp/cb"
	var club := "COL"
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
	state.save_path = "user://capture_combine.save"
	state.settings_path = "user://capture_combine_settings.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(state.settings_path))
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
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(20)
	await _shot(out + "_room.png")
	ui.call("_open_combine")
	await _frames(10)
	await _shot(out + "_intro.png")
	ui.call("handle_back")
	await _frames(10)
	await _shot(out + "_day.png")
	var sc: ScrollContainer = ui.find_child("CombineScroll", true, false)
	sc.scroll_vertical = 100000
	await _shot(out + "_day_end.png")
	var tab: Button = ui.find_child("CombineTab_sprint", true, false)
	tab.pressed.emit()
	await _frames(10)
	await _shot(out + "_test.png")
	ui.get("_combine_place")["shown"] = 999
	ui.get("_combine").call("_fill_rows", "sprint")
	await _frames(6)
	sc = ui.find_child("CombineScroll", true, false)
	sc.scroll_vertical = 100000
	await _shot(out + "_test_end.png")
	sc.scroll_vertical = 0
	(ui.find_child("CombineRole_RUCK", true, false) as Button).pressed.emit()
	await _frames(10)
	await _shot(out + "_filtered.png")
	var rows: Node = ui.find_child("CombineRows", true, false)
	(rows.get_child(0) as Button).pressed.emit()
	await _frames(10)
	await _shot(out + "_sheet.png")
	# The first postseason's intro on the hub, in the one run (row 83's look).
	ui.queue_free()
	await _frames(4)
	state.draft = null
	var sea = state.season
	# A season really played, so the hub behind the sheet has a ladder and a premier.
	while sea.round_index < sea.fixture.size():
		sea.play_round()
	sea.start_finals()
	while not bool(sea.finals["done"]):
		sea.play_finals_week()
	state.week_events = []
	state.tutorials = true
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(60)
	await _shot(out + "_postseason.png")
	quit(0)
