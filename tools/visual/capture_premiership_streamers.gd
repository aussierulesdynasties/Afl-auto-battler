extends SceneTree
## The premiership streamers over the hub's finals series, for the director's
## look. Needs a real renderer:
##   godot --path . --script tools/visual/capture_premiership_streamers.gd --
##       --out <existing dir> [--size 390x844] [--club FRE] [--premier FRE]
## Plays a seeded season through the Grand Final, opens the hub, opens the
## finals series as a player does and writes the fall at four moments
## (streamers_08.png, _16, _24: early, mid-fall, late; streamers_after.png:
## the fall over). --premier shows that club as the premier (it trades places
## with the club that won, this capture only; nothing is saved).

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "."
	var club := "FRE"
	var premier := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		var v := str(a[i + 1]) if i + 1 < a.size() else ""
		match str(a[i]):
			"--out": out = v
			"--size":
				W = int(v.split("x")[0])
				H = int(v.split("x")[1])
			"--club": club = v
			"--premier": premier = v
	await process_frame
	var db = root.get_node("GameDB")
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.event_sheets = false
	gs.save_path = "user://capture_streamers.save"
	gs.settings_path = "user://capture_streamers_settings.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		gs.set_setting("seen_%s_intro" % key, true)
	gs.reset()
	gs.career_seed = 7
	gs.replay_seed = 7
	gs.start_season(club, db.club_list(club))
	var guard := 0
	while guard < 400 and not gs.season.is_season_over():
		guard += 1
		gs.advance()
	var won := str(gs.season.finals.get("premier", ""))
	if premier != "" and won != "" and premier != won:
		gs.season.finals = _swap(gs.season.finals, won, premier)
	if not gs.training_report.is_empty():
		gs.training_report["dismissed"] = true
	# The canvas a player's screen gives the game, whatever this machine's display density.
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	for i in range(10):
		await process_frame
	var layout = root.get_node("ScreenLayout")
	var density: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, density)
	layout._update_scale()
	for i in range(10):
		await process_frame
	print("canvas ", root.get_visible_rect().size)
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _wait(1.2)
	var tries := 0
	while hub.find_child("MediaConference", true, false) != null and tries < 4:
		hub.call("handle_back")
		await _wait(0.3)
		tries += 1
	hub.call("_show_finals")
	await _wait(0.6)   # the sheet has risen
	var fall: Control = hub.find_child("PremiershipStreamers", true, false)
	if fall == null:
		push_error("no streamers over the finals series")
		quit(1)
		return
	fall.set_process(false)
	print("premier ", fall.get("club"), " colours ", fall.get("colours"))
	for t in [0.8, 1.6, 2.4]:
		fall.call("seek", t)
		for i in range(4):
			await process_frame
		_save("%s/streamers_%02d.png" % [out, int(round(t * 10.0))])
	fall.call("seek", 99.0)
	await _wait(0.3)
	print("after the fall: ", hub.find_child("PremiershipStreamers", true, false))
	_save("%s/streamers_after.png" % out)
	quit()


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path)


func _wait(seconds: float) -> void:
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < int(seconds * 1000.0):
		await process_frame


## `v` with the two club codes trading places wherever they appear.
func _swap(v, a: String, b: String):
	if v is String:
		return b if v == a else (a if v == b else v)
	if v is Array:
		var out := []
		for x in v:
			out.append(_swap(x, a, b))
		return out
	if v is Dictionary:
		var d := {}
		for k in v:
			d[k] = _swap(v[k], a, b)
		return d
	return v
