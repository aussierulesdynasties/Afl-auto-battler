extends SceneTree
## The main menu's save-release pieces (row T7.R84), at --size WxH into --out <dir>:
##   menu_restore.png      the menu with "Restore last good save" and the version line
##   restore_confirm.png   the sheet that asks before restoring
##   menu_restored.png     the menu after the restore
##   patch_notes.png       this version's patch notes, as they open once
##   godot --windowed --path . -s tools/visual/capture_save_release.gd -- --size 390x844 --out <dir>

var _w := 390
var _h := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "."
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
	var db = root.get_node("GameDB")
	var notes = load("res://scripts/core/PatchNotes.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_save_release.save"
	state.settings_path = "user://capture_save_release.cfg"
	# Only the window: the game's own scaling then lays the menu out as a
	# phone would show it (as capture_save_problem does).
	var layout = root.get_node("ScreenLayout")
	layout.call("set_screen_size", "standard")
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	var os_density := maxf(1.0, DisplayServer.screen_get_dpi() / 96.0)
	var fit := maxf(1.0, minf(_w / 1280.0, _h / 720.0))
	layout.ui_scale = fit / os_density
	layout.call("_update_scale")
	await _frames(10)
	print("window %s logical %s" % [root.size, root.content_scale_size])

	# Fremantle, saved after round 1 and again after round 2.
	state.delete_saved_career()
	state.replay_seed = 2027
	state.reset()
	state.career_seed = 2027
	state.start_season("FRE", db.club_list("FRE"))
	state.advance()
	state.save_career()
	state.advance()
	state.save_career()
	state.reset()
	state.set_setting(notes.SEEN_KEY, notes.version())

	var main: Control = load("res://scenes/Main.tscn").instantiate()
	root.add_child(main)
	await _frames(20)
	_save(out + "/menu_restore.png")
	(main.find_child("RestoreLastGood", true, false) as Button).pressed.emit()
	await _frames(60)
	_save(out + "/restore_confirm.png")
	(main.find_child("ConfirmRestore", true, false) as Button).pressed.emit()
	await _frames(20)
	_save(out + "/menu_restored.png")
	main.queue_free()
	await _frames(3)

	# A device that last ran an older version: the notes open by themselves.
	state.set_setting(notes.SEEN_KEY, "0.0.1")
	main = load("res://scenes/Main.tscn").instantiate()
	root.add_child(main)
	await _frames(60)
	print("patch notes open: ", main.find_child("PatchNotes", true, false) != null)
	_save(out + "/patch_notes.png")
	main.queue_free()
	await _frames(2)
	state.delete_saved_career()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(state.settings_path))
	quit()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _save(path: String) -> void:
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
