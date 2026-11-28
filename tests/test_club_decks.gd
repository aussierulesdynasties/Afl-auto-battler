extends RefCounted
## Each club's own deck of event cards (TODO row 157): about 25 cards for every
## club, the Brisbane Bears, Fitzroy, Tasmania and Canberra included; each card
## valid, every choice with a gain and a cost, drawn only for its own club, a
## controversy only with the switch on, and every choice playable. Run through
## tests/run_club_decks_tests.gd.

var failures: Array[String] = []
var checks := 0

const SUITE_SEED := 157
## "25ish cards for each club" (director 2026-11-11).
const DECK_MIN := 23
const DECK_MAX := 28


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	GameDB.reload()
	StoryDeck.reload()
	_t("_test_every_club_has_its_deck")
	_t("_test_cards_are_valid")
	_t("_test_every_choice_has_gain_and_cost")
	_t("_test_era_agnostic")
	_t("_test_drawn_for_its_club_only")
	_t("_test_controversy_switch")
	_t("_test_bears_draw_their_own_deck")
	_t("_test_odds_roll")
	_t("_test_every_choice_plays")
	print(Ran.line("Club decks", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _deck(code: String) -> Array:
	return StoryDeck.load_file("%s%s.json" % [StoryDeck.CLUBS_DIR, code.to_lower()])


func _test_every_club_has_its_deck() -> void:
	for code in StoryDeck.CLUB_DECKS:
		var deck := _deck(str(code))
		_check(deck.size() >= DECK_MIN and deck.size() <= DECK_MAX,
				"%s has about 25 cards of its own (%d)" % [code, deck.size()])
		for t in deck:
			_check(str(t.get("club", "")) == str(code), "%s is in %s's file and names that deck" % [t["id"], code])
			_check(str(t["id"]).begins_with(str(code).to_lower() + "_"), "%s's id starts with its deck" % t["id"])
	# Every club the game can field, past and future, has a deck.
	for code in GameDB.CLUB_ORDER + GameDB.PAST_CLUBS.keys():
		_check(StoryDeck.CLUB_DECKS.has(ClubStories.deck_code(str(code))), "%s has a deck" % code)


func _test_cards_are_valid() -> void:
	var errs := StoryDeck.validate(StoryDeck.all())
	_check(errs.is_empty(), "Every card, club decks included, passes the deck checks: %s" % "; ".join(PackedStringArray(errs)))
	# The checks catch a club card's own faults.
	var bad := StoryDeck.normalise({"id": "x_bad", "club": "XYZ", "category": "board", "title": ["t"], "text": ["t"],
			"choices": [{"key": "a", "label": "A", "effects": [{"op": "odds", "chance": 99, "hit": [{"op": "board", "d": 2}]}]},
				{"key": "b", "label": "B", "effects": [{"op": "odds", "chance": 50, "hit": [{"op": "odds", "chance": 50}]}]}]})
	var said := " ".join(PackedStringArray(StoryDeck.validate([bad])))
	_check(said.contains("unknown club deck"), "An unknown deck is caught: %s" % said)
	_check(said.contains("odds of 99"), "Odds outside 5..95 are caught")
	_check(said.contains("cannot roll"), "A roll inside a roll is caught")
	var loose := StoryDeck.normalise({"id": "y", "controversy": true, "category": "board", "title": ["t"], "text": ["t"],
			"choices": [{"key": "a", "label": "A"}, {"key": "b", "label": "B"}]})
	_check(" ".join(PackedStringArray(StoryDeck.validate([loose]))).contains("Controversies switch"),
			"Only a club deck's card can sit behind the Controversies switch")


## Every option carries a positive and a negative (bible, principle 4), from
## its own effects, as the card prints them.
func _test_every_choice_has_gain_and_cost() -> void:
	for t in StoryDeck.club_decks():
		for c in t["choices"]:
			var lines := StoryEngine.stakes_lines(c.get("effects", []), {})
			var joined := "\n".join(lines)
			_check(joined.contains(StoryEngine.GAIN_MARK) and joined.contains(StoryEngine.COST_MARK),
					"%s/%s states a gain and a cost: %s" % [t["id"], c["key"], joined])


## No club card depends on a year (director 2026-11-11: "club decks should be era agnostic").
func _test_era_agnostic() -> void:
	var year := RegEx.create_from_string("\\b(19|20)\\d\\d\\b")
	for t in StoryDeck.club_decks():
		var words := " ".join(PackedStringArray(t["title"] + t["text"]))
		for c in t["choices"]:
			words += " %s %s" % [c.get("label", ""), c.get("result", "")]
		_check(year.search(words) == null, "%s names no year" % t["id"])
		_check(not (t.get("when", {}) as Dictionary).has("year") and not (t.get("when", {}) as Dictionary).has("year_min")
				and not (t.get("when", {}) as Dictionary).has("year_max"), "%s waits for no year" % t["id"])


func _ctx(deck: String, controversies := 1) -> Dictionary:
	return {"seed": 1, "year": 2026, "week": 5, "phase": "regular",
			"club": {"club_deck": deck, "opp_deck": "", "controversies": controversies, "round": 5}, "players": []}


func _can_draw(t: Dictionary, ctx: Dictionary) -> bool:
	var rng := RandomNumberGenerator.new()
	var subj := StoryEngine.eligible_subject(t, ctx, StoryEngine.new_state(), 100, rng)
	return not subj.is_empty()


func _plain(code: String) -> Dictionary:
	for t in _deck(code):
		if (t.get("when", {}) as Dictionary).is_empty() and not bool(t.get("controversy", false)) \
				and str(t["subject"].get("kind", "club")) == "club" and (t["phase"] as Array).has("regular"):
			return t
	return {}


func _test_drawn_for_its_club_only() -> void:
	for code in StoryDeck.CLUB_DECKS:
		var t := _plain(str(code))
		_check(not t.is_empty(), "%s has a plain regular-season club card" % code)
		if t.is_empty():
			continue
		_check(_can_draw(t, _ctx(str(code))), "%s comes up for %s" % [t["id"], code])
		var other := "GEE" if str(code) != "GEE" else "HAW"
		_check(not _can_draw(t, _ctx(other)), "%s never comes up for %s" % [t["id"], other])


func _test_controversy_switch() -> void:
	var n := 0
	for t in StoryDeck.club_decks():
		if not bool(t.get("controversy", false)) or not (t["phase"] as Array).has("regular") \
				or not (t.get("when", {}) as Dictionary).is_empty() or str(t["subject"].get("kind", "club")) != "club":
			continue
		n += 1
		_check(_can_draw(t, _ctx(str(t["club"]), 1)), "%s comes up with Controversies on" % t["id"])
		_check(not _can_draw(t, _ctx(str(t["club"]), 0)), "%s never comes up with Controversies off" % t["id"])
	_check(n > 0, "Some club cards sit behind the Controversies switch (%d)" % n)


## The Brisbane club draws the Bears' deck while it plays as the Bears, the Lions' after.
func _test_bears_draw_their_own_deck() -> void:
	GameDB.apply_era(1993)
	_check(ClubStories.deck_code("BRL") == "BRB", "Brisbane in 1993 draws the Bears' deck (%s)" % ClubStories.deck_code("BRL"))
	_check(ClubStories.deck_code("BRB") == "BRB", "The Bears' own code draws the Bears' deck")
	GameDB.apply_era(2026)
	_check(ClubStories.deck_code("BRL") == "BRL", "Brisbane in 2026 draws the Lions' deck")
	_check(ClubStories.deck_code("FOO") == "WBD", "Footscray draws the Bulldogs' deck")
	_check(ClubStories.deck_code("FIT") == "FIT", "Fitzroy draws its own deck")


## A rolled outcome says its odds both ways, and lands one way, the same way for the same save.
func _test_odds_roll() -> void:
	var e := {"op": "odds", "chance": 60, "hit": [{"op": "board", "d": 4}], "miss": [{"op": "board", "d": -3}]}
	var lines := "\n".join(StoryEngine.stakes_lines([e], {}))
	_check(lines.contains("60% chance") and lines.contains("40% chance"), "The roll prints both odds: %s" % lines)
	_check(lines.contains(StoryEngine.GAIN_MARK) and lines.contains(StoryEngine.COST_MARK), "The roll is a gain one way and a cost the other")
	GameState.reset()
	GameState.replay_seed = SUITE_SEED
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var facts := {"_tid": "odds_test", "year": 2026, "round": 3}
	var before := GameState.board_confidence()
	ClubStories._apply(GameState, e, {}, facts, {})
	var moved := GameState.board_confidence() - before
	_check(moved == 4 or moved == -3, "The roll lands one way (%d)" % moved)
	var again := GameState.board_confidence()
	ClubStories._apply(GameState, e, {}, facts, {})
	_check(GameState.board_confidence() - again == moved, "The same save rolls the same way")
	var rolls := 0
	for t in StoryDeck.club_decks():
		for c in t["choices"]:
			for ef in c.get("effects", []):
				if str(ef.get("op", "")) == "odds":
					rolls += 1
	_check(rolls > 0, "Club cards roll odds where the draft named them (%d)" % rolls)


## Every choice of every club card plays through the game without a fault.
func _test_every_choice_plays() -> void:
	GameState.reset()
	GameState.replay_seed = SUITE_SEED
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var p: Dictionary = GameState.my_list[3]
	for t in StoryDeck.club_decks():
		var player := str(t["subject"].get("kind", "club")) == "player"
		for i in range((t["choices"] as Array).size()):
			var card := GameState.story_card(str(t["id"]), p if player else {})
			_check(not card.is_empty(), "%s builds" % t["id"])
			if card.is_empty():
				break
			var shown := "%s %s" % [card["title"], card["text"]]
			_check(not shown.contains("{"), "%s fills every placeholder: %s" % [t["id"], shown])
			for o in card["options"]:
				_check(not str(o["detail"]).contains("{") and str(o["detail"]) != "",
						"%s/%s says what it does: %s" % [t["id"], o["key"], o["detail"]])
			GameState.week_event = card
			var out = GameState.resolve_week_event(i)
			_check(str(out) != "" and not str(out).contains("{"), "%s/%d plays: %s" % [t["id"], i, str(out)])
