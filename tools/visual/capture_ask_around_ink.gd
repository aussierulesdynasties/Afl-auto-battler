extends SceneTree
## Visual review tool for Ask around's answers in club ink (row 174) on the
## off-season Trade tab, on a phone (390x844), dark. Needs a real renderer:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_ask_around_ink.gd
## Environment: CAP_OUT (path prefix, default "ask_around_ink"; --out <folder> from capture.yml wins); writes
## <prefix>_head.png (the heading and the first answers) and <prefix>_more.png
## (further down the answers).
## The director's state (2026-11-12, "sanders uncoloured?"): an Essendon
## career with Ryley Sanders traded in from the Bulldogs, asked around about at
## the off-season, so his name sits in Essendon's red. Never touches a real save.

const W := 390
const H := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := OS.get_environment("CAP_OUT") if OS.get_environment("CAP_OUT") != "" else "ask_around_ink"
	var args := OS.get_cmdline_user_args()
	var at := args.find("--out")
	if at >= 0 and at + 1 < args.size():   # capture.yml: a folder
		DirAccess.make_dir_recursive_absolute(args[at + 1])
		out = args[at + 1].path_join("ask_around_ink")
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_ask_around_ink.save"
	state.settings_path = "user://capture_ask_around_ink.cfg"
	state.reset()
	state.career_seed = 5508
	state.replay_seed = 5508
	state.set_setting("seen_training_intro", true)
	state.set_setting("seen_offseason_intro", true)
	state.start_season("ESS", db.club_list("ESS"))
	var pid := ""
	for p in (state.season.lists["WBD"] as Array).duplicate():
		if db.player_display_name(p) == "Ryley Sanders":
			(state.season.lists["WBD"] as Array).erase(p)
			p["club"] = "ESS"
			(state.season.lists["ESS"] as Array).append(p)
			pid = str(p["id"])
	print("Sanders ", pid)
	state.season.round_index = state.season.fixture.size()
	state.open_offseason()
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
	off.set("_trade_side", "mine")
	off.set("_mine", [pid])
	off.set("_asked_id", pid)
	off.set("_asked", state.ask_around(pid))
	off.call("_build")
	await _shot(off, "AskHead", out + "_head.png")
	var answers: Array = off.find_children("Answer_*", "", true, false)
	var later := str(answers[mini(6, answers.size() - 1)].name) if not answers.is_empty() else "AskHead"
	await _shot(off, later, out + "_more.png")
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
