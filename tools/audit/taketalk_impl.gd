extends RefCounted
## How often a learning-a-position project takes, by how far off he is early on
## (row T5.r93, the development talk's odds: "Players this far off at this
## stage get there about N in 10 times"). Measurement only.
## Per seed, a League Draft drafted as an AI club would, then seasons in which
## you keep both project places busy (as passmargin_impl); rival clubs run
## theirs as the game does (_ai_projects). Every club's project counts: at the
## end of each of its weeks 1 to 4 the gap (own rating minus his rating there)
## is kept, and paired with the verdict when it comes.
## Args after the impl name: seeds (comma-separated) club seasons
## Prints a ROW line per (week, gap) and a TOTAL line.

const PassMargin := preload("res://tools/audit/passmargin_impl.gd")

var club := "MEL"
# "id|year" -> {week: gap}
var open := {}
# [week, gap, learned]
var rows := []


func _all_players() -> Array:
	var out := []
	var seen := {}
	for c in GameState.season.lists:
		var list: Array = GameState.my_list if str(c) == GameState.my_club else GameState.season.lists[c]
		for p in list:
			if not seen.has(str(p["id"])):
				seen[str(p["id"])] = true
				out.append(p)
	return out


func _watch() -> void:
	for p in _all_players():
		var key := "%s|%d" % [str(p["id"]), GameState.season_year]
		var job := GameState.project_job(p)
		if job != "":
			var w := int((p["project"] as Dictionary).get("weeks", 0))
			if w >= 1 and w <= 4:
				var gaps: Dictionary = open.get(key, {})
				if not gaps.has(w):
					gaps[w] = int(p.get("overall", 0)) - GameState.rating_as(p, GameState.project_role(p))
				open[key] = gaps
	# Judged: the career fact for this year is there and the project is gone.
	for key in open.keys():
		var id := str(key).get_slice("|", 0)
		var year := int(str(key).get_slice("|", 1))
		var facts := CareerFacts.of(GameState.career_facts, id, "project")
		for f in facts:
			if int(f["y"]) == year and str(f["out"]) in ["learned", "not taken"]:
				var learned := str(f["out"]) == "learned"
				var gaps: Dictionary = open[key]
				for w in gaps:
					rows.append([int(w), int(gaps[w]), learned])
				open.erase(key)
				break


func _career(seed: int, seasons: int) -> void:
	var pm = PassMargin.new()
	pm.club = club
	GameState.reset()
	GameState.autosave_enabled = false
	GameState.replay_seed = seed
	var pool: Array = GameDB.all_players_sorted() + GameDB.all_draftees_sorted()
	pool.sort_custom(func(a, b): return a["overall"] > b["overall"])
	GameState.draft = Draft.new(pool, GameDB.active_clubs(GameState.season_year).duplicate(), seed)
	GameState.draft.start_for_user(club)
	pm._run_draft(GameState.draft)
	GameState.start_season(club, GameState.draft.list())
	for s in range(seasons):
		open = {}
		pm._fill_projects()
		while not GameState.season.is_season_over():
			GameState.advance()
			_watch()
			pm._fill_projects()
		_watch()
		if s == seasons - 1:
			break
		GameState.open_offseason()
		_watch()
		if GameState.begin_intake_draft():
			pm._run_draft(GameState.draft)
			GameState.finish_intake_draft()
		else:
			GameState.start_next_season()


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seeds := (str(args[1]) if args.size() > 1 else "301").split(",")
	club = str(args[2]) if args.size() > 2 else "MEL"
	var seasons := int(args[3]) if args.size() > 3 else 3
	for s in seeds:
		_career(int(s), seasons)
		print("SEED %s rows so far %d" % [s, rows.size()])
	var t := {}
	for r in rows:
		var k := "%d|%d" % [int(r[0]), int(r[1])]
		var c: Array = t.get(k, [0, 0])
		c[1] += 1
		if bool(r[2]):
			c[0] += 1
		t[k] = c
	var keys := t.keys()
	keys.sort_custom(func(a, b):
		var aw := int(str(a).get_slice("|", 0))
		var bw := int(str(b).get_slice("|", 0))
		if aw != bw:
			return aw < bw
		return int(str(a).get_slice("|", 1)) < int(str(b).get_slice("|", 1)))
	for k in keys:
		var c: Array = t[k]
		print("ROW week %s gap %s | learned %d of %d (%.0f%%)" % [str(k).get_slice("|", 0), str(k).get_slice("|", 1),
				c[0], c[1], 100.0 * float(c[0]) / float(maxi(1, c[1]))])
	print("TOTAL seeds %s seasons %d margin %d rows %d" % [",".join(seeds), seasons, GameState.PROJECT_PASS, rows.size()])
