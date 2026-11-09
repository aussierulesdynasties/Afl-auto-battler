extends RefCounted
## Audit 19/60 (TODO section D): over long saves, how often press-conference
## questions and full-time coaching notes repeat, and how many pressers a
## season. Args after the impl name: seeds club seasons
## (`press_repeat_impl 41,42,43 MEL 12`). Each seed is one career from the
## club's real list; the autopilot answers every card and question with a
## seeded random option, and drafts with the AI's pick.
##
## The clock is your club's matches: "round" below is the count of your
## matches played since the career began (finals included), so a gap of 23
## is about one season.
##
## A press question is its "qid" (MediaConference._q: key.version, the
## written question before names and numbers fill it). A coaching note is the
## line the full-time screen shows under "Coaching notes", built exactly as
## MatchScene does (CoachReport.glance on match_report, less what the story
## and How it went said, first two), identified by its text with numbers
## taken out (CoachReport._second_half_keys writes each one).
##
## Prints per season and seed:
##   PR_SEASON seed <s> year <y> games <n> pressers <n> q_total <n> q_distinct <n>
##       q_repeats <n> q_top <qid=n,...> notes_total <n> notes_distinct <n> n_top <id=n,...>
## and per career:
##   PR_GAPS seed <s> kind q|n id <id> count <n> gaps <g,g,...>
##   SUMMARY seed <s> ...
## A random-answer autopilot gets sacked within a few seasons; the audit is
## about long saves at one club, so a sacking is cleared on the spot and
## counted (reprieves in SUMMARY). Measurement only: it never changes a rule.

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seeds := str(args[1]) if args.size() > 1 else "1"
	var club := str(args[2]) if args.size() > 2 else "MEL"
	var seasons := int(args[3]) if args.size() > 3 else 10
	for s in seeds.split(",", false):
		_career(int(s), club, seasons)


func _career(seed: int, club: String, seasons: int) -> void:
	GameState.reset()
	GameState.career_seed = seed
	GameState.replay_seed = seed
	GameState.autosave_enabled = false
	GameState.start_season(club, GameDB.club_list(club))
	var answer := RandomNumberGenerator.new()
	answer.seed = hash("press-repeat|%d" % seed)
	var clock := 0
	var q_seen := {}   # qid -> [clock, ...]
	var n_seen := {}   # note id -> [clock, ...]
	var q_text := {}   # qid -> an example question
	var n_text := {}
	var tot_press := 0
	var tot_games := 0
	var played := 0
	var reprieves := 0
	for s in range(seasons):
		var games := 0
		var press := 0
		var qs := {}
		var ns := {}
		var notes_total := 0
		while not GameState.season.is_season_over():
			if GameState.is_sacked():
				GameState.board["sacked"] = false
				reprieves += 1
			for i in range(GameState.week_events.size() - 1, -1, -1):
				var c: Dictionary = GameState.week_events[i]
				GameState.resolve_card(i, answer.randi_range(0, maxi(0, (c.get("options", []) as Array).size() - 1)))
			if GameState.media_conference_pending():
				var mc: Dictionary = GameState.media_conference
				var qid := str(mc.get("qid", "")) if str(mc.get("qid", "")) != "" else str(mc.get("key", "?")) + ".?"
				press += 1
				qs[qid] = int(qs.get(qid, 0)) + 1
				var arr: Array = q_seen.get(qid, [])
				arr.append(clock)
				q_seen[qid] = arr
				if not q_text.has(qid):
					q_text[qid] = str(mc.get("question", "")).replace("\n", " ")
				var opts: Array = mc.get("options", [])
				GameState.resolve_media_conference(answer.randi_range(0, maxi(0, opts.size() - 1)))
			GameState.advance()
			var res := GameState._my_result(GameState.last_results)
			if res.is_empty():
				continue
			games += 1
			clock += 1
			for note in _ft_notes(res):
				var nid := _note_id(str(note))
				notes_total += 1
				ns[nid] = int(ns.get(nid, 0)) + 1
				var na: Array = n_seen.get(nid, [])
				na.append(clock)
				n_seen[nid] = na
				if not n_text.has(nid):
					n_text[nid] = str(note)
		played += 1
		var q_total := 0
		for k in qs:
			q_total += int(qs[k])
		print("PR_SEASON seed %d year %d games %d pressers %d q_total %d q_distinct %d q_repeats %d q_top %s notes_total %d notes_distinct %d n_top %s" % [
				seed, GameState.season_year, games, press, q_total, qs.size(), q_total - qs.size(),
				_top(qs, 5), notes_total, ns.size(), _top(ns, 5)])
		tot_press += press
		tot_games += games
		if GameState.is_sacked():
			GameState.board["sacked"] = false
			reprieves += 1
		if s == seasons - 1:
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
	for qid in q_seen:
		print("PR_GAPS seed %d kind q id %s count %d gaps %s text %s" % [seed, qid, (q_seen[qid] as Array).size(), _gaps(q_seen[qid]), q_text[qid]])
	for nid in n_seen:
		print("PR_GAPS seed %d kind n id %s count %d gaps %s text %s" % [seed, nid, (n_seen[nid] as Array).size(), _gaps(n_seen[nid]), n_text[nid]])
	print("SUMMARY seed %d %s | seasons %d | games %d | pressers %d (%.1f a season) | distinct qids %d | distinct notes %d | reprieves %d" % [
			seed, club, played, tot_games, tot_press, float(tot_press) / float(maxi(1, played)),
			q_seen.size(), n_seen.size(), reprieves])


## The full-time "Coaching notes" lines, as MatchScene builds them for your match.
func _ft_notes(res: Dictionary) -> Array:
	if (res.get("quarter_teams", []) as Array).size() < 2:
		return []
	var me := 0 if str(res.get("home", "")) == GameState.my_club else 1
	var told := MatchStory.told_facts(MatchStory.build(res, me))
	var said := told.duplicate()
	var shown := MatchNotes.match_factors(res, me, told)
	for it in MatchNotes.match_factor_items(res, me):
		if shown.has(str(it["text"])):
			said[str(it["fact"])] = true
	var g := CoachReport.glance(CoachReport.match_report(res, me), true)
	return CoachReport.notes_not_told(g["notes"], said).slice(0, 2)


func _note_id(t: String) -> String:
	var re := RegEx.new()
	re.compile("[0-9]+")
	return re.sub(t, "#", true).replace(" ", "_")


func _gaps(clocks: Array) -> String:
	var out := []
	for i in range(1, clocks.size()):
		out.append(str(int(clocks[i]) - int(clocks[i - 1])))
	return ",".join(out) if not out.is_empty() else "-"


func _top(d: Dictionary, n: int) -> String:
	var ks := d.keys()
	ks.sort_custom(func(a, b): return int(d[a]) > int(d[b]) or (int(d[a]) == int(d[b]) and str(a) < str(b)))
	var bits := []
	for k in ks.slice(0, n):
		bits.append("%s=%d" % [k, int(d[k])])
	return ",".join(bits)
