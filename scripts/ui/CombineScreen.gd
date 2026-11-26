class_name CombineScreen
extends Control
## The National Draft Combine (row 83): the day's results to browse in the draft
## room. "The day" leads with who stood out in each test and what the test says
## about his football; a test's own tab is the whole class, best first, by
## position or name. A tap on a name opens his sheet over this screen, so closing
## it comes back to the same place. Results only as Combine.gd holds them: nobody
## who missed testing gets a figure, and nothing here says who to take.

signal inspect(id: String)
signal closed

const PAGE := 40
const TABS := [["day", "The day"], ["sprint", "Sprint"], ["trial", "2 km"], ["leap", "Jump"], ["kick", "Kick"]]
const ROLES := ["DEF", "MID", "RUCK", "FWD"]
const MAX_WIDTH := 640.0

var draft: Draft
var club := ""
## Where the coach is, kept by the draft screen for the next visit:
## {"view", "role", "search", "shown", "scroll"}.
var place := {}

var _pool: Array = []
var _ranked := {}    # test -> Combine.ranked
var _fields := {}    # test -> every result, for Combine.standing
var _margin: MarginContainer
var _root: VBoxContainer
var _body: VBoxContainer
var _scroll: ScrollContainer
var _rows: BoxContainer

# A PC (UI batch 5, the director's board A, "four tests across"): the window,
# not a phone column. The day's four tests side by side and the turned heads
# in a row under them; a test's class in one-line rows, two columns, a page at
# a time. Nothing scrolls.
const ROW_H := 26.0
## The day's sizes, roomiest first, as the board fitted them: big type or
## small, and the room inside a test, the first that ends above the window's foot.
const DAY_FITS := [[true, 24], [true, 16], [true, 10], [false, 12], [false, 8], [false, 4]]
## How a test's class is ordered, said at the foot of its page.
const ORDER := {"sprint": "Fastest first", "trial": "Fastest first", "leap": "Highest first", "kick": "Best first"}
var _pc := false
var _fitted := Vector2.ZERO
var _day_fit := 0
var _room: Control
var _laid_h := -1
var _pager: HBoxContainer


func _ready() -> void:
	name = "CombineScreen"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_pool = _whole_class()
	for t in Combine.TESTS:
		var key := str(t[0])
		_ranked[key] = Combine.ranked(_pool, key, draft.seed)
		_fields[key] = (_ranked[key] as Array).map(func(r): return float(r["result"]))
	var page := ColorRect.new()
	page.color = UiKit.BG
	page.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(page)
	page.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(ClubBackdrop.new().setup(club))
	_margin = MarginContainer.new()
	_margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_margin)
	_root = UiKit.vbox(UiKit.GAP)
	_margin.add_child(_root)
	_pc = _wide()
	_fitted = size
	resized.connect(_fit)
	_fit()
	_build()
	_return_to_place()


## The whole class, drafted or not: the day doesn't change once he's gone. A
## drafted man stays in the draft's pool as well as its picks: list him once.
func _whole_class() -> Array:
	var seen := {}
	var out := []
	for p in draft.pool + draft.picked.values():
		var id := str(p.get("id", ""))
		if not seen.has(id) and bool(p.get("projected", false)):
			seen[id] = true
			out.append(p)
	return out


## A phone column on a narrow window; on a PC, the whole window.
func _fit() -> void:
	UiKit.apply_insets(_margin, 12)
	if size != _fitted:
		_fitted = size
		var pc := _wide()
		if pc != _pc or (pc and _view() == "day"):
			_pc = pc
			_day_fit = 0
			_build.call_deferred()
	if _pc:
		_margin.add_theme_constant_override("margin_left", 16)
		_margin.add_theme_constant_override("margin_right", 16)
		return
	var spare := (size.x - MAX_WIDTH) * 0.5
	if spare > 12.0:
		_margin.add_theme_constant_override("margin_left", int(spare))
		_margin.add_theme_constant_override("margin_right", int(spare))


func _return_to_place() -> void:
	var at := int(place.get("scroll", 0))
	if at <= 0:
		return
	await get_tree().process_frame
	await get_tree().process_frame
	if is_instance_valid(_scroll):
		_scroll.scroll_vertical = at


func _wide() -> bool:
	return ScreenLayout.roomy(UiKit.view_width(self), UiKit.view_height(self))


func _view() -> String:
	return str(place.get("view", "day"))


func _role() -> String:
	return str(place.get("role", ""))


func _search() -> String:
	return str(place.get("search", ""))


func _shown() -> int:
	return int(place.get("shown", PAGE))


func close() -> void:
	if is_instance_valid(_scroll):
		place["scroll"] = _scroll.scroll_vertical
	closed.emit()
	queue_free()


func _build() -> void:
	UiKit.clear(_root)
	_root.add_child(UiKit.top_bar("The Combine", true, null, func() -> bool:
		close()
		return true))
	if _pc:
		_build_pc()
		return
	var tabs := UiKit.hbox(0)
	tabs.name = "CombineTabs"
	_root.add_child(tabs)
	for t in TABS:
		var key := str(t[0])
		var b := UiKit.tab(str(t[1]), _view() == key)
		b.name = "CombineTab_" + key
		b.custom_minimum_size.y = 44
		b.pressed.connect(_open_view.bind(key), CONNECT_DEFERRED)
		tabs.add_child(b)
	_body = UiKit.vbox(UiKit.GAP)
	_body.name = "CombineBody"
	_scroll = UiKit.scroll(_body)
	_scroll.name = "CombineScroll"
	_root.add_child(_scroll)
	if _view() == "day":
		_day()
	else:
		_test_board(_view())


func _open_view(key: String) -> void:
	place["view"] = key
	place["shown"] = PAGE
	place["page"] = 0
	place["scroll"] = 0
	_day_fit = 0
	_build()


# ---------------------------------------------------------------------------
# The day: who stood out, test by test.
# ---------------------------------------------------------------------------
func _day() -> void:
	var missed := Combine.untested(_pool, draft.seed).size()
	var said := "All %d prospects tested." % _pool.size()
	if missed > 0:
		said = "%d of %d prospects tested. %d missed testing, so there are no results for %s." % [
				_pool.size() - missed, _pool.size(), missed, "him" if missed == 1 else "them"]
	var count := _words(said, UiKit.TEXT)
	count.name = "CombineCount"
	_body.add_child(count)
	for t in Combine.TESTS:
		_headline(t)
	_turned_heads()
	_body.add_child(UiKit.rule())
	var note := _words("A quick time doesn't make a footballer. His junior football and our scouts' read are on his sheet: tap a name.",
			UiKit.TEXT, UiKit.SECONDARY)
	note.name = "CombineCaveat"
	_body.add_child(note)


## One test on the day: its name, what it says about his football, the best
## man, how far clear he was.
func _headline(t: Array) -> void:
	var key := str(t[0])
	var rows: Array = _ranked[key]
	_body.add_child(UiKit.rule())
	var head := UiKit.hbox(UiKit.GAP)
	head.name = "Headline_" + key
	_body.add_child(head)
	var name_l := UiKit.lbl(str(t[1]), UiKit.HEADING, StatsSide.mine_ink(), true)
	name_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(name_l)
	var all := UiKit.text_action("All results ›", UiKit.SECONDARY)
	all.name = "AllResults_" + key
	all.pressed.connect(_open_view.bind(key), CONNECT_DEFERRED)
	head.add_child(all)
	_body.add_child(_words(str(t[4]), UiKit.TEXT, UiKit.SECONDARY))
	if rows.is_empty():
		_body.add_child(_words("Nobody tested.", UiKit.MUTED))
		return
	_body.add_child(_row(rows[0], key))
	var next_name := GameDB.player_display_name(rows[1]["p"]) if rows.size() > 1 else ""
	var line := Combine.day_line(key, rows, next_name)
	if line != "":
		var l := _words(line, UiKit.TEXT, UiKit.SECONDARY)
		l.name = "DayLine_" + key
		_body.add_child(l)


## Prospects who stood out more than once: names worth remembering.
func _turned_heads() -> void:
	var rows := Combine.all_rounders(_pool, draft.seed)
	if rows.is_empty():
		return
	_body.add_child(UiKit.rule())
	_body.add_child(UiKit.lbl("Turned heads", UiKit.HEADING, StatsSide.mine_ink(), true))
	for r in rows:
		var p: Dictionary = r["p"]
		var b := _tap_row(p, Combine.top_ten_words(r["tests"]), "", "", -1)
		b.name = "TurnedHeads_" + str(p.get("id", ""))
		_body.add_child(b)


# ---------------------------------------------------------------------------
# One test: the whole class, best first.
# ---------------------------------------------------------------------------
func _test_board(key: String) -> void:
	var t := Combine.test(key)
	var head := UiKit.lbl(str(t[1]), UiKit.HEADING, StatsSide.mine_ink(), true)
	head.name = "CombineTest"
	_body.add_child(head)
	_body.add_child(_words(str(t[4]), UiKit.TEXT, UiKit.SECONDARY))
	var mid := Combine.middle(_ranked[key])
	if mid >= 0.0:
		var m := _words("The middle of the class: %s." % Combine.text(key, mid), UiKit.TEXT, UiKit.SECONDARY)
		m.name = "CombineMiddle"
		_body.add_child(m)
	var filters := UiKit.hbox(0)
	filters.name = "CombineRoles"
	_body.add_child(filters)
	for role in [""] + ROLES:
		var b := UiKit.tab("All" if role == "" else role, _role() == role)
		b.name = "CombineRole_" + (role if role != "" else "ALL")
		b.custom_minimum_size.y = 44
		b.pressed.connect(func():
			place["role"] = role
			place["shown"] = PAGE
			place["scroll"] = 0
			_build.call_deferred())
		filters.add_child(b)
	var field := UiKit.search_field(_search(), "Search prospects...")
	field.name = "CombineSearch"
	field.text_changed.connect(func(text: String):
		place["search"] = text
		place["shown"] = PAGE
		_fill_rows(key))
	_body.add_child(field)
	_rows = UiKit.vbox(0)
	_rows.name = "CombineRows"
	_body.add_child(_rows)
	_fill_rows(key)


func _matches(p: Dictionary) -> bool:
	if _role() != "" and str(p.get("role", "")) != _role():
		return false
	var q := _search().strip_edges().to_lower()
	return q == "" or GameDB.player_display_name(p).to_lower().contains(q)


func _fill_rows(key: String) -> void:
	UiKit.clear(_rows)
	var rows: Array = (_ranked[key] as Array).filter(func(r): return _matches(r["p"]))
	var missed: Array = Combine.untested(_pool, draft.seed).filter(func(p): return _matches(p))
	if rows.is_empty() and missed.is_empty():
		var none := _words("No prospects match.", UiKit.TEXT)
		none.name = "CombineNone"
		_rows.add_child(none)
		var clear := UiKit.btn("Clear", UiKit.SECONDARY)
		clear.name = "CombineClear"
		clear.custom_minimum_size.y = 44
		clear.pressed.connect(func():
			place["role"] = ""
			place["search"] = ""
			_build.call_deferred())
		_rows.add_child(clear)
		return
	var total := rows.size() + missed.size()
	for i in mini(_shown(), total):
		_rows.add_child(_row(rows[i], key) if i < rows.size() else _missed_row(missed[i - rows.size()]))
	if _shown() < total:
		var more := UiKit.btn("Show more  ·  %d of %d" % [_shown(), total], UiKit.SECONDARY)
		more.name = "CombineMore"
		more.custom_minimum_size.y = 44
		more.pressed.connect(func():
			place["shown"] = _shown() + PAGE
			_fill_rows.call_deferred(key))
		_rows.add_child(more)


# ---------------------------------------------------------------------------
# A PC: the board the director picked (UI batch 5, "four tests across").
# ---------------------------------------------------------------------------
func _build_pc() -> void:
	# The tabs, each sized to its words, the line under them running on.
	var strip := UiKit.hbox(0)
	strip.name = "CombineTabs"
	_root.add_child(strip)
	for t in TABS:
		var key := str(t[0])
		var b := UiKit.tab(str(t[1]), _view() == key)
		b.name = "CombineTab_" + key
		b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		b.custom_minimum_size.y = 44
		var sb := b.get_theme_stylebox("normal") as StyleBoxFlat
		sb.content_margin_left = 20
		sb.content_margin_right = 20
		b.pressed.connect(_open_view.bind(key), CONNECT_DEFERRED)
		strip.add_child(b)
	var run_on := Panel.new()
	run_on.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	run_on.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var under := StyleBoxFlat.new()
	under.bg_color = Color.TRANSPARENT
	under.border_width_bottom = 1
	under.border_color = UiKit.LINE
	run_on.add_theme_stylebox_override("panel", under)
	strip.add_child(run_on)
	_body = UiKit.vbox(0)
	_body.name = "CombineBody"
	_body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_room = null
	_pager = null
	if _view() == "day":
		# The day is sized to fit; the scroll is a last resort for a tiny window.
		_scroll = UiKit.scroll(_body)
		_scroll.name = "CombineScroll"
		_root.add_child(_scroll)
		_day_pc()
		_check_day_fit()
	else:
		_scroll = null
		_root.add_child(_body)
		_test_board_pc(_view())


## The roomiest of DAY_FITS that ends above the window's foot.
func _check_day_fit() -> void:
	var at := _day_fit
	for f in 2:
		await get_tree().process_frame
	if not is_instance_valid(_scroll) or not _pc or _view() != "day" or _day_fit != at:
		return
	if _body.get_combined_minimum_size().y > _scroll.size.y + 0.5 and _day_fit < DAY_FITS.size() - 1:
		_day_fit += 1
		_build()


## Room shared out between the day's sections.
func _slack() -> Control:
	var c := Control.new()
	c.size_flags_vertical = Control.SIZE_EXPAND_FILL
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


func _vrule() -> ColorRect:
	var r := ColorRect.new()
	r.color = UiKit.LINE
	r.custom_minimum_size = Vector2(1, 0)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


func _gap_w(w: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(w, 0)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


func _day_pc() -> void:
	var big: bool = DAY_FITS[_day_fit][0]
	var gap: int = DAY_FITS[_day_fit][1]
	var z := {"test": UiKit.H1 if big else UiKit.H2, "desc": UiKit.BODY if big else UiKit.SMALL,
			"name": UiKit.H1 if big else UiKit.H2, "res": 52 if big else 28, "line": UiKit.BODY if big else UiKit.SMALL}
	var missed := Combine.untested(_pool, draft.seed).size()
	var said := "All %d prospects tested." % _pool.size()
	if missed > 0:
		said = "%d of %d prospects tested. %d missed testing, so there are no results for %s." % [
				_pool.size() - missed, _pool.size(), missed, "him" if missed == 1 else "them"]
	var count := _words(said, UiKit.TEXT)
	count.name = "CombineCount"
	_body.add_child(count)
	_body.add_child(_slack())
	var across := UiKit.hbox((40 if UiKit.view_width(self) > 1000.0 else 20) / 2)
	across.name = "CombineDay"
	_body.add_child(across)
	for i in Combine.TESTS.size():
		if i > 0:
			across.add_child(_vrule())
		across.add_child(_test_pc(Combine.TESTS[i], z, gap))
	_body.add_child(_slack())
	_body.add_child(UiKit.rule())
	_body.add_child(_slack())
	var rows := Combine.all_rounders(_pool, draft.seed)
	if not rows.is_empty():
		var head := UiKit.lbl("Turned heads", z["test"], UiKit.TEXT, true)
		head.name = "TurnedHeadsTitle"
		_body.add_child(head)
		_body.add_child(UiKit.spacer(UiKit.Space.CLOSE))
		var three := UiKit.hbox(32)
		three.name = "TurnedHeads"
		_body.add_child(three)
		for r in rows:
			var p: Dictionary = r["p"]
			var v := UiKit.vbox(UiKit.Space.SLIM)
			var who := UiKit.hbox(UiKit.GAP)
			v.add_child(who)
			var role := _role_line(p)
			role.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			who.add_child(role)
			who.add_child(UiKit.line(GameDB.player_display_name(p), int(z["name"]) - 3, UiKit.TEXT, true))
			v.add_child(_words(Combine.top_ten_words(r["tests"]), UiKit.TEXT, z["line"]))
			var b := _tap_box(p, v)
			b.name = "TurnedHeads_" + str(p.get("id", ""))
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			three.add_child(b)
		for i in range(rows.size(), 3):
			var keep := Control.new()
			keep.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			three.add_child(keep)
		_body.add_child(_slack())
	var note := _words("A quick time doesn't make a footballer. His junior football and our scouts' read are on his sheet: tap a name.",
			UiKit.MUTED, z["line"])
	note.name = "CombineCaveat"
	_body.add_child(note)
	_body.add_child(UiKit.spacer(UiKit.Space.LOOSE))


## One test on the day: its name, what it says about his football, the best
## man and his figure, the line on how clear he was, and the way to the rest.
func _test_pc(t: Array, z: Dictionary, gap: int) -> Control:
	var key := str(t[0])
	var rows: Array = _ranked[key]
	var v := UiKit.vbox(0)
	v.name = "Headline_" + key
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var title := UiKit.lbl(str(t[1]), z["test"], UiKit.TEXT, true)
	title.name = "TestName"
	v.add_child(title)
	v.add_child(UiKit.spacer(UiKit.Space.CLOSE))
	v.add_child(_words(str(t[4]), UiKit.TEXT, z["desc"]))
	v.add_child(UiKit.spacer(gap))
	if rows.is_empty():
		v.add_child(_words("Nobody tested.", UiKit.MUTED, z["line"]))
	else:
		var p: Dictionary = rows[0]["p"]
		var best := UiKit.vbox(UiKit.Space.SLIM)
		var tag := UiKit.hbox(UiKit.GAP)
		best.add_child(tag)
		tag.add_child(_role_line(p))
		tag.add_child(UiKit.ellipsis(_kind(p), UiKit.SMALL, UiKit.MUTED))
		best.add_child(UiKit.lbl(GameDB.player_display_name(p), z["name"], UiKit.TEXT, true))
		var fig := UiKit.hbox(UiKit.Space.ROOM)
		best.add_child(fig)
		var f := UiKit.figure(Combine.text(key, float(rows[0]["result"])), z["res"], UiKit.HEAD_DARK)
		f.name = "Result"
		fig.add_child(f)
		var said := UiKit.line("Best in the class", UiKit.SMALL, UiKit.MUTED)
		said.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		fig.add_child(said)
		var b := _tap_box(p, best)
		b.name = "Prospect_%s" % str(p.get("id", ""))
		v.add_child(b)
		v.add_child(UiKit.spacer(gap))
		var next_name := GameDB.player_display_name(rows[1]["p"]) if rows.size() > 1 else ""
		var line := Combine.day_line(key, rows, next_name)
		if line != "":
			var l := _words(line, UiKit.TEXT, z["line"])
			l.name = "DayLine_" + key
			v.add_child(l)
			v.add_child(UiKit.spacer(maxi(2, gap - 4)))
	var all := UiKit.text_action("All results ›", UiKit.BODY)
	all.name = "AllResults_" + key
	all.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	all.custom_minimum_size.y = 32
	(all.get_theme_stylebox("normal") as StyleBoxFlat).content_margin_left = 0
	all.pressed.connect(_open_view.bind(key), CONNECT_DEFERRED)
	v.add_child(all)
	return v


## One test's class: its name and what it says, the middle of the class at the
## right, the position filters and the search, then the class in one-line rows,
## two columns, as many to a column as the window holds, a page at a time.
func _test_board_pc(key: String) -> void:
	var t := Combine.test(key)
	var head := UiKit.hbox(UiKit.Space.OPEN)
	head.name = "CombineHead"
	_body.add_child(head)
	var name_l := UiKit.line(str(t[1]), UiKit.H2, UiKit.TEXT, true)
	name_l.name = "CombineTest"
	head.add_child(name_l)
	var desc := UiKit.ellipsis(str(t[4]), UiKit.SMALL, UiKit.TEXT)
	desc.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(desc)
	var mid := Combine.middle(_ranked[key])
	if mid >= 0.0:
		var m := UiKit.line("The middle of the class: %s." % Combine.text(key, mid), UiKit.SMALL, UiKit.TEXT, true)
		m.name = "CombineMiddle"
		m.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		head.add_child(m)
	_body.add_child(UiKit.spacer(UiKit.Space.ROOM))
	var filters := UiKit.hbox(UiKit.Space.CLOSE)
	filters.name = "CombineRoles"
	_body.add_child(filters)
	for role in [""] + ROLES:
		filters.add_child(_role_box(role))
	filters.add_child(_gap_w(UiKit.Space.ROOM))
	var field := UiKit.search_field(_search(), "Search prospects...")
	field.name = "CombineSearch"
	field.custom_minimum_size = Vector2(300, 32)
	field.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	UiKit.set_font_size(field, UiKit.SMALL)
	field.text_changed.connect(func(text: String):
		place["search"] = text
		place["page"] = 0
		_fill_pc_rows(key))
	filters.add_child(field)
	_body.add_child(UiKit.spacer(UiKit.Space.PAD))
	# The rows' room is whatever the page leaves; the rows never set its
	# height, so filling it again on a resize can't move it.
	_room = Control.new()
	_room.name = "CombineRoom"
	_room.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_room.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_room.clip_contents = true
	_room.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_body.add_child(_room)
	_rows = UiKit.hbox(32)
	_rows.name = "CombineRows"
	_rows.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_room.add_child(_rows)
	_pager = UiKit.hbox(UiKit.Space.LOOSE)
	_pager.name = "CombinePager"
	_pager.custom_minimum_size.y = 32
	_body.add_child(_pager)
	_laid_h = -1
	var room := _room
	room.resized.connect(func():
		if is_instance_valid(room) and int(room.size.y) > 0 and int(room.size.y) != _laid_h:
			_laid_h = int(room.size.y)
			_fill_pc_rows(key))


## A position filter as the board boxed it: the one on outlined in TEXT on the
## well, the rest on the raised surface in their position's colour.
func _role_box(role: String) -> Button:
	var on := _role() == role
	var b := UiKit.btn("All" if role == "" else role, UiKit.SMALL)
	b.name = "CombineRole_" + (role if role != "" else "ALL")
	b.custom_minimum_size = Vector2(UiKit.BOLD.get_string_size(b.text, HORIZONTAL_ALIGNMENT_LEFT, -1,
			UiKit.px(UiKit.SMALL)).x + 32.0, 32)
	b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var sb := UiKit.style(UiKit.INK if on else UiKit.PANEL_ALT, 0, 4, UiKit.TEXT if on else UiKit.LINE)
	for state in ["normal", "hover", "pressed", "hover_pressed"]:
		b.add_theme_stylebox_override(state, sb)
	b.add_theme_stylebox_override("focus", UiKit.focus_ring())
	var ink: Color = UiKit.TEXT if role == "" else UiKit.ROLE_COLOUR.get(role, UiKit.MUTED)
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(c, ink)
	b.pressed.connect(func():
		place["role"] = role
		place["page"] = 0
		_build.call_deferred())
	return b


func _fill_pc_rows(key: String) -> void:
	if not is_instance_valid(_room) or not is_instance_valid(_rows):
		return
	for c in _rows.get_children():
		_rows.remove_child(c)
		c.queue_free()
	for c in _pager.get_children():
		_pager.remove_child(c)
		c.queue_free()
	var rows: Array = (_ranked[key] as Array).filter(func(r): return _matches(r["p"]))
	var missed: Array = Combine.untested(_pool, draft.seed).filter(func(p): return _matches(p))
	var total := rows.size() + missed.size()
	if total == 0:
		var v := UiKit.vbox(UiKit.Space.ROOM)
		_rows.add_child(v)
		var none := _words("No prospects match.", UiKit.TEXT)
		none.name = "CombineNone"
		v.add_child(none)
		var clear := UiKit.btn("Clear", UiKit.SECONDARY)
		clear.name = "CombineClear"
		clear.custom_minimum_size = Vector2(120, 44)
		clear.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		clear.pressed.connect(func():
			place["role"] = ""
			place["search"] = ""
			place["page"] = 0
			_build.call_deferred())
		v.add_child(clear)
		return
	var per := maxi(1, int(_room.size.y / ROW_H))
	var per_page := per * 2
	var pages := ceili(float(total) / float(per_page))
	var page := clampi(int(place.get("page", 0)), 0, pages - 1)
	place["page"] = page
	var wide := (_room.size.x - 32.0) * 0.5 >= 500.0
	var first := page * per_page
	var last := mini(total, first + per_page)
	for c in 2:
		var col := UiKit.vbox(0)
		col.name = "CombineColumn_%d" % c
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_rows.add_child(col)
		for i in range(first + c * per, mini(last, first + (c + 1) * per)):
			if i < rows.size():
				var r: Dictionary = rows[i]
				var v := float(r["result"])
				var b := _line_row(r["p"], str(int(r["rank"])), Combine.text(key, v),
						Combine.standing(key, v, _fields[key]), wide)
				b.name = "Prospect_%s" % str(r["p"].get("id", ""))
				col.add_child(b)
			else:
				var p: Dictionary = missed[i - rows.size()]
				var b := _line_row(p, "", "", "Did not test", wide)
				b.name = "Missed_%s" % str(p.get("id", ""))
				col.add_child(b)
	var info := UiKit.line("%s  ·  %d-%d of %d" % [ORDER.get(key, "Best first"), first + 1, last, total],
			UiKit.SMALL, UiKit.MUTED)
	info.name = "CombinePageInfo"
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_pager.add_child(info)
	if page > 0:
		_pager.add_child(_page_link("CombinePrev", "‹ Previous %d" % per_page, key, page - 1))
	if last < total:
		_pager.add_child(_page_link("CombineNext", "Next %d ›" % mini(per_page, total - last), key, page + 1))


func _page_link(node_name: String, text: String, key: String, to: int) -> Button:
	var b := UiKit.text_action(text, UiKit.BODY)
	b.name = node_name
	b.custom_minimum_size.y = 32
	b.pressed.connect(func():
		place["page"] = to
		_fill_pc_rows.call_deferred(key))
	return b


## One prospect on one line: his place, position, name and how he plays, then
## his figure and where it stands. A tap anywhere on it opens his sheet.
func _line_row(p: Dictionary, rank: String, figure: String, standing: String, wide: bool) -> Button:
	var id := str(p.get("id", ""))
	var b := Button.new()
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size.y = ROW_H
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	b.set_meta("prospect_id", id)
	b.pressed.connect(func(): inspect.emit(id))
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color.TRANSPARENT
	sb.border_width_bottom = 1
	sb.border_color = UiKit.LINE
	var hv := sb.duplicate() as StyleBoxFlat
	hv.bg_color = Color(UiKit.TEXT, 0.05)
	for state in ["normal", "pressed", "focus"]:
		b.add_theme_stylebox_override(state, sb)
	b.add_theme_stylebox_override("hover", hv)
	b.add_theme_stylebox_override("hover_pressed", hv)
	var face := UiKit.hbox(0)
	face.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	b.add_child(face)
	var place_l := _cell(rank, UiKit.SMALL, UiKit.MUTED, false, 18.0, HORIZONTAL_ALIGNMENT_RIGHT)
	place_l.name = "Rank"
	face.add_child(place_l)
	face.add_child(_gap_w(UiKit.GAP))
	var tag := Ratings.role_tag(p)
	face.add_child(_cell(tag, UiKit.SMALL, UiKit.ROLE_COLOUR.get(tag.split("/")[0], UiKit.MUTED), true,
			64.0 if wide else 56.0, HORIZONTAL_ALIGNMENT_LEFT))
	var who := _cell(GameDB.player_display_name(p), UiKit.BODY, UiKit.MUTED if draft.has(id) else UiKit.TEXT, true,
			142.0 if wide else 119.0, HORIZONTAL_ALIGNMENT_LEFT)
	who.name = "PlayerName"
	who.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	face.add_child(who)
	var kind := _cell(_kind(p), UiKit.SMALL, UiKit.MUTED, false, 0.0, HORIZONTAL_ALIGNMENT_LEFT)
	kind.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	kind.clip_text = true
	kind.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	face.add_child(kind)
	var res := _cell(figure, UiKit.BODY, UiKit.TEXT, true, 0.0, HORIZONTAL_ALIGNMENT_RIGHT)
	res.name = "Result"
	face.add_child(res)
	var st := _cell(standing, UiKit.SMALL, UiKit.MUTED, false, 110.0 if wide else 93.0, HORIZONTAL_ALIGNMENT_RIGHT)
	st.name = "Standing"
	face.add_child(st)
	_ignore_mouse(face)
	return b


func _cell(text: String, fs: int, colour: Color, bold: bool, w: float, align: HorizontalAlignment) -> Label:
	var l := UiKit.line(text, fs, colour, bold)
	l.custom_minimum_size.x = w
	l.horizontal_alignment = align
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.size_flags_vertical = Control.SIZE_FILL
	l.clip_text = w > 0.0
	return l


## His position in its colour, as a word (no box).
func _role_line(p: Dictionary) -> Label:
	var tag := Ratings.role_tag(p)
	return UiKit.line(tag, UiKit.SMALL, UiKit.ROLE_COLOUR.get(tag.split("/")[0], UiKit.MUTED), true)


## A block that opens his sheet on a tap, as tall as what it holds.
func _tap_box(p: Dictionary, content: Control) -> Button:
	var b := Button.new()
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var id := str(p.get("id", ""))
	b.set_meta("prospect_id", id)
	b.pressed.connect(func(): inspect.emit(id))
	var clear := StyleBoxEmpty.new()
	for state in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		b.add_theme_stylebox_override(state, clear)
	content.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	b.add_child(content)
	_ignore_mouse(content)
	var grow := func(): b.custom_minimum_size.y = content.get_combined_minimum_size().y
	content.minimum_size_changed.connect(grow)
	grow.call()
	return b


# ---------------------------------------------------------------------------
# A prospect's row: a tap anywhere on it opens his sheet.
# ---------------------------------------------------------------------------
func _row(r: Dictionary, key: String) -> Control:
	var p: Dictionary = r["p"]
	var v := float(r["result"])
	var b := _tap_row(p, _kind(p), Combine.text(key, v),
			Combine.standing(key, v, _fields[key]), int(r["rank"]))
	b.name = "Prospect_%s" % str(p.get("id", ""))
	return b


func _missed_row(p: Dictionary) -> Control:
	var b := _tap_row(p, _kind(p), "", "Did not test", 0)
	b.name = "Missed_%s" % str(p.get("id", ""))
	return b


## How he plays; once he's gone, where he went.
func _kind(p: Dictionary) -> String:
	var id := str(p.get("id", ""))
	if draft.has(id):
		var went := draft.drafted_by(id)
		var pick := int(draft.pick_details(id).get("pick", 0))
		if went == club:
			return "Pick %d, on our list" % pick
		return "Pick %d, %s" % [pick, GameDB.club_name(went)]
	return PlayerProfile.player_type(p)


## `rank`: his place on a board; 0 keeps the column empty so his name lines up
## with the ranked rows; below 0 there is no column at all.
func _tap_row(p: Dictionary, under: String, figure: String, standing: String, rank: int) -> Button:
	var b := Button.new()
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size.y = 60
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var id := str(p.get("id", ""))
	b.set_meta("prospect_id", id)
	b.pressed.connect(func(): inspect.emit(id))
	var face := UiKit.hbox(UiKit.GAP)
	face.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	b.add_child(face)
	if rank >= 0:
		var ranks := UiKit.line(str(rank) if rank > 0 else "", UiKit.NAME, UiKit.MUTED, true)
		ranks.name = "Rank"
		ranks.custom_minimum_size.x = 28
		ranks.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		face.add_child(ranks)
	var who := UiKit.vbox(UiKit.Space.SLIM)
	who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	who.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	face.add_child(who)
	var top := UiKit.hbox(UiKit.Space.CLOSE)
	who.add_child(top)
	var chip := UiKit.role_chip_for(p)
	chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	top.add_child(chip)
	var name_l := UiKit.name_label(GameDB.player_display_name(p), UiKit.NAME,
			UiKit.MUTED if draft.has(id) else UiKit.TEXT)
	name_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(name_l)
	who.add_child(_words(under, UiKit.MUTED, UiKit.SECONDARY))
	if figure != "" or standing != "":
		var right := UiKit.vbox(0)
		right.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		face.add_child(right)
		if figure != "":
			var f := UiKit.line(figure, UiKit.NAME, UiKit.TEXT, true)
			f.name = "Result"
			f.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			right.add_child(f)
		var s := UiKit.line(standing, UiKit.FINE, UiKit.MUTED)
		s.name = "Standing"
		s.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		right.add_child(s)
	_ignore_mouse(face)
	var grow := func(): b.custom_minimum_size.y = maxf(60.0, face.get_combined_minimum_size().y + 8.0)
	face.minimum_size_changed.connect(grow)
	grow.call_deferred()
	return b


static func _words(text: String, colour: Color, fs := UiKit.BODY) -> Label:
	var l := UiKit.lbl(text, fs, colour)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


func _ignore_mouse(node: Control) -> void:
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for child in node.get_children():
		if child is Control:
			_ignore_mouse(child)
