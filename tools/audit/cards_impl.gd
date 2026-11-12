extends RefCounted
## Row 34 (event-card audit): how often every story card comes up, and which
## choice the answers take, over a long career. Args after the impl name:
## seed club seasons [lists] [real] (`cards_impl 41 MEL 10 lists real`). "lists"
## starts from the club's real list, otherwise a redraft start. Real names are
## always on, so private cards only pick generated players ("real" changes nothing).
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
## Three ways of coaching, each the coach's own call (row 107: to reach the cards a
## random coach seldom does), set by env and off by default:
## - COVER=1: every card is answered with the choice this career has taken least
##   (a tie goes to the seeded dice), so every branch of an arc gets its turn;
## - INTL=1: at the club's own draft picks, any international prospect on the board
##   is taken first;
## - KEEP=1: every expiring player under 31 in the best 30 of the list is offered two
##   more seasons at his asking price, and his counter if he makes one, so the list does
##   not run down and the draft still has spots to fill;
## - HEAVY=1: the first block of every pre-season is trained Heavy (Running), as the
##   game's contending clubs train it, so pre-season training can injure;
## - ANSWER=card:key,card:key: those cards are always answered with that choice (when
##   it is on the card), so an arc's rarer branch can be followed to its end.
## - STRONG=n: before each season every player on the coach's list gains n on each
##   attribute and his overall, so finals and Grand Finals are reached and their cards
##   can be counted. It changes the list, so its results say nothing about balance.
## Each season also prints NZSTATE for each New Zealander on the list, with what the
## rugby card asks of him, and FINISH <year> <club> ladder <position> finals <status>.
## Measurement only: it never changes a rule.

var deck: Array = []
var seen := {}
var took := {}
var cond := {}
var weeks := 0
var end_counted := 0
var answer := RandomNumberGenerator.new()
var probe := RandomNumberGenerator.new()
var cover := OS.get_environment("COVER") == "1"
var intl := OS.get_environment("INTL") == "1"
var keep := OS.get_environment("KEEP") == "1"
var heavy := OS.get_environment("HEAVY") == "1"
var fixed := _answers(OS.get_environment("ANSWER"))
var strong := int(OS.get_environment("STRONG"))


## ANSWER's "card:key,card:key" as {card: key}.
static func _answers(env: String) -> Dictionary:
	var out := {}
	for pair in env.split(",", false):
		var kv := pair.split(":")
		if kv.size() == 2:
			out[kv[0].strip_edges()] = kv[1].strip_edges()
	return out


func _run_draft(d: Draft) -> void:
	var guard := 0
	while not d.is_finished() and guard < 5000:
		guard += 1
		var code := d.current_club()
		var at := d.pick_index + 1
		var c := _intl_pick(d) if intl and code == d.user_club else {}
		if not c.is_empty() and d._draft_pick(code, c):
			print("INTL drafted %s from %s at pick %d for %s" % [str(c["id"]), str(c["intl"]), at, code])
			continue
		c = d._best_ai_pick(code)
		if c.is_empty() or not d._draft_pick(code, c):
			d._skip_current_pick()


## The first international prospect still on the board that the club can take, or {}.
func _intl_pick(d: Draft) -> Dictionary:
	for p in d.pool:
		if not InternationalProspects.is_international(p) or d.picked.has(str(p["id"])):
			continue
		if d._can_afford_for(d.user_club, p) and not (d.user_max_age > 0 and d.too_old_for_user(p)):
			return p
	return {}


## The choice to take: seeded random, or under COVER the one this career has taken least.
func _choose(tid: String, opts: Array, extra := 0) -> int:
	if fixed.has(tid):
		for i in range(opts.size()):
			if str((opts[i] as Dictionary).get("key", "")) == str(fixed[tid]):
				return i
	if not cover:
		return answer.randi_range(0, opts.size() - 1 + extra)
	var best := []
	var low := 1 << 30
	for i in range(opts.size() + extra):
		var k := "%s %s" % [tid, str((opts[i] as Dictionary).get("key", i)) if i < opts.size() else "nothing"]
		var n := int(took.get(k, 0))
		if n < low:
			low = n
			best = [i]
		elif n == low:
			best.append(i)
	return int(best[answer.randi_range(0, best.size() - 1)])


## KEEP: every expiring player of yours under 31 and in the list's best 30 offered two
## seasons at his asking price, then his counter if he makes one.
func _keep_list() -> void:
	if not keep or not GameState.offseason_open():
		return
	var best := GameState.my_list.duplicate()
	best.sort_custom(func(a, b): return float(a.get("overall", 0)) > float(b.get("overall", 0)))
	best = best.slice(0, 30)
	for p in Contracts.expiring(GameState.my_list).duplicate():
		if float(p.get("age", 30)) >= 31.0 or not best.has(p):
			continue
		var id := str(p["id"])
		var r: Dictionary = GameState.resign_player(id, 2)
		if str(r.get("answer", "")) == "counter":
			GameState.offer_contract(id, int(r.get("salary", 0)), 2)


func _strengthen() -> void:
	if strong <= 0:
		return
	for p in GameState.my_list:
		p["overall"] = mini(99, int(p.get("overall", 50)) + strong)
		var attr: Dictionary = p.get("attr", {})
		for k in attr:
			attr[k] = minf(99.0, float(attr[k]) + strong)


func _print_nz() -> void:
	for p in GameState.my_list:
		if InternationalProspects.region(p) == "nz":
			var room: int = GameState.cap_for(str(GameState.my_club)) - GameState.my_payroll()
			var over: int = ClubLife.early_price(p) - int(p.get("salary", 0))
			print("NZSTATE %d %s ovr %d pot %d years %d morale %d drafted %d wanted %s price_over %d cap_room %d" % [GameState.season_year, str(p["id"]),
					int(p.get("overall", 0)), int(p.get("potential", 0)), int(p.get("contract_years", 0)),
					int(ClubLife.morale(p)), int(p.get("drafted_year", -1)),
					str(ClubLife.extension_wanted(p, {}, ClubLife.INTL_EXTENSION_MIN_OVR)), over, room])
			var f: Dictionary = ClubStories.player_fact(GameState, p, true, {}, 99, room)
			print("NZFACT %s ok %s seasons %d fit %s intl %s region %s years %d" % [str(p["id"]), str(f.get("intl_extension_ok")),
					int(f.get("seasons_listed", -1)), str(f.get("fit")), str(f.get("intl")), str(f.get("intl_region")), int(f.get("contract_years", -1))])


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seed := int(args[1]) if args.size() > 1 else 1
	var club := str(args[2]) if args.size() > 2 else "MEL"
	var seasons := int(args[3]) if args.size() > 3 else 10
	GameState.reset()
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
		_strengthen()
		_print_nz()
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
		print("FINISH %d %s ladder %d finals %s" % [GameState.season_year, GameState.my_club, GameState.my_position(),
				GameState.my_finals_status() if GameState.my_finals_status() != "" else "out"])
		print("CARDS seed %d %s season %d | cards so far %d | distinct so far %d" % [seed, club, GameState.season_year,
				_sum(seen), seen.size()])
		if intl:
			print("INTL on list %d at %s" % [GameState.my_list.filter(func(q): return InternationalProspects.is_international(q)).size(),
					GameState.my_club])
		# Sacked with a job on offer: the audit takes the first club and goes on.
		ClubMoves.take_first_offer(GameState)
		if s == seasons - 1 or GameState.is_sacked():
			break
		GameState.open_offseason()
		_keep_list()
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
	print("SUMMARY seed %d %s %s names %s%s | seasons %d | weeks %d | cards %d | distinct %d of %d" % [seed, club,
			"lists" if args.has("lists") else "redraft", "real",
			(" coach" + (" cover" if cover else "") + (" intl" if intl else "") + (" keep" if keep else "")
					+ (" heavy" if heavy else "") + (" answer" if not fixed.is_empty() else "")) if cover or intl or keep or heavy or not fixed.is_empty() else "",
			seasons_played, weeks,
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
		var pick := _choose(tid, opts)
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
	if heavy:
		GameState.set_preseason_block(0, "heavy", "running")
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
	var pick := _choose(tid, opts, 1)
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
