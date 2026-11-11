extends SceneTree
## godot --headless --path . --script tests/run_international_tap_tests.gd
## An international player's story card on a phone (TODO row T5.r164): the
## club drafts an international, one of his cards whose moment has come is the
## week's card, the hub opens it at 390x844 portrait, and a finger's tap on an
## answer (tests/tap.gd) answers it. The answer's Gain and Cost are on the
## card before the tap, and what happened shows after it.

const Tap := preload("res://tests/tap.gd")
const SUITE_SEED := 2027
const PHONE := Vector2i(390, 844)
## Touch targets are thumb-sized: 48 px tall at least.
const THUMB := 48.0

var _state: Node
var _router: Node
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


func _settle(n := 8) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_router = root.get_node("Router")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://test_international_tap.save"
	_state.settings_path = "user://test_international_tap.cfg"
	_state.delete_saved_career()
	root.size = PHONE
	await _t("_test_his_card_answered_by_a_tap")
	_state.delete_saved_career()
	print(Ran.line("International tap", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


func _find(n: String) -> Node:
	return current_scene.find_child(n, true, false)


## Every word a control shows, plain (a name in club ink is rich text).
func _texts(n: Node, out: Array) -> void:
	if n is Label or n is Button:
		out.append(str(n.text))
	elif n is RichTextLabel:
		out.append((n as RichTextLabel).get_parsed_text())
	for c in n.get_children():
		_texts(c, out)


func _text_of(n: Node) -> String:
	var out := []
	if n != null and is_instance_valid(n):
		_texts(n, out)
	return " ".join(PackedStringArray(out)).strip_edges()


## Is c drawn, and wholly inside the phone's screen?
func _on_screen(c: Control) -> bool:
	if c == null or not is_instance_valid(c) or not c.is_visible_in_tree():
		return false
	return Rect2(Vector2.ZERO, Vector2(root.size)).grow(0.5).encloses(c.get_global_rect())


## Fremantle drafts an international prospect from the first class and the
## career rolls into the next season with him on the list. Returns his id.
func _draft_an_international() -> String:
	_state.reset()
	_state.career_seed = SUITE_SEED
	_state.replay_seed = SUITE_SEED
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


## The index of an international card of his still waiting this week, or -1.
func _waiting_intl(pid: String) -> int:
	for i in range(_state.week_events.size()):
		var c: Dictionary = _state.week_events[i]
		if str(c.get("tid", "")).begins_with("intl_") and str(c.get("player_id", "")) == pid \
				and not bool(c.get("resolved", false)):
			return i
	return -1


func _test_his_card_answered_by_a_tap() -> void:
	var pid := await _draft_an_international()
	_check(pid != "", "Fremantle drafts an international prospect and he is on the list next season")
	if pid == "":
		return
	var p: Dictionary = _state.list_player(pid)
	_check(str(p.get("intl", "")) != "", "He keeps where he is from")

	# The week's card is one of his whose moment has come on this week's real
	# facts (the deck's own conditions, StoryEngine.meets), built by the game's
	# card builder and put with the week's cards. Which week the dealer draws
	# it is the season's luck, and the waits between cards are StoryEngine's
	# own tests' business (tests/test_international.gd, tests/test_story.gd).
	var engine: GDScript = load("res://scripts/sim/StoryEngine.gd")
	var stories: GDScript = load("res://scripts/state/ClubStories.gd")
	var deck: GDScript = load("res://scripts/sim/StoryDeck.gd")
	# The off-season wrap is read and closed (HubScene's Begin season), then
	# through the pre-season to the home-and-away season, where his cards belong.
	if _state.needs_season_wrap():
		_state.begin_season_from_wrap()
	var played := 0
	while stories.phase(_state) != "regular" and played < 4:
		played += 1
		_state.advance()
	var ctx: Dictionary = stories.context(_state)
	var facts := {}
	for f in ctx["players"]:
		if str(f["id"]) == pid:
			facts = f
	var tid := ""
	for t in deck.all():
		if tid != "" or facts.is_empty() or not str(t["id"]).begins_with("intl_"):
			continue
		if not (t.get("phase", ["regular"]) as Array).has(str(ctx["phase"])):
			continue
		if engine.meets(ctx["club"], t.get("when", {}), {}) and engine.meets(facts, (t["subject"] as Dictionary).get("where", {}), {}):
			tid = str(t["id"])
	_check(tid != "", "One of the international cards fits him this week (round %s, %s games)" % [
			str((ctx["club"] as Dictionary).get("round", "?")), str(facts.get("games", "?"))])
	if tid == "":
		return
	_state.week_events.append(_state.story_card(tid, p))
	var index := _waiting_intl(pid)
	_check(index >= 0, "His card is with the week's cards, unanswered")
	if index < 0:
		return
	var card: Dictionary = _state.week_events[index]
	print("INTL tap: %s, card %d of %d this week" % [card.get("tid", ""), index + 1, _state.week_events.size()])

	# The hub opens the week's new cards one at a time: Later on any before his.
	# The press conference after the match is its own screen: the coach skips it.
	_state.skip_media_conference()
	_router.stack = ["main"]
	_router.go("hub")
	await _settle()
	var sheet: Control = _find("EventSheet")
	var hops := 0
	while sheet != null and hops < 6 and not _text_of(sheet.find_child("SheetEvent", true, false)).contains(str(card.get("title", "-"))):
		hops += 1
		var later: Button = sheet.find_child("EventLater", true, false)
		if later == null or await Tap.tap(later) != "":
			break
		await _settle()
		sheet = _find("EventSheet")
	var shown: Control = sheet.find_child("SheetEvent", true, false) if sheet != null else null
	var card_text := _text_of(shown)
	_check(Vector2i(root.size) == PHONE and shown != null and card_text.contains(str(card.get("title", "-")))
			and card_text.contains(str(card.get("text", "-"))),
			"On a 390x844 phone the hub opens his card, title and story (%s)" % card_text.left(120))
	if shown == null:
		return
	_check(not card_text.contains("{"), "Nothing on the card is left unfilled: %s" % card_text)

	# Every answer is a thumb-sized button with its Gain and its Cost under it.
	var options: Array = card.get("options", [])
	var small := []
	for i in range(options.size()):
		var b: Button = shown.find_child("Event_%d" % i, true, false)
		var gain: Control = shown.find_child("EventGain_%d_%d" % [index, i], true, false)
		var cost: Control = shown.find_child("EventCost_%d_%d" % [index, i], true, false)
		if b == null or b.size.y < THUMB or b.size.x < THUMB or gain == null or cost == null \
				or _text_of(gain) == "" or _text_of(cost) == "" \
				or shown.find_child("EventGainMark_%d_%d" % [index, i], true, false) == null \
				or shown.find_child("EventCostMark_%d_%d" % [index, i], true, false) == null:
			small.append("%d: %s" % [i, str(b.size) if b != null else "no button"])
	_check(options.size() >= 2 and small.is_empty(),
			"Each answer is thumb-sized and says its Gain and its Cost (%s)" % " | ".join(PackedStringArray(small)))

	# A finger's tap on the first answer, where it sits on the screen.
	var pick := 0
	var answer: Button = shown.find_child("Event_%d" % pick, true, false)
	var gain_line := _text_of(shown.find_child("EventGain_%d_%d" % [index, pick], true, false))
	var cost_line := _text_of(shown.find_child("EventCost_%d_%d" % [index, pick], true, false))
	var answer_tap: String = (await Tap.tap(answer)) if answer != null else "missing"
	await _settle()
	_check(answer_tap == "" and bool(card.get("resolved", false)) and int(card.get("choice", -1)) == pick,
			"A real tap on \"%s\" answers the card (%s)" % [str((options[pick] as Dictionary).get("label", "")), answer_tap])
	print("INTL tap: Gain: %s / Cost: %s / result: %s" % [gain_line, cost_line, card.get("outcome", "")])

	# What happened shows in the sheet, on the screen, and Done closes it.
	sheet = _find("EventSheet")
	var out: Control = sheet.find_child("EventOutcome_%d" % index, true, false) if sheet != null else null
	var outcome := str(card.get("outcome", ""))
	_check(out != null and outcome != "" and not outcome.contains("{") and _text_of(out) == outcome and _on_screen(out),
			"The result of the answer shows on the screen: %s" % outcome)
	var done: Button = sheet.find_child("EventDone", true, false) if sheet != null else null
	_check(done != null and done.size.y >= THUMB and sheet.find_child("EventLater", true, false) == null,
			"Done is the one way on from an answered card")
	var done_tap: String = (await Tap.tap(done)) if done != null else "missing"
	await _settle()
	_check(done_tap == "" and not _text_of(_find("EventSheet")).contains(str(card.get("title", "-"))), "A real tap on Done closes his card (%s)" % done_tap)
