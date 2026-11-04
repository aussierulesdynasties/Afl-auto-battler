extends SceneTree
## Visual review tool for the screen wipe (ScreenTransition). Windowed:
##   godot --windowed --path . --script tools/visual/capture_screen_wipe.gd -- --out <dir> --size 390x844
## Opens a Fremantle career on the hub, then changes to Season stats through
## Router.go() and saves every frame of the wipe as <dir>/f_000.png on, plus
## <dir>/after.png a second after it ends. Never touches a real save.

var _w := 1280
var _h := 720


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "wipe"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		match str(a[i]):
			"--out":
				out = str(a[i + 1])
			"--size":
				var wh := str(a[i + 1]).split("x")
				_w = int(wh[0])
				_h = int(wh[1])
	DirAccess.make_dir_recursive_absolute(out)
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	var wipe = root.get_node("ScreenTransition")
	state.autosave_enabled = false
	state.save_path = "user://capture_screen_wipe.save"
	state.settings_path = "user://capture_screen_wipe.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.show_real_names = false
	load("res://scripts/ui/UiKit.gd").apply_appearance("dark")
	root.size = Vector2i(_w, _h)
	DisplayServer.window_set_size(Vector2i(_w, _h))
	state.reset()
	state.replay_seed = 2027
	state.start_season("FRE", db.club_list("FRE"))
	state.tutorials = false    # no first-visit card over either screen
	router.stack = []
	router.go("hub")
	while bool(wipe.get("busy")):
		await process_frame
	await create_timer(1.5).timeout
	router.go("stats")
	var n := 0
	while bool(wipe.get("busy")) and n < 200:
		await process_frame
		root.get_texture().get_image().save_png("%s/f_%03d.png" % [out, n])
		n += 1
	for i in range(30):
		await process_frame
	await process_frame
	root.get_texture().get_image().save_png("%s/after.png" % out)
	print("frames: %d" % n)
	quit(0)
