extends SceneTree
## Scratch board capture: the sweep's seeded Melbourne career (seed 2031), but
## only the screens named in --only, each saved as <png dir>/<key>.png.
##   --size WxH --png dir --only selection,offseason [--text-size standard]
const SEED := 2031
const CLUB := "MEL"
var W := 960
var H := 540
var _png := ""
var _only: PackedStringArray = []
var _state
var _db


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(key: String, path: String) -> void:
	var scene: Node = load(path).instantiate()
	root.add_child(scene)
	await _frames(70)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(_png.path_join(key + ".png"))
	print("CAP %s" % key)
	scene.queue_free()
	await _frames(3)


func _career(start := true) -> void:
	_state.reset()
	_state.career_seed = SEED
	_state.replay_seed = SEED
	var seen := ["training", "weekly_loop", "season_stats", "momentum"]
	seen.append_array(load("res://scripts/ui/FirstVisitIntro.gd").TEXT.keys())
	for k in seen:
		_state.set_setting("seen_%s_intro" % k, true)
	if start:
		_state.start_season(CLUB, _db.club_list(CLUB))


func _run() -> void:
	var text_size := "standard"
	var cli := OS.get_cmdline_user_args()
	for i in range(cli.size() - 1):
		if str(cli[i]) == "--text-size":
			text_size = str(cli[i + 1])
		if str(cli[i]) == "--png":
			_png = str(cli[i + 1])
			DirAccess.make_dir_recursive_absolute(_png)
		if str(cli[i]) == "--only":
			_only = str(cli[i + 1]).split(",")
		if str(cli[i]) == "--size":
			var wh := str(cli[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://board.save"
	_state.settings_path = "user://board.cfg"
	UK.apply_appearance("dark")
	UK.apply_text_size(text_size)
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	var px := Vector2(root.size)
	var here: float = layout.desktop_density(px, DisplayServer.screen_get_scale(), DisplayServer.screen_get_dpi())
	var plain: float = layout.desktop_density(px, 1.0, 0)
	layout.ui_scale = plain / maxf(1.0, here)
	layout._update_scale()
	await _frames(10)
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	_career(true)
	for key in ["hub", "selection", "training", "list", "coaching", "staff", "stats"]:
		if key in _only:
			await _shot(key, root.get_node("Router").SCENES[key])
	if "preseason" in _only:
		_career(true)
		_state.open_preseason()
		await _shot("preseason", "res://scenes/PreSeasonScene.tscn")
	if "offseason" in _only or "season_review" in _only:
		_career(true)
		var guard := 0
		while not _state.season.is_season_over() and guard < 60:
			guard += 1
			_state.advance()
		if "season_review" in _only:
			await _shot("season_review", "res://scenes/SeasonReviewScene.tscn")
		_state.open_offseason()
		if "offseason" in _only:
			await _shot("offseason", "res://scenes/OffseasonScene.tscn")
	quit(0)
