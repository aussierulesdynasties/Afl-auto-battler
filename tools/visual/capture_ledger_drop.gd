extends SceneTree
## Row T5.r110 (People remembered): the selection drop's remembered line and
## Season stats > Coach, filled and empty. Staged career data on real players
## (the same shape the tests use). Needs a real renderer:
##   godot --path . --windowed --script tools/visual/capture_ledger_drop.gd -- --out /tmp/rem [--size 390x844]
## Writes <out>_drop.png, _coach.png, _coach_empty.png.

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


## Router.go plays the transition cover in a windowed run: wait for the new
## scene to be current and the cover to clear before touching it.
func _go(router: Node, key: String) -> Node:
	var path := str(router.SCENES.get(key, key))
	var old := current_scene
	router.go(key)
	for i in range(600):
		await process_frame
		if current_scene != null and current_scene != old and current_scene.scene_file_path == path:
			break
	await _frames(60)
	print("route ", key, ": ", current_scene.scene_file_path if current_scene != null else "none")
	return current_scene


## reset() forgets the first-visit cards: mark them seen again.
func _seen(gs: Node) -> void:
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		gs.set_setting("seen_%s_intro" % key, true)


func _has(host: Node, what: String) -> bool:
	var ok := host.find_child(what, true, false) != null
	print("%s: %s" % [what, "up" if ok else "MISSING"])
	return ok


func _run() -> void:
	var out := "/tmp/rem"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		if str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var router = root.get_node("Router")
	gs.autosave_enabled = false
	gs.event_sheets = false
	gs.save_path = "user://capture_ledger_drop.save"
	gs.settings_path = "user://capture_ledger_drop_settings.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		gs.set_setting("seen_%s_intro" % key, true)
	gs.career_seed = 2031
	gs.replay_seed = 2031
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

	# 1. The selection drop: a premiership player left out.
	gs.reset()
	_seen(gs)
	gs.start_season("FRE", db.club_list("FRE"))
	var year: int = gs.season_year
	var side: Dictionary = gs.current_side()
	var star_id := str(side["FWD"][0])
	var star: Dictionary = gs.list_player(star_id)
	star["career"] = {"games": 48, "goals": 61, "through": year - 1, "unknown": [],
			"stints": [["FRE", year - 3, year - 1, 48, 61]]}
	star.erase("firsts")
	gs.career_facts.erase(star_id)
	gs.honour_roll = [{"year": year - 2, "my_club": "FRE", "premier": "FRE", "my_bf": []}]
	var ui: Node = await _go(router, "selection")
	var in_id := ""
	for c in ui.find_child("NotSelected", true, false).get_children():
		if c is Button and load("res://scripts/sim/Ratings.gd").available(gs.list_player(str(c.get_meta("id")))):
			in_id = str(c.get_meta("id"))
			break
	var builder = ui.find_child("TeamBuilder", true, false)
	builder.call("_tap", star_id, "")
	await _frames(4)
	builder.call("_tap", in_id, "")
	await _frames(20)
	_has(current_scene, "BuilderRemembered")
	await _shot(out + "_drop.png")

	# 2. Season stats > Coach, empty: a first season.
	gs.reset()
	_seen(gs)
	gs.start_season("MEL", db.club_list("MEL"))
	await _go(router, "stats")
	current_scene.find_child("Section_coach", true, false).emit_signal("pressed")
	await _frames(20)
	_has(current_scene, "DrafteesEmpty")
	await _shot(out + "_coach_empty.png")

	# 3. Filled: three seasons in.
	gs.reset()
	_seen(gs)
	gs.start_season("MEL", db.club_list("MEL"))
	year = gs.season_year
	gs.my_first_season = year - 3
	var young: Array = gs.my_list.filter(func(q): return float(q.get("age", 30.0)) < 24.0)
	var a1: Dictionary = young[0]
	var a2: Dictionary = young[1]
	for pair in [[a1, year - 3, 7], [a2, year - 2, 31]]:
		var p: Dictionary = pair[0]
		p["drafted_club"] = "MEL"
		p["drafted_year"] = pair[1]
		p["drafted_pick"] = pair[2]
		p["drafted_type"] = "national"
	var id1 := str(a1["id"])
	var id2 := str(a2["id"])
	gs.honour_roll = [
		{"year": year - 3, "my_club": "MEL", "premier": "", "my_bf": [], "my_aa": [], "my_record": "12-11-0"},
		{"year": year - 2, "my_club": "MEL", "premier": "", "my_bf": [], "my_aa": [id1],
				"my_record": "14-9-0", "my_finals": "EF1"},
		{"year": year - 1, "my_club": "MEL", "premier": "MEL", "my_bf": [{"id": id1}], "my_aa": [id1, id2],
				"my_record": "17-6-0", "my_finals": "GF",
				"my_drafted": {id1: [year - 3, 7, "national"], id2: [year - 2, 31, "national"]}},
	]
	gs.board["history"] = [
		{"year": year - 3, "goal": "Make the finals", "met": false, "position": 11, "verdict": "The board is losing patience."},
		{"year": year - 2, "goal": "Make the finals", "met": true, "position": 6, "verdict": "The board is delighted."},
		{"year": year - 1, "goal": "Finish in the top four", "met": true, "position": 1, "verdict": "The board is delighted."},
	]
	await _go(router, "stats")
	current_scene.find_child("Section_coach", true, false).emit_signal("pressed")
	await _frames(20)
	_has(current_scene, "Draftees")
	_has(current_scene, "Verdicts")
	await _shot(out + "_coach.png")
	quit(0)
