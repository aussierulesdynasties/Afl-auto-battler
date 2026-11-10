extends SceneTree
## godot --headless --path . --script tests/run_nav_economy_tests.gd
## Navigation economy (row T3.R43, director bible 43: bundle 6 "Fewer taps,
## nothing hidden").
##   Two taps (P-60): each weekly fact (ladder, fixture, bio, draft order, board
##   goal, calls at the last break, cap) is at most two real taps from the hub
##   on a phone. Each fact's way in is a path of taps in FACTS; a path longer
##   than MAX_TAPS fails, and so does one whose taps don't land or don't show
##   the fact.
##   Overflow (P-77): every screen at phone size (360x740) and each text size,
##   no words run past the screen's edge.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 2031
const CLUB := "MEL"
const PHONE := Vector2i(360, 740)
const MAX_TAPS := 2

## [fact, [taps from the hub], the node that shows it]. A tap names a node, or
## "text:<words>" for a button found by its words, or "first:<parent>" for the
## first button inside <parent> (a player on the list's board).
const FACTS := [
	["ladder", [], "LadderSection"],
	["fixture", ["SeasonStats", "Section_fixture"], "StatsFixture"],
	["bio", ["text:My list", "first:Best22Board"], "PlayerProfile"],
	["draft order", [], "DraftPickLine"],
	["board goal", ["HubCoaching"], "Board"],
	["calls at the last break", ["ReviewLastMatch"], "FullTimeCalls"],
	["cap", ["HubCoaching"], "CapLine"],
]

var _checks := 0
var _failures: Array = []
var _gs: Node
var _router: Node
var UK


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 6) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	await process_frame
	_gs = root.get_node("GameState")
	_router = root.get_node("Router")
	UK = load("res://scripts/ui/UiKit.gd")
	_gs.autosave_enabled = false
	_gs.event_sheets = false
	_gs.save_path = "user://test_nav_economy.save"
	_gs.settings_path = "user://test_nav_economy.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(_gs.settings_path))
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_gs.set_setting("seen_%s_intro" % key, true)
	_gs.set_setting("seen_season_stats_intro", true)
	root.size = PHONE
	_late_season_career()
	await _t("_test_paths_are_short")
	await _t("_test_two_taps")
	await _t("_test_overflow")
	UK.apply_text_size("standard")
	_router.stack = []
	print(Ran.line("Nav economy", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(0 if _failures.is_empty() else 1)


## A Melbourne career late in the home and away (the draft pick line shows
## from six rounds out), with the last match coached live so its calls exist.
func _late_season_career() -> void:
	_gs.reset()
	_gs.career_seed = SUITE_SEED
	_gs.replay_seed = SUITE_SEED
	_gs.start_season(CLUB, root.get_node("GameDB").club_list(CLUB))
	_gs.set_setting("seen_weekly_loop_intro", true)
	var target: int = _gs.season.fixture.size() - 5
	var guard := 0
	while _gs.season.round_index < target - 1 and guard < 40:
		guard += 1
		_gs.skip_media_conference()
		_gs.advance()
	# The last week before the hub: a match coached live, played out.
	guard = 0
	while guard < 4 and not _gs.prepare_interactive_match():
		guard += 1
		_gs.advance()
	if _gs.pending_sim != null:
		var sim = _gs.pending_sim
		var res := {}
		while sim.current_quarter <= 4:
			res = sim.run_quarter()
		res["home"] = _gs.pending_match["home"]
		res["away"] = _gs.pending_match["away"]
		res["label"] = _gs.pending_match["label"]
		_gs.finish_interactive_match(res)
	_gs.skip_media_conference()


## The table itself: no fact sits more than two taps from the hub.
func _test_paths_are_short() -> void:
	_check(FACTS.size() == 7, "seven weekly facts (%d)" % FACTS.size())
	for f in FACTS:
		_check((f[1] as Array).size() <= MAX_TAPS, "%s is %d taps from the hub (at most %d)" % [f[0], (f[1] as Array).size(), MAX_TAPS])


func _hub() -> void:
	_router.stack = []
	_router.go("hub")
	await _settle(12)


func _find_tap(step: String) -> Control:
	var scene := current_scene
	if scene == null:
		return null
	if step.begins_with("text:"):
		var words := step.substr(5)
		for b in scene.find_children("*", "BaseButton", true, false):
			if b is Button and (b as Button).text == words and (b as Control).is_visible_in_tree():
				return b
		return null
	if step.begins_with("first:"):
		var parent := scene.find_child(step.substr(6), true, false)
		if parent == null:
			return null
		for b in parent.find_children("*", "BaseButton", true, false):
			if (b as Control).is_visible_in_tree():
				return b
		return null
	return scene.find_child(step, true, false) as Control


## Each fact, walked with real taps on a phone from a fresh hub.
func _test_two_taps() -> void:
	_check(_gs.season.round_index >= _gs.season.fixture.size() - 6,
			"late in the home and away (round %d of %d)" % [_gs.season.round_index, _gs.season.fixture.size()])
	for f in FACTS:
		var fact := str(f[0])
		await _hub()
		_check(_router.current() == "hub", "%s: the walk starts on the hub (on %s)" % [fact, _router.current()])
		var ok := true
		for step in f[1]:
			var c := _find_tap(str(step))
			if c == null:
				_check(false, "%s: no %s to tap on %s" % [fact, step, _router.current()])
				ok = false
				break
			var why: String = await Tap.tap(c)
			_check(why == "", "%s: a tap on %s lands (%s)" % [fact, step, why])
			if why != "":
				ok = false
				break
			await _settle(10)
		if not ok:
			continue
		var shown := current_scene.find_child(str(f[2]), true, false) as Control if current_scene != null else null
		_check(shown != null and shown.is_visible_in_tree(), "%s: %s shows after %d tap(s) (on %s)" % [fact, f[2], (f[1] as Array).size(), _router.current()])
	await _hub()


## The screens a coach reaches in the season, walked at phone size: [router
## key, a tab to open first or ""].
const SCREENS := [
	["hub", ""], ["selection", ""], ["training", ""], ["list", ""], ["list", "ListTabFull"],
	["coaching", ""], ["staff", ""], ["almanac", ""],
	["stats", "Section_ladder"], ["stats", "Section_players"], ["stats", "Section_ratings"],
	["stats", "Section_awards"], ["stats", "Section_fixture"],
	["main", ""],
]


## A control with words whose drawn part runs past the screen's edge: nothing
## that clips it (a scroll, a clipped panel) holds it in.
func _overflows(scene: Node, win: Vector2) -> Array:
	var out: Array = []
	for n in scene.find_children("*", "Control", true, false):
		var c := n as Control
		if not c.is_visible_in_tree():
			continue
		var words := ""
		if c is Label:
			words = (c as Label).text
		elif c is Button:
			words = (c as Button).text
		elif c is RichTextLabel:
			words = (c as RichTextLabel).get_parsed_text()
		if words.strip_edges() == "":
			continue
		var r := c.get_global_rect()
		var p := c.get_parent()
		while p != null and r.size.x > 0.0:
			if p is Control and ((p as Control).clip_contents or p is ScrollContainer):
				r = r.intersection((p as Control).get_global_rect())
			p = p.get_parent()
		if r.size.x <= 0.0:
			continue
		if r.position.x < -1.0 or r.end.x > win.x + 1.0:
			out.append("%s %s \"%s\" x %.0f..%.0f" % [c.get_class(), c.name, words.strip_edges().left(24), r.position.x, r.end.x])
	return out


func _test_overflow() -> void:
	root.size = PHONE
	var win := Vector2(PHONE)
	_check(UK.TEXT_SIZES.size() == 3, "three text sizes (%d)" % UK.TEXT_SIZES.size())
	for row in UK.TEXT_SIZES:
		var size_key := str(row[0])
		_gs.set_text_size(size_key)
		for s in SCREENS:
			var key := str(s[0])
			_router.stack = []
			_router.go(key)
			await _settle(10)
			var tag := "%s%s at %s" % [key, "" if str(s[1]) == "" else " " + str(s[1]), size_key]
			_check(current_scene != null and _router.current() == key, "%s opens (on %s)" % [tag, _router.current()])
			if current_scene == null:
				continue
			if str(s[1]) != "":
				var tab := current_scene.find_child(str(s[1]), true, false) as Control
				_check(tab != null, "%s: the tab is there" % tag)
				if tab == null:
					continue
				var why: String = await Tap.tap(tab)
				_check(why == "", "%s: a tap on the tab lands (%s)" % [tag, why])
				await _settle(10)
			var over := _overflows(current_scene, win)
			_check(over.is_empty(), "%s: words past the screen's edge: %s" % [tag, "; ".join(over.slice(0, 8))])
	_gs.set_text_size("standard")
