extends SceneTree
const Ovr := preload("res://tests/ovr.gd")
## godot --headless --path . --script tests/run_merger_cut_tests.gd
## After the Fitzroy merger your list is over the era's spots and you pick who
## goes (director 2026-11-15: "I pick, delist screen"): the count each list kind
## must lose, the refusals, the club's own cut if Round 1 comes first, the flag
## in the save, the hub opening the screen, and the screen worked with real taps
## (tests/tap.gd) on a phone in portrait, 390x844. The setup is the real 1997
## rollover in small: the Bears' list cut to the era's spots by the rivals' rule,
## then LegacyRollover._merge brings Fitzroy's best across. The same screen
## opens whenever a Legacy season has fewer spots than your list (director
## 2026-11-25, "You pick"): 1994's cut from 52 to 42, and an opening list longer
## than its first season allows.
## Classes are reached through load() and autoload nodes (a --script runner
## compiles before the autoloads exist).

var _gs: Node
var _db: Node
var _router: Node
var _checks := 0
var _failures: Array[String] = []

const Tap := preload("res://tests/tap.gd")
const PHONE := Vector2i(390, 844)
## The 1997 rollover is seeded, so each run is the same.
const SUITE_SEED := 1997


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


func _settle(n := 6) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	await process_frame
	_gs = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_router = root.get_node("Router")
	_gs.autosave_enabled = false
	_gs.save_path = "user://test_merger_cut.save"
	_gs.settings_path = "user://test_merger_cut.cfg"
	_gs.replay_seed = SUITE_SEED
	root.size = PHONE
	_t("_test_needs")
	_t("_test_refusals")
	_t("_test_club_cut_before_round_one")
	_t("_test_saved")
	await _t("_test_screen_taps")
	_t("_test_list_cut_any_year")
	_t("_test_opening_list_cut")
	await _t("_test_list_cut_screen_taps")
	# A PC (UI batch 5): the whole list across the window and his card beside it.
	for sz in [Vector2i(1280, 720), Vector2i(960, 540)]:
		await _t("_test_merger_pc", [sz])
	root.size = PHONE
	_db.reload()
	print(Ran.line("Merger cut", self))
	quit(1 if not _failures.is_empty() else 0)


## The Brisbane Bears at the 1997 rollover: their list at the era's spots, then
## Fitzroy's best across with the merger, and the cut due.
func _setup() -> void:
	var LegacyRollover = load("res://scripts/state/LegacyRollover.gd")
	_gs.reset("1990")
	_gs.begin_real_lists()
	_gs.choose_real_club("BRL")
	_gs.finish_intake_draft()
	_gs.set_setting("seen_weekly_loop_intro", true)
	_gs.media_conference = {}
	_gs.legacy = {"fitzroy": "merged"}
	_gs.season_year = LegacyRollover.TALKS_YEAR + 1
	_db.apply_era(LegacyRollover.TALKS_YEAR + 1)
	_gs._era_trim("BRL", false)
	LegacyRollover._merge(_gs, false)
	_gs.merger_cut_due = true


func _list() -> Array:
	return _gs.season.lists.get(_gs.my_club, _gs.my_list)


func _fits() -> bool:
	var RookieList = load("res://scripts/state/RookieList.gd")
	var list := _list()
	return RookieList.senior_count(list) <= RookieList.senior_spots() \
			and RookieList.cat_a_count(list) <= RookieList.cat_a_spots()


func _test_needs() -> void:
	var LegacyRollover = load("res://scripts/state/LegacyRollover.gd")
	var RookieList = load("res://scripts/state/RookieList.gd")
	_setup()
	var list := _list()
	var from_fit := list.filter(func(q): return str(q.get("merged_from", "")) == "FIT").size()
	_check(from_fit == LegacyRollover.LIONS_TAKE, "The merger brings Fitzroy's best %d across (%d)" % [LegacyRollover.LIONS_TAKE, from_fit])
	var needs: Dictionary = _gs.merger_cut_needs()
	_check(int(needs.get("", 0)) == RookieList.senior_count(list) - RookieList.senior_spots() and int(needs.get("", 0)) > 0,
			"Seniors to go = over the era's spots (%s, %d of %d)" % [str(needs), RookieList.senior_count(list), RookieList.senior_spots()])
	_check(_gs.merger_cut_left() == int(needs.get("", 0)) + int(needs.get("A", 0)), "merger_cut_left sums the needs")
	_gs.merger_cut_due = false
	_check(_gs.merger_cut_left() == 0 and _gs.merger_cut_needs().is_empty(), "Nothing to cut once the flag is off")


func _test_refusals() -> void:
	_setup()
	var n: int = _gs.merger_cut_left()
	var list := _list().duplicate()
	list.sort_custom(func(a, b): return int(Ovr.of(a, 0)) < int(Ovr.of(b, 0)))
	var ids := list.slice(0, n).map(func(q): return str(q["id"]))
	var short := ids.slice(0, n - 1)
	var out: Dictionary = _gs.merger_delist(short)
	_check(not bool(out["ok"]) and str(out["reason"]).begins_with("Pick "), "One short is refused (%s)" % str(out))
	out = _gs.merger_delist(ids + [str(list[n]["id"])])
	_check(not bool(out["ok"]), "One too many is refused (%s)" % str(out))
	out = _gs.merger_delist(short + ["nobody"])
	_check(not bool(out["ok"]) and str(out["reason"]) == "That player is not on our list.", "A player off the list is refused (%s)" % str(out))
	var held: Dictionary = list[0]
	held["play_on"] = int(_gs.season_year)
	out = _gs.merger_delist(ids)
	_check(not bool(out["ok"]) and str(out["reason"]).contains(_db.player_display_name(held)),
			"One talked round to play on this season can't be delisted (%s)" % str(out))
	held.erase("play_on")
	_check(_gs.merger_cut_due and _gs.merger_cut_left() == n, "A refusal changes nothing")
	out = _gs.merger_delist(ids)
	_check(bool(out["ok"]) and _fits() and not _gs.merger_cut_due, "The right count delists them and the list fits (%s)" % str(out))
	for id in ids:
		var fa: Array = _gs.free_agents.filter(func(q): return str(q["id"]) == id)
		_check(fa.size() == 1 and str(fa[0].get("released_by", "")) == "BRL", "%s is a free agent, delisted by the Lions" % id)


func _test_club_cut_before_round_one() -> void:
	_setup()
	var n: int = _gs.merger_cut_left()
	var held: Dictionary = _list().reduce(func(a, q): return q if a.is_empty() or int(Ovr.of(q, 0)) < int(Ovr.of(a, 0)) else a, {})
	held["play_on"] = int(_gs.season_year)
	var before: int = _list().size()
	_gs._merger_cut_by_club()
	_check(_list().size() == before - n and _fits() and not _gs.merger_cut_due, "The club cuts exactly the %d over (%d -> %d)" % [n, before, _list().size()])
	_check(_list().has(held), "One talked round to play on stays through the club's cut")
	var news: Array = _gs.news.filter(func(e): return str(e.get("text", "")).contains("after the merger, before Round 1"))
	_check(news.size() == 1, "The news says the club delisted them before Round 1")


func _test_saved() -> void:
	_setup()
	var d: Dictionary = _gs._save_state()
	_check(bool(d.get("merger_cut_due", false)), "The save keeps the cut that is due")
	_gs.merger_cut_due = false
	_check(not bool(_gs._save_state().get("merger_cut_due", true)), "And no cut once it is done")


func _scene_named(n: String, frames := 900) -> Node:
	for i in range(frames):
		await process_frame
		if current_scene != null and str(current_scene.name) == n:
			await _settle(10)
			return current_scene
	return null


func _row_button(scene: Node, id: String, which: String) -> Button:
	var row := scene.find_child("MergerRow_" + id, true, false)
	return row.find_child(which, true, false) as Button if row != null else null


## Scrolled into view first, as a thumb would, then a real tap.
func _tap(b: Button) -> String:
	if b == null:
		return "missing"
	var p := b.get_parent()
	while p != null and not (p is ScrollContainer):
		p = p.get_parent()
	if p != null:
		(p as ScrollContainer).ensure_control_visible(b)
		await _settle(3)
	var why: String = await Tap.tap(b)
	await _settle(4)
	return why


func _test_screen_taps() -> void:
	_setup()
	var n: int = _gs.merger_cut_left()
	var list := _list().duplicate()
	list.sort_custom(func(a, b): return int(Ovr.of(a, 0)) < int(Ovr.of(b, 0)))
	# One talked round to play on: no Delist button on his row.
	var held: Dictionary = list[n + 1]
	held["play_on"] = int(_gs.season_year)
	_router.go("hub")
	var scene: Node = await _scene_named("MergerCutScene")
	_check(scene != null, "The hub opens the merger screen while the list is over (scene %s)" % str(current_scene.name if current_scene else null))
	if scene == null:
		return
	var fig := scene.find_child("LeftFigure", true, false) as Label
	_check(fig != null and fig.text == str(n), "The figure says %d still to pick (%s)" % [n, fig.text if fig else "none"])
	var held_row := scene.find_child("MergerRow_" + str(held["id"]), true, false)
	_check(held_row != null and held_row.find_child("ReleaseHeld", true, false) != null and held_row.find_child("Delist", true, false) == null,
			"A player talked round to play on shows why and has no Delist")
	var from := scene.find_child("MergerRow_" + str(list.filter(func(q): return str(q.get("merged_from", "")) == "FIT")[0]["id"]), true, false)
	_check(from != null and (from.find_child("From", true, false) as Label).text.begins_with("From "), "A Fitzroy player's row says which side he came from")
	var going := list.slice(0, n).map(func(q): return str(q["id"]))
	for id in going:
		var why: String = await _tap(_row_button(scene, id, "Delist"))
		_check(why == "", "A real tap on Delist for %s lands (%s)" % [id, why])
	var marked := scene.find_child("MergerRow_" + str(going[0]), true, false)
	_check(marked != null and marked.find_child("DelistGain", true, false) != null and marked.find_child("DelistCost", true, false) != null,
			"A marked row states the gain and the cost")
	var spare := _row_button(scene, str(list[n]["id"]), "Delist")
	_check(spare != null and spare.disabled, "With %d picked, every other Delist is off" % n)
	var confirm := scene.find_child("ConfirmCut", true, false) as Button
	_check(confirm != null and not confirm.disabled and confirm.text == "Delist %d players" % n, "Confirm reads Delist %d players (%s)" % [n, confirm.text if confirm else "none"])
	var why_keep: String = await _tap(_row_button(scene, str(going[0]), "Keep"))
	confirm = scene.find_child("ConfirmCut", true, false) as Button
	_check(why_keep == "" and confirm.disabled and confirm.text == "Pick 1 more", "Keep takes one back off (%s, %s)" % [why_keep, confirm.text])
	_check(not _row_button(scene, str(list[n]["id"]), "Delist").disabled, "And the other Delists come back on")
	await _tap(_row_button(scene, str(going[0]), "Delist"))
	_check(_gs.merger_cut_due, "Nothing is delisted before Confirm")
	var why_go: String = await _tap(scene.find_child("ConfirmCut", true, false) as Button)
	_check(why_go == "" and not _gs.merger_cut_due and _fits(), "A real tap on Confirm delists them and the list fits (%s)" % why_go)
	for id in going:
		_check(_gs.free_agents.any(func(q): return str(q["id"]) == id and str(q.get("released_by", "")) == "BRL"), "%s is a free agent" % id)
	for i in range(900):
		if current_scene != null and str(current_scene.name) != "MergerCutScene":
			break
		await process_frame
	_check(current_scene != null and str(current_scene.name) != "MergerCutScene",
			"Confirm leaves the merger screen (%s)" % str(current_scene.name if current_scene else null))


## A Bears career in 1990 moved on to 1994, when senior lists fell from 52 to
## 42: the list is over that season's spots with no merger behind it.
func _setup_1994() -> void:
	_gs.reset("1990")
	_gs.begin_real_lists()
	_gs.choose_real_club("BRL")
	_gs.finish_intake_draft()
	_gs.set_setting("seen_weekly_loop_intro", true)
	_gs.media_conference = {}
	_gs.merger_cut_due = false
	_gs.season_year = 1994
	_db.apply_era(1994)


## The list cut opens whenever your list is over the season's limit, not only
## after the merger (director, 2026-11-25, "You pick"), and the club cuts the
## rest by least worth at Round 1, as it does after the merger; the news says
## why.
func _test_list_cut_any_year() -> void:
	var RookieList = load("res://scripts/state/RookieList.gd")
	_setup_1994()
	var list := _list()
	var over: int = RookieList.senior_count(list) - RookieList.senior_spots()
	_check(RookieList.senior_spots() == 42 and over > 0,
			"(setup) 1994 lists 42 seniors and ours has %d" % RookieList.senior_count(list))
	_gs._flag_list_cut()
	var needs: Dictionary = _gs.merger_cut_needs()
	_check(_gs.merger_cut_due and int(needs.get("", 0)) == over and not needs.has("A"),
			"Over 1994's spots, the list cut is due: %d to go (%s)" % [over, str(needs)])
	_check(not _gs.list_cut_after_merger(), "It is not the merger's cut")
	_gs.news.clear()
	_gs._merger_cut_by_club()
	_check(_fits() and not _gs.merger_cut_due, "Round 1 first: the club cuts the %d over and the list fits" % over)
	var line := "The club delisted %s before Round 1, to fit the list." % ("one player" if over == 1 else "%d players" % over)
	_check(_gs.news.any(func(e): return str(e.get("text", "")) == line), "The news says so: %s" % line)
	_gs._flag_list_cut()
	_check(not _gs.merger_cut_due, "A list that fits raises no cut")


## A Legacy start whose real list is longer than its first season allows
## (Essendon's 55 in 1990, against 52): rivals delist their least worth as
## before (bug bash 4, L3); ours opens the list cut for you to pick.
func _test_opening_list_cut() -> void:
	var RookieList = load("res://scripts/state/RookieList.gd")
	_gs.reset("1990")
	_gs.begin_real_lists()
	_gs.choose_real_club("ESS")
	_gs.finish_intake_draft()
	var list := _list()
	var over: int = RookieList.senior_count(list) - RookieList.senior_spots()
	_check(over > 0 and _gs.merger_cut_due and int(_gs.merger_cut_needs().get("", 0)) == over,
			"Essendon opens %d over 1990's %d, the list cut due (%s)" % [over, RookieList.senior_spots(), str(_gs.merger_cut_needs())])
	var rivals_over := []
	for code in _gs.season.lists:
		if code != _gs.my_club and not _gs.list_over(_gs.season.lists[code]).is_empty():
			rivals_over.append(code)
	_check(_gs.season.lists.size() >= 14 and rivals_over.is_empty(),
			"Every rival opens inside the spots (%d clubs; over: %s)" % [_gs.season.lists.size(), str(rivals_over)])


## The screen for a cut with no merger: its own title and lead, worked with
## real taps on a phone in portrait.
func _test_list_cut_screen_taps() -> void:
	var RookieList = load("res://scripts/state/RookieList.gd")
	_setup_1994()
	_gs._flag_list_cut()
	var n: int = _gs.merger_cut_left()
	var have: int = RookieList.senior_count(_list())
	_router.go("hub")
	var scene: Node = await _scene_named("MergerCutScene")
	_check(scene != null, "The hub opens the list cut while the list is over (scene %s)" % str(current_scene.name if current_scene else null))
	if scene == null:
		return
	var titled := scene.find_children("*", "Label", true, false).any(func(l): return (l as Label).text == "List cut")
	_check(titled, "Its title is List cut")
	var lead := scene.find_child("MergerLead", true, false)
	var want := "A club can list 42 senior players in 1994, and we have %d.\nThe ones we delist are free to sign with any club." % have
	_check(lead != null and str(lead.get("text")) == want, "Its lead: %s (%s)" % [want, str(lead.get("text")) if lead else "none"])
	var list := _list().duplicate()
	list.sort_custom(func(a, b): return int(a.get("overall", 0)) < int(b.get("overall", 0)))
	var going := list.slice(0, n).map(func(q): return str(q["id"]))
	for id in going:
		var why: String = await _tap(_row_button(scene, id, "Delist"))
		_check(why == "", "A real tap on Delist for %s lands (%s)" % [id, why])
	var why_go: String = await _tap(scene.find_child("ConfirmCut", true, false) as Button)
	_check(why_go == "" and not _gs.merger_cut_due and _fits(), "A real tap on Confirm delists them and the list fits (%s)" % why_go)
	for i in range(900):
		if current_scene != null and str(current_scene.name) != "MergerCutScene":
			break
		await process_frame
	_check(current_scene != null and str(current_scene.name) != "MergerCutScene",
			"Confirm leaves the list cut (%s)" % str(current_scene.name if current_scene else null))

## A PC (UI batch 5, the director's board A): the list in one-line rows across
## the window (three columns at 1280 x 720; two, a page at a time, at 960 x 540)
## with the clicked man's card beside it, and nothing scrolls. A real tap on a
## row puts him on the card, a real tap on the card's Delist marks him, and
## once enough are marked a real tap on Confirm delists them.
func _test_merger_pc(sz: Vector2i) -> void:
	_setup()
	root.size = sz
	var tag := "%dx%d" % [sz.x, sz.y]
	var n: int = _gs.merger_cut_left()
	var kinds: Array = _gs.merger_cut_needs().keys()
	var listed := _list().filter(func(q): return kinds.has(str(q.get("rookie_list", ""))))
	_router.go("hub")
	var scene: Node = await _scene_named("MergerCutScene")
	_check(scene != null, "PC %s: the hub opens the merger screen" % tag)
	if scene == null:
		return
	await _settle(6)
	var view := Rect2(Vector2.ZERO, Vector2(root.size))
	var cols: Control = scene.find_child("MergerColumns", true, false)
	var room: Control = scene.find_child("MergerRoom", true, false)
	var columns: Array = cols.get_children().filter(func(c): return str(c.name).begins_with("MergerColumn_")) if cols != null else []
	var want := 3 if sz.x >= 1000 else 2
	_check(columns.size() == want, "PC %s: the list runs in %d columns (%d)" % [tag, want, columns.size()])
	_check(room != null and cols.get_combined_minimum_size().y <= room.size.y + 0.5,
			"PC %s: the list fits its room (%.0f in %.0f)" % [tag, cols.get_combined_minimum_size().y if cols != null else 0.0, room.size.y if room != null else 0.0])
	var page: Control = room.get_parent().get_parent().get_parent() if room != null else null
	_check(page != null and page.get_combined_minimum_size().y <= view.size.y,
			"PC %s: the page fits the window, nothing scrolls (%.0f in %.0f)" % [tag, page.get_combined_minimum_size().y if page != null else 0.0, view.size.y])
	var pages := scene.find_child("MergerPages", true, false)
	var shown: Array = cols.find_children("MergerRow_*", "Button", true, false) if cols != null else []
	if want == 3:
		_check(pages == null and shown.size() == listed.size(), "PC %s: all %d players on one page (%d)" % [tag, listed.size(), shown.size()])
	else:
		_check(pages != null and pages.get_child_count() == 2 and shown.size() < listed.size(),
				"PC %s: the list splits into two pages (%d of %d shown)" % [tag, shown.size(), listed.size()])
	_check(not shown.is_empty() and shown.all(func(b): return view.encloses((b as Control).get_global_rect()) and (b as Control).size.y <= 44.5),
			"PC %s: every row is one line and on screen" % tag)
	var card: Control = scene.find_child("MergerCard", true, false)
	_check(card != null and room != null and card.get_global_rect().position.x > room.get_global_rect().end.x and view.encloses(card.get_global_rect()),
			"PC %s: the card sits beside the list, on screen" % tag)
	if want == 2 and pages != null and pages.get_child_count() == 2:
		var first_ids: Array = shown.map(func(r): return str(r.name))
		var why_p: String = await _tap(pages.get_child(1) as Button)
		var now: Array = scene.find_children("MergerRow_*", "Button", true, false)
		_check(why_p == "" and not now.is_empty() and now.all(func(r): return not first_ids.has(str(r.name)))
				and first_ids.size() + now.size() == listed.size(),
				"PC %s: a real tap on the second page shows the other %d players (%s)" % [tag, now.size(), why_p])
		var back := scene.find_child("MergerPages", true, false)
		why_p = await _tap(back.get_child(0) as Button if back != null else null)
		_check(why_p == "" and scene.find_children("MergerRow_*", "Button", true, false).size() == first_ids.size(),
				"PC %s: ...and the first page brings them back" % tag)
	# The lowest n, picked as a coach would: find him (turning the page if he is
	# on the other one), click his row, then Delist on his card.
	var list := _list().duplicate()
	list.sort_custom(func(a, b): return int(a.get("overall", 0)) < int(b.get("overall", 0)))
	var going := list.filter(func(q): return kinds.has(str(q.get("rookie_list", ""))) \
			and int(q.get("play_on", 0)) != int(_gs.season_year)).slice(0, n).map(func(q): return str(q["id"]))
	for id in going:
		var row := scene.find_child("MergerRow_" + id, true, false) as Button
		if row == null:
			# A page tap rebuilds the screen, so find each page button afresh by name.
			var turn := scene.find_child("MergerPages", true, false)
			var names: Array = (turn.get_children() if turn != null else []).map(func(c): return str(c.name))
			for nm in names:
				if scene.find_child("MergerRow_" + id, true, false) == null:
					await _tap(scene.find_child(nm, true, false) as Button)
			row = scene.find_child("MergerRow_" + id, true, false) as Button
		var why: String = await _tap(row)
		var name_on := scene.find_child("CardName", true, false) as Label
		_check(why == "" and name_on != null and name_on.text == _db.player_display_name(_player(id)),
				"PC %s: a real tap on %s's row puts him on the card (%s)" % [tag, id, why])
		var act := (scene.find_child("MergerCard", true, false) as Node).find_child("Delist", true, false) as Button
		why = await _tap(act)
		_check(why == "", "PC %s: a real tap on the card's Delist for %s lands (%s)" % [tag, id, why])
		var crossed := scene.find_child("MergerRow_" + id, true, false)
		_check(crossed != null and crossed.find_child("CrossedOff", true, false) != null,
				"PC %s: %s's row is crossed off once he is marked" % [tag, id])
	var marked := scene.find_child("MergerCard", true, false)
	_check(marked != null and marked.find_child("DelistGain", true, false) != null and marked.find_child("DelistCost", true, false) != null
			and marked.find_child("Keep", true, false) != null, "PC %s: the card states the gain and the cost, then Keep" % tag)
	var confirm := scene.find_child("ConfirmCut", true, false) as Button
	var at: Rect2 = confirm.get_global_rect() if confirm != null else Rect2()
	_check(confirm != null and not confirm.disabled and confirm.text == "Delist %d players" % n and at.size.x < 400.0
			and view.encloses(at) and at.end.x > view.size.x * 0.9,
			"PC %s: Confirm reads Delist %d players, sized to its words at the right (%s)" % [tag, n, str(at)])
	var why_go: String = await _tap(confirm)
	_check(why_go == "" and not _gs.merger_cut_due and _fits(), "PC %s: a real tap on Confirm delists them and the list fits (%s)" % [tag, why_go])
	for i in range(900):
		if current_scene != null and str(current_scene.name) != "MergerCutScene":
			break
		await process_frame


func _player(id: String) -> Dictionary:
	for p in _list():
		if str(p["id"]) == id:
			return p
	return {}
