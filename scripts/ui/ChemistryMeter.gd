class_name ChemistryMeter
extends RefCounted
## The Team Chemistry meter above the oval, and the sheet a tap on it opens: what is
## acting on the side, drawn more than written (row 125, director 2026-11-10: "players
## who play together get better at playing together"; "teams with a lot of new players
## take time to gel"; "when we can explain info visually rather than with copy, its
## better"). The trait line combinations stay apart. The sim doesn't read any of this.

const NAME_W := 110.0
const PCT_W := 44.0
const OFF_W := 84.0
const PIP := 22.0
const PIP_GAP := 8.0
const FADE_H := 112.0
const ROW_H := 30.0
## A bar tall enough to carry its figure, and the least fill the figure fits inside.
const FIGURE_H := 22.0
const FIGURE_PAD := 6.0
const FIGURE_INSIDE := 0.3


## A drawn bar, 0 to 1: a dim track and the fill. Passes every touch through.
static func bar(share: float, colour: Color, h := 10.0, fill_name := "") -> Control:
	var holder := Control.new()
	holder.custom_minimum_size = Vector2(0, h)
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	holder.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var track := ColorRect.new()
	track.color = Color(1, 1, 1, 0.14)
	track.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(track)
	track.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var fill := ColorRect.new()
	fill.color = colour
	fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if fill_name != "":
		fill.name = fill_name
	holder.add_child(fill)
	fill.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	fill.anchor_right = clampf(share, 0.0, 1.0)
	return holder


## The bar with its figure written in it (director, 2026-11-11: "its hard to
## tell if the chem bar is full or not, add a number in the bar with %"). The
## figure rides the end of the fill, so it moves with it; on a short fill it
## stands just past the end, on the track.
static func figure_bar(share: float, colour: Color, fill_name: String) -> Control:
	var holder := bar(share, colour, FIGURE_H, fill_name)
	var fill: Control = holder.get_child(1)
	var fig := UiKit.line("", UiKit.SMALL, UiKit.TEXT, true)
	fig.name = "ChemistryFigure"
	fig.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fig.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	fill.add_child(fig)
	_set_figure(fill, share)
	return holder


## 100% only when the side is fully settled: a figure never rounds up to full.
static func percent(share: float) -> int:
	return clampi(int(floor(share * 100.0 + 0.0001)), 0, 100)


static func _set_figure(fill: Control, share: float) -> void:
	var fig: Label = fill.get_node_or_null("ChemistryFigure") if fill != null else null
	if fig == null:
		return
	fig.text = "%d%%" % percent(share)
	var inside := share >= FIGURE_INSIDE
	fig.add_theme_color_override("font_color", UiKit.ink_on((fill as ColorRect).color) if inside else UiKit.TEXT)
	fig.anchor_left = 1.0
	fig.anchor_right = 1.0
	fig.anchor_top = 0.0
	fig.anchor_bottom = 1.0
	fig.grow_horizontal = Control.GROW_DIRECTION_BEGIN if inside else Control.GROW_DIRECTION_END
	var w := fig.get_combined_minimum_size().x
	fig.offset_left = (-w - FIGURE_PAD) if inside else FIGURE_PAD
	fig.offset_right = -FIGURE_PAD if inside else (w + FIGURE_PAD)
	fig.offset_top = 0.0
	fig.offset_bottom = 0.0


## A man's chemistry as a bar with its figure, for his profile.
static func familiarity_row(p: Dictionary, colour: Color) -> Control:
	var row := UiKit.hbox(10)
	row.add_child(UiKit.line("Chemistry", UiKit.BODY, UiKit.TEXT, true))
	row.add_child(bar(TeamFamiliarity.value(p) / TeamFamiliarity.FULL, colour))
	row.add_child(UiKit.line("%d%%" % roundi(TeamFamiliarity.value(p)), UiKit.BODY, UiKit.TEXT, true))
	return row


static func _ink() -> Color:
	return UiKit.club_ink(GameState.my_club)


static func _share() -> float:
	return TeamFamiliarity.chemistry(GameState.familiarity_side())


## The meter: thumb-sized, the whole strip is the target.
static func meter(on_tap: Callable) -> Button:
	var b := Button.new()
	b.name = "ChemistryMeter"
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(0, 48)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var row := UiKit.hbox(10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(row)
	row.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	row.add_child(UiKit.line("Team Chemistry", UiKit.BODY, UiKit.TEXT, true))
	var share := _share()
	row.add_child(figure_bar(share, _ink(), "ChemistryFill"))
	row.add_child(UiKit.line("›", UiKit.NAME, UiKit.TEXT, true))
	b.set_meta("share", share)
	b.pressed.connect(on_tap)
	return b


## The side changed: the bar moves to where it now stands.
static func refresh(b: Button) -> void:
	var share := _share()
	var fill: Control = b.find_child("ChemistryFill", true, false)
	UiKit.fill_bar(fill, float(b.get_meta("share", share)), share)
	_set_figure(fill, share)
	b.set_meta("share", share)


## What is acting on the side. It states the facts and never says what to do.
static func open(host: Control, on_close := Callable()) -> Control:
	var side := GameState.familiarity_side()
	var ink := _ink()
	var box := UiKit.modal_box(host, 560.0, 0.0)
	var overlay: Control = box["overlay"]
	overlay.name = "ChemistrySheet"
	UiKit.close_on_outside_tap(box, on_close)
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.lbl("Team Chemistry", UiKit.H1, UiKit.TEXT, true))
	v.add_child(figure_bar(TeamFamiliarity.chemistry(side), ink, "SheetChemistryFill"))

	var men := TeamFamiliarity.new_club_men(side)
	v.add_child(UiKit.spacer(6))
	v.add_child(_head("Men from other clubs", ink))
	v.add_child(_count_row(men.size(), ink))

	v.add_child(UiKit.spacer(6))
	var cost := UiKit.hbox(10)
	cost.name = "ChemistryCost"
	var pts := UiKit.figure(str(TeamFamiliarity.team_points(side)), UiKit.HERO, UiKit.TEXT)
	pts.name = "ChemistryPoints"
	cost.add_child(pts)
	var words := UiKit.vbox(0)
	words.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	words.add_child(UiKit.line("points worse", UiKit.BODY, UiKit.TEXT, true))
	words.add_child(UiKit.line("this round", UiKit.SECONDARY, UiKit.TEXT))
	cost.add_child(words)
	v.add_child(cost)
	v.add_child(UiKit.line("Time to gel: with %d or more, points worse by round" % TeamFamiliarity.TEAM_ARRIVALS, UiKit.SECONDARY, UiKit.TEXT))
	v.add_child(_fade(TeamFamiliarity.fade_step(side), ink))

	var others := []
	for p in side:
		if TeamFamiliarity.value(p) < TeamFamiliarity.FULL and not men.has(p):
			others.append(p)
	v.add_child(UiKit.spacer(6))
	if men.is_empty() and others.is_empty():
		var none := UiKit.line("Nobody new in this side.", UiKit.BODY, UiKit.TEXT)
		none.name = "ChemistryNobody"
		v.add_child(none)
	else:
		v.add_child(_columns())
		var rows := UiKit.vbox(0)
		rows.name = "ChemistryMen"
		for p in men:
			rows.add_child(_man_row(p, ink))
		v.add_child(rows)
		if not others.is_empty():
			v.add_child(UiKit.spacer(6))
			var head := _head("Draftees and first-gamers", ink)
			head.add_child(UiKit.line("Don't count", UiKit.SECONDARY, UiKit.TEXT))
			v.add_child(head)
			var rest := UiKit.vbox(0)
			rest.name = "ChemistryDraftees"
			for p in others:
				rest.add_child(_man_row(p, ink))
			v.add_child(rest)
	var close := UiKit.btn("Close", UiKit.NAME)
	close.name = "ChemistryClose"
	close.custom_minimum_size = Vector2(0, 48)
	close.pressed.connect(func() -> void:
		overlay.queue_free()
		if on_close.is_valid():
			on_close.call())
	box["footer"].add_child(close)
	return overlay


static func _head(text: String, ink: Color) -> HBoxContainer:
	var row := UiKit.hbox(8)
	var l := UiKit.line(text, UiKit.NAME, UiKit.club_name_colour(ink), true)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(l)
	return row


## The count against the threshold as a picture: a pip per man, the threshold's pip
## ringed and numbered.
static func _count_row(n: int, ink: Color) -> Control:
	var limit: int = TeamFamiliarity.TEAM_ARRIVALS
	var pips := Control.new()
	pips.name = "ChemistryPips"
	pips.set_meta("men", n)
	pips.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pips.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pips.custom_minimum_size = Vector2(0, PIP + 22.0)
	pips.draw.connect(func() -> void:
		var shown := maxi(limit, n)
		var pitch := minf(PIP + PIP_GAP, pips.size.x / float(shown))
		var font: Font = UiKit.BOLD
		for i in range(shown):
			var c := Vector2(pitch * (i + 0.5), PIP / 2.0 + 1.0)
			if i < n:
				pips.draw_circle(c, minf(PIP, pitch - 2.0) / 2.0, ink)
			else:
				pips.draw_circle(c, minf(PIP, pitch - 2.0) / 2.0, Color(1, 1, 1, 0.14))
			if i == limit - 1:
				pips.draw_arc(c, minf(PIP, pitch - 2.0) / 2.0 + 2.0, 0.0, TAU, 32, UiKit.TEXT, 2.0, true)
				pips.draw_string(font, Vector2(c.x - pitch / 2.0, PIP + 20.0), str(limit),
						HORIZONTAL_ALIGNMENT_CENTER, pitch, UiKit.px(UiKit.SECONDARY), UiKit.TEXT))
	return pips


## Rounds 1 to 7 as falling columns, this side's round lit.
static func _fade(step: int, ink: Color) -> Control:
	var chart := Control.new()
	chart.name = "ChemistryFade"
	chart.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chart.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	chart.custom_minimum_size = Vector2(0, FADE_H)
	chart.set_meta("step", step)
	var values: Array = TeamFamiliarity.fade_points()
	chart.draw.connect(func() -> void:
		var font: Font = UiKit.BOLD
		var fs := UiKit.px(UiKit.SECONDARY)
		var col_w := chart.size.x / float(values.size())
		var foot := chart.size.y - 22.0
		var tall := foot - 22.0
		var top := float(values[0])
		for i in range(values.size()):
			var pts := float(values[i])
			var lit: bool = i == step
			var h := tall * pts / top
			var x := col_w * i
			if h > 0.0:
				chart.draw_rect(Rect2(x + 4.0, foot - h, col_w - 8.0, h), ink if lit else Color(ink, 0.45))
			chart.draw_string(font, Vector2(x, foot - h - 5.0), str(int(pts)),
					HORIZONTAL_ALIGNMENT_CENTER, col_w, fs, UiKit.TEXT)
			chart.draw_string(font, Vector2(x, chart.size.y - 4.0), "R%d" % (i + 1),
					HORIZONTAL_ALIGNMENT_CENTER, col_w, fs, UiKit.TEXT))
	return chart


static func _columns() -> Control:
	var row := UiKit.hbox(8)
	var fam := UiKit.line("Chemistry, up 5% a game", UiKit.SECONDARY, UiKit.TEXT)
	fam.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(fam)
	var off := UiKit.line("Off his footy", UiKit.SECONDARY, UiKit.TEXT)
	off.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	off.custom_minimum_size = Vector2(OFF_W, 0)
	row.add_child(off)
	return row


static func _man_row(p: Dictionary, ink: Color) -> Control:
	var row := UiKit.hbox(8)
	row.name = "ChemistryMan_" + str(p["id"])
	row.custom_minimum_size = Vector2(0, ROW_H)
	var who := UiKit.ellipsis(GameDB.player_display_name(p), UiKit.BODY, UiKit.TEXT)
	who.custom_minimum_size = Vector2(NAME_W, 0)
	row.add_child(who)
	row.add_child(bar(TeamFamiliarity.value(p) / TeamFamiliarity.FULL, ink))
	var pct := UiKit.line("%d%%" % roundi(TeamFamiliarity.value(p)), UiKit.SECONDARY, UiKit.TEXT, true)
	pct.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	pct.custom_minimum_size = Vector2(PCT_W, 0)
	row.add_child(pct)
	var off := UiKit.line(TeamFamiliarity.own_percent(p), UiKit.SECONDARY, UiKit.TEXT)
	off.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	off.custom_minimum_size = Vector2(OFF_W, 0)
	row.add_child(off)
	return row
