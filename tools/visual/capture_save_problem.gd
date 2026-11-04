extends SceneTree
## The main menu when the career file on disk cannot be continued (T5.Q24):
## writes <out>_unreadable.png and <out>_newer.png at --size WxH.
##   godot --path . -s tools/visual/capture_save_problem.gd -- --size 390x844 --out x

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "save_problem"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://capture_save_problem.save"
	state.settings_path = "user://capture_save_problem.cfg"
	# Only the window: the game's own scaling then lays the menu out as a
	# phone or a PC would show it (as capture_desktop does).
	root.get_node("ScreenLayout").call("set_screen_size", "standard")
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	# Lay out as a 96-DPI screen of this size would, whatever this machine's
	# own Windows scaling is (a 300% 4K desktop would shrink the canvas to a
	# third).
	var layout = root.get_node("ScreenLayout")
	var os_density := maxf(1.0, DisplayServer.screen_get_dpi() / 96.0)
	var fit := maxf(1.0, minf(_w / 1280.0, _h / 720.0))
	layout.ui_scale = fit / os_density
	layout.call("_update_scale")
	await _frames(10)
	print("window %s logical %s" % [root.size, root.content_scale_size])
	for kind in ["unreadable", "newer"]:
		state.reset()
		_write(state.save_path, kind)
		var main: Control = load("res://scenes/Main.tscn").instantiate()
		root.add_child(main)
		await _frames(12)
		_save("%s_%s.png" % [out, kind])
		main.queue_free()
		await _frames(2)
	DirAccess.remove_absolute(ProjectSettings.globalize_path(state.save_path))
	quit()


func _write(path: String, kind: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if kind == "newer":
		f.store_var({"version": 99, "meta": {}, "state": {}})
	else:
		f.store_string("not a save")
	f.close()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
