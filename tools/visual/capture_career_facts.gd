extends SceneTree
## Visual review tool for T5.r110 (the Career section of the player sheet:
## the facts on record from his career). Fremantle, seeded.
## Needs a real renderer (windowed, through C:/kt/gpu_slot.sh, off screen via override.cfg):
##   godot --path . --script tools/visual/capture_career_facts.gd -- --out /tmp/cf --size 390x844
## Writes <out>_veteran.png (a traded-in veteran with honours at two clubs,
## scrolled to Career), <out>_debutant.png (a player who debuted for you this
## season) and <out>_rookie.png (a draftee yet to play). Never touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


func _scroll_to(sheet: Control, node: Node) -> void:
	if node == null:
		return
	var p := node.get_parent()
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null:
		var sc := p as ScrollContainer
		sc.scroll_vertical = int((node as Control).global_position.y - sc.global_position.y) + sc.scroll_vertical - 60


func _open(host: Control, p: Dictionary, anchor: String, out: String) -> void:
	var sheet: Control = load("res://scripts/ui/PlayerSheet.gd").open(host, p)
	await _shot()
	var heads := sheet.find_children("*", "Label", true, false).filter(func(l): return (l as Label).text == "Career")
	_scroll_to(sheet, heads[0] if not heads.is_empty() else sheet.find_child(anchor, true, false))
	(await _shot()).save_png(out)
	print("CAPTURED ", out, " | ", " / ".join(PackedStringArray(sheet.find_children("CareerFact_*", "Label", true, false).map(func(l): return (l as Label).text))))
	sheet.queue_free()
	await process_frame


func _run() -> void:
	var out := "/tmp/cf"
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
	root.size = size
	DisplayServer.window_set_size(size)
	var y: int = state.season_year
	var host := Control.new()
	host.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	for p in state.my_list:
		for key in ["injury_weeks", "injury_kind", "suspension_weeks"]:
			p.erase(key)

	# A veteran: six seasons and a flag at Melbourne, then four with you.
	var vet: Dictionary = state.my_list.filter(func(q): return float(q.get("age", 0.0)) >= 29.0)[0]
	var vid := str(vet["id"])
	vet["career"] = {"games": 212, "goals": 96, "through": y - 1, "unknown": [],
			"stints": [["MEL", y - 10, y - 5, 140, 64], ["FRE", y - 4, y - 1, 72, 32]]}
	vet.erase("firsts")
	vet["honours"] = {"bf": {"MEL": 1, "FRE": 1}, "aa": 1, "captain": {"FRE": 2}, "brownlow": 1}
	state.honour_roll = [
		{"year": y - 6, "my_club": "", "premier": "MEL"},
		{"year": y - 3, "my_club": "FRE", "premier": "GEE", "brownlow": [{"id": vid, "club": "FRE"}]},
		{"year": y - 2, "my_club": "FRE", "premier": "BRL", "my_bf": [{"id": vid}], "my_aa": [vid]},
		{"year": y - 1, "my_club": "FRE", "premier": "FRE"},
	]
	state.milestone_log["log"] = [{"who": "player", "kind": "games", "value": 200, "id": vid,
			"year": y - 1, "label": "Round 12", "club": "FRE"}]
	state.season_tally[vid] = {"club": "FRE", "games": 0, "goals": 0}
	await _open(host, vet, "CareerFact_0", out + "_veteran.png")

	# A debutant: his first game for you this season, Round 3.
	var young: Array = state.my_list.filter(func(q): return str(q["id"]) != vid)
	young.sort_custom(func(x, z): return float(x.get("age", 30.0)) < float(z.get("age", 30.0)))
	# Neither has a senior season behind him: no last-season stat line either.
	for q in young.slice(0, 2):
		for key in ["gm", "di", "cl", "cp", "tk", "rb", "onepct", "mk", "gl", "mi", "ga", "ho", "br"]:
			q[key] = 0
	var deb: Dictionary = young[0]
	var did := str(deb["id"])
	deb["career"] = {"games": 0, "goals": 0, "through": y - 1, "unknown": [], "stints": []}
	deb["firsts"] = {"debut": {"year": y, "label": "Round 3"}}
	state.season_tally[did] = {"club": "FRE", "games": 1, "goals": 0}
	await _open(host, deb, "WithUsTitle", out + "_debutant.png")

	# A rookie yet to play a senior game.
	var rook: Dictionary = young[1]
	rook["career"] = {"games": 0, "goals": 0, "through": y - 1, "unknown": [], "stints": []}
	rook.erase("firsts")
	state.season_tally.erase(str(rook["id"]))
	await _open(host, rook, "CareerNone", out + "_rookie.png")
	quit(0)
