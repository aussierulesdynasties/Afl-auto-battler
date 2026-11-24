extends SceneTree
## Run against an EXPORTED pack, not the source tree (tools/check_export_data.sh
## does this): godot --headless --main-pack game.pck --script <this file>
## An exported build only contains a data CSV whose .import uses the "keep"
## importer. The game must find its player data there with real bio fields -
## never quietly load players without ages.
## The pack is exported with the Android preset's filters, so it also proves the
## phone build's Create a player and Settings work without the 3D art.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var db = root.get_node("GameDB")
	var failures: Array[String] = []
	var path: String = db.PLAYERS_ENRICHED_CSV
	if not FileAccess.file_exists(path):
		failures.append("%s is missing from the exported pack" % path)
	if not db.loaded or db.players.is_empty():
		failures.append("GameDB loaded no players from the exported pack")
	var no_age := 0
	var no_dob := 0
	for p in db.players:
		if float(p.get("age", 0.0)) <= 0.0:
			no_age += 1
		if str(p.get("dob", "")) == "":
			no_dob += 1
	if no_age > 0:
		failures.append("%d of %d players have no age" % [no_age, db.players.size()])
	if no_dob > 0:
		failures.append("%d of %d players have no date of birth" % [no_dob, db.players.size()])
	# The coaching world's Round 1 seed ships too.
	var coach_csv := "res://data/coaches_2026.csv"
	if not FileAccess.file_exists(coach_csv):
		failures.append("%s is missing from the exported pack" % coach_csv)
	elif (load("res://scripts/sim/Coaches.gd").seed("CAR") as Dictionary).size() < 100:
		failures.append("the coaching seed loaded too few coaches from the exported pack")
	await _check_forge_player(failures)
	for f in failures:
		push_error("Export data check: " + f)
	print("Export data check: %d players, %d failures" % [db.players.size(), failures.size()])
	quit(0 if failures.is_empty() else 1)


## Release 1.0.21 leaves the 3D art out: a real tap on Club Forge > Create a player
## opens the form with the player's name line and no 3D figure, and Settings offers
## no 3D oval or Graphics row.
func _check_forge_player(failures: Array[String]) -> void:
	# tests/ is not in the pack: the tap helper comes from beside this script.
	var tap: GDScript = load(get_script().resource_path.get_base_dir().path_join("tap.gd"))
	var state = root.get_node("GameState")
	state.autosave_enabled = false
	state.save_path = "user://export_check.save"
	state.settings_path = "user://export_check_settings.cfg"
	state.set_forge_player({})
	root.size = Vector2i(390, 844)
	var scene: Node = load("res://scenes/ClubForgeScene.tscn").instantiate()
	root.add_child(scene)
	for i in range(3):
		await process_frame
	var make := scene.find_child("ForgeCreatePlayer", true, false) as Control
	var why: String = await tap.tap(make) if make != null else "no Create a player button"
	for i in range(3):
		await process_frame
	if why != "":
		failures.append("a tap on Create a player did not reach it (%s)" % why)
	if scene.find_child("ForgePlayerPreview", true, false) != null:
		failures.append("Create a player built a 3D figure in a build without the 3D art")
	elif scene.find_child("ForgePlayerPreviewName", true, false) == null:
		failures.append("Create a player opened without the player's name line")
	else:
		print("Export data check: Create a player opened with the name line and no 3D figure")
	scene.queue_free()
	await process_frame
	await _check_settings(failures, tap)


func _check_settings(failures: Array[String], tap: GDScript) -> void:
	var host := Control.new()
	host.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	root.get_node("GameState").set_match_figures_on(false)
	var sheet: Control = load("res://scripts/ui/OptionsSheet.gd").open(host, false)
	for i in range(3):
		await process_frame
	if sheet.find_child("SettingsMatchFigures_3d", true, false) != null:
		failures.append("Settings still offers the 3D oval")
	if sheet.find_child("SettingsGraphics", true, false) != null:
		failures.append("Settings still offers the Graphics row")
	var fig := sheet.find_child("SettingsMatchFigures_figures", true, false) as Control
	if fig == null:
		failures.append("Settings has no Figures choice")
	else:
		for s in sheet.find_children("*", "ScrollContainer", true, false):
			(s as ScrollContainer).ensure_control_visible(fig)
		for i in range(3):
			await process_frame
		var why: String = await tap.tap(fig)
		for i in range(3):
			await process_frame
		if why != "":
			failures.append("a tap on Settings > Figures did not reach it (%s)" % why)
		elif not root.get_node("GameState").match_figures_on():
			failures.append("a tap on Settings > Figures did not turn figures on")
		else:
			print("Export data check: Settings has no 3D or Graphics row and Figures takes a tap")
	host.queue_free()
	await process_frame
