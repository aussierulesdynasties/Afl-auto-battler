extends SceneTree
## Review capture for row 119 (Undo for a delisting, a free-agent signing and
## a re-signing), dark, 390x844, Geelong's first off-season:
##   godot --path . --script tools/visual/capture_recruit_undo.gd -- --out /tmp/undo
## Needs a real renderer and a window (keep it off screen with an override.cfg).
## Writes <out>_1_delisted.png (the notice and the Undo row after a delisting),
## <out>_2_undone.png (after Undo), <out>_3_signed_other_tab.png (a free-agent
## signing seen from another tab, the row naming it). Nothing touches a save.

const W := 390
const H := 844


func _initialize() -> void:
	_run.call_deferred()


func _shot() -> Image:
	for i in range(8):
		await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.convert(Image.FORMAT_RGBA8)
	return img


func _run() -> void:
	var out := "/tmp/undo"
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		if str(a[i]) == "--out":
			out = str(a[i + 1])
	await process_frame
	var state = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	var C = load("res://scripts/sim/Contracts.gd")
	state.autosave_enabled = false
	state.save_path = "user://capture_undo.save"
	state.settings_path = "user://capture_undo.cfg"
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
	# Room to let one go: Geelong's list sits at its 32 minimum.
	var base: Dictionary = state.my_list[state.my_list.size() - 1]
	for i in range(3):
		var extra: Dictionary = base.duplicate(true)
		extra["id"] = "undo_extra_%d" % i
		extra["contract_years"] = 2
		extra.erase("resigned")
		extra.erase("retiring")
		state.my_list.append(extra)
	var p: Dictionary = {}
	# Release sits on the out-of-contract rows: the weakest of them.
	for q in C.expiring(state.my_list):
		if not state.retiring_now(q) and not bool(q.get("resigned", false)) \
				and (p.is_empty() or int(q["overall"]) < int(p["overall"])):
			p = q
	var scene: Control = load("res://scenes/OffseasonScene.tscn").instantiate()
	root.add_child(scene)
	await _shot()
	# Through the screen's own buttons: Release on his row, then the confirm.
	var row: Node = scene.find_child("Contract_" + str(p["id"]), true, false)
	if row == null:
		push_error("No contract row for %s" % str(p["id"]))
		quit(1)
		return
	(row.find_child("Release", true, false) as Button).pressed.emit()
	await _shot()
	(scene.find_child("ConfirmRelease", true, false) as Button).pressed.emit()
	(await _shot()).save_png(out + "_1_delisted.png")
	(scene.find_child("UndoAction", true, false) as Button).pressed.emit()
	(await _shot()).save_png(out + "_2_undone.png")
	# A free agent signs; the coach then looks at the Trade tab.
	for fa in state.free_agents:
		if state.retiring_now(fa) or bool(state.free_agent_terms(str(fa["id"]))["refuse"]):
			continue
		var salary: int = maxi(int(C.lowest(fa, 2)), int(C.asking_salary(fa)))
		if salary > state.cap_room():
			continue
		fa.erase("offers")
		state.offer_free_agent(str(fa["id"]), salary, 2)
		break
	(scene.find_child("Tab_trade", true, false) as Button).pressed.emit()
	(await _shot()).save_png(out + "_3_signed_other_tab.png")
	quit(0)
