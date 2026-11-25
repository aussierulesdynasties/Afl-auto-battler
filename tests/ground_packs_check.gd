extends SceneTree
## Run against an EXPORTED pack that leaves the ground models out and carries
## res://ground_packs.json (tools/check_ground_packs.sh does this):
##   godot --headless --main-pack game.pck --script <this file> -- <slug>
## The ground is not in the build; GroundPacks fetches its pack over HTTP, checks it,
## keeps it in user://grounds/ and loads it, and the ground then builds with its stadium.
## A second run finds the kept pack and needs no download.
## With "pitch" after the slug (a fresh user://): a 3D match at the ground first fails to
## fetch it (no server), the flat oval plays on and the line over it says so; a real tap on
## the line, with the server back, fetches the ground and the 3D picture starts.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var slug: String = OS.get_cmdline_user_args()[0]
	if OS.get_cmdline_user_args().size() > 1 and OS.get_cmdline_user_args()[1] == "pitch":
		await _pitch(slug)
		return
	var failures: Array[String] = []
	var gp: GDScript = load("res://scripts/ui/match/GroundPacks.gd")
	var gm: GDScript = load("res://scripts/ui/match/GroundModels.gd")
	var was_kept: bool = FileAccess.file_exists(gp.DIR + str(gp.entry(slug).get("file", "-")))
	if gp.entry(slug).is_empty():
		failures.append("the build lists no pack for %s" % slug)
	var ready_now: bool = gp.ready(slug)
	if not was_kept and ready_now:
		failures.append("%s was ready before its pack was fetched: the model is in the build" % slug)
	if not ready_now:
		var packs: Node = gp.new()
		root.add_child(packs)
		var seen := [0]
		packs.progress.connect(func(_s, done, _t): seen[0] = maxi(seen[0], done))
		packs.fetch(slug)
		var res: Array = await packs.finished
		print("Ground packs check: fetched %s, ok %s, %d bytes seen %s" % [slug, res[1], seen[0], res[2]])
		if not res[1]:
			failures.append("fetching %s failed: %s" % [slug, res[2]])
	else:
		print("Ground packs check: %s loaded from the kept pack, no download" % slug)
	if failures.is_empty():
		var g: Node3D = gm.instantiate(slug)
		var meshes := g.find_children("*", "MeshInstance3D", true, false).size()
		g.free()
		if meshes == 0:
			failures.append("%s built with no stadium meshes from its pack" % slug)
		else:
			print("Ground packs check: %s built with %d meshes" % [slug, meshes])
	# The pack never stands over the build's own files.
	if not ResourceLoader.exists("res://scripts/core/GameDB.gd"):
		failures.append("the game's own scripts went missing after the pack loaded")
	for f in failures:
		push_error("Ground packs check: " + f)
	print("Ground packs check: %d failures" % failures.size())
	quit(0 if failures.is_empty() else 1)


func _pitch(slug: String) -> void:
	var failures: Array[String] = []
	var gp: GDScript = load("res://scripts/ui/match/GroundPacks.gd")
	var gm: GDScript = load("res://scripts/ui/match/GroundModels.gd")
	var tap: GDScript = load(get_script().resource_path.get_base_dir().path_join("tap.gd"))
	var good := str(gp.manifest().get("url", ""))
	gp.manifest()["url"] = "http://127.0.0.1:9/grounds"
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	res["venue"] = gm.ground_name(slug)
	root.size = Vector2i(390, 844)
	var pv: Control = load("res://scripts/ui/PitchView.gd").new()
	pv.size = Vector2(390, 480)
	pv.three_d = true
	root.add_child(pv)
	pv.setup(res)
	if pv._oval3d != null:
		failures.append("the 3D picture started before %s was fetched" % slug)
	print("Ground packs check: %s" % pv.ground_fetch_text())
	for i in range(600):
		await process_frame
		if str(pv.ground_fetch.get("why", "")) != "":
			break
	var line: String = pv.ground_fetch_text()
	print("Ground packs check: %s" % line)
	if not line.ends_with("Tap here to try again."):
		failures.append("with no server, the line over the oval said: %s" % line)
	gp.manifest()["url"] = good
	var why: String = await tap.tap_at(pv, pv._fetch_rect.get_center())
	if why != "":
		failures.append("the tap on the line did not reach it: %s" % why)
	for i in range(3000):
		await process_frame
		if pv._oval3d != null or str(pv.ground_fetch.get("why", "")) != "":
			break
	if pv._oval3d == null:
		failures.append("after the tap the 3D picture did not start (%s)" % pv.ground_fetch_text())
	else:
		print("Ground packs check: after a tap on the line, %s came and the 3D match started with %d footballers" % [
				slug, pv._oval3d.players.size()])
	pv.queue_free()
	await process_frame
	for f in failures:
		push_error("Ground packs check: " + f)
	print("Ground packs check: %d failures" % failures.size())
	quit(0 if failures.is_empty() else 1)
