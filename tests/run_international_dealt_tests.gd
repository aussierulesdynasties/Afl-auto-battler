extends SceneTree
## godot --headless --path . --script tests/run_international_dealt_tests.gd
## An international's first season brings his own story cards, dealt by the
## game (director 2026-11-11: a story that can never fire is a bug). Seeded
## careers: Fremantle drafts an international, the next home-and-away season is
## played week by week, and the week's dealer (GameState's own, never this
## test) draws at least one of his international cards in most careers.
## Before the fix another card was about him every 8 to 10 weeks and his own
## cards waited 12 weeks after any card about him, so none ever came.
##
## INTL_CAREERS=<n> plays more careers; INTL_REPORT=1 prints what held his
## cards back each week (the measurement behind the rule).

const SUITE_SEED := 2027
## Careers played, seeds SUITE_SEED, SUITE_SEED + 1, ...
const CAREERS := 20
## Of those, how many must see one of his international cards dealt.
const NEED := 4

var _state: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://test_international_dealt.save"
	_state.settings_path = "user://test_international_dealt.cfg"
	_state.delete_saved_career()
	await _t("_test_the_dealer_draws_his_cards")
	_state.delete_saved_career()
	print(Ran.line("International dealt", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


## Fremantle drafts an international prospect from the first class and the
## career rolls into the next season with him on the list. Returns his id.
func _draft_an_international(career_seed: int) -> String:
	_state.reset()
	_state.career_seed = career_seed
	_state.replay_seed = career_seed
	_state.start_season("FRE", _db.club_list("FRE"))
	_state.tutorials = false
	_state.season.round_index = _state.season.fixture.size()
	_state.open_offseason()
	# A full list passes its picks: the coach makes room, as a coach would.
	var spare: Dictionary = _state.my_list[0]
	for p in _state.my_list:
		if int(p["overall"]) < int(spare["overall"]):
			spare = p
	_state.release_player(str(spare["id"]))
	if not _state.begin_intake_draft():
		return ""
	var draft: Object = _state.draft
	var mine := ""
	var guard := 0
	while not draft.is_finished() and guard < 2000:
		guard += 1
		var code: String = draft.current_club()
		var pick := {}
		if code == "FRE" and mine == "":
			for q in draft.pool:
				if q.has("intl") and not draft.picked.has(str(q["id"])):
					pick = q
					break
		if pick.is_empty():
			pick = draft._best_ai_pick(code)
		if pick.is_empty() or not draft._draft_pick(code, pick):
			draft._skip_current_pick()
		elif code == "FRE" and pick.has("intl"):
			mine = str(pick["id"])
	if mine == "" or not _state.finish_intake_draft():
		return ""
	return mine if not _state.list_player(mine).is_empty() else ""


## Why each of his international cards could not come this week, on the
## story's memory from before the week's draw: one word per card.
func _held(engine: GDScript, deck: Array, ctx: Dictionary, before: Dictionary, pid: String, w: int) -> Dictionary:
	var facts := {}
	for f in ctx["players"]:
		if str(f["id"]) == pid:
			facts = f
	var out := {}
	var rng := RandomNumberGenerator.new()
	for t in deck:
		var id := str(t["id"])
		if not id.begins_with("intl_"):
			continue
		var why := "free"
		if facts.is_empty() or not (t.get("phase", ["regular"]) as Array).has(str(ctx["phase"])) \
				or not engine.meets(ctx["club"], t.get("when", {}), {}) \
				or not engine.meets(facts, (t["subject"] as Dictionary).get("where", {}), {}):
			why = "moment"
		elif int(before["season"].get(id, 0)) >= maxi(1, int(t.get("per_season", 0))):
			why = "had"
		elif engine.category_count(before, str(t["category"]), w) >= engine.DIVERSITY_MAX and not bool(t.get("priority", false)):
			why = "category"
		else:
			var one := {"seed": ctx["seed"], "year": ctx["year"], "week": ctx["week"], "phase": ctx["phase"],
					"big": false, "club": ctx["club"], "players": [facts]}
			if (engine.eligible_subject(t, one, before, w, rng) as Dictionary).is_empty():
				why = "wait"
		out[id] = why
	return out


func _test_the_dealer_draws_his_cards() -> void:
	var engine: GDScript = load("res://scripts/sim/StoryEngine.gd")
	var stories: GDScript = load("res://scripts/state/ClubStories.gd")
	var deck: Array = (load("res://scripts/sim/StoryDeck.gd") as GDScript).all()
	var careers := maxi(CAREERS, int(OS.get_environment("INTL_CAREERS")))
	var drafted := 0
	var with_card := 0
	var crowded := 0
	var tally := {}
	for n in range(careers):
		var career_seed := SUITE_SEED + n
		var pid := _draft_an_international(career_seed)
		if pid == "":
			print("INTL dealt: seed %d, no international drafted" % career_seed)
			continue
		drafted += 1
		if _state.needs_season_wrap():
			_state.begin_season_from_wrap()
		var guard := 0
		var his := []       # his international cards, as "round:tid"
		var others := []    # every other card about him
		var trail := []     # each week: what held his cards, and played weeks since a card was about him
		while stories.phase(_state) != "regular" and guard < 6:
			guard += 1
			_state.advance()
			for c in _state.week_events:
				if str(c.get("player_id", "")) == pid:
					others.append("pre:%s" % str(c.get("tid", c.get("key", "?"))))
		var weeks := {}     # why his cards were held, counted by week
		var last_his: int = engine.NEVER   # the week of his last international card
		while _state.season != null and not _state.season.is_regular_done() and guard < 60:
			guard += 1
			var before: Dictionary = (_state.story as Dictionary).duplicate(true)
			_state.skip_media_conference()
			_state.advance()
			if stories.phase(_state) != "regular":
				break
			var ctx: Dictionary = stories.context(_state)
			var w: int = _state.story_week()
			var round_no := int((ctx["club"] as Dictionary).get("round", 0))
			var dealt_his := false
			var since: int = engine.played_between(int(before["subj"].get(pid, engine.NEVER)), w)
			for c in _state.week_events:
				if str(c.get("player_id", "")) != pid:
					continue
				if str(c.get("tid", "")).begins_with("intl_"):
					his.append("%d:%s" % [round_no, c["tid"]])
					# His card keeps its distance: a month from any card about him, twelve weeks from his last.
					if dealt_his or since < int(engine.SERIES_GAP) or engine.played_between(last_his, w) < 12:
						crowded += 1
					dealt_his = true
					last_his = w
				else:
					others.append("%d:%s" % [round_no, c.get("tid", c.get("key", "?"))])
			var held := _held(engine, deck, ctx, before, pid, w)
			var word := "moment"
			for k in ["free", "wait", "category", "had"]:
				if held.values().has(k):
					word = k
					break
			if dealt_his:
				word = "dealt"
			weeks[word] = int(weeks.get(word, 0)) + 1
			trail.append("%d:%s%s" % [round_no, word, "" if since > 99 else "(%d)" % since])
		if not his.is_empty():
			with_card += 1
		for k in weeks:
			tally[k] = int(tally.get(k, 0)) + int(weeks[k])
		var p: Dictionary = _state.list_player(pid)
		print("INTL dealt: seed %d, %s (%s, %d games): his cards [%s]" % [career_seed, str(p.get("name", pid)),
				str(p.get("intl", "?")), int(_state.games_played(p)), ", ".join(PackedStringArray(his))])
		if true:
			print("  other cards about him [%s]; weeks by what held his cards %s" % [", ".join(PackedStringArray(others)), str(weeks)])
			print("  " + " ".join(PackedStringArray(trail)))
	print("INTL dealt: %d of %d careers saw an international card in his first season; weeks %s" % [with_card, drafted, str(tally)])
	_check(drafted == careers, "Fremantle drafts an international in every seeded career (%d of %d)" % [drafted, careers])
	_check(with_card * CAREERS >= NEED * drafted,
			"The game deals an international his own card in his first season in most careers (%d of %d)" % [with_card, drafted])
	_check(crowded == 0, "His international cards come a month or more after any card about him, and twelve weeks apart (%d did not)" % crowded)
