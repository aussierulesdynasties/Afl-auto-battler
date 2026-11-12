extends SceneTree
## The League redraft board in the chosen club's colours (director 2026-11-10:
## the board and its tip were the no-club red until Start season), from a fresh
## settings file so the draft's tip is due. Needs a real renderer:
##   godot --path . --windowed --script tools/visual/capture_redraft_colour.gd -- --out /tmp/redraft [--club FRE] [--size 390x844]
## Writes <out>_tip.png (the board under its tip) and <out>_board.png (the tip closed).

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
	var out := "/tmp/redraft"
	var club := "FRE"
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
	# Loaded once the autoloads exist: naming them in this script fails to compile.
	var Intro = load("res://scripts/ui/FirstVisitIntro.gd")
	var Kit = load("res://scripts/ui/UiKit.gd")
	var state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://capture_redraft.save"
	state.settings_path = "user://capture_redraft_settings.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(state.settings_path))
	state.career_seed = 2031
	state.replay_seed = 2031
	state.reset()
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	var base: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, base)
	layout._update_scale()
	await _frames(10)

	state.begin_draft()
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(10)
	# Close whatever tip opened on Choose your club, then choose the club.
	Intro.close_open(ui)
	await _frames(4)
	ui.call("_on_club_chosen", club)
	await _frames(20)
	print("my_club=", state.my_club, " colour club=", Kit.my_club())
	# The redraft's tip over the board: the League redraft's own where it exists, else the draft's.
	var key: String = "league_draft" if Intro.TEXT.has("league_draft") else "draft"
	Intro.show(ui, key)
	await _frames(20)
	await _shot(out + "_tip.png")
	Intro.close_open(ui)
	await _frames(10)
	await _shot(out + "_board.png")
	quit(0 if Kit.my_club() == club and str(state.my_club) == "" else 1)
