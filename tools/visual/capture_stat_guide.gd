extends SceneTree
## The stat guide's topic grid and one topic page, opened from Training with
## real taps. Needs a real renderer:
##   godot --path . --script tools/visual/capture_stat_guide.gd -- --out /tmp/sg [--club FRE] [--size 1280x720]
## Writes <out>_grid.png and <out>_page.png (the Scoring page).

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
	if W >= 760 and img.get_width() != W:
		img.resize(W, H, Image.INTERPOLATE_LANCZOS)
	img.save_png(path)
	print("wrote ", path, " ", img.get_size())


func _run() -> void:
	var out := "/tmp/tr"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--club":
			club = str(a[i + 1])
		if str(a[i]) == "--art" and str(a[i + 1]) == "off":
			# Loaded here, not named: a branch without the script still captures.
			var art = load("res://scripts/ui/UiArt.gd")
			if art != null:
				art.set("dir", "res://assets/ui/none")
		if str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_sg.save"
	state.settings_path = "user://capture_sg_settings.cfg"
	state.show_real_names = true
	state.reset()
	state.career_seed = 2031
	state.replay_seed = 2031
	state.set_setting("seen_weekly_loop_intro", true)
	# The canvas is the size a player's screen gives the game (capture_culture.gd).
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
	state.set_setting("seen_training_intro", true)
	state.start_season(club, db.club_list(club))
	state.advance()
	var scene: Control = load("res://scenes/TrainingScene.tscn").instantiate()
	root.add_child(scene)
	await _frames(30)
	var tap = load("res://tests/tap.gd")
	await tap.tap(scene.find_child("StatGuideButton", true, false))
	await _frames(20)
	await _shot(out + "_grid.png")
	await tap.tap(scene.find_child("Tile_group2", true, false))
	await _frames(20)
	await _shot(out + "_page.png")
	quit(0)
