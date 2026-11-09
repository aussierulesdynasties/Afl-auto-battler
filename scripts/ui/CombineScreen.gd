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
var _rows: VBoxContainer


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
	_root = UiKit.vbox(8)
	_margin.add_child(_root)
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


## A phone column on a wide window.
func _fit() -> void:
	UiKit.apply_insets(_margin, 12)
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
	_body = UiKit.vbox(8)
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
	place["scroll"] = 0
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
	var note := _words("A quick time doesn't make a footballer. His junior football and your scouts' read are on his sheet: tap a name.",
			UiKit.TEXT, UiKit.SECONDARY)
	note.name = "CombineCaveat"
	_body.add_child(note)


## One test on the day: its name, what it says about his football, the best
## man, how far clear he was.
func _headline(t: Array) -> void:
	var key := str(t[0])
	var rows: Array = _ranked[key]
	_body.add_child(UiKit.rule())
	var head := UiKit.hbox(8)
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
			return "Pick %d, on your list" % pick
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
	var face := UiKit.hbox(8)
	face.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	b.add_child(face)
	if rank >= 0:
		var ranks := UiKit.line(str(rank) if rank > 0 else "", UiKit.NAME, UiKit.MUTED, true)
		ranks.name = "Rank"
		ranks.custom_minimum_size.x = 28
		ranks.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		face.add_child(ranks)
	var who := UiKit.vbox(2)
	who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	who.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	face.add_child(who)
	var top := UiKit.hbox(6)
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
