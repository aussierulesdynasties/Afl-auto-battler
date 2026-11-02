extends RefCounted
## Run by tests/run_match_story_tests.gd (suite "match_story").
## The match makes the story (MatchStory.gd; director, 2026-11-03, plan step
## 1b): the hero is the best by real match stats, every reason traces to a
## number in the result, records persist across save and load, an old save
## loads, and with the switch "match_story" off nothing shows or is kept.

var _tree: SceneTree
var checks := 0
var failures: Array[String] = []
const SUITE_SEED := 2027


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 6) -> void:
	for i in range(n):
		await _tree.process_frame


func _fresh() -> void:
	GameState.reset()
	GameState.start_season("FRE", GameDB.club_list("FRE"))
	GameState.replay_seed = SUITE_SEED
	GameState.tutorials = false
	Router.stack = []


func _rounds(n: int) -> void:
	for i in range(n):
		GameState.advance()


func _my_matches() -> Array:
	var out := []
	for r in GameState.season_log:
		if str(r["home"]) == GameState.my_club or str(r["away"]) == GameState.my_club:
			out.append(r)
	return out


func run(tree: SceneTree) -> void:
	_tree = tree
	await _tree.process_frame
	GameState.autosave_enabled = false
	GameState.save_path = "user://test_match_story.save"
	GameState.settings_path = "user://test_match_story.cfg"
	GameState.delete_saved_career()
	await _t("_test_switch_off")
	Features.set_on("match_story", true)
	_t("_test_pure_hero")
	_t("_test_hero_matches_stats")
	_t("_test_reasons_trace")
	_t("_test_records_persist")
	_t("_test_old_save")
	for size in [Vector2i(390, 844), Vector2i(1280, 720)]:
		_tree.root.size = size
		await _settle()
		await _t("_test_summary", [size])
	Features.clear("match_story")
	GameState.delete_saved_career()
	print(Ran.line("Match story", self))
	for f in failures:
		print("  FAIL: " + f)


func _review() -> Node:
	GameState.review_requested = true
	Router.go("match")
	await _settle(10)
	return _tree.current_scene.find_child("FullTime", true, false)


func _test_switch_off() -> void:
	_check(not Features.on("match_story") and not GameState.match_story_on(), "the switch ships off")
	_fresh()
	_rounds(3)
	_check(GameState.match_stories.is_empty(), "off: no story is kept")
	var told := false
	for n in GameState.news:
		if str(n.get("kind", "")) == "match_story":
			told = true
	_check(not told, "off: no hero on the news front")
	_check(GameState.last_match_story().is_empty(), "off: no last story")
	_check(str(GameState.media_conference.get("question", "")).find("was the hero") < 0, "off: the press never asks about a hero")
	_tree.root.size = Vector2i(390, 844)
	await _settle()
	var ft := await _review()
	_check(ft != null, "off: full time opens")
	_check(ft != null and ft.find_child("MatchStory", true, false) == null, "off: the Summary shows no match story")
	_check(ft != null and ft.find_child("MatchFactors", true, false) != null, "off: How it went is still there")
	Router.stack = []
	Router.go("hub")
	await _settle(4)
	_check(GameState.save_career(), "off: saves")
	GameState.match_stories = [{"junk": 1}]
	_check(GameState.load_career() and GameState.match_stories.is_empty(), "off: the save has no stories")


## A hand-made result: the clutch goal and the clearances count toward the hero.
func _test_pure_hero() -> void:
	var a := {"kicks": 10, "handballs": 5, "marks": 4, "tackles": 3, "goals": 1, "disposals": 15}
	var b := a.duplicate()
	var res := {
		"home": "FRE", "away": "WCE", "score": [70, 64], "goals": [10, 9], "behinds": [10, 10],
		"roster": [[{"id": "p1", "name": "One"}, {"id": "p2", "name": "Two"}], [{"id": "p3", "name": "Three"}]],
		"players": {"p1": a, "p2": b, "p3": {"goals": 6, "kicks": 20, "disposals": 20}},
		"events": [{"kind": "goal", "side": 0, "q": 4, "min": 115, "score": [70, 64], "player_id": "p2", "name": "Two"}],
		"team": [{}, {}],
	}
	var clutch := MatchStory.clutch_goals(res)
	_check(int(clutch.get("p2", 0)) == 1, "a goal 25 minutes into the last, two points down before it, is clutch")
	var hero := MatchStory.hero_of(res)
	_check(str(hero.get("id", "")) == "p2", "the clutch goal makes the hero among equals (%s)" % str(hero.get("id")))
	_check(str(hero.get("line", "")).contains("late with the game in the balance"), "his line says the late goal")
	_check(int(hero["side"]) == 0, "the hero comes from the winners, not the losers' six-goal man")
	res["players"]["p1"]["clearances"] = 12
	_check(str(MatchStory.hero_of(res)["id"]) == "p1", "twelve clearances outweigh one clutch goal")
	res["events"][0]["min"] = 100
	_check(MatchStory.clutch_goals(res).is_empty(), "a goal ten minutes into the last is not clutch")


func _test_hero_matches_stats() -> void:
	_fresh()
	_rounds(4)
	var n := 0
	var ok := true
	for res in GameState.season_log:
		var hero := MatchStory.hero_of(res)
		var s: Array = res["score"]
		var sides := [0, 1] if int(s[0]) == int(s[1]) else [0 if int(s[0]) > int(s[1]) else 1]
		var clutch := MatchStory.clutch_goals(res)
		var best := -1
		var best_ids := []
		for side in sides:
			for r in res["roster"][side]:
				var st: Dictionary = res["players"].get(str(r["id"]), {})
				var pts := MatchStory.hero_points(st, int(clutch.get(str(r["id"]), 0)))
				if pts > best:
					best = pts
					best_ids = [str(r["id"])]
				elif pts == best:
					best_ids.append(str(r["id"]))
		var st: Dictionary = res["players"].get(str(hero.get("id", "")), {})
		if hero.is_empty() or not best_ids.has(str(hero["id"])) or int(hero["points"]) != best \
				or not sides.has(int(hero["side"])) or int(hero["goals"]) != int(float(st.get("goals", 0.0))) \
				or int(hero["disposals"]) != int(float(st.get("disposals", 0.0))):
			ok = false
			print("  hero mismatch: %s vs %s (%d)" % [str(hero), str(best_ids), best])
		n += 1
	_check(n >= 30, "four rounds give enough matches (%d)" % n)
	_check(ok, "every match's hero is the winners' best by goals, disposals, tackles, clearances and clutch goals")


func _test_reasons_trace() -> void:
	_fresh()
	_rounds(4)
	var bad := []
	var counts := {}
	for res in GameState.season_log:
		for side in [0, 1]:
			var why := MatchStory.reasons(res, side)
			if why.is_empty() or why.size() > 3:
				bad.append("%d reasons" % why.size())
			var me: Dictionary = res["team"][side]
			var op: Dictionary = res["team"][1 - side]
			for r in why:
				var stat := str(r["stat"])
				counts[stat] = int(counts.get(stat, 0)) + 1
				var a := int(r["mine"])
				var b := int(r["theirs"])
				var want := []
				if stat == "pressure_rating":
					want = [MatchSim.pressure_rating(me, op), MatchSim.pressure_rating(op, me)]
				elif stat == "scoring_shots":
					want = [int(res["goals"][side]) + int(res["behinds"][side]),
							int(res["goals"][1 - side]) + int(res["behinds"][1 - side])]
				elif stat.begins_with("q"):
					var i := int(r["quarter"]) - 1
					want = [int(res["q_goals"][i][side]) * 6 + int(res["q_behinds"][i][side]),
							int(res["q_goals"][i][1 - side]) * 6 + int(res["q_behinds"][i][1 - side])]
					if not MatchNotes.calls_lines(res, side, i + 1).has(str(r["call"])):
						bad.append("call line not from What your calls did: %s" % str(r["call"]))
				else:
					want = [int(float(me.get(stat, 0.0))), int(float(op.get(stat, 0.0)))]
				if [a, b] != want:
					bad.append("%s says %d-%d, result has %s" % [stat, a, b, str(want)])
				var text := str(r["text"])
				if not (text.contains(str(a)) and text.contains(str(b))):
					bad.append("text lacks its numbers: %s" % text)
	_check(bad.is_empty(), "every reason traces to a number in the result (%s)" % str(bad.slice(0, 3)))
	_check(counts.size() >= 2, "reasons come from more than one stat (%s)" % str(counts))


func _test_records_persist() -> void:
	_fresh()
	_rounds(3)
	var mine := _my_matches()
	_check(GameState.match_stories.size() == mine.size() and mine.size() >= 2,
			"one story per match of yours (%d of %d)" % [GameState.match_stories.size(), mine.size()])
	var rec: Dictionary = GameState.last_match_story()
	var hero := MatchStory.hero_of(GameState.last_match)
	_check(str(rec.get("hero_id", "")) == str(hero.get("id", "x")), "the record names the hero")
	_check(not (rec.get("reasons", []) as Array).is_empty(), "the record keeps the reasons")
	var news := {}
	for n in GameState.news:
		if str(n.get("kind", "")) == "match_story":
			news = n
			break
	_check(not news.is_empty(), "the hero is on the news")
	var story := NewsFront.story(news, GameState.my_club)
	_check(str(story["headline"]) == str(rec["headline"]) and str(story["name"]) == str(rec["hero_name"]),
			"the news front leads with the match headline (%s)" % str(story["headline"]))
	_check(bool(story["mine"]), "the story is marked as your club's")
	var mc: Dictionary = GameState.media_conference
	_check(mc.is_empty() or str(mc.get("question", "")) != "", "the press question still forms")
	var kept: Array = GameState.match_stories.duplicate(true)
	_check(GameState.save_career(), "saves with stories")
	GameState.match_stories = []
	_check(GameState.load_career(), "loads")
	_check(GameState.match_stories == kept, "the stories round-trip through save and load")
	_rounds(1)
	_check(GameState.match_stories.size() == _my_matches().size(), "Sim the week keeps adding them after a load")


func _test_old_save() -> void:
	_fresh()
	_rounds(2)
	Features.set_on("match_story", false)
	GameState.match_stories = []
	_check(GameState.save_career(), "an old-style save is written")
	Features.set_on("match_story", true)
	GameState.match_stories = [{"junk": 1}]
	_check(GameState.load_career(), "an old save loads")
	_check(GameState.match_stories.is_empty(), "absent stories load as empty")
	_rounds(1)
	_check(GameState.match_stories.size() == 1, "and the next match starts the record")
	GameState.delete_saved_career()


func _test_summary(size: Vector2i) -> void:
	var tag := "%dx%d" % [size.x, size.y]
	_fresh()
	_rounds(1)
	var ft := await _review()
	_check(ft != null, "%s: full time opens" % tag)
	var box: Control = ft.find_child("MatchStory", true, false) if ft != null else null
	_check(box != null and box.is_visible_in_tree(), "%s: the Summary shows the match story" % tag)
	if box == null:
		return
	var rec := GameState.last_match_story()
	var hl: Label = box.find_child("MatchHero", true, false)
	_check(hl != null and hl.text == str(rec["hero_name"]), "%s: the hero is named" % tag)
	var why: Node = box.find_child("WhyReasons", true, false)
	_check(why != null and why.get_child_count() == (rec["reasons"] as Array).size(), "%s: the reasons are listed" % tag)
	var factors: Control = ft.find_child("MatchFactors", true, false)
	_check(factors != null and box.get_global_rect().position.y < factors.get_global_rect().position.y,
			"%s: the story sits above How it went" % tag)
	var r := box.get_global_rect()
	_check(r.position.x >= -0.5 and r.end.x <= size.x + 0.5, "%s: the story fits the screen" % tag)
	Router.stack = []
	Router.go("hub")
	await _settle(4)
