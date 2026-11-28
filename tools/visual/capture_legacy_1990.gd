extends SceneTree
## Row 142 first-slice captures (not committed): the year step with 1990
## picked, and a 1990 club's rated list.
##   godot --path . --script tools/visual/capture_legacy_1990.gd -- --out DIR --club FIT

const W := 390
const H := 844
var out := "."
var state


func _initialize() -> void:
	_run.call_deferred()


func _arg(name: String, fallback: String) -> String:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == name:
			return str(a[i + 1])
	return fallback


func _frames(n := 14) -> void:
	for i in range(n):
		await process_frame


func _shot(name: String) -> void:
	await _frames()
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png("%s/%s.png" % [out, name])
	print("wrote ", name)


func _fresh(id := "2026") -> void:
	state.reset(id)
	state.career_seed = 1990
	state.replay_seed = 1990
	state.tutorials = false
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)


func _run() -> void:
	out = _arg("--out", out)
	var club := _arg("--club", "FIT")
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://capture_legacy_1990.save"
	state.settings_path = "user://capture_legacy_1990.cfg"
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))

	# Look 1: the year step, then 1990 picked.
	_fresh()
	load("res://scenes/Main.tscn")
	root.get_node("Router").to_main_menu(false)
	for i in range(120):
		await process_frame
		if current_scene != null and current_scene.has_method("_on_new_career"):
			break
	var menu = current_scene
	if menu == null or not menu.has_method("_on_new_career"):
		print("CAPTURE no main menu")
		quit(1)
		return
	menu._on_new_career()
	await _shot("1_year_step")
	menu._on_pick_year("1990")
	await _shot("1_year_1990_setup")
	menu.queue_free()
	await _frames(3)

	# Look 2: a 1990 club's list on its real players, rated.
	_fresh("1990")
	state.interview_due = true
	state.begin_real_lists()
	state.choose_real_club(club)
	state.interview_due = false
	state.finish_intake_draft()
	print("CAPTURE year=%d club=%s list=%d" % [int(state.season_year), str(state.my_club), state.my_list().size() if state.has_method("my_list") else -1])
	var ls: Control = load("res://scenes/ListScene.tscn").instantiate()
	root.add_child(ls)
	await _frames(8)
	await _shot("2_list_%s" % club)
	for t in ls.find_children("*", "Button", true, false):
		if (t as Button).text == "Full list":
			(t as Button).emit_signal("pressed")
			break
	await _frames(30)
	await _shot("2_full_list_%s" % club)
	var rows: Node = ls.find_child("ListRows", true, false)
	var sc: Node = rows
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		(sc as ScrollContainer).scroll_vertical = int((sc as ScrollContainer).size.y) - 40
		await _shot("2_full_list_%s_down" % club)
	# The captain's row (Roos, a defender), well down the list.
	for l in ls.find_children("*", "Label", true, false):
		if (l as Label).text.contains("Paul Roos") and sc != null:
			(sc as ScrollContainer).ensure_control_visible(l)
			await _frames(2)
			(sc as ScrollContainer).scroll_vertical += 300
			await _shot("2_full_list_%s_roos" % club)
			break
	quit(0)
