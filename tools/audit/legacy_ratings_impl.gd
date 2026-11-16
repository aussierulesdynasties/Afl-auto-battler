extends RefCounted
## Every Legacy start's real players as the game rates them (director
## 2026-11-15: "audit every legacy player to make sure theyre rated properly
## and in the right positions"). For each past start (1990, 2000, 2010, 2020,
## or the ones named), one parseable line per player:
##   ROW start|id|club|name|age|role|role2|overall|potential|real_peak|gm|gl|season_overall|flags
## flags: R rated on record, H lifted by honours, O hand-set override.
## tools/audit/legacy_ratings_report.py joins these to honours and listed positions.
## Reads; changes nothing. Args: starts (default 1990 2000 2010 2020).


func run() -> void:
	var args := OS.get_cmdline_user_args().slice(1)
	var starts: Array = args if not args.is_empty() else ["1990", "2000", "2010", "2020"]
	for s in starts:
		GameDB.reload(str(s))
		for p in GameDB.players:
			var flags := ""
			if bool(p.get("rated_on_record", false)):
				flags += "R"
			if bool(p.get("rated_on_honours", false)):
				flags += "H"
			if bool(p.get("ovr_override", false)):
				flags += "O"
			print("ROW %s|%s|%s|%s|%d|%s|%s|%d|%d|%d|%d|%d|%d|%s" % [str(s), str(p.get("id", "")),
					str(p.get("club", "")), str(p.get("real_name", p.get("name", ""))),
					int(p.get("age", 0)), str(p.get("role", "")), str(p.get("role2", "")),
					int(p.get("overall", 0)), int(p.get("potential", 0)), int(p.get("real_peak", 0)),
					int(p.get("gm", 0)), int(p.get("gl", 0)), int(p.get("season_overall", p.get("overall", 0))),
					flags])
	GameDB.reload(Datasets.DEFAULT)
