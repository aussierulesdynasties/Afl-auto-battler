extends RefCounted
## Row 64 (4.Q8): the prospect you create at New Career, Alastair McNeil,
## enters the first National Draft and his story is told (OwnProspect).
## Run through tests/run_own_prospect_tests.gd.

var failures: Array[String] = []
var checks := 0

const SEED := 6464
## The real-lists club the coach takes: Adelaide start with room under the
## 38 senior spots, so they pick in the opening National Draft (a full club,
## Geelong among them, passes every pick).
const CLUB := "ADE"


const Tap := preload("res://tests/tap.gd")


func run() -> void:
	failures.clear()
	checks = 0
	_t("_test_spec")
	_t("_test_redraft_first_draft")
	_t("_test_real_lists_first_draft")
	_t("_test_career_beats")
	_t("_test_real_paths")
	_t("_test_news_front")
	_t("_test_save_reload")
	await _t("_test_marks_on_screen")
	GameState.replay_seed = 0
	GameState.reset()
	print(Ran.line("Own prospect", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## Alastair McNeil as the coach would make him in the Club Forge.
func _alastair() -> Dictionary:
	return {"first": "Alastair", "last": "McNeil", "nickname": "", "role": "FWD", "role2": "",
			"height_cm": 194, "style": "key_forward", "strengths": ["marking"], "weaknesses": ["pressure"],
			"foot": "R", "number_pref": 0, "fav_club": "", "look": {}}


func _gs():
	return GameState


## A fresh career with Alastair made.
func _fresh() -> void:
	var gs = _gs()
	gs.reset()
	gs.replay_seed = SEED
	gs.career_seed = SEED
	_check(gs.add_custom_prospect(_alastair()) == "", "(setup) Alastair McNeil is created")


func _mine(gs) -> Array:
	return (gs.news as Array).filter(func(n): return str(n.get("kind", "")) == OwnProspect.KIND)


func _own(gs) -> Dictionary:
	return OwnProspect.locate(gs)["p"]


## Run the National Draft on the board: the user's club takes the top of the
## board, the AI does the rest. No preference for him either way, unless
## `take_him`: then the user's first pick is him. An overlooked prospect of
## the opening real-lists draft leaves the game with the draft's pool, so the
## tests that follow his career have your club take him.
func _run_draft(gs, take_him := false) -> void:
	var guard := 0
	while not gs.draft.is_finished() and guard < 600:
		guard += 1
		if gs.draft.is_user_turn():
			var board: Array = gs.draft.board("", "", "", "overall", true)
			var pick: Dictionary = board[0] if not board.is_empty() else {}
			if take_him:
				for c in board:
					if str(c.get("id", "")) == str(gs.custom_prospect_id):
						pick = c
						take_him = false
			if pick.is_empty() or not gs.draft.pick(pick):
				break
		else:
			var club: String = gs.draft.current_club()
			var cand: Dictionary = gs.draft._best_ai_pick(club)
			if cand.is_empty() or not gs.draft._draft_pick(club, cand):
				gs.draft._skip_current_pick()


func _test_spec() -> void:
	var spec := _alastair()
	_check(Prospects.forge_problem(spec) == "", "Alastair McNeil is a valid Club Forge prospect")
	var p := Prospects.make_custom(spec, 2027, SEED)
	_check(GameDB.player_display_name(p) == "Alastair McNeil" and bool(p.get("user_created", false)),
			"He keeps his name and is marked as created")


func _test_redraft_first_draft() -> void:
	_fresh()
	var gs = _gs()
	gs.begin_draft()
	var ids: Array = gs.draft.pool.map(func(q): return str(q["id"]))
	_check(not ids.has(gs.custom_prospect_id), "He is not in the League Draft: he is a prospect")
	var p := _own(gs)
	_check(OwnProspect.locate(gs)["at"] == "pool" and int(p["draft_year"]) == gs.season_year,
			"He is in the first National Draft class (%d)" % gs.season_year)
	_check(OwnProspect.tag(p) == OwnProspect.TAG, "His row and profile say %s" % OwnProspect.TAG)
	var told := _mine(gs)
	_check(told.size() == 1 and str(told[0]["text"]).contains("Alastair McNeil")
			and str(told[0]["text"]).contains("has nominated for the %d National Draft" % gs.season_year),
			"The news tells his nomination (%s)" % str(told))
	# The League Draft done, the first season played (fast-forwarded), then
	# the first National Draft: he is taken, or overlooked, and the news says which.
	gs.start_season("ADE", GameDB.club_list("ADE"))
	_check(OwnProspect.locate(gs)["at"] == "pool", "He waits in the class through the first season")
	gs.season.round_index = gs.season.fixture.size()
	# In play the National Draft opens after the finals: the season is over.
	gs.season.finals = {"done": true}
	_check(gs.begin_intake_draft(), "(setup) the first National Draft opens")
	var year: int = gs.season_year
	var before: int = _mine(gs).size()
	_run_draft(gs)
	_check(gs.draft.is_finished() and gs.finish_intake_draft(), "(setup) the draft finishes")
	_check(_mine(gs).size() == before + 1,
			"Draft day tells one line about him, and no season he never had (%s)" % str(_mine(gs).map(func(n): return n["text"])))
	_draft_beat(gs, year, "redraft")


func _test_real_lists_first_draft() -> void:
	_fresh()
	var gs = _gs()
	gs.begin_real_lists()
	var told := _mine(gs)
	_check(told.size() == 1 and str(told[0]["text"]).contains("has nominated for the %d National Draft" % GameDB.DATA_SEASON),
			"Real lists: he nominates for the 2026 National Draft (%s)" % str(told))
	var ids: Array = gs.draft.pool.map(func(q): return str(q["id"]))
	_check(ids.has(gs.custom_prospect_id), "Real lists: he is in the opening National Draft pool")
	gs.choose_real_club(CLUB)
	_run_draft(gs, true)
	_check(gs.draft.is_finished() and gs.finish_intake_draft(), "(setup) the opening draft finishes")
	_draft_beat(gs, GameDB.DATA_SEASON, "real lists")


## After his first National Draft: one line, and it is the truth.
func _draft_beat(gs, year: int, label: String) -> void:
	var now := OwnProspect.locate(gs)
	var p: Dictionary = now["p"]
	var lines: Array = _mine(gs).map(func(n): return str(n["text"]))
	var taken := lines.filter(func(t): return t.contains("National Draft") and t.contains("with pick"))
	var missed := lines.filter(func(t): return t.contains("overlooked in the %d National Draft" % year))
	if str(now["at"]) == "club":
		var want := "%s have taken Alastair McNeil with pick %d in the %d National Draft." % [
				GameDB.club_name(str(now["club"])), int(p.get("drafted_pick", 0)), year]
		_check(taken.size() == 1 and str(taken[0]) == want and missed.is_empty(),
				"%s: the news names his club and pick (%s / %s)" % [label, want, str(lines)])
	else:
		_check(missed.size() == 1 and taken.is_empty(),
				"%s: the news says he was overlooked (%s)" % [label, str(lines)])
	print("  %s: %s" % [label, " / ".join(lines)])
	# A second look tells nothing new.
	var n: int = _mine(gs).size()
	OwnProspect.check(gs, year)
	OwnProspect.check(gs)
	_check(_mine(gs).size() == n, "%s: nothing is told twice" % label)


## His career from the news: taken, debut, a move, delisted, re-signed, a
## season, retired. The moves are made by hand; the lines are the system's.
func _test_career_beats() -> void:
	_fresh()
	var gs = _gs()
	gs.begin_real_lists()
	gs.choose_real_club(CLUB)
	_run_draft(gs, true)
	gs.finish_intake_draft()
	var id: String = gs.custom_prospect_id
	var p := _own(gs)
	# Wherever the draft left him, put him on Carlton's list as pick 9.
	_take_out(gs, id)
	p["drafted_type"] = "national"
	p["drafted_pick"] = 9
	p["drafted_year"] = 2026
	p["club"] = "CAR"
	gs.custom_prospect_story["at"] = "pool"
	gs.custom_prospect_story["club"] = ""
	(gs.season.lists["CAR"] as Array).append(p)
	OwnProspect.check(gs)
	_check(_last(gs) == "Carlton have taken Alastair McNeil with pick 9 in the 2026 National Draft.",
			"Taken: club and pick (%s)" % _last(gs))
	gs.season_tally[id] = {"games": 1, "goals": 2}
	OwnProspect.check(gs)
	_check(_last(gs) == "Alastair McNeil made his AFL debut for Carlton.", "His debut (%s)" % _last(gs))
	OwnProspect.check(gs)
	_check(_count(gs, "debut") == 1, "A debut is told once")
	_take_out(gs, id)
	p["club"] = "ESS"
	(gs.season.lists["ESS"] as Array).append(p)
	OwnProspect.check(gs)
	_check(_last(gs) == "Alastair McNeil has moved from Carlton to Essendon.", "A move (%s)" % _last(gs))
	OwnProspect.check(gs)
	_check(_count(gs, "has moved from") == 1, "A move is told once")
	gs.season_tally[id] = {"games": 12, "goals": 20}
	gs.season.finals = {"done": true}
	OwnProspect.check(gs)
	_check(_last(gs) == "Alastair McNeil's 2027: 12 games and 20 goals for Essendon.", "His season (%s)" % _last(gs))
	OwnProspect.check(gs)
	_check(_mine(gs).filter(func(n): return str(n["text"]).contains("'s 2027:")).size() == 1, "A season is told once")
	gs.season.finals = {}
	_take_out(gs, id)
	gs.free_agents.append(p)
	OwnProspect.check(gs)
	_check(_last(gs) == "Alastair McNeil is off Essendon's list and looking for a new club.", "Delisted (%s)" % _last(gs))
	OwnProspect.check(gs)
	_check(_count(gs, "looking for a new club") == 1, "A delisting is told once")
	_take_out(gs, id)
	(gs.season.lists["ESS"] as Array).append(p)
	OwnProspect.check(gs)
	_check(_last(gs) == "Essendon have signed Alastair McNeil.", "Signed again (%s)" % _last(gs))
	OwnProspect.check(gs)
	_check(_count(gs, "have signed") == 1, "A re-signing is told once")
	_take_out(gs, id)
	gs.departed_names[id] = p
	OwnProspect.check(gs)
	_check(_last(gs) == "Alastair McNeil's playing career is over: 12 games and 20 goals.",
			"His career ends with his record (%s)" % _last(gs))
	_check(OwnProspect.over_line("Alastair McNeil", 0, 0) == "Alastair McNeil's playing career is over without a senior game."
			and OwnProspect.season_line("Alastair McNeil", "ESS", 2028, {}) == "Alastair McNeil did not play a senior game for Essendon in 2028.",
			"A bust is told plainly")
	_check(_mine(gs).all(func(n): return str(n["text"]).contains("Alastair McNeil")),
			"Every line names him as created, in this name mode")
	gs.show_real_names = not gs.show_real_names
	_check(GameDB.player_display_name(p) == "Alastair McNeil", "His name is his in the other name mode too")
	gs.show_real_names = not gs.show_real_names


## The same story through the game's own paths, no look called by hand: a
## round he plays (his debut), a trade, the season to its end, the next
## National Draft and the rollover he retires at. The news keeps only the
## latest lines, so each of his is gathered as it is told.
func _test_real_paths() -> void:
	_fresh()
	var gs = _gs()
	gs.begin_real_lists()
	gs.choose_real_club(CLUB)
	_run_draft(gs, true)
	gs.finish_intake_draft()
	var id: String = gs.custom_prospect_id
	var p := _own(gs)
	var told: Array = []
	_gather(gs, told)
	told.clear()
	# Wherever the draft left him, he is on your list and named in your side.
	_take_out(gs, id)
	p["club"] = gs.my_club
	(gs.season.lists[gs.my_club] as Array).insert(0, p)
	if not is_same(gs.my_list, gs.season.lists[gs.my_club]):
		gs.my_list.insert(0, p)
	var sel: Dictionary = gs.current_side()
	var fwd: Array = sel.get("FWD", [])
	_check(not fwd.is_empty(), "(setup) your side has a forward line")
	if not fwd.is_empty() and not fwd.has(id):
		fwd[0] = id
	gs.set_selection(sel)
	# The hand move above is setup, not story: the story knows where he is.
	gs.custom_prospect_story["at"] = "club"
	gs.custom_prospect_story["club"] = gs.my_club
	gs.advance()
	_gather(gs, told)
	_check(gs.games_played(p) >= 1, "(setup) he plays the round")
	_check(_has(told, "made his AFL debut for Adelaide") == 1, "A round played tells his debut (%s)" % str(told))
	gs.advance()
	_gather(gs, told)
	_check(_has(told, "debut") == 1, "The next round does not tell it again (%s)" % str(told))
	# A trade: Adelaide send him to Carlton.
	gs._execute_trade(gs.my_club, "CAR", [p], [])
	_gather(gs, told)
	_check(_has(told, "has moved from Adelaide to Carlton") == 1, "A trade tells his move (%s)" % str(told))
	# The season to its end: one line with his year at Carlton.
	var guard := 0
	while not gs.season.is_season_over() and guard < 60:
		guard += 1
		gs.advance()
		_gather(gs, told)
	var year: int = gs.season_year
	_check(gs.season.is_season_over(), "(setup) the season is played out")
	var head := "Alastair McNeil's %d:" % year
	var lines := told.filter(func(t): return t.begins_with(head) or t.contains("did not play a senior game"))
	_check(lines.size() == 1 and str(lines[0]).ends_with("for Carlton."),
			"The season's end tells his year at Carlton, once (%s)" % str(told))
	# The next National Draft and the rollover. Wherever he is when the
	# draft closes, he is 38 by then: he retires at the rollover.
	var n: int = told.size()
	_check(gs.begin_intake_draft(), "(setup) the National Draft opens")
	_run_draft(gs)
	(OwnProspect.locate(gs)["p"] as Dictionary)["age"] = 38.0
	_check(gs.draft.is_finished() and gs.finish_intake_draft(), "(setup) the draft and rollover finish")
	_gather(gs, told)
	_check(OwnProspect.locate(gs)["at"] == "gone", "(setup) he retires at the rollover")
	var after := told.slice(n)
	_check(not after.is_empty() and str(after[-1]).begins_with("Alastair McNeil's playing career is over: ")
			and _has(after, "career is over") == 1,
			"The rollover tells his career's end, once (%s)" % str(after))
	_check(_has(after, "Alastair McNeil's %d" % year) == 0 and _has(after, "did not play a senior game") == 0,
			"The draft and rollover tell no season line (%s)" % str(after))
	print("  real paths: %s" % " / ".join(told))


## Adds his lines told since the last call to `into`, oldest first.
func _gather(gs, into: Array) -> void:
	var fresh: Array = []
	for item in gs.news:
		if str(item.get("kind", "")) == OwnProspect.KIND and not item.has("_gathered"):
			item["_gathered"] = true
			fresh.push_front(str(item["text"]))
	into.append_array(fresh)


func _has(lines: Array, text: String) -> int:
	return lines.filter(func(t): return str(t).contains(text)).size()

func _take_out(gs, id: String) -> void:
	var all: Array = [gs.league_lists]
	if gs.season != null:
		all.append(gs.season.lists)
	for lists in all:
		for code in lists:
			var arr: Array = lists[code]
			for i in range(arr.size() - 1, -1, -1):
				if str(arr[i].get("id", "")) == id:
					arr.remove_at(i)
	for i in range(gs.free_agents.size() - 1, -1, -1):
		if str(gs.free_agents[i].get("id", "")) == id:
			gs.free_agents.remove_at(i)
	gs.draftee_pool = gs.draftee_pool.filter(func(q): return str(q.get("id", "")) != id)
	if gs.draft != null:
		gs.draft.pool = gs.draft.pool.filter(func(q): return str(q.get("id", "")) != id)


## How many lines about him contain `text`.
func _count(gs, text: String) -> int:
	return _mine(gs).filter(func(n): return str(n["text"]).contains(text)).size()


func _last(gs) -> String:
	var told := _mine(gs)
	return str(told[0]["text"]) if not told.is_empty() else ""


func _test_news_front() -> void:
	var item := {"kind": OwnProspect.KIND, "club": "CAR", "text": "Carlton have taken Alastair McNeil with pick 9 in the 2026 National Draft."}
	var mine := NewsFront.story(item, "CAR")
	var theirs := NewsFront.story(item, "GEE")
	_check(str(theirs["club"]) == "CAR" and str(theirs["headline"]) == str(item["text"])
			and str(theirs["standfirst"]) == "The player you created." and not bool(theirs["mine"]),
			"The front page tells his line in his club's colours")
	_check(bool(mine["mine"]) and int(mine["weight"]) > int(theirs["weight"]), "At your club he is your story")


func _test_save_reload() -> void:
	_fresh()
	var gs = _gs()
	gs.begin_real_lists()
	gs.choose_real_club(CLUB)
	var before: Dictionary = gs.custom_prospect_story.duplicate(true)
	_check(not before.is_empty() and gs.save_career() and gs.load_career(), "(setup) save and reload mid-draft")
	_check(gs.custom_prospect_story == before, "His story survives a reload (%s)" % str(gs.custom_prospect_story))
	_check(OwnProspect.locate(gs)["at"] == "pool", "He is still in the draft pool after the reload")
	var n: int = _mine(gs).size()
	OwnProspect.check(gs)
	_check(_mine(gs).size() == n, "A reload tells nothing again")
	# Still in the pool when a draft closes: overlooked, once a year; and the
	# day he leaves the pool unpicked, the news says so.
	OwnProspect.check(gs, 2026)
	OwnProspect.check(gs, 2026)
	_check(_last(gs) == "Alastair McNeil was overlooked in the 2026 National Draft."
			and _mine(gs).size() == n + 1, "Overlooked, told once (%s)" % _last(gs))
	_take_out(gs, gs.custom_prospect_id)
	OwnProspect.check(gs)
	_check(_last(gs) == "Alastair McNeil's time in the draft pool is over: no club took him.",
			"Unpicked and out of the pool (%s)" % _last(gs))
	# An old save has no story: a career reloaded with it absent starts the
	# story from where he is, without telling the past again.
	gs.custom_prospect_story = {}
	gs.save_career()
	gs.load_career()
	_check(gs.custom_prospect_story.is_empty(), "A save without his story loads without one")


## His draft-board row and his profile say "Created by you"; a finger's tap on
## the row opens him.
func _test_marks_on_screen() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		GameState.set_setting("seen_%s_intro" % key, true)
	_fresh()
	GameState.begin_real_lists()
	GameState.choose_real_club(CLUB)
	var id: String = GameState.custom_prospect_id
	tree.root.size = Vector2i(390, 844)
	var ui: Control = load("res://scenes/DraftScene.tscn").instantiate()
	tree.root.add_child(ui)
	await _settle(tree)
	var done = ui.find_child("MeetingDone", true, false)
	if done != null:
		await Tap.tap(done)
		await _settle(tree)
	ui.set("_search", "McNeil")
	ui.call("_refresh_board", true)
	await _settle(tree)
	var mark: Label = ui.find_child("Own_" + id, true, false)
	var inspect: Button = ui.find_child("Inspect_" + id, true, false)
	_check(inspect != null, "His row is on the board when searched")
	_check(mark != null and mark.text == OwnProspect.TAG and mark.is_visible_in_tree(),
			"His draft row says %s" % OwnProspect.TAG)
	if inspect != null:
		var why: String = await Tap.tap(inspect)
		_check(why == "", "A finger's tap on his row reaches it (%s)" % why)
		await _settle(tree)
		_check(ui.find_child("PlayerDetail", true, false) != null, "The tap opens his details")
	ui.queue_free()
	await _settle(tree)
	var box := VBoxContainer.new()
	PlayerSheet._identity(box, _own(GameState))
	var line: Label = box.find_child("ProfileCreatedByYou", true, false)
	_check(line != null and line.text == "Created by you at the start of this career.",
			"His profile says he is the player you created")
	box.free()


func _settle(tree: SceneTree) -> void:
	for i in range(5):
		await tree.process_frame
