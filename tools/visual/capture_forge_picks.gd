extends SceneTree
## The Forge draft fix, for the director's look (2026-11-25): a Forge club
## (Darwin) signs free agents in the opening off-season until a pick will
## pass, then three screens:
##   <prefix>_brief.png  the off-season brief naming the picks that will pass
##   <prefix>_offer.png  a free agent's offer sheet naming the pick he costs
##   <prefix>_log.png    the draft's Picks log after the draft, passes as rows
## Never touches a real save.
##   godot --path . --script tools/visual/capture_forge_picks.gd -- --out PREFIX [--size 390x844]
const Ovr := preload("res://tests/ovr.gd")

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _shot(path: String) -> void:
	await _frames(20)
	root.get_viewport().get_texture().get_image().save_png(path)
	print("wrote ", path)


func _run() -> void:
	var out := "forge_picks"
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
	gs.save_path = "user://capture_forge_picks.save"
	gs.settings_path = "user://capture_forge_picks.cfg"
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(W, H))
	await _frames(10)
	var layout = root.get_node("ScreenLayout")
	layout.ui_scale = 1.0 / maxf(1.0, layout.desktop_density(Vector2(root.size), DisplayServer.screen_get_scale(),
			DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0))
	layout._update_scale()
	await _frames(10)
	gs.reset("2026")
	gs.create_club({"name": "Darwin", "short": "Darwin", "code": "DAR",
			"location": "darwin", "primary": "#F2B705", "secondary": "#7A1F2B",
			"accent": "#FFFFFF", "design": "sash", "kit": "p/s/a"})
	gs.interview_due = false
	gs.tutorials = false  # first-visit tips would cover the screens
	gs.begin_real_lists()
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(ui)
	await _frames(20)
	ui.call("_on_club_chosen", "DAR")
	await _frames(20)
	# Sign until a pick will pass, then one more so the sheet says "too".
	var signed := 0
	for p in gs.free_agents.duplicate():
		if not (gs.draft_list_spots()["passing"] as Array).is_empty():
			break
		var r: Dictionary = gs.sign_free_agent(str(p["id"]), 1)
		for k in 8:
			if str(r.get("answer", "")) == "counter":
				r = gs.offer_free_agent(str(p["id"]), int(r["salary"]), 1)
			elif str(r.get("answer", "")) == "table":
				r = gs.offer_free_agent(str(p["id"]), int(r["salary"]) + 20000, 1)
			else:
				break
		if str(r.get("answer", "")) == "signed":
			signed += 1
	print("signed %d: %s" % [signed, gs.draft_spots_line()])
	ui.visible = false
	var off: Control = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(off)
	await _shot(out + "_brief.png")
	var fa_id := ""
	for p in gs.free_agents:
		if int(Ovr.of(p, 0)) >= 60:
			fa_id = str(p["id"])
			break
	if fa_id == "" and not gs.free_agents.is_empty():
		fa_id = str(gs.free_agents[0]["id"])
	off.call("_open_talks", fa_id, true)
	await _frames(10)
	var cost := off.find_child("FaPickCost", true, false) as Control
	var sc: ScrollContainer = null
	var p2 := cost.get_parent() if cost != null else null
	while p2 != null:
		if p2 is ScrollContainer:
			sc = p2
			break
		p2 = p2.get_parent()
	if sc != null:
		sc.ensure_control_visible(cost)
	print("offer line: ", (cost as Label).text if cost != null else "none")
	await _shot(out + "_offer.png")
	off.queue_free()
	ui.visible = true
	ui.call("_end_first_offseason")
	await _frames(20)
	var done := ui.find_child("MeetingDone", true, false) as Button
	if done != null:
		done.emit_signal("pressed")
	await _frames(10)
	var d = gs.draft
	var guard := 0
	while not d.is_finished() and guard < 200:
		guard += 1
		if d.is_user_turn():
			var chosen := {}
			for q in d.pool:
				if d.can_pick_player(q):
					chosen = q
					break
			if chosen.is_empty():
				break
			d.pick(chosen)
		d.auto_until_user_turn()
	ui.call("_finish_replay")
	ui.call("_refresh")
	await _frames(10)
	var tab := ui.find_child("SideTab_picks" if ui.get("_wide") else "Tab_picks", true, false) as Button
	if tab != null:
		tab.emit_signal("pressed")
	await _frames(20)
	# Scroll the log so Darwin's own pass is in view.
	var mine := ""
	for e in d.user_passed:
		mine = "HistoryPass_%d" % int(e["pick"])
	var row := ui.find_child(mine, true, false) as Control if mine != "" else null
	var p3 := row.get_parent() if row != null else null
	while p3 != null:
		if p3 is ScrollContainer:
			(p3 as ScrollContainer).ensure_control_visible(row)
			break
		p3 = p3.get_parent()
	print("tab: %s  passes: %d  my row: %s" % [tab.text if tab != null else "-", d.passed_picks.size(), mine if row != null else "missing"])
	await _shot(out + "_log.png")
	quit()
