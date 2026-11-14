extends RefCounted
## Run by tests/run_match_story_tests.gd (suite "match_story").
## The match makes the story (MatchStory.gd; director, 2026-11-03, plan step
## 1b): the hero is the best by real match stats, every reason traces to a
## number in the result, records persist across save and load, an old save
## loads.

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


## The suite's one seeded season, twelve rounds in (Fremantle), played once and
## read by every test that needs real results. The read-only tests run on it
## first; no_repeats, which changes it, runs
## after them. The save tests play their own short careers.
var _shared_played := false


func _shared() -> void:
	if _shared_played:
		return
	_shared_played = true
	_fresh()
	_rounds(12)


## A Fremantle career one round in, played once and read by the tests that
## need one real match (calls, summary). It is played again whenever the career
## in GameState is no longer that one (another test reset, loaded or played on).
var _r1: Dictionary = {}


func _round_one() -> void:
	if not _r1.is_empty() and GameState.my_club == "FRE" and GameState.season_log.size() == int(_r1["log"]) \
			and GameState.last_match == _r1["match"]:
		return
	_fresh()
	_rounds(1)
	_r1 = {"log": GameState.season_log.size(), "match": (GameState.last_match as Dictionary).duplicate(true)}


func _has_win_and_loss() -> bool:
	var won := false
	var lost := false
	for r in _my_matches():
		var me := _side(r)
		var m := int(r["score"][me]) - int(r["score"][1 - me])
		won = won or m > 0
		lost = lost or m < 0
	return won and lost


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
	_t("_test_pure_hero")
	# On the one shared season (_shared): the tests that only read it, then the
	# ones that change it.
	_t("_test_hero_matches_stats")
	_t("_test_reasons_trace")
	_t("_test_reasons_call_agrees_with_ledger")
	_t("_test_calls_trace")
	_t("_test_arc_facts_and_digest")
	_t("_test_my_best_in_loss")
	_t("_test_factors_never_repeat")
	for size in [Vector2i(390, 844), Vector2i(1280, 720)]:
		_tree.root.size = size
		await _settle()
		await _t("_test_no_repeats", [size])
	_t("_test_records_persist")
	_t("_test_old_save")
	_t("_test_calls_old_fixture")
	_t("_test_calls_name_skip_loose")
	_t("_test_calls_name_switched_loose")
	_t("_test_calls_name_moment_tag")
	_t("_test_calls_skip_men_against_the_row")
	# One round-one career (_round_one) from here on: the calls and the summary
	# read its match; the screen and the trim test, which change it, come last.
	_t("_test_calls_kept")
	_t("_test_calls_every_quarter_pure")
	_t("_test_calls_new_call_before_carried")
	for size in [Vector2i(390, 844), Vector2i(1280, 720)]:
		_tree.root.size = size
		await _settle()
		await _t("_test_summary", [size])
	await _t("_test_calls_every_quarter_screen")
	_t("_test_digest_survives_trim")
	GameState.delete_saved_career()
	print(Ran.line("Match story", self))
	for f in failures:
		print("  FAIL: " + f)


func _review() -> Node:
	GameState.review_requested = true
	Router.go("match")
	await _settle(10)
	return _tree.current_scene.find_child("FullTime", true, false)


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
	_shared()
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
	_check(n >= 30, "the season gives enough matches (%d)" % n)
	_check(ok, "every match's hero is the winners' best by goals, disposals, tackles, clearances and clutch goals")


func _test_reasons_trace() -> void:
	_shared()
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
					var dir := 1 if int(res["score"][side]) >= int(res["score"][1 - side]) else -1
					var led := 0
					for c in MatchStory.calls(res, side)["rows"]:
						if str(c["kind"]) == "call" and str(c["cause"]) == str(r.get("cause", "")):
							led = int(c["pts"])
					if led * dir <= 0:
						bad.append("call cited without its own Our calls row going the result's way (%s %+d): %s" % [str(r.get("cause", "")), led, str(r["call"])])
				else:
					want = [int(float(me.get(stat, 0.0))), int(float(op.get(stat, 0.0)))]
				if [a, b] != want:
					bad.append("%s says %d-%d, result has %s" % [stat, a, b, str(want)])
				var text := str(r["text"])
				if not (text.contains(str(a)) and text.contains(str(b))):
					bad.append("text lacks its numbers: %s" % text)
	_check(bad.is_empty(), "every reason traces to a number in the result (%s)" % str(bad.slice(0, 3)))
	_check(counts.size() >= 2, "reasons come from more than one stat (%s)" % str(counts))


## Why you won never puts the win down to a call that Our calls says cost us
## (director bug, 2026-11-12: "Attack Corridor" cited as why we won while Our
## calls showed it at -2). A real result whose cited call's ledger figure is
## flipped against the result: the cited line goes, or another takes its place.
func _test_reasons_call_agrees_with_ledger() -> void:
	_shared()
	var tried := 0
	var bad := []
	for res0 in GameState.season_log:
		for side in [0, 1]:
			var res: Dictionary = (res0 as Dictionary).duplicate(true)
			var dir := 1 if int(res["score"][side]) >= int(res["score"][1 - side]) else -1
			var cited := {}
			for r in MatchStory.reasons(res, side):
				if r.has("call"):
					cited = r
			if cited.is_empty():
				continue
			tried += 1
			var cause := str(cited["cause"])
			# The call now cost us (or, in a loss, helped us) by three points.
			(res["impact"][side] as Dictionary)[cause] = -3.0 * dir
			for r in MatchStory.reasons(res, side):
				if r.has("call") and str(r["cause"]) == cause:
					bad.append("%s still cited at %+d: %s" % [cause, -3 * dir, str(r["text"])])
			var row := {}
			for c in MatchStory.calls(res, side)["rows"]:
				if str(c["cause"]) == cause:
					row = c
			if not row.is_empty() and int(row["pts"]) != -3 * dir:
				bad.append("Our calls does not show %s at %+d (%s)" % [cause, -3 * dir, str(row)])
	_check(tried >= 5, "enough matches cite a call (%d)" % tried)
	_check(bad.is_empty(), "a call is cited only when its ledger figure went the result's way (%s)" % str(bad.slice(0, 3)))


func _test_records_persist() -> void:
	# Its own short career: the shared season's last match is changed by the
	# tests before it, so "the last record names the hero" is read on a fresh one.
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
	GameState.match_stories = []
	_check(GameState.save_career(), "an old-style save is written")
	GameState.match_stories = [{"junk": 1}]
	_check(GameState.load_career(), "an old save loads")
	_check(GameState.match_stories.is_empty(), "absent stories load as empty")
	_rounds(1)
	_check(GameState.match_stories.size() == 1, "and the next match starts the record")
	GameState.delete_saved_career()


func _test_summary(size: Vector2i) -> void:
	var tag := "%dx%d" % [size.x, size.y]
	_round_one()
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
	_check(factors != null, "%s: How it went is built" % tag)
	if factors != null and factors.visible:
		_check(box.get_global_rect().position.y < factors.get_global_rect().position.y,
				"%s: the story sits above How it went" % tag)
	var r := box.get_global_rect()
	_check(r.position.x >= -0.5 and r.end.x <= size.x + 0.5, "%s: the story fits the screen" % tag)
	# Our calls (row 144): a row per MatchStory.calls row, then the final margin.
	var c := MatchStory.calls(GameState.last_match, _side(GameState.last_match))
	var grid: GridContainer = box.find_child("CallsStory", true, false)
	_check(not c.is_empty() and grid != null, "%s: the story shows our calls" % tag)
	if grid != null and not c.is_empty():
		_check(grid.get_child_count() == 2 * ((c["rows"] as Array).size() + 1),
				"%s: a row per call plus the margin (%d children)" % [tag, grid.get_child_count()])
		var gr := grid.get_global_rect()
		_check(gr.position.x >= -0.5 and gr.end.x <= size.x + 0.5, "%s: our calls fit the screen" % tag)
	Router.stack = []
	Router.go("hub")
	await _settle(4)


## hero_streak / hero_count / close_losses equal a count made by hand from
## match_stories, and the season digest totals equal the per-match records.
func _test_arc_facts_and_digest() -> void:
	_shared()
	var year := int(GameState.season_year)
	var recs: Array = GameState.match_stories.filter(func(r): return int(r["year"]) == year)
	var counts := {}
	var close_l := 0
	var against := 0
	var mine_ids := []
	for r in recs:
		var id := ""
		if str(r["hero_club"]) == str(r["club"]) and str(r["hero_id"]) != "":
			id = str(r["hero_id"])
		elif str(r.get("my_best_id", "")) != "":
			id = str(r["my_best_id"])
		if id != "":
			counts[id] = int(counts.get(id, 0)) + 1
		mine_ids.append(id)
		if int(r["margin"]) < 0 and int(r["margin"]) >= -12:
			close_l += 1
		if int(r["margin"]) < 0 and bool(r["comeback"]):
			against += 1
	var streak := 0
	if not mine_ids.is_empty() and str(mine_ids[-1]) != "":
		for i in range(mine_ids.size() - 1, -1, -1):
			if mine_ids[i] != mine_ids[-1]:
				break
			streak += 1
	var f := MatchStory.arc_facts(GameState.match_stories, year)
	_check(f["hero_counts"] == counts, "hero counts match a hand count (%s vs %s)" % [str(f["hero_counts"]), str(counts)])
	_check(int(f["hero_streak"]) == streak, "hero streak matches a hand count (%d vs %d)" % [int(f["hero_streak"]), streak])
	_check(int(f["close_losses"]) == close_l and int(f["turned_against"]) == against, "close losses and comebacks against match")
	var d: Dictionary = GameState.match_story_digest.get(str(year), {})
	_check(int(d.get("played", 0)) == recs.size() and recs.size() >= 10, "the digest counts every match (%d)" % recs.size())
	var total := 0
	for id in d.get("heroes", {}):
		total += int(d["heroes"][id]["count"])
		_check(int(d["heroes"][id]["count"]) == int(counts.get(id, -1)), "digest hero count for %s matches" % str(id))
	var hand_total := 0
	for id in counts:
		hand_total += int(counts[id])
	_check(total == hand_total, "digest hero total matches the records")
	var best := 0
	var worst := 0
	for r in recs:
		best = maxi(best, int(r["margin"]))
		worst = mini(worst, int(r["margin"]))
	_check(int((d["best_win"] as Dictionary).get("margin", 0)) == best and int((d["worst_loss"] as Dictionary).get("margin", 0)) == worst,
			"digest best win and worst loss are the real ones")
	_check(int(d["close_losses"]) == close_l, "digest close losses match")


## In a loss the record names your best player: yours, and the top by hero points.
func _test_my_best_in_loss() -> void:
	_shared()
	var found := false
	for r in GameState.season_log:
		var side := 0 if str(r["home"]) == GameState.my_club else (1 if str(r["away"]) == GameState.my_club else -1)
		if side < 0 or int(r["score"][side]) >= int(r["score"][1 - side]):
			continue
		found = true
		var rec := MatchStory.record(r, side, GameState.season_year)
		var mb := MatchStory.my_best(r, side)
		_check(int(mb["side"]) == side and str(rec["my_best_id"]) == str(mb["id"]) and str(rec["my_best_id"]) != "",
				"a loss names your best player from your side")
		var clutch := MatchStory.clutch_goals(r)
		var top := -9999
		for p in MatchNotes.rated_players(r, side):
			top = maxi(top, MatchStory.hero_points(p["stats"], int(clutch.get(str(p["id"]), 0))))
		_check(int(mb["points"]) == top, "your best is the top by hero points (%d vs %d)" % [int(mb["points"]), top])
		_check(str(rec["hero_club"]) != str(rec["club"]), "the hero is still the winners'")
		break
	if not found:
		_check(true, "no loss in the sample to check")


## A season folded into the digest survives the list being trimmed past 120.
func _test_digest_survives_trim() -> void:
	# Any Fremantle career with a round played will do: the stories and the
	# digest are replaced below, and one more round trims the list.
	if GameState.my_club != "FRE" or GameState.season_log.is_empty():
		_round_one()
	var old := int(GameState.season_year) - 1
	GameState.match_stories = []
	GameState.match_story_digest = {}
	for i in range(GameState.MAX_MATCH_STORIES):
		var rec := {"year": old, "label": "Round %d" % (i % 23 + 1), "club": "FRE", "opp": "WCE", "margin": 10 if i % 2 == 0 else -5,
				"hero_id": "H1", "hero_name": "Old Hero", "hero_club": "FRE", "headline": "x", "turning_point": ""}
		GameState.match_stories.append(rec)
		MatchStory.fold(GameState.match_story_digest, rec)
	var log0 := _my_matches().size()
	_rounds(1)
	_check(_my_matches().size() == log0 + 1, "(setup) one more match of ours is played")
	_check(GameState.match_stories.size() == GameState.MAX_MATCH_STORIES, "the list stays capped at 120")
	var d: Dictionary = GameState.match_story_digest.get(str(old), {})
	_check(int(d.get("played", 0)) == GameState.MAX_MATCH_STORIES and int(d["heroes"]["H1"]["count"]) == GameState.MAX_MATCH_STORIES,
			"the trimmed season's digest is whole (%s)" % str(d.get("played")))
	_check(GameState.save_career() and GameState.load_career(), "saves and loads with a digest")
	_check(int((GameState.match_story_digest.get(str(old), {}) as Dictionary).get("played", 0)) == GameState.MAX_MATCH_STORIES,
			"the digest survives a save and load")


# ---------------------------------------------------------------------------
# Each fact once (director's bug report, 2026-11-06: "Double up of copy in hero
# of the match and how it went section").
# ---------------------------------------------------------------------------

func _side(r: Dictionary) -> int:
	return 0 if str(r["home"]) == GameState.my_club else (1 if str(r["away"]) == GameState.my_club else -1)


## Pure: How it went never says a fact the story above it already told, over
## twelve seeded rounds.
func _test_factors_never_repeat() -> void:
	_shared()
	var bad := []
	var cut := 0
	for r in _my_matches():
		var me := _side(r)
		var st := MatchStory.build(r, me)
		var told := MatchStory.told_facts(st)
		var items := MatchNotes.match_factor_items(r, me)
		var shown := MatchNotes.match_factors(r, me, told)
		if shown.size() < MatchNotes.match_factors(r, me).size():
			cut += 1
		for f in shown:
			var fact := ""
			for it in items:
				if str(it["text"]) == str(f):
					fact = str(it["fact"])
			if fact != "" and told.has(fact):
				bad.append("%s repeats %s" % [str(r["label"]), fact])
			if told.has("=" + MatchNotes.norm_sentence(str(f))):
				bad.append("%s repeats the sentence %s" % [str(r["label"]), str(f)])
			if str(f) == str(st["turning_point"]):
				bad.append("%s repeats the turning point" % str(r["label"]))
	# One turning point, from either side's seat: a comeback and the goal that
	# put a side in front for good are one moment, told once. Every match of
	# the twelve rounds, from both seats: one club's dozen games is too thin a
	# sample to be sure of a comeback built on the match's goal run.
	var comebacks := 0
	var run_merged := 0
	for r in GameState.season_log:
		if (r.get("events", []) as Array).is_empty():
			continue
		for side in [0, 1]:
			var st2 := MatchStory.build(r, side)
			if not ["turn", "turn:lead"].has(str(st2.get("turning_fact", ""))):
				continue
			comebacks += 1
			var run := MatchNotes._longest_run(r.get("events", []))
			var same_run := false
			if int(run["len"]) >= 4:
				var turn := ComebackTelling.turn_facts(r, side)
				if not turn.is_empty():
					same_run = int(run["side"]) == int(ComebackTelling.turning_quarter(r, side).get("side", -1)) 							and (turn.get("quarters", []) as Array).has(int(run["q"]))
				else:
					var lead: Array = MatchNotes.turning_point_items(r, side).filter(func(it): return str(it["fact"]) == "turn:lead")
					same_run = not lead.is_empty() and int(lead[0]["side"]) == int(run["side"]) and int(lead[0]["q"]) == int(run["q"])
			if same_run:
				run_merged += 1
			for f in MatchNotes.match_factors(r, side, MatchStory.told_facts(st2)):
				if str(f).contains("in front for good") or str(f).contains("turned it in the"):
					bad.append("%s tells the turning point twice: %s" % [str(r["label"]), str(f)])
				if same_run and str(f) == MatchNotes.run_sentence(r, run):
					bad.append("%s tells the comeback's goal run again: %s" % [str(r["label"]), str(f)])
	_check(comebacks > 0, "the seeded season has a turning point that is a lead change (%d)" % comebacks)
	_check(run_merged > 0, "the seeded season has a turning point made of the match's goal run (%d)" % run_merged)
	_check(bad.is_empty(), "How it went never repeats the story's facts (%s)" % str(bad.slice(0, 3)))
	_check(cut > 0, "the seeded season has matches where the story already said something (%d)" % cut)
	# No told facts: How it went is as it was for every older caller.
	var r0: Dictionary = _my_matches()[0]
	_check(MatchNotes.match_factors(r0, _side(r0)) == MatchNotes.match_factors(r0, _side(r0), {}),
			"no told facts leaves How it went as before")
	# A five-goal second quarter with no run of four is still told when a turning
	# point comes first: only a told run covers its quarter.
	var evs := []
	var sc := [0, 0]
	var seq := [[1, 1], [0, 2], [0, 2], [0, 2], [1, 2], [0, 2], [0, 2], [0, 2]]
	for i in seq.size():
		var s: int = seq[i][0]
		sc[s] += 6
		evs.append({"kind": "goal", "side": s, "q": int(seq[i][1]), "min": int(seq[i][1]) * 30 - 25 + i,
				"score": sc.duplicate(), "name": "Kicker %d" % i, "player_id": "k%d" % i})
	var q2 := {"home": "GEE", "away": "MEL", "score": sc.duplicate(), "events": evs, "team": [{}, {}],
			"q_goals": [[0, 1], [6, 1], [0, 0], [0, 0]], "q_behinds": [[0, 0], [0, 0], [0, 0], [0, 0]]}
	var q2_facts := MatchNotes.match_factor_items(q2, 0).map(func(it): return str(it["fact"]))
	_check(int(MatchNotes._longest_run(evs)["len"]) == 3 and q2_facts.has("turn:lead") and q2_facts.has("q2"),
			"a big quarter is told unless a told run covers it (%s)" % str(q2_facts))


## The Summary tab's visible text, sentence by sentence, normalised. Only
## sentences of four words or more: a name or a score alone is not a sentence.
func _summary_sentences(ft: Node) -> Array:
	var out := []
	for l in ft.find_children("*", "Label", true, false):
		if not (l as Label).is_visible_in_tree():
			continue
		for line in str(l.text).split("\n", false):
			for part in line.split(". ", false):
				var n := MatchNotes.norm_sentence(part)
				if n.split(" ", false).size() >= 4:
					out.append(n)
	return out


func _labels_text(n: Node) -> String:
	var t := ""
	if n == null:
		return t
	if n is Label:
		t += str(n.text) + "\n"
	for l in n.find_children("*", "Label", true, false):
		t += str(l.text) + "\n"
	return t


## Renders one match's full time and fails on any sentence or fact said twice.
func _check_once(r: Dictionary, tag: String) -> void:
	GameState.last_match = r
	var ft := await _review()
	_check(ft != null, "%s: full time opens" % tag)
	if ft == null:
		return
	var seen := {}
	var twice := []
	for n in _summary_sentences(ft):
		if seen.has(n):
			twice.append(n)
		seen[n] = true
	_check(twice.is_empty(), "%s: no sentence twice on full time (%s)" % [tag, str(twice.slice(0, 2))])
	var me := _side(r)
	var st := MatchStory.build(r, me)
	var factors: Control = ft.find_child("MatchFactors", true, false)
	var ftext := _labels_text(factors)
	var tp := str(st["turning_point"])
	_check(tp == "" or not ftext.contains(tp), "%s: the turning point is not said again under How it went" % tag)
	if (st.get("turning_also", []) as Array).has("run"):
		var run2 := MatchNotes._longest_run(r.get("events", []))
		_check(not ftext.contains(MatchNotes.run_sentence(r, run2)),
				"%s: the goal run the turning point was made of is not told again (%s)" % [tag, ftext.strip_edges()])
	# One turning point: a comeback and the goal that put a side in front for good are the same moment.
	if ["turn", "turn:lead"].has(str(st.get("turning_fact", ""))):
		_check(not ftext.contains("in front for good") and not ftext.contains("turned it in the"),
				"%s: How it went does not tell the turning point a second way (%s)" % [tag, ftext.strip_edges()])
	var codes := [str(r["home"]), str(r["away"])]
	for reason in st["reasons"]:
		if str(reason["stat"]) == "scoring_shots":
			# The no-clear-edge reason quotes both scorelines: How it went does not quote them again.
			for s in [me, 1 - me]:
				var sl := "%d.%d" % [int(r["goals"][s]), int(r["behinds"][s])]
				_check(not ftext.contains(sl), "%s: How it went does not repeat the %s scoreline %s" % [tag, codes[s], sl])
			continue
		if not ["pressure_rating", "clearances", "inside50"].has(str(reason["stat"])):
			continue
		var a := int(reason["mine"])
		var b := int(reason["theirs"])
		for l in ftext.split("\n", false):
			_check(not (l.contains("%d to %d" % [a, b]) or l.contains("%d to %d" % [b, a])),
					"%s: How it went does not repeat the %s numbers (%s)" % [tag, str(reason["stat"]), l])
	# The hero's line (and your best's) never repeats a number his Best players row gives.
	var rows := {}
	var votes := MatchNotes.coaches_votes(r)
	for side in [0, 1]:
		for p in MatchNotes.standouts_by_votes(r, side, 3, votes):
			rows[str(p["id"])] = str(p["line"])
	for pair in [["MatchHeroLine", st["hero"]], ["MatchMyBest", MatchStory.my_best(r, me) if int(st["margin"]) < 0 else {}]]:
		var node := ft.find_child(str(pair[0]), true, false)
		var who: Dictionary = pair[1]
		if node == null or who.is_empty() or not rows.has(str(who["id"])):
			continue
		for bit in str(rows[str(who["id"])]).split(", ", false):
			_check(not str(node.text).to_lower().contains(bit.to_lower()),
					"%s: %s does not repeat %s from Best players (%s)" % [tag, str(pair[0]), bit, str(node.text)])
	# The coaching notes do not say a reason again in other words.
	var notes := _labels_text(ft.find_child("ReportNotes", true, false))
	var topics := CoachReport.told_topics()
	for reason in st["reasons"]:
		var topic := str(topics.get(str(reason["stat"]), ""))
		_check(topic == "" or not notes.contains(topic),
				"%s: the coaching notes do not repeat the %s reason (%s)" % [tag, str(reason["stat"]), notes.strip_edges()])
	var head: Control = ft.find_child("HowItWentHead", true, false)
	_check(factors != null and head != null, "%s: How it went is built" % tag)
	if factors != null and head != null:
		var empty := factors.get_child_count() == 0
		_check(factors.visible == (not empty) and head.visible == (not empty),
				"%s: How it went shows only with something left to say (%d lines)" % [tag, factors.get_child_count()])
	print("  %s: %s" % [tag, " | ".join(_summary_sentences(ft))])
	Router.stack = []
	Router.go("hub")
	await _settle(4)


func _test_no_repeats(size: Vector2i) -> void:
	var tag := "%dx%d" % [size.x, size.y]
	_shared()
	# What this test writes (the last match shown, two debuts in the milestone
	# log) is put back at its end, so the next size reads the season as played.
	var kept_last: Dictionary = GameState.last_match
	var kept_log: Dictionary = GameState.milestone_log.duplicate(true)
	# Play on until the season has both a win and a loss to read: how many
	# rounds that takes is the sim's business, not this test's.
	var extra := 0
	while extra < 12 and not _has_win_and_loss():
		_rounds(1)
		extra += 1
	var win := {}
	var loss := {}
	for r in _my_matches():
		var me := _side(r)
		var m := int(r["score"][me]) - int(r["score"][1 - me])
		var told := MatchStory.told_facts(MatchStory.build(r, me))
		# The director's kind first: the story already told something How it went had.
		var rich := MatchNotes.match_factors(r, me, told).size() < MatchNotes.match_factors(r, me).size()
		if m > 0 and (win.is_empty() or (rich and not bool(win["rich"]))):
			win = {"r": r, "rich": rich}
		elif m < 0 and (loss.is_empty() or (rich and not bool(loss["rich"]))):
			loss = {"r": r, "rich": rich}
	_check(not win.is_empty() and not loss.is_empty(), "%s: the season gives a win and a loss" % tag)
	if not win.is_empty():
		await _check_once(win["r"], tag + " win")
	if not loss.is_empty():
		await _check_once(loss["r"], tag + " loss")
	# Two debuts in the last match, as the director saw: each said once, in
	# Milestones, in the fuller words; "made his debut" is gone.
	var last: Dictionary = _my_matches()[-1]
	GameState.last_match = last
	var me := _side(last)
	var ids := []
	for row in last["roster"][me]:
		if ids.size() < 2:
			ids.append(str(row["id"]))
	var mk := Milestones.match_key(GameState.season_year, last)
	GameState.milestone_log["last_match"] = mk
	var names := []
	for id in ids:
		var p: Dictionary = GameState.list_player(id)
		var nm := str(GameDB.player_display_name(p))
		names.append(nm)
		Firsts.note(p, "debut", GameState.season_year, str(last["label"]))
		(GameState.milestone_log["log"] as Array).append({"who": "player", "kind": "debut", "value": 1, "id": id,
				"name": nm, "text": "%s made his debut." % nm, "match": mk})
	var ft := await _review()
	var said := _labels_text(ft.find_child("MilestoneLine", true, false) if ft != null else null) \
			+ _labels_text(ft.find_child("PayoffLines", true, false) if ft != null else null)
	_check(not said.contains("made his debut"), "%s: the debut is said in the fuller words (%s)" % [tag, said])
	for i in range(names.size()):
		var goals := int((last["players"].get(ids[i], {}) as Dictionary).get("goals", 0))
		_check(said.count(str(names[i])) == 1 and said.contains(Firsts.debut_line(str(names[i]), goals)),
				"%s: %s's debut is said once (%s)" % [tag, str(names[i]), said.strip_edges()])
	Router.stack = []
	Router.go("hub")
	await _settle(4)
	GameState.last_match = kept_last
	GameState.milestone_log = kept_log


## Our calls at full time (row 144): every number traces to the result. Each
## call row is its impact-ledger credit rounded, the other rows are the sums
## they name, and all of them add up to the final margin.
func _test_calls_trace() -> void:
	_shared()
	var bad := []
	var seen := 0
	var kinds := {}
	for res in GameState.season_log:
		if not res.has("impact"):
			continue
		for side in [0, 1]:
			var c := MatchStory.calls(res, side)
			if c.is_empty():
				continue
			seen += 1
			var margin := int(res["score"][side]) - int(res["score"][1 - side])
			var imp: Array = res["impact"]
			var credit := func(s: int, cause: String) -> float:
				return snappedf(float((imp[s] as Dictionary).get(cause, 0.0)), 0.01)
			var mine_total := 0.0
			var theirs := 0.0
			for cause in MatchSim.DECISION_CAUSES:
				mine_total += credit.call(side, cause)
				theirs -= credit.call(1 - side, cause)
			var shown := 0.0
			var sum := 0
			for r in c["rows"]:
				var pts := int(r["pts"])
				sum += pts
				kinds[str(r["kind"])] = true
				if pts == 0:
					bad.append("a row worth nothing: %s" % r["text"])
				if not str(r["text"]).contains(str(absi(pts))):
					bad.append("text lacks its number: %s" % r["text"])
				if str(r["kind"]) == "call":
					var cr: float = credit.call(side, str(r["cause"]))
					shown += cr
					if pts != roundi(cr):
						bad.append("%s says %d, the ledger %.2f" % [r["cause"], pts, cr])
				elif str(r["kind"]) == "theirs" and pts != roundi(theirs):
					bad.append("their calls say %d, the ledger %.2f" % [pts, theirs])
			for r in c["rows"]:
				if str(r["kind"]) == "other" and int(r["pts"]) != roundi(mine_total - shown):
					bad.append("our other calls say %d, the ledger %.2f" % [int(r["pts"]), mine_total - shown])
			if sum != margin or int(c["margin"]) != margin:
				bad.append("rows add to %d, the margin is %d" % [sum, margin])
	_check(seen >= 8, "calls are told for most matches (%d)" % seen)
	_check(bad.is_empty(), "every calls number traces to the result (%s)" % str(bad.slice(0, 3)))
	_check(kinds.has("call") and kinds.has("rest"), "our calls and the players and the bounce both show (%s)" % str(kinds))


## The save keeps each match's coach rows (director 2026-11-10: "Yes, keep
## them"), they survive save and load, and a kept record retells the same
## calls as the result it came from.
func _test_calls_kept() -> void:
	_round_one()
	var rec: Dictionary = GameState.last_match_story()
	var me := _side(GameState.last_match)
	_check(rec.get("coach_rows") is Dictionary and not (rec["coach_rows"]["mine"] as Dictionary).is_empty(),
			"the record keeps our coach rows")
	var live := MatchStory.calls(GameState.last_match, me)
	var kept := MatchStory.calls_from(rec.get("coach_rows", {}), rec.get("call_names", {}), int(rec["margin"]))
	_check(kept == live, "the kept rows tell the same calls (%s vs %s)" % [str(kept.get("rows", [])).left(160),
			str(live.get("rows", [])).left(160)])
	_check(GameState.save_career(), "saves")
	GameState.reset()
	_check(GameState.load_career(), "loads")
	var back: Dictionary = GameState.last_match_story()
	_check(back.get("coach_rows") == rec.get("coach_rows") and back.get("call_names") == rec.get("call_names"),
			"the coach rows round-trip through the save")
	_check(MatchStory.calls(GameState.last_match, me) == live,
			"the last match's review tells the same calls after a reload")
	GameState.delete_saved_career()


## An old save (the frozen version 2 fixture, written before the coach rows
## were kept) loads, its records and last match tell no calls rather than
## wrong ones, and the next match keeps them.
func _test_calls_old_fixture() -> void:
	GameState.delete_saved_career()
	var gz := FileAccess.get_file_as_bytes("res://tests/fixtures/career_v2_2026-11-11.save.gz")
	var f := FileAccess.open(GameState.save_path, FileAccess.WRITE)
	f.store_buffer(gz.decompress_dynamic(-1, FileAccess.COMPRESSION_GZIP))
	f.close()
	GameState.reset()
	_check(GameState.load_career(), "the old fixture loads")
	var old := GameState.match_stories.size()
	_check(old >= 1 and not (GameState.match_stories[0] as Dictionary).has("coach_rows"),
			"its records predate the coach rows (%d)" % old)
	var first: Dictionary = GameState.match_stories[0] if old > 0 else {}
	_check(MatchStory.calls_from(first.get("coach_rows", {}), first.get("call_names", {}),
			int(first.get("margin", 0))).is_empty(), "an old record tells no calls")
	_check(MatchStory.calls(GameState.last_match, 0).is_empty() and MatchStory.calls(GameState.last_match, 1).is_empty(),
			"an old last match tells no calls")
	GameState.replay_seed = SUITE_SEED
	GameState.advance()
	var rec: Dictionary = GameState.last_match_story()
	_check(GameState.match_stories.size() == old + 1 and rec.get("coach_rows") is Dictionary
			and not (rec["coach_rows"]["mine"] as Dictionary).is_empty(), "the next match keeps its coach rows")
	GameState.delete_saved_career()


## A match with your assistant on your side (MatchScene: Skip to full time and
## the breaks run the same MatchSim calls), against a rival coach.
func _assisted_sim(seed: int) -> MatchSim:
	var a := Squad.new("FRE", GameDB.club_list("FRE"), true, "FRE")
	a.assistant = true
	var b := Squad.new("MEL", GameDB.club_list("MEL"), false, "MEL")
	b.ai_plans = true
	return MatchSim.new(a, b, seed)


## Plays the match a quarter at a time: [result, loose man at each quarter's
## start, our loose credit earned in each quarter].
func _play_quarters(sim: MatchSim) -> Array:
	var who := []
	var pts := []
	while sim.current_quarter <= 4:
		who.append(str(sim.interceptor[0]))
		var before := float((sim.impact[0] as Dictionary).get("loose", 0.0))
		sim.run_quarter()
		pts.append(float((sim.impact[0] as Dictionary).get("loose", 0.0)) - before)
	if sim.needs_extra_time():
		sim.run_extra_time()
	return [sim.result(), who, pts]


## Skip to full time before the first bounce: the assistant's loose man plays
## the whole match and is named, not "Our loose men" (he was never in the
## plans the quarters kept).
func _test_calls_name_skip_loose() -> void:
	var played := _play_quarters(_assisted_sim(4411))
	var res: Dictionary = played[0]
	var who: Array = played[1]
	_check(who[0] != "" and who.count(who[0]) == who.size(), "one man plays loose all match (%s)" % str(who))
	var want := "%s as our loose man" % MatchStory._name_in(res, str(who[0]))
	var got := str(MatchStory.call_names(res, 0)["loose"])
	_check(got == want, "the one loose man is named (%s, want %s)" % [got, want])


## The coach box starts Q1 with A loose, then the match is skipped at quarter
## time and the assistant sends B: the row names the man who earned the most
## of the loose man's points, not A for the whole match.
func _test_calls_name_switched_loose() -> void:
	var sim := _assisted_sim(4412)
	var pick := str(sim.interceptor[0])
	var a := ""
	for p in Matchups.defenders((sim.squads[0] as Squad).ground):
		if str(p["id"]) != pick:
			a = str(p["id"])
			break
	_check(a != "", "a second defender to start loose")
	var t: Dictionary = (sim.tactics[0] as Dictionary).duplicate()
	t["interceptor_id"] = a
	sim.set_tactics(0, t)
	var played := _play_quarters(sim)
	var res: Dictionary = played[0]
	var who: Array = played[1]
	var pts: Array = played[2]
	_check(str(who[0]) == a and str(who[1]) != a and str(who[1]) != "",
			"A plays Q1 loose and the assistant sends another man at quarter time (%s)" % str(who))
	var by := {}
	for i in range(who.size()):
		by[str(who[i])] = float(by.get(str(who[i]), 0.0)) + float(pts[i])
	var best := ""
	for id in by:
		if best == "" or absf(float(by[id])) > absf(float(by[best])):
			best = str(id)
	_check(best != a, "the man after quarter time earned more than A (%s)" % str(by))
	var got := str(MatchStory.call_names(res, 0)["loose"])
	_check(got.begins_with(MatchStory._name_in(res, best) + " ") and got.contains("loose m"),
			"the loose man's row leads with the biggest earner (%s, want %s first)" % [got, MatchStory._name_in(res, best)])


## A man who cost points is never named on a row that shows a gain, even when
## he moved the most points: A -9, B +6, C +5 is "B and C", not "A and B".
func _test_calls_skip_men_against_the_row() -> void:
	var res := {"roster": [[{"id": "a", "name": "Al"}, {"id": "b", "name": "Bo"}, {"id": "c", "name": "Cy"}]]}
	var got: Array = MatchStory._earners(res, {"a": -9.0, "b": 6.0, "c": 5.0})
	_check(got == ["Bo", "Cy"], "only the men who added to a +2 row are named (%s)" % str(got))
	got = MatchStory._earners(res, {"a": 9.0, "b": -3.0})
	_check(got == ["Al"], "the man who cost 3 is left off a +6 row (%s)" % str(got))
	got = MatchStory._earners(res, {"a": -4.0, "b": 1.0})
	_check(got == ["Al"], "a -3 row names the man who cost points (%s)" % str(got))


## A tag called from a moment card in the last quarter (no tag before it, the
## tag kept as the coach's call): the row names the man tagged.
func _test_calls_name_moment_tag() -> void:
	var sim := _assisted_sim(4413)
	var t: Dictionary = (sim.tactics[0] as Dictionary).duplicate()
	t["tag_id"] = ""
	t["tag_set"] = true
	sim.set_tactics(0, t)
	for q in range(3):
		sim.run_quarter()
	sim.begin_quarter()
	var hot := ""
	for p in (sim.squads[1] as Squad).ground:
		if MatchSim.taggable(p):
			hot = str(p["id"])
			break
	_check(hot != "" and sim._tag_id(0) == "", "an untagged rival midfielder in the last quarter (%s)" % hot)
	sim.pending_moment = {"kind": "hot", "player_id": hot, "side": 0, "default": 1, "q": 4,
			"title": "He has kicked 3", "options": [{"key": "tag", "label": "Tag him"}, {"key": "leave", "label": "Back your defenders"}]}
	sim.resolve_moment(0)
	_check(sim._tag_id(0) == hot, "the card puts the tag on him")
	sim.run_quarter()
	if sim.needs_extra_time():
		sim.run_extra_time()
	var res := sim.result()
	_check(absf(float((res["impact"][0] as Dictionary).get("tag", 0.0))) > 0.0, "the tag earned credit")
	var want := "Our tag on %s" % MatchStory._name_in(res, hot)
	var got := str(MatchStory.call_names(res, 0)["tag"])
	_check(got == want, "the tagged man is named (%s, want %s)" % [got, want])


## A seeded match with a call in every quarter (director bug, 2026-11-12: "Your
## calls" showed Q1, rarely Q2, never Q3 or Q4). Round 1's real result, with
## your plan rewritten each quarter to a game plan, a tag and three players to
## go through: five lines a quarter, twenty in all, against a cap of five.
func _calls_every_quarter_result() -> Dictionary:
	_round_one()
	var res: Dictionary = (GameState.last_match as Dictionary).duplicate(true)
	var me := _side(res)
	var mine: Array = res["roster"][me]
	var theirs: Array = res["roster"][1 - me]
	var plans := ["attacking", "defensive", "contest", "controlled"]
	for h in res["tactics_history"]:
		var q := int(h["quarter"])
		if q < 1 or q > 4:
			continue
		var p: Dictionary = h["plans"][me]
		p["gameplan"] = plans[q - 1]
		p["tag_id"] = str(theirs[q]["id"])
		p["focus_mid"] = str(mine[q]["id"])
		p["focus_fwd"] = str(mine[q + 4]["id"])
		p["focus_def"] = str(mine[q + 8]["id"])
	return res


func _quarters_in(lines: Array) -> Array:
	var qs := []
	for t in lines:
		qs.append(int(str(t).substr(1, 1)))
	return qs


func _test_calls_every_quarter_pure() -> void:
	var res := _calls_every_quarter_result()
	var me := _side(res)
	var all := 0
	for q in range(1, 5):
		var n := (MatchNotes.calls_lines(res, me, q) as Array).size()
		_check(n == 5, "calls: Q%d has five call lines (got %d)" % [q, n])
		all += n
	# Win Contest (Q3 here) names the last quarter's clearances in brackets, as
	# the attacking and defensive lines do: "from 8 to 10" read as a rise.
	var contest := str(MatchNotes.calls_lines(res, me, 3)[0])
	var cl := RegEx.create_from_string("^Win Contest: clearances \\d+ to \\d+ \\(\\d+ to \\d+ in the second\\)\\.$")
	_check(cl.search(contest) != null and not contest.contains("from"),
			"calls: the contest line puts the last quarter in brackets (got %s)" % contest)
	# The old summary: every line in quarter order, the first five kept.
	var old := []
	for q in range(1, 5):
		for t in MatchNotes.calls_lines(res, me, q):
			old.append("Q%d  ·  %s" % [q, str(t)])
	_check(_quarters_in(old.slice(0, 5)) == [1, 1, 1, 1, 1],
			"calls: in order, the first five are all Q1 (the bug reproduced): %s" % str(_quarters_in(old.slice(0, 5))))
	var got := MatchNotes.full_time_calls(res, me, {})
	_check(got.size() == 5, "calls: the summary keeps five of %d (got %d)" % [all, got.size()])
	var qs := _quarters_in(got)
	_check(qs == [1, 1, 2, 3, 4], "calls: each quarter's first call, then Q1's second, in quarter order (got %s)" % str(qs))
	_check(got[0] == old[0] and got[2] == old[5] and got[3] == old[10] and got[4] == old[15],
			"calls: each quarter's first line is its game plan")
	# Calls only late in the match: all five slots go to Q3 and Q4.
	for h in res["tactics_history"]:
		if int(h["quarter"]) <= 2:
			h["plans"][me] = {"gameplan": "balanced"}
	qs = _quarters_in(MatchNotes.full_time_calls(res, me, {}))
	_check(qs == [3, 3, 3, 4, 4], "calls: late calls only fill from Q3 and Q4 (got %s)" % str(qs))
	# A line Why already quoted for its quarter is not said again.
	var q3 := str(MatchNotes.calls_lines(res, me, 3)[0])
	var told := {"q3": true, "call:" + q3: true}
	_check(not MatchNotes.full_time_calls(res, me, told).has("Q3  ·  " + q3), "calls: a call Why quoted is left out")


## A Q1 tag still in force in Q2 must not take Q2's place from the call made
## in Q2 (capture 2026-11-12: Q2 showed "Tag on ..." and dropped the new
## Through call). Q1 sets the tag; Q2 keeps it and adds a man to go through.
func _test_calls_new_call_before_carried() -> void:
	var res := _calls_every_quarter_result()
	var me := _side(res)
	var mine: Array = res["roster"][me]
	var theirs: Array = res["roster"][1 - me]
	var tag_id := str(theirs[1]["id"])
	var thru_id := str(mine[5]["id"])
	for h in res["tactics_history"]:
		var q := int(h["quarter"])
		if q == 1:
			h["plans"][me] = {"gameplan": "balanced", "tag_id": tag_id}
		elif q >= 2:
			h["plans"][me] = {"gameplan": "balanced", "tag_id": tag_id, "focus_fwd": thru_id}
	var q2: Array = MatchNotes.calls_lines(res, me, 2)
	_check(q2.size() == 2 and str(q2[0]).begins_with("Tag on"),
			"calls: fixture, Q2 lists the carried tag first (got %s)" % str(q2))
	var got := MatchNotes.full_time_calls(res, me, {}, 2)
	var want := "Q2  ·  " + str(q2[1])
	_check(got.has(want) and str(q2[1]).begins_with("Through"),
			"calls: Q2's place goes to the Through call made in Q2 (got %s)" % str(got))
	_check(not got.has("Q2  ·  " + str(q2[0])), "calls: the Q1 tag carried into Q2 waits behind it (got %s)" % str(got))
	# With room, the carried tag still shows after the new call.
	var all := MatchNotes.full_time_calls(res, me, {}, 20)
	_check(all.find(want) < all.find("Q2  ·  " + str(q2[0])), "calls: in Q2 the new call reads before the carried tag")


## On the screen: the full-time Summary's Your calls lists Q3 and Q4.
func _test_calls_every_quarter_screen() -> void:
	_tree.root.size = Vector2i(390, 844)
	var res := _calls_every_quarter_result()
	GameState.last_match = res
	var ft := await _review()
	var box: Node = ft.find_child("FullTimeCalls", true, false) if ft != null else null
	_check(box != null and (box as Control).is_visible_in_tree(), "calls: the Summary shows Your calls")
	# A line naming a player is a RichTextLabel; its words ride as "plain".
	var text := ""
	if box != null:
		for c in box.get_children():
			text += str(c.get_meta("plain", c.get("text"))) + "\n"
	for q in range(1, 5):
		_check(text.contains("Q%d  ·  " % q), "calls: Your calls lists a Q%d call:\n%s" % [q, text])
	Router.stack = []
	Router.go("hub")
	await _settle(4)
