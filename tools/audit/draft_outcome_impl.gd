extends RefCounted
## Draft outcome audit (director question 2026-11-07, "Wow these players are good.. does that seem
## normal?"): what a draft-night POT turns into. Same autopilot careers as draft_bust_impl (real
## 2026 lists, game's own ageing, training, list management and drafts), but each season end
## also records the draftee's games that season, his OVR rank in the whole league, and whether
## he made the All-Australian team. Measurement only.
##   OP|seed|draft_year|pick|id|club|src|age0|ovr0|pot0                       one per pick
##   OT|seed|draft_year|k|id|on_list|ovr|best|games|league_rank|aa|age        each season end
##   OL|seed|year|n_listed|ovr_rank20|ovr_rank50|ovr_rank100|games_max         league context
## godot --headless --path . --script tools/audit/run_audit.gd -- draft_outcome_impl 11,12 6

var cohort := {}


func _draft(d: Draft, year: int, seed_n: int, user: String) -> void:
	var guard := 0
	while not d.is_finished() and guard < 400:
		guard += 1
		if d.is_user_turn():
			var choice := {}
			for cand in d.board("", "", "", "overall", true):
				if d.can_pick_player(cand):
					choice = cand
					break
			if choice.is_empty() or not d.pick(choice):
				d._skip_current_pick()
				d.auto_until_user_turn()
		else:
			d.auto_until_user_turn()
	for e in d.pick_history:
		var p: Dictionary = d.picked.get(str(e["player_id"]), {})
		if p.is_empty():
			continue
		var club := "USER" if str(e["club"]) == user else str(e["club"])
		print("OP|%d|%d|%d|%s|%s|%s|%.1f|%d|%d" % [seed_n, year, int(e["pick"]), str(p["id"]), club,
				"real" if not bool(p.get("generated", false)) else "gen", float(p.get("age", 0)),
				int(p["overall"]), maxi(int(p["overall"]), int(p.get("potential", p["overall"])))])
		if club != "USER":
			cohort[str(p["id"])] = {"year": year, "best": int(p["overall"])}


func _track(year: int, seed_n: int) -> void:
	var on := {}
	var all := []
	for code in GameState.season.lists:
		for p in GameState.season.lists[code]:
			on[str(p["id"])] = p
			all.append(int(p["overall"]))
	all.sort()
	all.reverse()
	var rank_of := func(ovr: int) -> int:
		# 1 + number of listed players strictly better
		var r := 0
		for v in all:
			if v > ovr:
				r += 1
			else:
				break
		return r + 1
	var aa := {}
	for r in (GameState.season_awards.get("all_australian", []) as Array):
		aa[str(r.get("id", ""))] = true
	var gmax := 0
	for id in GameState.season_tally:
		gmax = maxi(gmax, int(GameState.season_tally[id].get("games", 0)))
	print("OL|%d|%d|%d|%d|%d|%d|%d|aa%d" % [seed_n, year, all.size(), all[mini(19, all.size() - 1)],
			all[mini(49, all.size() - 1)], all[mini(99, all.size() - 1)], gmax, aa.size()])
	for id in cohort:
		var c: Dictionary = cohort[id]
		var k: int = year - int(c["year"])
		if k < 1:
			continue
		var p = on.get(id)
		var ovr := 0
		var rank := 0
		var age := 0.0
		if p != null:
			ovr = int(p["overall"])
			c["best"] = maxi(int(c["best"]), ovr)
			rank = rank_of.call(ovr)
			age = float(p.get("age", 0))
		var games := int((GameState.season_tally.get(id, {}) as Dictionary).get("games", 0))
		print("OT|%d|%d|%d|%s|%d|%d|%d|%d|%d|%d|%.1f" % [seed_n, int(c["year"]), k, id, 1 if p != null else 0,
				ovr, int(c["best"]), games, rank, 1 if aa.has(id) else 0, age])


func _career(seed_n: int, seasons: int) -> void:
	var clubs := ["MEL", "COL", "ADE", "CAR", "FRE", "SYD", "GEE", "HAW"]
	var user: String = clubs[seed_n % clubs.size()]
	cohort = {}
	GameState.reset()
	GameState.autosave_enabled = false
	GameState.career_seed = seed_n
	GameState.replay_seed = seed_n
	print("OA|%d|user %s|seasons %d" % [seed_n, user, seasons])
	GameState.begin_real_lists()
	GameState.choose_real_club(user)
	_draft(GameState.draft, GameDB.DATA_SEASON, seed_n, user)
	GameState.finish_intake_draft()
	for s in range(seasons):
		var year := GameState.season_year
		while not GameState.season.is_season_over():
			GameState.advance()
		_track(year, seed_n)
		print("OS|%d|%d|done" % [seed_n, year])
		if s == seasons - 1:
			break
		GameState.open_offseason()
		if GameState.begin_intake_draft():
			_draft(GameState.draft, year, seed_n, user)
			GameState.finish_intake_draft()
		else:
			GameState.start_next_season()


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seeds := str(args[1]).split(",") if args.size() > 1 else PackedStringArray(["11"])
	var seasons := int(args[2]) if args.size() > 2 else 6
	for s in seeds:
		_career(int(s), seasons)
