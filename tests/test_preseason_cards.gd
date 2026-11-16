extends RefCounted
## The bonding deck (rule 69a): a Team bonding week deals one card from the nine
## in data/stories/bonding.json. Each card has a small choice (a gain alone) and
## a big one (a gain and a cost), and every answer does what its lines say. The
## card stops the pre-season after its week, Round 1's own cards wait aside and
## come back, the cultural day comes only to a club with an Indigenous player,
## a rival's bonding week rolls a card of its own, Sim to Round 1 stops for
## nothing, and a save made at the card reloads at it. Part of the story suite
## (tests/test_story.gd calls run()).

var s   # the story suite: _check()

const Press := preload("res://tests/preseason_press.gd")
const SEED := 6113
const CLUB := "FRE"
const IDS := ["bond_away_camp", "bond_talent_quest", "bond_community_week", "bond_beach_day", "bond_cultural_day",
		"bond_leadership_workshop", "bond_families_day", "pre_leaders_vote", "pre_sim_heated"]
## The old pre-season cards the nine replaced (director, rule 69a).
const GONE := ["pre_recruit_behind", "pre_contract_talk", "pre_bulking_up", "pre_camp", "pre_knee_return",
		"pre_flag_hangover", "pre_kid_flying", "pre_star_last", "pre_members_open"]


func run(suite) -> void:
	s = suite
	var before: int = s.checks
	PreSeason.reload()
	_t("_test_deck")
	_t("_test_flow")
	_t("_test_effects")
	_t("_test_cultural_day")
	_t("_test_rivals")
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


## Past the meetings and the fitness plan (Develop: two weeks of running), to
## the first week waiting on its action.
func _to_week() -> void:
	GameState.preseason_meetings_done()
	GameState.set_preseason_plan("develop")
	Press.to("week")


## One week on Team bonding: the week is trained and its card is dealt.
func _bond_week() -> void:
	Press.to("week")
	GameState.set_preseason_action("bond")
	GameState.preseason_advance()


func _test_deck() -> void:
	StoryDeck.reload()
	var deck := StoryDeck.all()
	_check(StoryDeck.validate(deck).is_empty(), "The deck with the bonding cards in it still validates: %s" % " | ".join(PackedStringArray(StoryDeck.validate(deck).slice(0, 4))))
	var bonding := []
	for t in deck:
		if (t.get("phase", []) as Array).has("bonding") and str(t.get("club", "")) == "":
			bonding.append(str(t["id"]))
	bonding.sort()
	var want := IDS.duplicate()
	want.sort()
	_check(bonding == want, "The bonding deck is the nine approved cards: %s" % ", ".join(PackedStringArray(bonding)))
	var gone := GONE.filter(func(id): return not StoryDeck.by_id(deck, id).is_empty())
	_check(gone.is_empty(), "The old pre-season cards are out of the deck: %s" % ", ".join(PackedStringArray(gone)))
	var only := true
	for id in IDS:
		only = only and (StoryDeck.by_id(deck, id).get("phase", []) as Array) == ["bonding"]
	_check(only, "A bonding card comes only in a bonding week, never in the season")
	# The clubs' own summer cards became bonding cards ("Keep fitting ones"): no
	# club card is left in the old pre-season phase, and each has a small choice
	# (gain alone) and a big one (gain and a cost), with no running, loads or XP.
	var club_wrong := []
	var club_cards := 0
	for t in deck:
		var club := str(t.get("club", ""))
		var phase: Array = t.get("phase", [])
		if club == "":
			continue
		if phase.has("preseason"):
			club_wrong.append("%s still in the old pre-season" % t["id"])
		if not phase.has("bonding"):
			continue
		club_cards += 1
		var small := 0
		var big := 0
		for c in (t.get("choices", []) as Array):
			var cost := false
			for e in (c.get("effects", []) as Array):
				var op := str(e.get("op", ""))
				if op in ["xp", "forgo_xp", "running", "heavy_legs", "fresh"]:
					club_wrong.append("%s uses %s" % [t["id"], op])
				cost = cost or op in ["sore", "loss_sting", "slow_start"] or int(e.get("d", 0)) < 0
			big += 1 if cost else 0
			small += 0 if cost else 1
		if (t.get("choices", []) as Array).size() != 2 or small != 1 or big != 1:
			club_wrong.append("%s (%d small, %d big)" % [t["id"], small, big])
	_check(club_cards == 58 and club_wrong.is_empty(),
			"The 58 club cards are bonding cards with a small and a big choice (%d): %s" % [club_cards, " | ".join(PackedStringArray(club_wrong))])
	# A small choice and a big one: one answer is a gain alone, the other a gain
	# and a cost (rule 69a).
	_career()
	_to_week()
	_bond_week()
	for q in GameState.my_list.slice(0, 2):
		q["indigenous"] = true
	var wrong := []
	for id in IDS:
		var card := GameState.story_card(id)
		var opts: Array = card["options"]
		var gain_only := 0
		var gain_cost := 0
		for o in opts:
			var lines := StoryEngine.stakes_lines(o["effects"], card["facts"])
			var gain := _has(lines, StoryEngine.GAIN_MARK)
			var cost := _has(lines, StoryEngine.COST_MARK)
			gain_only += 1 if gain and not cost else 0
			gain_cost += 1 if gain and cost else 0
		if opts.size() != 2 or gain_only != 1 or gain_cost != 1:
			wrong.append("%s (%d choices, %d gain alone, %d gain and cost)" % [id, opts.size(), gain_only, gain_cost])
	_check(wrong.is_empty(), "Every card has a small choice (a gain alone) and a big one (a gain and a cost): %s" % " | ".join(PackedStringArray(wrong)))


## A bonding week deals one card and stops after it; another action deals none.
func _test_flow() -> void:
	_career()
	var round1 := _ids(GameState.week_events)
	_to_week()
	Press.to("week")
	GameState.set_preseason_action("run")
	GameState.preseason_advance()
	_check(GameState.preseason_stop() != "story", "A running week deals no card")
	_bond_week()
	_check(GameState.preseason_stop() == "story" and GameState.week_events.size() == 1,
			"A bonding week stops on one card (stop %s, %d cards)" % [GameState.preseason_stop(), GameState.week_events.size()])
	var tid := str(GameState.week_events[0]["tid"]) if not GameState.week_events.is_empty() else ""
	var dealt := StoryDeck.by_id(StoryDeck.all(), tid)
	_check(IDS.has(tid) or (str(dealt.get("club", "")) == CLUB and (dealt.get("phase", []) as Array).has("bonding")),
			"...a card from the bonding deck or the club's own (%s)" % tid)
	var acts: Array = GameState.preseason_entry().get("acts", [])
	_check(not acts.is_empty() and str((acts[acts.size() - 1] as Dictionary).get("card", "")) == tid,
			"...and the week records the card it dealt")
	GameState.resolve_card(0, 0)
	GameState.preseason_advance()
	_check(GameState.preseason_stop() != "story" and _ids(GameState.week_events) == round1,
			"Pressing on brings Round 1's own cards back as they were")
	# A second bonding week deals a card not had this pre-season.
	_bond_week()
	var tid2 := str(GameState.week_events[0]["tid"]) if GameState.preseason_stop() == "story" else ""
	_check(tid2 != "" and tid2 != tid, "A second bonding week deals another card (%s, then %s)" % [tid, tid2])
	# Unanswered: the stop settles and the pre-season finishes.
	var guard := 0
	while GameState.preseason_active() and guard < 30:
		guard += 1
		Press.advance()
	_check(not GameState.preseason_active() and _ids(GameState.week_events) == round1,
			"Pressing on past a card leaves it unanswered and the pre-season finishes")
	# Determinism.
	var a := _bond_run(SEED + 2)
	var b := _bond_run(SEED + 2)
	_check(a == b and a.size() == 3, "The same save deals the same cards in the same weeks: %s" % str(a))


## Three bonding weeks in a row from week 1, the cards dealt.
func _bond_run(seed: int) -> Array:
	_career(seed)
	_to_week()
	var out := []
	for i in range(3):
		_bond_week()
		if GameState.preseason_stop() == "story":
			out.append([GameState.preseason_week(), _ids(GameState.week_events)])
			GameState.resolve_card(0, 1)
		if GameState.preseason_stop() == "story":
			GameState.preseason_advance()
	return out


## Every answer does what its lines say: the strands, morale, the board, trust
## and a sore player.
func _test_effects() -> void:
	var wrong := []
	var moved := 0
	for id in IDS:
		for ci in range(2):
			_career()
			_to_week()
			_bond_week()
			for q in GameState.my_list.slice(0, 3):
				q["indigenous"] = true
			GameState.board["confidence"] = 50
			var card := GameState.story_card(id)
			var opts: Array = card["options"]
			var before := _snapshot()
			GameState.week_events = [card]
			GameState.resolve_card(0, ci)
			var after := _snapshot()
			for e in opts[ci]["effects"]:
				var d := int(e.get("d", 0))
				var who := str(e.get("who", ""))
				var op := str(e["op"])
				var k := str(e.get("strand", "")) if op == "culture" else op + ("_" + who if who != "" else "")
				if op == "sore":
					if int(after["sore"]) <= int(before["sore"]):
						wrong.append("%s/%s sore" % [id, opts[ci]["key"]])
				elif not before.has(k):
					wrong.append("%s/%s %s not measured" % [id, opts[ci]["key"], k])
				elif (int(after[k]) - int(before[k])) * d <= 0:
					wrong.append("%s/%s %s did not move %d" % [id, opts[ci]["key"], k, d])
				moved += 1
	_check(wrong.is_empty(), "Every answer moves what its lines say: %s" % " | ".join(PackedStringArray(wrong.slice(0, 6))))
	_check(moved >= 30, "...and every effect on the nine cards was exercised (%d)" % moved)
	# Culture steps land on the culture page with their reason.
	_career()
	_to_week()
	_bond_week()
	GameState.week_events = [GameState.story_card("pre_sim_heated")]
	GameState.resolve_card(0, 0)
	var rs := Culture.reasons(GameState.relations, CLUB, "standards")
	_check(not rs.is_empty() and str(rs[0]["why"]).begins_with("You pulled the group up"),
			"A strand step is logged on the culture page with its reason")


func _snapshot() -> Dictionary:
	var lead := ClubStories.leader_ids(GameState, CLUB, GameState.my_list)
	var out := {"standards": Culture.value(GameState.relations, CLUB, "standards"),
			"together": Culture.value(GameState.relations, CLUB, "together"),
			"ambition": Culture.value(GameState.relations, CLUB, "ambition"),
			"board": GameState.board_confidence(), "morale_all": 0, "morale_rest": 0,
			"trust_leaders": 0, "trust_indigenous": 0, "sore": 0}
	for p in GameState.my_list:
		var id := str(p["id"])
		out["morale_all"] += ClubLife.morale(p)
		if not lead.has(id):
			out["morale_rest"] += ClubLife.morale(p)
		else:
			out["trust_leaders"] += Trust.value(GameState.relations, Trust.player_key(id))
		if bool(p.get("indigenous", false)):
			out["trust_indigenous"] += Trust.value(GameState.relations, Trust.player_key(id))
		out["sore"] += 1 if bool(p.get("sore", false)) else 0
	return out


## "if a club has no indigenous players then the card shouldnt appear"
## (director, 2026-11-17): yours and a rival's.
func _test_cultural_day() -> void:
	_career()
	_to_week()
	var t := StoryDeck.by_id(StoryDeck.all(), "bond_cultural_day")
	for q in GameState.my_list:
		q["indigenous"] = false
	var facts := ClubStories.club_facts(GameState, 0, "bonding")
	_check(not StoryEngine.meets(facts, t.get("when", {}), {}), "With no Indigenous player on our list, the cultural day cannot come")
	GameState.my_list[4]["indigenous"] = true
	facts = ClubStories.club_facts(GameState, 0, "bonding")
	_check(StoryEngine.meets(facts, t.get("when", {}), {}), "...and with one it can")
	var rival := ""
	for c in GameState.season.clubs:
		if str(c) != CLUB:
			rival = str(c)
			break
	for q in GameState.season.lists[rival]:
		q["indigenous"] = false
	var dealt := {}
	for w in range(1, 8):
		dealt[ClubStories.rival_bond(GameState, rival, w)] = true
	_check(not dealt.has("bond_cultural_day") and dealt.size() > 1,
			"A rival with no Indigenous player never draws the cultural day (%s)" % ", ".join(PackedStringArray(dealt.keys())))
	# A rival draws from the shared deck and its own club cards, never another
	# club's, and never one about a named player (that needs your club's facts).
	var deck := StoryDeck.all()
	var own_seen := false
	var wrong := []
	for code in GameState.season.clubs:
		if str(code) == CLUB:
			continue
		for w in range(1, 8):
			var t := StoryDeck.by_id(deck, ClubStories.rival_bond(GameState, str(code), w))
			var club := str(t.get("club", ""))
			own_seen = own_seen or club == str(code)
			if club != "" and (club != str(code) or str((t.get("subject", {}) as Dictionary).get("kind", "club")) != "club"):
				wrong.append("%s drew %s" % [code, t["id"]])
	_check(own_seen and wrong.is_empty(), "Rivals draw their own club's cards, never another club's or a named player's: %s" % " | ".join(PackedStringArray(wrong)))


## "Drill, then bond": a rival's bonding week rolls a card of its own, the same
## card on the same save.
func _test_rivals() -> void:
	var runs := []
	for i in range(2):
		_career(SEED + 5)
		var guard := 0
		while GameState.preseason_active() and guard < 40:
			guard += 1
			Press.advance()
		var cards := {}
		var bonds := 0
		for c in GameState.season.clubs:
			if str(c) == CLUB:
				continue
			var acts: Array = (GameState.preseason.get("clubs", {}) as Dictionary).get(str(c), {}).get("acts", [])
			for wk in acts:
				if str((wk as Dictionary).get("a", "")) == "bond":
					bonds += 1
					cards["%s|%s" % [c, (wk as Dictionary).get("card", "")]] = true
		runs.append([bonds, cards.keys()])
	var bonds_seen := int(runs[0][0])
	var no_card := (runs[0][1] as Array).filter(func(k): return str(k).ends_with("|"))
	_check(bonds_seen > 0, "Rivals take bonding weeks (%d across the league)" % bonds_seen)
	_check(no_card.is_empty(), "...and each rival bonding week records the card it rolled: %s" % ", ".join(PackedStringArray(no_card.slice(0, 4))))
	_check(JSON.stringify(runs[0]) == JSON.stringify(runs[1]), "The same save rolls the same cards for the rivals")


func _test_hands_off_and_save() -> void:
	_career(SEED + 3)
	var round1 := _ids(GameState.week_events)
	GameState.preseason_sim_to_round1()
	_check(not GameState.preseason_active() and _ids(GameState.week_events) == round1,
			"Sim to Round 1 stops for no card, and Round 1's cards are exactly what they were")
	# A save made while a card is waiting reloads with it waiting.
	_career(SEED)
	_to_week()
	_bond_week()
	_check(GameState.preseason_stop() == "story", "(setup) a bonding card waits")
	var tid := str(GameState.week_events[0]["tid"])
	var week := GameState.preseason_week()
	_check(GameState.save_career() and GameState.load_career(), "A career saved at a card stop saves and loads")
	_check(GameState.preseason_stop() == "story" and GameState.preseason_week() == week
			and str(GameState.week_events[0]["tid"]) == tid and GameState.preseason.has("round1"),
			"...and is still at that card, with Round 1's cards still waiting aside")
	GameState.delete_saved_career()


func _has(lines: PackedStringArray, mark: String) -> bool:
	for l in lines:
		if str(l).begins_with(mark):
			return true
	return false
