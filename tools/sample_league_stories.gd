extends SceneTree
## godot --headless --path . --script tools/sample_league_stories.gd -- [club] [seed] [rounds]
## Plays a seeded career's first rounds and prints each round's league stories
## (LeagueStories.gd), for reading the copy. Reads only; writes no save.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var club := args[0] if args.size() > 0 else "FRE"
	var seed := int(args[1]) if args.size() > 1 else 2027
	var rounds := int(args[2]) if args.size() > 2 else 6
	var nf = load("res://scripts/ui/NewsFront.gd")
	var gs = root.get_node("GameState")
	var db = root.get_node("GameDB")
	gs.autosave_enabled = false
	gs.save_path = "user://sample_league_stories.save"
	gs.settings_path = "user://sample_league_stories.cfg"
	gs.replay_seed = seed
	gs.reset()
	gs.career_seed = seed
	gs.replay_seed = seed
	gs.start_season(club, db.club_list(club))
	gs.tutorials = false
	gs.event_sheets = false
	for r in range(rounds):
		gs.advance()
		var items: Array = nf.latest_round(gs.news)
		print("=== %s ===" % (items[0]["when"] if not items.is_empty() else "?"))
		for it in items:
			if str(it.get("kind", "")) == "league_story":
				print("[%s w%d %s] %s" % [it["angle"], int(it["weight"]), it["club"], it["headline"]])
				for b in it["beats"]:
					print("    " + str(b))
	quit(0)
