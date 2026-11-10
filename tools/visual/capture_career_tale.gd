extends SceneTree
## Visual review of a player's career story (CareerTale; director 2026-11-10):
## the player sheet and Brownlow night. Fremantle, seeded.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen via override.cfg):
##   godot --path . --script tools/visual/capture_career_tale.gd -- --out /tmp/ct --size 390x844
## Writes <out>_payoff.png (our late pick who won the Brownlow, scrolled to Career),
## <out>_fellshort.png (our early pick who left for St Kilda), <out>_thin.png (a
## rookie with no story yet: the section as it was) and <out>_brownlow.png (the
## Brownlow winner revealed on awards night). Never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


func _scroll_to(node: Node) -> void:
	if node == null:
		return
	var p := node.get_parent()
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null:
		var sc := p as ScrollContainer
		sc.scroll_vertical = int((node as Control).global_position.y - sc.global_position.y) + sc.scroll_vertical - 60


func _open(host: Control, p: Dictionary, out: String) -> void:
	var sheet: Control = load("res://scripts/ui/PlayerSheet.gd").open(host, p)
	await _shot()
	var heads := sheet.find_children("*", "Label", true, false).filter(func(l): return (l as Label).text == "Career")
	_scroll_to(heads[0] if not heads.is_empty() else sheet.find_child("CareerNone", true, false))
	(await _shot()).save_png(out)
	var story: Label = sheet.find_child("CareerStory", true, false)
	print("CAPTURED ", out, " | ", story.text if story != null else "(no story)")
	sheet.queue_free()
	await process_frame


func _seasons(state, from: int, to: int) -> void:
	for y in range(from, to + 1):
		state.honour_roll.append({"year": y, "my_club": "FRE", "premier": "GEE"})


func _run() -> void:
	var out := "/tmp/ct"
	var size := Vector2i(390, 844)
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--size":
			size = Vector2i(int(str(a[i + 1]).get_slice("x", 0)), int(str(a[i + 1]).get_slice("x", 1)))
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	state.autosave_enabled = false
	state.save_path = "user://capture.save"
	state.settings_path = "user://capture_settings.cfg"
	state.career_seed = 7737
	state.replay_seed = 7737
	state.reset()
	state.start_season("FRE", db.club_list("FRE"))
	state.tutorials = false
	root.size = size
	DisplayServer.window_set_size(size)
	var y: int = state.season_year
	var host := Control.new()
	host.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	for p in state.my_list:
		for key in ["injury_weeks", "injury_kind", "suspension_weeks"]:
			p.erase(key)
	# We have coached Fremantle for five seasons; Geelong won four flags, we won one.
	_seasons(state, y - 5, y - 1)
	state.honour_roll[3]["premier"] = "FRE"

	# The payoff: pick 38, a debut, a flag, his 100th, then the Brownlow.
	var mids: Array = state.my_list.filter(func(q): return float(q.get("age", 0.0)) >= 24.0 and float(q.get("age", 0.0)) <= 27.0)
	var star: Dictionary = mids[0]
	var sid := str(star["id"])
	star.merge({"drafted_year": y - 6, "drafted_type": "national", "drafted_pick": 38, "drafted_club": "FRE"}, true)
	star["career"] = {"games": 104, "goals": 61, "through": y - 1, "unknown": [], "stints": [["FRE", y - 5, y - 1, 104, 61]]}
	star["firsts"] = {"debut": {"year": y - 5, "label": "Round 3"}}
	state.honour_roll[4]["brownlow"] = [{"id": sid, "votes": 31, "club": "FRE"}]
	state.milestone_log["log"] = [{"who": "player", "kind": "games", "value": 100, "id": sid,
			"year": y - 1, "label": "Round 19", "club": "FRE"}]
	await _open(host, star, out + "_payoff.png")

	# Fell short: pick 6, a promise broken, 14 games, now at St Kilda.
	var saint: Dictionary = (state.season.lists["STK"] as Array).filter(func(q): return float(q.get("age", 0.0)) <= 24.0)[0]
	saint.merge({"drafted_year": y - 5, "drafted_type": "national", "drafted_pick": 6, "drafted_club": "FRE"}, true)
	saint["career"] = {"games": 22, "goals": 5, "through": y - 1, "unknown": [],
			"stints": [["FRE", y - 4, y - 2, 14, 4], ["STK", y - 1, y - 1, 8, 1]]}
	saint["backed"] = [{"year": y - 4, "round": 6, "games": 3, "played": 1, "state": "broken"}]
	saint.erase("firsts")
	await _open(host, saint, out + "_fellshort.png")

	# Thin: last year's rookie pick, one game. No story; the section as it was.
	var young: Array = state.my_list.filter(func(q): return str(q["id"]) != sid)
	young.sort_custom(func(x, z): return float(x.get("age", 30.0)) < float(z.get("age", 30.0)))
	var rook: Dictionary = young[0]
	rook.merge({"drafted_year": y - 1, "drafted_type": "rookie", "drafted_club": "FRE"}, true)
	rook.erase("drafted_pick")
	rook["career"] = {"games": 1, "goals": 0, "through": y - 1, "unknown": [], "stints": [["FRE", y - 1, y - 1, 1, 0]]}
	rook["firsts"] = {"debut": {"year": y - 1, "label": "Round 22"}}
	await _open(host, rook, out + "_thin.png")

	# Brownlow night: the winner revealed, his story under his votes.
	var row := {"id": sid, "club": "FRE", "votes": 31, "slot": "MID"}
	state.season_awards = {"year": y - 1, "brownlow": [row, {"id": str(mids[1]["id"]), "club": "FRE", "votes": 24, "slot": "MID"}]}
	var ceremony: Control = load("res://scripts/ui/SeasonAwards.gd").open(host)
	await _shot()
	ceremony.find_child("AwardsNext", true, false).emit_signal("pressed")
	for i in range(120):          # the walk-on plays and settles
		await process_frame
	(await _shot()).save_png(out + "_brownlow.png")
	var ws: Label = ceremony.find_child("WinnerStory", true, false)
	print("CAPTURED ", out + "_brownlow.png | ", ws.text if ws != null else "(no story)")
	quit(0)
