extends SceneTree
## The Grand Final week's freeze (the off-season trade market opens inside it).
## Plays a seeded career with GameState.advance() to the end of the season and
## times the Grand Final week; prints how often the market worked out a club's
## selection bars, and a fingerprint of everything the market decides.
##   godot --headless --path . --script tools/perf/gf_week.gd -- [--club GEE] [--seed 4242]
## Isolate the save folder with APPDATA. Nothing touches a real save.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var club := "GEE"
	var seed := 4242
	var a := OS.get_cmdline_user_args()
	for i in range(a.size() - 1):
		match str(a[i]):
			"--club": club = str(a[i + 1])
			"--seed": seed = int(a[i + 1])
	await process_frame
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	var tv = load("res://scripts/sim/TradeValue.gd")
	gs.replay_seed = seed
	gs.start_season(club, db.club_list(club))
	gs.autosave_enabled = false
	var weeks := 0
	while gs.offseason_year != gs.season_year and weeks < 60:
		var before: int = tv.bars_built
		var t := Time.get_ticks_usec()
		gs.advance()
		var ms := (Time.get_ticks_usec() - t) / 1000.0
		weeks += 1
		if gs.offseason_year == gs.season_year:
			print("PERF gf_week %.0f ms, bars_built %d" % [ms, tv.bars_built - before])
	var h := hash(var_to_str(gs.offseason_log)) ^ hash(var_to_str(gs.trade_offers))
	for code in gs.season.lists:
		for q in gs.season.lists[code]:
			h = hash([h, code, str(q["id"]), int(q.get("overall", 0)), var_to_str(q.get("contract", {}))])
	print("PERF fingerprint %d weeks %d" % [h, weeks])
	quit()
