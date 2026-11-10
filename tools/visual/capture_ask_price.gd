extends SceneTree
## Visual review tool for Ask their price (row 67) on the off-season Trade
## tab, on a phone (390x844), dark. Needs a real renderer:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_ask_price.gd
## Environment: CAP_OUT (path prefix, default "ask_price"; --out <folder> from capture.yml wins); writes
## <prefix>_before.png (one of theirs on the sheet, the button showing) and
## <prefix>_after.png (after the button: their price filled in).
## A fresh Melbourne career at the off-season, trading with the Western
## Bulldogs for the best of theirs who has a price. Never touches a real save.

const W := 390
const H := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := OS.get_environment("CAP_OUT") if OS.get_environment("CAP_OUT") != "" else "ask_price"
	var args := OS.get_cmdline_user_args()
	var at := args.find("--out")
	if at >= 0 and at + 1 < args.size():   # capture.yml: a folder
		DirAccess.make_dir_recursive_absolute(args[at + 1])
		out = args[at + 1].path_join("ask_price")
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_ask_price.save"
	state.settings_path = "user://capture_ask_price.cfg"
	state.reset()
	state.career_seed = 2026
	state.replay_seed = 2026
	state.set_setting("seen_training_intro", true)
	state.set_setting("seen_offseason_intro", true)
	state.start_season("MEL", db.club_list("MEL"))
	state.season.round_index = state.season.fixture.size()
	state.open_offseason()
	var club := "WBD"
	var theirs: Array = (state.season.lists[club] as Array).duplicate()
	theirs.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
	var pid := ""
	for q in theirs:
		if bool(state.ask_price(club, str(q["id"]))["ok"]):
			pid = str(q["id"])
			break
	print("target ", pid)
	UK.apply_appearance("dark")
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	var off = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(off)
	off.set("_tab", "trade")
	off.set("_trade_club", club)
	off.set("_theirs", [pid])
	off.call("_build")
	await _shot(off, "AskPrice", out + "_before.png")
	(off.find_child("AskPrice", true, false) as Button).pressed.emit()
	await _shot(off, "TradePrice", out + "_after.png")
	quit()


## Scroll `name` into the middle of the screen and save the frame.
func _shot(off: Node, name: String, path: String) -> void:
	for i in range(8):
		await process_frame
	var target: Control = off.find_child(name, true, false)
	var box: ScrollContainer = null
	var up: Node = target
	while up != null and box == null:
		up = up.get_parent()
		box = up as ScrollContainer
	print("%s found %s, scroll box %s" % [name, target != null, box != null])
	if target != null and box != null:
		box.scroll_vertical = maxi(0, int(target.global_position.y - box.global_position.y) + box.scroll_vertical - 260)
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(path) != OK:
		push_error("could not save " + path)
	print("wrote ", path)
