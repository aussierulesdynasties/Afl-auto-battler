extends SceneTree
## Readability sweep (row T3.R9): one screen at the director's two sizes, the
## same career every time so before and after line up. A real renderer and a
## window (no --headless). Never touches a real save.
##   godot --path . --windowed --script tools/visual/capture_sweep.gd -- --screen hub --out DIR --tag before --size 390x844
## Writes DIR/<tag>_<screen>_<w>.png and, when the page scrolls, <tag>_<screen>_<w>_down.png.

var _size := Vector2i(390, 844)
var _state: Node
var _router: Node


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
			"--rounds":
				rounds = int(str(a[i + 1]))
			"--size":
				var wh := str(a[i + 1]).split("x")
				_size = Vector2i(int(wh[0]), int(wh[1]))
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
	if screen == "match":
		_state.prepare_interactive_match()
	_router.stack = []
	_router.go("main")
	await _frames(6)
	_router.go(screen)
	# The first screen of a run can sit behind the loading cover for a while.
	var cover: Node = root.get_node("ScreenTransition")
	for wait in range(1200):
		if wait > 60 and str(_router.call("current")) == screen and not bool(cover.get("busy")):
			break
		await process_frame
	await _frames(60)
	await _shut_popups()
	if screen == "match":
		await _play_into_match(root.find_child("MatchScene", true, false))
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


## The live match: Start, play at 8x, take each in-play call's default, and pause
## at Q1 15' so the feed, the score and the momentum all have something to show.
func _play_into_match(scene: Node) -> void:
	if scene == null:
		push_error("capture_sweep: no MatchScene")
		return
	for b in scene.find_children("*", "Button", true, false):
		if (b as Button).text == "Start" and (b as Button).is_visible_in_tree():
			(b as Button).emit_signal("pressed")
			break
	await _frames(20)
	scene.call("_on_speed", 8.0)
	for wait in range(12000):
		if int(scene.get("_shown_q")) > 1 or int(scene.get("_shown_min")) >= 15:
			break
		if scene.get("_moment_overlay") != null:
			var m: Dictionary = _state.pending_sim.pending_moment
			scene.call("_on_moment_choice", int(m.get("default", 0)))
		await process_frame
	var pitch: Node = scene.get("_pitch")
	if bool(pitch.get("playing")):
		scene.call("_on_toggle")
	print("match paused at Q%d %d'" % [int(scene.get("_shown_q")), int(scene.get("_shown_min"))])


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
