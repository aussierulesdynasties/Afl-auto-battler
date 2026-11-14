class_name StatsCoach
extends RefCounted
## Season stats > Coach: your own record (P-39, director "Yes" 2026-10-18).
## Your seasons in charge in one line, the players you drafted who won your
## best and fairest or made the All-Australian team, and the board's verdict
## on each season. Everything is read from what the career recorded
## (CoachLedger); nothing is estimated, and an empty part says so plainly.

const ROW_H_PHONE := 44


static func build(host: Control) -> Control:
	var v := UiKit.vbox(6)
	v.name = "StatsCoach"
	_record(v)
	_draftees(host, v)
	_board(host, v)
	return v


## "3 seasons · 41-25-0 · finals twice · 1 premiership" (Almanac.coach_record).
static func _record(v: Control) -> void:
	_title(v, "Your record")
	var t := Almanac.coach_record(Almanac.rows(GameState.almanac, GameState.honour_roll))
	var n := int(t["seasons"])
	if n == 0:
		v.add_child(_para("Your record starts when your first season ends.", "CoachRecordEmpty"))
		return
	var finals := int(t["finals_years"])
	var flags := int(t["flags"])
	var bits := PackedStringArray([
		"%d season%s" % [n, "" if n == 1 else "s"],
		"%d-%d-%d" % [int(t["w"]), int(t["l"]), int(t["d"])],
		"no finals" if finals == 0 else ("finals once" if finals == 1 else "finals %d times" % finals),
		"no premierships" if flags == 0 else "%d premiership%s" % [flags, "" if flags == 1 else "s"],
	])
	# Each part stays whole on a phone: a line breaks only between them.
	for i in range(bits.size()):
		bits[i] = bits[i].replace(" ", "\u00a0")
	var l := UiKit.lbl("  ·  ".join(bits), UiKit.H2, UiKit.TEXT, true)
	l.name = "CoachRecordLine"
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(l)
	# Coach of the Year (CoachOfYear.gd): the seasons you won it.
	CoachSheet.add_coty(v, GameState.my_coach_of_year_years(), GameState.coach_of_year_reasons(""))


static func _draftees(host: Control, v: Control) -> void:
	_title(v, "Players you drafted")
	var rows := CoachLedger.draftees(GameState.honour_roll, StatsAwards._find, GameState.my_club,
			GameState.season_year, GameState.my_first_season, GameState.start_mode)
	if rows.is_empty():
		v.add_child(_para("No one yet. A player you draft shows here once he wins our best and fairest. Making the All-Australian team counts too.",
				"DrafteesEmpty"))
		return
	var list := UiKit.vbox(2)
	list.name = "Draftees"
	for i in range(rows.size()):
		list.add_child(_draftee_row(host, rows[i], i % 2 == 1))
	v.add_child(list)


## His name, what he won, and how you drafted him. Tap: his profile, while he
## is in the game.
static func _draftee_row(host: Control, r: Dictionary, band: bool) -> Control:
	var id := str(r["id"])
	var club := str(r["club"])
	var lines := PackedStringArray()
	var bf: Array = r["bf"]
	if not bf.is_empty():
		lines.append("%s %s" % [BestAndFairest.award_name(club), _years(bf)])
	var aa: Array = r["aa"]
	if not aa.is_empty():
		lines.append("All-Australian %s" % _years(aa))
	var col := UiKit.vbox(0)
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	var name := UiKit.line(GameState.award_name({"id": id}), UiKit.NAME, UiKit.TEXT, true)
	name.name = "Name"
	col.add_child(name)
	var won := UiKit.lbl("  ·  ".join(lines), UiKit.SECONDARY, StatsSide.ink(club), true)
	won.name = "Honours"
	won.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(won)
	var how := UiKit.lbl(CoachLedger.draft_words(r["draft"]) + ".", UiKit.SMALL, UiKit.MUTED)
	how.name = "Drafted"
	how.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(how)
	var face := StatsSide.row_style(club, band, club == GameState.my_club)
	face.content_margin_left = StatsSide.RULE_INSET + 4
	face.content_margin_right = 8
	face.content_margin_top = 6
	face.content_margin_bottom = 6
	var p := StatsAwards._find(id)
	var box: Control
	if p.is_empty():
		# He has left the game: his row stays, with no profile to open.
		var panel := PanelContainer.new()
		panel.add_theme_stylebox_override("panel", face)
		panel.add_child(col)
		box = panel
	else:
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		b.mouse_filter = Control.MOUSE_FILTER_PASS
		b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		for state in ["normal", "focus", "hover", "pressed", "hover_pressed"]:
			b.add_theme_stylebox_override(state, face)
		var m := MarginContainer.new()
		m.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		for side in ["left", "right", "top", "bottom"]:
			m.add_theme_constant_override("margin_" + side, int(face.get("content_margin_" + side)))
		m.add_child(col)
		b.add_child(m)
		_ignore_mouse(m)
		b.pressed.connect(func(): StatsAwards.open_player(host, id))
		# A button does not grow with its children: its height is theirs.
		b.custom_minimum_size.y = maxf(ROW_H_PHONE, col.get_combined_minimum_size().y + 12.0)
		col.minimum_size_changed.connect(func():
			if is_instance_valid(b):
				b.custom_minimum_size.y = maxf(ROW_H_PHONE, col.get_combined_minimum_size().y + 12.0))
		box = b
	box.name = "Draftee_" + id
	return box


static func _board(host: Control, v: Control) -> void:
	_title(v, "The board's verdict")
	var rows := CoachLedger.verdicts(GameState.board, GameState.honour_roll, GameState.my_club,
			GameState.season_year)
	if rows.is_empty():
		v.add_child(_para("The board gives its first verdict when your first season ends.", "VerdictsEmpty"))
		return
	var list := UiKit.vbox(2)
	list.name = "Verdicts"
	for i in range(rows.size()):
		var r: Dictionary = rows[i]
		var club := str(r["club"])
		var face := StatsSide.row_style(club, i % 2 == 1, club == GameState.my_club)
		face.content_margin_left = StatsSide.RULE_INSET + 4
		face.content_margin_right = 8
		face.content_margin_top = 6
		face.content_margin_bottom = 6
		var panel := PanelContainer.new()
		panel.name = "Verdict_%d" % int(r["year"])
		panel.add_theme_stylebox_override("panel", face)
		var row := UiKit.hbox(12)
		panel.add_child(row)
		var when := UiKit.vbox(0)
		when.custom_minimum_size.x = 56
		var year := UiKit.line(str(int(r["year"])), UiKit.H2, StatsSide.ink(club), true)
		year.name = "Year"
		when.add_child(year)
		var code := UiKit.line(GameDB.club_short(club), UiKit.SMALL, StatsSide.code_ink(club))
		when.add_child(code)
		row.add_child(when)
		var col := UiKit.vbox(0)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var said := UiKit.lbl(str(r["verdict"]), UiKit.NAME, UiKit.TEXT, true)
		said.name = "Said"
		said.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		col.add_child(said)
		var goal := UiKit.lbl(CoachLedger.goal_line(r), UiKit.SECONDARY, UiKit.MUTED)
		goal.name = "Goal"
		goal.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		col.add_child(goal)
		row.add_child(col)
		list.add_child(panel)
	v.add_child(list)


## "2029", "2029, 2031", "2029-2031".
static func _years(ys: Array) -> String:
	var s := ys.duplicate()
	s.sort()
	var runs := PackedStringArray()
	var i := 0
	while i < s.size():
		var j := i
		while j + 1 < s.size() and int(s[j + 1]) == int(s[j]) + 1:
			j += 1
		runs.append(str(int(s[i])) if j == i else ("%d, %d" % [int(s[i]), int(s[j])] if j == i + 1
				else "%d-%d" % [int(s[i]), int(s[j])]))
		i = j + 1
	return ", ".join(runs)


static func _title(v: Control, text: String) -> void:
	var air := Control.new()
	air.custom_minimum_size.y = 12
	air.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(air)
	v.add_child(StatsSide.heading(text))


static func _para(text: String, node_name: String) -> Label:
	var l := UiKit.lbl(text, UiKit.SECONDARY, UiKit.TEXT)
	l.name = node_name
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


static func _ignore_mouse(n: Node) -> void:
	if n is Control:
		(n as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	for c in n.get_children():
		_ignore_mouse(c)
