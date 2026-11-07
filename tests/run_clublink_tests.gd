extends SceneTree
## godot --headless --path . --script tests/run_clublink_tests.gd
## The club honour board and every club's page (row 122; rulings 5.11 no. 112
## and 113). The board's rules (150 games, a best and fairest, a Brownlow or a
## flag; newest first; one row per player id; a dash for what an old save never
## kept), its save round trip and an old save's backfill. Real touches at
## 390x844 and 1280x720: a club's name opens its page, Back closes it, a swipe
## that starts on a club's name still scrolls, the page leads to the honour
## board and a name on the board opens his facts; the trophy room's link. A
## rival's page shows nothing hidden (#759).

const Tap := preload("res://tests/tap.gd")
const SAVE := "user://test_clublink.save"

var _checks := 0
var _failures: Array = []
var _gs: Node
var _db: Node
var _router: Node
var _hb: GDScript
var _cp: GDScript
var _cl: GDScript
var _ui: GDScript
var _ni: GDScript
var _nl: GDScript
var _cs: GDScript
var _car: GDScript


## The seasons this suite starts are the same every run (C15).
const SUITE_SEED := 2027


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
	_hb = load("res://scripts/sim/HonourBoard.gd")
	_cp = load("res://scripts/ui/ClubPage.gd")
	_cl = load("res://scripts/ui/ClubLink.gd")
	_ui = load("res://scripts/ui/UiKit.gd")
	_ni = load("res://scripts/ui/NameInk.gd")
	_nl = load("res://scripts/ui/NameLink.gd")
	_cs = load("res://scripts/state/CareerSave.gd")
	_car = load("res://scripts/sim/Career.gd")
	_gs.autosave_enabled = false
	_gs.replay_seed = SUITE_SEED
	_gs.save_path = SAVE
	_gs.settings_path = "user://test_clublink.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_gs.set_setting("seen_%s_intro" % key, true)
	_gs.show_real_names = false
	await _t("_test_rules")
	await _t("_test_save_round_trip")
	await _t("_test_old_save_backfill")
	await _t("_test_club_move")
	await _t("_test_departures")
	await _t("_test_club_names_in_lines")
	await _t("_test_left_game_opens_facts", [Vector2i(390, 844)])
	await _t("_test_news_club_tap", [Vector2i(390, 844)])
	for sz in [Vector2i(390, 844), Vector2i(1280, 720)]:
		await _t("_test_club_tap", [sz])
		await _t("_test_board_taps", [sz])
		await _t("_test_trophy_link", [sz])
	# The narrowest phone the game lays out for.
	await _t("_test_board_taps", [Vector2i(320, 693)])
	await _t("_test_drag_over_club", [Vector2i(390, 844)])
	await _t("_test_profile_club_line", [Vector2i(390, 844)])
	_gs.replay_seed = 0
	print(Ran.line("Club link", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(0 if _failures.is_empty() else 1)


# ---------------------------------------------------------------------------
# Set-up
# ---------------------------------------------------------------------------
func _fresh(club := "FRE") -> void:
	_gs.reset()
	_gs.start_season(club, _db.club_list(club))


## Give p a career at `club`: `games` games over from..to, through this season
## so nothing more is added from the running tally.
func _career(p: Dictionary, club: String, from: int, to: int, games: int, goals := 0) -> void:
	var c: Dictionary = _car.fresh()
	c["stints"] = [[club, from, to, games, goals]]
	c["through"] = int(_gs.season_year)
	p["career"] = c


## Move p off your list to `code`'s.
func _move(p: Dictionary, code: String) -> void:
	_gs.my_list.erase(p)
	if _gs.season.lists[_gs.my_club] != _gs.my_list:
		(_gs.season.lists[_gs.my_club] as Array).erase(p)
	p["club"] = code
	(_gs.season.lists[code] as Array).append(p)


## A board with one player of each kind gone, for the UI tests: a 150-gamer who
## went to Melbourne, and a best and fairest winner who has left the game.
func _board_setup() -> Dictionary:
	_fresh("FRE")
	var y := int(_gs.season_year)
	var big: Dictionary = _gs.my_list[0]
	_career(big, "FRE", y - 8, y, 160, 90)
	_hb.upsert(_gs, big)
	_move(big, "MEL")
	_hb.sweep(_gs)
	_gs.honour_roll.append({"year": y - 1, "my_club": "FRE", "premier": "", "my_bf": [{"id": "ghost1", "name": "Old Champion"}],
			"brownlow": [{"id": "ghost1", "name": "Old Champion", "club": "FRE"}]})
	_gs.departed_names["ghost1"] = {"generic_name": "Old Champion", "year": y - 1}
	_hb.backfill(_gs, func(id: String) -> Dictionary: return _gs._any_player(id))
	return {"big": big}


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
func _test_rules() -> void:
	_fresh("FRE")
	var y := int(_gs.season_year)
	var a: Dictionary = _gs.my_list[0]
	_career(a, "FRE", y - 7, y, 149, 30)
	_hb.upsert(_gs, a)
	_check(not _gs.honour_board.has(str(a["id"])), "149 games and no honour: not on the board")
	_career(a, "FRE", y - 7, y, 150, 30)
	_hb.upsert(_gs, a)
	var row: Dictionary = _gs.honour_board.get(str(a["id"]), {})
	_check(int(row.get("games", 0)) == 150 and int(row.get("left", -1)) == 0,
			"150 games earns a row, not shown while he is still here (%s)" % str(row))
	_check(_hb.rows(_gs.honour_board).is_empty(), "A player still on your list is not on the board")
	_hb.upsert(_gs, a)
	_hb.upsert(_gs, a)
	_check(int(_gs.honour_board[str(a["id"])]["games"]) == 150, "Refreshing a row never adds to it")
	_move(a, "MEL")
	_hb.sweep(_gs)
	row = _gs.honour_board[str(a["id"])]
	_check(int(row["left"]) == y and str(row["how"]) == "moved" and str(row["to_club"]) == "MEL",
			"A traded 150-gamer is stamped as moved to his new club (%s)" % str(row))
	_check(_hb.rows(_gs.honour_board).size() == 1, "...and is on the board")

	# A best and fairest alone.
	var b: Dictionary = _gs.my_list[0]
	_career(b, "FRE", y - 1, y, 12, 1)
	_gs.honour_roll.append({"year": y, "my_club": "FRE", "premier": "", "my_bf": [{"id": str(b["id"]), "name": "x"}]})
	_hb.upsert(_gs, b)
	_check(_gs.honour_board.has(str(b["id"])) and (_gs.honour_board[str(b["id"])]["bf"] as Array) == [y],
			"A best and fairest earns a row on 12 games")
	# A flag alone.
	var c: Dictionary = _gs.my_list[1]
	_career(c, "FRE", y, y, 4, 0)
	_gs.honour_roll.append({"year": y, "my_club": "FRE", "premier": "FRE", "my_bf": []})
	_hb.upsert(_gs, c)
	_check(_gs.honour_board.has(str(c["id"])) and (_gs.honour_board[str(c["id"])]["flags"] as Array) == [y],
			"A flag earns a row on 4 games")
	# A spell that ended before the career began is the club's history (ruling 118).
	var old: Dictionary = _gs.my_list[2]
	_career(old, "FRE", 2010, _car.BEFORE_GAME, 200, 10)
	old["club"] = "MEL"
	var held: Dictionary = _gs.honour_board.duplicate()
	_hb.upsert(_gs, old)
	_check(not _gs.honour_board.has(str(old["id"])) or held.has(str(old["id"])),
			"A 200-gamer from before your time is not on your board")

	# Two players with one name keep their own rows (ids, never names).
	var d: Dictionary = _gs.my_list[3]
	var e: Dictionary = _gs.my_list[4]
	e["generic_name"] = str(d.get("generic_name", d.get("name", "")))
	e["real_name"] = str(d.get("real_name", ""))
	_career(d, "FRE", y - 9, y, 170, 5)
	_career(e, "FRE", y - 9, y, 180, 6)
	_hb.upsert(_gs, d)
	_hb.upsert(_gs, e)
	_check(int(_gs.honour_board[str(d["id"])]["games"]) == 170 and int(_gs.honour_board[str(e["id"])]["games"]) == 180,
			"Two players with one name have a row each")

	# Newest departure first.
	var store := {
		"p1": {"id": "p1", "games": 200, "bf": [], "flags": [], "brownlow": [], "left": 2027},
		"p2": {"id": "p2", "games": 150, "bf": [], "flags": [], "brownlow": [], "left": 2029},
		"p3": {"id": "p3", "games": 160, "bf": [], "flags": [], "brownlow": [], "left": 2029},
		"p4": {"id": "p4", "games": 20, "bf": [], "flags": [], "brownlow": [], "left": 2030}}
	var order: Array = _hb.rows(store).map(func(r): return str(r["id"]))
	_check(order == ["p3", "p2", "p1"], "Newest first, then most games; a 20-gamer with no honour is left off (%s)" % str(order))

	# A delisting stamps the season and how.
	var f: Dictionary = _gs.my_list[5]
	_career(f, "FRE", y - 8, y, 155, 3)
	_hb.leave(_gs, f, "delisted")
	_check(int(_gs.honour_board[str(f["id"])]["left"]) == y and str(_gs.honour_board[str(f["id"])]["how"]) == "delisted",
			"Leaving stamps the season and how he went")
	# A retirement after that is the fuller word; the season stays.
	_hb.leave(_gs, f, "retired")
	_check(str(_gs.honour_board[str(f["id"])]["how"]) == "retired", "A later retirement replaces the delisting")

	# A row an old save rebuilt with no figures shows dashes, never a guess.
	_check(_cp._cell({"games": -1}, "games") == "-" and _cp._cell({"goals": -1}, "goals") == "-",
			"Games and goals not on record show a dash")
	_check(_cp._cell({"bf": []}, "bf") == "-" and _cp._cell({"flags": []}, "flags") == "-" 			and _cp._cell({"games": 0}, "games") == "-",
			"Every column shows none the same way: a dash, never a blank")


func _test_save_round_trip() -> void:
	_board_setup()
	var before: Dictionary = _gs.honour_board.duplicate(true)
	_check(before.size() >= 2, "The board has rows to save (%d)" % before.size())
	_check(_gs.save_career(), "The career saves")
	_gs.reset()
	_check(_gs.honour_board.is_empty(), "reset() clears the board")
	_check(_gs.load_career(), "The career loads")
	_check(_gs.honour_board.size() == before.size(), "The board comes back whole (%d of %d)" % [_gs.honour_board.size(), before.size()])
	for id in before:
		var a: Dictionary = before[id]
		var b: Dictionary = _gs.honour_board.get(id, {})
		_check(int(a.get("games", 0)) == int(b.get("games", 0)) and int(a.get("left", 0)) == int(b.get("left", 0))
				and str(a.get("how", "")) == str(b.get("how", "")), "%s keeps his row through a save" % id)


func _test_old_save_backfill() -> void:
	_board_setup()
	_check(_gs.save_career(), "The career saves")
	var state: Dictionary = _cs.read(SAVE)
	var meta: Dictionary = _cs.read_meta(SAVE)
	state.erase("honour_board")
	_check(_cs.write(state, meta, SAVE), "An old save without a board is written")
	_check(_gs.load_career(), "The old save loads")
	var ghost: Dictionary = _gs.honour_board.get("ghost1", {})
	_check(not ghost.is_empty() and int(ghost["games"]) == -1 and (ghost["bf"] as Array).size() == 1,
			"A best and fairest winner who has left the game is rebuilt from the honour roll, his games a dash (%s)" % str(ghost))
	_check(_db.player_display_name(ghost.get("card", {})) == "Old Champion", "...under his own name")
	# A 150-gamer who went to Melbourne before the board existed: no honour on
	# the roll, still rebuilt from his record at his new club.
	var big: Dictionary = _gs.honour_board.get(str(_gs.season.lists["MEL"][-1]["id"]), {})
	_check(not big.is_empty() and int(big.get("games", 0)) == 160 and str(big.get("how", "")) == "moved"
			and str(big.get("to_club", "")) == "MEL", "A 150-gamer now at another club is rebuilt too (%s)" % str(big))


## A coach who moves clubs leaves the old board behind; the new club's starts
## empty, and the old one comes back if he ever returns.
func _test_club_move() -> void:
	_board_setup()
	var y := int(_gs.season_year)
	var cap: Dictionary = _gs.my_list[0]
	_career(cap, "FRE", y - 10, y, 200, 40)
	_hb.upsert(_gs, cap)
	var fre_rows: int = _hb.rows(_gs.honour_board, _gs.my_list).size()
	_check(fre_rows >= 2 and _gs.honour_board.has(str(cap["id"])), "Fremantle's board before the move (%d)" % fre_rows)
	_hb.change_club(_gs, "FRE", "MEL")
	_gs.my_club = "MEL"
	_gs.my_list = _gs.season.lists["MEL"]
	_hb.sweep(_gs)
	_check(_hb.rows(_gs.honour_board, _gs.my_list).is_empty() and not _gs.honour_board.has(str(cap["id"])),
			"Melbourne's board starts empty: your old captain is not 'left for Fremantle' on it (%s)" % str(_gs.honour_board.keys()))
	_check((_gs.honour_boards.get("FRE", {}) as Dictionary).has(str(cap["id"])), "Fremantle's board is kept")
	_check(int((_gs.honour_boards.get("FRE", {}) as Dictionary).get(str(cap["id"]), {}).get("left", -1)) == 0,
			"...with your captain still at Fremantle")
	_hb.change_club(_gs, "MEL", "FRE")
	_gs.my_club = "FRE"
	_check(_hb.rows(_gs.honour_board).size() == fre_rows, "Back at Fremantle, its board returns")


## How a player left reads true: a free agent who signs elsewhere left for that
## club; a player who left you and retired elsewhere keeps his years with you; a
## release undone is off the board.
func _test_departures() -> void:
	_fresh("FRE")
	var y := int(_gs.season_year)
	# Out of contract, he walks, then signs with Collingwood.
	var w: Dictionary = _gs.my_list[0]
	_career(w, "FRE", y - 8, y, 160, 20)
	_hb.upsert(_gs, w)
	_gs.my_list.erase(w)
	if _gs.season.lists["FRE"] != _gs.my_list:
		(_gs.season.lists["FRE"] as Array).erase(w)
	_gs.free_agents.append(w)
	_hb.sweep(_gs)
	var row: Dictionary = _gs.honour_board.get(str(w["id"]), {})
	_check(str(row.get("how", "")) == "free_agent", "Out of contract and unsigned: he left as a free agent, not delisted (%s)" % str(row))
	_check(_cp._how(row) == "Left as a free agent after the %d season." % y, "...in those words (%s)" % _cp._how(row))
	_gs.free_agents.erase(w)
	w["club"] = "COL"
	(_gs.season.lists["COL"] as Array).append(w)
	_hb.sweep(_gs)
	row = _gs.honour_board.get(str(w["id"]), {})
	_check(str(row.get("how", "")) == "moved" and str(row.get("to_club", "")) == "COL" and int(row.get("left", 0)) == y,
			"...then signs with Collingwood: he left for Collingwood that season (%s)" % str(row))
	# Played for you, left, retires at Melbourne three seasons later.
	# (Four seasons on, so his years with you are in this career.)
	var r: Dictionary = _gs.my_list[0]
	var c: Dictionary = _car.fresh()
	c["stints"] = [["FRE", y - 6, y + 1, 160, 50], ["MEL", y + 2, y + 4, 40, 5]]
	_gs.season_year = y + 4
	c["through"] = y + 4
	r["career"] = c
	_move(r, "MEL")
	_hb.leave(_gs, r, "retired")
	row = _gs.honour_board.get(str(r["id"]), {})
	_check(int(row.get("left", 0)) == y + 1 and str(row.get("how", "")) == "moved" and str(row.get("to_club", "")) == "MEL",
			"A former player retiring elsewhere left you when his spell ended (%s)" % str(row))
	_check(_cp._cell(row, "years") == "%d-%02d" % [y - 6, (y + 1) % 100],
			"...and his years are his years with you (%s)" % _cp._cell(row, "years"))
	# A release undone: he is on your list, so not on the board.
	var u: Dictionary = _gs.my_list[0]
	_career(u, "FRE", y - 8, y, 170, 20)
	_hb.leave(_gs, u, "delisted")
	var uid := str(u["id"])
	_check(_hb.rows(_gs.honour_board, _gs.my_list).filter(func(x): return str(x["id"]) == uid).is_empty(),
			"A player back on your list is not on the board, whatever his row says")


## A club named in a running line (news, match notes, a pick's story) wears its
## colours and is a tap to its page; a ground named for a city is not the club.
func _test_club_names_in_lines() -> void:
	_fresh("FRE")
	var idx: Dictionary = _ni.from_lists(_gs.season.lists)
	var bb: String = _ni.markup("Collingwood beat North Melbourne at Adelaide Oval.", idx)
	_check(bb.contains("club:COL") and bb.contains("club:NTH"), "Club names in a line are taps (%s)" % bb)
	_check(not bb.contains("club:MEL") and not bb.contains("club:ADE"),
			"North Melbourne is not Melbourne, Adelaide Oval is not Adelaide (%s)" % bb)
	_check(_ni.markup("Collingwood beat North Melbourne.", idx, false) == "", "A button's own words keep club names plain")
	_check(_ni.markup("A quiet week at the club.", idx) == "", "A line naming no one stays plain")


## A player who has left the game opens his career facts, never his record
## from the league's data (a retiree's first-season profile).
func _test_left_game_opens_facts(sz: Vector2i) -> void:
	_fresh("FRE")
	var screen := _screen(sz)
	await _settle()
	var p: Dictionary = _gs.my_list[0]
	var id := str(p["id"])
	_check(not _nl.find(id).is_empty(), "He is in the league's data")
	_gs.my_list.erase(p)
	if _gs.season.lists["FRE"] != _gs.my_list:
		(_gs.season.lists["FRE"] as Array).erase(p)
	_gs.departed_names[id] = {"generic_name": "Gone Player", "year": int(_gs.season_year)}
	var row := {"id": id, "card": {"generic_name": "Gone Player"}, "from": 2026, "to": int(_gs.season_year),
			"games": 160, "goals": 10, "bf": [], "flags": [], "brownlow": [], "aa": [],
			"left": int(_gs.season_year), "how": "retired", "to_club": "", "facts": []}
	var opened: Control = _cp.open_row(screen, row)
	await _settle()
	_check(opened != null and opened.name == _cp.FACTS_NAME and screen.get_node_or_null("PlayerProfile") == null,
			"A retired player in the league's data opens his career facts (%s)" % (str(opened.name) if opened != null else "null"))
	_router.handle_back()
	await _settle()
	screen.queue_free()
	await _settle()


## A real tap on a club named in a news line opens its page.
func _test_news_club_tap(sz: Vector2i) -> void:
	_fresh("FRE")
	root.size = sz
	var page := Control.new()
	page.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(page)
	current_scene = page
	var line: Control = _ni.label("Richmond have signed a new ruckman.", _ni.from_lists(_gs.season.lists), _ui.BODY, _ui.TEXT)
	line.name = "NewsLine"
	line.position = Vector2(16, 60)
	line.size = Vector2(sz.x - 32, 60)
	page.add_child(line)
	await _settle()
	_check(line is RichTextLabel, "A news line naming a club is drawn with the club in its colours")
	var opened: bool = await _tap_scan(line, page)
	var cp := _page(page)
	_check(opened and cp != null and str(cp.get_meta("club_code", "")) == "RIC",
			"A finger on the club in a news line opens its page")
	page.queue_free()
	await _settle()


# ---------------------------------------------------------------------------
# Taps
# ---------------------------------------------------------------------------
## A plain screen holding a line that names two clubs and a label that is one.
func _screen(sz: Vector2i) -> Control:
	root.size = sz
	var page := Control.new()
	page.name = "Screen"
	page.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var v := VBoxContainer.new()
	v.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	page.add_child(v)
	var line: RichTextLabel = _ni.rich(_ui.BODY, _ui.TEXT)
	line.name = "ClubLine"
	line.text = "%s beat %s" % [_cl.ink("MEL"), _cl.ink("FRE")]
	_nl.wire(line)
	v.add_child(line)
	var lab: Label = _ui.lbl(_db.club_name("MEL"), _ui.NAME, _ui.TEXT, true)
	lab.name = "ClubLabel"
	lab.custom_minimum_size = Vector2(0, 44)
	lab.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_cl.tappable(lab, "MEL")
	v.add_child(lab)
	root.add_child(page)
	current_scene = page
	return page


func _page(host: Node) -> Control:
	var c := host.get_node_or_null(_cp.SHEET_NAME)
	return c as Control if c != null and not c.is_queued_for_deletion() else null


func _text_of(n: Node) -> String:
	var out := []
	for c in n.find_children("*", "", true, false):
		if c is Label:
			out.append((c as Label).text)
		elif c is RichTextLabel:
			out.append((c as RichTextLabel).get_parsed_text())
		elif c is Button:
			out.append((c as Button).text)
	return "\n".join(out)


func _test_club_tap(sz: Vector2i) -> void:
	var tag := "%dx%d" % [sz.x, sz.y]
	_board_setup()
	var screen := _screen(sz)
	await _settle()
	# A club's own label.
	var why: String = await Tap.tap(screen.find_child("ClubLabel", true, false))
	await _settle()
	var page := _page(screen)
	_check(why == "" and page != null and str(page.get_meta("club_code", "")) == "MEL",
			"%s: a finger on a club's name opens its page (%s)" % [tag, why])
	if page != null:
		var txt := _text_of(page)
		for want in [_db.club_name("MEL"), "Home ground", "Senior coach", "Premierships", "Last five", "Best 22"]:
			_check(txt.contains(want), "%s: the page shows %s" % [tag, want])
		_check(page.find_child("LineMID", true, false) != null, "%s: the best 22 is named by line" % tag)
		# #759: a rival's page shows public facts only.
		for banned in ["OVR", "Mood", "morale", "Game plan", "rating", "Rating", "potential"]:
			_check(not txt.contains(banned), "%s: a rival's page never shows '%s'" % [tag, banned])
		_check(page.find_child("HonourBoardButton", true, false) == null, "%s: a rival's page has no honour board" % tag)
		_check(txt.contains("Players swapped") and txt.contains("Played 160 for you"),
				"%s: the page names the player you swapped with them" % tag)
		_check(page.find_child("ClubName", true, false).get_global_rect().size.x <= float(sz.x),
				"%s: the club's name fits the screen" % tag)
	_router.handle_back()
	await _settle()
	_check(_page(screen) == null and is_instance_valid(screen) and screen.is_inside_tree(),
			"%s: Back closes the page and leaves the screen as it was" % tag)
	# A club named in a running line.
	var opened: bool = await _tap_scan(screen.find_child("ClubLine", true, false), screen)
	_check(opened, "%s: tapping a club in a running line opens its page" % tag)
	var p2 := _page(screen)
	if p2 != null:
		# Your own club's page: the honour board, "You" as coach.
		var code := str(p2.get_meta("club_code", ""))
		if code != "FRE":
			_router.handle_back()
			await _settle()
			_cl.open(screen, "FRE")
			await _settle()
			p2 = _page(screen)
		_check(_text_of(p2).contains("Senior coach  You"), "%s: your own page names you as senior coach" % tag)
		_check(p2.find_child("HonourBoardButton", true, false) != null, "%s: your page leads to the honour board" % tag)
		# The close button, a real tap.
		var why2: String = await Tap.tap(p2.find_child("CloseClub", true, false))
		await _settle()
		_check(why2 == "" and _page(screen) == null, "%s: Close closes the page (%s)" % [tag, why2])
	screen.queue_free()
	await _settle()


func _test_board_taps(sz: Vector2i) -> void:
	var tag := "%dx%d" % [sz.x, sz.y]
	var s: Dictionary = _board_setup()
	var screen := _screen(sz)
	await _settle()
	var page: Control = _cl.open(screen, "FRE")
	await _settle()
	var why: String = await Tap.tap(page.find_child("HonourBoardButton", true, false))
	await _settle()
	var board: Node = screen.get_node_or_null(_cp.BOARD_NAME)
	_check(why == "" and board != null, "%s: the page's button opens the honour board (%s)" % [tag, why])
	if board == null:
		screen.queue_free()
		return
	var big: Dictionary = s["big"]
	var big_row: Node = board.find_child("Board_" + str(big["id"]), true, false)
	var ghost_row: Node = board.find_child("Board_ghost1", true, false)
	_check(big_row != null and ghost_row != null, "%s: both players who left are on the board" % tag)
	_check(board.find_child("BoardHead", true, false) != null and _text_of(board.find_child("BoardHead", true, false)).contains("B&F"),
			"%s: the board has its column heads" % tag)
	var right := 0.0
	for r in [board.find_child("BoardHead", true, false), big_row, ghost_row]:
		if r != null:
			right = maxf(right, (r as Control).get_global_rect().end.x)
	_check(right <= sz.x - 16.0, "%s: the board fits the screen (right edge %.0f of %d)" % [tag, right, sz.x])
	var wide_cols: bool = _text_of(board.find_child("BoardHead", true, false)).contains("Brownlow")
	_check(wide_cols == (sz.x >= int(_cp.BOARD_WIDE)), "%s: Brownlow and All-Australian columns only where they fit" % tag)
	if ghost_row != null:
		_check(_text_of(ghost_row).contains("-"), "%s: a games figure not on record is a dash" % tag)
		var gn: Control = ghost_row.find_child("BoardName", true, false)
		_check((ghost_row as Control).size.y >= 44.0, "%s: a row on the board is a 44 px tap (%.0f)" % [tag, (ghost_row as Control).size.y])
		# No Brownlow column on a phone: his medal is in words under his name.
		_check(wide_cols or _text_of(ghost_row).contains("Brownlow %d" % (int(_gs.season_year) - 1)),
				"%s: a Brownlow medallist's medal shows on his row (%s)" % [tag, _text_of(ghost_row)])
		var font: Font = gn.get_theme_font("font")
		var need: float = font.get_string_size((gn as Label).text, HORIZONTAL_ALIGNMENT_LEFT, -1,
				gn.get_theme_font_size("font_size")).x
		_check(gn.size.x >= need, "%s: a name on the board reads in full (%.0f px for %.0f)" % [tag, gn.size.x, need])
		# The tap lands on his name; the row under it takes it.
		var why2: String = await Tap.tap_at(ghost_row, gn.get_global_rect().get_center() - (ghost_row as Control).global_position, true)
		await _settle()
		var facts: Node = screen.get_node_or_null(_cp.FACTS_NAME)
		_check(why2 == "" and facts != null and _text_of(facts).contains("Old Champion"),
				"%s: a name of a player who left the game opens his career facts (%s)" % [tag, why2])
		_router.handle_back()
		await _settle()
		_check(screen.get_node_or_null(_cp.FACTS_NAME) == null and screen.get_node_or_null(_cp.BOARD_NAME) != null,
				"%s: Back closes the facts and leaves the board" % tag)
	if big_row != null:
		# His career facts on record (T5.r110): a flag and a medal, read on the
		# profile a real tap opens.
		var y := int(_gs.season_year)
		_gs.honour_roll.append({"year": y - 2, "my_club": "FRE", "premier": "FRE",
				"coleman": [{"id": str(big["id"]), "club": "FRE", "goals": 70}]})
		var bn: Control = big_row.find_child("BoardName", true, false)
		var why3: String = await Tap.tap_at(big_row, bn.get_global_rect().get_center() - (big_row as Control).global_position, true)
		await _settle()
		var prof: Node = screen.get_node_or_null("PlayerProfile")
		_check(why3 == "" and prof != null, "%s: a name of a player still in the game opens his profile (%s)" % [tag, why3])
		var ptext := _text_of(prof) if prof != null else ""
		_check(ptext.contains("Debuted in %d, for Fremantle." % (y - 8))
				and ptext.contains("At Fremantle for the %d premiership." % (y - 2))
				and ptext.contains("Coleman Medal %d." % (y - 2)),
				"%s: his profile's Career section lists his debut, flag and medal on record (%s)" % [tag, ptext.replace("\n", " | ")])
		_gs.honour_roll.pop_back()
		_router.handle_back()
		await _settle()
	_router.handle_back()
	await _settle()
	_check(screen.get_node_or_null(_cp.BOARD_NAME) == null and _page(screen) != null,
			"%s: Back closes the board and leaves the club page" % tag)
	_router.handle_back()
	await _settle()
	_check(_page(screen) == null, "%s: Back closes the club page" % tag)
	screen.queue_free()
	await _settle()


func _test_trophy_link(sz: Vector2i) -> void:
	var tag := "%dx%d" % [sz.x, sz.y]
	_board_setup()
	# The stats hub's first-visit intro is not in FirstVisitIntro.TEXT; seen,
	# so its overlay does not take the tap meant for the link.
	_gs.set_setting("seen_season_stats_intro", true)
	root.size = sz
	load("res://scripts/ui/StatsHubScene.gd").current = "trophies"
	var s: Control = load("res://scenes/StatsHubScene.tscn").instantiate()
	root.add_child(s)
	current_scene = s
	await _settle()
	var link: Control = s.find_child("HonourBoardLink", true, false)
	_check(link != null, "%s: the trophy room links to the honour board" % tag)
	if link != null:
		# A player scrolls down to it first; let the scroll settle before the tap.
		var anc: Node = link.get_parent()
		while anc != null and not (anc is ScrollContainer):
			anc = anc.get_parent()
		if anc != null:
			(anc as ScrollContainer).ensure_control_visible(link)
		await _settle()
		var why: String = await Tap.tap(link)
		await _settle()
		_check(why == "" and s.find_child(_cp.BOARD_NAME, true, false) != null,
				"%s: a finger on the link opens the board (%s)" % [tag, why])
		_check(s.call("handle_back") == true, "%s: the stats hub's Back closes the board" % tag)
		await _settle()
		_check(s.find_child(_cp.BOARD_NAME, true, false) == null, "%s: ...and it is gone" % tag)
	s.queue_free()
	await _settle()


## A swipe that begins on a club's name scrolls and opens nothing.
func _test_drag_over_club(sz: Vector2i) -> void:
	_fresh("FRE")
	root.size = sz
	var page := Control.new()
	page.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(page)
	current_scene = page
	var body: VBoxContainer = _ui.vbox(8)
	var sc: ScrollContainer = _ui.scroll(body)
	sc.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	page.add_child(sc)
	var lab: Label = _ui.lbl(_db.club_name("MEL"), _ui.NAME, _ui.TEXT, true)
	lab.custom_minimum_size = Vector2(0, 44)
	_cl.tappable(lab, "MEL")
	body.add_child(lab)
	for i in 40:
		body.add_child(_ui.lbl("Filler %d" % i, _ui.BODY))
	await _settle()
	var at: Vector2 = lab.get_global_rect().get_center()
	await _touch(at, true)
	for i in 8:
		await _drag(at - Vector2(0, 10 * (i + 1)), Vector2(0, -10))
	await _touch(at - Vector2(0, 80), false)
	await _settle()
	_check(_page(page) == null, "A swipe that starts on a club's name opens nothing")
	_check(sc.scroll_vertical > 0, "...and scrolls the page (%d)" % sc.scroll_vertical)
	page.queue_free()
	await _settle()


## The player's profile names his club, and the name is a tap.
func _test_profile_club_line(sz: Vector2i) -> void:
	_fresh("FRE")
	var screen := _screen(sz)
	await _settle()
	var p: Dictionary = _gs.season.lists["MEL"][0]
	var prof: Control = _nl.open(screen, str(p["id"]))
	await _settle()
	var cl: Control = prof.find_child("ProfileClub", true, false) if prof != null else null
	_check(cl != null and (cl as Label).text == _db.club_name("MEL"), "A profile names his club")
	if cl != null:
		var why: String = await Tap.tap_at(cl, cl.size * 0.5, true)
		await _settle()
		var page := _page(screen)
		_check(why == "" and page != null and str(page.get_meta("club_code", "")) == "MEL",
				"A finger on his club opens its page over the profile (%s)" % why)
		_router.handle_back()
		await _settle()
		_check(_page(screen) == null and screen.get_node_or_null("PlayerProfile") != null,
				"Back closes the club page first, leaving the profile")
		_router.handle_back()
		await _settle()
		_check(screen.get_node_or_null("PlayerProfile") == null, "...then the profile")
	screen.queue_free()
	await _settle()


# ---------------------------------------------------------------------------
# Touch helpers (as tests/run_namelink_tests.gd)
# ---------------------------------------------------------------------------
func _tap_scan(label: Control, host: Node) -> bool:
	var r := label.get_global_rect()
	var y := r.position.y + 8.0
	while y < r.end.y:
		var x := r.position.x + 4.0
		while x < r.end.x:
			await _touch(Vector2(x, y), true)
			await _touch(Vector2(x, y), false)
			await _settle(2)
			if _page(host) != null:
				return true
			x += 5.0
		y += 14.0
	return false


func _touch(pos: Vector2, down: bool) -> void:
	var t := InputEventScreenTouch.new()
	t.index = 0
	t.position = pos
	t.pressed = down
	Input.parse_input_event(t)
	Input.flush_buffered_events()
	await process_frame


func _drag(pos: Vector2, rel: Vector2) -> void:
	var d := InputEventScreenDrag.new()
	d.index = 0
	d.position = pos
	d.relative = rel
	Input.parse_input_event(d)
	Input.flush_buffered_events()
	await process_frame
