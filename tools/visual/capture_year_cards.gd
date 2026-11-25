extends SceneTree
## The year step's start cards, scrolled to one card, for the director's look.
## Never touches a real save.
##   godot --path . --script tools/visual/capture_year_cards.gd -- --out PREFIX [--size 390x844] [--card 2020]
## Writes <prefix>.png.

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	var out := "year_cards"
	var card := "2020"
	var cli := OS.get_cmdline_user_args()
	for i in range(cli.size() - 1):
		match str(cli[i]):
			"--out": out = str(cli[i + 1])
			"--card": card = str(cli[i + 1])
			"--size":
				var wh := str(cli[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://capture_year_cards.save"
	gs.settings_path = "user://capture_year_cards.cfg"
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
	var b := main.find_child("StartYear_" + card, true, false) as Control
	var sc := main.find_child("StartsScroll", true, false) as ScrollContainer
	if sc != null and b != null:
		sc.ensure_control_visible(b)
	await _frames(30)
	if b != null:
		var pad := b.get_child(0) as Control
		print("card %s: button %.0f tall, words need %.0f" % [card, b.size.y, pad.get_combined_minimum_size().y])
	root.get_viewport().get_texture().get_image().save_png(out + ".png")
	print("wrote ", out, ".png")
	quit()
