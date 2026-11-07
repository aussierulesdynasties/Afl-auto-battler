extends RefCounted
## Row 34 (event-card audit): how often every story card comes up, and which
## choice the answers take, over a long career. Args after the impl name:
## seed club seasons [lists] [real] (`cards_impl 41 MEL 10 lists real`). "lists"
## starts from the club's real list, otherwise a redraft start; "real" plays with
## real names on, where private cards only pick players shown under a fictional name.
##
## The autopilot answers every card with a seeded random choice, so each choice and
## each arc beat can come up. Each week it also asks every card, against the live
## state, whether its trigger could be met at all (ignoring cooldowns, per-season
## limits, the category rule and arcs), so a card that never comes up can be told
## apart: trigger never true, or true but never drawn.
##
## The coach walks every pre-season stop (as a player who does not sim to Round 1
## does), so the pre-season's cards are dealt, and the card the week a season ends
## brings (knocked out, or the Grand Final played) is answered too. At the papers
## he answers the paper's question with a seeded random choice, or says nothing
## (one chance more than the card has choices), so the papers arc can follow.
##
## Prints per career: CARD <id> <times>, CHOICE <id> <key> <times>, COND <id>
## <weeks the trigger was met>, NEVER <id> <trigger weeks> for a card not dealt
## once, PRESS <question key> <times> (the post-match press questions, skipped),
## WEEKS <weeks in play>, SEASONS, then SUMMARY. WEEKS counts the weeks a card
## could come: the regular season, the finals while alive or on the week off, the
## pre-season's card weeks and the week the season ends.
## Measurement only: it never changes a rule.

var deck: Array = []
var seen := {}
var took := {}
var cond := {}
var weeks := 0
var end_counted := 0
var answer := RandomNumberGenerator.new()
var probe := RandomNumberGenerator.new()


func _run_draft(d: Draft) -> void:
	var guard := 0
	while not d.is_finished() and guard < 5000:
		guard += 1
		var c := d._best_ai_pick(d.current_club())
		if c.is_empty() or not d._draft_pick(d.current_club(), c):
			d._skip_current_pick()


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seed := int(args[1]) if args.size() > 1 else 1
	var club := str(args[2]) if args.size() > 2 else "MEL"
	var seasons := int(args[3]) if args.size() > 3 else 10
	var real := args.has("real")
	GameState.reset()
	GameState.show_real_names = real
	GameState.career_seed = seed
	GameState.replay_seed = seed
	GameState.autosave_enabled = false
	if args.has("lists"):
		GameState.start_season(club, GameDB.club_list(club))
	else:
		var pool: Array = GameDB.all_players_sorted() + GameDB.all_draftees_sorted()
		pool.sort_custom(func(a, b): return a["overall"] > b["overall"])
		GameState.draft = Draft.new(pool, GameDB.active_clubs(GameState.season_year).duplicate(), seed)
		GameState.draft.start_for_user(club)
		_run_draft(GameState.draft)
		GameState.start_season(club, GameState.draft.list())
	# A new career opens its pre-season after the draft (DraftScene).
	GameState.open_preseason(false)
	answer.seed = hash("cards-audit|%d" % seed)
	probe.seed = hash("cards-probe|%d" % seed)
	deck = StoryDeck.all()
	var press := {}
	var seasons_played := 0
	for s in range(seasons):
		_walk_preseason()
		while not GameState.season.is_season_over() and not GameState.is_sacked():
			var ph := ClubStories.phase(GameState)
			if ph == "regular" or ["alive", "bye"].has(GameState.my_finals_status()):
				weeks += 1
				_count_cond(ClubStories.context(GameState))
			else:
				_season_end_cond()
			_deal()
			if GameState.media_conference_pending():
				# The press question is counted, then skipped, so the career is the
				# same as one that never looked at it.
				var mk := str(GameState.media_conference.get("key", "?"))
				press[mk] = int(press.get(mk, 0)) + 1
				GameState.skip_media_conference()
			GameState.advance()
		# The Grand Final ends the season: its card (premiers, runners-up, or the
		# side knocked out that week) is dealt after the last match.
		if not GameState.is_sacked():
			_season_end_cond()
		_deal()
		seasons_played += 1
		print("CARDS seed %d %s season %d | cards so far %d | distinct so far %d" % [seed, club, GameState.season_year,
				_sum(seen), seen.size()])
		# Sacked with a job on offer: the audit takes the first club and goes on.
		ClubMoves.take_first_offer(GameState)
		if s == seasons - 1 or GameState.is_sacked():
			break
		GameState.open_offseason()
		if GameState.begin_intake_draft():
			_run_draft(GameState.draft)
			GameState.finish_intake_draft()
		else:
			GameState.start_next_season()
	for t in deck:
		var id := str(t["id"])
		print("CARD %s %d" % [id, int(seen.get(id, 0))])
		print("COND %s %d" % [id, int(cond.get(id, 0))])
	# The cards this career never dealt, with how many weeks their trigger was met:
	# 0 means the trigger never held; more means it held and the card was not drawn.
	for t in deck:
		var id := str(t["id"])
		if int(seen.get(id, 0)) == 0:
			print("NEVER %s %d" % [id, int(cond.get(id, 0))])
	for k in press:
		print("PRESS %s %d" % [k, int(press[k])])
	for k in took:
		print("CHOICE %s %d" % [k, int(took[k])])
	print("WEEKS %d" % weeks)
	print("SEASONS %d" % seasons_played)
	print("SUMMARY seed %d %s %s names %s | seasons %d | weeks %d | cards %d | distinct %d of %d" % [seed, club,
			"lists" if args.has("lists") else "redraft", "real" if real else "fictional", seasons_played, weeks,
			_sum(seen), seen.size(), deck.size()])


func _sum(d: Dictionary) -> int:
	var n := 0
	for k in d:
		n += int(d[k])
	return n


## Every card waiting this week, answered with a seeded random choice.
func _deal() -> void:
	for i in range(GameState.week_events.size()):
		var c: Dictionary = GameState.week_events[i]
		if bool(c.get("resolved", false)):
			continue
		var tid := str(c.get("tid", c.get("key", "")))
		seen[tid] = int(seen.get(tid, 0)) + 1
		var opts: Array = c.get("options", [])
		if opts.is_empty():
			continue
		var pick := answer.randi_range(0, opts.size() - 1)
		var ck := "%s %s" % [tid, str((opts[pick] as Dictionary).get("key", pick))]
		took[ck] = int(took.get(ck, 0)) + 1
		GameState.resolve_card(i, pick)


## The pre-season, stop by stop: the time trial, the pre-season match, the papers
## and the card stops after each block, answered like any card.
## Its triggers are asked on the card weeks it stops at (a card week that brings
## no card and no other stop passes unasked), so a pre-season COND is a floor.
func _walk_preseason() -> void:
	var guard := 0
	var counted := -1
	while GameState.preseason_active() and guard < 100:
		guard += 1
		var pw := GameState.preseason_week()
		if PreSeason.STORY_WEEKS.has(pw) and pw != counted:
			counted = pw
			weeks += 1
			_count_cond(ClubStories.context(GameState))
		if GameState.preseason_stop() == "story":
			_deal()
		elif GameState.preseason_stop() == "papers":
			_answer_papers()
		GameState.preseason_advance()


## The paper's card (the finish it tips, the pressure, a breakout): counted as
## dealt, then answered with one of its choices or with nothing said.
func _answer_papers() -> void:
	var card := GameState.papers_card()
	if card.is_empty() or bool(GameState.papers_record().get("answered", false)):
		return
	var tid := str(card.get("tid", card.get("key", "")))
	seen[tid] = int(seen.get(tid, 0)) + 1
	var opts: Array = card.get("options", [])
	var pick := answer.randi_range(0, opts.size())
	if pick >= opts.size():
		took["%s nothing" % tid] = int(took.get("%s nothing" % tid, 0)) + 1
		return   # preseason_advance says nothing
	var ck := "%s %s" % [tid, str((opts[pick] as Dictionary).get("key", pick))]
	took[ck] = int(took.get(ck, 0)) + 1
	GameState.papers_answer(pick)


## The week a season ends (knocked out, or the Grand Final played): the
## season-end cards' triggers, once a season. The card itself was drawn when
## the last match was played.
func _season_end_cond() -> void:
	if end_counted == GameState.season_year or GameState.season == null or not GameState.season.is_regular_done():
		return
	if not ["eliminated", "premier", "runner_up"].has(GameState.my_finals_status()):
		return
	end_counted = GameState.season_year
	weeks += 1
	_count_cond(ClubStories.context(GameState, "season_end"))


## Each card asked, against the live state, whether its trigger alone holds.
func _count_cond(ctx: Dictionary) -> void:
	var w := StoryEngine.week_abs(int(ctx["year"]), int(ctx["week"]))
	for t in deck:
		# The trigger alone: an empty memory, so no cooldown, limit,
		# category rule or flag decides it. A follow-up's own trigger
		# is its conditions with the flag taken as given.
		var bare: Dictionary = (t as Dictionary).duplicate(true)
		bare.erase("needs")
		bare.erase("arc")
		bare["cooldown"] = 0
		bare["subject_cooldown"] = 0
		bare["per_season"] = 0
		if not (bare.get("subject", {}) as Dictionary).is_empty():
			var sj: Dictionary = bare["subject"]
			var wh: Dictionary = (sj.get("where", {}) as Dictionary).duplicate()
			wh.erase("flag")
			sj["where"] = wh
		if not StoryEngine.eligible_subject(bare, ctx, StoryEngine.new_state(), w, probe).is_empty():
			cond[str(t["id"])] = int(cond.get(str(t["id"]), 0)) + 1
