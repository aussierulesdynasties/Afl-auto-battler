extends Control
## Your list: how the side stacks up, the best 23 on an oval, and every
## player in one line each - who he is, whether he is available, how good.
## Tap a player for his profile: role, state, development, strengths,
## season and the attributes behind his rating.

var _root: VBoxContainer
var _squad: Squad = null
var _pane := "shape"
var _profile: Control
## Built panes by key ("shape", "list" on a phone, "wide" on PC): a tab tap
## shows the other pane, building it the first time, and never rebuilds.
var _panes := {}
var _built_narrow := false
var _built_width := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.my_club == "" or GameState.my_list.is_empty():
		Router.replace("main")
		return
	_squad = GameState.my_squad()

	# Your club's colour behind the page, as on the hub and match day
	# (director, 2026-10-10: every screen in the gameday style).
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)

	_root = UiKit.vbox(9)
	margin.add_child(_root)
	get_viewport().size_changed.connect(func():
		if is_inside_tree() and not UiKit.keyboard_resize(self):
			# A phone's system bars showing or hiding change the height only:
			# the page is the same, so it is not rebuilt (a rebuild is a stall
			# on a phone). Width matters across the phone/PC line, and on PC.
			if _narrow() == _built_narrow and (_narrow() or UiKit.view_width(self) == _built_width):
				return
			var places := UiKit.scroll_places(_root)
			_build()
			UiKit.restore_places(_root, places))
	if not GameState.player_names_changed.is_connected(_on_names):
		GameState.player_names_changed.connect(_on_names)
	_build()
	FirstVisitIntro.show_if_due.call_deferred(self, "list")


func _on_names() -> void:
	if is_inside_tree():
		_squad = GameState.my_squad()
		_build()


func _narrow() -> bool:
	return UiKit.view_width(self) < 760.0


## Rebuild the page from the career (after a change to the list): the panes
## built so far are dropped and only the one on show is built again.
func _build() -> void:
	UiKit.clear(_root)
	_panes = {}
	_built_narrow = _narrow()
	_built_width = UiKit.view_width(self)
	var train := UiKit.btn("Train", 14)
	train.custom_minimum_size = Vector2(72, 44)
	train.pressed.connect(func(): Router.go("training"))
	_root.add_child(UiKit.top_bar("My list", true, train))
	_show_pane()


## Show the pane the tabs ask for, building it the first time it is shown.
func _show_pane() -> void:
	var key := _pane if _narrow() else "wide"
	if not _panes.has(key):
		_panes[key] = _build_pane()
		_root.add_child(_panes[key])
	for k in _panes:
		(_panes[k] as Control).visible = k == key


func _build_pane() -> Control:
	var pane_root: Control

	# On a phone the Shape pane is the whole page below the title: the board
	# is 600 px of oval and a bench under a header of standing and captaincy
	# (culture sits in the Captaincy panel), taller than the screen, so the page scrolls to the foot of the
	# oval and the bench (the sweep, 2026-10-18: it ran to y 1005 on 844). A
	# swipe that starts on a guernsey still scrolls it: the kit lets drags
	# through every button inside a scroll. The Full list pane scrolls its
	# own rows.
	var host: BoxContainer
	if _narrow() and _pane == "shape":
		var page := UiKit.vbox(9)
		page.name = "ShapePage"
		var page_scroll := UiKit.scroll(page)
		page_scroll.name = "ShapeScroll"
		pane_root = page_scroll
		host = page
	else:
		host = UiKit.vbox(9)
		host.name = "ListPage" if _narrow() else "WidePage"
		host.size_flags_vertical = Control.SIZE_EXPAND_FILL
		pane_root = host

	# How the side stacks up, in words, and who is available.
	var injured := 0
	for p in GameState.my_list:
		if int(p.get("injury_weeks", 0)) > 0:
			injured += 1
	var head := UiKit.lbl(GameState.my_line_standing_text(), UiKit.SMALL, UiKit.TEXT)
	head.name = "LineStanding"
	head.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	host.add_child(head)
	var count := "%d senior  ·  %d rookie" % [RookieList.senior_count(GameState.my_list),
			RookieList.rookie_count(GameState.my_list)]
	if injured > 0:
		count += "  ·  %d injured" % injured
	host.add_child(UiKit.lbl(count, UiKit.SMALL, UiKit.MUTED))
	var named := PackedStringArray()
	var cap_rec := GameState.captaincy_record(GameState.my_club)
	for id in Captaincy.ids(cap_rec):
		for q in GameState.my_list:
			if str(q.get("id", "")) == str(id):
				# A phone row names them by surname, so all three fit beside the word.
				named.append(GameDB.player_surname(q) if _narrow() else GameDB.player_display_name(q))
	var cap_link := UiKit.section_link("Captaincy", (", ".join(named) if not named.is_empty() else "No captain named") + "  ›",
			"CaptaincyOpen")
	cap_link.pressed.connect(func(): _open_captaincy())
	if not _narrow():
		# A PC row is a row of text, not a bar across the whole window (PC is
		# not a big phone): it takes what its words need, left-aligned.
		cap_link.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		cap_link.custom_minimum_size = Vector2(460, 48)
		# The names start a clear step after the label, and the row says it opens.
		var title_l := cap_link.find_child("SectionTitle", true, false)
		if title_l != null:
			# The label keeps the width of its own word (a trimmed label with no
			# room asked for collapses to nothing beside the names).
			(title_l as Label).text_overrun_behavior = TextServer.OVERRUN_NO_TRIMMING
			(title_l as Control).size_flags_horizontal = Control.SIZE_FILL
		var h := cap_link.find_child("SectionLeadsTo", true, false)
		if h != null:
			(h as Control).size_flags_horizontal = Control.SIZE_EXPAND_FILL
		(cap_link.get_child(0) as BoxContainer).add_theme_constant_override("separation", 16)
	else:
		# A phone keeps the word whole ("Captain…" said nothing, critic
		# 2026-11-04): the names give way instead, and the chevron stays.
		var title_n := cap_link.find_child("SectionTitle", true, false) as Label
		var names_n := cap_link.find_child("SectionLeadsTo", true, false) as Label
		if title_n != null and names_n != null:
			title_n.text_overrun_behavior = TextServer.OVERRUN_NO_TRIMMING
			title_n.size_flags_horizontal = Control.SIZE_FILL
			names_n.text = names_n.text.trim_suffix("›").strip_edges()
			names_n.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
			names_n.clip_text = true
			names_n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			names_n.custom_minimum_size.x = 0.0
			var chev := UiKit.lbl("›", UiKit.NAME, UiKit.TEXT)
			chev.name = "CaptaincyChevron"
			chev.autowrap_mode = TextServer.AUTOWRAP_OFF
			chev.mouse_filter = Control.MOUSE_FILTER_IGNORE
			names_n.get_parent().add_child(chev)
	host.add_child(cap_link)
	var value: Node = cap_link.find_child("SectionLeadsTo", true, false)
	if value is Label:
		(value as Label).add_theme_color_override("font_color", UiKit.TEXT)

	if _narrow():
		var tabs := UiKit.hbox(2)
		host.add_child(tabs)
		var shape_tab := UiKit.tab("Shape", _pane == "shape")
		shape_tab.name = "ListTabShape"
		shape_tab.pressed.connect(func():
			_pane = "shape"
			_show_pane())
		tabs.add_child(shape_tab)
		var list_tab := UiKit.tab("Full list", _pane == "list")
		list_tab.name = "ListTabFull"
		list_tab.pressed.connect(func():
			_pane = "list"
			_show_pane())
		tabs.add_child(list_tab)

	var body: BoxContainer
	if _narrow():
		body = UiKit.vbox(10)
	else:
		body = UiKit.hbox(10)
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	host.add_child(body)

	if not _narrow() or _pane == "shape":
		body.add_child(_shape_panel())
	if not _narrow() or _pane == "list":
		body.add_child(_full_list_panel())
	return pane_root


func _shape_panel() -> Control:
	# On a phone the page's scroll rail takes 20 px of the width; the panel's
	# padding gives some of it back so the cards keep their full names (the
	# sweep: "Andy Moniz-Wakefield" needs 116 px, the squeezed card gave 114).
	var left := UiKit.panel(UiKit.PANEL, 6 if _narrow() else 12)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.custom_minimum_size = Vector2(0, 220)
	var lv := UiKit.vbox(5)
	lv.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(lv)
	lv.add_child(UiKit.lbl("Best 23", UiKit.H2, UiKit.EMPH, true))
	var shape_note := UiKit.lbl("Six defenders, six midfielders (ruck included), six forwards and five on the bench. Tap a guernsey.",
			UiKit.SMALL, UiKit.MUTED)
	shape_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lv.add_child(shape_note)
	if _narrow():
		# A phone gets the selection board itself, read-only (guide §4.3: one
		# board grammar, names readable on the tokens), not a postage-stamp oval.
		var board := TeamBuilder.new()
		board.name = "Best22Board"
		board.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		board.setup(GameState.current_side(), false, [], true)
		board.inspect.connect(_open_profile)
		lv.add_child(board)
		return left
	var oval := FormationView.new()
	oval.name = "Best22Oval"
	oval.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	oval.size_flags_vertical = Control.SIZE_EXPAND_FILL
	oval.custom_minimum_size = Vector2(0, 180)
	oval.setup(_squad.ground, _squad.bench, GameState.my_club, not GameState.my_selection().is_empty())
	lv.add_child(oval)
	return left


func _full_list_panel() -> Control:
	var right := UiKit.panel(UiKit.PANEL, 12)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var rv := UiKit.vbox(5)
	rv.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(rv)
	rv.add_child(UiKit.lbl("Full list", UiKit.H2, UiKit.EMPH, true))
	var lbox := UiKit.vbox(0)
	lbox.name = "ListRows"
	rv.add_child(UiKit.scroll(lbox))

	# Two lists (row 88): the senior list, then the rookie list, each with its spots.
	var seniors := RookieList.seniors(GameState.my_list)
	var rookies := RookieList.rookies(GameState.my_list)
	var sh := UiKit.lbl("Senior list  %d / %d" % [seniors.size(), RookieList.SENIOR_SPOTS], UiKit.BODY, UiKit.EMPH, true)
	sh.name = "SeniorListHead"
	lbox.add_child(sh)
	_role_groups(lbox, seniors, false)
	lbox.add_child(UiKit.spacer(8))
	var rh := UiKit.lbl("Rookie list  %d / %d" % [rookies.size(), RookieList.CAT_A_SPOTS], UiKit.BODY, UiKit.EMPH, true)
	rh.name = "RookieListHead"
	lbox.add_child(rh)
	if rookies.is_empty():
		var none := UiKit.lbl("No rookies. The Rookie Draft after the National Draft and the mid-season rookie draft fill these spots.",
				UiKit.SMALL, UiKit.MUTED)
		none.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		lbox.add_child(none)
	else:
		_role_groups(lbox, rookies, true)
	return right


## Players under a heading per position, best first. A rookie list skips an
## empty position.
func _role_groups(lbox: Control, players: Array, skip_empty: bool) -> void:
	var grouped := {}
	for r in ["RUCK", "MID", "DEF", "FWD"]:
		grouped[r] = []
	for p in players:
		grouped[str(p["role"])].append(p)
	for r in ["RUCK", "MID", "DEF", "FWD"]:
		var g: Array = grouped[r]
		if skip_empty and g.is_empty():
			continue
		g.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
		lbox.add_child(UiKit.spacer(4))
		lbox.add_child(UiKit.lbl("%s  (%d)" % [UiKit.ROLE_LABEL[r], g.size()],
				UiKit.SMALL, UiKit.MUTED, true))
		for p in g:
			lbox.add_child(_list_row(p))
		lbox.add_child(UiKit.spacer(6))


## His number on your club's guernsey: everyone on this list plays for you,
## whatever club he came from (p["club"] can be his source club after a
## league re-draft).
func _guernsey(p: Dictionary) -> PanelContainer:
	var cols: Array = GameDB.club_colours(GameState.my_club)
	var chip := UiKit.chip(str(p["num"]), cols[0])
	chip.name = "Guernsey"
	var sb := UiKit.style(cols[0], 4, 4, cols[1])
	sb.set_border_width_all(2)
	chip.add_theme_stylebox_override("panel", sb)
	return chip


## One player in one line: guernsey, name, who he is (type, age, height),
## anything that stops him playing, and how good he is. Tap for his profile.
func _list_row(p: Dictionary) -> Control:
	var row := Button.new()
	row.name = "Row_" + str(p["id"])
	row.custom_minimum_size = Vector2(0, 56)
	row.focus_mode = Control.FOCUS_NONE
	for state in ["normal", "hover", "pressed", "focus"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(1, 1, 1, 0.04) if state == "hover" or state == "pressed" else Color.TRANSPARENT
		sb.border_color = UiKit.LINE
		sb.border_width_bottom = 1
		row.add_theme_stylebox_override(state, sb)
	row.pressed.connect(_open_profile.bind(str(p["id"])))
	var h := UiKit.hbox(8)
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 2
	h.offset_right = -2
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(h)
	var num := _guernsey(p)
	num.mouse_filter = Control.MOUSE_FILTER_IGNORE
	num.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	# One width for every guernsey, so the names line up.
	num.custom_minimum_size = Vector2(30, 0)
	h.add_child(num)
	var who := UiKit.vbox(0)
	who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	who.alignment = BoxContainer.ALIGNMENT_CENTER
	who.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(who)
	who.add_child(UiKit.ellipsis(GameDB.player_display_name(p), UiKit.BODY, UiKit.TEXT, true))
	var bits := PackedStringArray([Roles.label(p)])
	if float(p.get("age", 0.0)) > 0.0:
		bits.append("%d" % int(p["age"]))
	if float(p.get("height_cm", 0.0)) > 0.0:
		bits.append("%d cm" % int(p["height_cm"]))
	var sub := UiKit.ellipsis("  ·  ".join(bits), UiKit.SMALL, UiKit.MUTED)
	sub.name = "RowIdentity"
	who.add_child(sub)
	# Marked untouchable: a line of its own, so his name and his details are never cut for it.
	if GameState.is_untouchable(str(p["id"])):
		var mark := UiKit.ellipsis("Untouchable", UiKit.SMALL, UiKit.TEXT, true)
		mark.name = "RowUntouchable"
		mark.mouse_filter = Control.MOUSE_FILTER_IGNORE
		who.add_child(mark)
		row.custom_minimum_size = Vector2(0, 74)
	var status := _status(p)
	if str(status[0]) != "":
		var st := UiKit.line(str(status[0]), UiKit.SMALL, status[1], true)
		st.name = "RowStatus"
		st.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(st)
	var nums := UiKit.vbox(0)
	nums.alignment = BoxContainer.ALIGNMENT_CENTER
	nums.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(nums)
	var ov := UiKit.line(str(int(p["overall"])), 20, UiKit.TEXT, true)
	ov.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	ov.custom_minimum_size = Vector2(40, 0)
	nums.add_child(ov)
	var pot := UiKit.line("POT %d" % int(p.get("potential", p["overall"])), UiKit.TINY, UiKit.MUTED)
	pot.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	nums.add_child(pot)
	return row


## The one thing that matters most about his availability: [text, colour].
func _status(p: Dictionary) -> Array:
	var weeks := int(p.get("injury_weeks", 0))
	if Injuries.concussion_text(p) != "":
		return [Injuries.concussion_text(p), UiKit.BAD]
	if weeks > 0:
		return ["Out %s" % ("1 week" if weeks == 1 else "%d weeks" % weeks), UiKit.BAD]
	if bool(p.get("rested", false)):
		return ["Rested", UiKit.MUTED]
	if ClubLife.morale(p) < 40:
		return ["Unhappy", UiKit.BAD]
	return ["", UiKit.TEXT]


## His profile (PlayerSheet): who he is, his state, how good and how much
## room, what he is picked for, his season and his attributes.
func _open_profile(id: String) -> void:
	var p := GameState.list_player(id)
	if p.is_empty():
		return
	_close_profile()
	# One toggle: rivals stop asking for him in trade talks. Nothing about his rating.
	var on := GameState.is_untouchable(id)
	var actions := [{"name": "Untouchable",
			"label": "Remove untouchable mark" if on else "Mark untouchable",
			"detail": "Rivals are not asking for him in trade talks." if on else "Rivals stop asking for him in trade talks.",
			"run": func():
				GameState.set_untouchable(id, not on)
				_build()
				_open_profile(id)}]
	if RookieList.is_rookie(p):
		var block := RookieList.upgrade_block(GameState, GameState.my_club, id)
		var used := RookieList.senior_count(GameState.my_list)
		actions.append({"name": "Upgrade", "label": "Upgrade to the senior list",
				"disabled": block != "",
				"detail": block if block != "" else "He takes a senior spot (%d of %d used) and his wage rises to the senior minimum, %s a season." % [
						used, RookieList.SENIOR_SPOTS, Contracts.money(RookieList.senior_wage(GameState.season_year))],
				"run": func():
					if RookieList.upgrade(GameState, GameState.my_club, id):
						GameState.autosave()
					_build()
					_open_profile(id)})
	_profile = PlayerSheet.open(self, p, func(): _profile = null, actions)


func _open_captaincy() -> void:
	_close_profile()
	WeekChecklist.mark(GameState, "captaincy")
	_profile = CaptaincySheet.open(self, func():
		_profile = null
		_build())


func _close_profile() -> void:
	if _profile != null and is_instance_valid(_profile):
		_profile.queue_free()
	_profile = null


## Android Back closes a profile before leaving the list.
func handle_back() -> bool:
	if FirstVisitIntro.close_open(self):
		return true
	if _profile != null and is_instance_valid(_profile):
		if _profile.has_meta("back") and bool((_profile.get_meta("back") as Callable).call()):
			return true
		_close_profile()
		return true
	return false


func _attr_columns() -> int:
	var w := UiKit.view_width(self)
	if w < 520.0:
		return 1
	return 2 if w < 1000.0 else 3
