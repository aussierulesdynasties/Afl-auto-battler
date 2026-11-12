extends SceneTree
## The tips added for row T3.R56, each over the screen it explains, from a
## fresh settings file (every tip unseen). Needs a real renderer:
##   godot --path . --windowed --script tools/visual/capture_tips.gd -- --out /tmp/tips [--club FRE] [--size 390x844]
## Writes <out>_league_draft.png, _contracts.png, _trade.png, _national_draft.png, _draft_trade.png.

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(10)
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	img.save_png(path)
	print("wrote ", path, " ", img.get_size())


## The tip named `tip` must be up over `host`, or the shot would show the wrong thing.
func _has(host: Node, tip: String) -> bool:
	var ok := host.find_child(tip, true, false) != null
	print("%s: %s" % [tip, "up" if ok else "MISSING"])
	return ok


func _run() -> void:
	var out := "/tmp/tips"
	var club := "FRE"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--club":
			club = str(a[i + 1])
		if str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture_tips.save"
	state.settings_path = "user://capture_tips_settings.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(state.settings_path))
	state.career_seed = 2031
	state.replay_seed = 2031
	state.reset()
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	var base: float = layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
	layout.ui_scale = 1.0 / maxf(1.0, base)
	layout._update_scale()
	await _frames(10)
	print("canvas ", root.get_visible_rect().size)
	var missing := 0

	# 1. The League redraft's tip, on the board once the club is chosen.
	state.begin_draft()
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(10)
	ui.call("_on_club_chosen", club)
	await _frames(20)
	missing += 0 if _has(ui, "LeagueDraftIntro") else 1
	await _shot(out + "_league_draft.png")
	ui.queue_free()
	await _frames(4)
	state.draft = null

	# 2-3. The first off-season: contract talks with an own player, then the Trade tab.
	state.reset()
	state.start_season(club, db.club_list(club))
	var sea = state.season
	while sea.round_index < sea.fixture.size():
		sea.play_round()
	sea.start_finals()
	while not bool(sea.finals["done"]):
		sea.play_finals_week()
	state.week_events = []
	state.open_offseason()
	var p: Dictionary = {}
	for q in state.my_list:
		if int(q.get("contract_years", 0)) <= 1 and not bool(q.get("retiring", false)):
			p = q
			break
	if p.is_empty():
		p = state.my_list[0]
		p["contract_years"] = 1
		for k in ["resigned", "talks", "retiring"]:
			p.erase(k)
	var off: Control = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(off)
	await _frames(20)
	off.call("handle_back")   # the off-season's own tip, seen in an earlier row
	await _frames(6)
	off.call("_open_talks", str(p["id"]))
	await _frames(20)
	missing += 0 if _has(off, "ContractsIntro") else 1
	await _shot(out + "_contracts.png")
	off.call("handle_back")
	await _frames(4)
	off.call("_close_talks")
	await _frames(4)
	(off.find_child("Tab_trade", true, false) as Button).pressed.emit()
	await _frames(20)
	missing += 0 if _has(off, "TradeIntro") else 1
	await _shot(out + "_trade.png")
	off.queue_free()
	await _frames(4)

	# 4-5. The National Draft: its tip after the recruiting panel, then pick trading.
	if not state.begin_intake_draft():
		print("MISSING: the National Draft did not open")
		quit(1)
		return
	ui = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(20)
	var meet: Button = ui.find_child("MeetingDone", true, false)
	if meet != null:
		meet.pressed.emit()
	await _frames(20)
	missing += 0 if _has(ui, "DraftIntro") else 1
	await _shot(out + "_national_draft.png")
	ui.call("handle_back")
	await _frames(4)
	var d = state.draft
	var guard := 0
	while not d.is_user_turn() and not d.is_finished() and guard < 200:
		guard += 1
		d.auto_until_user_turn()
	ui.call("_refresh")
	await _frames(10)
	(ui.find_child("TradePicks", true, false) as Button).pressed.emit()
	await _frames(20)
	missing += 0 if _has(ui, "DraftTradeIntro") else 1
	await _shot(out + "_draft_trade.png")
	quit(0 if missing == 0 else 1)
