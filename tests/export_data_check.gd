extends SceneTree
## Run against an EXPORTED pack, not the source tree (tools/check_export_data.sh
## does this): godot --headless --main-pack game.pck --script <this file>
## An exported build only contains a data CSV whose .import uses the "keep"
## importer. The game must find its player data there with real bio fields -
## never quietly load players without ages.
## The pack is exported with the Android preset's filters, so it also proves the
## phone build carries what Club Forge's Create a player draws (the 3D footballer,
## his moves and his hair), and a real tap on the button builds him there, and
## every ground's model the 3D match plays in (docs/ITCH_BUILDS.md, "What each
## build carries").

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
	_check_grounds(failures)
	for f in failures:
		push_error("Export data check: " + f)
	print("Export data check: %d players, %d failures" % [db.players.size(), failures.size()])
	quit(0 if failures.is_empty() else 1)


## Club Forge > Create a player in the exported pack: the files the 3D preview loads are
## there, and a real tap on the button opens the form with both figures built.
func _check_forge_player(failures: Array[String]) -> void:
	var oval: GDScript = load("res://scripts/ui/match/Oval3D.gd")
	for path in [oval.PLAYER_GLB, oval.LOOPS_GLB, oval.HAIR_GLB]:
		if not ResourceLoader.exists(path):
			failures.append("%s is missing from the exported pack (Club Forge's player preview loads it)" % path)
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
	var preview = scene.find_child("ForgePlayerPreview", true, false)
	if preview == null:
		failures.append("Create a player opened no player preview")
	elif preview.figures.size() != 2:
		failures.append("Create a player's preview built %d of its 2 figures" % preview.figures.size())
	else:
		print("Export data check: Create a player opened with both 3D figures")
	scene.queue_free()
	await process_frame


## Every ground the 3D match has a model for is in the pack, and one of them builds with its
## stadium and its seats: the phone build once shipped seats with no stadium under them.
func _check_grounds(failures: Array[String]) -> void:
	var gm: GDScript = load("res://scripts/ui/match/GroundModels.gd")
	var missing: Array[String] = []
	var slugs := {}
	for g in gm.grounds():
		slugs[gm.slug_for(g)] = true
	for slug: String in slugs:
		if gm.files(slug).is_empty():
			missing.append(slug)
	if not missing.is_empty():
		failures.append("%d grounds have no model in the exported pack: %s" % [missing.size(), ", ".join(missing)])
	var oval: GDScript = load("res://scripts/ui/match/Oval3D.gd")
	for path in [oval.PLAYER_GLB, "res://assets/oval3d/player_mh.glb", "res://assets/oval3d/crew_mh.glb"]:
		if not ResourceLoader.exists(path):
			failures.append("%s is missing from the exported pack (the 3D match draws it)" % path)
	var mcg: Node3D = gm.instantiate("mcg")
	var meshes := mcg.find_children("*", "MeshInstance3D", true, false).size()
	var seats := mcg.find_children("*", "MultiMeshInstance3D", true, false).size()
	mcg.free()
	if meshes == 0 or seats == 0:
		failures.append("the MCG built from the pack with %d stadium meshes and %d seat sets" % [meshes, seats])
	else:
		print("Export data check: %d grounds in the pack; the MCG built with %d meshes and %d seat sets" % [slugs.size(), meshes, seats])
