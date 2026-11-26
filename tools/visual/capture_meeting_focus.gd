extends SceneTree
## A midfielder's pre-season meeting, the stat focus picker (director,
## 2026-11-24): the stats his position is rated on in bold, and on a PC his
## profile beside the choices. Needs a real renderer:
##   godot --path . --script tools/visual/capture_meeting_focus.gd -- --out DIR/meeting [--size 1600x900] [--club FRE] [--seed 4127]
## Writes <out>_<W>x<H>_page.png (the four lines, nothing open) and
## <out>_<W>x<H>.png (his meeting open over the page), <out>_<W>x<H>_ticked.png
## (the mids and one defender ticked) and <out>_<W>x<H>_group.png (one stat
## focus for them all, the player who can't train it named). Never touches a real save.
const Ovr := preload("res://tests/ovr.gd")

var W := 1600
var H := 900
var _seed := 4127


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(8)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if W >= 760 and img.get_width() != W:
		img.resize(W, H, Image.INTERPOLATE_LANCZOS)
	img.save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "meeting"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out": out = str(a[i + 1])
			"--club": club = str(a[i + 1])
			"--seed": _seed = int(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_meeting_focus.save"
	state.settings_path = "user://capture_meeting_focus.cfg"
	seed(_seed)
	state.reset()
	state.career_seed = _seed
	state.replay_seed = _seed
	state.set_setting("seen_weekly_loop_intro", true)
	state.set_setting("seen_training_intro", true)
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	var density: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, density)
	layout._update_scale()
	await _frames(10)
	print("canvas ", root.get_visible_rect().size)
	state.start_season(club, db.club_list(club))
	state.open_preseason()
	# The first midfielder (best first, as the meetings list them) with a focus to pick.
	var pick: Dictionary = {}
	var mids := []
	for q in state.my_list:
		if str(q.get("role", "")) == "MID" and state.project_job(q) == "" and state.focus_options(q).size() >= 10:
			mids.append(q)
	mids.sort_custom(func(x, y): return int(Ovr.of(x, 0)) > int(Ovr.of(y, 0)))
	if not mids.is_empty():
		pick = mids[0]
	root.get_node("Router").go("hub")
	var guard := 0
	while (current_scene == null or not current_scene.scene_file_path.contains("PreSeason")) and guard < 600:
		await process_frame
		guard += 1
	await _frames(10)
	if pick.is_empty():
		print("MISSING a midfielder")
		quit(1)
		return
	print("player ", db.player_display_name(pick), " ", pick["role"], " ", Ovr.of(pick))
	var tag := "%dx%d" % [W, H]
	await _shot("%s_%s_page.png" % [out, tag])
	var lines := current_scene.find_child("PreSeasonMeetings", true, false) as Control
	var page := current_scene.find_child("PreSeasonPage", true, false) as Control
	var sc := page.get_parent() as ScrollContainer
	print("lines ", lines.get_global_rect(), " page view ", sc.get_global_rect(), " scroll max ", sc.get_v_scroll_bar().max_value - sc.size.y)
	var tap := current_scene.find_child("MeetTap_" + str(pick["id"]), true, false) as Button
	tap.emit_signal("pressed")
	await _frames(12)
	await _shot("%s_%s.png" % [out, tag])
	(current_scene.find_child("MeetClose", true, false) as Button).emit_signal("pressed")
	await _frames(8)
	(current_scene.find_child("MeetAll_MID", true, false) as Button).emit_signal("pressed")
	await _frames(4)
	var defs := current_scene.find_child("MeetLine_DEF", true, false) as Node
	for q in state.my_list:
		var t := defs.find_child("MeetTick_" + str(q["id"]), true, false) as Button
		if t != null:
			t.emit_signal("pressed")
			break
	await _frames(6)
	await _shot("%s_%s_ticked.png" % [out, tag])
	(current_scene.find_child("PreSeasonGo", true, false) as Button).emit_signal("pressed")
	await _frames(6)
	var grid := current_scene.find_child("MeetGroupFocus", true, false) as Node
	var names := []
	for b in grid.get_children():
		names.append(str(b.name))
	for n in names:
		var b := current_scene.find_child(n, true, false) as Button
		b.emit_signal("pressed")
		await _frames(3)
		if current_scene.find_child("MeetGroupSkip", true, false) != null:
			print("picked ", n)
			break
	await _shot("%s_%s_group.png" % [out, tag])
	quit()
