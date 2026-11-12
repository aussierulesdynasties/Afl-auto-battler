extends SceneTree
## The two ways to take your match (Watch, Skip; Key moments cut, director
## 2026-11-08) for the director's look: the hub's poster with each chosen, and
## your match watched, the first quarter under way, with its top bar.
## Needs a real renderer:
##   godot --path . --script tools/visual/capture_match_way.gd -- --out /tmp/way [--size 390x844] [--club FRE] [--opp MEL]
## Writes <out>_watch.png and <out>_skip.png (the hub, the poster with Watch or
## Skip chosen) and <out>_match.png (the match screen watched, the first quarter
## under way). Prints each button's size and place.

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


## Waits for the Router's threaded load to put `scene_name` up (slow on a busy
## machine), then a few frames more for it to lay out.
func _await_scene(scene_name: String) -> Node:
	for i in range(1200):
		if current_scene != null and current_scene.name == scene_name:
			break
		await process_frame
	await _frames(20)
	print("scene ", current_scene.name if current_scene != null else "none")
	return current_scene


func _shot(path: String) -> void:
	await _frames(10)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if W >= 760 and img.get_width() != W:
		img.resize(W, H, Image.INTERPOLATE_LANCZOS)
	img.save_png(path)
	print("wrote ", path, " ", img.get_size())
	# The thumb targets this capture shows, measured (at least 44 px tall).
	for b in root.find_children("*", "Button", true, false):
		var t := (b as Button).text
		if (b as Button).is_visible_in_tree() and t in ["Watch", "Skip", "Pause", "Play", "1x", "2x", "4x", "8x",
				"Skip to full time", "Skip to quarter time", "Play match", "Pick the side"]:
			print("  button '", t, "' ", (b as Button).size, " at ", (b as Button).global_position)
	var grid := root.find_child("MatchWay", true, false) as Control
	if grid != null and grid.is_visible_in_tree():
		print("  MatchWay grid ", grid.get_global_rect())


## The hub with the poster's choices in view, `way` chosen by a press on it.
func _poster(way: String, path: String) -> void:
	var b := root.find_child("MatchWay_" + way, true, false) as Button
	if b != null:
		var p := b.get_parent()
		while p != null:
			if p is ScrollContainer:
				(p as ScrollContainer).ensure_control_visible(b)
				break
			p = p.get_parent()
		b.emit_signal("pressed")
	await _frames(20)
	await _shot(path)


func _run() -> void:
	var out := "/tmp/way"
	var club := "FRE"
	var opp := "MEL"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--club":
				club = str(a[i + 1])
			"--opp":
				opp = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_way.save"
	state.settings_path = "user://capture_way_settings.cfg"
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	var base: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, base)
	layout._update_scale()
	await _frames(10)
	# A season whose first match is against `opp`.
	var found := false
	for tries in range(120):
		state.reset()
		state.career_seed = 2050 + tries
		state.replay_seed = 2050 + tries
		state.set_setting("seen_weekly_loop_intro", true)
		state.set_setting("seen_training_intro", true)
		state.start_season(club, db.club_list(club))
		var m: Dictionary = {}
		for f in state.season.fixture[state.season.round_index]:
			if str(f["home"]) == club or str(f["away"]) == club:
				m = f
		if str(m.get("home", "")) == opp or str(m.get("away", "")) == opp:
			found = true
			break
	print("opponent ", opp, " found ", found)
	state.set_match_way("watch")
	var router = root.get_node("Router")
	router.go("hub")
	await _await_scene("HubScene")
	for b in root.find_children("*", "Button", true, false):
		if (b as Button).text == "Got it" and (b as Button).is_visible_in_tree():
			(b as Button).emit_signal("pressed")
	await _frames(40)
	await _poster("watch", out + "_watch.png")
	await _poster("skip", out + "_skip.png")
	# Your match watched, the first quarter under way.
	state.set_match_way("watch")
	state.set_vignettes_on(false)
	state.prepare_interactive_match()
	router.go("match")
	var scene := await _await_scene("MatchScene")
	if scene == null:
		quit(1)
		return
	var start = scene.find_child("StartQuarter", true, false)
	if start != null:
		start.emit_signal("pressed")
	await _frames(20)
	var pitch = scene.get("_pitch")
	for i in range(900):
		if pitch != null and pitch.playing and int(pitch.current_index()) > 30:
			break
		await process_frame
	print("way ", state.match_way_live, " speed ", pitch.speed if pitch != null else -1,
			" events ", pitch.current_index() if pitch != null else -1)
	await _shot(out + "_match.png")
	quit(0)
