extends SceneTree
## godot --headless --path . --script tests/run_stats_tests.gd
## Season stats (the Stats patch, ROADMAP §1.11): the hub's Season stats
## button, every section, and the numbers behind them.
const Tap := preload("res://tests/tap.gd")
const SUITE_SEED := 2031

var _state: Node
# Loaded, not named: a SceneTree script compiles before the autoloads exist.
var _SB
var _CA
## Loaded at run time: in --script mode a class that reads an autoload
## (GameDB) cannot compile into this script.
var _aw
var _cs
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_SB = load("res://scripts/sim/StatBook.gd")
	_CA = load("res://scripts/sim/Career.gd")
	_aw = load("res://scripts/sim/Awards.gd")
	_cs = load("res://scripts/state/CareerSave.gd")
	_state.autosave_enabled = false
	# These tests drive the hub for other things: no club card opens over it.
	_state.event_sheets = false
	_state.save_path = "user://test_stats.save"
	_state.settings_path = "user://test_stats_settings.cfg"
	# Return visits: the first-visit intros (FirstVisitIntro.gd) have their own suite.
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.show_real_names = false
	_state.replay_seed = SUITE_SEED
	var ev = load("res://tests/test_stats_events.gd").new()
	ev.run()
	_checks += ev.checks
	_failures.append_array(ev.failures)
	var db = root.get_node("GameDB")
	_state.reset()
	_state.start_season("COL", db.club_list("COL"))
	# Before any round: no press conference sits over the hub.
	await _t("_test_intro")
	await _t("_test_hub_button")
	for sz in [Vector2i(390, 844), Vector2i(1920, 1080)]:
		await _t("_test_ladder_only_in_season_stats", [sz])
	await _t("_test_awards_early")
	await _t("_test_trophies_unplayed")
	_t("_test_club_code_colours")
	_t("_test_finals_cell")
	for i in range(4):
		_state.advance()
	await _t("_test_sections")
	# The awards read the season after four rounds: before anything below
	# plays it on (the fixture's finals test plays it to the end).
	await _t("_test_awards_races")
	await _t("_test_awards_unchanged")
	await _t("_test_awards_open_fast")
	await _t("_test_awards_ties")
	_t("_test_rising_star_rules")
	await _t("_test_rising_star_saves")
	await _t("_test_awards_awarded")
	await _t("_test_players_section")
	for sz in [Vector2i(390, 844), Vector2i(360, 800), Vector2i(1280, 720)]:
		await _t("_test_ratings_section", [sz])
	_t("_test_club_per_game")
	_t("_test_season_book")
	_t("_test_book_rates")
	for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
		await _t("_test_fixture", [sz])
	# 320 x 693: a 390 x 844 window on a scaled desktop (ScreenLayout's 320-unit floor).
	for sz in [Vector2i(390, 844), Vector2i(320, 693), Vector2i(1280, 720)]:
		await _t("_test_ladder", [sz])
	for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
		await _t("_test_team_rating", [sz])
	for w in [366.0, 680.0]:
		await _t("_test_hub_ladder_heads", [w])
	await _t("_test_trophies_early")
	await _t("_test_fixture_finals")
	await _t("_test_trophies")
	await _t("_test_readability_b1")
	await _t("_test_whole_text_checks_bite")
	print(Ran.line("Stats", self, [ev]))
	quit(0 if _failures.is_empty() else 1)


## The first visit explains the hub in two lines, once; "Got it" closes it.
func _test_intro() -> void:
	root.size = Vector2i(390, 844)
	_state.set_setting("seen_season_stats_intro", false)
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	var intro: Node = s.find_child("SeasonStatsIntro", true, false)
	var ok: Button = s.find_child("SeasonStatsIntroOk", true, false)
	_check(intro != null and ok != null, "The first visit to Season stats explains it")
	if ok != null:
		_check((await Tap.tap(ok)) == "", "Got it takes a tap")
		await _settle()
	_check(s.find_child("SeasonStatsIntro", true, false) == null
			and bool(_state.get_setting("seen_season_stats_intro", false)), "...and closes it for good")
	s.queue_free()
	await _settle()
	var again: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(again)
	await _settle()
	_check(again.find_child("SeasonStatsIntro", true, false) == null, "The next visit goes straight to the stats")
	again.queue_free()
	await _settle()


## The hub's Season stats button takes a tap and opens the hub.
func _test_hub_button() -> void:
	root.size = Vector2i(1280, 720)
	_state.set_setting("seen_weekly_loop_intro", true)
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	var b: Button = hub.find_child("SeasonStats", true, false)
	_check(b != null and hub.find_child("FullLadder", true, false) == null,
			"The hub offers Season stats in place of Full ladder")
	# Row 84 (T3.Q13, T9.Q29): the hub's nav bar has no Ladder entry.
	var navs := []
	for n in hub.find_children("*", "Button", true, false):
		if (n as Button).text.to_lower().contains("ladder"):
			navs.append(str(n.name))
	_check(navs.is_empty(), "No hub button says Ladder (%s)" % str(navs))
	if b != null:
		var got := await Tap.tap(b)
		_check(got == "", "Season stats takes a tap (%s)" % got)
	hub.queue_free()
	await _settle()


## Row 84 (ruling: docs/TODO.md rulings, T3.Q13 / T9.Q29): the ladder lives
## only in Season stats. No Ladder screen or route, no Ladder button in the
## hub's nav row; a real tap on the hub's Ladder heading opens Season stats,
## and a real tap on its Ladder tab shows the ladder.
func _test_ladder_only_in_season_stats(sz: Vector2i) -> void:
	var tag := "%dx%d" % [sz.x, sz.y]
	var old_size := root.size
	var old_stack: Array = root.get_node("Router").stack.duplicate()
	var old_scene := current_scene
	var hub_stats = load("res://scripts/ui/StatsHubScene.gd")
	var old_current := str(hub_stats.current)
	_check(not ResourceLoader.exists("res://scenes/LadderScene.tscn")
			and not ResourceLoader.exists("res://scripts/ui/LadderScene.gd"), "No Ladder screen exists")
	var routes: Dictionary = load("res://scripts/core/Router.gd").SCENES
	for k in routes:
		_check(not str(k).to_lower().contains("ladder") and not str(routes[k]).to_lower().contains("ladder"),
				"No route leads to a Ladder screen (%s)" % k)
	root.size = sz
	# Awards open last, so landing on the ladder has to come from the taps.
	hub_stats.current = "awards"
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	var navs := 0
	for name in ["HubFooter", "HubFooterWide"]:
		var row: Node = hub.find_child(name, true, false)
		if row == null:
			continue
		for b in row.find_children("*", "Button", true, false):
			navs += 1
			_check(not (b as Button).text.to_lower().contains("ladder"),
					"The hub nav row has no Ladder button (%s: %s)" % [tag, (b as Button).text])
	_check(navs > 0, "The hub nav row is there to check (%s)" % tag)
	var link: Button = hub.find_child("SeasonStats", true, false)
	_check(link != null, "The hub's Ladder heading is there (%s)" % tag)
	if link != null:
		var got := await Tap.tap(link)
		_check(got == "", "The Ladder heading takes a real tap (%s: %s)" % [tag, got])
		await _settle()
	var s: Node = current_scene
	_check(s != null and s.scene_file_path == "res://scenes/StatsHubScene.tscn",
			"The tap opens Season stats (%s)" % tag)
	if s != null and s.scene_file_path == "res://scenes/StatsHubScene.tscn":
		var tab: Button = s.find_child("Section_ladder", true, false)
		_check(tab != null, "Season stats has a Ladder tab (%s)" % tag)
		if tab != null:
			var got2 := await Tap.tap(tab)
			_check(got2 == "", "The Ladder tab takes a real tap (%s: %s)" % [tag, got2])
			await _settle()
			tab = s.find_child("Section_ladder", true, false)
			var sb := tab.get_theme_stylebox("normal") as StyleBoxFlat if tab != null else null
			_check(sb != null and sb.border_width_bottom == 2, "The Ladder tab is the selected one (%s)" % tag)
			_check(s.find_child("LadderHeader", true, false) != null,
					"The ladder shows in Season stats (%s)" % tag)
	# Leave the tree as it was: no stray Season stats, stack, section or size.
	if is_instance_valid(hub):
		hub.queue_free()
	if s != null and s != old_scene and is_instance_valid(s):
		s.queue_free()
	if is_instance_valid(old_scene):
		current_scene = old_scene
	root.get_node("Router").stack = old_stack
	hub_stats.current = old_current
	root.size = old_size
	await _settle()


## Ratings (director, 2026-10-11): every player who has played, ranked by
## Player rating a game from the season book; a player is ranked once he has
## played half his club's games, the rest follow, still listed. Your club's
## players carry its colour. A real tap opens it; nothing is cut off.
func _test_ratings_section(sz: Vector2i) -> void:
	var tag := "%dx%d" % [sz.x, sz.y]
	var Hub = load("res://scripts/ui/StatsHubScene.gd")
	var points: Dictionary = load("res://scripts/ui/match/MatchNotes.gd").RATING_POINTS
	root.size = sz
	Hub.current = "ladder"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	var tab: Button = s.find_child("Section_ratings", true, false)
	_check(tab != null and tab.text == "Ratings" and (await Tap.tap(tab)) == "", "The Ratings tab takes a tap (%s)" % tag)
	await _settle()
	var sec: Node = s.find_child("StatsRatings", true, false)
	_check(sec != null, "Ratings opens (%s)" % tag)
	if sec == null:
		s.queue_free()
		await _settle()
		return
	# The list opens with its first rows and adds the rest a batch a frame.
	var list_node: Node = s.find_child("RatingsList", true, false)
	var waited := 0
	while list_node != null and not bool(list_node.get_meta("filled", true)) and waited < 120:
		await process_frame
		waited += 1
	_check(list_node != null and bool(list_node.get_meta("filled", false)),
			"The whole list is built within a few frames (%s: %d frames)" % [tag, waited])
	# The expected list, worked out here from the season book and the ladder.
	var want := []
	for id in _state.season_stats:
		var e: Dictionary = _state.season_stats[id]
		var g := int(e.get("games", 0))
		if g <= 0:
			continue
		var total := 0.0
		for k in points:
			total += float(points[k]) * float((e.get("s", {}) as Dictionary).get(k, 0.0))
		total = maxf(0.0, total)
		var club := ""
		for code in _state.season.lists:
			for p in _state.season.lists[code]:
				if str(p["id"]) == str(id):
					club = str(code)
		if club == "":
			club = str(e.get("club", ""))
		var cg := int((_state.season.ladder.get(club, {}) as Dictionary).get("p", 0))
		want.append({"id": str(id), "per": total / float(g), "total": total, "q": g * 2 >= cg, "club": club})
	var rows := s.find_children("RatingRow_*", "Button", true, false)
	_check(rows.size() == want.size() and rows.size() > 100,
			"Every player who has played is listed (%s: %d of %d)" % [tag, rows.size(), want.size()])
	var by_id := {}
	for w in want:
		by_id[str(w["id"])] = w
	var order_ok := true
	var figs_ok := true
	var seen_unq := false
	var last := INF
	var q_n := 0
	var unq_n := 0
	for r in rows:
		var w: Dictionary = by_id.get(str(r.name).trim_prefix("RatingRow_"), {})
		if w.is_empty():
			order_ok = false
			continue
		if bool(w["q"]):
			q_n += 1
			if seen_unq or float(w["per"]) > last + 0.0001:
				order_ok = false
			last = float(w["per"])
		else:
			if not seen_unq:
				seen_unq = true
				last = INF
			unq_n += 1
			if float(w["per"]) > last + 0.0001:
				order_ok = false
			last = float(w["per"])
		var pg: Label = r.find_child("PerGame", true, false)
		if pg == null or pg.text != "%.1f" % float(w["per"]):
			figs_ok = false
	_check(order_ok and q_n > 0, "Ranked players first, best rating a game first; the rest after them (%s: %d ranked, %d not)" % [tag, q_n, unq_n])
	_check(figs_ok, "Each row's figure is his rating points over his games (%s)" % tag)
	_check(unq_n == 0 or s.find_child("RatingsUnranked", true, false) != null,
			"The players short of half their club's games sit under their own line (%s)" % tag)
	var first_rank: Label = rows[0].find_child("Rank", true, false) if not rows.is_empty() else null
	_check(first_rank != null and first_rank.text == "1", "The top row is ranked 1 (%s)" % tag)
	# Your club's rows carry its colour; nobody else's does.
	var mine_ok := true
	var mine_n := 0
	for r in rows:
		var w: Dictionary = by_id.get(str(r.name).trim_prefix("RatingRow_"), {})
		var sb := (r as Button).get_theme_stylebox("normal") as StyleBoxFlat
		var lit := sb != null and sb.bg_color.a > 0.0
		if str(w.get("club", "")) == _state.my_club:
			mine_n += 1
		if lit != (str(w.get("club", "")) == _state.my_club):
			mine_ok = false
	_check(mine_ok and mine_n > 0, "Your club's players are highlighted, and only they are (%s: %d)" % [tag, mine_n])
	# Nothing cut off: the rule line wraps on screen, every label of the first
	# rows sits inside the screen, and the figures fit their cells.
	var rule: Label = s.find_child("RatingsRule", true, false)
	_check(rule != null and rule.get_global_rect().end.x <= sz.x + 1 and rule.get_line_count() >= 1
			and rule.get_visible_line_count() == rule.get_line_count(), "The ranking rule is said in full at the top (%s)" % tag)
	var intro: Control = s.find_child("RatingsIntro", true, false)
	var first_row: Control = s.find_child("RatingsList", true, false)
	var heading_x: float = (intro.get_child(0).get_child(0) as Control).get_global_rect().position.x if intro != null else -1.0
	_check(intro != null and first_row != null and heading_x >= (sec as Control).get_global_rect().position.x + 8.0 and heading_x >= 8.0,
			"The Ratings heading starts inside the page, not on its edge (%s)" % tag)
	var head := []
	for i in range(mini(12, rows.size())):
		head.append(rows[i])
	var off := []
	for r in head:
		for l in (r as Node).find_children("*", "Label", true, false):
			if l.get_global_rect().end.x > sz.x + 1 or l.get_global_rect().position.x < -1:
				off.append(str(l.name))
		var pg: Label = (r as Node).find_child("PerGame", true, false)
		if pg != null and not _label_fits(pg):
			off.append("PerGame")
	_check(off.is_empty(), "Nothing on the Ratings rows is cut off (%s: %s)" % [tag, str(off)])
	# Whose team he plays for, by name, on every row and never cut to a letter.
	var club_bad := []
	for r in rows:
		var w: Dictionary = by_id.get(str(r.name).trim_prefix("RatingRow_"), {})
		var cl: Label = (r as Node).find_child("Club", true, false)
		var want_club := str(root.get_node("GameDB").club_short(str(w.get("club", ""))))
		var sl: Label = (r as Node).find_child("Season", true, false)
		if cl == null or not cl.text.begins_with(want_club) or not _label_fits(cl) or (r as Node).find_child("ClubMark", true, false) == null 				or sl == null or not _label_fits(sl):
			club_bad.append(str(r.name))
	_check(club_bad.is_empty(), "Every row names the player's club in full, with its guernsey, and his games and total in full (%s: %d bad, %s)" % [tag, club_bad.size(), str(club_bad.slice(0, 3))])
	# A real tap on a row opens his season.
	if not rows.is_empty():
		var got: String = await Tap.tap(rows[0])
		await _settle()
		_check(got == "" and s.find_child("PlayerStatsSheet", true, false) != null, "A tap on a player opens his season (%s: %s)" % [tag, got])
	s.queue_free()
	Hub.current = "ladder"
	await _settle()


## Every section opens, at a phone's width and a PC's.
func _test_sections() -> void:
	for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
		root.size = sz
		var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
		root.add_child(s)
		await _settle()
		if sz.x < 900:
			var all_in := true
			for key in ["ladder", "players", "ratings", "awards", "fixture", "coach"]:
				var tb: Control = s.find_child("Section_" + key, true, false)
				if tb == null or tb.get_global_rect().end.x > sz.x + 1 or tb.get_global_rect().position.x < -1:
					all_in = false
			_check(all_in and s.find_child("SectionStrip", true, false) == null,
					"Six short tabs fit one row on a phone, none cut and no sideways scroll (%dx%d)" % [sz.x, sz.y])
			_check(s.find_child("Section_players", true, false).text == "Players",
					"...with short names: Players (%dx%d)" % [sz.x, sz.y])
		_check(s.find_child("Section_trophies", true, false) == null,
				"The trophies are on the club's page now, not a Season stats tab (%dx%d)" % [sz.x, sz.y])
		for key in ["ladder", "players", "ratings", "awards", "fixture", "coach"]:
			var t: Button = s.find_child("Section_" + key, true, false)
			_check(t != null, "Season stats has a %s section (%dx%d)" % [key, sz.x, sz.y])
			if t == null:
				continue
			_check((await Tap.tap(t)) == "", "The %s tab takes a tap (%dx%d)" % [key, sz.x, sz.y])
			await _settle()
			var body: Node = s.find_child("SectionBody", true, false)
			_check(body != null and body.get_child_count() == 1, "The %s section builds (%dx%d)" % [key, sz.x, sz.y])
		s.queue_free()
		await _settle()


## Players: every player's season. A phone shows one stat at a time as a
## leaderboard (rank, guernsey, full name, one big figure); a wide screen the
## table with words in its headings. Per game, a rate's qualifiers, filters in
## a sheet, and a tap away from his season and career.
func _test_players_section() -> void:
	var SP = load("res://scripts/ui/stats/StatsPlayers.gd")
	var Hub = load("res://scripts/ui/StatsHubScene.gd")
	for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
		var tag := "%dx%d" % [sz.x, sz.y]
		var wide: bool = sz.x >= 900
		var list_name := "PlayersTable" if wide else "PlayersBoard"
		root.size = sz
		SP.reset_view()
		Hub.current = "players"
		var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
		root.add_child(s)
		await _settle()
		var table: Node = s.find_child(list_name, true, false)
		var rows := s.find_children("PlayerRow_*", "Button", true, false)
		_check(table != null and rows.size() == mini(SP.PAGE, (SP.rows() as Array).size()),
				"Players lists the competition's players, a page at a time (%s, %d rows)" % [tag, rows.size()])
		_check((s.find_child("PlayersTable", true, false) == null) == (not wide),
				"A phone shows the leaderboard, a wide screen the table (%s)" % tag)
		# The list is the season book, most disposals first.
		var cells := _column(s, "disposals")
		_check(_descending(cells) and not cells.is_empty(), "Sorted by disposals, most first (%s)" % tag)
		var top: Dictionary = SP.sorted_rows()[0]
		_check(not cells.is_empty() and int(cells[0]) == int(_SB.total(_state.season_stats[top["id"]], "disposals")),
				"The top row's disposals are his season total (%s)" % tag)
		var pick: Button = s.find_child("StatPick", true, false)
		_check(pick != null and pick.text == "Disposals", "The stat is chosen by its name (%s: %s)" % [tag, pick.text if pick else "-"])
		# The stats open as a sheet that scrolls under a finger, with Player
		# rating in it; a real tap on it ranks by it and closes the sheet.
		_check(pick != null and (await Tap.tap(pick)) == "", "The stat picker takes a tap (%s)" % tag)
		await _settle()
		var stat_sheet: Control = s.find_child("StatSheet", true, false)
		var in_scroll := false
		var pr: Button = stat_sheet.find_child("Stat_rating", true, false) if stat_sheet else null
		var last_stat: Button = stat_sheet.find_child("Stat_clangers", true, false) if stat_sheet else null
		var above: Node = last_stat
		var sc: ScrollContainer = null
		while above != null and above != stat_sheet:
			if above is ScrollContainer:
				in_scroll = true
				sc = above
			above = above.get_parent()
		_check(stat_sheet != null and pr != null and last_stat != null and in_scroll,
				"Every stat is in a scrolling sheet, down to the last (%s)" % tag)
		# The list is longer than the screen: a finger's drag moves it.
		var moved := false
		if sc != null and sc.get_v_scroll_bar().max_value > sc.size.y + 1.0:
			var mid := sc.get_global_rect().get_center()
			var press := InputEventScreenTouch.new()
			press.index = 0
			press.position = mid
			press.pressed = true
			Input.parse_input_event(press)
			Input.flush_buffered_events()
			await process_frame
			for step in range(6):
				var drag := InputEventScreenDrag.new()
				drag.index = 0
				drag.position = mid - Vector2(0, 40.0 * float(step + 1))
				drag.relative = Vector2(0, -40.0)
				Input.parse_input_event(drag)
				Input.flush_buffered_events()
				await process_frame
			var lift := InputEventScreenTouch.new()
			lift.index = 0
			lift.position = mid - Vector2(0, 240.0)
			lift.pressed = false
			Input.parse_input_event(lift)
			Input.flush_buffered_events()
			await _settle()
			moved = sc.scroll_vertical > 0
			_check(moved and s.find_child("StatSheet", true, false) != null and SP._sort == "disposals",
					"A finger's drag scrolls the stat list without picking a stat (%s: %d)" % [tag, sc.scroll_vertical])
		else:
			_check(sc != null and wide, "Only a wide screen fits the stat list without scrolling (%s)" % tag)
		_check(pr != null and (await Tap.tap(pr)) == "", "Player rating takes a tap (%s)" % tag)
		await _settle()
		pick = s.find_child("StatPick", true, false)
		var by_rating: Array = SP.sorted_rows()
		# Ranked by Player rating, the list opens on Per game (director, 2026-10-11).
		var mode_row: Node = s.find_child("StatMode", true, false)
		_check(SP._per_game and mode_row != null and mode_row.has_meta("current")
				and str((mode_row.get_meta("current") as Node).name) == "StatMode_per_game",
				"Ranked by Player rating, the list opens on Per game (%s)" % tag)
		var want := 0.0
		var points: Dictionary = load("res://scripts/ui/match/MatchNotes.gd").RATING_POINTS
		for k in points:
			want += float(points[k]) * float((by_rating[0]["s"] as Dictionary).get(k, 0.0))
		_check(s.find_child("StatSheet", true, false) == null and pick != null and pick.text == "Player rating"
				and by_rating.size() > 1 and is_equal_approx(SP.value(by_rating[0], "rating", false), maxf(0.0, want))
				and SP.value(by_rating[0], "rating", true) >= SP.value(by_rating[1], "rating", true)
				and SP.value(by_rating[0], "rating", false) > 0.0,
				"Player rating ranks the season by the match rating's points (%s: %s)" % [tag, pick.text if pick else "-"])
		SP.pick_stat("disposals")
		s.call("refresh")
		await _settle()
		await _settle()
		if wide:
			# Words in the headings, and a real tap on one reverses it.
			var head: Button = s.find_child("Sort_disposals", true, false)
			_check(head != null and head.text.begins_with("Disposals") and s.find_child("Sort_efficiency", true, false).text.begins_with("Disposal efficiency")
					and s.find_child("Sort_kh", true, false) == null,
					"The table's headings are words, not codes (%s)" % tag)
			# Each group's name spans its own columns, from the first to the last.
			var span: Control = s.find_child("PlayersGroup_Disposals", true, false)
			var first: Control = s.find_child("Sort_disposals", true, false)
			var last: Control = s.find_child("Sort_efficiency", true, false)
			_check(span != null and first != null and last != null
					and absf(span.global_position.x - first.global_position.x) <= 1.0
					and absf(span.get_global_rect().end.x - last.get_global_rect().end.x) <= 1.0,
					"A group's name and its rule span just its columns (%s)" % tag)
			_check(head != null and (await Tap.tap(head)) == "", "The disposals heading takes a tap (%s)" % tag)
			await _settle()
			cells = _column(s, "disposals")
			_check(_ascending(cells), "A second tap sorts fewest first (%s)" % tag)
		else:
			# His full name, never cut, with his club and games under it.
			var first_row: Node = s.find_children("PlayerRow_*", "Button", true, false)[0]
			var nm: Label = first_row.find_child("Name", true, false)
			_check(nm != null and nm.text == str(top["name"]) and nm.get_line_count() <= 2,
					"A row shows the player's full name (%s: %s)" % [tag, nm.text if nm else "-"])
			var meta := _text(first_row.find_child("Meta", true, false))
			_check(meta.contains(str(top["club"])) and meta.contains("game"), "...with his club and games under it (%s: %s)" % [tag, meta])
			_check(_text(first_row.find_child("Under", true, false)).ends_with("a game"),
					"...and the figure a game under his total (%s)" % tag)
		# Per game: one toggle, by finger.
		var pg: Button = s.find_child("StatMode_per_game", true, false)
		_check(pg != null and (await Tap.tap(pg)) == "", "Per game takes a tap (%s)" % tag)
		await _settle()
		var one: Node = s.find_child("Cell_disposals", true, false)
		_check(one != null and str(one.text).contains("."), "Per game shows a figure a game (%s: %s)" % [tag, one.text if one else "-"])
		pg = s.find_child("StatMode_per_game", true, false)
		var tot: Node = s.find_child("StatMode_total", true, false)
		_check(tot != null and pg != null and tot.get_parent() == pg.get_parent() and str(pg.get_parent().name) == "StatMode",
				"Totals and per game are one line of words (%s)" % tag)
		_check(tot != null and (await Tap.tap(tot)) == "", "Totals takes a tap back (%s)" % tag)
		await _settle()
		var back: Node = s.find_child("Cell_disposals", true, false)
		_check(back != null and not str(back.text).contains("."), "Totals shows whole numbers again (%s: %s)" % [tag, back.text if back else "-"])
		pg = s.find_child("StatMode_per_game", true, false)
		await Tap.tap(pg)
		await _settle()
		# A rate: only those with enough shots rank, and the list says so.
		SP.pick_stat("accuracy")
		s.call("refresh")
		await _settle()
		_check(s.find_child("PlayersQualify", true, false) != null, "A rate says who it ranks (%s)" % tag)
		_check(SP.qualify_noun("accuracy", 1) == "shot" and SP.qualify_noun("accuracy", 2) == "shots",
				"One shot is a shot, not 'shots' (%s)" % tag)
		if wide:
			_check(s.find_child("Sort_goals", true, false) != null, "The table shows the rate's group (%s)" % tag)
		var ranked: Array = SP.sorted_rows()
		var seen_unqualified := false
		var order_ok := true
		for r in ranked:
			var q: bool = SP.qualifies(r, "accuracy")
			if not q:
				seen_unqualified = true
			elif seen_unqualified:
				order_ok = false
		_check(order_ok, "Players without enough shots come after those ranked by accuracy (%s)" % tag)
		# Filters: a sheet, by finger; Done closes it.
		var fb: Button = s.find_child("FiltersToggle", true, false)
		_check(fb != null and (await Tap.tap(fb)) == "", "Filters takes a tap (%s)" % tag)
		await _settle()
		var fsheet: Node = s.find_child("FiltersSheet", true, false)
		_check(fsheet != null and fsheet.find_child("Filter_club", true, false) != null
				and fsheet.find_child("Filter_games", true, false) != null, "Filters open as a sheet (%s)" % tag)
		var done: Button = s.find_child("FiltersDone", true, false)
		_check(done != null and (await Tap.tap(done)) == "", "Done takes a tap (%s)" % tag)
		await _settle()
		_check(s.find_child("FiltersSheet", true, false) == null, "...and closes the sheet (%s)" % tag)
		# One club, then reset.
		SP.set_filter("club", "COL")
		s.call("refresh")
		await _settle()
		var clubs_ok := true
		for r in SP.rows():
			if str(r["club"]) != "COL":
				clubs_ok = false
		_check(clubs_ok and s.find_child("ActiveFilters", true, false) != null, "A club filter shows that club only, and says so (%s)" % tag)
		var reset: Button = s.find_child("FiltersReset", true, false)
		_check(reset != null and (await Tap.tap(reset)) == "", "Reset takes a tap (%s)" % tag)
		await _settle()
		_check(s.find_child("ActiveFilters", true, false) == null, "Reset clears the filters (%s)" % tag)
		# Every listed player includes those yet to play, shown as nothing.
		var played_count: int = (SP.rows() as Array).size()
		SP.set_filter("games", "0")
		var all_rows: Array = SP.rows()
		var zero := false
		for r in all_rows:
			if int(r["games"]) == 0:
				zero = true
				_check(SP.fmt(SP.value(r, "disposals", true), "disposals", true) == "–", "A player yet to play has no per-game figure (%s)" % tag)
				break
		_check(zero and all_rows.size() > played_count, "Every listed player includes those yet to play (%d of %d, %s)" % [all_rows.size(), played_count, tag])
		SP.reset_view()
		s.call("refresh")
		await _settle()
		# Nothing runs off the screen.
		var spill := ""
		for c in s.find_children("*", "Label", true, false):
			if c.is_visible_in_tree() and c.get_global_rect().end.x > sz.x + 1:
				spill = str(c.name)
				break
		_check(spill == "", "Players fit the screen (%s%s)" % [tag, (": " + spill) if spill != "" else ""])
		# Show more keeps the player's place (director bug report: a real tap on it
		# sent the list back to the top): the rows he was reading stay in view,
		# the next page comes in under them.
		var more: Button = s.find_child("PlayersMore", true, false)
		var sc0: ScrollContainer = s.find_child("StatsScroll", true, false)
		_check(more != null and sc0 != null, "The list has a Show more button under it (%s)" % tag)
		if more != null and sc0 != null:
			var shown_before := s.find_children("PlayerRow_*", "Button", true, false).size()
			sc0.ensure_control_visible(more)
			await _settle()
			var before := sc0.scroll_vertical
			_check(before > 0, "Show more sits below the fold (%s: %d)" % [tag, before])
			_check((await Tap.tap(more)) == "", "Show more takes a tap (%s)" % tag)
			for i in range(12):
				await process_frame
			var sc1: ScrollContainer = s.find_child("StatsScroll", true, false)
			var after := sc1.scroll_vertical if sc1 != null else -1
			var shown_after := s.find_children("PlayerRow_*", "Button", true, false).size()
			_check(shown_after > shown_before, "Show more adds rows (%s: %d -> %d)" % [tag, shown_before, shown_after])
			_check(after > 0 and absi(after - before) <= 2,
					"Show more keeps the list where it was, not back at the top (%s: %d -> %d)" % [tag, before, after])
			# The first new row is below the ones on show, not above the view.
			var rows_now := s.find_children("PlayerRow_*", "Button", true, false)
			if sc1 != null and rows_now.size() > shown_before:
				var first_new: Control = rows_now[shown_before]
				_check(first_new.get_global_rect().position.y >= sc1.get_global_rect().position.y,
						"The new rows come in under the ones on show (%s)" % tag)
			SP.reset_view()
			s.call("refresh")
			await _settle()
		# A player's season and career, then back.
		var first: Button = s.find_children("PlayerRow_*", "Button", true, false)[0]
		_check((await Tap.tap(first)) == "", "A player's row takes a tap (%s)" % tag)
		await _settle()
		var sheet: Node = s.find_child("PlayerStatsSheet", true, false)
		_check(sheet != null and sheet.find_child("PlayerSeasonGrid", true, false) != null
				and sheet.find_child("PlayerCareer", true, false) != null,
				"The tap opens his season and his career (%s)" % tag)
		_check(s.call("handle_back") == true, "Back closes his sheet (%s)" % tag)
		await _settle()
		_check(s.find_child("PlayerStatsSheet", true, false) == null and s.find_child(list_name, true, false) != null,
				"...and leaves the list as it was (%s)" % tag)
		s.queue_free()
		await _settle()


func _column(s: Node, key: String) -> Array:
	var out := []
	for row in s.find_children("PlayerRow_*", "Button", true, false):
		var c: Node = row.find_child("Cell_" + key, true, false)
		if c != null and str(c.text) != "–":
			out.append(float(str(c.text).trim_suffix("%")))
	return out


func _descending(a: Array) -> bool:
	for i in range(1, a.size()):
		if float(a[i]) > float(a[i - 1]):
			return false
	return true


func _ascending(a: Array) -> bool:
	for i in range(1, a.size()):
		if float(a[i]) < float(a[i - 1]):
			return false
	return true


## The season book adds up to the season's matches, matches the awards tally,
## and survives a save and load with every match's stat lines.
func _test_season_book() -> void:
	var book: Dictionary = _state.season_stats
	var tally: Dictionary = _state.season_tally
	_check(not book.is_empty() and book.size() == tally.size(),
			"Every player who played has a season row (%d, tally %d)" % [book.size(), tally.size()])
	var bad := ""
	for id in tally:
		var row: Dictionary = book.get(id, {})
		if int(row.get("games", -1)) != int(tally[id]["games"]) \
				or int(_SB.total(row, "goals")) != int(tally[id]["goals"]) \
				or int(_SB.total(row, "disposals")) != int(tally[id]["disposals"]):
			bad = "%s: book %s, tally %s" % [id, str(row.get("games", -1)), str(tally[id]["games"])]
			break
	_check(bad == "", "The book agrees with the awards tally on games, goals, disposals (%s)" % bad)
	# The book is the sum of the season's matches, key by key.
	var sums := {}
	for week in _state.season.results:
		for packed in week:
			# A reload leaves the matches packed (StatBook): unpack them.
			var res: Dictionary = _SB.full(packed)
			for id in res.get("players", {}):
				var st: Dictionary = res["players"][id]
				for k in ["contested_possessions", "ground_ball_gets", "shots", "running_bounces", "hitouts", "ruck_contests"]:
					var key: String = id + "|" + k
					sums[key] = float(sums.get(key, 0.0)) + float(st.get(k, 0.0))
	bad = ""
	for key in sums:
		var parts: PackedStringArray = str(key).split("|")
		if int(round(_SB.total(book.get(parts[0], {}), parts[1]))) != int(round(float(sums[key]))):
			bad = key
			break
	_check(bad == "" and not sums.is_empty(), "The season totals are the matches added up (%s)" % bad)
	# Save, start again, load: the book and the match boxes come back.
	var before := book.duplicate(true)
	var res0: Dictionary = _SB.full((_state.season.results[0] as Array)[0])
	var some_id := str(((res0["roster"] as Array)[0] as Array)[0]["id"])
	var line0: Dictionary = (res0["players"] as Dictionary).get(some_id, {}).duplicate()
	var saved: bool = _state.save_career()
	var size := 0
	var f := FileAccess.open(_state.save_path, FileAccess.READ)
	if f != null:
		size = f.get_length()
		f.close()
	print("Stats: save after %d rounds is %d KB" % [_state.season.round_index, size / 1024])
	_state.reset()
	var loaded: bool = _state.load_career()
	_check(saved and loaded, "The career saves and loads")
	bad = ""
	for id in before:
		var a_row: Dictionary = before[id]
		var b_row: Dictionary = _state.season_stats.get(id, {})
		if int(b_row.get("games", -1)) != int(a_row["games"]):
			bad = id
			break
		for k in a_row["s"]:
			if int(round(float(a_row["s"][k]))) != int(round(_SB.total(b_row, k))):
				bad = "%s %s" % [id, k]
				break
	_check(bad == "" and _state.season_stats.size() == before.size(), "The season book survives a save and load (%s)" % bad)
	var back: Dictionary = (_state.season.results[0] as Array)[0]
	_check(back.has("box") and not back.has("players"), "A saved match keeps its stat lines packed, not whole")
	var full: Dictionary = _SB.full(back)
	var line1: Dictionary = (full.get("players", {}) as Dictionary).get(some_id, {})
	bad = ""
	for k in _SB.KEYS:
		if int(round(float(line0.get(k, 0.0)))) != int(round(float(line1.get(k, 0.0)))):
			bad = k
	_check(bad == "" and (full["roster"] as Array).size() == 2 and (full["team"] as Array).size() == 2,
			"A match opened again after a reload has every player's line and both teams (%s)" % bad)


## A club's new statistics a game, over the games it has counted them.
func _test_club_per_game() -> void:
	var code := str(_state.my_club)
	var row: Dictionary = _state.season_team.get(code, {})
	var g := int(row.get("book_games", 0))
	_check(g > 0 and g == int(row.get("games", 0)), "A new season counts the clubs' new statistics every game (%d of %d)" % [g, int(row.get("games", 0))])
	var cp: float = _state.club_per_game(code, "contested_possessions")
	_check(cp > 0.0 and is_equal_approx(cp, float(row["contested_possessions"]) / float(g)),
			"A club's contested possessions a game is its total over its games (%.1f)" % cp)
	_check(_state.club_per_game("NOPE", "disposals") == -1.0, "A club with no games has no figure")
	# A book begun part way through (an older save, one round ago) ranks a player
	# who played the one game it saw.
	var played := int((_state.season.ladder.get(code, {}) as Dictionary).get("p", 0))
	var pid := str(_state.my_list[0]["id"])
	var had = _state.season_stats.get(pid)
	var from_was := int(_state.season_stats_from)
	_state.season_stats[pid] = {"club": code, "clubs": [code], "games": 1, "s": {}}
	_state.season_stats_from = played - 1
	var his := {}
	for r in load("res://scripts/ui/stats/StatsRatings.gd").rows():
		if str(r["id"]) == pid:
			his = r
	_state.season_stats_from = from_was
	if had == null:
		_state.season_stats.erase(pid)
	else:
		_state.season_stats[pid] = had
	_check(played >= 3 and bool(his.get("qualified", false)),
			"A part-season book ranks a player on the games it saw (%d played, %s)" % [played, str(his.get("qualified", "missing"))])


## Rates come from their counts; nothing under a rate is no rate, not zero.
func _test_book_rates() -> void:
	_check(_SB.rate({}, "accuracy") == -1.0 and _SB.rate({"goals": 3.0, "shots": 4.0}, "accuracy") == 0.75,
			"Accuracy is goals over shots, and no shots is no rate")
	_check(_SB.rate({"hitouts": 10.0, "ruck_contests": 25.0}, "hitout_win") == 0.4
			and _SB.rate({"hitouts": 0.0}, "hitout_win") == -1.0,
			"Hit-out win rate is hit-outs over ruck contests")
	_check(is_equal_approx(_SB.rate({"contested_possessions": 3.0, "uncontested_possessions": 9.0}, "cp_rate"), 0.25),
			"Contested possession rate is contested over all possessions")
	_check(_SB.kick_ratio({"kicks": 6.0}) == -1.0 and _SB.kick_ratio({"kicks": 6.0, "handballs": 4.0}) == 1.5,
			"Kicks to handballs, none without a handball")
	_check(_SB.per_game({"games": 0}, "goals") == -1.0 and _SB.per_game({"games": 4, "s": {"goals": 6.0}}, "goals") == 1.5,
			"Per game is over the games he played, and nothing with no games")
	# Season rates come from season counts, not an average of match rates:
	# 1 from 1 then 0 from 3 is 1 from 4 (25%), not the 50% an average says.
	var season := {}
	for st in [{"goals": 1.0, "shots": 1.0}, {"goals": 0.0, "shots": 3.0}]:
		for k in st:
			season[k] = float(season.get(k, 0.0)) + float(st[k])
	_check(_SB.rate(season, "accuracy") == 0.25, "A season's accuracy is its goals over its shots")
	# A career line from a season row, from now on; seasons before it keep
	# games and goals only.
	var p := {"id": "t1", "career": _CA.fresh()}
	_CA.add_season(p, 2030, "COL", 20, 15, {"games": 20, "s": {"goals": 15.0, "disposals": 400.0}}, 0)
	var lines: Array = p["career"].get("lines", [])
	_check(lines.size() == 1 and int(lines[0][2]) == 20
			and int((lines[0][3] as PackedInt32Array)[_SB.KEYS.find("disposals")]) == 400,
			"A finished season adds his statistics line to his career")
	_CA.add_season(p, 2030, "COL", 20, 15, {"games": 20, "s": {}}, 0)
	_check((p["career"]["lines"] as Array).size() == 1, "A season is never added twice")
	# Traded in the off-season (the only time a player changes clubs): next
	# season's line is his new club's, the old one keeps its own.
	_CA.add_season(p, 2031, "CAR", 18, 9, {"games": 18, "s": {"goals": 9.0, "disposals": 300.0}}, 0)
	var two: Array = p["career"]["lines"]
	_check(two.size() == 2 and str(two[0][1]) == "COL" and str(two[1][1]) == "CAR"
			and int((two[1][3] as PackedInt32Array)[_SB.KEYS.find("disposals")]) == 300,
			"A player traded between seasons keeps each season with the club he played it for")

## Season stats > Fixture, by finger: it opens on the round to play, Previous,
## Next and the picker move about, a played match opens its box score and an
## upcoming one a preview, Back closes the sheet first, and nothing runs off
## the screen. A result with only what a save keeps says what was not kept.
func _test_fixture(sz: Vector2i) -> void:
	var tag := "%dx%d" % [sz.x, sz.y]
	var db = root.get_node("GameDB")
	var season = _state.season
	var fix = load("res://scripts/ui/stats/StatsFixture.gd")
	var bold_font = load("res://scripts/ui/UiKit.gd").BOLD
	fix.reset()
	root.size = sz
	load("res://scripts/ui/StatsHubScene.gd").current = "fixture"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	var next_round := "Round %d" % (season.round_index + 1)
	var picker: Button = s.find_child("RoundPicker", true, false)
	_check(picker != null and picker.text == next_round, "The fixture opens on the round to play (%s: %s)" % [tag, picker.text if picker else "-"])
	var rows: Array = s.find_children("Match_*", "Button", true, false)
	_check(rows.size() == (season.fixture[season.round_index] as Array).size() and not rows.is_empty(),
			"Every match of the round is a row (%s)" % tag)
	var upcoming := true
	for r in rows:
		upcoming = upcoming and not bool(r.get_meta("done")) and not _text(r).contains("(") 				and not _text(r).contains("Upcoming")
	_check(upcoming, "A round all to come shows the ground, not a score and not Upcoming on every row (%s)" % tag)
	var grounds := true
	for i in range(rows.size()):
		var m: Dictionary = season.fixture[season.round_index][i]
		grounds = grounds and _text(rows[i]).contains(season.round_venue(season.round_index, str(m["home"]), str(m["away"])))
	_check(grounds, "Each match shows its ground (%s)" % tag)
	if sz.x >= 900:
		var widest := 0.0
		for r in rows:
			widest = maxf(widest, r.size.x)
		_check(widest <= 430.0, "On a wide screen a match row is compact, not a bar across the window (%s: %d)" % [tag, int(widest)])
		var nav_w: float = s.find_child("NextRound", true, false).get_global_rect().end.x - s.find_child("PrevRound", true, false).get_global_rect().position.x
		_check(nav_w <= 560.0, "Previous, round and Next are a compact group (%s: %d)" % [tag, int(nav_w)])
	var byes: Node = s.find_child("ByeLine", true, false)
	_check(byes == null or _text(byes).begins_with("Bye: "), "A round with byes names the clubs (%s)" % tag)
	_fits(s, sz, "the next round", tag)

	# Your club's match is set in bold, the others' are not.
	var mine_name: String = str(_state.my_club) if sz.x < 900 else str(db.club_short(str(_state.my_club)))
	var bold_mine := false
	var bold_other := false
	for r in rows:
		var yours: bool = _text(r).contains(mine_name)
		for l in r.find_children("*", "Label", true, false):
			var is_bold: bool = l.get_theme_font("font") == bold_font
			if yours:
				bold_mine = bold_mine or is_bold
			elif is_bold:
				bold_other = true
	_check(bold_mine and not bold_other, "Your club's match stands out by weight (%s)" % tag)

	# Previous, by finger: the round before, played, with both scores.
	var why: String = await Tap.tap(s.find_child("PrevRound", true, false))
	await _settle()
	_check(why == "", "A finger takes Previous (%s: %s)" % [tag, why])
	picker = s.find_child("RoundPicker", true, false)
	_check(picker.text == "Round %d" % season.round_index, "Previous goes to the round before (%s)" % tag)
	rows = s.find_children("Match_*", "Button", true, false)
	var played := not rows.is_empty()
	for r in rows:
		played = played and bool(r.get_meta("done")) and not _text(r).contains("Upcoming") and _text(r).contains("(") 				and _text(r).contains(season.home_ground(str(season.fixture[season.round_index - 1][r.get_index()]["home"])))
	_check(played, "Played matches show both scorelines (%s)" % tag)
	_fits(s, sz, "a played round", tag)

	# A played match opens its box score; Back closes it, and the next Back is the screen's.
	var why2: String = await Tap.tap(rows[0])
	await _settle()
	var sheet: Node = s.find_child("FixtureSheet", true, false)
	_check(why2 == "" and sheet != null and sheet.find_child("MatchBox", true, false) != null,
			"A finger on a played match opens it (%s: %s)" % [tag, why2])
	if sheet != null:
		var q: Node = sheet.find_child("QuarterStrip", true, false)
		var res: Dictionary = season.results[season.round_index - 1][0]
		_check(q != null and _text(q).contains("%d.%d" % [int(res["q_goals"][0][0]), int(res["q_behinds"][0][0])]),
				"The box score has the quarters (%s)" % tag)
		_check(not sheet.find_children("BoxPlayer_*", "Button", true, false).is_empty()
				and sheet.find_child("HeadToHead", true, false) != null and sheet.find_child("NotKept", true, false) == null,
				"A match with its players kept shows them, and the team numbers head to head (%s)" % tag)
		var box = sheet.find_child("BoxScore", true, false)
		_check(box != null and not (box.get("_scores") as Array).is_empty(),
				"The worm has the match's goals and behinds (%s)" % tag)
		_fits(sheet, sz, "the box score", tag)
	var backed: bool = s.call("handle_back")
	await _settle()
	_check(backed and s.find_child("FixtureSheet", true, false) == null, "Back closes the sheet first (%s)" % tag)
	_check(s.call("handle_back") == false, "...and the next Back is the screen's own (%s)" % tag)

	# What a save keeps is the score by quarter, nothing more: say so.
	var at: int = season.round_index - 1
	var kept: Array = season.results[at]
	season.results[at] = load("res://scripts/state/CareerSave.gd").slim_results(kept)
	s.call("refresh")
	await _settle()
	rows = s.find_children("Match_*", "Button", true, false)
	var why3: String = await Tap.tap(rows[0])
	await _settle()
	var slim_box = s.find_child("BoxScore", true, false)
	_check(why3 == "" and s.find_child("NotKept", true, false) != null and s.find_child("QuarterStrip", true, false) != null
			and slim_box != null and not (slim_box.get("_scores") as Array).is_empty(),
			"A match kept only as a score still shows its quarters and worm, and says the rest was not kept (%s)" % tag)
	var close: Button = s.find_child("CloseSheet", true, false)
	await Tap.tap(close)
	await _settle()
	season.results[at] = kept
	_check(s.find_child("FixtureSheet", true, false) == null, "Close closes the sheet (%s)" % tag)

	# Next, back to the round to play; an upcoming match opens its preview.
	await Tap.tap(s.find_child("NextRound", true, false))
	await _settle()
	picker = s.find_child("RoundPicker", true, false)
	_check(picker.text == next_round, "Next goes to the round to play (%s)" % tag)
	rows = s.find_children("Match_*", "Button", true, false)
	var why4: String = await Tap.tap(rows[0])
	await _settle()
	sheet = s.find_child("FixtureSheet", true, false)
	var pv: Node = sheet.find_child("PreviewBox", true, false) if sheet != null else null
	_check(why4 == "" and pv != null, "A finger on an upcoming match opens its preview (%s: %s)" % [tag, why4])
	if pv != null:
		var pt := _text(pv)
		var f0: Dictionary = season.fixture[season.round_index][0]
		_check(pt.contains(db.club_short(str(f0["home"]))) and pt.contains(db.club_short(str(f0["away"]))),
				"The preview names both clubs (%s)" % tag)
		_check(pt.contains(season.round_venue(season.round_index, str(f0["home"]), str(f0["away"]))), "...and the ground (%s)" % tag)
		_check(pt.contains("st ·") or pt.contains("nd ·") or pt.contains("rd ·") or pt.contains("th ·"),
				"...and where each sits on the ladder (%s)" % tag)
		_check(pt.contains("Round %d:" % season.round_index) and (pt.contains("won by") or pt.contains("lost by") or pt.contains("drew")),
				"...and how each has gone lately (%s)" % tag)
		_fits(sheet, sz, "the preview", tag)
	s.call("handle_back")
	await _settle()

	# The round picker: a finger on a round takes you there.
	var why5: String = await Tap.tap(s.find_child("RoundPicker", true, false))
	await _settle()
	sheet = s.find_child("FixtureSheet", true, false)
	_check(why5 == "" and sheet != null and sheet.find_children("RoundPick_*", "Button", true, false).size() == _rounds(),
			"The picker offers every round (%s)" % tag)
	_fits(sheet, sz, "the picker", tag)
	var why6: String = await Tap.tap(s.find_child("RoundPick_0", true, false))
	await _settle()
	_check(why6 == "" and s.find_child("FixtureSheet", true, false) == null and s.find_child("RoundPicker", true, false).text == "Round 1",
			"A finger on round 1 goes there and closes the picker (%s: %s)" % [tag, why6])
# ---------------------------------------------------------------------------
# Awards
# ---------------------------------------------------------------------------
func _open_awards(sz: Vector2i) -> Control:
	root.size = sz
	load("res://scripts/ui/StatsHubScene.gd").current = "awards"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	return s


# ---------------------------------------------------------------------------
# Trophies (on the club's page since 2026-11-06, rulings 118 and 118a)
# ---------------------------------------------------------------------------
## Your club's trophies, opened over Season stats as its club page opens them.
func _open_trophies(sz: Vector2i) -> Control:
	root.size = sz
	load("res://scripts/ui/StatsHubScene.gd").current = "ladder"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	load("res://scripts/ui/ClubPage.gd").open_trophies(s, _state.my_club)
	await _settle()
	return s


## The hub's ladder (UiKit.ladder_table): "Pts" ends where its figures end,
## and "Club" starts over the names, past the crests (critic 2026-11-04: Pts
## 5 px off, Club over the crests; StatsLadder's fix in #950).
func _test_hub_ladder_heads(width: float) -> void:
	var tag := "%.0f wide" % width
	var UK = load("res://scripts/ui/UiKit.gd")
	var holder := Control.new()
	holder.size = Vector2(width, 800)
	root.add_child(holder)
	var t: VBoxContainer = UK.ladder_table(_state.season.ladder_sorted(), _state.my_club, width)
	t.size = Vector2(width, 0)
	holder.add_child(t)
	await _settle()
	var head: HBoxContainer = t.get_child(0)
	var specs: Array = UK.ladder_specs(width, false)
	var pts_i := -1
	var club_i := -1
	for i in specs.size():
		if str(specs[i]["key"]) == "pts":
			pts_i = i
		if str(specs[i]["key"]) == "club":
			club_i = i
	# The header puts a spacer before Club (the crest's room), so its labels
	# from Club on sit one child later than the rows' cells.
	var club_head: Label = head.get_child(club_i + 1)
	var inset: float = club_head.get_theme_stylebox("normal").get_margin(SIDE_LEFT)
	var head_end := _ink_end(head.get_child(pts_i + 1))
	var worst := 0.0
	var crest_off := 0.0
	for i in range(1, t.get_child_count()):
		var row := t.get_child(i)
		if not row is HBoxContainer:
			continue
		worst = maxf(worst, absf(_ink_end(row.get_child(pts_i)) - head_end))
		var names: Array = (row.get_child(club_i) as Node).find_children("*", "Label", true, false)
		crest_off = maxf(crest_off, absf(club_head.get_global_rect().position.x + inset
				- (names[0] as Control).get_global_rect().position.x))
	_check(worst <= 1.0, "The hub ladder's Pts ends where its figures end (%s: %.1f px off)" % [tag, worst])
	_check(crest_off <= 1.0, "The hub ladder's Club starts over the names, not the crests (%s: %.1f px off)" % [tag, crest_off])
	holder.queue_free()
	await _settle()


## Where a one-line label's text ends on screen, by its alignment.
func _ink_end(l: Label) -> float:
	var w: float = l.get_theme_font("font").get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1,
			l.get_theme_font_size("font_size")).x
	var r := l.get_global_rect()
	if l.horizontal_alignment == HORIZONTAL_ALIGNMENT_RIGHT:
		return r.end.x
	if l.horizontal_alignment == HORIZONTAL_ALIGNMENT_CENTER:
		return r.position.x + (r.size.x + w) * 0.5
	return r.position.x + w


func _close(s: Control) -> void:
	s.queue_free()
	await _settle()


## Season stats > Ladder, by finger: the true order to start, a header sorts and
## sorts back, "Ladder order" and Reset restore it, the filters narrow it, the
## team view is per game from season_team, and a club opens its side on the field
## view with Back returning to the table as it was.
func _test_ladder(sz: Vector2i) -> void:
	var tag := "%dx%d" % [sz.x, sz.y]
	var db = root.get_node("GameDB")
	var season = _state.season
	var ladder = load("res://scripts/ui/stats/StatsLadder.gd")
	var bold_font = load("res://scripts/ui/UiKit.gd").BOLD
	ladder.reset()
	root.size = sz
	load("res://scripts/ui/StatsHubScene.gd").current = "ladder"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	var true_order := []
	for r in season.ladder_sorted():
		true_order.append(str(r["code"]))
	var mine := str(_state.my_club)
	_check(_row_codes(s) == true_order, "The ladder opens in the true order (%s)" % tag)
	_fits(s, sz, "the ladder", tag)
	_table_recipe(s, tag, true)
	_header_aligns(s, tag)

	# Phone columns, and the wide screen's extra ones.
	var heads := []
	for b in s.find_child("LadderHeader", true, false).get_children():
		heads.append(str(b.name))
	var phone: Array = ["Sort_pos", "Sort_club", "Sort_p", "Sort_w", "Sort_l", "Sort_d", "Sort_pct", "Sort_pts", "Sort_rating"]
	if sz.x < 900:
		_check(heads == phone, "Phone columns are # Club P W L D %% Pts Rating (%s: %s)" % [tag, str(heads)])
	else:
		_check(heads.slice(0, 8).size() == 8 and heads.has("Sort_pf") and heads.has("Sort_home") and heads.has("Sort_away"),
				"A wide screen adds points for and against, home and away (%s: %s)" % [tag, str(heads)])
		var row_text := _text(s.find_child("Club_" + mine, true, false))
		_check(season.club_results(mine).size() == 0 or row_text.contains("".join(PackedStringArray((season.club_results(mine) as Array).slice(-5)))),
				"...and the last five results as letters (%s)" % tag)

	# The sort headers are thumb high on a phone (44 px; the sweep, 2026-10-18:
	# they were 40) with the columns no wider than before, and unchanged on a PC.
	var short_heads := []
	var header_w := 0.0
	for b in s.find_child("LadderHeader", true, false).get_children():
		if not b is Button:
			continue
		if (b as Control).size.y < (44.0 if sz.x < 900 else 40.0):
			short_heads.append("%s %.0f" % [b.name, (b as Control).size.y])
		header_w += (b as Control).size.x
	_check(short_heads.is_empty(), "Ladder sort headers are %s px tall (%s: short %s)" % ["at least 44" if sz.x < 900 else "40", tag, str(short_heads)])
	var short_rows := []
	for b in s.find_children("Club_*", "Button", true, false):
		if (b as Control).size.y < (44.0 if sz.x < 900 else 32.0):
			short_rows.append("%s %.0f" % [b.name, (b as Control).size.y])
	_check(short_rows.is_empty() and not _row_codes(s).is_empty(), "Ladder rows are %s px tall (%s: short %s)" % ["at least 44" if sz.x < 900 else "at least 32", tag, str(short_rows.slice(0, 3))])
	if sz.x < 900:
		_check(header_w <= sz.x, "...and the header row still fits the screen (%s: %.0f px)" % [tag, header_w])
		# A finger on the narrowest header, the "#" column, takes the tap and
		# puts the ladder back in its true order.
		var pos_why: String = await Tap.tap(s.find_child("Sort_pos", true, false))
		_check(pos_why == "", "A finger on the # header (24 px wide, 44 tall) reaches it (%s: %s)" % [tag, pos_why])
	else:
		# On a PC the "#" header, the way back to the true order, is at least thumb-wide too.
		var pos_btn: Control = s.find_child("Sort_pos", true, false)
		_check(pos_btn != null and pos_btn.size.x >= 44.0, "The # sort header is at least 44 px wide (%s: %.0f)" % [tag, pos_btn.size.x if pos_btn != null else 0.0])
		var pos_pc: String = await Tap.tap(pos_btn)
		_check(pos_pc == "", "A real tap on the # header reaches it (%s: %s)" % [tag, pos_pc])

	# Every header and cell is whole, and nothing in a row runs into its neighbour.
	_table_text_whole(s, "ladder", tag)
	# A wide screen: the toggles are compact groups rather than bars across the
	# window, each with its words whole (row 149: the 100 to 140 px band is retired).
	if sz.x >= 900:
		for n in ["Filter_all", "Filter_top10", "Filter_near"]:
			var tb: Button = s.find_child(n, true, false)
			_check(tb != null and _button_text_fits(tb) and tb.size.x < sz.x * 0.5,
					"%s shows its words whole and is not a bar across the window (%s: %.0f px)" % [n, tag, tb.size.x if tb != null else -1.0])

	# Your club is set in bold, another is not.
	var other: String = true_order[0] if true_order[0] != mine else true_order[1]
	var mine_name := mine if sz.x < 900 else str(db.club_short(mine))
	var other_name := other if sz.x < 900 else str(db.club_short(other))
	_check(_label_bold(s.find_child("Club_" + mine, true, false), mine_name, bold_font)
			and not _label_bold(s.find_child("Club_" + other, true, false), other_name, bold_font),
			"Your club is in bold, another is not (%s)" % tag)

	# Sort by wins, by finger; again to reverse; Ladder order to restore.
	var why: String = await Tap.tap(s.find_child("Sort_w", true, false))
	await _settle()
	_check(why == "", "A finger on W sorts (%s: %s)" % [tag, why])
	var wins := _by(s, season, "w")
	_check(_non_increasing(wins), "W sorts most first (%s: %s)" % [tag, str(wins)])
	_check(_text(s.find_child("ActiveState", true, false)).contains("sorted by W, most first"), "The sort is named (%s)" % tag)
	await Tap.tap(s.find_child("Sort_w", true, false))
	await _settle()
	wins = _by(s, season, "w")
	_check(_non_decreasing(wins), "A second tap reverses it (%s: %s)" % [tag, str(wins)])
	_header_aligns(s, tag + " sorted")
	await Tap.tap(s.find_child("LadderOrder", true, false))
	await _settle()
	_check(_row_codes(s) == true_order and s.find_child("LadderOrder", true, false) == null,
			"Ladder order restores the true order (%s)" % tag)
	await Tap.tap(s.find_child("Sort_club", true, false))
	await _settle()
	var names := []
	for c in _row_codes(s):
		names.append(str(db.club_short(c)))
	var az := names.duplicate()
	az.sort()
	_check(names == az, "The club column sorts A to Z first (%s)" % tag)
	_check(_text(s.find_child("ActiveState", true, false)).contains("Club, A–Z first"), "The club sort reads A–Z, not fewest first (%s)" % tag)

	# Filters, by finger: Top 10, Near you, and Reset.
	await Tap.tap(s.find_child("Filter_top10", true, false))
	await _settle()
	var top8 := _row_codes(s)
	var expect8 := []
	for c in true_order.slice(0, load("res://scripts/sim/Season.gd").FINALISTS):
		expect8.append(c)
	top8.sort()
	expect8.sort()
	_check(top8 == expect8, "Top 10 shows every finals club (%s)" % tag)
	_check(_text(s.find_child("ActiveState", true, false)).contains("Top %d" % load("res://scripts/sim/Season.gd").FINALISTS), "The active filter is shown (%s)" % tag)
	await Tap.tap(s.find_child("Filter_near", true, false))
	await _settle()
	var near := _row_codes(s)
	var at := true_order.find(mine)
	var expect_near := []
	for i in range(maxi(0, at - 2), mini(true_order.size(), at + 3)):
		expect_near.append(true_order[i])
	near.sort()
	expect_near.sort()
	_check(near == expect_near and near.has(mine), "Near you is two places either side of your club (%s)" % tag)
	await Tap.tap(s.find_child("ResetLadder", true, false))
	await _settle()
	_check(_row_codes(s) == true_order and s.find_child("ResetLadder", true, false) == null,
			"Reset puts back every club in ladder order (%s)" % tag)

	# Team stats: a leaderboard, one fact at a time, a game.
	await Tap.tap(s.find_child("View_team", true, false))
	await _settle()
	var t: Dictionary = _state.season_team.get(mine, {})
	var games := int(t.get("games", 0))
	_check(games > 0, "(setup) your club has games to average (%s)" % tag)
	_check(s.find_child("TeamBoard", true, false) != null and s.find_child("TeamStat", true, false) != null
			and s.find_child("Filter_top10", true, false) == null,
			"Team stats is a leaderboard with its own picker (%s)" % tag)
	var mine_row: Node = s.find_child("Club_" + mine, true, false)
	var club_nm: Label = mine_row.find_child("Name", true, false) if mine_row else null
	_check(club_nm != null and club_nm.text == str(db.club_name(mine)), "Each club by its name (%s: %s)" % [tag, club_nm.text if club_nm else "-"])
	var want_pf: String = ladder.team_text(float(t["for"]) / float(games), "for")
	_check(_text(mine_row.find_child("Figure", true, false)) == want_pf,
			"Points for is a game over games played, whole: %s (%s)" % [want_pf, tag])
	var others := _text(mine_row.find_child("Others", true, false))
	_check(others.contains("inside 50s") and others.contains("goals"),
			"...with the view's other two facts beside it (%s: %s)" % [tag, others])
	var figs := []
	for c in _row_codes(s):
		figs.append(float(_text(s.find_child("Club_" + c, true, false).find_child("Figure", true, false))))
	_check(_non_increasing(figs), "Ranked on points for, most first (%s)" % tag)
	var first_bar: Node = s.find_child("Club_" + str(_row_codes(s)[0]), true, false).find_child("Bar", true, false)
	_check(first_bar != null and is_equal_approx(float(first_bar.get_meta("share")), 1.0),
			"The league's best fills the bar (%s)" % tag)
	var whole_rx := RegEx.new()
	whole_rx.compile("^[0-9]+$")
	_check(whole_rx.search(want_pf) != null, "No decimals where a whole number says it (%s: %s)" % [tag, want_pf])
	ladder.pick_team_fact("against")
	s.call("refresh")
	await _settle()
	figs = []
	for c in _row_codes(s):
		figs.append(float(_text(s.find_child("Club_" + c, true, false).find_child("Figure", true, false))))
	_check(_non_decreasing(figs), "Points against ranks the fewest first (%s)" % tag)
	ladder.pick_team_fact("goals")
	s.call("refresh")
	await _settle()
	var tenth_rx := RegEx.new()
	tenth_rx.compile("^[0-9]+[.][0-9]$")
	_check(tenth_rx.search(_text(s.find_child("Club_" + mine, true, false).find_child("Figure", true, false))) != null,
			"Goals a game keep their tenth (%s)" % tag)
	_fits(s, sz, "team stats", tag)
	# No word or figure is cut short, runs out of its row or into its neighbour,
	# and no figure is drawn over its bar (row 149, director 2026-11-10: the
	# 3 to 8 px band between them is retired).
	_table_text_whole(s, "team stats", tag)
	var on_bar := []
	for c in _row_codes(s):
		var row: Node = s.find_child("Club_" + c, true, false)
		var bar: Control = row.find_child("Bar", true, false)
		var fig: Label = row.find_child("Figure", true, false)
		if _ink_rect(fig).position.x < bar.get_global_rect().end.x - 0.5:
			on_bar.append("%s %s" % [c, fig.text])
	_check(on_bar.is_empty() and not _row_codes(s).is_empty(),
			"Every team stats figure is clear of its bar (%s: %s)" % [tag, str(on_bar.slice(0, 4))])
	ladder.pick_team_fact("for")
	await Tap.tap(s.find_child("View_ladder", true, false))
	await _settle()

	# A club opens its side, read-only; Back returns to the table as it was.
	await Tap.tap(s.find_child("Sort_pts", true, false))
	await _settle()
	await Tap.tap(s.find_child("Filter_top10", true, false))
	await _settle()
	var before := _row_codes(s)
	var tapped: String = before[1] if before[0] == mine else before[0]
	var why2: String = await Tap.tap(s.find_child("Club_" + tapped, true, false))
	await _settle()
	# A club's name opens its page (rulings no. 113); the page leads to the side.
	var page: Node = s.find_child("ClubPage", true, false)
	_check(why2 == "" and page != null and str(page.get_meta("club_code", "")) == tapped,
			"A finger on a club opens its page (%s: %s)" % [tag, why2])
	var why3: String = await Tap.tap(page.find_child("SideOnGround", true, false)) if page != null else "no page"
	await _settle()
	var side: Node = s.find_child("ClubSide", true, false)
	_check(why3 == "" and side != null and side.find_child("TeamBuilder", true, false) != null,
			"The page's button opens the side on the ground (%s: %s)" % [tag, why3])
	if side != null:
		var builder: Node = side.find_child("TeamBuilder", true, false)
		_check(bool(builder.get("_read_only")), "The side is read-only (%s)" % tag)
		var named: bool = not (season.selections.get(tapped, {}) as Dictionary).is_empty()
		var note := _text(side.find_child("SideNote", true, false)).strip_edges()
		_check(note == ("Side named for this round" if named else "Projected side: picked on match day"),
				"The side says whether it is projected (%s: %s)" % [tag, note])
		_fits(side, sz, "a club's side", tag)
		var gap: Array = pitch_gap(builder)
		print("PITCHGAP side %s %.1f %s" % [tag, float(gap[0]), str(gap[1])])
		var off_ground: Array = pitch_off_ground(builder)
		print("PITCHOFF side %s %s" % [tag, str(off_ground)])
		print("PITCHSKEW side %s %s" % [tag, str(pitch_skew(builder))])
		# 320 units: too narrow for three cards abreast inside the line.
		_check(sz.x < 390 or off_ground.is_empty(), "Every card on the side's oval sits inside the boundary line (%s: %s)" % [tag, str(off_ground)])
		_check(float(gap[0]) >= 8.0, "No two names on the side's oval come within 8 px (%s: %.1f px, %s)" % [tag, float(gap[0]), str(gap[1])])
		# Every list card holds its own rating and its whole third line (critic
		# 2026-11-04: on a PC the right column hid the left one's ratings and
		# "Playmak…" was cut).
		var spill := []
		var cut := []
		for card in builder.find_child("NotSelected", true, false).get_children():
			if not card is Button:
				continue
			var box: Rect2 = (card as Control).get_global_rect().grow(0.5)
			for l in card.find_children("*", "Label", true, false):
				if not box.encloses((l as Control).get_global_rect()):
					spill.append("%s %s" % [card.name, (l as Label).text])
			if sz.x >= 900:
				var top_y := (card as Control).get_global_rect().position.y
				var name_y: float = (card.find_children("*", "Label", true, false)[0] as Control).get_global_rect().position.y
				if absf(name_y - top_y - 8.0) > 1.0:
					cut.append("%s name %.0f px in" % [card.name, name_y - top_y])
			var third: Label = card.find_child("Third", true, false)
			if third != null and sz.x >= 900 and third.text_overrun_behavior != TextServer.OVERRUN_NO_TRIMMING:
				cut.append(str(card.name))
		_check(spill.is_empty(), "Every list card holds its own words and rating (%s: %s)" % [tag, str(spill.slice(0, 3))])
		_check(cut.is_empty(), "A PC card's third line wraps, never cut, and its name sits 8 px in (%s: %s)" % [tag, str(cut.slice(0, 3))])
		# A player opens his profile over the side; Back closes it first.
		var list: Array = _state.opponent_side(tapped)["list"]
		builder.emit_signal("inspect", str(list[0]["id"]))
		await _settle()
		_check(s.find_child("PlayerProfile", true, false) != null and s.find_child("ClubSide", true, false) != null,
				"A player opens over the side (%s)" % tag)
		_check(s.call("handle_back") == true, "Back closes the profile (%s)" % tag)
		await _settle()
		_check(s.find_child("PlayerProfile", true, false) == null and s.find_child("ClubSide", true, false) != null,
				"...and leaves the side (%s)" % tag)
	_check(s.call("handle_back") == true, "Back closes the side (%s)" % tag)
	await _settle()
	_check(s.find_child("ClubSide", true, false) == null and s.find_child("ClubPage", true, false) != null,
			"...and leaves the club's page (%s)" % tag)
	_check(s.call("handle_back") == true, "Back closes the club's page (%s)" % tag)
	await _settle()
	_check(s.find_child("ClubPage", true, false) == null and _row_codes(s) == before
			and _text(s.find_child("ActiveState", true, false)).contains("sorted by Pts"),
			"Back returns to the ladder as it was, sort and filter kept (%s)" % tag)
	s.queue_free()
	await _settle()


## Each header sits over its own column (row 84: on a phone the header was one
## column off): every header's right edge (the club's left edge) is within 2 px
## of the same column's cell in every row.
func _header_aligns(s: Node, tag: String) -> void:
	var header: Control = s.find_child("LadderHeader", true, false)
	_check(header != null, "The ladder has a header row (%s)" % tag)
	if header == null:
		return
	var heads: Array = header.get_children()
	var off := []
	for b in s.find_children("Club_*", "Button", true, false):
		var cells: Array = (b as Control).get_child(0).get_children()
		if cells.size() != heads.size():
			off.append("%s has %d cells for %d headers" % [b.name, cells.size(), heads.size()])
			continue
		for i in heads.size():
			var h: Control = heads[i]
			var c: Control = cells[i]
			var club := str(h.name) == "Sort_club"
			var hx: float = h.get_global_rect().position.x if club else h.get_global_rect().end.x
			var cx: float = c.get_global_rect().position.x if club else c.get_global_rect().end.x
			if absf(hx - cx) > 2.0:
				off.append("%s %s %.0f vs %.0f" % [b.name, h.name, hx, cx])
	var body: Control = s.find_child("Club_*", true, false)
	if body != null:
		var rw: float = (body as Control).get_child(0).size.x
		_check(absf(rw - header.size.x) <= 2.0, "A ladder row is as wide as its header (%s: %.0f vs %.0f)" % [tag, rw, header.size.x])
	_check(off.is_empty(), "Ladder headers line up with their columns (%s: %s)" % [tag, str(off.slice(0, 4))])


## The table's words are whole and apart (row 149, director 2026-11-10: the
## 700 to 900 px table and 170 to 200 px club column bands are retired, a
## layout may move): no header or cell is cut short or runs out of its row, and
## no two pieces of text in a row run into each other.
func _table_text_whole(s: Node, what: String, tag: String) -> void:
	var table: Control = s.find_child("LadderTable", true, false)
	var rows: Array = s.find_children("Club_*", "Button", true, false)
	_check(table != null and not rows.is_empty(), "The %s table has rows to read (%s)" % [what, tag])
	if table == null:
		return
	var cut: Array = _cut_text(table)
	var header: Node = s.find_child("LadderHeader", true, false)
	if header != null:
		cut.append_array(_cut_text(header))
		for h in header.get_children():
			if h is Button and (h as Button).is_visible_in_tree() and not _button_text_fits(h as Button):
				cut.append("%s \"%s\"" % [h.name, (h as Button).text])
	_check(cut.is_empty(), "No %s header or cell is clipped (%s: %s)" % [what, tag, str(cut.slice(0, 4))])
	var over := []
	for b in rows:
		over.append_array(_overlapping(b))
	_check(over.is_empty(), "No two pieces of text in a %s row overlap (%s: %s)" % [what, tag, str(over.slice(0, 4))])


## Every one-line label under `root_node` whose words do not all show: trimmed
## to an ellipsis or set in a box narrower than its words, or whole in its own
## box but drawn outside a row or a clipping parent (a row of fixed columns
## that outgrows its button is cut at the button's edge).
func _cut_text(root_node: Node) -> Array:
	var out := []
	for n in root_node.find_children("*", "Label", true, false):
		var l := n as Label
		if not l.is_visible_in_tree() or l.text == "" or l.autowrap_mode != TextServer.AUTOWRAP_OFF:
			continue   # wrapped text takes another line instead
		if _text_width(l) > l.size.x + 1.0:
			out.append("%s \"%s\" is cut to %.0f px" % [l.name, l.text.left(24), l.size.x])
			continue
		var ink := _ink_rect(l)
		var p: Node = l.get_parent()
		while p != null and p != root_node.get_parent():
			if p is Control and ((p as Control).clip_contents or str(p.name).begins_with("Club_")):
				var box := (p as Control).get_global_rect()
				if ink.position.x < box.position.x - 1.0 or ink.end.x > box.end.x + 1.0:
					out.append("%s \"%s\" runs out of %s" % [l.name, l.text.left(24), p.name])
					break
			p = p.get_parent()
	return out


## Pairs of labels in a row whose words are drawn over each other.
func _overlapping(row: Node) -> Array:
	var out := []
	var inks := []
	for n in row.find_children("*", "Label", true, false):
		var l := n as Label
		if l.is_visible_in_tree() and l.text != "":
			inks.append([_ink_rect(l), l.text])
	for i in inks.size():
		for j in range(i + 1, inks.size()):
			if (inks[i][0] as Rect2).grow(-0.5).intersects((inks[j][0] as Rect2).grow(-0.5)):
				out.append("%s: \"%s\" on \"%s\"" % [row.name, inks[i][1], inks[j][1]])
	return out


func _text_width(l: Label) -> float:
	return l.get_theme_font("font").get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1,
			l.get_theme_font_size("font_size")).x


## Whether a button's words fit between its margins.
func _button_text_fits(b: Button) -> bool:
	var sb := b.get_theme_stylebox("normal")
	var pad: float = sb.get_margin(SIDE_LEFT) + sb.get_margin(SIDE_RIGHT) if sb != null else 0.0
	var w: float = b.get_theme_font("font").get_string_size(b.text, HORIZONTAL_ALIGNMENT_LEFT, -1,
			b.get_theme_font_size("font_size")).x
	return w + pad <= b.size.x + 1.0


## Where a label's words are drawn: its own box when it wraps or is trimmed to
## fit, otherwise the full width of its words from its aligned edge (which can
## be wider than the box it was given).
func _ink_rect(l: Label) -> Rect2:
	var box := l.get_global_rect()
	if l.autowrap_mode != TextServer.AUTOWRAP_OFF or l.text_overrun_behavior != TextServer.OVERRUN_NO_TRIMMING \
			or l.clip_text:
		return box
	var w := _text_width(l)
	var x := box.position.x
	if l.horizontal_alignment == HORIZONTAL_ALIGNMENT_RIGHT:
		x = box.end.x - w
	elif l.horizontal_alignment == HORIZONTAL_ALIGNMENT_CENTER:
		x = box.position.x + (box.size.x - w) / 2.0
	return Rect2(x, box.position.y, w, box.size.y)


## The clipped-text checks fail on the ways a table cell is really cut (review
## of row 149): a row that outgrows its clipping button, a club name trimmed to
## an ellipsis, and words drawn over each other. A whole row passes.
func _test_whole_text_checks_bite() -> void:
	var holder := Control.new()
	holder.name = "BiteTable"
	root.add_child(holder)
	holder.position = Vector2(10, 10)
	holder.size = Vector2(360, 200)
	# A row of two one-line cells in a button narrower than the cells.
	var tight := Button.new()
	tight.name = "Club_TIGHT"
	tight.clip_contents = true
	holder.add_child(tight)
	tight.size = Vector2(60, 32)
	var cells := HBoxContainer.new()
	tight.add_child(cells)
	cells.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for word in ["Fremantle", "1234.5"]:
		var cell := Label.new()
		cell.text = word
		cells.add_child(cell)
	# A club name trimmed to an ellipsis.
	var trim_row := Control.new()
	trim_row.name = "Club_TRIM"
	holder.add_child(trim_row)
	trim_row.position = Vector2(0, 40)
	trim_row.size = Vector2(300, 32)
	var trimmed := Label.new()
	trimmed.name = "Trimmed"
	trimmed.text = "Greater Western Sydney"
	trimmed.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	trim_row.add_child(trimmed)
	trimmed.size = Vector2(40, 24)
	# Two labels set over each other.
	var piled := Control.new()
	piled.name = "Club_PILED"
	holder.add_child(piled)
	piled.position = Vector2(0, 80)
	piled.size = Vector2(300, 32)
	for at in [0.0, 12.0]:
		var word := Label.new()
		word.text = "Bulldogs"
		piled.add_child(word)
		word.position = Vector2(at, 0)
	# A row with room for everything.
	var whole := Button.new()
	whole.name = "Club_WHOLE"
	whole.clip_contents = true
	holder.add_child(whole)
	whole.position = Vector2(0, 120)
	whole.size = Vector2(300, 32)
	var roomy := HBoxContainer.new()
	whole.add_child(roomy)
	roomy.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for word in ["Fremantle", "12"]:
		var cell := Label.new()
		cell.text = word
		roomy.add_child(cell)
	var snug := Button.new()
	snug.text = "Top 10"
	holder.add_child(snug)
	snug.position = Vector2(0, 160)
	await _settle()
	var tight_cut := _cut_text(tight)
	_check(tight_cut.size() >= 1 and str(tight_cut[-1]).contains("runs out of Club_TIGHT"),
			"A cell pushed past its row's clipping edge is reported as clipped (%s)" % str(tight_cut))
	var trim_cut := _cut_text(trim_row)
	_check(trim_cut.size() == 1 and str(trim_cut[0]).contains("is cut to"),
			"A club name trimmed to an ellipsis is reported as clipped (%s)" % str(trim_cut))
	_check(_overlapping(piled).size() == 1,
			"Two labels drawn over each other are reported as overlapping (%s)" % str(_overlapping(piled)))
	_check(_cut_text(whole).is_empty() and _overlapping(whole).is_empty(),
			"A row with room for its words passes (%s %s)" % [str(_cut_text(whole)), str(_overlapping(whole))])
	var fits_first := _button_text_fits(snug)
	snug.clip_text = true
	snug.size = Vector2(20, 30)
	_check(fits_first and not _button_text_fits(snug), "A button narrower than its words is reported as clipped")
	holder.queue_free()
	await _settle()


## The shared table recipe: no panel around the table, every other
## row banded in PANEL, numbers and their headers right-aligned, the position
## muted, a zero muted, the sort key's header bold.
func _table_recipe(s: Node, tag: String, with_pos: bool) -> void:
	var table: Control = s.find_child("LadderTable", true, false)
	_check(table.get_parent().name == "StatsLadder", "The table sits in no panel or card (%s)" % tag)
	var rows := s.find_children("Club_*", "Button", true, false)
	# Row heights: a thumb-sized least is checked in _test_ladder; the exact
	# 32 and 44 px are retired (row 149).
	_check(not rows.is_empty(), "The table has rows (%s)" % tag)
	# Your club's row is in your colour instead of its band.
	var kit = load("res://scripts/ui/UiKit.gd")
	var mine := str(_state.my_club)
	var banded := rows.size() > 1
	var mine_tinted := false
	for i in range(rows.size()):
		var sb := (rows[i] as Button).get_theme_stylebox("normal") as StyleBoxFlat
		if rows[i].name == "Club_" + mine:
			mine_tinted = sb != null and sb.bg_color.is_equal_approx(Color(kit.club_vivid(mine), 0.22))
			continue
		var want := (kit.PANEL as Color) if i % 2 == 1 else Color.TRANSPARENT
		if sb == null or not sb.bg_color.is_equal_approx(want):
			banded = false
	_check(banded, "Every other row is banded in the panel colour (%s)" % tag)
	_check(mine_tinted, "...and your club's row is in your colour (%s)" % tag)
	var right := true
	var zero_muted := true
	var muted: Color = load("res://scripts/ui/UiKit.gd").MUTED
	for b in rows:
		for l in (b as Node).find_children("*", "Label", true, false):
			var tx := str(l.text)
			if tx.is_valid_float() or tx == "-":
				if (l as Label).horizontal_alignment != HORIZONTAL_ALIGNMENT_RIGHT:
					right = false
				if tx.is_valid_float() and float(tx) == 0.0 and (l as Label).get_theme_color("font_color") != muted:
					zero_muted = false
	_check(right, "Numbers are right-aligned (%s)" % tag)
	_check(zero_muted, "A zero is muted (%s)" % tag)
	var head_right := true
	for h in s.find_child("LadderHeader", true, false).get_children():
		if h is Button and str(h.name) != "Sort_club" and (h as Button).alignment != HORIZONTAL_ALIGNMENT_RIGHT:
			head_right = false
	_check(head_right, "Their headers are right-aligned to match (%s)" % tag)
	if with_pos:
		var pos: Label = null
		for l in (rows[0] as Node).find_children("*", "Label", true, false):
			if str(l.text) == "1":
				pos = l
				break
		_check(pos != null and pos.get_theme_color("font_color") == muted and pos.horizontal_alignment == HORIZONTAL_ALIGNMENT_RIGHT,
				"The position is its own muted, right-aligned column (%s)" % tag)


## Team rating and category (director, 2026-10-11): a club's best 22 today on
## the OVR scale, the same list in three seasons, and the phase the AI trades
## on in football words. On the ladder (a List column; a tap on a club says it
## in full), nothing cut off with the longest club names.
func _test_team_rating(sz: Vector2i) -> void:
	var tag := "%dx%d" % [sz.x, sz.y]
	var TR = load("res://scripts/sim/TeamRating.gd")
	var RT = load("res://scripts/sim/Ratings.gd")
	var PT = load("res://scripts/sim/Potential.gd")
	var TV = load("res://scripts/sim/TradeValue.gd")
	if sz.x < 900:
		# The numbers, once: every club against the selector and the AI's rule.
		var rating_ok := true
		var phase_ok := true
		for code in _state.season.lists:
			var list: Array = _state.season.lists[code]
			var side: Dictionary = RT.select_side(list)
			var picked: Array = (side["ground"] as Array) + (side["bench"] as Array)
			var sum := 0.0
			for p in picked:
				sum += float(p["overall"])
			if int(TR.rating(list)) != int(round(sum / float(picked.size()))):
				rating_ok = false
			var standing: Array = _state._standing(code)
			var ages := 0.0
			var sel: Dictionary = RT.select_22(list)
			var both: Array = (sel["ground"] as Array) + (sel["bench"] as Array)
			for q in both:
				ages += float(q.get("age", 25.0))
			var want: String = TV.phase(float(standing[0]), float(standing[1]), ages / float(maxi(1, both.size())))
			var o: Dictionary = _state.team_outlook(code)
			var words := {"contending": "Contender", "building": "Wildcard", "rebuilding": "Rebuilding"}
			if str(o.get("phase", "")) != want or str(o.get("category", "")) != str(words[want]) 					or str(o.get("line", "")) != "%s. Team rating %d. On this list, %d in three years." % [words[want], int(o["rating"]), int(o["forecast"])]:
				phase_ok = false
		# The words under a club on the hub (director, 2026-10-13), pinned to fixed values.
		_check(TR.line("contending", 68, 65) == "Contender. Team rating 68. On this list, 65 in three years."
				and TR.line("rebuilding", 65, 68) == "Rebuilding. Team rating 65. On this list, 68 in three years."
				and TR.line("building", 70, 70) == "Wildcard. Team rating 70. On this list, 70 in three years.",
				"The line under a club reads: category, team rating, then the rating in three years")
		_check(rating_ok, "A club's rating is the mean OVR of the 22 the selector picks")
		_check(phase_ok, "Its category is the phase the AI trades on, in words, for every club")
		# The forecast only ever uses players on the list.
		var some: Array = (_state.season.lists[_state.my_club] as Array).slice(0, 10)
		var vals := []
		for p in some:
			var at: Array = PT.outlook(p, 4)[3]
			if float(at[1]) >= 0.5:
				vals.append(float(at[0]))
		var mean := 0.0
		for x in vals:
			mean += float(x)
		mean = mean / float(maxi(1, vals.size()))
		_check(not vals.is_empty() and int(TR.forecast(some)) == int(round(mean)) and int(TR.forecast([])) == 0,
				"The forecast reads only the players on the list (10 of them: %d)" % int(TR.forecast(some)))
	var Hub = load("res://scripts/ui/StatsHubScene.gd")
	var ladder = load("res://scripts/ui/stats/StatsLadder.gd")
	ladder.reset()
	root.size = sz
	Hub.current = "ladder"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	var head: Button = s.find_child("Sort_rating", true, false)
	_check(head != null and head.text == "Rating", "The ladder has a Rating column (%s)" % tag)
	if head != null:
		_check((await Tap.tap(head)) == "", "Rating takes a tap (%s)" % tag)
		await _settle()
		var vals := []
		for c in _row_codes(s):
			vals.append(int(_state.team_outlook(c)["rating"]))
		_check(_non_increasing(vals), "...and ranks the clubs by their lists, best first (%s)" % tag)
		await Tap.tap(s.find_child("Sort_pos", true, false))
		await _settle()
	_check(s.find_child("Sort_window", true, false) == null and _text(s.find_child("LadderTable", true, false)).find("Contender") < 0,
			"The ladder keeps one compact column; the category is a tap away (%s)" % tag)
	# Nothing cut off, with the longest club names on show.
	var longest := ""
	for c in _row_codes(s):
		if str(root.get_node("GameDB").club_name(c)).length() > str(root.get_node("GameDB").club_name(longest)).length() or longest == "":
			longest = c
	var off := []
	for c in _row_codes(s):
		var row: Node = s.find_child("Club_" + c, true, false)
		for l in row.find_children("*", "Label", true, false):
			if l.is_visible_in_tree() and (l.get_global_rect().end.x > sz.x + 1 or l.get_global_rect().position.x < -1):
				off.append("%s/%s" % [c, l.name])
		var cells: Array = row.get_child(0).get_children()
		var last: Control = cells[cells.size() - 1]
		if last is Label and not _label_fits(last):
			off.append(c + "/last")
	_check(off.is_empty(), "No ladder cell runs off the screen, the Rating column included (%s: %s)" % [tag, str(off)])
	var long_row: Node = s.find_child("Club_" + longest, true, false)
	var shown := ""
	for l in long_row.find_children("*", "Label", true, false):
		if str(l.text).length() > shown.length():
			shown = str(l.text)
	_check(shown.length() >= 3, "The longest club name still reads (%s: %s)" % [tag, shown])
	# A tap on a club says its list in full.
	var mine_row: Button = s.find_child("Club_" + _state.my_club, true, false)
	_check((await Tap.tap(mine_row)) == "", "A club takes a tap (%s)" % tag)
	await _settle()
	var club_page: Node = s.find_child("ClubPage", true, false)
	_check(club_page != null and (await Tap.tap(club_page.find_child("SideOnGround", true, false))) == "",
			"Its page leads to its side (%s)" % tag)
	await _settle()
	var outlook: Label = s.find_child("TeamOutlook", true, false)
	_check(outlook != null and outlook.text == str(_state.team_outlook(_state.my_club)["line"])
			and outlook.text.contains(". On this list, ") and outlook.text.ends_with(" in three years."), "Its side says its list in full (%s: %s)" % [tag, outlook.text if outlook else "-"])
	s.queue_free()
	await _settle()


## The clubs in the table, top to bottom.
func _row_codes(s: Node) -> Array:
	var out := []
	for b in s.find_children("Club_*", "Button", true, false):
		out.append(str(b.name).trim_prefix("Club_"))
	return out


## A ladder column for the clubs in the table, top to bottom.
func _by(s: Node, season, key: String) -> Array:
	var out := []
	for c in _row_codes(s):
		out.append(int(season.ladder[c][key]))
	return out


func _non_increasing(a: Array) -> bool:
	for i in range(1, a.size()):
		if a[i] > a[i - 1]:
			return false
	return true


func _non_decreasing(a: Array) -> bool:
	for i in range(1, a.size()):
		if a[i] < a[i - 1]:
			return false
	return true


## The width the label reading `text` in `row` has been given.
func _label_width(row: Node, text: String) -> float:
	for l in row.find_children("*", "Label", true, false):
		if str(l.text) == text:
			return l.size.x
	return 0.0


## Whether the label reading `text` in `row` is in the bold face.
func _label_bold(row: Node, text: String, bold_font) -> bool:
	for l in row.find_children("*", "Label", true, false):
		if str(l.text) == text:
			return l.get_theme_font("font") == bold_font
	return false


## The finals weeks are in the fixture once the finals start, and not before.
func _test_fixture_finals() -> void:
	var season = _state.season
	var fix = load("res://scripts/ui/stats/StatsFixture.gd")
	_check(fix.pages(season).size() == _rounds() and season.finals.is_empty(),
			"Before the finals the fixture is the home-and-away rounds only")
	var guard := 0
	while season.finals.is_empty() and guard < 40:
		_state.advance()
		guard += 1
	var pgs: Array = fix.pages(season)
	_check(pgs.size() == _rounds() + 1 and bool(pgs.back()["finals"]) and str(pgs.back()["title"]) == "Wildcard finals",
			"The finals week to play joins the fixture once the finals start")
	root.size = Vector2i(390, 844)
	fix.reset()
	load("res://scripts/ui/StatsHubScene.gd").current = "fixture"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	var picker: Button = s.find_child("RoundPicker", true, false)
	_check(picker != null and picker.text == "Wildcard finals", "It opens on the finals week to play (%s)" % (picker.text if picker else "-"))
	var rows: Array = s.find_children("Match_*", "Button", true, false)
	_check(rows.size() == 2 and not bool(rows[0].get_meta("done")), "The wildcard finals are two matches to come")
	var why: String = await Tap.tap(s.find_child("RoundPicker", true, false))
	await _settle()
	var f: Button = s.find_child("RoundPick_%d" % _rounds(), true, false)
	_check(why == "" and f != null and f.text == "Wildcard finals", "The picker lists the finals under the rounds")
	s.call("handle_back")
	s.queue_free()
	await _settle()
	# Play the finals out: every week is there, and the last is the Grand Final.
	guard = 0
	while not season.is_season_over() and guard < 10:
		_state.advance()
		guard += 1
	pgs = fix.pages(season)
	_check(pgs.size() == _rounds() + 5 and str(pgs.back()["title"]) == "Grand Final" and bool(pgs.back()["played"]),
			"After the Grand Final all five finals weeks are in the fixture")
	_check(fix.current_page(pgs) == pgs.size() - 1, "A finished season opens on the Grand Final")


## No label in `node` runs off the screen at this size.
## The closest two of a TeamBuilder's oval tokens (each name's card) come (the director, 2026-11-04: Howes and Pickett overlapped on a PC's
## side sheet, Gawn and Sharp 2 px apart): [gap px, the two names].
static func pitch_gap(builder: Node) -> Array:
	var boxes := []
	for c in builder.find_children("*", "Control", true, false):
		if not c.has_meta("spot") or not (c as Control).is_visible_in_tree():
			continue
		var box: Rect2 = (c as Control).get_global_rect()
		var who := ""
		for l in c.find_children("*", "Label", true, false):
			if who == "" and (l as Label).text.strip_edges() != "":
				who = (l as Label).text
		if who != "":
			boxes.append([box, who])
	var best := [INF, []]
	for i in range(boxes.size()):
		for j in range(i + 1, boxes.size()):
			var p: Rect2 = boxes[i][0]
			var q: Rect2 = boxes[j][0]
			var dx := maxf(q.position.x - p.end.x, p.position.x - q.end.x)
			var dy := maxf(q.position.y - p.end.y, p.position.y - q.end.y)
			var g := maxf(dx, dy)
			if g < float(best[0]):
				best = [g, [boxes[i][1], boxes[j][1]]]
	return best


## Cards whose corners cross the oval's white boundary (the line is drawn on
## the pitch's rect inset 2 px): [names] of any corner outside it.
static func pitch_off_ground(builder: Node) -> Array:
	var off := []
	for c in builder.find_children("*", "Control", true, false):
		if not c.has_meta("spot") or not (c as Control).is_visible_in_tree():
			continue
		var pitch: Control = c.get_parent()
		var g := Rect2(Vector2.ZERO, pitch.size).grow(-3.0)
		var k := c as Control
		for corner in [k.position, k.position + Vector2(k.size.x, 0), k.position + Vector2(0, k.size.y), k.position + k.size]:
			var q: Vector2 = (corner - g.get_center()) / (g.size * 0.5)
			if q.length_squared() > 1.0:
				off.append(str(c.get_meta("spot")))
				break
	return off


## How far the left and right twins (BPL/BPR, HBFL/HBFR, IL/IR, WL/WR,
## HFFL/HFFR, FPL/FPR) sit from mirror images of each other, in px: [px, key].
static func pitch_skew(builder: Node) -> Array:
	var at := {}
	var pitch: Control = null
	for c in builder.find_children("*", "Control", true, false):
		if c.has_meta("spot") and (c as Control).is_visible_in_tree():
			at[str(c.get_meta("spot"))] = (c as Control).position + (c as Control).size * 0.5
			pitch = c.get_parent()
	var worst := [0.0, ""]
	if pitch == null:
		return worst
	var mid: Vector2 = pitch.size * 0.5
	for k in ["BP", "HBF", "I", "W", "HFF", "FP"]:
		if not at.has(k + "L") or not at.has(k + "R"):
			continue
		var a: Vector2 = at[k + "L"] - mid
		var b: Vector2 = at[k + "R"] - mid
		# Twins mirror across the ground's length: one coordinate equal, the other opposite.
		var d := minf(absf(a.x + b.x) + absf(a.y - b.y), absf(a.x - b.x) + absf(a.y + b.y))
		if d > float(worst[0]):
			worst = [d, k]
	return worst


func _fits(node: Node, sz: Vector2i, what: String, tag: String) -> void:
	var off := []
	for c in node.find_children("*", "Label", true, false):
		if c.is_visible_in_tree() and c.get_global_rect().end.x > sz.x + 1:
			off.append(str(c.name))
	_check(off.is_empty(), "Nothing runs off the screen on %s (%s: %s)" % [what, tag, str(off)])


func _text(node: Node) -> String:
	if node == null:
		return ""
	var out := ""
	for n in node.find_children("*", "Label", true, false):
		out += str(n.text) + "\n"
	if node is Label or node is Button:
		out += str(node.text)
	return out


## Rounds in the home-and-away season. Loaded, not named as Season: the
## autoloads are not there when this script compiles.
func _rounds() -> int:
	return load("res://scripts/sim/Season.gd").REGULAR_ROUNDS
## Before a ball is bounced: every race says so, nothing is projected.
func _test_awards_early() -> void:
	var s := await _open_awards(Vector2i(390, 844))
	_check(s.find_child("AwardsProvisional", true, false) != null, "Awards before Round 1 are labelled provisional")
	var none: Label = s.find_child("ColemanEmpty", true, false)
	_check(none != null and none.text == "No goals kicked yet.", "The Coleman race before a goal says so")
	_check(s.find_child("Coleman_1", true, false) == null, "No Coleman leader before a goal")
	_check(s.find_child("CoachesAwardEmpty", true, false) != null, "The Coaches Award before a vote says so")
	_check(s.find_child("AATeam", true, false) == null, "No projected All-Australian team before Round 1")
	_check(s.find_child("BrownlowSealed", true, false) != null, "The Brownlow is sealed before Round 1")
	await _close(s)


## Four rounds in, at a phone's size and a PC's: the races, the sealed
## Brownlow, the projected team, and real taps on a player and the team.
func _test_awards_races() -> void:
	var min_games: int = _aw.aa_min_games(4)
	_check(min_games == 2, "The All-Australian minimum after 4 of 24 rounds is 2 games (%d)" % min_games)
	for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
		var s := await _open_awards(sz)
		var tag := "%dx%d" % [sz.x, sz.y]
		var prov: Label = s.find_child("AwardsProvisional", true, false)
		_check(prov != null and prov.text.contains("After Round 4") and prov.text.contains("Nothing here is awarded"),
				"The races are labelled provisional (%s)" % tag)
		_check(s.find_child("AwardsHonours", true, false) == null, "No honours before they are awarded (%s)" % tag)
		var sealed: Node = s.find_child("BrownlowSealed", true, false)
		_check(sealed != null and sealed.find_children("*", "Button", true, false).is_empty(),
				"The Brownlow stays sealed: no names, no counts (%s)" % tag)
		var proj: Label = s.find_child("AAProjected", true, false)
		_check(proj != null and proj.text.begins_with("Projected") and proj.text.contains("2 or more games"),
				"The All-Australian team is labelled projected, with its games line (%s)" % tag)
		_check(s.find_child("AANamed", true, false) == null, "The projected team is never called named (%s)" % tag)
		# A finger on the Coleman leader opens his profile; Back shuts it first.
		var lead: Button = s.find_child("Coleman_1", true, false)
		_check(lead != null, "The Coleman race has a leader (%s)" % tag)
		if lead != null:
			_check((await Tap.tap(lead)) == "", "The Coleman leader takes a tap (%s)" % tag)
			await _settle()
			_check(s.find_child("PlayerProfile", true, false) != null, "The tap opens his profile (%s)" % tag)
			_check(s.call("handle_back"), "Back closes the profile first (%s)" % tag)
			await _settle()
			_check(s.find_child("PlayerProfile", true, false) == null and not s.call("handle_back"),
					"The profile is gone, and the next Back leaves (%s)" % tag)
		# The projected team on the oval: 18 spots and five on the bench, filled.
		var team: Node = s.find_child("AATeam", true, false)
		if team != null:
			var agap: Array = pitch_gap(team)
			print("PITCHGAP aa %s %.1f %s" % [tag, float(agap[0]), str(agap[1])])
			var aoff: Array = pitch_off_ground(team)
			print("PITCHOFF aa %s %s" % [tag, str(aoff)])
			print("PITCHSKEW aa %s %s" % [tag, str(pitch_skew(team))])
			_check(aoff.is_empty(), "Every card on the All-Australian oval sits inside the boundary line (%s: %s)" % [tag, str(aoff)])
			_check(float(agap[0]) >= 8.0, "No two names on the All-Australian oval come within 8 px (%s: %.1f px, %s)" % [tag, float(agap[0]), str(agap[1])])
		var spots := []
		if team != null:
			for c in team.find_children("*Spot_*", "Button", true, false):
				if str(c.get_meta("id", "")) != "":
					spots.append(c)
		_check(spots.size() == 23, "The projected team fills 23 spots on the oval (%s: %d)" % [tag, spots.size()])
		_check(team != null and team.find_child("BuilderSearch", true, false) == null
				and team.find_child("NotSelected", true, false) == null, "The team shows just the oval (%s)" % tag)
		var ruck: Button = team.find_child("Spot_RUCK", true, false) if team != null else null
		_check(ruck != null, "The projected team has a ruckman (%s)" % tag)
		if ruck != null:
			_check((await Tap.tap(ruck)) == "", "The All-Australian ruckman takes a tap (%s)" % tag)
			await _settle()
			_check(s.find_child("PlayerProfile", true, false) != null, "The tap opens the ruckman's profile (%s)" % tag)
			s.call("handle_back")
			await _settle()
		await _close(s)
	# The projected team by position, from the tally so far.
	var players := _players()
	var team: Array = _aw.projected_all_australian(_state.season_tally, players, min_games)
	var slots := {}
	var ok := true
	var ids := {}
	for r in team:
		slots[str(r["slot"])] = int(slots.get(str(r["slot"]), 0)) + 1
		ids[str(r["id"])] = true
		if int(r["games"]) < min_games:
			ok = false
		if str(r["slot"]) != "BENCH" and str(players[str(r["id"])]["role"]) != str(r["slot"]):
			ok = false
	_check(team.size() == 23 and ids.size() == 23, "The projected All-Australian team is 23 different players (%d)" % team.size())
	_check(slots == {"RUCK": 1, "MID": 5, "DEF": 6, "FWD": 6, "BENCH": 5} and ok,
			"Every projected All-Australian plays his position and has the games (%s)" % str(slots))


## The Awards tab after four rounds of the suite's seeded season, read off the
## screen: every race row, every Rising Star row and every card on the
## All-Australian oval with where it sits. Recorded from main before the
## Awards speed-up (AWARDS_SNAPSHOT_WRITE=1 rewrites it); the faster tab must
## show exactly the same thing.
const AWARDS_SNAPSHOT := "res://tests/fixtures/awards_round4_snapshot.txt"


func _awards_snapshot(s: Control, tag: String) -> PackedStringArray:
	var out := PackedStringArray()
	var sec: Node = s.find_child("StatsAwards", true, false)
	if sec == null:
		return out
	for b in sec.find_children("*", "Button", true, false):
		var words := PackedStringArray()
		for l in (b as Node).find_children("*", "Label", true, false):
			words.append((l as Label).text)
		var line := "%s %s | %s" % [tag, str(b.name), " | ".join(words)]
		if str(b.name).contains("Spot_"):
			var c := b as Control
			line += " | id %s at %.2f,%.2f size %.2f,%.2f" % [str(c.get_meta("id", "")),
					c.position.x, c.position.y, c.size.x, c.size.y]
		out.append(line)
	return out


func _test_awards_unchanged() -> void:
	var now := PackedStringArray()
	for sz in [Vector2i(390, 844), Vector2i(360, 800), Vector2i(1280, 720)]:
		var s := await _open_awards(sz)
		now.append_array(_awards_snapshot(s, "%dx%d" % [sz.x, sz.y]))
		await _close(s)
	_check(now.size() > 60, "The Awards tab has its races, nominations and oval to compare (%d lines)" % now.size())
	if OS.get_environment("AWARDS_SNAPSHOT_WRITE") == "1":
		var f := FileAccess.open(ProjectSettings.globalize_path(AWARDS_SNAPSHOT), FileAccess.WRITE)
		f.store_string("\n".join(now) + "\n")
		f.close()
		print("Wrote %s (%d lines)" % [AWARDS_SNAPSHOT, now.size()])
		return
	var want := FileAccess.get_file_as_string(AWARDS_SNAPSHOT).strip_edges().split("\n")
	var first := ""
	for i in range(maxi(want.size(), now.size())):
		var a: String = want[i] if i < want.size() else "(none)"
		var b: String = now[i] if i < now.size() else "(none)"
		if a != b:
			first = "line %d: want '%s', got '%s'" % [i + 1, a, b]
			break
	if first != "":
		# Any redraw of the seeded season changes this fixture. The whole new snapshot goes to the
		# log (CI artifact test-logs-shard-N, stats.log), so it can be refreshed without a local run.
		for line in now:
			print("AWARDS_FIXTURE|", line)
	_check(first == "", "The Awards tab shows exactly what it did before the speed-up (%d lines; %s)" % [now.size(), first])


## The director's report: the Awards tab was slow to open. A tap on the tab
## builds the section and lays out the oval's cards once (not again for every
## size the page passes through on its way to the screen), well inside a
## frame budget a phone can live with.
func _test_awards_open_fast() -> void:
	root.size = Vector2i(390, 844)
	load("res://scripts/ui/StatsHubScene.gd").current = "ladder"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	await _settle()
	var tab: Button = s.find_child("Section_awards", true, false)
	_check(tab != null, "Season stats has its Awards tab")
	if tab == null:
		await _close(s)
		return
	var tb = load("res://scripts/ui/TeamBuilder.gd")
	tb.layouts = 0
	var t0 := Time.get_ticks_usec()
	_check((await Tap.tap(tab)) == "", "The Awards tab takes a tap")
	var team: Node = null
	for i in range(30):
		await process_frame
		team = s.find_child("AATeam", true, false)
		if team != null:
			break
	await process_frame
	var ms := (Time.get_ticks_usec() - t0) / 1000.0
	print("PERF awards tab tap to drawn: %.0f ms, %d oval layouts" % [ms, int(tb.layouts)])
	_check(team != null, "The tap opens the Awards tab with its oval")
	_check(int(tb.layouts) == 1, "The oval's cards are laid out once on the way in (%d)" % int(tb.layouts))
	_check(ms < 400.0, "The Awards tab opens inside 400 ms here (%.0f ms; it took over 20 s before the fix)" % ms)
	await _close(s)


## Level counts share a rank; a tie across the cut is summed up, never split.
func _test_awards_ties() -> void:
	var keep: Dictionary = _state.season_tally
	var ids := []
	for p in _state.season.lists["COL"]:
		ids.append(str(p["id"]))
	var tally := {}
	var goals := [9, 5, 5, 5, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
	for i in range(goals.size()):
		tally[ids[i]] = _row(goals[i])
	_state.season_tally = tally
	var s := await _open_awards(Vector2i(390, 844))
	var ranks := []
	for i in range(1, 6):
		var b: Node = s.find_child("Coleman_%d" % i, true, false)
		ranks.append(_rank(b) if b != null else "-")
	_check(ranks == ["1", "2", "2", "2", "-"], "Level goals share a rank and a tie across the cut isn't split (%s)" % str(ranks))
	var more: Label = s.find_child("ColemanMore", true, false)
	_check(more != null and more.text == "10 more on 2 goals.", "The tie at the cut is summed up (%s)" % (more.text if more else "none"))
	await _close(s)
	# Twelve level on one goal: the leaders are shown, the rest counted.
	tally = {}
	for i in range(12):
		tally[ids[i]] = _row(1)
	_state.season_tally = tally
	s = await _open_awards(Vector2i(390, 844))
	var b10: Node = s.find_child("Coleman_10", true, false)
	more = s.find_child("ColemanMore", true, false)
	_check(b10 != null and _rank(b10) == "1" and more != null and more.text == "2 more on 1 goal.",
			"Twelve level leaders: ten shown at rank 1, two counted (%s)" % (more.text if more else "none"))
	await _close(s)
	_state.season_tally = keep


## One nominee a round: the most influential eligible player, once a season.
func _test_rising_star_rules() -> void:
	var res := {"home": "COL", "away": "CAR",
		"roster": [[{"id": "old"}, {"id": "kid"}], [{"id": "kid2"}]],
		"players": {"old": {"disposals": 40}, "kid": {"disposals": 20}, "kid2": {"disposals": 10}}}
	var ages := {"old": 22.0, "kid": 20.0, "kid2": 19.0}
	_check(str(_aw.rising_star_nominee([res], ages, {}).get("id", "")) == "kid",
			"The Rising Star nominee is the best player 21 and under, not the best overall")
	_check(str(_aw.rising_star_nominee([res], ages, {"kid": true}).get("id", "")) == "kid2",
			"A player is nominated once a season")
	var fin := res.duplicate()
	fin["tag"] = "GF"
	_check(_aw.rising_star_nominee([fin], ages, {}).is_empty(), "Finals bring no nomination")
	# The four rounds so far: one nominee each, all eligible, all different.
	var noms: Array = _state.rising_star_noms["rounds"]
	var players := _players()
	var rounds := []
	var seen := {}
	var young := true
	for n in noms:
		rounds.append(int(n["round"]))
		seen[str(n["id"])] = true
		if float(players[str(n["id"])]["age"]) > _aw.RISING_STAR_AGE:
			young = false
	_check(rounds == [1, 2, 3, 4] and seen.size() == 4 and young,
			"Four rounds, four different nominees, all 21 or under (%s)" % str(rounds))
	var before := {}
	for n in noms.slice(0, 3):
		before[str(n["id"])] = true
	var ages_now := {}
	for id in players:
		ages_now[id] = float(players[id]["age"])
	var pick: Dictionary = _aw.rising_star_nominee(_state.last_results, ages_now, before)
	_check(noms.size() == 4 and str(pick.get("id", "")) == str(noms[3]["id"]),
			"Round 4's nominee was that round's best eligible player")
	# The winner comes from the nominees, as in the AFL; a season without a
	# full record (an older save) keeps the old rule.
	var tally := {"a": _row(0, 10, 10), "b": _row(0, 5, 3)}
	var who := {"a": {"role": "MID", "age": 20.0}, "b": {"role": "MID", "age": 19.0}}
	var full: Dictionary = _aw.season_awards(tally, who, 2026, {"from": 1, "rounds": [{"round": 1, "id": "b", "club": "COL"}]})
	_check(str(full["rising_star"][0]["id"]) == "b", "With every round recorded, the Rising Star comes from the nominees")
	var old: Dictionary = _aw.season_awards(tally, who, 2026, {"from": 5, "rounds": [{"round": 5, "id": "b", "club": "COL"}]})
	_check(old["rising_star"].size() == 1 and str(old["rising_star"][0]["id"]) == "a",
			"Without a full record (an older save), the old Rising Star rule stands")


## Nominations survive a save and load; an older save says which rounds it
## never recorded, and records from the next round on.
func _test_rising_star_saves() -> void:
	var before := JSON.stringify(_state.rising_star_noms)
	_check(_state.save_career() and _state.load_career(), "The career saves and loads")
	_check(JSON.stringify(_state.rising_star_noms) == before, "The Rising Star nominations survive a save and load")
	var s := await _open_awards(Vector2i(390, 844))
	_check(s.find_child("RisingStar_4", true, false) != null and s.find_child("RisingStarUnrecorded", true, false) == null,
			"The nominations show by round, with no unrecorded rounds")
	await _close(s)
	var state: Dictionary = _cs.read(_state.save_path)
	var meta: Dictionary = _cs.read_meta(_state.save_path)
	state.erase("rising_star_noms")
	_cs.write(state, meta, _state.save_path)
	_check(_state.load_career(), "An older save, without nominations, loads")
	_check(int(_state.rising_star_noms["from"]) == 5 and (_state.rising_star_noms["rounds"] as Array).is_empty(),
			"An older save invents no nominations for the rounds played")
	s = await _open_awards(Vector2i(390, 844))
	var gap: Label = s.find_child("RisingStarUnrecorded", true, false)
	_check(gap != null and gap.text == "Nominations from Rounds 1 to 4 weren't recorded in this save."
			and s.find_child("RisingStar_1", true, false) == null, "An older save says plainly which rounds weren't recorded")
	await _close(s)
	_state.advance()
	var noms: Array = _state.rising_star_noms["rounds"]
	_check(noms.size() == 1 and int(noms[0]["round"]) == 5, "Recording starts with the next round")


## Once the season's awards are presented they lead, labelled awarded, and
## nothing is called projected.
func _test_awards_awarded() -> void:
	_state.season_awards = _aw.season_awards(_state.season_tally, _players(), _state.season_year,
			_state.rising_star_noms)
	for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
		var s := await _open_awards(sz)
		var tag := "%dx%d" % [sz.x, sz.y]
		var awarded: Label = s.find_child("AwardsAwarded", true, false)
		_check(s.find_child("AwardsHonours", true, false) != null and awarded != null and awarded.text.begins_with("Awarded"),
				"Presented awards are labelled awarded (%s)" % tag)
		_check(s.find_child("AwardsProvisional", true, false) == null and s.find_child("AAProjected", true, false) == null,
				"Nothing presented is called provisional or projected (%s)" % tag)
		_check(s.find_child("AANamed", true, false) != null, "The All-Australian team is the one named (%s)" % tag)
		var medal: Button = s.find_child("Honour_BrownlowMedal", true, false)
		var fig: Label = medal.find_child("Figure", true, false) if medal != null else null
		_check(fig != null and (fig.text.ends_with(" votes") or fig.text.ends_with(" vote")),
				"The medallist's count carries its unit (%s: %s)" % [tag, fig.text if fig else "none"])
		var name_l: Label = medal.find_child("Name", true, false) if medal != null else null
		var club_l: Label = medal.find_child("Club", true, false) if medal != null else null
		_check(name_l != null and club_l != null and _label_fits(name_l),
				"The medallist's name fits in full, beside the count (%s, club %s)"
				% [tag, "under the name" if club_l != null and name_l != null and name_l.get_parent() == club_l.get_parent() else "beside it"])
		_check(medal != null and (await Tap.tap(medal)) == "", "The Brownlow medallist takes a tap (%s)" % tag)
		await _settle()
		_check(s.find_child("PlayerProfile", true, false) != null, "The tap opens the medallist's profile (%s)" % tag)
		await _close(s)
	_state.season_awards = {}


func _players() -> Dictionary:
	var out := {}
	for code in _state.season.lists:
		for p in _state.season.lists[code]:
			out[str(p["id"])] = p
	return out


func _row(goals: int, votes := 0, games := 4) -> Dictionary:
	return {"club": "COL", "games": games, "goals": goals, "goals_ha": goals, "disposals": 0,
			"distance_run": 0.0, "influence": 10.0 * games, "votes": votes, "bf": 0, "polled": 0, "coaches": 0}


## Whether a label shows its whole text, without an ellipsis.
func _label_fits(l: Label) -> bool:
	var w := l.get_theme_font("font").get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1,
			l.get_theme_font_size("font_size")).x
	return w <= l.size.x + 1.0


func _rank(row: Node) -> String:
	return str((row.get_child(0).get_child(0) as Label).text)


## Every club's line under a name on the Season stats lists (director,
## 2026-11-06): its strongest real colour, never white or the pitch tint, read
## at 4.5:1 on every surface its row can sit on (the page up to PANEL_ALT, a
## pressed row, and your own club's tinted row), one of its real colours or
## one lightened with its hue kept. Collingwood has no colour but black and
## white: it reads plain white (director 2026-11-07, "white").
func _test_club_code_colours() -> void:
	var UK = load("res://scripts/ui/UiKit.gd")
	var SS = load("res://scripts/ui/stats/StatsSide.gd")
	var db = root.get_node("GameDB")
	var codes := ["ADE", "BRL", "CAR", "COL", "ESS", "FRE", "GEE", "GCS", "GWS", "HAW", "MEL", "NTH",
			"PAD", "RIC", "STK", "SYD", "WCE", "WBD", "TAS", "CANB"]
	var was: String = _state.my_club
	var line := []
	# Each club both as a rival's row and as your own (tinted) row.
	for own in [false, true]:
		for code in codes:
			_state.my_club = code if own else ("COL" if code != "COL" else "CAR")
			var c: Color = SS.code_ink(code)
			line.append("%s%s #%s" % [code, " (own)" if own else "", c.to_html(false).to_upper()])
			var lo: float = UK.min_contrast(c, SS.row_surfaces(code))
			_check(lo >= 4.5, "%s's code reads at 4.5:1 on every row surface%s (%.2f)" % [code, ", own club" if own else "", lo])
			var real: Array = db.club_marker_colours(code)
			var vivid := real.filter(func(r: Color) -> bool: return r.s >= UK.CODE_MIN_SAT)
			if vivid.is_empty():
				_check(code == "COL" and c.is_equal_approx(UK.TEXT), "%s: no colour but black and white, so plain white (#%s)" % [code, c.to_html(false)])
				continue
			_check(not (c.v > 0.9 and c.s < 0.15), "%s's code is never white" % code)
			_check(c.s >= UK.CODE_MIN_SAT, "%s's code is a colour, not grey" % code)
			var from_real := false
			for r in vivid:
				var col: Color = r
				if c.is_equal_approx(col) or (absf(c.h - col.h) < 0.01 and c.v >= col.v - 0.01 and c.s <= col.s + 0.01):
					from_real = true
			_check(from_real, "%s's code is one of its real colours or one lightened, same hue (#%s)" % [code, c.to_html(false)])
			_check(not db.club_colours(code)[2].is_equal_approx(c) or db.THREE_COLOUR_CLUBS.has(code),
					"%s's code is not its pitch tint" % code)
	# A sheet's wash (director 2026-11-07, "fix now"): Collingwood's is its
	# black lifted to a neutral grey, never the accent's red-brown; every
	# other club keeps its own colour.
	_state.my_club = "COL"
	var pw: Color = UK.team_wash()
	_check(pw.s < 0.05 and not pw.is_equal_approx(UK.ACCENT) and pw.get_luminance() > 0.1,
			"Collingwood's sheet wash is a neutral grey (#%s)" % pw.to_html(false))
	var pb: Color = UK.team_button()
	_check(pb.s < 0.05 and not pb.is_equal_approx(UK.ACCENT) and pb.get_luminance() >= UK.SURFACE.get_luminance() + 0.15,
			"Collingwood's buttons are a grey clear of the quiet buttons (#%s)" % pb.to_html(false))
	_check(UK.ink_on(pb).is_equal_approx(UK.TEXT) or UK.min_contrast(UK.ink_on(pb), [pb]) >= 4.5,
			"Collingwood's button label reads")
	for code in ["CAR", "RIC", "ESS", "MEL"]:
		_state.my_club = code
		_check(UK.team_wash().is_equal_approx(UK.team_colour()), "%s's sheet wash is its own colour" % code)
		_check(UK.team_button().is_equal_approx(UK.team_colour()), "%s's buttons are its own colour" % code)
	_state.my_club = was
	print("Club code colours: " + ", ".join(line))
	# A Forge club whose colours are all pale never falls back to its white.
	db.clubs["ZZF"] = {"code": "ZZF", "custom": true, "primary": Color("ffffff"),
			"secondary": Color("f4f0e8"), "accent": Color("d8d8d0")}
	var f: Color = SS.code_ink("ZZF")
	_check(not (f.v > 0.9 and f.s < 0.15), "A pale Forge club's code is not white (#%s)" % f.to_html(false))
	_check(UK.min_contrast(f, SS.row_surfaces("ZZF")) >= 4.5, "A pale Forge club's code reads")
	db.clubs["ZZF"]["secondary"] = Color("1a6b3c")
	f = SS.code_ink("ZZF")
	_check(f.s >= UK.CODE_MIN_SAT and absf(f.h - Color("1a6b3c").h) < 0.01,
			"A Forge club with one real colour among the pale: that colour, lightened (#%s)" % f.to_html(false))
	db.clubs.erase("ZZF")


## This season's Finals cell in the trophy room: the round before the finals,
## the final during them, the result after.
func _test_finals_cell() -> void:
	var T = load("res://scripts/ui/ClubTrophies.gd")
	var se = load("res://scripts/sim/Season.gd").new(["COL", "CAR"], {})
	se.fixture = []
	for i in range(24):
		se.fixture.append([])
	se.round_index = 3
	_check(T.progress(se, "COL") == "Round 3 of 24", "After round 3: Round 3 of 24 (%s)" % T.progress(se, "COL"))
	se.round_index = 24
	se.finals = {"week": 1, "weeks": [], "done": false, "premier": "", "runner_up": ""}
	_check(T.progress(se, "COL") == "Round 24 of 24", "Finals set but not begun: still Round 24 of 24 (%s)" % T.progress(se, "COL"))
	se.finals["weeks"] = [[{"home": "GEE", "away": "STK", "tag": "WC1"}], [{"home": "COL", "away": "CAR", "tag": "QF1"}]]
	se.finals["week"] = 3
	_check(T.progress(se, "COL") == "Qualifying final", "During the finals: the final you played (%s)" % T.progress(se, "COL"))
	_check(T.progress(se, "ADE") == "Qualifying and elimination finals", "Not in it: the week as the Fixture names it (%s)" % T.progress(se, "ADE"))
	se.finals["weeks"].append([{"home": "CAR", "away": "GEE", "tag": "SF1"}])
	se.finals["weeks"].append([{"home": "CAR", "away": "SYD", "tag": "PF1"}])
	se.finals["weeks"].append([{"home": "COL", "away": "SYD", "tag": "GF"}])
	se.finals["done"] = true
	se.finals["premier"] = "COL"
	se.finals["runner_up"] = "SYD"
	_check(T.progress(se, "COL") == "Premiers", "Finished: the result, Premiers (%s)" % T.progress(se, "COL"))
	_check(T.progress(se, "SYD") == "Runners-up", "Finished: Runners-up (%s)" % T.progress(se, "SYD"))
	_check(T.progress(se, "CAR") == "Preliminary final", "Finished: out in a preliminary final (%s)" % T.progress(se, "CAR"))
	_check(T.progress(se, "MEL") == "", "Finished without a final: blank, as a past season reads (%s)" % T.progress(se, "MEL"))


## The trophy room through a first season and into a seeded second: empty
## and honest at first, then a premiership on the shelf, only your club's
## seasons counted, older entries said plainly, taps and Back, save and load.
func _test_trophies_early() -> void:
	var year: int = _state.season_year
	var s := await _open_trophies(Vector2i(390, 844))
	var none: Label = s.find_child("NoPremierships", true, false)
	_check(none != null and none.text == "No premierships yet.", "An empty trophy room says so: no premierships yet")
	_check(s.find_child("NoPlayerHonours", true, false) != null, "No player honours yet, said plainly")
	_check(s.find_child("AwardFilter", true, false) == null, "With nothing won there is nothing to filter")
	var intro: Label = s.find_child("TrophiesTenure", true, false)
	_check(intro != null and intro.text == "Your time at %s: 1 season, from %d." % [root.get_node("GameDB").club_name("COL"), year],
			"The tenure line counts the season in progress (%s)" % (intro.text if intro else "none"))
	var now: Node = s.find_child("Season_%d" % year, true, false)
	var at := "Round %d of %d" % [maxi(1, _state.season.round_index), _state.season.fixture.size()]
	_check(now != null and _row_text(now).contains(at), "This season is in the table, at %s (%s)" % [at, _row_text(now) if now else "none"])
	_check(now != null and _finish(now) != "", "Mid-season it gives where you sit (%s)" % (_finish(now) if now else "none"))
	s.queue_free()
	await _settle()


## Before a game this season's row gives no ladder finish: there is no
## ladder to sit on yet.
func _test_trophies_unplayed() -> void:
	var s := await _open_trophies(Vector2i(390, 844))
	var now: Node = s.find_child("Season_%d" % _state.season_year, true, false)
	_check(now != null and _finish(now) == "" and _row_text(now).contains("0-0-0"),
			"Before a game, this season's row gives no finish (%s)" % (_row_text(now) if now else "none"))
	s.queue_free()
	await _settle()


## The Finish column of a row in Your seasons.
func _finish(row: Node) -> String:
	var cells := row.find_children("*", "Label", true, false)
	return str((cells[1] as Label).text) if cells.size() > 1 else "?"


## ...and once the season is over (the fixture's finals test plays it out).
func _test_trophies() -> void:
	var year: int = _state.season_year
	var s: Control
	var intro: Label
	# Play the season out: its honour roll entry records your season.
	var guard := 0
	while not _state.season_is_over() and guard < 40:
		_state.advance()
		guard += 1
	var entry: Dictionary = _state.honour_roll.back() if not _state.honour_roll.is_empty() else {}
	_check(int(entry.get("year", 0)) == year and str(entry.get("my_club", "")) == "COL",
			"The finished season is on the honour roll")
	_check(str(entry.get("my_record", "")) == _state.my_record() and str(entry.get("my_record", "")).split("-").size() == 3,
			"The season's record is kept (%s)" % str(entry.get("my_record", "")))
	var tags := {}
	for week in _state.season.finals.get("weeks", []):
		for res in week:
			if _state.is_my_match(res):
				tags[str(res["tag"])] = true
	_check(entry.has("my_finals") and (str(entry["my_finals"]) == "" if tags.is_empty() else tags.has(str(entry["my_finals"]))),
			"How far the finals went is kept (%s)" % str(entry.get("my_finals", "missing")))
	var aa_ok: bool = entry.has("my_aa")
	for r in _state.season_awards.get("all_australian", []):
		if (str(r["club"]) == "COL") != (entry.get("my_aa", []) as Array).has(str(r["id"])):
			aa_ok = false
	_check(aa_ok, "Your club's All-Australians are kept, and only yours")
	# Seed the rest: a season coaching elsewhere (never yours to count), an
	# older entry without the new keys, and this season as a premiership.
	var ids := []
	for p in _state.season.lists["COL"]:
		ids.append(str(p["id"]))
	entry["premier"] = "COL"
	entry["runner_up"] = "CAR"
	entry["my_position"] = 1
	entry["my_aa"] = [ids[2]]
	entry["brownlow"] = [{"id": ids[0], "club": "COL", "votes": 31}]
	for key in ["coleman", "rising_star", "coaches_award", "my_bf", "norm_smith", "golden_fist"]:
		entry[key] = []
	var old := {"year": year - 1, "my_club": "COL", "premier": "GEE", "runner_up": "COL", "my_position": 3,
		"brownlow": [], "coleman": [{"id": "far_away", "club": "CAR", "goals": 70}], "rising_star": [],
		"coaches_award": [], "my_bf": [{"id": ids[0], "club": "COL", "bf": 120}]}
	var elsewhere := {"year": year - 2, "my_club": "CAR", "premier": "COL", "runner_up": "GEE", "my_position": 1,
		"brownlow": [{"id": ids[3], "club": "COL", "votes": 40}], "coleman": [], "rising_star": [],
		"coaches_award": [], "my_bf": [], "my_record": "20-3-0", "my_finals": "GF1", "my_aa": []}
	_state.honour_roll = [elsewhere, old, entry]
	# The club's real history from the data file (a stand-in table here): a long
	# list, so it has to wrap on a phone.
	var hist_years := [1896, 1902, 1910, 1917, 1919, 1927, 1928, 1930, 1935, 1936, 1953, 1958, 1990, 2010, 2023]
	ClubHistory.use({"COL": {"years": hist_years, "comps": {}, "also": {"Fitzroy": [1898, 1899]}, "none": false}})
	for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
		s = await _open_trophies(sz)
		var tag := "%dx%d" % [sz.x, sz.y]
		var hist_title: Label = s.find_child("HistoryTitle", true, false)
		var hist_list: Label = s.find_child("HistoryYears", true, false)
		var yours: Label = s.find_child("YourPremierships", true, false)
		_check(hist_title != null and hist_title.text == "Before you: 15 premierships"
				and hist_list != null and hist_list.text == ", ".join(hist_years.map(func(y): return str(y))),
				"The club's history reads from the file: a count, then every year (%s)" % tag)
		var fz: Label = s.find_child("HistoryAsYears_Fitzroy", true, false)
		var fzt: Label = s.find_child("HistoryAs_Fitzroy", true, false)
		_check(fz != null and fz.text == "1898, 1899" and fzt != null and fzt.text == "Fitzroy: 2 premierships",
				"Flags carried from a merged club read under its name, apart from the club's own (%s)" % tag)
		_check(hist_list != null and hist_list.get_theme_color("font_color") == load("res://scripts/ui/UiKit.gd").MUTED
				and hist_list.autowrap_mode != TextServer.AUTOWRAP_OFF and hist_list.get_combined_minimum_size().x < 380.0,
				"The history is the quiet colour and wraps rather than widening the screen (%s)" % tag)
		_check(hist_list != null and yours != null and hist_list.is_visible_in_tree()
				and s.find_child("ClubHistory", true, false).get_index() < yours.get_index()
				and yours.get_index() < s.find_child("ClubShelf", true, false).get_index(),
				"History comes first, then 'Your premierships' with your own flags apart from it (%s)" % tag)
		_check(yours != null and s.find_children("Club_premiership_*", "Button", true, false).size() == 1
				and s.find_child("ClubHistory", true, false).find_child("Club_premiership_%d" % year, true, false) == null,
				"Your flag is on the shelf, not among the history years (%s)" % tag)
		s.queue_free()
		await _settle()
	for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
		s = await _open_trophies(sz)
		var tag := "%dx%d" % [sz.x, sz.y]
		intro = s.find_child("TrophiesTenure", true, false)
		_check(intro != null and intro.text.ends_with("2 seasons, from %d." % (year - 1)),
				"Only seasons at your club count (%s: %s)" % [tag, intro.text if intro else "none"])
		var flag: Button = s.find_child("Club_premiership_%d" % year, true, false)
		_check(flag != null and s.find_child("Club_minor_premiership_%d" % year, true, false) != null,
				"The premiership and minor premiership are on the shelf (%s)" % tag)
		_check(s.find_child("Club_premiership_%d" % (year - 2), true, false) == null
				and s.find_child("NoPremierships", true, false) == null,
				"A flag from before your time isn't yours (%s)" % tag)
		_check(flag != null and (flag.find_child("Honour_premiership_cup", true, false) != null
				or flag.find_child("StandIn_premiership_cup", true, false) != null),
				"The cup shows: its art, or its name standing in (%s)" % tag)
		# By player: his name, then all his honours under it.
		var groups := []
		for g in s.find_children("PlayerGroup_*", "", true, false):
			var hon := []
			var gs: Node = g.find_child("PlayerShelf", true, false)
			for b in gs.get_children() if gs != null else []:
				hon.append("%s %s" % [(b.find_child("Top", true, false) as Label).text,
						(b.find_child("Bottom", true, false) as Label).text])
			var who: Label = g.find_child("PlayerName", true, false)
			groups.append([str(g.name).trim_prefix("PlayerGroup_"), who.text if who else "", hon])
		_check(groups.size() == 2 and groups[0][0] == ids[0] and groups[1][0] == ids[2],
				"Your players' honours by player, the most decorated first, none from elsewhere (%s: %s)" % [tag, str(groups)])
		_check(groups.size() == 2 and groups[0][2] == ["Brownlow Medal %d" % year, "Copeland Trophy %d" % (year - 1)]
				and groups[1][2] == ["All-Australian %d" % year],
				"Each player's honours sit under him, newest first (%s)" % tag)
		_check(groups.size() == 2 and groups[0][1] == str(_state.award_name({"id": ids[0]})),
				"Each group is headed by the player's name (%s)" % tag)
		var gap: Label = s.find_child("AAUnrecorded", true, false)
		_check(gap != null and gap.text == "All-Australian selections weren't kept for %d in this save." % (year - 1),
				"An older season's missing All-Australians are said plainly (%s)" % tag)
		var rec: Label = s.find_child("RecordUnrecorded", true, false)
		_check(rec != null and rec.text.contains(str(year - 1)) and s.find_child("FinalsUnrecorded", true, false) == null,
				"A missing record is said plainly; a known Grand Final needs no such line (%s)" % tag)
		var row: Node = s.find_child("Season_%d" % year, true, false)
		_check(row != null and _row_text(row).contains("Premiers") and _row_text(row).contains("1st"),
				"Your premiership season reads 1st and Premiers (%s)" % tag)
		var old_row: Node = s.find_child("Season_%d" % (year - 1), true, false)
		_check(old_row != null and _row_text(old_row).contains("Runners-up"), "The older season reads Runners-up (%s)" % tag)
		# Everything fits the screen across.
		var fits := true
		for c in s.find_child("ClubTrophies", true, false).find_children("*", "Control", true, false):
			if (c as Control).is_visible_in_tree() and (c as Control).get_global_rect().end.x > sz.x + 1:
				fits = false
		_check(fits, "The trophy room fits across the screen (%s)" % tag)
		var mine: Node = s.find_child("PlayerGroup_" + str(ids[0]), true, false)
		var shelf: Node = mine.find_child("PlayerShelf", true, false) if mine != null else null
		var rows := {}
		for b in shelf.get_children() if shelf != null else []:
			rows[int((b as Control).position.y)] = true
		_check(shelf != null and rows.size() == 1, "A player's honours sit side by side under his name (%s: %d rows)" % [tag, rows.size()])
		# A finger on the flag opens it; Back closes it first, then leaves.
		if flag != null:
			_check((await Tap.tap(flag)) == "", "The premiership takes a tap (%s)" % tag)
			await _settle()
			var sheet: Node = s.find_child("ClubHonourSheet", true, false)
			var title: Label = sheet.find_child("SheetTitle", true, false) if sheet != null else null
			_check(title != null and title.text == "Premiers %d" % year, "Its sheet opens on the premiership (%s)" % tag)
			var inside := sheet != null
			if sheet != null:
				for c in sheet.find_children("*", "Control", true, false):
					if (c as Control).is_visible_in_tree() and (c as Control).get_global_rect().end.x > sz.x + 1:
						inside = false
			_check(inside, "The cup and flag fit the sheet across the screen (%s)" % tag)
			_check(s.call("handle_back"), "Back closes the sheet first (%s)" % tag)
			await _settle()
			_check(s.find_child("ClubHonourSheet", true, false) == null and s.call("handle_back"),
					"The sheet is gone, and the next Back closes the trophies (%s)" % tag)
			await _settle()
			_check(s.find_child("ClubTrophiesSheet", true, false) == null and not s.call("handle_back"),
					"The trophies are gone, and the next Back leaves (%s)" % tag)
		var medal: Button = s.find_child("Honour_brownlow_%d" % year, true, false)
		if medal != null:
			_check((await Tap.tap(medal)) == "", "The Brownlow takes a tap (%s)" % tag)
			await _settle()
			var line: Label = s.find_child("SheetLine_1", true, false)
			_check(line != null and line.text == "31 votes.", "The sheet gives the count with its unit (%s)" % tag)
			s.call("handle_back")
			await _settle()
		s.queue_free()
		await _settle()
	# The shipped file: the counts the public list gives, Fitzroy's apart on Brisbane's, Fremantle none.
	ClubHistory.reload()
	var real := {}
	for code in ["COL", "ESS", "CAR", "RIC", "HAW", "MEL", "GEE", "SYD", "BRL", "NTH", "WCE", "WBD", "ADE", "STK", "PAD", "FRE", "GCS", "GWS"]:
		real[code] = ClubHistory.before_career(code)
	var brl_also: Dictionary = real["BRL"]["also"]
	_check(real["COL"]["years"].size() == 16 and real["ESS"]["years"].size() == 16 and real["CAR"]["years"].size() == 16
			and real["RIC"]["years"].size() == 13 and real["GEE"]["years"].size() == 10 and real["SYD"]["years"].size() == 5
			and real["BRL"]["years"].size() == 6 and (brl_also.get("Fitzroy", []) as Array).size() == 8
			and real["WBD"]["years"].size() == 2 and real["STK"]["years"].size() == 1 and real["PAD"]["years"].size() == 1,
			"The shipped file gives each club its flags, Brisbane's own five and Fitzroy's eight apart")
	_check(real["FRE"]["known"] and real["FRE"]["years"].is_empty() and real["GCS"]["known"] and real["GWS"]["years"].is_empty(),
			"Fremantle, Gold Coast and GWS are on file as having none")
	# History cases: nothing on file shows nothing; confirmed none says so; a new club has none.
	ClubHistory.use({})
	s = await _open_trophies(Vector2i(390, 844))
	_check(s.find_child("ClubHistory", true, false) == null and s.find_child("YourPremierships", true, false) == null,
			"A club the file does not cover shows no history row (nothing guessed)")
	s.queue_free()
	await _settle()
	ClubHistory.use({"COL": {"years": [], "comps": {}, "none": true}})
	s = await _open_trophies(Vector2i(390, 844))
	var no_hist: Label = s.find_child("HistoryNone", true, false)
	_check(no_hist != null and no_hist.text == "No premierships yet.", "A club confirmed to have none says so plainly")
	s.queue_free()
	await _settle()
	_check(ClubHistory.before_career("TAS") == {"known": true, "years": [], "also": {}}
			and ClubHistory.before_career("CANB") == {"known": true, "years": [], "also": {}},
			"Tasmania and Canberra have no premierships before the career")
	var forged: Dictionary = root.get_node("GameDB").clubs["COL"].duplicate()
	forged["custom"] = true
	root.get_node("GameDB").clubs["ZZZ"] = forged
	ClubHistory.use({"ZZZ": {"years": [1999], "comps": {}, "none": false}})
	_check(ClubHistory.before_career("ZZZ") == {"known": true, "years": [], "also": {}},
			"A Club Forge club has none, whatever the file says")
	root.get_node("GameDB").clubs.erase("ZZZ")
	ClubHistory.use({"COL": {"years": hist_years, "comps": {}, "none": false}})
	# The filter: the kinds won, one at a time; your seasons stay.
	s = await _open_trophies(Vector2i(390, 844))
	var opt: OptionButton = s.find_child("AwardFilter", true, false)
	var listed := []
	for i in range(opt.item_count if opt != null else 0):
		listed.append(opt.get_item_text(i))
	_check(listed == ["All honours", "Premierships", "Minor premierships", "Brownlow Medal", "All-Australian", "Copeland Trophy"],
			"The filter lists only the kinds of honour won (%s)" % str(listed))
	_check(opt != null and (await Tap.tap(opt)) == "", "The filter takes a tap")
	await _settle()
	if opt != null:
		opt.get_popup().hide()
	await _pick_filter(s, 3)
	_check(s.find_child("ClubHonours", true, false) == null and s.find_children("PlayerGroup_*", "", true, false).size() == 1
			and s.find_child("Honour_brownlow_%d" % year, true, false) != null
			and s.find_child("Honour_my_bf_%d" % (year - 1), true, false) == null,
			"Brownlow Medal shows the Brownlow alone, under its winner")
	_check(s.find_child("Tenure", true, false) != null, "Your seasons stay, whatever the filter")
	await _pick_filter(s, 1)
	_check(s.find_child("PlayerHonours", true, false) == null and s.find_child("Club_premiership_%d" % year, true, false) != null
			and s.find_child("Club_minor_premiership_%d" % year, true, false) == null,
			"Premierships shows the flags alone")
	_check(s.find_child("ClubHistory", true, false) != null, "Premierships keeps the club's history with the flags")
	await _pick_filter(s, 2)
	_check(s.find_child("ClubHistory", true, false) == null, "Minor premierships leaves the history out")
	await _pick_filter(s, 0)
	_check(s.find_child("ClubHonours", true, false) != null and s.find_child("PlayerHonours", true, false) != null,
			"All honours brings everything back")
	s.queue_free()
	await _settle()
	# The room survives a save and load.
	var before := JSON.stringify(_state.honour_roll)
	_check(_state.save_career() and _state.load_career(), "The career saves and loads")
	_check(JSON.stringify(_state.honour_roll) == before, "The honour roll, new keys and all, survives a save and load")
	s = await _open_trophies(Vector2i(390, 844))
	_check(s.find_child("Club_premiership_%d" % year, true, false) != null, "The premiership is still on the shelf after loading")
	s.queue_free()
	ClubHistory.reload()
	await _settle()


## Choose the filter's option i, as its list would.
func _pick_filter(s: Node, i: int) -> void:
	var opt: OptionButton = s.find_child("AwardFilter", true, false)
	if opt == null:
		return
	opt.select(i)
	opt.item_selected.emit(i)
	await _settle()


func _row_text(n: Node) -> String:
	var out := ""
	for l in n.find_children("*", "Label", true, false):
		out += (l as Label).text + " "
	return out


func _settle() -> void:
	for i in range(4):
		await process_frame


func _check(ok: bool, what: String) -> void:
	_checks += 1
	if not ok:
		_failures.append(what)
		push_error(what)


## Readability roll-out, batch 1 (director, 2026-10-13: allegiance and sections
## at a glance): the fixture marks your match like the ladder's mine row, the
## clubs' names carry their colour, nothing is clipped, and the touched screens
## still take a real tap.

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
func _test_readability_b1() -> void:
	var uk = load("res://scripts/ui/UiKit.gd")
	var fix = load("res://scripts/ui/stats/StatsFixture.gd")
	var mine: String = _state.my_club
	for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
		var tag := "%dx%d" % [sz.x, sz.y]
		fix.reset()
		root.size = sz
		load("res://scripts/ui/StatsHubScene.gd").current = "fixture"
		var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
		root.add_child(s)
		await _settle()
		await Tap.tap(s.find_child("PrevRound", true, false))
		await _settle()
		var marked := 0
		var rows := s.find_children("Match_*", "Button", true, false)
		for r in rows:
			var sb := (r as Button).get_theme_stylebox("normal") as StyleBoxFlat
			if sb != null and sb.border_width_left == 4:
				marked += 1
		var face = load("res://scripts/ui/stats/StatsSide.gd").row_style(mine, false, true)
		_check(marked <= 1 and face.border_width_left == 4 and face.bg_color.a > 0.0,
				"At most your own match is marked, with the ladder's mine row face (%s: %d of %d)" % [tag, marked, rows.size()])
		_check(_clipped(s).is_empty(), "No fixture text is clipped (%s: %s)" % [tag, str(_clipped(s).slice(0, 3))])
		_check(not rows.is_empty() and (await Tap.tap(rows[0])) == "", "A fixture row takes a real tap (%s)" % tag)
		await _settle()
		_check(s.find_child("FixtureSheet", true, false) != null, "The tap opens the match (%s)" % tag)
		await _close(s)
		s = await _open_awards(sz)
		_check(_clipped(s).is_empty(), "No awards text is clipped (%s: %s)" % [tag, str(_clipped(s).slice(0, 3))])
		await _close(s)
		s = await _open_trophies(sz)
		_check(_clipped(s).is_empty(), "No trophy room text is clipped (%s: %s)" % [tag, str(_clipped(s).slice(0, 3))])
		var head: Label = s.find_child("Title", true, false)
		_check(head != null and head.get_theme_color("font_color") == load("res://scripts/ui/stats/StatsSide.gd").mine_ink(),
				"A trophy room section heading carries your colour where it reads (%s)" % tag)
		await _close(s)
	# The season review and its awards night, by finger.
	if _state.season != null and _state.season.is_season_over() and not _state.season_awards.is_empty():
		_state.season_awards["presentation_seen"] = false
		var rv: Control = load("res://scenes/SeasonReviewScene.tscn").instantiate()
		root.add_child(rv)
		await _settle()
		var next: Button = rv.find_child("AwardsNext", true, false)
		_check(next != null and (await Tap.tap(next)) == "", "Reveal results takes a real tap")
		await _settle()
		var skip: Button = rv.find_child("AwardsSkip", true, false)
		_check(skip != null and (await Tap.tap(skip)) == "", "Skip to season review takes a real tap")
		await _settle()
		_check(rv.find_child("SeasonAwards", true, false) == null, "The awards night closes on Skip")
		_check(_clipped(rv).is_empty(), "No season review text is clipped: %s" % str(_clipped(rv).slice(0, 3)))
		rv.queue_free()
		await _settle()
	else:
		for i in 4:
			_check(true, "SKIP: the season is not over here, the review is captured instead")


## Labels that are set on one line and wider than the room they have.
func _clipped(root_node: Node) -> Array:
	var out := []
	for n in root_node.find_children("*", "Label", true, false):
		var l := n as Label
		if not l.is_visible_in_tree() or l.text == "" or l.autowrap_mode != TextServer.AUTOWRAP_OFF 				or l.text_overrun_behavior != TextServer.OVERRUN_NO_TRIMMING:
			continue   # wrapped, or trimmed on purpose (a venue, a long name)
		if l.size.x > 0.0 and not _label_fits(l):
			out.append("%s \"%s\"" % [l.name, l.text.left(24)])
	return out
