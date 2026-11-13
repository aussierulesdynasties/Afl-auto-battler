extends SceneTree
## The year step (Legacy mode, TODO row 142 L2) and the screens after it, for
## the director's look:
##   godot --path . --script tools/visual/capture_year_step.gd -- --out DIR [--size 390x844]
## Writes DIR/<W>x<H>_<screen>.png: year, setup_1990, setup_2026, club_1990,
## hub_1990 (Melbourne's first week, no draft before 1990).
## Needs a real renderer: run windowed, never --headless.

var W := 390
var H := 844
var out := "/tmp/year_step"
var state
var db


func _initialize() -> void:
	_run.call_deferred()


func _arg(name: String, fallback: String) -> String:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == name:
			return str(a[i + 1])
	return fallback


func _shot(name: String) -> void:
	for i in range(14):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	var path := "%s/%dx%d_%s.png" % [out, W, H, name]
	img.save_png(path)
	print("wrote ", path)


func _fresh(id := "2026") -> void:
	state.reset(id)
	state.career_seed = 2027
	state.replay_seed = 2027
	state.tutorials = false
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)


func _run() -> void:
	out = _arg("--out", out)
	var wh := _arg("--size", "390x844").split("x")
	W = int(wh[0])
	H = int(wh[1])
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	state = root.get_node("GameState")
	db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_year_step.save"
	state.settings_path = "user://capture_year_step.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(W, H)
	root.gui_disable_input = true
	DisplayServer.window_set_size(Vector2i(W, H))

	_fresh()
	load("res://scenes/Main.tscn")
	root.get_node("Router").to_main_menu(false)
	for i in range(60):
		await process_frame
		if current_scene != null and current_scene.has_method("_on_new_career"):
			break
	if current_scene == null or not current_scene.has_method("_on_new_career"):
		print("CAPTURE no main menu")
		quit(1)
		return
	var menu = current_scene
	menu._on_new_career()
	await _shot("year")
	menu._on_pick_year("1990")
	await _shot("setup_1990")
	menu._back_from_setup()
	menu._on_pick_year("2026")
	await _shot("setup_2026")
	menu.queue_free()
	await process_frame

	_fresh("1990")
	state.interview_due = true
	state.begin_real_lists()
	var ds: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ds)
	for i in range(6):
		await process_frame
	# Scrolled to Melbourne: no Collingwood in a capture (director 2026-10-13).
	var mel: Control = ds.find_child("Choose_MEL", true, false)
	for sc in ds.find_children("*", "ScrollContainer", true, false):
		if (sc as ScrollContainer).is_ancestor_of(mel):
			(sc as ScrollContainer).scroll_vertical = int(mel.position.y)
	await _shot("club_1990")
	ds.queue_free()
	await process_frame
	state.choose_real_club("MEL")
	state.interview_due = false
	state.finish_intake_draft()
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	# Past the "Starting the pre-season" card.
	for i in range(240):
		await process_frame
	print("CAPTURE hub year=%d club=%s" % [int(state.season_year), str(state.my_club)])
	await _shot("hub_1990")
	hub.queue_free()
	await process_frame
	quit(0)
