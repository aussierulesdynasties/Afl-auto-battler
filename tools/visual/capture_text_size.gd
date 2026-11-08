extends SceneTree
## The screens the sweep (sweep_screens.gd --png) does not open, at a Settings
## text size (row 118): the Settings sheet itself, the match preview, the match
## live after the bounce, its first call, the press conference, the almanac
## and its club picker, the players' stats filters and Selection's search.
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_text_size.gd -- --size 390x844 --text-size largest --out DIR
## Writes DIR/settings.png, preview.png, match_live.png, match_call.png,
## press.png, almanac.png, almanac_pick.png, stats_filters.png,
## stats_filter_list.png and selection.png. A windowed run (headless draws no image). Seeded Melbourne
## career; never touches a real save.

const SEED := 2031
const CLUB := "MEL"

var _state
var _db
var _router
var _out := "caps"


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(name: String) -> void:
	await _frames(4)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(_out.path_join(name + ".png"))
	print("wrote ", _out.path_join(name + ".png"))


func _career() -> void:
	_state.reset()
	_state.career_seed = SEED
	_state.replay_seed = SEED
	seed(SEED)
	var seen := ["training", "weekly_loop", "season_stats", "momentum"]
	seen.append_array(load("res://scripts/ui/FirstVisitIntro.gd").TEXT.keys())
	for k in seen:
		_state.set_setting("seen_%s_intro" % k, true)
	_state.start_season(CLUB, _db.club_list(CLUB))


## Waits up to `limit` frames for a visible node named `name`.
func _wait_for(name: String, limit := 600) -> Node:
	for i in range(limit):
		await process_frame
		var n := root.find_child(name, true, false)
		if n is CanvasItem and (n as CanvasItem).is_visible_in_tree():
			await _frames(30)
			return n
	return null


func _go(key: String) -> void:
	_router.stack = []
	_router.go(key)
	await _frames(120)


func _run() -> void:
	var text_size := "standard"
	var w := 390
	var h := 844
	var cli := OS.get_cmdline_user_args()
	for i in range(cli.size() - 1):
		match str(cli[i]):
			"--out":
				_out = str(cli[i + 1])
			"--text-size":
				text_size = str(cli[i + 1])
			"--size":
				var wh := str(cli[i + 1]).split("x")
				w = int(wh[0])
				h = int(wh[1])
	DirAccess.make_dir_recursive_absolute(_out)
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_router = root.get_node("Router")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_text_size.save"
	_state.settings_path = "user://capture_text_size.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(_state.settings_path))
	# Loaded, not named: the autoloads UiKit needs are not up when this script compiles.
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	_state.set_text_size(text_size)
	root.size = Vector2i(w, h)
	DisplayServer.window_set_size(Vector2i(w, h))
	await _frames(10)
	# The same UI units as the sweep and CI: a plain 96-dpi screen.
	var layout = root.get_node("ScreenLayout")
	var px := Vector2(root.size)
	var here: float = layout.desktop_density(px, DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = layout.desktop_density(px, 1.0, 0) / maxf(1.0, here)
	layout._update_scale()
	await _frames(10)

	# Settings, opened from the main menu.
	_career()
	await _go("main")
	var open := await _wait_for("MenuSettings") as Button
	if open != null:
		open.emit_signal("pressed")
		if await _wait_for("SettingsTextSize") != null:
			await _shot("settings")
	else:
		push_error("capture_text_size: no Settings on the main menu")

	# The match preview, then the match live after the first bounce.
	_career()
	await _go("preview")
	if await _wait_for("PreviewColumn") != null:
		await _shot("preview")
	if _state.prepare_interactive_match():
		await _go("match")
		var start := await _wait_for("StartQuarter") as Button
		if start != null:
			start.emit_signal("pressed")
			await _frames(420)
			await _shot("match_live")
			# The first call of the match, once its choices are up.
			for i in range(9000):
				await process_frame
				var c := root.find_child("Moment_0", true, false)
				if c is Button and not (c as Button).disabled:
					await _frames(40)
					await _shot("match_call")
					break
		else:
			push_error("capture_text_size: no pre-bounce box")

	# The press conference after a loss.
	_career()
	var MC = load("res://scripts/sim/MediaConference.gd")
	_state.media_conference = MC.pick({"club": CLUB, "opponent_name": "Carlton", "round": 8,
			"year": int(_state.season_year), "result": {"home": CLUB, "away": "CAR", "score": [55, 101]}}, {})
	_state.media_conference["opp"] = "Carlton"
	await _go("press")
	if await _wait_for("MediaQuestion") != null:
		await _shot("press")

	# The almanac a round in, its club picker open.
	_career()
	_state.advance()
	await _go("almanac")
	await _shot("almanac")
	var pick := await _wait_for("ClubRecordsPick") as OptionButton
	if pick != null:
		pick.show_popup()
		await _frames(20)
		await _shot("almanac_pick")

	# The players' stats: the filters sheet, then the club filter's list.
	var stats_script: GDScript = load("res://scripts/ui/StatsHubScene.gd")
	stats_script.set("current", "players")
	await _go("stats")
	var filters := await _wait_for("FiltersToggle") as Button
	if filters != null:
		filters.emit_signal("pressed")
		var club_pick := await _wait_for("Filter_club") as OptionButton
		if club_pick != null:
			await _shot("stats_filters")
			club_pick.show_popup()
			await _frames(20)
			await _shot("stats_filter_list")
	stats_script.set("current", "ladder")

	# Selection: the search field beside the line tabs.
	await _go("selection")
	if await _wait_for("BuilderSearch") != null:
		await _shot("selection")
	_state.set_text_size("standard")
	quit(0)
