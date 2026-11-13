extends SceneTree
## The Supplements saga switch for the director's look, on a phone: the New
## career setup with Controversies and Supplements saga side by side, each
## row's "?" note open so its words show. Never touches a real save.
##   godot --path . --script tools/visual/capture_supplements.gd -- --out PREFIX [--size 390x844]
## Writes <prefix>_on.png (both on) and <prefix>_apart.png (Controversies off, saga on).

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(30)
	root.get_viewport().get_texture().get_image().save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "supplements"
	var cli := OS.get_cmdline_user_args()
	for i in range(cli.size() - 1):
		match str(cli[i]):
			"--out": out = str(cli[i + 1])
			"--size":
				var wh := str(cli[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_supplements.save"
	gs.settings_path = "user://capture_supplements.cfg"
	gs.set_setting("controversies", true)
	gs.set_setting("supplements", true)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	layout.ui_scale = 1.0 / maxf(1.0, layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0))
	layout._update_scale()
	await _frames(10)

	var main: Control = load("res://scenes/Main.tscn").instantiate()
	root.add_child(main)
	await _frames(30)
	main.find_child("NewCareer", true, false).emit_signal("pressed")
	await _frames(30)
	for info in ["ControversiesInfo", "SupplementsInfo"]:
		var b = main.find_child(info, true, false)
		if b == null:
			push_error("capture_supplements: no %s" % info)
		else:
			b.emit_signal("pressed")
	await _frames(10)
	var row = main.find_child("Supplements_on", true, false)
	if row == null:
		push_error("capture_supplements: no Supplements saga switch")
		quit(1)
		return
	var n: Node = row.get_parent()
	while n != null and not (n is ScrollContainer):
		n = n.get_parent()
	if n != null:
		await _frames(5)
		(n as ScrollContainer).ensure_control_visible(row)
	await _shot("%s_on.png" % out)
	main.find_child("Controversies_off", true, false).emit_signal("pressed")
	await _shot("%s_apart.png" % out)
	quit()
