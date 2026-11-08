extends RefCounted
## The pre-season story cards (open requirements 39, slice 5): the deck is valid
## and kept to the pre-season, a card stops the pre-season only at the end of a
## block, every answer does what its Gain and Cost lines say, Round 1's own cards
## wait aside and come back, a hands-off run draws none, the same save sees the
## same cards, and a save made at the stop reloads at the stop. Part of the story
## suite (tests/test_story.gd calls run()).

var s   # the story suite: _check()

const SEED := 6113
const CLUB := "FRE"
const IDS := ["pre_recruit_behind", "pre_contract_talk", "pre_bulking_up", "pre_camp", "pre_leaders_vote",
		"pre_knee_return", "pre_flag_hangover", "pre_kid_flying", "pre_star_last", "pre_members_open", "pre_sim_heated"]


func run(suite) -> void:
	s = suite
	var before: int = s.checks
	PreSeason.reload()
	_t("_test_deck")
	_t("_test_flow")
	_t("_test_effects")
	_t("_test_facts")
	_t("_test_running_again")
	_t("_test_running_again_comes")
	_t("_test_hands_off_and_save")
	print("Pre-season cards: %d of the story suite's checks" % (s.checks - before))
	PreSeason.reload()


func _check(c: bool, m: String) -> void:
	s._check(c, m)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args, s)


func _career(seed := SEED) -> void:
	GameState.reset()
	GameState.career_seed = seed
	GameState.replay_seed = seed
	GameState.start_season(CLUB, GameDB.club_list(CLUB))
	GameState.open_preseason()


func _ids(cards: Array) -> Array:
	return cards.map(func(c): return str(c["tid"]))


func _test_deck() -> void:
	StoryDeck.reload()
	var deck := StoryDeck.all()
	_check(StoryDeck.validate(deck).is_empty(), "The deck with the pre-season cards in it still validates: %s" % " | ".join(PackedStringArray(StoryDeck.validate(deck).slice(0, 4))))
	var found := 0
	var only := true
	for id in IDS:
		var t := StoryDeck.by_id(deck, id)
		if not t.is_empty():
			found += 1
			only = only and (t["phase"] as Array) == ["preseason"]
	_check(found == IDS.size() and only, "All %d pre-season cards are in the deck, and they are written for the pre-season alone" % IDS.size())
	var gates := true
	for t in deck:
		if not IDS.has(str(t["id"])) and (t["phase"] as Array).has("preseason"):
			gates = false
	_check(gates, "No older card was opened to the pre-season by accident")
	# Not drawn in the season: the phase gate.
	_career()
	GameState.preseason_advance()
	var ctx := ClubStories.context(GameState)
	_check(str(ctx["phase"]) == "preseason" and not bool(ctx["big"]), "At a stop the cards draw in the pre-season phase, one at a time")
	var rng := RandomNumberGenerator.new()
	var leaked := false
	var regular_ctx := ctx.duplicate(true)
	regular_ctx["phase"] = "regular"
	for id in IDS:
		var subj := StoryEngine.eligible_subject(StoryDeck.by_id(deck, id), regular_ctx, GameState.story, 100, rng)
		leaked = leaked or not subj.is_empty()
	_check(not leaked, "None of them can come up in a home-and-away week")


## Press on through a pre-season by hand, answering nothing; returns the ids met at the stops.
func _walk(answer := -1) -> Array:
	var met := []
	var guard := 0
	while GameState.preseason_active() and guard < 30:
		guard += 1
		if GameState.preseason_stop() == "story":
			var n: int = GameState.week_events.size()
			met.append([GameState.preseason_week(), _ids(GameState.week_events), n])
			if answer >= 0:
				GameState.resolve_week_event(answer)
		GameState.preseason_advance()
	return met


func _test_flow() -> void:
	var seen := {}
	var one_a_block := true
	var weeks_ok := true
	var most := 0
	var total := 0
	var comes_back := true
	var starts_with_cards := 0
	for seed in range(SEED, SEED + 14):
		_career(seed)
		var round1 := _ids(GameState.week_events)
		var met := _walk(0)
		starts_with_cards += 1 if not met.is_empty() else 0
		most = maxi(most, met.size())
		for m in met:
			total += 1
			one_a_block = one_a_block and int(m[2]) == 1
			weeks_ok = weeks_ok and PreSeason.STORY_WEEKS.has(int(m[0]))
			for id in m[1]:
				seen[id] = true
		comes_back = comes_back and _ids(GameState.week_events) == round1
	_check(one_a_block, "A stop holds one card")
	_check(weeks_ok, "Cards stop the pre-season only at the end of a block (after weeks 3, 5 and 7)")
	_check(most <= 3 and total > 0, "At most three cards in a pre-season, and some do come (%d across 14 careers)" % total)
	_check(starts_with_cards >= 10, "Nearly every pre-season brings a card or two (%d of 14 had one, %d in all)" % [starts_with_cards, total])
	_check(comes_back, "Round 1's own cards wait aside through the pre-season and come back as they were")
	_check(seen.size() >= 4, "A spread of the cards comes up across careers (%d different)" % seen.size())
	for id in seen:
		_check(IDS.has(id), "Only pre-season cards come up at a stop (%s)" % id)
	# Unanswered: the stop settles and nothing breaks.
	_career(SEED + 1)
	var met_silent := _walk(-1)
	_check(not GameState.preseason_active() and GameState.week_events.size() <= 2, "Pressing on past a card leaves it unanswered and the pre-season finishes (%d stops)" % met_silent.size())
	# Determinism.
	_career(SEED + 2)
	var a := _walk(1)
	_career(SEED + 2)
	var b := _walk(1)
	_check(JSON.stringify(a) == JSON.stringify(b), "The same save meets the same cards at the same stops")


func _first_player(where: Callable) -> Dictionary:
	for p in GameState.my_list:
		if where.call(p):
			return p
	return {}


## Every answer does what its lines say: the strands, the base, the plan, and what a player feels.
func _test_effects() -> void:
	_career()
	GameState.preseason_advance()   # week 3 stop
	var deck := StoryDeck.all()
	var wrong := []
	var lines_missing := []
	var one_sided := []
	var clubs_checked := 0
	for id in IDS:
		var t := StoryDeck.by_id(deck, id)
		var player := str(t["subject"].get("kind", "")) == "player"
		for ci in range((t["choices"] as Array).size()):
			_career()
			GameState.preseason_advance()
			var subj := {}
			if player:
				subj = _subject_for(id)
				if subj.is_empty():
					continue
			var card := GameState.story_card(id, subj)
			var opts: Array = card["options"]
			if ci >= opts.size():
				continue
			var lines := StoryEngine.stakes_lines(opts[ci]["effects"], card["facts"])
			if lines.is_empty():
				lines_missing.append("%s/%s" % [id, opts[ci]["key"]])
			# Every answer has an upside and a downside (director, 2026-10-18; the sizes are the story suite's check).
			var has_gain := false
			var has_cost := false
			for l in lines:
				has_gain = has_gain or l.begins_with(StoryEngine.GAIN_MARK)
				has_cost = has_cost or l.begins_with(StoryEngine.COST_MARK)
			if not (has_gain and has_cost):
				one_sided.append("%s/%s: %s" % [id, opts[ci]["key"], " ".join(lines)])
			var before := _snapshot(subj)
			GameState.week_events = [card]
			GameState.resolve_card(0, ci)
			var after := _snapshot(subj)
			for e in opts[ci]["effects"]:
				var d := int(e.get("d", 0))
				match str(e["op"]):
					"culture":
						var k: String = str(e["strand"])
						if (int(after[k]) - int(before[k])) * d <= 0:
							wrong.append("%s/%s %s did not move %d" % [id, opts[ci]["key"], k, d])
						clubs_checked += 1
					"running":
						if absf((float(after["run"]) - float(before["run"])) - float(d)) > 0.01 and not (d < 0 and float(after["run"]) == 0.0):
							wrong.append("%s/%s running" % [id, opts[ci]["key"]])
						clubs_checked += 1
					"drill":
						if float(after["drill"]) - float(before["drill"]) != float(d):
							wrong.append("%s/%s drill" % [id, opts[ci]["key"]])
						clubs_checked += 1
					"morale":
						if str(e.get("who", "subject")) == "all" and (int(after["morale"]) - int(before["morale"])) * d <= 0:
							wrong.append("%s/%s morale" % [id, opts[ci]["key"]])
					"trust":
						if (int(after["trust"]) - int(before["trust"])) * d <= 0:
							wrong.append("%s/%s trust" % [id, opts[ci]["key"]])
					"xp":
						if int(after["xp"]) <= int(before["xp"]) and str(e.get("who", "subject")) == "subject":
							pass   # spent at once on his training plan: the rating or the xp moves
	_check(wrong.is_empty(), "Every answer moves what its lines say: %s" % " | ".join(PackedStringArray(wrong.slice(0, 6))))
	_check(clubs_checked >= 14, "...and the strand, running and drilling steps were really exercised (%d)" % clubs_checked)
	_check(lines_missing.is_empty(), "Every answer carries a Gain or Cost line: %s" % " | ".join(PackedStringArray(lines_missing)))
	_check(one_sided.is_empty(), "Every answer on the 11 cards states both a Gain and a Cost: %s" % " | ".join(PackedStringArray(one_sided)))
	# Culture steps land on the culture page with their reason, dated the pre-season.
	_career()
	GameState.preseason_advance()
	GameState.week_events = [GameState.story_card("pre_sim_heated")]
	GameState.resolve_card(0, 1)
	var rs := Culture.reasons(GameState.relations, CLUB, "standards")
	_check(not rs.is_empty() and str(rs[0]["why"]).begins_with("You pulled the group up") and str(rs[0]["w"]) != "",
			"A strand step is logged on the culture page with its reason")
	# The base: Run it out of them lifts the running, Let them enjoy lowers it.
	_career()
	var run0 := float(GameState.preseason["clubs"][CLUB]["run"])
	GameState.preseason_add_running(1.0)
	GameState.preseason_add_running(-9.0)
	_check(float(GameState.preseason["clubs"][CLUB]["run"]) == 0.0 and run0 == 0.0, "Running taken off never goes below nothing")
	# A drilled plan counts when the pre-season ends.
	_career()
	GameState.club_plan = "defensive"
	GameState.preseason_add_drill(3)
	var was := GameState.plan_level(CLUB, "defensive")
	_walk(-1)
	_check(GameState.plan_level(CLUB, "defensive") >= was, "A drill added by a card is counted in with the blocks' when the pre-season ends")


func _snapshot(subj: Dictionary) -> Dictionary:
	var morale := 0
	for p in GameState.my_list:
		morale += ClubLife.morale(p)
	var out := {"standards": Culture.value(GameState.relations, CLUB, "standards"),
			"together": Culture.value(GameState.relations, CLUB, "together"),
			"ambition": Culture.value(GameState.relations, CLUB, "ambition"),
			"run": float(((GameState.preseason.get("clubs", {}) as Dictionary).get(CLUB, {}) as Dictionary).get("run", 0.0)),
			"drill": 0.0, "morale": morale, "trust": 0, "xp": 0}
	for v in (GameState.preseason.get("bonus_drill", {}) as Dictionary).values():
		out["drill"] = float(out["drill"]) + float(v)
	if not subj.is_empty():
		out["trust"] = Trust.value(GameState.relations, Trust.player_key(str(subj["id"])))
		out["xp"] = int(GameState.list_player(str(subj["id"])).get("xp", 0))
	return out


## A player the card could really be about, made so if the list has none.
func _subject_for(id: String) -> Dictionary:
	var p: Dictionary = GameState.my_list[3]
	p["injury_weeks"] = 0
	p.erase("injury_kind")
	match id:
		"pre_contract_talk":
			p["contract_years"] = 1
			p["age"] = 29.0
		"pre_knee_return":
			p["injury_weeks"] = 3
			p["injury_kind"] = "hamstring"
	return p


func _test_facts() -> void:
	_career()
	var p: Dictionary = GameState.my_list[5]
	p["joined"] = GameState.season_year - 1
	_check(bool(ClubStories.player_fact(GameState, p, false, {}, 99, 0)["new_here"]), "A player signed last off-season is new here")
	p["joined"] = GameState.season_year - 4
	p["drafted_year"] = GameState.season_year - 1
	_check(bool(ClubStories.player_fact(GameState, p, false, {}, 99, 0)["new_here"]), "...and so is a draftee of last year")
	p.erase("drafted_year")
	_check(not bool(ClubStories.player_fact(GameState, p, false, {}, 99, 0)["new_here"]), "...but not a player who has been here years")
	GameState.preseason_advance()   # the time trial
	var tr := GameState.preseason_trial()
	var best := str((tr["best"] as Array)[0])
	var last := str((tr["worst"] as Array)[0])
	_check(ClubStories._trial_place(GameState, best) == "best" and ClubStories._trial_place(GameState, last) == "worst"
			and ClubStories._trial_place(GameState, "nobody") == "", "The time trial's front and back are what the cards read")
	# Premiers: the honour roll says so only for last year.
	GameState.honour_roll = [{"year": GameState.season_year - 1, "premier": CLUB, "runner_up": "GEE"}]
	_check(bool(ClubStories.club_facts(GameState, 3, "preseason")["premiers"]), "Won the flag last year is read from the honour roll")
	GameState.honour_roll = [{"year": GameState.season_year - 2, "premier": CLUB, "runner_up": "GEE"}]
	_check(not bool(ClubStories.club_facts(GameState, 3, "preseason")["premiers"]), "...and not a flag from two years ago")
	GameState.honour_roll = [{"year": GameState.season_year - 1, "premier": "GEE", "runner_up": CLUB}]
	_check(not bool(ClubStories.club_facts(GameState, 3, "preseason")["premiers"]), "...nor one the club lost")
	GameState.honour_roll = []
	# The hangover card can only come up for the premiers.
	var t := StoryDeck.by_id(StoryDeck.all(), "pre_flag_hangover")
	var ctx := ClubStories.context(GameState)
	_check(StoryEngine.eligible_subject(t, ctx, GameState.story, 100, RandomNumberGenerator.new()).is_empty(), "The flag card stays away from a club that did not win one")
	(ctx["club"] as Dictionary)["premiers"] = true
	_check(not StoryEngine.eligible_subject(t, ctx, GameState.story, 100, RandomNumberGenerator.new()).is_empty(), "...and is there for the premiers")
	# The running-again card (row 107): written for a knee no pre-season ever had, it now
	# comes up for whatever the physio is managing, the track's own soft-tissue injuries
	# included, and the card names the injury.
	var kt := StoryDeck.by_id(StoryDeck.all(), "pre_knee_return")
	var hurt: Dictionary = GameState.my_list[6]
	for q in GameState.my_list:
		q["injury_weeks"] = 0
		q.erase("injury_kind")
	hurt["injury_weeks"] = 2
	hurt["injury_kind"] = "hamstring"
	var ks := StoryEngine.eligible_subject(kt, ClubStories.context(GameState), GameState.story, 100, RandomNumberGenerator.new())
	_check(str(ks.get("id", "")) == str(hurt["id"]), "The running-again card comes up for a hamstring picked up on the track, not a knee alone")
	var ktext := str(GameState.story_card("pre_knee_return", hurt).get("text", ""))
	_check(ktext.contains(Injuries.wording("hamstring")) and not ktext.contains("knee") and not ktext.contains("{"),
			"...and the card names his injury: %s" % ktext)
	hurt["injury_kind"] = "concussion"
	_check(StoryEngine.eligible_subject(kt, ClubStories.context(GameState), GameState.story, 100, RandomNumberGenerator.new()).is_empty(),
			"...but never a concussion, which no player can be rushed back from")
	hurt["injury_weeks"] = 0
	hurt.erase("injury_kind")
	# Words: nothing in the deck reads as engine talk.
	var bad := []
	for id in IDS:
		var tt := StoryDeck.by_id(StoryDeck.all(), id)
		var blob := JSON.stringify(tt)
		for w in ["XP", "coefficient", "multiplier", "simulation"]:
			if blob.contains(w):
				bad.append("%s says %s" % [id, w])
	_check(bad.is_empty(), "The pre-season cards read as football, not as engine: %s" % " | ".join(PackedStringArray(bad)))


## The running-again card (row 107) in the pre-season's own words: clearing him gains
## the training and the Round 1 he would miss on the physio's plan, on the club's blocks;
## it costs soreness to Round 1 and the Heavy weeks he would have sat out; the physio's
## plan costs that training. A player back next week anyway still brings the card
## (director 2026-11-08: every time), and clearing him says it gains him nothing. In play,
## a Heavy first block hurts players on the track and a story stop deals the card about one.
func _test_running_again() -> void:
	var kt := StoryDeck.by_id(StoryDeck.all(), "pre_knee_return")
	_career()
	GameState.preseason_advance()   # the week 3 stop
	_check(GameState.set_preseason_block(1, "heavy", "skills"), "Weeks 4 to 5 go Heavy")
	for q in GameState.my_list:
		q["injury_weeks"] = 0
		q.erase("injury_kind")
	var p: Dictionary = GameState.my_list[6]
	p["injury_weeks"] = 4
	p["injury_kind"] = "hamstring"
	var b2: Array = GameState.preseason_blocks()[2]
	var want := 2 * PreSeason.week_xp("heavy", "skills") + PreSeason.week_xp(str(b2[0]), str(b2[1]))
	var card := GameState.story_card("pre_knee_return", p)
	var f: Dictionary = card["facts"]
	_check(int(f["pre_miss_xp"]) == want and int(f["pre_miss_heavy"]) == 2 and int(f["pre_miss_rounds"]) == 0,
			"Four weeks out after week 3, he misses weeks 4 to 6: %d XP (want %d), %d Heavy weeks, %d rounds"
			% [int(f["pre_miss_xp"]), want, int(f["pre_miss_heavy"]), int(f["pre_miss_rounds"])])
	var rush := " / ".join(StoryEngine.stakes_lines(card["options"][0]["effects"], f))
	_check(rush.contains("about %d XP of pre-season development" % want) and rush.contains("sore until Round 1")
			and rush.contains("hurt in Round 1 and half that in the pre-season match") and rush.contains("two Heavy weeks")
			and not rush.contains("you name him"), "Clearing him reads as the pre-season: %s" % rush)
	_check(rush.contains("he starts each match"), "...both games, so each match: %s" % rush)
	# After week 7 the pre-season match has been played: Round 1 is all that is left.
	var late := f.duplicate()
	late["pre_week"] = PreSeason.tune("practice_week")
	var last_stop := " / ".join(StoryEngine.stakes_lines(card["options"][0]["effects"], late))
	_check(last_stop.contains("hurt in Round 1 (") and last_stop.contains("he starts it") and not last_stop.contains("pre-season match"),
			"After the pre-season match the odds are for Round 1 alone: %s" % last_stop)
	var physio := " / ".join(StoryEngine.stakes_lines(card["options"][1]["effects"], f))
	_check(physio.contains("goes without about %d XP of pre-season development" % want), "The physio's plan names the training it costs: %s" % physio)
	GameState.week_events = [card]
	var said := GameState.resolve_card(0, 0)
	_check(int(p.get("injury_weeks", 0)) == 0 and bool(p.get("sore", false)) and str(said).contains("trains with the group"),
			"Cleared, he is sore and trains with the group: %s" % said)
	# Out past the pre-season: Round 1 is the gain and the cost.
	p["injury_weeks"] = 8
	p["injury_kind"] = "hamstring"
	p.erase("sore")
	card = GameState.story_card("pre_knee_return", p)
	_check(int(card["facts"]["pre_miss_rounds"]) == 3 and " ".join(StoryEngine.stakes_lines(card["options"][0]["effects"], card["facts"])).contains("right for Round 1")
			and " ".join(StoryEngine.stakes_lines(card["options"][1]["effects"], card["facts"])).contains("still out at Round 1, with three weeks to run"),
			"Eight weeks out, the physio's plan keeps him out of Round 1 and clearing him makes him right for it")
	# Back next week anyway: the card still comes, and clearing him says it gains nothing.
	p["injury_weeks"] = 1
	_check(not StoryEngine.eligible_subject(kt, ClubStories.context(GameState), GameState.story, 100, RandomNumberGenerator.new()).is_empty(),
			"A player back next week anyway still brings the running-again card")
	card = GameState.story_card("pre_knee_return", p)
	var soon := StoryEngine.stakes_lines(card["options"][0]["effects"], card["facts"])
	var soon_blob := " / ".join(soon)
	_check(int(card["facts"]["pre_miss_xp"]) == 0 and int(card["facts"]["pre_miss_rounds"]) == 0
			and _has_gain(soon) and soon_blob.contains("back for next week's training anyway")
			and soon_blob.contains("gains no development and no Round 1 game")
			and not soon_blob.contains("would otherwise miss") and not soon_blob.contains("right for Round 1"),
			"Back next week anyway, clearing him says truthfully it gains little: %s" % soon_blob)
	var soon_physio := StoryEngine.stakes_lines(card["options"][1]["effects"], card["facts"])
	_check(_has_gain(soon_physio) and " / ".join(soon_physio).contains("morale down"),
			"...and the physio's plan still shows a gain and a cost: %s" % " / ".join(soon_physio))
	# A concussion never brings it.
	p["injury_weeks"] = 3
	p["injury_kind"] = "concussion"
	_check(StoryEngine.eligible_subject(kt, ClubStories.context(GameState), GameState.story, 100, RandomNumberGenerator.new()).is_empty(),
			"A concussed player never brings the running-again card")
	p["injury_weeks"] = 0
	p.erase("injury_kind")
	# In play: a Heavy first block, walked stop by stop. Each card stop deals the card for
	# every player who fits and has not had his this pre-season, and for nobody else.
	PreSeason.data()["heavy_week_injury"] = 0.1
	var where: Dictionary = kt["subject"]["where"]
	var hurt_careers := 0
	var dealt := []
	var wrong := []
	for seed in range(SEED, SEED + 10):
		_career(seed)
		for q in GameState.my_list:
			q["injury_weeks"] = 0
			q.erase("injury_kind")
		GameState.set_preseason_block(0, "heavy", "running")
		var guard := 0
		var hurt := {}
		var told := {}
		var seen_week := -1
		while GameState.preseason_active() and guard < 30:
			guard += 1
			var week := GameState.preseason_week()
			if PreSeason.STORY_WEEKS.has(week) and week != seen_week:
				seen_week = week
				for row in GameState.preseason.get("injuries", []):
					if str(row["club"]) == CLUB:
						hurt[str(row["id"])] = true
				var at := "%d@%d" % [seed, week]
				var want := []
				for facts in ClubStories.context(GameState)["players"]:
					if StoryEngine.meets(facts, where, {}) and not told.has(str(facts["id"])):
						want.append(str(facts["id"]))
				var got := []
				for c in GameState.week_events:
					if str(c.get("tid", "")) == "pre_knee_return":
						got.append(str(c["player_id"]))
						told[str(c["player_id"])] = true
						if not hurt.has(str(c["player_id"])):
							wrong.append(at + " not hurt on the track")
				want.sort()
				got.sort()
				if want != got:
					wrong.append("%s wanted %s, dealt %s" % [at, str(want), str(got)])
				if not got.is_empty():
					dealt.append(at)
			GameState.preseason_advance()
		hurt_careers += 1 if not hurt.is_empty() else 0
	PreSeason.reload()
	_check(hurt_careers >= 5, "A Heavy first block hurts players on the track (%d of 10 careers, the risk raised for the test)" % hurt_careers)
	_check(not dealt.is_empty() and wrong.is_empty(),
			"...and each card stop deals the running-again card for every player who fits, nobody else (dealt at %s; wrong: %s)" % [
			", ".join(PackedStringArray(dealt)), ", ".join(PackedStringArray(wrong))])


## The running-again card comes every time (director 2026-11-08): no quiet roll, no draw
## against the other cards, no full category and no recent card about him holds it back.
## One for each player who fits, once each a season.
func _test_running_again_comes() -> void:
	_career()
	for q in GameState.my_list:
		q["injury_weeks"] = 0
		q.erase("injury_kind")
	var deck := StoryDeck.all()
	var hurt: Dictionary = GameState.my_list[6]
	hurt["injury_weeks"] = 3
	hurt["injury_kind"] = "hamstring"
	var ctx := ClubStories.context(GameState)
	var w := StoryEngine.week_abs(int(ctx["year"]), int(ctx["week"]))
	var missed := []
	var quiet := 0
	for seed in range(40):
		ctx["seed"] = seed
		var roll := RandomNumberGenerator.new()
		roll.seed = hash("story|%d|%d|%d" % [seed, int(ctx["year"]), int(ctx["week"])])
		quiet += 1 if roll.randf() >= StoryEngine.EVENT_CHANCE else 0
		var story := StoryEngine.ensure({})
		# A full health category and a card about him last week would hold back a drawn card.
		for i in range(StoryEngine.DIVERSITY_MAX):
			(story["cats"] as Array).append([w, "health"])
		story["subj"][str(hurt["id"])] = w
		var cards := StoryEngine.pick_week(deck, ctx, story)
		if cards.size() != 1 or str(cards[0]["tid"]) != "pre_knee_return" or str(cards[0]["player_id"]) != str(hurt["id"]):
			missed.append(seed)
	_check(quiet >= 5 and missed.is_empty(), "It comes at every stop he fits, %d quiet weeks among 40 included (missed: %s)" % [quiet, str(missed)])

	var story := StoryEngine.ensure({})
	var second: Dictionary = GameState.my_list[7]
	second["injury_weeks"] = 2
	second["injury_kind"] = "calf"
	ctx = ClubStories.context(GameState)
	var ids := []
	for c in StoryEngine.pick_week(deck, ctx, story):
		ids.append(str(c.get("player_id", "")) if str(c["tid"]) == "pre_knee_return" else "other")
	ids.sort()
	var both := [str(hurt["id"]), str(second["id"])]
	both.sort()
	_check(ids == both, "Two players the physio has at one stop get a card each, and nothing else that stop (%s)" % str(ids))
	ctx["week"] = int(ctx["week"]) + 1
	var again := StoryEngine.pick_week(deck, ctx, story).filter(func(c): return str(c["tid"]) == "pre_knee_return")
	_check(again.is_empty(), "He does not bring it twice in a pre-season")
	StoryEngine.new_season(story)
	ctx["year"] = int(ctx["year"]) + 1
	var next := StoryEngine.pick_week(deck, ctx, story).filter(func(c): return str(c["tid"]) == "pre_knee_return")
	_check(next.size() == 2, "Hurt again next pre-season, it comes again (%d cards)" % next.size())
	hurt["injury_weeks"] = 0
	hurt.erase("injury_kind")
	second["injury_weeks"] = 0
	second.erase("injury_kind")
	var t: Dictionary = (StoryDeck.by_id(deck, "pre_knee_return") as Dictionary).duplicate(true)
	t["subject"] = {"kind": "club"}
	_check(StoryDeck.validate([t]).any(func(x): return str(x).contains("always comes")), "A card that always comes must be about a player")


func _test_hands_off_and_save() -> void:
	_career(SEED + 3)
	var round1 := _ids(GameState.week_events)
	GameState.preseason_sim_to_round1()
	_check(not GameState.preseason_active() and _ids(GameState.week_events) == round1,
			"Sim to Round 1 stops for no card, and Round 1's cards are exactly what they were")
	# A save made while a card is waiting reloads with it waiting.
	var found := false
	for seed in range(SEED, SEED + 20):
		_career(seed)
		var guard := 0
		while GameState.preseason_active() and GameState.preseason_stop() != "story" and guard < 10:
			guard += 1
			GameState.preseason_advance()
		if GameState.preseason_stop() == "story":
			found = true
			var tid := str(GameState.week_events[0]["tid"])
			var week := GameState.preseason_week()
			_check(GameState.save_career() and GameState.load_career(), "A career saved at a card stop saves and loads")
			_check(GameState.preseason_stop() == "story" and GameState.preseason_week() == week
					and str(GameState.week_events[0]["tid"]) == tid and GameState.preseason.has("round1"),
					"...and is still at that card, with Round 1's cards still waiting aside")
			GameState.resolve_week_event(0)
			GameState.preseason_advance()
			break
	_check(found, "A card stop turned up in twenty careers to save at")
	GameState.delete_saved_career()


func _has_gain(lines: PackedStringArray) -> bool:
	for l in lines:
		if str(l).begins_with(StoryEngine.GAIN_MARK):
			return true
	return false
