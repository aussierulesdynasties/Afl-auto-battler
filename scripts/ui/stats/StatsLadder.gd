class_name StatsLadder
extends RefCounted
## Season stats > Ladder: the full ladder in its true order (Season.ladder_sorted,
## the real tiebreaks), a second view of each club's per-game team numbers, a
## tap on a header to sort and a few simple filters. Tap a club for its side on
## the field view, read-only. The sort, the filter and the view are kept for
## the visit back from a club's side (STATS patch, ROADMAP §1.11).

## Rows are 32 px on a wide screen, 40 px (thumb-sized) on a narrow one, with no
## rules between them; every other row has a very faint
## band (PANEL, flat). Numbers and their headers are right-aligned.
const ROW_H := 32
## A phone's row opens a club: thumb high (CLAUDE.md "Mobile first").
const ROW_H_NARROW := 44
const COL_GAP := 4
## A full-width (phone) table keeps its last column's words this far in from
## the band's edge.
const END_PAD := 8

## The ladder's columns, phone first; a wide screen adds the rest.
## {key, title, w}; on a phone the club column takes what is left (0). On a
## wide screen the table is as wide as its columns and sits at the left, the
## club right beside its numbers (WIDE_CLUB).
const WIDE_CLUB := 190
## "Rating": the club's match-day side today on the OVR scale (TeamRating). A
## tap on a club says it in full: where the club is in its cycle (Contender,
## Wildcard, Rebuilding) and the list in three years.
const CLUB_NAME_INSET := 26
const LADDER_PHONE := [["pos", "#", 24], ["club", "Club", 0], ["p", "P", 26], ["w", "W", 26],
		["l", "L", 26], ["d", "D", 24], ["pct", "%", 42], ["pts", "Pts", 34], ["rating", "Rating", 46]]
const LADDER_WIDE := [["pos", "#", 44], ["club", "Club", WIDE_CLUB], ["p", "P", 32], ["w", "W", 32],
		["l", "L", 32], ["d", "D", 30], ["pf", "PF", 50], ["pa", "PA", 50], ["pct", "%", 50],
		["pts", "Pts", 40], ["home", "Home", 68], ["away", "Away", 68], ["form", "Form", 76],
		["rating", "Rating", 52]]
## A small phone (under PHONE_TIGHT units of content, e.g. 320 units on a
## scaled desktop window) keeps every phone column at tighter widths, so the
## club column keeps room for its guernsey and the header stays over its rows
## (row 84: at 296 units the club column fell to 0 in the header and to the
## guernsey's width in the rows, one column off).
const PHONE_TIGHT := 340.0
const LADDER_TIGHT := [["pos", "#", 20], ["club", "Club", 0], ["p", "P", 22], ["w", "W", 22],
		["l", "L", 22], ["d", "D", 20], ["pct", "%", 36], ["pts", "Pts", 30], ["rating", "Rating", 44]]
## The least a phone's club column takes, header and rows alike: a guernsey.
const CLUB_MIN_NARROW := 28
## Team stats: a per-game value for each, from GameState.season_team (only
## what is recorded there). One list, so a newly recorded stat joins with one
## line: {season_team key, column title, width on a phone, width on a wide
## screen, on a phone}.
const TEAM_STATS := [
	["for", "PF", 32, 46, true], ["against", "PA", 32, 46, true],
	["disposals", "D", 32, 46, true], ["marks", "MK", 32, 46, true],
	["tackles", "TK", 32, 46, true], ["inside50", "I50", 32, 46, true],
	["clearances", "CL", 32, 46, true], ["hitouts", "HO", 32, 46, true],
	["contested_possessions", "CP", 32, 46, false], ["ground_ball_gets", "GBG", 32, 46, false],
	["rebounds", "R50", 32, 46, false], ["clangers", "CG", 32, 46, false],
	["metres_gained", "MG", 32, 56, false],
]
## Metres gained reads well rounded; every other figure is one decimal.
const WHOLE_STATS := ["metres_gained"]

## Team stats as a leaderboard (visual audit Phase 2, guide 4.5): one fact
## at a time, chosen by name from three views of a club's game, each club with
## the view's other two facts beside it and a bar against the league's best.
## {view key, view name, [[season_team key, the fact's name], ...]}.
const TEAM_FACTS := [
	["attack", "Attack", [["for", "Points for"], ["inside50", "Inside 50s"], ["goals", "Goals"]]],
	["defence", "Defence", [["against", "Points against"], ["tackles", "Tackles"], ["rebounds", "Rebound 50s"]]],
	["contest", "Contest", [["contested_possessions", "Contested possessions"], ["clearances", "Clearances"],
			["hitouts", "Hit-outs"]]],
]
## Facts where fewer is better: the best club is the one with the fewest.
const TEAM_LOW := ["against"]
## Few enough a game that a tenth tells two clubs apart; every other figure is whole.
const TEAM_TENTHS := ["goals"]
## The longest a bar gets (the league's best), so it reads the same on a phone and a PC.
const TEAM_BAR_MAX := 360.0

const FILTERS := [["all", "All"], ["top10", "Top 10"], ["near", "Near you"]]
const VIEWS := [["ladder", "Ladder"], ["team", "Team stats"]]

## Kept across a rebuild and a visit to a club's side. "" sorts nothing: the
## true ladder order.
static var _view := "ladder"
static var _sort := ""
static var _desc := true
static var _filter := "all"
static var _team_fact := "for"


static func reset() -> void:
	_view = "ladder"
	_sort = ""
	_desc = true
	_filter = "all"
	_team_fact = "for"


static func build(host: Control) -> Control:
	var season: Season = GameState.season
	var v := UiKit.vbox(10)
	v.name = "StatsLadder"
	# The round is in the page's headline now (StatsHubScene._hero).
	var wide := bool(host.call("wide"))
	var width := float(host.call("content_width"))

	# The view, as one line of words (the kit's choice idiom), then the filters.
	var views := UiKit.segmented("View", VIEWS, _view, func(key: String):
		_view = key
		_sort = ""
		host.call("refresh"))
	views.name = "Views"
	var filters := UiKit.hbox(6)
	filters.name = "Filters"
	for o in FILTERS:
		var key := str(o[0])
		var b := UiKit.btn(str(o[1]), UiKit.BODY)
		b.name = "Filter_" + key
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size.y = 44
		UiKit.set_selected(b, key == _filter)
		b.pressed.connect(func():
			_filter = key
			host.call("refresh"))
		filters.add_child(b)
	if _view == "team":
		# The team leaderboard has its own picker; the ladder's filters are the ladder's.
		v.add_child(views)
		v.add_child(_team_board(host, season, wide))
		return v
	if wide:
		# One compact row on a wide screen, not two bars across the window.
		for b in filters.get_children():
			b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
			b.custom_minimum_size.x = 120
		var both := UiKit.hbox(28)
		both.name = "Controls"
		both.add_child(views)
		both.add_child(filters)
		v.add_child(both)
	else:
		v.add_child(views)
		v.add_child(filters)

	var shown := visible_rows(season, GameState.my_club, _filter, _sort, _desc, _view)
	# Only when something is filtered or sorted: the whole ladder says so itself.
	var specs := fit(columns(_view, wide, width), rows(season))
	if _filter != "all" or _sort != "":
		var status := _status(host, shown.size())
		if wide:
			# Its buttons end where the table's columns end, not past them.
			status.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
			status.custom_minimum_size.x = table_width(specs)
		v.add_child(status)

	# No panel around it: the bands do the work.
	var t := UiKit.vbox(0)
	t.name = "LadderTable"
	v.add_child(t)
	if wide:
		# As wide as its columns, left-aligned: no gap between a club and its numbers.
		t.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	t.add_child(_header(host, specs, width, wide))
	var band := false
	for r in shown:
		t.add_child(_row(host, r, specs, width, band, ROW_H if wide else ROW_H_NARROW))
		band = not band
		# The cut for the finals, as the ladder has always drawn it.
		if _sort == "" and _filter == "all" and int(r["pos"]) == Season.FINALISTS 				and int(r["pos"]) < season.ladder.size():
			t.add_child(UiKit.rule())
	if shown.is_empty():
		t.add_child(UiKit.lbl("No clubs to show.", UiKit.BODY, UiKit.MUTED))
	return v


static func columns(view: String, wide: bool, width := 9999.0) -> Array:
	if view == "team":
		var out := [["club", "Club", WIDE_CLUB if wide else 0]]
		for c in TEAM_STATS:
			if wide or bool(c[4]):
				out.append([c[0], c[1], c[3] if wide else c[2]])
		return out
	if wide:
		return LADDER_WIDE
	return LADDER_TIGHT if width < PHONE_TIGHT else LADDER_PHONE


## Each fixed column as wide as its title and its widest figure need at the
## text size (Settings): a larger size widens the columns and the club column,
## which takes what is left, gives up the room. Never narrower than its spec.
static func fit(specs: Array, rows: Array) -> Array:
	var fs := UiKit.px(UiKit.FINE)
	var out := []
	for c in specs:
		var key := str(c[0])
		var w := int(c[2])
		if w > 0 and key != "club" and key != "form":
			var need := UiKit.BOLD.get_string_size(str(c[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			for r in rows:
				need = maxf(need, UiKit.BOLD.get_string_size(cell_text(r, key),
						HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x)
			if c == specs[-1] and not _all_fixed(specs):
				need += END_PAD
			w = maxi(w, ceili(need) + 2)
		out.append([c[0], c[1], w])
	return out


## The least width of a table of these columns: the sum the rows are sized to.
static func table_width(specs: Array) -> float:
	var fixed := 0
	var all_fixed := true
	for c in specs:
		if int(c[2]) == 0:
			all_fixed = false
		fixed += maxi(int(c[2]), CLUB_MIN_NARROW if int(c[2]) == 0 else 0) + COL_GAP
	return float(fixed if all_fixed else fixed - COL_GAP)


## One line that says what is on show, with the way back to the plain ladder.
static func _status(host: Control, count: int) -> Control:
	var h := UiKit.hbox(8)
	h.name = "LadderStatus"
	var bits := PackedStringArray()
	for o in FILTERS:
		if str(o[0]) == _filter and _filter != "all":
			bits.append(str(o[1]))
	if _sort != "":
		var ends := ["Z–A", "A–Z"] if _sort == "club" else ["most", "fewest"]
		bits.append("sorted by %s, %s first" % [_title_of(_sort), ends[0] if _desc else ends[1]])
	var text := "Showing " + (", ".join(bits) if not bits.is_empty() else "all %d clubs" % count)
	var l := UiKit.lbl(text, UiKit.SMALL, UiKit.MUTED)
	l.name = "ActiveState"
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(l)
	if _sort != "":
		var order := UiKit.btn("Ladder order", UiKit.SMALL)
		order.name = "LadderOrder"
		order.pressed.connect(func():
			_sort = ""
			host.call("refresh"))
		h.add_child(order)
	if _sort != "" or _filter != "all":
		var rs := UiKit.btn("Reset", UiKit.SMALL)
		rs.name = "ResetLadder"
		rs.pressed.connect(func():
			_sort = ""
			_desc = true
			_filter = "all"
			host.call("refresh"))
		h.add_child(rs)
	return h


static func _title_of(key: String) -> String:
	for set in [LADDER_WIDE, TEAM_STATS]:
		for c in set:
			if str(c[0]) == key:
				return str(c[1])
	return key


static func _header(host: Control, specs: Array, width: float, wide := false) -> Control:
	var h := UiKit.hbox(COL_GAP)
	h.name = "LadderHeader"
	for c in specs:
		var key := str(c[0])
		if key == "form":
			h.add_child(_plain(str(c[1]), int(c[2]), UiKit.MUTED))
			continue
		var b := Button.new()
		b.name = "Sort_" + key
		b.text = str(c[1])
		b.flat = true
		b.clip_text = true
		b.mouse_filter = Control.MOUSE_FILTER_PASS
		b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		b.add_theme_font_override("font", UiKit.BOLD if key == _sort else UiKit.FONT)
		UiKit.set_font_size(b, UiKit.FINE)
		var on: bool = key == _sort
		for col in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
			b.add_theme_color_override(col, UiKit.TEXT if on else UiKit.MUTED)
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color.TRANSPARENT
		sb.border_width_bottom = 2 if on else 0
		sb.border_color = UiKit.TEXT
		if key == "club":
			# Over the names, not the crests before them: the crest's 20 px plus
			# the badge's 6 px gap (UiKit.club_badge, club_marker).
			sb.content_margin_left = CLUB_NAME_INSET
		if c == specs[-1] and not _all_fixed(specs):
			sb.content_margin_right = END_PAD
		for state in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
			b.add_theme_stylebox_override(state, sb)
		# A thumb-high header on a phone (44 px, CLAUDE.md "Mobile first"); the
		# columns keep their widths. A wide screen keeps 40.
		b.custom_minimum_size = Vector2(int(c[2]), 40 if wide else 44)
		if int(c[2]) == 0:
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			b.custom_minimum_size.x = CLUB_MIN_NARROW
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT if key == "club" else HORIZONTAL_ALIGNMENT_RIGHT
		b.pressed.connect(func(): _sort_by(host, key))
		h.add_child(b)
	return h


static func _all_fixed(specs: Array) -> bool:
	for c in specs:
		if int(c[2]) == 0:
			return false
	return true


static func _plain(text: String, w: int, col: Color) -> Label:
	var l := UiKit.line(text, UiKit.FINE, col)
	l.custom_minimum_size = Vector2(w, 0)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	return l


## Tap a header: that column, biggest first (names A to Z); tap it again to
## reverse. The position column is the way back to the true order.
static func _sort_by(host: Control, key: String) -> void:
	if key == "pos":
		_sort = ""
		_desc = true
	elif key == _sort:
		_desc = not _desc
	else:
		_sort = key
		_desc = key != "club"
	host.call("refresh")


## One club as a tappable row.
static func _row(host: Control, r: Dictionary, specs: Array, width: float, band := false, height := ROW_H) -> Control:
	var code := str(r["code"])
	var mine: bool = code == GameState.my_club
	var b := Button.new()
	b.name = "Club_" + code
	b.mouse_filter = Control.MOUSE_FILTER_PASS
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	# A button does not take its child row's width: a table of fixed columns says so.
	# Every row is as wide as the header's least, so the two share one width.
	b.custom_minimum_size = Vector2(table_width(specs), height)
	b.clip_contents = true
	var flat := StyleBoxFlat.new()
	flat.bg_color = UiKit.PANEL if band else Color.TRANSPARENT
	if mine:
		# Your club's row in your colour, as the hub's ladder marks it.
		flat.bg_color = Color(UiKit.club_vivid(code), 0.22)
		flat.border_width_left = 4
		flat.border_color = UiKit.club_vivid(code)
	var hover := StyleBoxFlat.new()
	hover.bg_color = Color(UiKit.TEXT, 0.05)
	for state in ["normal", "focus"]:
		b.add_theme_stylebox_override(state, flat)
	for state in ["hover", "pressed", "hover_pressed"]:
		b.add_theme_stylebox_override(state, hover)
	var row := UiKit.hbox(COL_GAP)
	b.add_child(row)
	row.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for c in specs:
		var key := str(c[0])
		var w := int(c[2])
		if key == "club":
			var badge := UiKit.club_badge(code, 13, width < 460.0, true)
			if w > 0:
				badge.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
				badge.alignment = BoxContainer.ALIGNMENT_BEGIN
				badge.custom_minimum_size.x = w
			else:
				badge.custom_minimum_size.x = CLUB_MIN_NARROW
			if mine:
				_bold(badge)
			row.add_child(badge)
			continue
		var text := cell_text(r, key)
		# The position is muted, so is a zero; the rest is plain text.
		var ink := UiKit.MUTED if key == "pos" or _is_zero(text) else UiKit.TEXT
		var l := UiKit.line(text, UiKit.FINE, ink, mine or key == "pts")
		l.custom_minimum_size = Vector2(w, 0)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		if c == specs[-1] and not _all_fixed(specs):
			# Off the band's edge, as the header's last label is (_header).
			var pad := StyleBoxEmpty.new()
			pad.content_margin_right = END_PAD
			l.add_theme_stylebox_override("normal", pad)
		row.add_child(l)
	_ignore(row)
	b.pressed.connect(func(): ClubLink.open(host, code))
	return b


## "0", "0.0": nothing to read.
static func _is_zero(text: String) -> bool:
	return text.is_valid_float() and float(text) == 0.0


static func _bold(n: Node) -> void:
	if n is Label:
		(n as Label).add_theme_font_override("font", UiKit.BOLD)
	for c in n.get_children():
		_bold(c)


static func _ignore(n: Node) -> void:
	if n is Control:
		(n as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	for c in n.get_children():
		_ignore(c)


# ---------------------------------------------------------------------------
# Team stats: a leaderboard
# ---------------------------------------------------------------------------
## The picker (each view's three facts under its name), then every club ranked
## on the chosen fact, a game.
static func _team_board(host: Control, season: Season, wide: bool) -> Control:
	var v := UiKit.vbox(8)
	v.name = "TeamBoard"
	var pick := UiKit.option()
	pick.name = "TeamStat"
	pick.custom_minimum_size = Vector2(260 if wide else 0, 44)
	if wide:
		pick.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	for view in TEAM_FACTS:
		pick.add_separator(str(view[1]))
		for f in view[2]:
			pick.add_item(str(f[1]))
			var at := pick.item_count - 1
			pick.set_item_metadata(at, str(f[0]))
			if str(f[0]) == _team_fact:
				pick.select(at)
	pick.item_selected.connect(func(i: int):
		_team_fact = str(pick.get_item_metadata(i))
		host.call("refresh"))
	v.add_child(pick)
	var list := team_rows(season, _team_fact)
	var best := team_best(list, _team_fact)
	var t := UiKit.vbox(0)
	t.name = "LadderTable"
	v.add_child(t)
	# The figure column is as wide as the widest figure, so the best club's
	# figure starts one gap past the end of its bar (critic, 2026-11-04: 420 px
	# of nothing between them on a PC, then 45 px of an over-wide column).
	var fig_w := 0.0
	for r in list:
		var probe := UiKit.figure(team_text(float(r["t_" + _team_fact]), _team_fact), UiKit.NUMBER)
		fig_w = maxf(fig_w, ceilf(probe.get_minimum_size().x))
		probe.free()
	# A bar reads the same on a phone and a PC: no longer than a phone gives it.
	var bar_w := minf(TEAM_BAR_MAX, float(host.call("content_width")) - team_row_width(0.0, fig_w))
	if wide:
		# The bar spans its club's sub-line (the other facts), so the figure
		# follows the bar, not 4 px of sub-line past it.
		for r in list:
			var others := PackedStringArray()
			for f in _view_of(_team_fact)[2]:
				var k := str(f[0])
				if k != _team_fact:
					others.append("%s %s" % [team_text(float(r["t_" + k]), k), str(f[1]).to_lower()])
			var sub := UiKit.lbl(" · ".join(others), UiKit.SECONDARY, UiKit.MUTED)
			bar_w = maxf(bar_w, ceilf(sub.get_minimum_size().x))
			sub.free()
		# As wide as a row needs, left-aligned.
		t.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		t.custom_minimum_size.x = team_row_width(bar_w, fig_w)
	for i in range(list.size()):
		if i > 0:
			t.add_child(UiKit.rule())
		t.add_child(_team_row(host, list[i], i + 1, best, bar_w, fig_w))
	var note := UiKit.lbl("A game, over the games each club has played.", UiKit.SECONDARY, UiKit.MUTED)
	note.name = "TeamNote"
	v.add_child(note)
	return v


## A team row's width around a bar of `bar_w` (0: the row less its bar) and a
## figure column of `fig_w`: margins 8 + 8, rank 22, crest 22, the row's
## two 10 px gaps and the figure's 2 px (_team_row).
static func team_row_width(bar_w: float, fig_w: float) -> float:
	return 8.0 + 22.0 + 10.0 + 22.0 + 10.0 + (maxf(40.0, bar_w) if bar_w > 0.0 else 0.0) + 2.0 + fig_w + 8.0


## Every season_team key a club row carries a game of.
static func team_keys() -> Array:
	var out := []
	for c in TEAM_STATS:
		out.append(str(c[0]))
	for view in TEAM_FACTS:
		for f in view[2]:
			if not out.has(str(f[0])):
				out.append(str(f[0]))
	return out


## Pick the fact the team leaderboard ranks on (tests, a return visit).
static func pick_team_fact(fact: String) -> void:
	_team_fact = fact


## The clubs ranked on a fact, best first (fewest for points against); a club
## yet to play goes last. Ties keep their ladder order.
static func team_rows(season: Season, fact: String) -> Array:
	var list := rows(season)
	var low := TEAM_LOW.has(fact)
	list.sort_custom(func(a, b):
		var x := float(a["t_" + fact])
		var y := float(b["t_" + fact])
		if (x < 0.0) != (y < 0.0):
			return y < 0.0
		if x != y:
			return x < y if low else x > y
		return int(a["pos"]) < int(b["pos"]))
	return list


## The league's best on a fact (-1 before anyone has played).
static func team_best(list: Array, fact: String) -> float:
	var best := -1.0
	for r in list:
		var x := float(r["t_" + fact])
		if x < 0.0:
			continue
		if best < 0.0 or (x < best if TEAM_LOW.has(fact) else x > best):
			best = x
	return best


## A team fact as shown: whole, or to a tenth where a tenth matters (goals).
static func team_text(x: float, fact: String) -> String:
	if x < 0.0:
		return "–"
	return "%.1f" % x if TEAM_TENTHS.has(fact) else "%d" % int(round(x))


## How near a club is to the league's best, 0 to 1 (1 is the best).
static func team_share(x: float, best: float, fact: String) -> float:
	if x <= 0.0 or best <= 0.0:
		return 0.0
	return clampf(best / x if TEAM_LOW.has(fact) else x / best, 0.0, 1.0)


## The view a fact belongs to.
static func _view_of(fact: String) -> Array:
	for view in TEAM_FACTS:
		for f in view[2]:
			if str(f[0]) == fact:
				return view
	return TEAM_FACTS[0]


## One club: its rank, its guernsey and name, the view's other two facts in
## words, a bar against the league's best, and the chosen fact big at the right.
static func _team_row(host: Control, r: Dictionary, rank: int, best: float, bar_w: float,
		fig_w := 56.0) -> Control:
	var code := str(r["code"])
	var mine: bool = code == GameState.my_club
	var b := Button.new()
	b.name = "Club_" + code
	b.mouse_filter = Control.MOUSE_FILTER_PASS
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	# Editorial: no surface of its own (rules between rows); your club's row
	# in your colour.
	var flat := StyleBoxFlat.new()
	flat.bg_color = Color.TRANSPARENT
	if mine:
		flat.bg_color = Color(UiKit.club_vivid(code), 0.22)
		flat.border_width_left = 4
		flat.border_color = UiKit.club_vivid(code)
	var hover := StyleBoxFlat.new()
	hover.bg_color = Color(UiKit.TEXT, 0.05)
	for state in ["normal", "focus"]:
		b.add_theme_stylebox_override(state, flat)
	for state in ["hover", "pressed", "hover_pressed"]:
		b.add_theme_stylebox_override(state, hover)
	var m := MarginContainer.new()
	m.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["margin_left", "margin_right"]:
		m.add_theme_constant_override(side, 8)
	for side in ["margin_top", "margin_bottom"]:
		m.add_theme_constant_override(side, 6)
	b.add_child(m)
	var row := UiKit.hbox(10)
	m.add_child(row)
	var pos := UiKit.line(str(rank), UiKit.SECONDARY, UiKit.MUTED)
	pos.name = "Rank"
	pos.custom_minimum_size.x = 22
	pos.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	pos.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(pos)
	var marker := UiKit.club_marker(code, 22.0)
	marker.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(marker)
	var mid := UiKit.vbox(2)
	mid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mid.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(mid)
	mid.add_child(UiKit.name_label(GameDB.club_name(code), UiKit.NAME, UiKit.TEXT, true))
	var others := PackedStringArray()
	for f in _view_of(_team_fact)[2]:
		var k := str(f[0])
		if k != _team_fact:
			others.append("%s %s" % [team_text(float(r["t_" + k]), k), str(f[1]).to_lower()])
	var sub := UiKit.lbl(" · ".join(others), UiKit.SECONDARY, UiKit.MUTED)
	sub.name = "Others"
	mid.add_child(sub)
	# The bar: how near the league's best, in the club's colour.
	var x := float(r["t_" + _team_fact])
	var share := team_share(x, best, _team_fact)
	var bar := HBoxContainer.new()
	bar.name = "Bar"
	bar.add_theme_constant_override("separation", 0)
	bar.custom_minimum_size = Vector2(maxf(40.0, bar_w), 4)
	bar.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	var fill := ColorRect.new()
	fill.name = "Fill"
	fill.color = UiKit.club_vivid(code)
	fill.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	fill.size_flags_stretch_ratio = maxf(0.001, share)
	bar.add_child(fill)
	var rest := Control.new()
	rest.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rest.size_flags_stretch_ratio = maxf(0.001, 1.0 - share)
	bar.add_child(rest)
	bar.set_meta("share", share)
	mid.add_child(bar)
	var fig := UiKit.figure(team_text(x, _team_fact), UiKit.NUMBER, UiKit.TEXT if x > 0.0 else UiKit.MUTED)
	fig.name = "Figure"
	fig.custom_minimum_size.x = fig_w
	fig.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	fig.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	# 2 px from the bar, not the row's 10: the figure's shade and side bearing
	# make up the rest, so its ink starts about 10 px past the bar (critic,
	# 2026-11-04: 18 px).
	var tail := UiKit.hbox(2)
	tail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.remove_child(mid)
	tail.add_child(mid)
	tail.add_child(fig)
	row.add_child(tail)
	_ignore(m)
	# A button does not grow with its child: the row asks for what it holds.
	b.custom_minimum_size.y = maxf(64.0, m.get_combined_minimum_size().y)
	b.pressed.connect(func(): ClubLink.open(host, code))
	return b


# ---------------------------------------------------------------------------
# The numbers
# ---------------------------------------------------------------------------
## Every club in the true ladder order, with what the table shows: the
## ladder's own columns, a home and an away record, the last five results, and
## each team stat per game (games are the denominator; no games, no number).
static func rows(season: Season) -> Array:
	var out := []
	var home := {}
	var away := {}
	for rnd in season.results:
		for res in rnd:
			var s: Array = res["score"]
			_tally(home, str(res["home"]), int(s[0]) - int(s[1]))
			_tally(away, str(res["away"]), int(s[1]) - int(s[0]))
	var sorted: Array = season.ladder_sorted()
	for i in range(sorted.size()):
		var l: Dictionary = sorted[i]
		var code := str(l["code"])
		var row := {"pos": i + 1, "code": code, "p": int(l["p"]), "w": int(l["w"]), "l": int(l["l"]),
				"d": int(l["d"]), "pf": int(l["pf"]), "pa": int(l["pa"]), "pct": float(l["pct"]),
				"pts": int(l["pts"]), "home": home.get(code, [0, 0, 0]), "away": away.get(code, [0, 0, 0]),
				"form": "".join(PackedStringArray((season.club_results(code) as Array).slice(-5)))}
		var outlook := GameState.team_outlook(code)
		row["rating"] = int(outlook.get("rating", 0))
		var t: Dictionary = GameState.season_team.get(code, {})
		row["games"] = int(t.get("games", 0))
		# A game each over the games that stat was counted for
		# (GameState.club_per_game: an older save counts the newer stats from
		# where it loaded).
		for k in team_keys():
			row["t_" + k] = GameState.club_per_game(code, k)
		out.append(row)
	return out


static func _tally(into: Dictionary, code: String, diff: int) -> void:
	var rec: Array = into.get(code, [0, 0, 0])
	if diff > 0:
		rec[0] += 1
	elif diff < 0:
		rec[1] += 1
	else:
		rec[2] += 1
	into[code] = rec


## What the table shows for one cell: the ladder's own columns as they are,
## a team stat per game.
static func cell_text(r: Dictionary, key: String) -> String:
	match key:
		"pos", "p", "w", "l", "d", "pf", "pa", "pts", "rating":
			return str(int(r[key]))
		"pct":
			return "%.0f" % float(r["pct"])
		"home", "away":
			var rec: Array = r[key]
			return "%d-%d" % [rec[0], rec[1]] + ("-%d" % rec[2] if int(rec[2]) > 0 else "")
		"form":
			return str(r["form"])
	return per_game_text(float(r.get("t_" + key, -1.0)), WHOLE_STATS.has(key))


## A per-game number: one decimal for every figure (106.0, 392.3 and 9.4 line
## up), whole for the few that read better rounded; "-" with no games to divide by.
static func per_game_text(x: float, whole := false) -> String:
	if x < 0.0:
		return "-"
	return "%.0f" % x if whole else "%.1f" % x


## The value a column sorts on.
static func sort_value(r: Dictionary, key: String) -> Variant:
	match key:
		"club":
			return GameDB.club_short(str(r["code"]))
		"home", "away":
			var rec: Array = r[key]
			return int(rec[0]) * 1000 + int(rec[2]) * 10 - int(rec[1])
		"pct":
			return float(r["pct"])
		"for", "against", "disposals", "marks", "tackles", "inside50", "clearances", "hitouts", \
		"rebounds", "clangers", "metres_gained":
			return float(r["t_" + key])
	return float(int(r.get(key, 0)))


## The clubs on show: filtered from the true ladder, then sorted ("" keeps
## the true order). Ties keep their ladder order.
static func visible_rows(season: Season, mine: String, filter: String, sort: String, desc: bool,
		view := "ladder") -> Array:
	var all := rows(season)
	var out := []
	var my_pos := 0
	for r in all:
		if str(r["code"]) == mine:
			my_pos = int(r["pos"])
	for r in all:
		var pos := int(r["pos"])
		match filter:
			"top10":
				if pos > Season.FINALISTS:
					continue
			"near":
				if my_pos <= 0 or absi(pos - my_pos) > 2:
					continue
		out.append(r)
	if sort != "":
		var key := sort
		out.sort_custom(func(a, b):
			var x = sort_value(a, key)
			var y = sort_value(b, key)
			if x == y:
				return int(a["pos"]) < int(b["pos"])
			return (x > y) if desc else (x < y))
	return out


