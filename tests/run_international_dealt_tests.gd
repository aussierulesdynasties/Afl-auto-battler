extends SceneTree
## godot --headless --path . --script tests/run_international_dealt_tests.gd
## An international's own story cards can come up in his first season
## (director 2026-11-11: a story that can never fire is a bug). The bug: his
## cards waited 12 weeks after ANY card about him, and another card was about
## him every 8 to 10 weeks, so the wait never ended. The fix (StoryEngine
## SERIES_GAP): a card of the "intl" series waits a month after any card about
## him, and 12 weeks after his last card of that series.
##
## Director, 2026-11-14: test the rule itself, not six simulated seasons. Each
## check below builds the story's memory by hand and asks the engine directly,
## so the suite runs in well under a second.

var _checks := 0
var _failures: Array[String] = []
var _engine: GDScript
var _card: Dictionary   # a real international card from the shipped deck


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
	_engine = load("res://scripts/sim/StoryEngine.gd")
	for t in _deck():
		if str(t["id"]) == "intl_homesick":
			_card = t
	await _t("_test_every_international_card_is_in_the_series")
	await _t("_test_a_month_after_any_card_about_him")
	await _t("_test_twelve_weeks_after_his_last_international_card")
	await _t("_test_an_ordinary_card_still_waits_its_full_cooldown")
	await _t("_test_a_busy_first_season_still_deals_his_cards")
	print(Ran.line("International dealt", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


## The shipped international cards, read straight from the deck file.
func _deck() -> Array:
	var f := FileAccess.open("res://data/stories/international.json", FileAccess.READ)
	return JSON.parse_string(f.get_as_text()) if f != null else []


## A first-season international, fit, on his club's list.
func _him() -> Dictionary:
	return {"id": "p_intl", "intl": true, "fit": true, "seasons_listed": 1, "games": 0, "goals": 0}


## An empty story memory, as a new career starts with.
func _story() -> Dictionary:
	return {"last": {}, "seen": {}, "season": {}, "cats": [], "flags": {}, "subj": {}, "arcs": {}}


## Round 15 of 2027 on the stories' calendar: every "n weeks ago" below stays inside the one season.
func _week() -> int:
	return _engine.week_abs(2027, 15)


## Can this card be about him this week, given the story's memory?
func _open(card: Dictionary, story: Dictionary, w: int, round_no := 15) -> bool:
	var ctx := {"phase": "regular", "club": {"round": round_no}, "players": [_him()]}
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	return not (_engine.eligible_subject(card, ctx, story, w, rng) as Dictionary).is_empty()


func _test_every_international_card_is_in_the_series() -> void:
	var deck := _deck()
	_check(deck.size() >= 1 and not _card.is_empty(), "The international deck loads with intl_homesick in it (%d cards)" % deck.size())
	for t in deck:
		_check(str(t.get("series", "")) == "intl" and int(t.get("subject_cooldown", 0)) > _engine.SERIES_GAP,
				"%s is an intl series card with a wait longer than the month (series %s, wait %s)"
				% [t["id"], t.get("series"), t.get("subject_cooldown")])


func _test_a_month_after_any_card_about_him() -> void:
	var w := _week()
	var gap: int = _engine.SERIES_GAP
	_check(_open(_card, _story(), w), "With nothing about him yet, his card can come")
	var story := _story()
	story["subj"]["p_intl"] = w - (gap - 1)
	_check(not _open(_card, story, w), "%d weeks after another card about him, his card waits" % (gap - 1))
	story["subj"]["p_intl"] = w - gap
	_check(_open(_card, story, w), "%d weeks after another card about him, his card can come" % gap)


func _test_twelve_weeks_after_his_last_international_card() -> void:
	var w := _week()
	var wait := int(_card["subject_cooldown"])
	var key: String = _engine._series_key("intl", "p_intl")
	var story := _story()
	story["subj"]["p_intl"] = w - (wait - 1)
	story["subj"][key] = w - (wait - 1)
	_check(not _open(_card, story, w), "%d weeks after his last international card, the next waits" % (wait - 1))
	story["subj"]["p_intl"] = w - wait
	story["subj"][key] = w - wait
	_check(_open(_card, story, w), "%d weeks after his last international card, the next can come" % wait)
	# Recording a dealt card stamps both clocks, so the rule above is what the game really keeps.
	var fresh := _story()
	_engine._record_pick(fresh, {"tid": "intl_homesick", "player_id": "p_intl", "series": "intl", "category": str(_card["category"])}, w)
	_check(int(fresh["subj"].get("p_intl", 0)) == w and int(fresh["subj"].get(key, 0)) == w,
			"A dealt international card stamps his own clock and his series clock")


## The control: without a series, a card about him keeps its full wait from any card.
func _test_an_ordinary_card_still_waits_its_full_cooldown() -> void:
	var plain := _card.duplicate(true)
	plain.erase("series")
	var story := _story()
	story["subj"]["p_intl"] = _week() - _engine.SERIES_GAP
	_check(not _open(plain, story, _week()), "An ordinary card about him still waits its full cooldown after any card about him")


## The bug's own week pattern: another card about him every 8 weeks for a whole
## home-and-away season. His international cards must still come, a month or
## more after the other cards and twelve weeks apart.
func _test_a_busy_first_season_still_deals_his_cards() -> void:
	var story := _story()
	var cards := _deck()
	var his := []
	for r in range(1, 25):
		var w: int = _engine.week_abs(2027, r)
		if r % 8 == 1:
			_engine._record_pick(story, {"tid": "other_card", "player_id": "p_intl", "category": "other"}, w)
			continue
		for t in cards:
			if _open(t, story, w, r):
				his.append([r, str(t["id"])])
				_engine._record_pick(story, {"tid": t["id"], "player_id": "p_intl", "series": "intl", "category": str(t["category"])}, w)
				break
	_check(his.size() >= 2, "A first season with another card about him every 8 weeks still deals him international cards (%s)" % str(his))
	for i in range(1, his.size()):
		_check(int(his[i][0]) - int(his[i - 1][0]) >= int(_card["subject_cooldown"]),
				"His international cards stay twelve weeks apart (%s)" % str(his))
