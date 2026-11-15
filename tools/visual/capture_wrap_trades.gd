extends SceneTree
## Visual review tool for the off-season wrap's Trade period (row 176): every
## club and player in his colours, on a phone (390x844), dark. Needs a real renderer:
##   godot --path . --rendering-method gl_compatibility --script tools/visual/capture_wrap_trades.gd
## Environment: CAP_OUT (path prefix, default "wrap_trades"; --out <folder> wins); writes
## <prefix>.png with the Trade period scrolled into view.
## A fresh Melbourne career at the off-season: the trade period the game itself
## ran, and the first offer to you turned down. Never touches a real save.

const W := 390
const H := 844


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := OS.get_environment("CAP_OUT") if OS.get_environment("CAP_OUT") != "" else "wrap_trades"
	var args := OS.get_cmdline_user_args()
	var at := args.find("--out")
	if at >= 0 and at + 1 < args.size():
		DirAccess.make_dir_recursive_absolute(args[at + 1])
		out = args[at + 1].path_join("wrap_trades")
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.event_sheets = false
	state.save_path = "user://capture_wrap_trades.save"
	state.settings_path = "user://capture_wrap_trades.cfg"
	state.reset()
	state.career_seed = 2026
	state.replay_seed = 2026
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.set_setting("seen_weekly_loop_intro", true)
	state.start_season("MEL", db.club_list("MEL"))
	state.season.round_index = state.season.fixture.size()
	state.open_offseason()
	# The game's own trade period (open_offseason ran it): rival deals that
	# both clubs accepted by their own valuations, and the first offer put to
	# you, turned down. Nothing is forced.
	var open: Array = state.open_trade_offers()
	if not open.is_empty():
		state.decline_trade_offer(int(open[0]))
	var lines := []
	for e in state.offseason_log:
		if str(e.get("kind", "")) in ["ai_trade", "offer_declined"]:
			lines.append(str(e.get("text", "")))
	print("%d trade lines" % lines.size())
	for l in lines:
		print("  ", l)
	state.season_wrap = {"year": state.season_year, "seen": false, "ins": [], "outs": [],
			"staff": [], "trades": lines, "goal": "", "reason": ""}
	UK.apply_appearance("dark")
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	var hub = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	for i in range(10):
		await process_frame
	var target: Control = hub.find_child("WrapTrade_0", true, false)
	var box: ScrollContainer = null
	var up: Node = target
	while up != null and box == null:
		up = up.get_parent()
		box = up as ScrollContainer
	print("trade line found %s, scroll box %s" % [target != null, box != null])
	if target != null and box != null:
		box.scroll_vertical = maxi(0, int(target.global_position.y - box.global_position.y) + box.scroll_vertical - 80)
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	if img.save_png(out + ".png") != OK:
		push_error("could not save " + out)
	print("wrote ", out, ".png")
	quit()
