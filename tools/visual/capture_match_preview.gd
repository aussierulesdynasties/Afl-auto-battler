extends SceneTree
## The match preview (the step between Play match and the setup, director
## 2026-11-07), dark, 390x844 by default:
##   godot --path . --script tools/visual/capture_match_preview.gd -- --out /tmp/prev [--club COL] [--rounds N] [--size 390x844]
## Needs a real renderer and a window (keep it off screen with an override.cfg).
## Writes <out>_1_top.png (the page as it opens), <out>_2_bottom.png (scrolled to
## the end, Continue under it), <out>_3_synergies.png (the synergy guide over it)
## and <out>_4_report.png (the Assistant's report over it). Nothing touches a save.

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _save(path: String) -> void:
	for i in range(10):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "/tmp/prev"
	var club := "COL"
	var rounds := 0
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--club":
				club = str(a[i + 1])
			"--rounds":
				rounds = int(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				W = int(wh[0])
				H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_preview.save"
	state.settings_path = "user://capture_preview.cfg"
	state.reset()
	state.career_seed = 2027
	state.replay_seed = 2027
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.start_season(club, db.club_list(club))
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	var sl = root.get_node("ScreenLayout")
	sl.ui_scale = 1.0 / maxf(0.01, sl.desktop_density(Vector2(W, H), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0))
	sl._update_scale()
	for r in range(rounds):
		state.advance()
	var ui: Control = load("res://scenes/MatchPreviewScene.tscn").instantiate()
	root.add_child(ui)
	await _save(out + "_1_top.png")
	var sc: ScrollContainer = ui.find_child("PreviewScroll", true, false)
	if sc != null:
		sc.scroll_vertical = 100000
	await _save(out + "_2_bottom.png")
	var week = ui.get("_week")
	week.show_synergies()
	await _save(out + "_3_synergies.png")
	week.close_overlay()
	week.show_report(str(state.my_next_opponent().get("code", "")))
	await _save(out + "_4_report.png")
	quit(0)
