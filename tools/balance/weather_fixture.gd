extends SceneTree
## Where and when the game plays its matches, for fitting the weather cut-offs
## (tools/balance/weather_cutoffs.py). Measurement only.
##
##   godot --headless --path . --script tools/balance/weather_fixture.gd -- \
##       --seasons 20 --out runs/weather_fixture.jsonl
##
## One JSON line per match of each seeded 2026 season: {"ground", "month",
## "state"} exactly as Season.weather_for reads them (the Gather Round at its
## host ground). The finals (September) have no ladder here, so each of the
## nine is hosted at a club's ground picked from the season seed, the Grand
## Final at the MCG.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	var seasons := 20
	var out := "user://weather_fixture.jsonl"
	for i in range(a.size() - 1):
		match str(a[i]):
			"--seasons": seasons = int(a[i + 1])
			"--out": out = str(a[i + 1])
	var db = root.get_node("/root/GameDB")
	var codes: Array = db.active_clubs(2026).duplicate()
	var lists := {}
	for c in codes:
		lists[c] = []
	var season_script = load("res://scripts/sim/Season.gd")
	var fh := FileAccess.open(out, FileAccess.WRITE)
	if fh == null:
		push_error("weather_fixture: cannot write " + out)
		quit(1)
		return
	for s in range(seasons):
		var season = season_script.new(codes, lists, 9000 + s)
		var gather: int = season.gather_round()
		for r in range(season.fixture.size()):
			for m in season.fixture[r]:
				var home := str(m["home"])
				var ground: String = season.home_ground(home)
				var state := str(db.club(home).get("state", ""))
				if r == gather:
					ground = season.round_venue(r, home, str(m["away"]))
					state = "SA"
				fh.store_line(JSON.stringify({"ground": ground, "month": Weather.month_of_round(r),
						"state": state}))
		var rng := RandomNumberGenerator.new()
		rng.seed = 9000 + s
		for k in range(9):
			var host := str(codes[rng.randi() % codes.size()])
			var ground: String = "MCG" if k == 8 else season.home_ground(host)
			fh.store_line(JSON.stringify({"ground": ground, "month": 6,
					"state": "VIC" if k == 8 else str(db.club(host).get("state", ""))}))
	fh.close()
	quit(0)
