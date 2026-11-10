extends SceneTree
## Review capture for row T1.R26 (free-agent talks: what each offer is worth
## to him, what he counts besides salary, and your offer's Gain / Cost), dark,
## Geelong's first off-season:
##   godot --path . --script tools/visual/capture_fa_weights.gd -- --out /tmp/fa --size 390x844
## Needs a real renderer and a window (keep it off screen with an override.cfg).
## Writes <out>_talks_top.png and <out>_talks_end.png (the sheet scrolled to its
## foot). Prints FA_WEIGHTS lines with the rows shown. Nothing touches a save.

var W := 390
var H := 844


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


func _run() -> void:
	var out := "/tmp/fa"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
		elif str(a[i]) == "--size":
			var wh := str(a[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_fa_weights.save"
	state.settings_path = "user://capture_fa_weights.cfg"
	state.reset()
	state.career_seed = 2027
	state.replay_seed = 2027
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		state.set_setting("seen_%s_intro" % key, true)
	state.start_season("GEE", db.club_list("GEE"))
	UK.apply_appearance("dark")
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	state.season.round_index = state.season.fixture.size()
	state.ensure_finals()
	while not state.season.is_season_over():
		state.advance()
	state.open_offseason()
	# The free agent with the most rival offers on the table.
	var pick := ""
	var most := 0
	for fa in state.free_agents:
		if state.retiring_now(fa) or bool(state.free_agent_terms(str(fa["id"]))["refuse"]):
			continue
		var n: int = state.fa_offers(str(fa["id"])).size()
		if n > most:
			most = n
			pick = str(fa["id"])
	if pick == "":
		push_error("No free agent with a rival offer")
		quit(1)
		return
	for row in state.fa_offers(pick):
		print("FA_WEIGHTS offer %s %d x %d worth %d" % [row["name"], row["salary"], row["years"], row["worth"]])
	var scene: Control = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(scene)
	await _shot()
	root.gui_disable_input = true
	scene._open_talks(pick, true)
	(await _shot()).save_png(out + "_talks_top.png")
	for node in [scene.find_child("FaGain", true, false), scene.find_child("FaCost", true, false),
			scene.find_child("FaWeights", true, false)]:
		print("FA_WEIGHTS node %s" % (str(node.name) if node != null else "MISSING"))
	var scroll := scene.find_child("ContractTalks", true, false).find_children("*", "ScrollContainer", true, false)
	for s in scroll:
		(s as ScrollContainer).scroll_vertical = 100000
	(await _shot()).save_png(out + "_talks_end.png")
	quit(0)
