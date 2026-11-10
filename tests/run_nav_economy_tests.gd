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

## [fact, [taps from the hub], the node that shows it ("A|B": either)]. A tap names a node, or
## "text:<words>" for a button found by its words, or "first:<parent>" for the
## first button inside <parent> (a player on the list's board).
const FACTS := [
	["ladder", [], "LadderSection"],
	["fixture", ["SeasonStats", "Section_fixture"], "StatsFixture"],
	["bio", ["text:My list", "first:Best22Board"], "PlayerProfile"],
	["draft order", [], "DraftPickLine"],
	["board goal", ["HubCoaching"], "Board"],
	# A call the Why section already quoted is not said again under Your calls.
	["calls at the last break", ["ReviewLastMatch"], "FullTimeCalls|WhyReasons"],
	["cap", ["HubCoaching"], "CapLine"],
]

var _checks := 0
var _failures: Array = []
var _gs: Node
var _router: Node
var UK
var FW
var WP


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
	FW = load("res://scripts/ui/FootballWords.gd")
	WP = load("res://scripts/ui/WordPress.gd")
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
	_t("_test_word_source")
	await _t("_test_long_press_label")
	await _t("_test_long_press_button")
	_t("_test_search_finds")
	await _t("_test_search_taps")
	await _t("_test_sim_orders")
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
		var me := 0 if str(_gs.pending_match["home"]) == _gs.my_club else 1
		while sim.current_quarter <= 4:
			# A call at the last break, so the review has one to show.
			if sim.current_quarter == 4:
				var t: Dictionary = (sim.tactics[me] as Dictionary).duplicate()
				t["gameplan"] = "attacking"
				sim.set_tactics(me, t)
			res = sim.run_quarter()
		res["home"] = _gs.pending_match["home"]
		res["away"] = _gs.pending_match["away"]
		res["label"] = _gs.pending_match["label"]
		_gs.finish_interactive_match(res)
	_gs.skip_media_conference()
	# The week's one-off asks (the under-18 carnival) are seen already: the
	# walk starts on a clear hub.
	load("res://scripts/state/MidseasonDraft.gd").close_carnival(_gs)


## The table itself: no fact sits more than two taps from the hub.
func _test_paths_are_short() -> void:
	_check(FACTS.size() == 7, "seven weekly facts (%d)" % FACTS.size())
	for f in FACTS:
		_check((f[1] as Array).size() <= MAX_TAPS, "%s is %d taps from the hub (at most %d)" % [f[0], (f[1] as Array).size(), MAX_TAPS])


func _hub() -> void:
	_router.stack = []
	_router.go("hub")
	await _settle(12)
	# Nothing may sit over the hub when a walk starts.
	for c in current_scene.get_children():
		if c is Control and (c as Control).visible and str(c.name) in ["CarnivalWeek", "MidseasonDraft", "BackingTalk", "EventSheet", "TrainingReport"]:
			_check(false, "the hub opens under %s" % c.name)


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
		var seen := false
		for want in str(f[2]).split("|"):
			var shown := current_scene.find_child(want, true, false) as Control if current_scene != null else null
			if shown != null and shown.is_visible_in_tree():
				seen = true
				if want == "WhyReasons":
					# Only when the reasons quote the call itself.
					var lm2: Dictionary = _gs.last_match
					var st: Dictionary = load("res://scripts/sim/MatchStory.gd").build(lm2,
							0 if str(lm2.get("home", "")) == _gs.my_club else 1)
					var quoted := false
					for r in st.get("reasons", []):
						quoted = quoted or str((r as Dictionary).get("call", "")) != ""
					_check(quoted, "%s: Why quotes the call" % fact)
				break
		_check(seen, "%s: %s shows after %d tap(s) (on %s)" % [fact, f[2], (f[1] as Array).size(), _router.current()])
		if not seen and current_scene != null:
			# What the screen did build, to say why without another run.
			var names: Array = []
			for n in current_scene.find_children("FullTime*", "", true, false):
				names.append("%s%s" % [n.name, "" if (n as CanvasItem).is_visible_in_tree() else "(hidden)"])
			var lm: Dictionary = _gs.last_match
			var side := 0 if str(lm.get("home", "")) == _gs.my_club else 1
			var MN = load("res://scripts/ui/match/MatchNotes.gd")
			var lines := 0
			for q in range(1, 5):
				lines += (MN.calls_lines(lm, side, q) as Array).size()
			print("  DEBUG %s: built %s; last_match hist %d, snaps %d, call lines %d" % [fact, str(names),
					(lm.get("tactics_history", []) as Array).size(), (lm.get("quarter_teams", []) as Array).size(), lines])
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
			out.append("%s %s \"%s\" x %.0f..%.0f%s" % [c.get_class(), c.name, words.strip_edges().left(24), r.position.x, r.end.x, _widest(c, win)])
	return out


## A thumb needs MIN_TARGET px (bible 86, P-77): every button that takes a
## tap is at least that tall.
const MIN_TARGET := 44


func _small_targets(scene: Node) -> Array:
	var out: Array = []
	for n in scene.find_children("*", "BaseButton", true, false):
		var b := n as BaseButton
		if not b.is_visible_in_tree() or b.disabled or b.mouse_filter == Control.MOUSE_FILTER_IGNORE:
			continue
		if b.size.y < MIN_TARGET - 0.5:
			var words: String = (b as Button).text if b is Button else ""
			out.append("%s \"%s\" %.0f px" % [b.name, words.strip_edges().left(20), b.size.y])
	return out


## Which parent asks for more width than the screen has: the cause to fix.
func _widest(c: Control, win: Vector2) -> String:
	# Each ancestor's own minimum width, leaf first, and the first one over the
	# screen: the jump between two links names the control that widens it.
	var n: Node = c
	var cause := ""
	var chain: Array = []
	while n != null and n is Control:
		var w := (n as Control).get_combined_minimum_size().x
		chain.append("%s:%.0f" % [n.name if not str(n.name).begins_with("@") else n.get_class(), w])
		if w > win.x + 1.0 and cause == "":
			cause = " (%s needs %.0f px)" % [n.name, w]
		n = n.get_parent()
	if cause != "":
		cause += " [" + " < ".join(chain.slice(0, 12)) + "]"
		# And down from the screen's page: the widest child at each level.
		var down: Array = []
		var d: Node = current_scene
		while d != null and down.size() < 16:
			var best: Control = null
			for k in d.get_children():
				if k is Control and (k as Control).visible and (best == null or (k as Control).get_combined_minimum_size().x > best.get_combined_minimum_size().x):
					best = k
			if best == null:
				break
			down.append("%s:%.0f" % [best.name if not str(best.name).begins_with("@") else best.get_class(), best.get_combined_minimum_size().x])
			d = best
		cause += " {" + " > ".join(down) + "}"
	return cause


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
			var small := _small_targets(current_scene)
			_check(small.is_empty(), "%s: targets under %d px: %s" % [tag, MIN_TARGET, "; ".join(small.slice(0, 8))])
	_gs.set_text_size("standard")


# ---------------------------------------------------------------------------
# Long-press a football word for its rule (P-61)
# ---------------------------------------------------------------------------

## One source: a rated stat says what the stat guide says, a plan what the
## coach box says, a pep talk what the break says; every trait is a word.
func _test_word_source() -> void:
	var all: Dictionary = FW.entries()
	var SG = load("res://scripts/ui/StatGuide.gd")
	var CR = load("res://scripts/sim/CoachReport.gd")
	var TL = load("res://scripts/ui/TraitLink.gd")
	_check(_gs.TRAIN_STATS.size() == 13, "13 rated stats (%d)" % _gs.TRAIN_STATS.size())
	for row in _gs.TRAIN_STATS:
		var e: Dictionary = all.get(str(row[1]), {})
		_check(not e.is_empty() and str(e["lines"][0]) == SG.short(str(row[0])), "%s reads the stat guide's line" % row[1])
	for k in CR.PLAN_NAMES:
		var e: Dictionary = all.get(str(CR.PLAN_NAMES[k]), {})
		_check(not e.is_empty() and str(e["lines"][0]) == str(CR.PLAN_PARTS[k]["does"]), "%s reads the plan's own words" % CR.PLAN_NAMES[k])
	for k in CR.PEP_NAMES:
		var e: Dictionary = all.get(str(CR.PEP_NAMES[k]), {})
		_check(not e.is_empty() and str(e["lines"][0]) == str(CR.PEP_EFFECTS[k]), "%s reads the pep talk's effect" % CR.PEP_NAMES[k])
	var tn: Dictionary = TL.names()
	_check(tn.size() >= 10, "traits and synergies are words (%d)" % tn.size())
	for shown in tn:
		_check(str((all.get(str(shown), {}) as Dictionary).get("trait", "")) == str(tn[shown]), "%s opens its trait sheet" % shown)
	for t in SG.TOPICS:
		_check(all.has(str(t[0])), "the guide's topic %s is a word" % t[0])
	_check(all.has("OVR") and all.has("POT") and not all.has("XP"), "OVR and POT are words; XP is not said on the screens")
	# Words in a line: whole words, longest first, in reading order.
	var found: Array = FW.find_in("A Defensive Press asks for pressure; impressive.")
	_check(found == ["Defensive Press", "Pressure"], "words in a line (%s)" % str(found))
	_check(FW.word_at("Go with Attack Corridor now", 12) == "Attack Corridor", "the word under a letter")
	_check(FW.word_at("Go with Attack Corridor now", 2) == "", "no word under a plain letter")


## The first visible label on the screen holding a football word, and the
## middle of that word's first letters, in the label's own pixels.
func _word_label(scene: Node) -> Array:
	for n in scene.find_children("*", "Label", true, false):
		var l := n as Label
		if not l.is_visible_in_tree() or l.get_global_rect().end.y > PHONE.y or l.get_global_rect().position.y < 0:
			continue
		var words: Array = FW.find_in(l.text)
		if words.is_empty():
			continue
		var at := l.text.to_lower().find(str(words[0]).to_lower())
		var r: Rect2 = l.get_character_bounds(at + 1)
		if r.size.x <= 0.0:
			continue
		return [l, r.get_center(), str(words[0])]
	return []


func _rule_sheet() -> Control:
	var s := current_scene.find_child(FW.SHEET_NAME, true, false) as Control
	if s == null:
		s = current_scene.find_child("TraitInfo", true, false) as Control
	if s != null and s.is_queued_for_deletion():
		return null
	return s


## A finger held still on a word in a line opens its rule; Back closes it and
## leaves the screen as it was; a quick tap opens nothing.
func _test_long_press_label() -> void:
	root.size = PHONE
	_gs.set_text_size("standard")
	var hit: Array = []
	for key in ["coaching", "selection", "hub", "training"]:
		_router.stack = []
		_router.go(key)
		await _settle(12)
		hit = _word_label(current_scene)
		if not hit.is_empty():
			break
	_check(not hit.is_empty(), "a screen shows a football word in a line")
	if hit.is_empty():
		return
	var on: String = _router.current()
	var why: String = await Tap.hold_at(hit[0], hit[1], WP.HOLD_SECONDS + 0.2)
	_check(why == "", "the hold lands on %s (%s)" % [hit[2], why])
	await _settle(4)
	var sheet := _rule_sheet()
	_check(sheet != null and sheet.is_visible_in_tree(), "%s on %s: holding it opens its rule" % [hit[2], on])
	if sheet != null and sheet.name == FW.SHEET_NAME:
		var title := sheet.find_child("WordTitle_0", true, false) as Label
		_check(title != null and title.text == str(FW.entries()[hit[2]]["title"]), "the sheet is %s's (%s)" % [hit[2], title.text if title else "none"])
		_check(sheet.find_child("WordRule_0_0", true, false) != null, "the sheet says the rule")
		_check(sheet.find_child("WordClose", true, false) != null, "the sheet has Close")
	_router.handle_back()
	await _settle(4)
	_check(_rule_sheet() == null, "Back closes the rule")
	_check(_router.current() == on, "Back closes only the rule (on %s)" % _router.current())
	if not is_instance_valid(hit[0]):
		hit = _word_label(current_scene)
	if hit.is_empty():
		_check(false, "the word is still on the screen after Back")
		return
	await Tap.tap_at(hit[0], hit[1], false)
	await _settle(4)
	_check(_rule_sheet() == null, "a quick tap on a word opens no rule")


## A held button with a football word opens the rule and does not act; a
## control with its own long press (Training's bulk pick) is left alone.
func _test_long_press_button() -> void:
	root.size = PHONE
	var target: Button = null
	for key in ["coaching", "selection", "hub"]:
		_router.stack = []
		_router.go(key)
		await _settle(12)
		for n in current_scene.find_children("*", "Button", true, false):
			var b := n as Button
			if b.is_visible_in_tree() and not b.disabled and not FW.find_in(b.text).is_empty() \
					and b.get_global_rect().end.y < PHONE.y and b.get_global_rect().position.y > 0:
				target = b
				break
		if target != null:
			break
	_check(target != null, "a screen has a button with a football word")
	if target != null:
		var acted := [false]
		target.pressed.connect(func(): acted[0] = true)
		var on: String = _router.current()
		var words := target.text
		var why: String = await Tap.hold_at(target, target.size * 0.5, WP.HOLD_SECONDS + 0.2)
		_check(why == "", "the hold lands on %s (%s)" % [words, why])
		await _settle(4)
		_check(_rule_sheet() != null, "holding \"%s\" on %s opens its rule" % [words, on])
		_check(not acted[0], "holding \"%s\" does not press it" % words)
		_router.handle_back()
		await _settle(4)
	# Training's rows keep their own hold.
	_router.stack = []
	_router.go("training")
	await _settle(12)
	var own := 0
	for n in current_scene.find_children("*", "BaseButton", true, false):
		if n.has_meta(WP.OWN_HOLD):
			own += 1
	_check(own > 0, "Training's player rows keep their own long press (%d)" % own)


# ---------------------------------------------------------------------------
# Search any player or club from the hub; shortlist by long-press (P-65)
# ---------------------------------------------------------------------------

## Names match whole clubs and any listed player, clubs first.
func _test_search_finds() -> void:
	var HS = load("res://scripts/ui/HubSearch.gd")
	var CL = load("res://scripts/ui/ClubLink.gd")
	var found: Array = HS.matches("Melb")
	_check(not found.is_empty() and str(found[0]) == CL.SCHEME + "MEL", "\"Melb\" finds Melbourne first (%s)" % str(found.slice(0, 3)))
	_check((HS.matches("M") as Array).is_empty(), "one letter searches nothing")
	_check(_gs.season.lists.size() >= 18, "every club's list is searched (%d)" % _gs.season.lists.size())
	var hits := 0
	for code in ["GEE", "SYD", "FRE"]:
		var p: Dictionary = _gs.season.lists[code][3]
		var surname := str(p["name"]).get_slice(" ", str(p["name"]).get_slice_count(" ") - 1)
		var ids: Array = HS.matches(surname)
		if ids.has(str(p["id"])):
			hits += 1
		else:
			_check(false, "%s finds %s of %s (%s)" % [surname, p["name"], code, str(ids.slice(0, 5))])
	_check(hits == 3, "a surname finds the player at any club (%d of 3)" % hits)
	_check(str(HS.describe(CL.SCHEME + "FRE")[0]) == "Fremantle", "a club row says the club")


func _search_sheet() -> Control:
	var s := current_scene.find_child("HubSearch", true, false) as Control
	return null if s == null or s.is_queued_for_deletion() else s


## Real taps: the hub's Search opens the sheet; a tap on a name opens his
## profile over it; Back closes the profile, then the sheet; a held name goes
## on the shortlist, shows on the empty field, and a second hold takes it off.
func _test_search_taps() -> void:
	root.size = PHONE
	_gs.set_text_size("standard")
	_gs.shortlist = []
	await _hub()
	var why: String = await Tap.tap(current_scene.find_child("HubSearchOpen", true, false))
	_check(why == "", "the tap on Search lands (%s)" % why)
	await _settle(4)
	var sheet := _search_sheet()
	_check(sheet != null and sheet.is_visible_in_tree(), "Search opens one sheet from the hub")
	if sheet == null:
		return
	_check(sheet.find_child("ShortlistEmpty", true, false) != null, "an empty shortlist says how to fill it")
	var p: Dictionary = _gs.season.lists["SYD"][2]
	var id := str(p["id"])
	var field := sheet.find_child("SearchField", true, false) as LineEdit
	field.text = str(p["name"])
	field.text_changed.emit(field.text)
	await _settle(3)
	var row := sheet.find_child("Result_" + id, true, false) as Button
	_check(row != null, "typing his name lists %s" % p["name"])
	if row == null:
		return
	# Seen, not just built: the name is drawn on one line across the row.
	var nm := row.find_child("Name", true, false) as Label
	_check(nm != null and nm.size.x >= 120.0 and nm.size.y <= row.size.y and row.size.x >= 240.0,
			"his row shows his name on one line (name %s, row %s)" % [str(nm.size) if nm else "none", str(row.size)])
	why = await Tap.tap(row)
	_check(why == "", "the tap on his name lands (%s)" % why)
	await _settle(4)
	var prof := current_scene.find_child("PlayerProfile", true, false) as Control
	_check(prof != null and prof.is_visible_in_tree(), "a tap on a name opens his profile")
	_router.handle_back()
	await _settle(4)
	_check(_search_sheet() != null and _router.current() == "hub", "Back closes the profile and keeps the search")
	row = _search_sheet().find_child("Result_" + id, true, false) as Button
	why = await Tap.hold_at(row, row.size * 0.5, WP.HOLD_SECONDS + 0.2)
	await _settle(4)
	_check(why == "" and _gs.shortlist.has(id), "holding his name puts him on the shortlist (%s)" % why)
	_check(current_scene.find_child("PlayerProfile", true, false) == null, "the hold opens no profile")
	_check(current_scene.find_child(FW.SHEET_NAME, true, false) == null, "the hold opens no word rule")
	var kept := row.find_child("Kept", true, false) as Label
	_check(kept != null and kept.visible, "his row says Kept")
	field.text = ""
	field.text_changed.emit("")
	await _settle(3)
	row = _search_sheet().find_child("Result_" + id, true, false) as Button
	_check(row != null, "the empty field shows the shortlist with him on it")
	# A club is kept the same way, and its row opens the club's page.
	field.text = "Fremantle"
	field.text_changed.emit(field.text)
	await _settle(3)
	var club := _search_sheet().find_child("Result_club_FRE", true, false) as Button
	_check(club != null, "typing a club lists it")
	if club != null:
		why = await Tap.tap(club)
		await _settle(4)
		_check(why == "" and current_scene.find_child("ClubPage", true, false) != null, "a tap on a club opens its page (%s)" % why)
		_router.handle_back()
		await _settle(4)
	field.text = ""
	field.text_changed.emit("")
	await _settle(3)
	row = _search_sheet().find_child("Result_" + id, true, false) as Button
	if row != null:
		why = await Tap.hold_at(row, row.size * 0.5, WP.HOLD_SECONDS + 0.2)
		await _settle(4)
	_check(not _gs.shortlist.has(id), "a second hold takes him off")
	_router.handle_back()
	await _settle(4)
	_check(_search_sheet() == null and _router.current() == "hub", "Back closes the search and stays on the hub")
	# The shortlist is the career's: it is saved with it.
	_gs.toggle_shortlist(id)
	var saved: Dictionary = _gs._save_state()
	_check((saved.get("shortlist", []) as Array).has(id), "the shortlist is saved with the career")
	_gs.shortlist = []


# ---------------------------------------------------------------------------
# "When I sim the week": standing orders, saved and followed (P-66)
# ---------------------------------------------------------------------------

## Real taps: Coaching > Set the lines opens the sheet; a tap sets a line and
## it is saved; a waiting card stops Sim the week when the line says ask me;
## the other lines answer the card and send the assistant to the press.
## Runs last: it plays rounds.
func _test_sim_orders() -> void:
	root.size = PHONE
	_gs.set_text_size("standard")
	_gs.sim_orders = {}
	_check(_gs.sim_order("youth") == "form" and _gs.sim_order("questions") == "usual" and _gs.sim_order("press") == "me",
			"the lines start on what Sim the week has always done")
	await _hub()
	var why: String = await Tap.tap(current_scene.find_child("HubCoaching", true, false))
	await _settle(10)
	var open := current_scene.find_child("SimOrdersOpen", true, false) as Button
	_check(why == "" and open != null, "Coaching has the standing orders (%s)" % why)
	if open == null:
		return
	why = await Tap.tap(open)
	await _settle(4)
	var sheet := current_scene.find_child("SimOrders", true, false) as Control
	_check(why == "" and sheet != null and sheet.is_visible_in_tree(), "Set the lines opens the sheet (%s)" % why)
	if sheet == null:
		return
	for k in ["youth", "questions", "press"]:
		_check(sheet.find_child("SimOrderOptions_" + k, true, false) != null, "the sheet has the %s line" % k)
	why = await Tap.tap(sheet.find_child("SimOrder_questions_ask", true, false))
	await _settle(2)
	var why2: String = await Tap.tap(sheet.find_child("SimOrder_press_assistant", true, false))
	await _settle(2)
	_check(why == "" and why2 == "" and _gs.sim_order("questions") == "ask" and _gs.sim_order("press") == "assistant",
			"a tap sets a line (%s, %s)" % [why, why2])
	var saved: Dictionary = _gs._save_state()
	_check(str((saved.get("sim_orders", {}) as Dictionary).get("questions", "")) == "ask", "the lines are saved with the career")
	_router.handle_back()
	await _settle(6)
	_check(current_scene.find_child("SimOrders", true, false) == null and _router.current() == "coaching", "Back closes the sheet")
	var line := current_scene.find_child("SimOrderLine_1", true, false) as Label
	_check(line != null and line.text.contains("Ask me"), "Coaching says the line as set (%s)" % (line.text if line else "none"))
	# Followed: a waiting card stops Sim the week, and nothing is played.
	var card: Dictionary = _gs.story_card("training_extra_session")
	_check(not card.is_empty(), "a week card to wait on")
	card["popped"] = true
	_gs.week_events = [card]
	await _hub()
	var before: int = _gs.season.round_index
	var sim := current_scene.find_child("SimRound", true, false) as Button
	_check(sim != null, "the hub has Sim the week")
	if sim != null:
		why = await Tap.tap(sim)
		await _settle(6)
		_check(why == "" and _gs.season.round_index == before, "Sim the week stops for the card: no round played (%s)" % why)
		var stop := current_scene.find_child("SimStopped", true, false) as Control
		_check(stop != null and stop.is_visible_in_tree(), "the card opens and says why the week waits")
	_router.handle_back()
	await _settle(4)
	_gs.resolve_card(0, 0)
	_check(_gs.sim_week_stops().is_empty(), "an answered card stops nothing")
	_gs.sim_week()
	_check(_gs.season.round_index == before + 1, "then the week is played (%d)" % _gs.season.round_index)
	_check(not _gs.media_conference_pending(), "the assistant fronted the press")
	# Back the players: the card is answered that way, with no stop.
	_gs.set_sim_order("questions", "players")
	var card2: Dictionary = _gs.story_card("members_open_training")
	card2["popped"] = true
	_gs.week_events = [card2]
	_check(_gs.sim_week_stops().is_empty(), "with a line for the cards, nothing stops")
	var want: int = load("res://scripts/sim/SkipOrders.gd").card_choice(card2, "players")
	_gs.sim_week()
	_check(bool(card2.get("resolved", false)) and int(card2.get("choice", -2)) == want,
			"the card is answered the way the line says (%d, wanted %d)" % [int(card2.get("choice", -2)), want])
	_gs.sim_orders = {}
	_gs.week_events = []
