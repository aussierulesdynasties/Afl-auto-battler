extends RefCounted
## Row 105 (press audit): over a long career, how often a press conference
## comes up a season, which questions and journalists, how many offer a named
## answer, how varied the question text is, where your standing with each
## journalist ends each season, and the largest press morale lift any player
## carried (it must stay inside the named cap). Args after the impl name:
## seed club seasons (`press_impl 41 MEL 10`). Starts from the club's real list.
##
## The autopilot answers every question with a seeded random answer, so every
## kind of answer, standing move and fade comes up.
##
## Prints per season: PRESS_SEASON <year> pressers <n> games <n> keys <k=n,...>
## journalists <j=n,...> named <n> distinct_text <n> standing <j=v,...>
## max_lift <n>; then PRESS_TOTAL lines (with how many games fielded each
## count of young players, MediaConference.is_young) and SUMMARY.
## Measurement only: it never changes a rule.

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seed := int(args[1]) if args.size() > 1 else 1
	var club := str(args[2]) if args.size() > 2 else "MEL"
	var seasons := int(args[3]) if args.size() > 3 else 10
	GameState.reset()
	GameState.career_seed = seed
	GameState.replay_seed = seed
	GameState.autosave_enabled = false
	GameState.start_season(club, GameDB.club_list(club))
	var answer := RandomNumberGenerator.new()
	answer.seed = hash("press-audit|%d" % seed)
	var tot_keys := {}
	var tot_j := {}
	var tot_kinds := {}
	var tot_landed := {}
	var tot_texts := {}
	var tot_press := 0
	var tot_named := 0
	var tot_games := 0
	var max_lift_all := 0
	var young_hist := {}
	var per_season: Array = []
	var played := 0
	for s in range(seasons):
		var keys := {}
		var js := {}
		var texts := {}
		var named := 0
		var press := 0
		var games := 0
		var max_lift := 0
		while not GameState.season.is_season_over() and not GameState.is_sacked():
			var ph := ClubStories.phase(GameState)
			if ph == "regular" or GameState.my_finals_status() == "alive":
				games += 1
			for i in range(GameState.week_events.size() - 1, -1, -1):
				var c: Dictionary = GameState.week_events[i]
				GameState.resolve_card(i, answer.randi_range(0, maxi(0, (c.get("options", []) as Array).size() - 1)))
			if GameState.media_conference_pending():
				var mc: Dictionary = GameState.media_conference
				var k := str(mc.get("key", "?"))
				var j := str(mc.get("journalist", "?"))
				press += 1
				keys[k] = int(keys.get(k, 0)) + 1
				js[j] = int(js.get(j, 0)) + 1
				texts[str(mc.get("question", ""))] = true
				tot_texts[str(mc.get("question", ""))] = true
				var opts: Array = mc.get("options", [])
				if opts.size() > 3:
					named += 1
				var pick := answer.randi_range(0, opts.size() - 1)
				var out: Dictionary = GameState.resolve_media_conference(pick)
				var kind := str(out.get("kind", "?"))
				tot_kinds[kind] = int(tot_kinds.get(kind, 0)) + 1
				var lk := "%s_%s" % [kind, str(out.get("landed", "?"))]
				tot_landed[lk] = int(tot_landed.get(lk, 0)) + 1
			for p in GameState.my_list:
				max_lift = maxi(max_lift, absi(int(p.get("press_lift", 0))))
			GameState.advance()
			var res := GameState._my_result(GameState.last_results)
			var roster: Array = res.get("roster", [])
			if roster.size() >= 2:
				var side := 0 if str(res.get("home", "")) == GameState.my_club else 1
				var young := 0
				for r in roster[side]:
					var yp: Dictionary = GameState._find_player(str(r.get("id", "")))
					if not yp.is_empty() and MediaConference.is_young(float(yp.get("age", 30.0))):
						young += 1
				young_hist[young] = int(young_hist.get(young, 0)) + 1
		played += 1
		var st := []
		for j in MediaConference.JOURNALISTS.keys():
			st.append("%s=%d" % [j, GameState.press_standing(j)])
		print("PRESS_SEASON %d pressers %d games %d keys %s journalists %s named %d distinct_text %d standing %s max_lift %d" % [
				GameState.season_year, press, games, _fmt(keys), _fmt(js), named, texts.size(), ",".join(st), max_lift])
		per_season.append(press)
		tot_press += press
		tot_named += named
		tot_games += games
		max_lift_all = maxi(max_lift_all, max_lift)
		for k in keys:
			tot_keys[k] = int(tot_keys.get(k, 0)) + int(keys[k])
		for k in js:
			tot_j[k] = int(tot_j.get(k, 0)) + int(js[k])
		if s == seasons - 1 or GameState.is_sacked():
			break
		GameState.open_offseason()
		if GameState.begin_intake_draft():
			var d: Draft = GameState.draft
			var guard := 0
			while not d.is_finished() and guard < 5000:
				guard += 1
				var c := d._best_ai_pick(d.current_club())
				if c.is_empty() or not d._draft_pick(d.current_club(), c):
					d._skip_current_pick()
			GameState.finish_intake_draft()
		else:
			GameState.start_next_season()
	print("PRESS_TOTAL keys %s" % _fmt(tot_keys))
	print("PRESS_TOTAL journalists %s" % _fmt(tot_j))
	print("PRESS_TOTAL answers %s" % _fmt(tot_kinds))
	print("PRESS_TOTAL landed %s" % _fmt(tot_landed))
	print("PRESS_TOTAL young_in_side %s" % _fmt(young_hist))
	var lo := 999
	var hi := 0
	for n in per_season:
		lo = mini(lo, int(n))
		hi = maxi(hi, int(n))
	var phil := int(tot_j.get("philosopher", 0))
	print("SUMMARY seed %d %s | seasons %d | games %d | pressers %d (%.1f a season, min %d max %d, %.0f%% of games) | named offered %d | distinct question texts %d | max press lift %d (cap %d) | philosopher %d (one in %.1f)" % [
			seed, club, played, tot_games, tot_press, float(tot_press) / float(maxi(1, played)), lo, hi,
			100.0 * float(tot_press) / float(maxi(1, tot_games)), tot_named, tot_texts.size(), max_lift_all,
			MediaConference.NAMED_CAP, phil, float(tot_press) / float(maxi(1, phil))])


func _fmt(d: Dictionary) -> String:
	var bits := []
	var ks := d.keys()
	ks.sort()
	for k in ks:
		bits.append("%s=%d" % [k, int(d[k])])
	return ",".join(bits)
