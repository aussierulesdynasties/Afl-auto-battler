extends Control
## Your list: how the side stacks up, the best 23 on an oval, and every
## player in one line each - who he is, whether he is available, how good.
## Tap a player for his profile: role, state, development, strengths,
## season and the attributes behind his rating.

var _root: VBoxContainer
var _squad: Squad = null
var _pane := "shape"
var _profile: Control
## A phone's built panes by key ("shape", "list"): a tab tap shows the other
## pane, building it the first time, and never rebuilds.
var _panes := {}
var _built_narrow := false
var _built_width := 0.0
var _built_height := 0.0
## A PC's stage on show: "best" (Best 23) or "full" (Full list).
var _stage := "best"


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

	_root = UiKit.vbox(UiKit.Space.EASY)
	margin.add_child(_root)
	get_viewport().size_changed.connect(func():
		if is_inside_tree() and not UiKit.keyboard_resize(self):
			# A phone's system bars showing or hiding change the height only:
			# the page is the same, so it is not rebuilt (a rebuild is a stall
			# on a phone). Width matters across the phone/PC line; on PC both do,
			# as the page fits its window without scrolling.
			if _narrow() == _built_narrow and (_narrow() or (UiKit.view_width(self) == _built_width
					and UiKit.view_height(self) == _built_height)):
				return
			var places := UiKit.scroll_places(_root)
			_build()
			UiKit.restore_places(_root, places))
	_build()
	FirstVisitIntro.show_if_due.call_deferred(self, "list")


func _narrow() -> bool:
	return UiKit.view_width(self) < 760.0


## Rebuild the page from the career (after a change to the list): the panes
## built so far are dropped and only the one on show is built again.
func _build() -> void:
	UiKit.clear(_root)
	_panes = {}
	_built_narrow = _narrow()
	_built_width = UiKit.view_width(self)
	_built_height = UiKit.view_height(self)
	var train := UiKit.btn("Train", 14)
	train.custom_minimum_size = Vector2(72, 44)
	train.pressed.connect(func(): Router.go("training"))
	_root.add_child(UiKit.top_bar("My list", true, train))
	if not _narrow():
		_pc_stages()
		return
	_show_pane()


## A PC: the page in two stages, neither scrolling (director's pick B, 2026-11-26).
## Best 23: the oval, how we stack up, captaincy and scouting. Full list: every
## man ranked best first, down then across in three columns.
func _pc_stages() -> void:
	var tabs := UiKit.hbox(UiKit.Space.TIGHT)
	tabs.name = "ListStages"
	_root.add_child(tabs)
	for s in [["best", "Best 23"], ["full", "Full list"]]:
		var t := UiKit.tab(str(s[1]), _stage == str(s[0]))
		t.name = "Stage_" + str(s[0])
		t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		t.pressed.connect(func():
			_stage = str(s[0])
			_build())
		tabs.add_child(t)
	if _stage == "full":
		_root.add_child(_full_stage())
		return
	var row := UiKit.hbox(UiKit.Space.APART)
	row.name = "BestStage"
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(row)
	var oval := _shape_panel()
	oval.size_flags_stretch_ratio = 1.9
	row.add_child(oval)
	row.add_child(_facts_column())


## Beside the oval: how the side stacks up, a line each, the count, then captaincy and scouting.
func _facts_column() -> Control:
	var col := UiKit.vbox(UiKit.Space.EASY)
	col.name = "ListFacts"
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_child(UiKit.section("How we stack up"))
	var lines := UiKit.vbox(UiKit.Space.TIGHT)
	lines.name = "LineStanding"
	col.add_child(lines)
	for r in GameState.my_line_standing():
		var h := UiKit.hbox(UiKit.GAP)
		var line_name := UiKit.lbl(str(r[0]), UiKit.BODY, UiKit.TEXT, true)
		line_name.custom_minimum_size = Vector2(96, 0)
		h.add_child(line_name)
		var said := UiKit.lbl(str(r[1]), UiKit.BODY, UiKit.TEXT)
		said.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		said.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(said)
		lines.add_child(h)
	col.add_child(UiKit.lbl(_count_line(), UiKit.SMALL, UiKit.MUTED))
	col.add_child(UiKit.rule())
	var cap := UiKit.section_link("Captaincy", _captains(false) + "  ›", "CaptaincyOpen")
	cap.pressed.connect(func(): _open_captaincy())
	var names := cap.find_child("SectionLeadsTo", true, false) as Label
	if names != null:
		names.add_theme_color_override("font_color", UiKit.TEXT)
		names.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		names.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		names.size_flags_stretch_ratio = 2.0
		names.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	col.add_child(cap)
	col.add_child(_scouting_link())
	return col


## "30 senior  ·  7 rookie  ·  2 injured".
func _count_line() -> String:
	var injured := 0
	for p in GameState.my_list:
		if int(p.get("injury_weeks", 0)) > 0:
			injured += 1
	var count := "%d senior  ·  %d rookie" % [RookieList.senior_count(GameState.my_list),
			RookieList.rookie_count(GameState.my_list)]
	if injured > 0:
		count += "  ·  %d injured" % injured
	return count


## The captain and his deputies by name (a phone row, by surname so all three fit).
func _captains(surnames: bool) -> String:
	var named := PackedStringArray()
	for id in Captaincy.ids(GameState.captaincy_record(GameState.my_club)):
		for q in GameState.my_list:
			if str(q.get("id", "")) == str(id):
				named.append(GameDB.player_surname(q) if surnames else GameDB.player_display_name(q))
	return ", ".join(named) if not named.is_empty() else "No captain named"


## The Full list stage: the lists' spots, then every man ranked best first, down then across.
func _full_stage() -> Control:
	var page := UiKit.vbox(UiKit.Space.CLOSE)
	page.name = "FullStage"
	page.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var top := UiKit.hbox(UiKit.GAP)
	page.add_child(top)
	_spots(top, page)
	var hint := UiKit.lbl("Tap a name for his profile", UiKit.SMALL, UiKit.MUTED)
	hint.autowrap_mode = TextServer.AUTOWRAP_OFF
	top.add_child(hint)
	var ranked: Array = GameState.my_list.duplicate()
	ranked.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
	var per := ceili(ranked.size() / 3.0)
	var grid := UiKit.hbox(UiKit.Space.GUTTER)
	grid.name = "FullColumns"
	grid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	page.add_child(grid)
	for c in range(3):
		var v := VBoxContainer.new()
		v.name = "FullColumn_%d" % c
		v.add_theme_constant_override("separation", 0)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		v.size_flags_vertical = Control.SIZE_EXPAND_FILL
		grid.add_child(v)
		v.add_child(_numbers_head())
		var men := ranked.slice(c * per, mini(ranked.size(), (c + 1) * per))
		for q in men:
			v.add_child(_compact_row(q))
		# Every column has as many slots as the first, so rows line up across.
		for i in range(per - men.size()):
			var pad := Control.new()
			pad.size_flags_vertical = Control.SIZE_EXPAND_FILL
			pad.custom_minimum_size = Vector2(0, 22)
			pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
			v.add_child(pad)
	return page


## The lists' spots on one line, in the phone's words; a club over its Category B
## spots says why under it, never "3 / 2" with no reason.
func _spots(top: Control, page: Control) -> void:
	var seniors := RookieList.seniors(GameState.my_list)
	var rookies := RookieList.rookies(GameState.my_list).filter(func(q): return not RookieList.is_cat_b(q))
	var cat_b := RookieList.rookies(GameState.my_list).filter(func(q): return RookieList.is_cat_b(q))
	var heads := [["SeniorListHead", "Senior list  %d / %d" % [seniors.size(), RookieList.senior_spots()]],
			["RookieListHead", "Rookie list  %d / %d" % [rookies.size(), RookieList.cat_a_spots()]]]
	var over_b: bool = cat_b.size() > RookieList.cat_b_spots()
	if not cat_b.is_empty():
		heads.append(["CatBListHead", "Category B rookies  %d" % cat_b.size() if over_b
				else "Category B rookies  %d / %d" % [cat_b.size(), RookieList.cat_b_spots()]])
	var spots := UiKit.hbox(UiKit.Space.WIDER)
	spots.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(spots)
	for h in heads:
		var l := UiKit.lbl(str(h[1]), UiKit.BODY, UiKit.EMPH, true)
		l.name = str(h[0])
		l.autowrap_mode = TextServer.AUTOWRAP_OFF
		spots.add_child(l)
	if over_b:
		var why := UiKit.lbl("The club's real 2026 list had %d. A club usually has %d spots for them. They take no rookie list spot and don't count in the 44." % [
				cat_b.size(), RookieList.cat_b_spots()], UiKit.SMALL, UiKit.MUTED)
		why.name = "CatBListWhy"
		why.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		page.add_child(why)


## A column's head: OVR and POT over the rows' numbers.
func _numbers_head() -> Control:
	var hc := UiKit.hbox(UiKit.Space.CLOSE)
	hc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	hc.custom_minimum_size = Vector2(0, 22)
	var push := Control.new()
	push.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hc.add_child(push)
	for t in ["OVR", "POT"]:
		var th := UiKit.line(t, UiKit.SMALL, UiKit.MUTED, true)
		th.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		th.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
		th.custom_minimum_size = Vector2(24, 0)
		th.size_flags_vertical = Control.SIZE_SHRINK_END
		hc.add_child(th)
	return hc


## One man in one line of the Full list stage: guernsey, name, then what stops him
## playing if anything (else his marks and who he is), his rating and potential.
func _compact_row(p: Dictionary) -> Control:
	var row := Button.new()
	row.name = "Row_" + str(p["id"])
	row.custom_minimum_size = Vector2(0, 22)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.focus_mode = Control.FOCUS_NONE
	for state in ["normal", "hover", "pressed", "focus"]:
		row.add_theme_stylebox_override(state, UiKit.line_row(state == "hover" or state == "pressed"))
	row.pressed.connect(_open_profile.bind(str(p["id"])))
	UiKit.feel(row, "soft")
	var h := UiKit.hbox(UiKit.Space.CLOSE)
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(h)
	var num := UiKit.figure(str(p["num"]), UiKit.NAME, UiKit.club_ink(GameState.my_club))
	num.name = "Guernsey"
	num.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	num.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	num.custom_minimum_size = Vector2(24, 0)
	h.add_child(num)
	var name_l := UiKit.ellipsis(GameDB.player_display_name(p), UiKit.SMALL, UiKit.TEXT, true)
	name_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(name_l)
	var info := UiKit.hbox(UiKit.Space.CLOSE)
	info.name = "RowInfo"
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.size_flags_stretch_ratio = 1.1
	info.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(info)
	_info_bits(info, p)
	var ov := UiKit.line(str(int(p["overall"])), UiKit.BODY, UiKit.TEXT, true)
	ov.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	ov.custom_minimum_size = Vector2(24, 0)
	ov.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(ov)
	var pot := UiKit.line("%d" % int(p.get("potential", p["overall"])), UiKit.SMALL, UiKit.MUTED)
	pot.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	pot.custom_minimum_size = Vector2(24, 0)
	pot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(pot)
	for n in h.find_children("*", "Control", true, false):
		(n as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	return row


## The compact row's middle: what keeps him out (and his concussions) when anything
## does; else his marks (untouchable, his chemistry), then who he is. The last
## piece gives way first when the column is narrow.
func _info_bits(info: Control, p: Dictionary) -> void:
	var bits: Array = []
	var status := _status(p)
	var knocks := GameState.concussions_in_window(p)
	if str(status[0]) != "":
		bits.append(["RowStatus", str(status[0]), status[1], true])
	if knocks >= MedicalPanel.SHOWN_FROM:
		bits.append(["RowConcussions", MedicalPanel.count_text(knocks), UiKit.BAD, true])
	if bits.is_empty():
		if GameState.is_untouchable(str(p["id"])):
			bits.append(["RowUntouchable", "Untouchable", UiKit.TEXT, true])
		if TeamFamiliarity.tag(p) != "":
			bits.append(["RowFamiliarity", TeamFamiliarity.tag(p), UiKit.TEXT, false])
		var who := PackedStringArray()
		if RookieList.is_cat_b(p):
			who.append("Cat B")
		elif RookieList.is_rookie(p):
			who.append("Rookie")
		who.append(Roles.label(p))
		if float(p.get("age", 0.0)) > 0.0:
			who.append("%d" % int(p["age"]))
		bits.append(["RowIdentity", " · ".join(who), UiKit.MUTED, false])
	for i in range(bits.size()):
		var b: Array = bits[i]
		if i > 0:
			info.add_child(UiKit.lbl("·", UiKit.SMALL, UiKit.MUTED))
		var l := UiKit.ellipsis(str(b[1]), UiKit.SMALL, b[2], bool(b[3]))
		l.name = str(b[0])
		if i == bits.size() - 1:
			l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		else:
			l.text_overrun_behavior = TextServer.OVERRUN_NO_TRIMMING
		info.add_child(l)


## A phone: show the pane the tabs ask for, building it the first time it is shown.
func _show_pane() -> void:
	var key := _pane
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
	if _pane == "shape":
		var page := UiKit.vbox(UiKit.Space.EASY)
		page.name = "ShapePage"
		var page_scroll := UiKit.scroll(page)
		page_scroll.name = "ShapeScroll"
		pane_root = page_scroll
		host = page
	else:
		host = UiKit.vbox(UiKit.Space.EASY)
		host.name = "ListPage"
		host.size_flags_vertical = Control.SIZE_EXPAND_FILL
		pane_root = host

	# How the side stacks up, in words, and who is available.
	var head := UiKit.lbl(GameState.my_line_standing_text(), UiKit.SMALL, UiKit.TEXT)
	head.name = "LineStanding"
	head.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	host.add_child(head)
	host.add_child(UiKit.lbl(_count_line(), UiKit.SMALL, UiKit.MUTED))
	var cap_link := UiKit.section_link("Captaincy", _captains(true) + "  ›", "CaptaincyOpen")
	cap_link.pressed.connect(func(): _open_captaincy())
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
	host.add_child(_scouting_link())

	var tabs := UiKit.hbox(UiKit.Space.SLIM)
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

	var body := UiKit.vbox(UiKit.Space.ROOM)
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	host.add_child(body)
	if _pane == "shape":
		body.add_child(_shape_panel())
	else:
		body.add_child(_full_list_panel())
	return pane_root


func _shape_panel() -> Control:
	# On a phone the page's scroll rail takes 20 px of the width; the panel's
	# padding gives some of it back so the cards keep their full names (the
	# sweep: "Andy Moniz-Wakefield" needs 116 px, the squeezed card gave 114).
	var left := UiKit.panel(UiKit.PANEL, UiKit.Space.CLOSE if _narrow() else UiKit.Space.PAD)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.custom_minimum_size = Vector2(0, 220)
	var lv := UiKit.vbox(UiKit.Space.SNUG)
	lv.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(lv)
	lv.add_child(UiKit.lbl("Best 23", UiKit.H2, UiKit.EMPH, true))
	var shape_note := UiKit.lbl("Six defenders, six midfielders with the ruck, six forwards and five on the bench. Tap a guernsey.",
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
	# At 960 the oval shows numbers only (director's pick B, 2026-11-26): names can't be read there.
	oval.names_shown = UiKit.view_height(self) >= 640.0
	oval.setup(_squad.ground, _squad.bench, GameState.my_club, not GameState.my_selection().is_empty())
	lv.add_child(oval)
	return left


func _full_list_panel() -> Control:
	var right := UiKit.panel(UiKit.PANEL, UiKit.Space.PAD)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var rv := UiKit.vbox(UiKit.Space.SNUG)
	rv.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(rv)
	rv.add_child(UiKit.lbl("Full list", UiKit.H2, UiKit.EMPH, true))
	var lbox := UiKit.vbox(0)
	lbox.name = "ListRows"
	rv.add_child(UiKit.scroll(lbox))

	# Two lists (row 88): the senior list, then the rookie list, each with its spots.
	var seniors := RookieList.seniors(GameState.my_list)
	var rookies := RookieList.rookies(GameState.my_list).filter(func(q): return not RookieList.is_cat_b(q))
	var cat_b := RookieList.rookies(GameState.my_list).filter(func(q): return RookieList.is_cat_b(q))
	var sh := UiKit.lbl("Senior list  %d / %d" % [seniors.size(), RookieList.senior_spots()], UiKit.BODY, UiKit.EMPH, true)
	sh.name = "SeniorListHead"
	lbox.add_child(sh)
	_role_groups(lbox, seniors, false)
	lbox.add_child(UiKit.spacer(UiKit.GAP))
	var rh := UiKit.lbl("Rookie list  %d / %d" % [rookies.size(), RookieList.cat_a_spots()], UiKit.BODY, UiKit.EMPH, true)
	rh.name = "RookieListHead"
	lbox.add_child(rh)
	if rookies.is_empty():
		var none := UiKit.lbl("No rookies yet. The Rookie Draft and the mid-season rookie draft fill these spots.",
				UiKit.SMALL, UiKit.MUTED)
		none.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		lbox.add_child(none)
	else:
		_role_groups(lbox, rookies, true)
	# Category B rookies have their own two spots, outside the 44 (real lists).
	if not cat_b.is_empty():
		lbox.add_child(UiKit.spacer(UiKit.GAP))
		# A club that started with more than two, as its real 2026 list had
		# (GWS: three), shows the count alone and says why: "3 / 2" is no rule.
		var over_b: bool = cat_b.size() > RookieList.cat_b_spots()
		var bh := UiKit.lbl("Category B rookies  %d" % cat_b.size() if over_b
				else "Category B rookies  %d / %d" % [cat_b.size(), RookieList.cat_b_spots()], UiKit.BODY, UiKit.EMPH, true)
		bh.name = "CatBListHead"
		lbox.add_child(bh)
		var why_words := "They have their own spots. They take no rookie list spot and don't count in the 44."
		if over_b:
			why_words = "The club's real 2026 list had %d. A club usually has %d spots for them. They take no rookie list spot and don't count in the 44." % [
					cat_b.size(), RookieList.cat_b_spots()]
		var why := UiKit.lbl(why_words,
				UiKit.SMALL, UiKit.MUTED)
		why.name = "CatBListWhy"
		why.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		lbox.add_child(why)
		_role_groups(lbox, cat_b, true)
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
		g.sort_custom(func(a, b): return int(Rating.ovr(a)) > int(Rating.ovr(b)))
		lbox.add_child(UiKit.spacer(UiKit.Space.TIGHT))
		# STYLE-05: each position heads its group in its role colour at name
		# weight (role colours are ink only, style guide 2.1), not small grey.
		var gh := UiKit.lbl("%s  (%d)" % [UiKit.ROLE_LABEL[r], g.size()],
				UiKit.NAME, UiKit.ROLE_COLOUR[r], true)
		gh.name = "RoleHead_" + r
		lbox.add_child(gh)
		for p in g:
			lbox.add_child(_list_row(p))
		lbox.add_child(UiKit.spacer(UiKit.Space.CLOSE))


## His number on your club's guernsey: everyone on this list plays for you,
## whatever club he came from (p["club"] can be his source club after a
## league re-draft).
##
## STYLE-05: the number is painted, not boxed - the scoreboard's Display cut
## with its shade, in your club's ink (club_ink keeps it readable on the
## page), so the column reads as a team sheet rather than a pile of chips.
func _guernsey(p: Dictionary) -> Label:
	var num := UiKit.figure(str(p["num"]), UiKit.NUMBER, UiKit.club_ink(GameState.my_club))
	num.name = "Guernsey"
	num.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return num


## One player in one line: guernsey, name, who he is (type, age, height),
## anything that stops him playing, and how good he is. Tap for his profile.
func _list_row(p: Dictionary) -> Control:
	var row := Button.new()
	row.name = "Row_" + str(p["id"])
	row.custom_minimum_size = Vector2(0, 56)
	row.focus_mode = Control.FOCUS_NONE
	for state in ["normal", "hover", "pressed", "focus"]:
		row.add_theme_stylebox_override(state, UiKit.line_row(state == "hover" or state == "pressed"))
	row.pressed.connect(_open_profile.bind(str(p["id"])))
	# It answers a finger as every button does: it presses in, sounds and buzzes.
	UiKit.feel(row, "soft")
	var h := UiKit.hbox(UiKit.GAP)
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
	# His familiarity (row 125): a line of its own, the same way.
	if TeamFamiliarity.tag(p) != "":
		var fam := UiKit.ellipsis(TeamFamiliarity.tag(p), UiKit.SMALL, UiKit.TEXT)
		fam.name = "RowFamiliarity"
		fam.mouse_filter = Control.MOUSE_FILTER_IGNORE
		who.add_child(fam)
		row.custom_minimum_size = Vector2(0, 92 if GameState.is_untouchable(str(p["id"])) else 74)
	# His concussions in five years, once they matter (MedicalPanel): a line of
	# its own under his details, with what is keeping him out above it when
	# something is, so his name is never cut for either.
	var knocks := GameState.concussions_in_window(p)
	var status := _status(p)
	if knocks >= MedicalPanel.SHOWN_FROM:
		var lines := 1
		if str(status[0]) != "":
			var out := UiKit.ellipsis(str(status[0]), UiKit.SMALL, status[1], true)
			out.name = "RowStatus"
			out.mouse_filter = Control.MOUSE_FILTER_IGNORE
			who.add_child(out)
			lines = 2
		var conc := UiKit.ellipsis(MedicalPanel.count_text(knocks), UiKit.SMALL, UiKit.BAD, true)
		conc.name = "RowConcussions"
		conc.mouse_filter = Control.MOUSE_FILTER_IGNORE
		who.add_child(conc)
		row.custom_minimum_size = Vector2(0, maxf(row.custom_minimum_size.y, 56.0) + 18.0 * lines)
	elif str(status[0]) != "":
		var st := UiKit.line(str(status[0]), UiKit.SMALL, status[1], true)
		st.name = "RowStatus"
		st.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(st)
	var nums := UiKit.vbox(0)
	nums.alignment = BoxContainer.ALIGNMENT_CENTER
	nums.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(nums)
	var ov := UiKit.line(str(int(Rating.ovr(p))), 20, UiKit.TEXT, true)
	ov.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	ov.custom_minimum_size = Vector2(40, 0)
	nums.add_child(ov)
	var pot := UiKit.line("POT %d" % int(p.get("potential", Rating.ovr(p))), UiKit.TINY, UiKit.MUTED)
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
				"detail": block if block != "" else "He takes a senior spot: %d of %d used. His wage rises to the senior minimum, %s a season." % [
						used, RookieList.senior_spots(), Contracts.money(RookieList.senior_wage(GameState.season_year))],
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


## The scouting list (row 130, ScoutingScene): a row like Captaincy's, saying
## how many prospects are on it.
func _scouting_link() -> Control:
	var n := ScoutingList.rows(GameState).size()
	var b := UiKit.section_link("Scouting list", "%d of %d  ›" % [n, ScoutingList.LIMIT], "ScoutingOpen")
	b.pressed.connect(func(): Router.go("scouting"))
	if not _narrow():
		# A PC's link fills the facts column beside the oval, like the Captaincy row above it.
		b.size_flags_horizontal = Control.SIZE_FILL
		b.custom_minimum_size = Vector2(0, 48)
	var value: Node = b.find_child("SectionLeadsTo", true, false)
	if value is Label:
		(value as Label).add_theme_color_override("font_color", UiKit.TEXT)
	return b
