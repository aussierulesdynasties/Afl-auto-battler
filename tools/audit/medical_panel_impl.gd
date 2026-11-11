extends RefCounted
## The concussion medical panel over a long autopilot career (MedicalPanel.gd):
## how often a player reaches five concussions in five seasons, how many the
## panel retires, and the concussion rate. Every club drafts as the AI does;
## every default is left alone. Measurement only: no rate is changed.
##
## Args after the impl name: seed club seasons (defaults 301 FRE 30).
##
## One PANEL line a season: concussions that season (and per club), sittings,
## cleared and retired, and how many listed players stand on 3, 4 and 5 or more
## in the five-season window at season's end. SITTING lines name each one.
## SUMMARY totals the seasons played; a career that stops rolling over (the
## autopilot coach sacked) prints STOPPED and is totalled to there.


func _run_draft(d: Draft) -> void:
	var guard := 0
	while not d.is_finished() and guard < 5000:
		guard += 1
		var c := d._best_ai_pick(d.current_club())
		if c.is_empty() or not d._draft_pick(d.current_club(), c):
			d._skip_current_pick()


func _concussions(year: int) -> int:
	var n := 0
	for id in GameState.career_facts:
		for r in GameState.career_facts[id]:
			if str(r[CareerFacts.K]) == "injury" and str(r[CareerFacts.OUT]) == "concussion" \
					and int(r[CareerFacts.Y]) == year:
				n += 1
	return n


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seed := int(args[1]) if args.size() > 1 else 301
	var club := str(args[2]) if args.size() > 2 else "FRE"
	var seasons := int(args[3]) if args.size() > 3 else 30
	GameState.reset()
	GameState.career_seed = seed
	GameState.replay_seed = seed
	GameState.autosave_enabled = false
	GameState.start_season(club, GameDB.club_list(club))
	var all_conc := 0
	var all_sat := 0
	var all_retired := 0
	var all_players := {}
	var all_games := 0
	var most := 0
	var played := 0
	for s in range(seasons):
		var year := GameState.season_year
		var sat := 0
		var retired := 0
		while not GameState.season.is_season_over():
			GameState.advance()
			for res in GameState.last_results:
				for side in res.get("roster", []):
					all_games += (side as Array).size()
			for row in GameState.last_medical:
				sat += 1
				all_players[str(row["id"])] = true
				if not bool(row["cleared"]):
					retired += 1
				print("SITTING seed %d %d %s | %s (%s, OVR %d) | concussion %d in 5 years | %s" % [
						seed, year, str(row.get("at", "")), str(row["name"]), str(row["club"]), int(row["overall"]),
						int(row["count"]), "cleared" if bool(row["cleared"]) else "retired"])
		var conc := _concussions(year)
		var on := {3: 0, 4: 0, 5: 0}
		var listed := 0
		for code in GameState.season.lists:
			for p in GameState.season.lists[code]:
				listed += 1
				var n := GameState.concussions_in_window(p)
				most = maxi(most, n)
				if n >= 3:
					on[mini(n, 5)] += 1
		var clubs := GameState.season.lists.size()
		print("PANEL seed %d season %d (%d) | concussions %d (%.2f a club) | sittings %d, cleared %d, retired %d | listed %d: on three %d, on four %d, on five or more %d" % [
				seed, s + 1, year, conc, float(conc) / maxf(1.0, clubs), sat, sat - retired, retired,
				listed, int(on[3]), int(on[4]), int(on[5])])
		all_conc += conc
		all_sat += sat
		all_retired += retired
		GameState.open_offseason()
		if GameState.begin_intake_draft():
			_run_draft(GameState.draft)
			GameState.finish_intake_draft()
		else:
			GameState.start_next_season()
		played += 1
		# A career that does not roll over (the autopilot coach was sacked) has no
		# more seasons to count: stop instead of printing the last one again.
		if GameState.season_year == year:
			print("STOPPED seed %d after %d seasons: the career did not roll over from %d (sacked: %s)" % [
					seed, played, year, str(GameState.is_sacked())])
			break
	seasons = played
	print("SUMMARY seed %d seasons %d | concussions %d (%.1f a season, %.4f a player-game over %d player-games) | sittings %d on %d players | cleared %d | retired %d | most in any five-season window %d | clear chance %d%%" % [
			seed, seasons, all_conc, float(all_conc) / maxf(1.0, seasons), float(all_conc) / maxf(1.0, all_games),
			all_games, all_sat, all_players.size(), all_sat - all_retired, all_retired, most, MedicalPanel.clear_pct()])
