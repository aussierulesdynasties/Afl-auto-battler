extends SceneTree
## Dumps a dataset's players as the game rates them, for the era watch report
## (TODO row 142: each decade's stat averages and rating spread against 2026).
##   godot --headless --path . --script tools/legacy_1990s/dump_ratings.gd -- 1990 out.json
## Every listed player (rated or a list addition): club, name, position, age,
## OVR, POT, real peak and whether he played the data season.


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2:
		print("usage: -- <dataset> <out.json>")
		quit(1)
		return
	await process_frame
	var db = root.get_node("GameDB")
	db.reload(str(args[0]))
	var out := []
	for p in db.players + db.list_additions:
		out.append({"club": str(p["club"]), "name": str(p["real_name"]), "role": str(p.get("role", "")),
				"role2": str(p.get("role2", "")), "age": float(p.get("age", 0.0)), "ovr": int(p["overall"]),
				"pot": int(p.get("potential", 0)), "real_peak": int(p.get("real_peak", -1)),
				"gm": float(p.get("gm", 0.0)), "played": not db.list_additions.has(p),
				"stats_year": int(p.get("stats_year", 0)), "projected": bool(p.get("projected", false)),
				"rated_on_record": bool(p.get("rated_on_record", false))})
	var f := FileAccess.open(str(args[1]), FileAccess.WRITE)
	f.store_string(JSON.stringify({"dataset": str(args[0]), "data_season": int(db.DATA_SEASON), "players": out}))
	f.close()
	print("DUMPED %d players of %s" % [out.size(), str(args[0])])
	quit(0)
