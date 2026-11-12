extends Control
## The scouting list (row 130, ScoutingList), reached from My list: the
## prospects your scouts watch every week, and the rest of the coming class to
## add from. Each row gives your recruiters' read of him (OVR and POT ranges),
## the draft-fit marks your coach's archetypes put on him (DraftFit) and, for a
## listed player, how the read has moved since he went on. Facts only: no
## order of preference beyond the recruiters' own ranking.

var _root: VBoxContainer
var _built_wide := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.my_club == "":
		Router.replace("main")
		return
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	_root = UiKit.vbox(9)
	margin.add_child(_root)
	get_viewport().size_changed.connect(func():
		if is_inside_tree() and not UiKit.keyboard_resize(self) and _wide() != _built_wide:
			_build())
	_build()


func _wide() -> bool:
	return UiKit.view_width(self) >= 760.0


func _build() -> void:
	var places := UiKit.scroll_places(_root)
	UiKit.clear(_root)
	_built_wide = _wide()
	_root.add_child(UiKit.top_bar("Scouting list", true))
	var class_now: Array = ScoutingList.pool(GameState)
	if class_now.is_empty():
		var none := UiKit.lbl("The next draft class is not out yet. It opens once this year's National Draft is done.",
				UiKit.BODY, UiKit.TEXT)
		none.name = "ScoutNoClass"
		none.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_root.add_child(none)
		return
	var intro := UiKit.lbl("Your scouts watch every player on this list each week, so their read of him narrows faster. Room for %d."
			% ScoutingList.LIMIT, UiKit.SECONDARY, UiKit.TEXT)
	intro.name = "ScoutIntro"
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_root.add_child(intro)

	var reads: Dictionary = GameState.prospect_reads(class_now)
	var fit: Dictionary = DraftFit.marks(class_now, GameState.coach_arch.get("held", {}), GameState.my_club,
			GameState.prospect_read_seed(), GameState.recruiting_uncertainty_mult())
	var listed := ScoutingList.rows(GameState)
	var listed_ids := {}
	for r in listed:
		listed_ids[str(r["entry"]["id"])] = true

	var mine := UiKit.vbox(UiKit.GAP)
	mine.name = "ScoutListed"
	mine.add_child(_heading("On your list", "%d of %d" % [listed.size(), ScoutingList.LIMIT]))
	if listed.is_empty():
		var empty := UiKit.lbl("Nobody yet. Add a prospect from the class.", UiKit.BODY, UiKit.TEXT)
		empty.name = "ScoutListEmpty"
		empty.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		mine.add_child(empty)
	for r in listed:
		mine.add_child(_row(r["p"], reads, fit, r["entry"]))

	var rest := UiKit.vbox(UiKit.GAP)
	rest.name = "ScoutClass"
	rest.add_child(_heading("The class", "by your recruiters' ranking"))
	var order := class_now.duplicate()
	order.sort_custom(func(a, b):
		return int(reads[str(a["id"])]["rank"]) < int(reads[str(b["id"])]["rank"]))
	var is_full := ScoutingList.full(GameState)
	for p in order:
		if not listed_ids.has(str(p["id"])):
			rest.add_child(_row(p, reads, fit, {}, is_full))

	var body: BoxContainer = UiKit.hbox(28) if _built_wide else UiKit.vbox(UiKit.SECTION)
	body.name = "ScoutBody"
	if _built_wide:
		# PC: the list and the class side by side, each scrolling its own rows.
		for col in [mine, rest]:
			var sc := UiKit.scroll(col)
			sc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
			body.add_child(sc)
		body.size_flags_vertical = Control.SIZE_EXPAND_FILL
		_root.add_child(body)
	else:
		body.add_child(mine)
		body.add_child(rest)
		var page := UiKit.scroll(body)
		page.name = "ScoutScroll"
		page.size_flags_vertical = Control.SIZE_EXPAND_FILL
		_root.add_child(page)
	UiKit.restore_places(_root, places)


## A section's heading in your club's ink, with a quiet note after it.
func _heading(text: String, note: String) -> Control:
	var h := UiKit.hbox(10)
	var t := UiKit.lbl(text, UiKit.H2, UiKit.label_ink(), true)
	t.autowrap_mode = TextServer.AUTOWRAP_OFF
	h.add_child(t)
	var n := UiKit.lbl(note, UiKit.SECONDARY, UiKit.MUTED)
	n.autowrap_mode = TextServer.AUTOWRAP_OFF
	n.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(n)
	return h


## One prospect: name and the button, who he is and where your recruiters rank
## him, their read, the fit marks, and (listed) how the read has moved.
func _row(p: Dictionary, reads: Dictionary, fit: Dictionary, entry: Dictionary, is_full := false) -> Control:
	var id := str(p["id"])
	var r: Dictionary = reads.get(id, {})
	var on_list := not entry.is_empty()
	var v := UiKit.vbox(2)
	v.name = ("ScoutRow_" if on_list else "ClassRow_") + id
	# Name and who he is on the left, the button beside both lines: the two
	# lines fill the button's thumb height, so no gap opens under the name.
	var top := UiKit.hbox(8)
	var who := UiKit.vbox(0)
	who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	who.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var nm := UiKit.name_label(GameDB.player_display_name(p))
	nm.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	who.add_child(nm)
	who.add_child(_line("%s  ·  age %d" % [
			str(UiKit.ROLE_LABEL.get(str(p.get("role", "")), str(p.get("role", "")))),
			int(float(p.get("age", 18.0)))], UiKit.TEXT))
	# The real player he plays like at his best (director 2026-11-12): his own line.
	var like := PlaysLikeLine.make(p)
	if like != null:
		who.add_child(like)
	top.add_child(who)
	var b := UiKit.btn("Remove" if on_list else ("List full" if is_full else "Add"), UiKit.NAME)
	b.name = ("ScoutRemove_" if on_list else "ClassAdd_") + id
	b.custom_minimum_size = Vector2(96, 44)
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	b.disabled = not on_list and is_full
	b.pressed.connect(func():
		if on_list:
			ScoutingList.remove(GameState, id)
		else:
			ScoutingList.add(GameState, id)
		_build())
	top.add_child(b)
	v.add_child(top)
	v.add_child(_line("Ranked %s  ·  OVR %s  ·  POT %s" % [PreSeason.ordinal(int(r.get("rank", 0))),
			DraftScouting.range_text(r.get("overall", [0, 0])),
			DraftScouting.range_text(r.get("potential", [0, 0]))], UiKit.TEXT, true))
	for m in fit.get(id, []):
		v.add_child(_line(str(m.get("text", "")), _fit_colour(), true))
	if on_list:
		var moved := ScoutingList.change_text(entry, r)
		var l := _line(moved if moved != "" else ScoutingList.listed_when(entry) + ": the read has not moved yet",
				UiKit.TEXT if moved != "" else UiKit.MUTED)
		l.name = "ScoutChange_" + id
		v.add_child(l)
	v.add_child(UiKit.rule())
	if on_list:
		return UiKit.club_section_body(GameState.my_club, v)
	return v


func _line(text: String, colour: Color, bold := false) -> Label:
	var l := UiKit.lbl(text, UiKit.SECONDARY, colour, bold)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l


## Your club's ink for a fit mark, as on the draft board (DraftScene): a red
## club uses its second ink, so the mark reads as yours.
func _fit_colour() -> Color:
	var club: String = GameState.my_club
	var ink := UiKit.club_name_colour(UiKit.club_ink(club))
	if ink == UiKit.TEXT:
		ink = UiKit.club_name_colour(UiKit.club_ink_second(club))
	return ink
