extends SceneTree
## The two screens that lost the "Player names" choice (director, 2026-11-12:
## "Real Names only"), for a frame check. Windowed:
##   godot --windowed --path . --script tools/visual/capture_real_names.gd -- --out <dir> --size 390x844
## Writes <dir>/new_career_<size>.png (the New career setup; _scrolled too where
## it scrolls), settings_menu_<size>.png
## (Settings from the main menu) and settings_hub_<size>.png (Settings in a
## Fremantle career). Dark theme. Never touches a real save or settings file.

var _w := 390
var _h := 844
var _out := "real_names"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				_out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	DirAccess.make_dir_recursive_absolute(_out)
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_real_names.save"
	state.settings_path = "user://capture_real_names.cfg"
	state.reset()
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	# The canvas is the size a player's screen gives the game (capture_culture.gd),
	# not this machine's own display scaling.
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	var base: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, base)
	layout._update_scale()
	await _frames(10)
	print("canvas ", root.get_visible_rect().size)

	# New career setup, straight from the main menu.
	state.new_career_setup_requested = true
	var menu: Control = load("res://scenes/Main.tscn").instantiate()
	root.add_child(menu)
	await _frames(20)
	print("NEW CAREER TEXT: ", _text(menu).replace("\n", " | "))
	_save("new_career")
	# On a phone the setup scrolls: the last rows too.
	var last: Control = menu.find_child("Canberra", true, false)
	var sc: Node = last.get_parent() if last != null else null
	while sc != null and not (sc is ScrollContainer):
		sc = sc.get_parent()
	if sc != null:
		(sc as ScrollContainer).scroll_vertical = 100000
		await _frames(6)
		print("NEW CAREER scrolls by ", (sc as ScrollContainer).scroll_vertical, " units")
		if (sc as ScrollContainer).scroll_vertical > 0:
			_save("new_career_scrolled")
	menu.queue_free()
	await _frames(4)

	# Settings from the main menu.
	menu = load("res://scenes/Main.tscn").instantiate()
	root.add_child(menu)
	await _frames(20)
	var sheet: Control = load("res://scripts/ui/OptionsSheet.gd").open(menu, false, true)
	await _frames(12)
	print("SETTINGS (MENU) TEXT: ", _text(sheet).replace("\n", " | "))
	_save("settings_menu")
	menu.queue_free()
	await _frames(4)

	# Settings inside a Fremantle career.
	state.replay_seed = 2027
	state.start_season("FRE", db.club_list("FRE"))
	state.tutorials = false
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _frames(20)
	sheet = load("res://scripts/ui/OptionsSheet.gd").open(hub, true)
	await _frames(12)
	print("SETTINGS (HUB) TEXT: ", _text(sheet).replace("\n", " | "))
	_save("settings_hub")
	quit(0)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


## Every visible label and button caption under a node, in tree order.
func _text(n: Node) -> String:
	var out := PackedStringArray()
	var todo := [n]
	while not todo.is_empty():
		var c: Node = todo.pop_front()
		if c is Control and not (c as Control).is_visible_in_tree():
			continue
		if (c is Label or c is Button) and str(c.get("text")) != "":
			out.append(str(c.get("text")))
		todo = c.get_children() + todo
	return "\n".join(out)


func _save(name: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	var path := "%s/%s_%dx%d.png" % [_out, name, _w, _h]
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
