extends SceneTree
## Every start's real players as a new career opens them: overall, potential
## and what set them. One CSV per start, for checking ratings against the real
## record (tools/ratings_check.py).
##   godot --headless --path . --script tools/ratings_dump.gd -- <out dir> [start ...]
const Ovr := preload("res://tests/ovr.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var gs = root.get_node("GameState")
	gs.autosave_enabled = false
	gs.save_path = "user://dump_career.save"
	gs.settings_path = "user://dump_settings.cfg"
	var args := OS.get_cmdline_user_args()
	var out_dir := str(args[0]) if args.size() > 0 else "user://"
	var starts: Array = Array(args.slice(1)) if args.size() > 1 else ["1990", "2000", "2010", "2020", "2026"]
	for ds in starts:
		gs.reset(str(ds))
		gs.replay_seed = 1
		gs.career_seed = 1
		gs.begin_real_lists()
		var db = root.get_node("GameDB")
		var f := FileAccess.open("%s/ratings_%s.csv" % [out_dir, ds], FileAccess.WRITE)
		f.store_line("kind,club,first,last,age,role,overall,potential,season_overall,honours,real_peak,on_record,on_honours,on_rehab,gm,draft_rank,draft_year")
		var rows: Array = []
		for p in db.players:
			rows.append(["list", p])
		for p in db.list_additions:
			rows.append(["addition", p])
		for p in db.draftees:
			rows.append(["draftee", p])
		for r in rows:
			var p: Dictionary = r[1]
			f.store_line(",".join(PackedStringArray([r[0], str(p.get("club", "")), str(p.get("first", "")).replace(",", " "),
					str(p.get("last", "")).replace(",", " "), str(p.get("age", "")), str(p.get("role", "")),
					str(Ovr.of(p, "")), str(p.get("potential", "")), str(p.get("season_overall", "")),
					str(p.get("honours", "")), str(p.get("real_peak", "")), str(p.get("rated_on_record", false)),
					str(p.get("rated_on_honours", false)), str(p.get("rated_on_rehab", false)), str(p.get("gm", "")), str(p.get("draft_rank", "")),
					str(p.get("draft_year", ""))])))
		f.close()
		print("dumped %s: %d" % [ds, rows.size()])
	quit(0)
