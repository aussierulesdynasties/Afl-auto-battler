extends Control
## Your list is over the season's spots: you pick who goes. It began with
## the Fitzroy merger (director 2026-11-15: "I pick, delist screen") and opens
## whenever a Legacy season has fewer spots than your list (director
## 2026-11-25, "You pick"). Rival clubs cut by their own rule
## (GameState._era_trim_rivals). The hub opens this screen until the list
## fits; a career that reaches Round 1 without it has the club delist the rest
## by that rule (GameState._merger_cut_by_club).

var _root: VBoxContainer
var _going: Array = []   # ids you marked to go
var _notice := ""
# A PC (UI batch 5, the director's board A): the man on the card and the
# list's page on a narrow window.
var _sel := ""
var _page := 0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.season == null:
		Router.replace("main")
		return
	# Your club's colour behind the page, as on the hub and match day.
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	_root = UiKit.vbox(UiKit.GAP)
	margin.add_child(_root)
	get_viewport().size_changed.connect(func():
		if is_inside_tree() and not UiKit.keyboard_resize(self):
			_build())
	_build()


func _list() -> Array:
	return GameState.season.lists.get(GameState.my_club, GameState.my_list)


func _player(id: String) -> Dictionary:
	for p in _list():
		if str(p["id"]) == id:
			return p
	return {}


## Marked to go, per list kind ("" senior, "A" Category A rookie).
func _picked(kind: String) -> int:
	var n := 0
	for id in _going:
		if str(_player(id).get("rookie_list", "")) == kind:
			n += 1
	return n


func _build() -> void:
	if not is_inside_tree():
		return
	UiKit.clear(_root)
	# No way round it: Back leaves for the title, as the hub's does.
	_root.add_child(UiKit.top_bar("After the merger" if GameState.list_cut_after_merger() else "List cut", false))
	var needs := GameState.merger_cut_needs()
	if _wide():
		_build_pc(needs)
		return
	var body := UiKit.vbox(UiKit.Space.CLOSE)
	body.name = "MergerRows"
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(_hero())
	body.add_child(_lead(needs))
	if _notice != "":
		var n := _para(_notice, UiKit.SECONDARY, UiKit.BAD)
		n.name = "MergerNotice"
		body.add_child(n)
	for kind in needs:
		var head := UiKit.lbl(("Senior list" if kind == "" else "Category A rookies") + "  (%d to go)" % int(needs[kind]),
				UiKit.H2, UiKit.EMPH, true)
		head.name = "MergerHead_" + ("senior" if kind == "" else "rookie")
		body.add_child(UiKit.spacer(UiKit.Space.TIGHT))
		body.add_child(head)
		var full := _picked(kind) >= int(needs[kind])
		for p in _rows(kind):
			body.add_child(_row(p, full))
	_root.add_child(UiKit.scroll(body))
	_root.add_child(_footer(needs))


## One list kind's players, best first.
func _rows(kind: String) -> Array:
	var rows := _list().filter(func(q): return str(q.get("rookie_list", "")) == kind)
	rows.sort_custom(func(a, b):
		if int(Rating.ovr(a, 0)) != int(Rating.ovr(b, 0)):
			return int(Rating.ovr(a, 0)) > int(Rating.ovr(b, 0))
		return str(a["id"]) < str(b["id"]))
	return rows


## The one figure the screen is about: how many are still to go.
func _hero(fig_size := UiKit.HERO, top := UiKit.NAME, low := UiKit.SECONDARY) -> Control:
	var left := maxi(0, GameState.merger_cut_left() - _going.size())
	var h := UiKit.hbox(UiKit.Space.PAD)
	h.name = "MergerLeft"
	h.add_child(UiKit.club_marker(GameState.my_club, 36.0))
	var fig := UiKit.figure(str(left), fig_size, UiKit.club_vivid(GameState.my_club))
	fig.name = "LeftFigure"
	h.add_child(fig)
	var v := UiKit.vbox(0)
	v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_child(UiKit.lbl("still to pick" if left > 0 else "picked: confirm below", top, UiKit.TEXT, true))
	v.add_child(UiKit.lbl("of %d to delist" % GameState.merger_cut_left(), low, UiKit.MUTED))
	h.add_child(v)
	return h


func _lead(needs: Dictionary) -> Control:
	var list := _list()
	var text := ""
	if GameState.list_cut_after_merger():
		var from_fit := list.filter(func(q): return str(q.get("merged_from", "")) != "").size()
		text = "%d of %s's players have joined our list. A club can list %d senior players in %d, and we have %d." % [
				from_fit, GameDB.club_name(LegacyRollover.MERGED),
				RookieList.senior_spots(), GameState.season_year, RookieList.senior_count(list)]
		if needs.has("A"):
			text += " We have %d Category A rookies for %d spots." % [RookieList.cat_a_count(list), RookieList.cat_a_spots()]
		text += " The ones we delist are free to sign with any club."
	else:
		# One fact a line (the list, the rookies, what happens to them).
		var lines: PackedStringArray = []
		if needs.has(""):
			lines.append("A club can list %d senior players in %d, and we have %d." % [
					RookieList.senior_spots(), GameState.season_year, RookieList.senior_count(list)])
		if needs.has("A"):
			lines.append("We have %d Category A rookies for %d spots." % [RookieList.cat_a_count(list), RookieList.cat_a_spots()])
		lines.append("The ones we delist are free to sign with any club.")
		text = "\n".join(lines)
	var l := _para(text, UiKit.BODY, UiKit.TEXT)
	l.name = "MergerLead"
	return l


## One player: who he is, which side he came from, and Delist or Keep.
func _row(p: Dictionary, full: bool) -> Control:
	var id := str(p["id"])
	var marked := _going.has(id)
	var card := PanelContainer.new()
	card.name = "MergerRow_" + id
	var quiet := UiKit.style(Color.TRANSPARENT, UiKit.GAP, 0)
	quiet.set_border_width_all(0)
	quiet.border_width_bottom = 1
	quiet.border_color = UiKit.LINE
	quiet.content_margin_top = UiKit.GAP
	quiet.content_margin_bottom = UiKit.GAP
	card.add_theme_stylebox_override("panel", quiet)
	var v := UiKit.vbox(UiKit.Space.THIN)
	card.add_child(v)
	var top := UiKit.hbox(UiKit.GAP)
	v.add_child(top)
	var info := UiKit.vbox(UiKit.Space.SLIM)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(info)
	# The name gets the row's full width; the role and the side sit under it.
	var who := UiKit.ellipsis(GameDB.player_display_name(p), UiKit.NAME, UiKit.BAD if marked else UiKit.TEXT, true)
	who.name = "PlayerName_" + id
	info.add_child(NameLink.tappable(who, id))
	var h := UiKit.hbox(UiKit.GAP)
	info.add_child(h)
	h.add_child(UiKit.role_chip(Ratings.role_tag(p)))
	# Which side he came from, in that club's colour: the merger's two halves.
	var side := str(p.get("merged_from", GameState.my_club))
	var from := UiKit.lbl(("From " if side != GameState.my_club else "") + GameDB.club_name(side),
			UiKit.FINE, UiKit.club_ink(side), true)
	from.name = "From"
	from.autowrap_mode = TextServer.AUTOWRAP_OFF
	from.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(from)
	var left := int(p.get("contract_years", 1))
	# Two lines, broken at a fixed place, so no line ends or starts with a "·".
	info.add_child(UiKit.lbl("%d OVR  ·  %d POT  ·  age %d" % [
			int(Rating.ovr(p, 0)), int(p.get("potential", Rating.ovr(p, 0))), int(p.get("age", 0))],
			UiKit.SECONDARY, UiKit.MUTED))
	info.add_child(UiKit.lbl("%s  ·  %s" % [
			"%d season%s left" % [left, "" if left == 1 else "s"] if left > 0 else "out of contract",
			Contracts.money(int(p.get("salary", 0)))], UiKit.SECONDARY, UiKit.MUTED))
	info.add_child(PlayerSheet.top_three(p, UiKit.FINE, true))
	if ListStings.release_held(p, GameState.season_year):
		var held := _para(ListCosts.HELD_LINE, UiKit.FINE, UiKit.TEXT)
		held.name = "ReleaseHeld"
		v.add_child(held)
		return card
	var act := UiKit.btn("Keep" if marked else "Delist", UiKit.NAME)
	act.name = "Keep" if marked else "Delist"
	act.custom_minimum_size = Vector2(96, 44)
	act.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	act.disabled = not marked and full
	act.pressed.connect(func():
		_notice = ""
		if marked:
			_going.erase(id)
		else:
			_going.append(id)
		_build())
	top.add_child(act)
	if marked:
		# The gate's two sides, as every delisting states them.
		# The club's voice: we and our (ruling 38); "you" is only the coach.
		v.add_child(UiKit.stake_row(GateOdds.gain(ListCosts.RELEASE_GAIN % Contracts.money(int(p.get("salary", 0)))), "DelistGain"))
		v.add_child(UiKit.stake_row(GateOdds.cost("%s leaves us for nothing, free for any club to sign" % GameDB.player_display_name(p)), "DelistCost"))
	return card


# -- A PC (UI batch 5, the director's board A): the list in one-line rows, three
# columns across (two on a narrow window, a page at a time), and the picked
# man's card beside them with his gain, his cost and Delist. Nothing scrolls.

func _wide() -> bool:
	return ScreenLayout.roomy(UiKit.view_width(self), UiKit.view_height(self))


## A window under 1000 units wide (960 x 540) takes two columns and pages.
func _narrow() -> bool:
	return UiKit.view_width(self) < 1000.0


func _heading(kind: String, needs: Dictionary) -> Label:
	var head := UiKit.lbl(("Senior list" if kind == "" else "Category A rookies") + "  (%d to go)" % maxi(0, int(needs[kind]) - _picked(kind)),
			UiKit.H2, UiKit.EMPH, true)
	head.name = "MergerHead_" + ("senior" if kind == "" else "rookie")
	head.autowrap_mode = TextServer.AUTOWRAP_OFF
	head.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	return head


func _build_pc(needs: Dictionary) -> void:
	var narrow := _narrow()
	var kinds := needs.keys()
	# Every row in list order; a second list kind's heading is a row of its own.
	var items: Array = []
	var players: Array = []
	for kind in kinds:
		if kind != kinds[0]:
			items.append({"head": kind})
		for p in _rows(kind):
			items.append({"p": p})
			players.append(p)
	if players.is_empty():
		_root.add_child(_footer(needs, 44))
		return
	if not players.any(func(q): return str(q["id"]) == _sel):
		_sel = str(players[0]["id"])
	var cols := 2 if narrow else 3
	var side_w := 0.0
	var font := UiKit.FONT
	for p in players:
		side_w = maxf(side_w, font.get_string_size(_side_name(p), HORIZONTAL_ALIGNMENT_LEFT, -1, UiKit.px(UiKit.SMALL)).x)
	var kind0: String = kinds[0]

	if narrow:
		# The figure and the lead across the top.
		var band := UiKit.hbox(UiKit.Space.GUTTER)
		band.name = "MergerBand"
		var hero := _hero(38, UiKit.BODY, UiKit.SMALL)
		hero.custom_minimum_size.x = 156
		hero.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		band.add_child(hero)
		var lead := _lead(needs)
		lead.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		band.add_child(lead)
		_root.add_child(band)
	var split := UiKit.hbox(UiKit.Space.LOOSE)
	split.name = "MergerSplit"
	split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(split)
	var left := UiKit.vbox(UiKit.Space.ROOM)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	split.add_child(left)
	var top := UiKit.hbox(UiKit.Space.GUTTER)
	top.add_child(_heading(kind0, needs))
	left.add_child(top)
	# The list's room is whatever the page leaves it; its rows never set its
	# height, so filling it again on a resize can't move it.
	var room := Control.new()
	room.name = "MergerRoom"
	room.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	room.size_flags_vertical = Control.SIZE_EXPAND_FILL
	room.clip_contents = true
	left.add_child(room)
	# The board's gap between columns, a rule in its middle.
	var grid := UiKit.hbox(UiKit.Space.ROOM if narrow else UiKit.Space.LOOSE)
	grid.name = "MergerColumns"
	grid.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	room.add_child(grid)
	var laid := {"h": -1}
	room.resized.connect(func():
		var h := int(room.size.y)
		if h <= 0 or h == int(laid["h"]):
			return
		laid["h"] = h
		_lay_list(top, grid, items, players, cols, maxi(1, h / 24), float(h), side_w, needs))
	split.add_child(_vrule())

	var right := UiKit.vbox(0)
	right.name = "MergerSide"
	right.custom_minimum_size.x = 280.0 if narrow else 350.0
	split.add_child(right)
	if not narrow:
		right.add_child(_hero(38, UiKit.BODY, UiKit.SMALL))
		right.add_child(UiKit.spacer(UiKit.Space.ROOM))
		right.add_child(_lead(needs))
		right.add_child(UiKit.spacer(UiKit.Space.LOOSE))
		right.add_child(UiKit.rule())
		right.add_child(UiKit.spacer(UiKit.Space.LOOSE))
	for p in players:
		if str(p["id"]) == _sel:
			var kind := str(p.get("rookie_list", ""))
			right.add_child(_pc_card(p, not narrow, _picked(kind) >= int(needs[kind])))
	if _notice != "":
		var n := _para(_notice, UiKit.SECONDARY, UiKit.BAD)
		n.name = "MergerNotice"
		right.add_child(UiKit.spacer(UiKit.Space.ROOM))
		right.add_child(n)
	var fill := Control.new()
	fill.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(fill)
	var go := _footer(needs, 44 if narrow else 52)
	if narrow:
		_root.add_child(go)
	else:
		right.add_child(go)


## The list in the room: as many rows to a column as it holds at the board's
## row heights, one page of three columns on a full window, pages of two on a
## narrow one, the pages named by the players on them ("1 to 26").
func _lay_list(top: HBoxContainer, grid: HBoxContainer, items: Array, players: Array, cols: int,
		per_fit: int, room_h: float, side_w: float, needs: Dictionary) -> void:
	var per := int(ceil(float(items.size()) / float(cols)))
	var pages := 1
	if per > per_fit:
		per = per_fit
		pages = int(ceil(float(items.size()) / float(per * cols)))
	# Clamped here only: the room's first size, mid-layout, can fit the list on
	# one page, and clamping _page itself then lost the page you turned to.
	var at := clampi(_page, 0, pages - 1)
	var row_h := floorf(minf(44.0, room_h / float(per)))
	var old := top.get_node_or_null("MergerPages")
	if old != null:
		top.remove_child(old)
		old.queue_free()
	if pages > 1:
		var opts: Array = []
		for pg in range(pages):
			var on_page := items.slice(pg * per * cols, (pg + 1) * per * cols).filter(func(it): return it.has("p"))
			var first := players.find(on_page[0]["p"]) + 1
			opts.append([str(pg), "%d to %d" % [first, first + on_page.size() - 1]])
		top.add_child(_page_buttons(opts, at))
	for c in grid.get_children():
		grid.remove_child(c)
		c.queue_free()
	var shown := items.slice(at * per * cols, (at + 1) * per * cols)
	for c in range(cols):
		if c > 0:
			grid.add_child(_vrule())
		var col := UiKit.vbox(0)
		col.name = "MergerColumn_%d" % c
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		grid.add_child(col)
		for it in shown.slice(c * per, (c + 1) * per):
			if it.has("head"):
				var h := _heading(str(it["head"]), needs)
				h.custom_minimum_size.y = row_h
				h.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
				col.add_child(h)
			else:
				col.add_child(_pc_row(it["p"], row_h, side_w))


## The pages as two boxes, as on the director's board A: the page you're on
## lit (a 2-unit TEXT outline on PANEL_ALT), the other one quiet (LINE on
## INK), each as wide as its words, 35 tall, 6 apart.
func _page_buttons(opts: Array, at: int) -> HBoxContainer:
	var row := UiKit.hbox(6)
	row.name = "MergerPages"
	row.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	for o in opts:
		var key := str(o[0])
		var on := key == str(at)
		var b := UiKit.btn(str(o[1]), UiKit.SMALL)
		b.name = "MergerPages_" + key
		b.custom_minimum_size = Vector2(0, 35)
		var sb := UiKit.style(UiKit.PANEL_ALT if on else UiKit.INK, 0, 4, UiKit.TEXT if on else UiKit.LINE)
		sb.set_border_width_all(2 if on else 1)
		sb.content_margin_left = 20
		sb.content_margin_right = 20
		sb.content_margin_top = 0
		sb.content_margin_bottom = 0
		for state in ["normal", "hover", "pressed", "hover_pressed"]:
			b.add_theme_stylebox_override(state, sb)
		for c in ["font_color", "font_hover_color", "font_pressed_color"]:
			b.add_theme_color_override(c, UiKit.TEXT if on else UiKit.MUTED)
		b.pressed.connect(func():
			_page = int(key)
			_build())
		row.add_child(b)
	return row


func _vrule() -> ColorRect:
	var r := ColorRect.new()
	r.color = UiKit.LINE
	r.custom_minimum_size = Vector2(1, 0)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


## The club he came from: the merger's other half, or ours.
func _side(p: Dictionary) -> String:
	return str(p.get("merged_from", GameState.my_club))


func _side_name(p: Dictionary) -> String:
	return GameDB.club_name(_side(p))


## One player on one line: his name (red once picked to go), his role, the
## side he came from and his rating. A click puts him on the card.
func _pc_row(p: Dictionary, h: float, side_w: float) -> Button:
	var id := str(p["id"])
	var on := id == _sel
	var b := Button.new()
	b.name = "MergerRow_" + id
	b.custom_minimum_size = Vector2(0, h)
	b.focus_mode = Control.FOCUS_ALL
	var sb := UiKit.style(UiKit.PANEL_ALT if on else Color.TRANSPARENT, 0, 4, UiKit.TEXT)
	if not on:
		sb.set_border_width_all(0)
	for state in ["normal", "pressed", "hover_pressed"]:
		b.add_theme_stylebox_override(state, sb)
	var hv := sb.duplicate() as StyleBoxFlat
	if not on:
		hv.bg_color = Color(UiKit.TEXT, 0.05)
	b.add_theme_stylebox_override("hover", hv)
	b.add_theme_stylebox_override("focus", UiKit.focus_ring())
	b.pressed.connect(func():
		_sel = id
		_build())
	var m := MarginContainer.new()
	m.set_anchors_preset(Control.PRESET_FULL_RECT)
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for s in ["left", "right"]:
		m.add_theme_constant_override("margin_" + s, UiKit.Space.CLOSE)
	b.add_child(m)
	var row := UiKit.hbox(0)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.add_child(row)
	var marked := _going.has(id)
	var who := UiKit.ellipsis(GameDB.player_display_name(p), UiKit.BODY, UiKit.BAD if marked else UiKit.TEXT, true)
	who.name = "PlayerName_" + id
	who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	who.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(who)
	if marked:
		# Crossed off the list: a line through his name as well as red, so the
		# mark is not colour alone, and it costs the name no room.
		var w := who.get_theme_font("font").get_string_size(who.text, HORIZONTAL_ALIGNMENT_LEFT, -1,
				who.get_theme_font_size("font_size")).x
		var cross := ColorRect.new()
		cross.name = "CrossedOff"
		cross.color = UiKit.BAD
		cross.mouse_filter = Control.MOUSE_FILTER_IGNORE
		cross.anchor_top = 0.5
		cross.anchor_bottom = 0.5
		cross.offset_top = -1.0
		cross.offset_bottom = 1.0
		cross.offset_right = w
		who.add_child(cross)
		who.resized.connect(func(): cross.offset_right = minf(w, who.size.x))
	var tag := Ratings.role_tag(p)
	var role := UiKit.line(tag, UiKit.SMALL, UiKit.ROLE_COLOUR.get(tag.split("/")[0], UiKit.MUTED), true)
	role.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	role.custom_minimum_size.x = UiKit.FONT.get_string_size(tag, HORIZONTAL_ALIGNMENT_LEFT, -1, UiKit.px(UiKit.SMALL)).x + UiKit.Space.CLOSE
	role.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(role)
	var side := UiKit.line(_side_name(p), UiKit.SMALL, UiKit.club_name_colour(UiKit.club_ink(_side(p))), true)
	side.name = "Side"
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	side.custom_minimum_size.x = side_w + 18.0
	side.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(side)
	var ovr := UiKit.line(str(int(Rating.ovr(p, 0))), UiKit.BODY, UiKit.TEXT, true)
	ovr.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	ovr.custom_minimum_size.x = 34.0
	ovr.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(ovr)
	return b


## The picked man's card: who he is, his contract and best three, then the
## gate's two sides and Delist (or Keep), sized to its word.
func _pc_card(p: Dictionary, big: bool, full: bool) -> VBoxContainer:
	var id := str(p["id"])
	var marked := _going.has(id)
	var v := UiKit.vbox(0)
	v.name = "MergerCard"
	var head := UiKit.hbox(UiKit.Space.CLOSE)
	v.add_child(head)
	var who := UiKit.ellipsis(GameDB.player_display_name(p), 28 if big else UiKit.H1, UiKit.BAD if marked else UiKit.TEXT, true)
	who.name = "CardName"
	who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	who.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(who)
	var prof := UiKit.text_action("Profile ›", UiKit.BODY)
	prof.name = "CardProfile"
	prof.pressed.connect(func(): NameLink.open(self, id))
	head.add_child(prof)
	var tag_size := UiKit.BODY if big else UiKit.SMALL
	var h := UiKit.hbox(UiKit.Space.ROOM)
	var tag := Ratings.role_tag(p)
	var role := UiKit.line(tag, tag_size, UiKit.ROLE_COLOUR.get(tag.split("/")[0], UiKit.MUTED), true)
	role.custom_minimum_size.x = 60
	h.add_child(role)
	var side := _side(p)
	var from := UiKit.line(("From " if side != GameState.my_club else "") + GameDB.club_name(side), tag_size, UiKit.club_name_colour(UiKit.club_ink(side)), true)
	from.name = "From"
	h.add_child(from)
	v.add_child(h)
	v.add_child(UiKit.spacer(UiKit.Space.ROOM))
	var facts := UiKit.H2 if big else UiKit.BODY
	var left := int(p.get("contract_years", 1))
	v.add_child(UiKit.lbl("%d OVR  ·  %d POT  ·  age %d" % [
			int(Rating.ovr(p, 0)), int(p.get("potential", Rating.ovr(p, 0))), int(p.get("age", 0))], facts, UiKit.MUTED))
	v.add_child(UiKit.spacer(UiKit.Space.THIN))
	v.add_child(UiKit.lbl("%s  ·  %s" % [
			"%d season%s left" % [left, "" if left == 1 else "s"] if left > 0 else "out of contract",
			Contracts.money(int(p.get("salary", 0)))], facts, UiKit.MUTED))
	v.add_child(UiKit.spacer(UiKit.Space.ROOM))
	v.add_child(PlayerSheet.top_three(p, UiKit.BODY if big else UiKit.SMALL, true))
	v.add_child(UiKit.spacer(UiKit.Space.LOOSE))
	v.add_child(UiKit.rule())
	v.add_child(UiKit.spacer(UiKit.Space.LOOSE))
	if ListStings.release_held(p, GameState.season_year):
		var held := _para(ListCosts.HELD_LINE, UiKit.BODY, UiKit.TEXT)
		held.name = "ReleaseHeld"
		v.add_child(held)
		return v
	# The gate's two sides, as every delisting states them (ruling 38: our voice).
	var gates := UiKit.vbox(UiKit.Space.TIGHT)
	gates.add_child(UiKit.stake_row(GateOdds.gain(ListCosts.RELEASE_GAIN % Contracts.money(int(p.get("salary", 0)))), "DelistGain"))
	gates.add_child(UiKit.stake_row(GateOdds.cost("%s leaves us for nothing, free for any club to sign" % GameDB.player_display_name(p)), "DelistCost"))
	v.add_child(gates)
	v.add_child(UiKit.spacer(UiKit.Space.OPEN))
	var act := UiKit.btn("Keep" if marked else "Delist", UiKit.H2)
	act.name = "Keep" if marked else "Delist"
	act.custom_minimum_size = Vector2(0, 52 if big else 48)
	act.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_pad_sides(act)
	act.disabled = not marked and full
	act.pressed.connect(func():
		_notice = ""
		if marked:
			_going.erase(id)
		else:
			_going.append(id)
		_build())
	v.add_child(act)
	return v


## On a PC the button is sized to its words at the right, `pc_h` tall.
func _footer(needs: Dictionary, pc_h := 0) -> Control:
	var ready := not needs.is_empty()
	for kind in needs:
		if _picked(kind) != int(needs[kind]):
			ready = false
	var go := UiKit.btn("Delist %d player%s" % [_going.size(), "" if _going.size() == 1 else "s"] if ready \
			else "Pick %d more" % maxi(0, GameState.merger_cut_left() - _going.size()), UiKit.H2 if pc_h > 0 else UiKit.NAME, true)
	go.name = "ConfirmCut"
	go.custom_minimum_size.y = pc_h if pc_h > 0 else 52
	go.size_flags_horizontal = Control.SIZE_SHRINK_END if pc_h > 0 else Control.SIZE_EXPAND_FILL
	if pc_h > 0:
		_pad_sides(go)
	go.disabled = not ready
	go.pressed.connect(_confirm)
	return go


## The board's 24 units of room either side of a button's words.
func _pad_sides(b: Button) -> void:
	for state in ["normal", "hover", "pressed", "hover_pressed", "disabled", "focus"]:
		if b.has_theme_stylebox_override(state):
			var sb := b.get_theme_stylebox(state).duplicate() as StyleBox
			sb.content_margin_left = 24
			sb.content_margin_right = 24
			b.add_theme_stylebox_override(state, sb)


func _confirm() -> void:
	var out := GameState.merger_delist(_going)
	if not bool(out["ok"]):
		_notice = str(out["reason"])
		_build()
		return
	GameState.autosave()
	Router.replace("hub")


func _para(text: String, size: int, colour: Color) -> Label:
	var l := UiKit.lbl(text, size, colour)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


## Back leaves for the title, as from the hub: the cut waits for your return.
func handle_back() -> bool:
	Router.to_main_menu(false)
	return true
