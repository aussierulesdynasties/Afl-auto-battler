extends SceneTree
## Readability sweep (row T3.R9): one screen at the director's two sizes, the
## same career every time so before and after line up. A real renderer and a
## window (no --headless). Never touches a real save.
##   godot --path . --windowed --script tools/visual/capture_sweep.gd -- --screen hub --out DIR --tag before --size 390x844
## Writes DIR/<tag>_<screen>_<w>.png and, when the page scrolls, <tag>_<screen>_<w>_down.png.
## --screen match: the coach's own live match of the next round. Writes
## <tag>_match_<w>_prebounce.png (the first coach box), then starts the quarter
## and writes <tag>_match_<w>_play.png after --play frames (default 900, about
## 15 s at 1x) and <tag>_match_<w>_late.png after as many again at 4x.

var _size := Vector2i(390, 844)
var _state: Node
var _router: Node
var _play := 900


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "."
	var tag := "now"
	var screen := "hub"
	var club := "FRE"
	var rounds := 6
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--tag":
				tag = str(a[i + 1])
			"--screen":
				screen = str(a[i + 1])
			"--club":
				club = str(a[i + 1])
			"--play":
				_play = int(str(a[i + 1]))
			"--rounds":
				rounds = int(str(a[i + 1]))
			"--size":
				var wh := str(a[i + 1]).split("x")
				_size = Vector2i(int(wh[0]), int(wh[1]))
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	_state = root.get_node("GameState")
	var db: Node = root.get_node("GameDB")
	_router = root.get_node("Router")
	_state.autosave_enabled = false
	_state.save_path = "user://capture_sweep.save"
	_state.settings_path = "user://capture_sweep.cfg"
	root.size = _size
	DisplayServer.window_set_size(_size)
	# --size is in UI units: a scaled (HiDPI) desktop would otherwise lay a wide
	# window out at half the units, as a phone.
	var sl: Node = root.get_node("ScreenLayout")
	sl.ui_scale = 96.0 / maxf(96.0, float(DisplayServer.screen_get_dpi()))
	sl.call("_update_scale")
	_state.reset()
	_state.replay_seed = 690
	_state.start_season(club, db.club_list(club))
	_state.tutorials = false
	for r in range(rounds):
		_state.advance()
	for card in _state.week_events:
		card["popped"] = true
	_state.skip_media_conference()
	_router.stack = []
	_router.go("main")
	await _frames(6)
	if screen == "match":
		await _match(out, tag)
		quit()
		return
	_router.go(screen)
	# The first screen of a run can sit behind the loading cover for a while.
	var cover: Node = root.get_node("ScreenTransition")
	for wait in range(1200):
		if wait > 60 and str(_router.call("current")) == screen and not bool(cover.get("busy")):
			break
		await process_frame
	await _frames(60)
	await _shut_popups()
	await _frames(40)
	var stem := "%s/%s_%s_%d" % [out, tag, screen, _size.x]
	_save(stem + ".png")
	var sc := _page_scroll()
	if sc != null and sc.get_v_scroll_bar().max_value > sc.size.y + 8:
		sc.scroll_vertical = int(sc.size.y) - 40
		await _frames(8)
		_save(stem + "_down.png")
	print("captured ", stem)
	quit()


func _match(out: String, tag: String) -> void:
	_state.set_setting("seen_training_intro", true)
	if not _state.prepare_interactive_match():
		push_error("no match to prepare")
		return
	_router.go("match")
	var cover: Node = root.get_node("ScreenTransition")
	for wait in range(1200):
		if wait > 60 and str(_router.call("current")) == "match" and not bool(cover.get("busy")):
			break
		await process_frame
	await _frames(60)
	var stem := "%s/%s_match_%d" % [out, tag, _size.x]
	_save(stem + "_prebounce.png")
	var start := root.find_child("StartQuarter", true, false) as Button
	if start == null:
		push_error("no StartQuarter button")
		return
	start.emit_signal("pressed")
	await _frames(_play)
	_save(stem + "_play.png")
	var scene: Node = root.find_child("MatchScene", true, false)
	if scene != null and scene.has_method("_on_speed"):
		scene.call("_on_speed", 4.0)
	await _frames(_play)
	_save(stem + "_late.png")
	print("captured ", stem)


func _shut_popups() -> void:
	for attempt in range(6):
		var shut := false
		for b in root.find_children("*", "Button", true, false):
			var t := (b as Button).text
			if (b as Button).is_visible_in_tree() and (t == "Got it" or t == "Close" or t == "Done" or t == "Later" or t == "Back to hub"):
				(b as Button).emit_signal("pressed")
				shut = true
				break
		if not shut:
			return
		await _frames(12)


## The tallest visible vertical scroller: the page a coach reads down.
func _page_scroll() -> ScrollContainer:
	var best: ScrollContainer = null
	for n in root.find_children("*", "ScrollContainer", true, false):
		var sc := n as ScrollContainer
		if sc.is_visible_in_tree() and (best == null or sc.size.y * sc.size.x > best.size.y * best.size.x):
			best = sc
	return best


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(path)
