class_name WeekPreview
extends RefCounted
## This week: what the match rests on, from the side as arranged now - the
## round, both sides' key forwards and defenders, the Assistant's report, line
## against line in the middle and the ruck, your synergies, your own news and the
## team sheet. Facts, never a verdict. One builder for every place it shows: the
## match preview, its own step between Play match and the setup (director,
## 2026-11-07), and Team selection's week column beside the oval on a wide screen.
## The report and the synergy guide open over `host`.

var host: Control
## A synergy completed from the guide changed the side: (note, side before).
var side_changed := Callable()
var _overlay: Control          # the report or the synergy guide, open over host
var _name_index := {}
var _name_key := ""


func _init(on: Control, changed := Callable()) -> void:
	host = on
	side_changed = changed


## This week: what the choice rests on, from the side as arranged now.
func page() -> Control:
	var v := UiKit.vbox(_gap())
	v.name = "WeekPage"
	fill(v)
	return v


## Line against line (your half moves with your selection), your lines, the
## synergies your side has, your own news, their key forwards. Facts, never a
## verdict. How they play is in the assistant's report.
func fill(v: VBoxContainer) -> void:
	var nxt := GameState.my_next_opponent()
	if nxt.is_empty():
		v.add_child(_strength_line())
	else:
		var code := str(nxt["code"])
		# One phrase, and the opponent is named once: over its own column below.
		var heading := UiKit.hbox(6)
		heading.name = "WeekHeading"
		# Gather Round names the event and the host ground (rule 2.38): "at home"
		# only for a club at its own ground.
		var where := ("at home" if str(nxt["venue"]) == "home" else "away")
		if nxt.has("event"):
			where = "%s at %s" % [str(nxt["event"]), str(nxt["ground"])]
		heading.add_child(UiKit.line("Round %d, %s" % [GameState.season.round_index + 1, where],
				UiKit.TITLE, UiKit.TEXT, true))
		v.add_child(heading)
		# Both sides' key forwards and defenders lead the sheet, as facts. Who
		# goes to each is set before the first ball-up, not here.
		var kp := GameState.week_key_players(code)
		if not kp.is_empty():
			v.add_child(_key_players(kp, code))
			v.add_child(_rule())
		# What your assistant has seen of them - said there, and only there.
		var report := _link_btn("Assistant's report ›")
		report.name = "AssistantReport"
		report.pressed.connect(show_report.bind(code))
		v.add_child(report)
		var lines := UiKit.vbox(22)
		lines.name = "HeadToHead"
		v.add_child(lines)
		# Midfield and ruck only: forwards against defenders is what the key
		# players above already show, side by side.
		for row in GameState.my_head_to_head(code):
			if ["midfield", "ruck"].has(str(row["key"])):
				lines.add_child(_h2h_row(row, code))
	v.add_child(_synergy_view())
	# What the week says about your own people, set apart from the facts above.
	var notes := UiKit.vbox(8)
	notes.name = "WeekNotes"
	var own := GameState.my_week_notes()
	# A key player already on the team sheet's outs is said there, once.
	var sheet_outs := {}
	for o in GameState.week_changes()["outs"]:
		sheet_outs[str(o["id"])] = true
	for f in own:
		if sheet_outs.has(str(f.get("player_id", ""))):
			continue
		# Only an injury is bad news; a milestone is a marked row of its own.
		var bad := str(f.get("key", "")) == "own_injury"
		notes.add_child(_note_row(para(str(f["text"]), UiKit.SECONDARY, UiKit.BAD if bad else UiKit.TEXT),
				UiKit.BAD if bad else Color(UiKit.TEXT, 0.45)))
	_backing_lines(notes)
	# The team sheet: who is in and out since your last match, and why.
	var changes := GameState.week_changes_text()
	if changes != "":
		var ch := para(changes, UiKit.SECONDARY, UiKit.TEXT)
		ch.name = "TeamChanges"
		notes.add_child(ch)
	if notes.get_child_count() > 0:
		v.add_child(notes)
	else:
		notes.free()


## One spacing scale for the week: 8 inside a block, 16 between blocks.
const GAP := 16


## 16 between blocks on a phone; a PC window shows the side and the week
## together with no scroll, so it spaces them closer (and clicks smaller targets).
func _gap() -> int:
	return 10 if _roomy() else GAP


func _roomy() -> bool:
	return ScreenLayout.roomy(UiKit.view_width(host), UiKit.view_height(host))
## Near-white for the facts a coach reads closely (TEXT is the full white).
const SOFT := Color("d6d2c8")


## A quiet way in: words with a chevron, left-aligned, thumb-high (48), no surface.
func _link_btn(text: String) -> Button:
	var b := UiKit.text_action(text, UiKit.NAME)
	b.custom_minimum_size = Vector2(0, 48)
	b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.add_theme_color_override("font_color", SOFT)
	var flush := StyleBoxEmpty.new()
	for state in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		b.add_theme_stylebox_override(state, flush)
	return b


## A secondary action: an outline, thumb-high (52), across the sheet. The same
## on every club - the accent is for the one primary action, and this sheet has none.
func _outline_btn(text: String) -> Button:
	var b := UiKit.btn(text, UiKit.NAME)
	b.custom_minimum_size = Vector2(0, 48 if _roomy() else 52)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var sb := UiKit.style(Color.TRANSPARENT, 8, UiKit.RADIUS, SOFT)
	sb.set_border_width_all(2)
	b.add_theme_stylebox_override("normal", sb)
	var down := sb.duplicate() as StyleBoxFlat
	down.bg_color = UiKit.SURFACE
	for state in ["hover", "pressed", "hover_pressed"]:
		b.add_theme_stylebox_override(state, down)
	return b



## "Midfield: yours below par, theirs good." as the line's name over two
## columns that match the header above: yours under your club's colour, theirs
## under theirs. "Even, both average" stays one line.
func _h2h_row(row: Dictionary, opp: String) -> Control:
	var text := str(row["text"])
	var cut := text.find(": ")
	var one := UiKit.vbox(4)
	one.name = "H2H_" + str(row["key"])
	one.set_meta("plain", text)
	if cut < 0:
		one.add_child(para(text, UiKit.SECONDARY, UiKit.TEXT))
		return one
	one.add_child(UiKit.lbl(text.substr(0, cut), UiKit.NAME, UiKit.TEXT, true))
	var rest := text.substr(cut + 2).trim_suffix(".")
	var at := rest.find(", theirs ")
	if not rest.begins_with("yours ") or at < 0:
		one.add_child(para(rest.substr(0, 1).to_upper() + rest.substr(1) + ".", UiKit.SECONDARY, SOFT))
		return one
	var inks: Array = UiKit.club_ink_pair(GameState.my_club, opp)
	var cols := UiKit.hbox(GAP)
	var parts := [["Yours", rest.substr(6, at - 6), inks[0]], ["Theirs", rest.substr(at + 9), inks[1]]]
	for part in parts:
		var c := UiKit.vbox(4)
		c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var bar := ColorRect.new()
		bar.color = part[2]
		bar.custom_minimum_size = Vector2(0, 3)
		bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
		c.add_child(bar)
		# Yours in weight (the verdict you decide on), theirs plain.
		c.add_child(UiKit.lbl("%s %s" % [part[0], part[1]], UiKit.SECONDARY,
				UiKit.club_name_colour(part[2]), true))
		cols.add_child(c)
	one.add_child(cols)
	return one


## A fact about your own people with a short bar in `ink` at its left: its own
## row, never a stray line under the buttons.
func _note_row(body: Control, ink: Color) -> Control:
	var row := UiKit.hbox(8)
	var bar := ColorRect.new()
	bar.color = ink
	bar.custom_minimum_size = Vector2(4, 0)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(bar)
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(body)
	return row


## A thin rule between the facts above and the report below.
func _rule() -> Control:
	var r := ColorRect.new()
	r.name = "SheetRule"
	r.color = Color(UiKit.TEXT, 0.14)
	r.custom_minimum_size = Vector2(0, 1)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


## A guernsey on a light tile, so a dark club (Carlton's navy) still reads on
## the dark page: 30 px of crest on a 36 px tile.
func _crest_tile(code: String) -> Control:
	var tile := PanelContainer.new()
	tile.name = "CrestTile"
	tile.add_theme_stylebox_override("panel", UiKit.style(Color("e8e4da"), 3, UiKit.RADIUS))
	tile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tile.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	tile.add_child(UiKit.club_marker(code, 30.0))
	return tile


## Both sides' key forwards and key defenders, your side on the left (marked
## "You") and theirs on the right: height and how they mark, one player a line.
## One rule for both sides: the club's readable colour as a bar over its column
## and on its name (a red club's name stays plain, as everywhere: red is the bar
## and the crest), the crest on a light tile. Rows are facts, not buttons.
func _key_players(kp: Dictionary, opp: String) -> Control:
	var tight := _roomy()
	var cols := UiKit.hbox(GAP)
	cols.name = "KeyMatchups"
	var inks: Array = UiKit.club_ink_pair(GameState.my_club, opp)
	var at := 0
	var wrap_head := false
	for c in [GameState.my_club, opp]:
		if UiKit.BOLD.get_string_size(GameDB.club_name(str(c)), HORIZONTAL_ALIGNMENT_LEFT, -1, UiKit.NAME).x > 112.0:
			wrap_head = true
	for side in ["mine", "theirs"]:
		var code: String = GameState.my_club if side == "mine" else opp
		var col := UiKit.vbox(6 if tight else GAP)
		col.name = "KeySide_" + side
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		col.size_flags_stretch_ratio = 1.0
		var bar := ColorRect.new()
		bar.name = "ClubBar"
		bar.color = inks[at]
		bar.custom_minimum_size = Vector2(0, 4)
		bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
		col.add_child(bar)
		var head := UiKit.hbox(8)
		head.name = "ClubHead"
		head.add_child(_crest_tile(code))
		var who := UiKit.vbox(0)
		who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var mark := UiKit.line("You" if side == "mine" else "Them", UiKit.SECONDARY,
				UiKit.TEXT if side == "mine" else SOFT, side == "mine")
		mark.name = "SideMark"
		who.add_child(mark)
		# The whole name, over two lines if it needs them (Greater Western Sydney).
		var nm := UiKit.lbl(GameDB.club_name(code), UiKit.NAME, UiKit.club_name_colour(inks[at]), true)
		nm.name = "ClubName"
		nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		nm.custom_minimum_size = Vector2(0, 0)
		who.add_child(nm)
		head.add_child(who)
		# Both heads stand as tall as the longer name needs, so the two columns line up.
		if wrap_head and not tight:
			head.custom_minimum_size = Vector2(0, 64)
		col.add_child(head)
		at += 1
		for group in [["fwd", "Key forwards, marking"], ["def", "Key defenders, marking"]]:
			var list: Array = (kp[side] as Dictionary)[group[0]]
			if list.is_empty():
				continue
			var sec := UiKit.vbox(4 if tight else 12)
			sec.name = "KeySection_" + str(group[0])
			# 16 before a group label (the column gap), 4 from it to its first row, 12 between rows.
			var lead := UiKit.vbox(4)
			lead.add_child(UiKit.lbl(str(group[1]), UiKit.SECONDARY, SOFT, true))
			sec.add_child(lead)
			var first := true
			for p in list:
				var one := UiKit.vbox(0)
				one.custom_minimum_size = Vector2(0, 0 if tight else 44)
				one.name = ("KeyForward_" if group[0] == "fwd" else "KeyDefender_") + str(p["id"])
				one.add_child(UiKit.ellipsis(GameDB.player_display_name(p), UiKit.NAME, UiKit.TEXT, true))
				one.add_child(_air_line(p))
				if first:
					lead.add_child(one)
					first = false
				else:
					sec.add_child(one)
			col.add_child(sec)
		cols.add_child(col)
	return cols


## "196 cm  strong": the height as plain secondary text, then the grade, which
## steps up in weight and size as it gets better (elite is the
## biggest and boldest, average the plainest) in the text colours only, so it is
## never read as GOOD or BAD. What is graded is said once, in the section label.
func _air_line(p: Dictionary) -> Control:
	var flow := HFlowContainer.new()
	flow.add_theme_constant_override("h_separation", 10)
	flow.add_theme_constant_override("v_separation", 0)
	flow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if float(p.get("height_cm", 0.0)) > 0.0:
		flow.add_child(UiKit.line("%d cm" % int(p["height_cm"]), UiKit.SECONDARY, SOFT))
	var g := PlayerProfile.grade(PlayerProfile.percentile(p, "marking")).to_lower()
	if g == "":
		g = "average"
	var size := UiKit.SECONDARY
	var bold := true
	var ink := UiKit.TEXT
	match g:
		"elite":
			size = UiKit.NAME
		"good":
			bold = false
		"average":
			bold = false
			ink = SOFT
	var gl := UiKit.line(g, size, ink, bold)
	gl.name = "Grade"
	flow.add_child(gl)
	return flow



## The line synergies your 18 switch on - what the side is good at - any
## one it is a single player short of (a fact, never a suggested swap: the
## choice is yours), and the full rules one tap away, under the line they explain.
func _synergy_view() -> Control:
	var h := UiKit.vbox(8)
	h.name = "Synergies"
	var on: PackedStringArray = []
	var lit := {}
	for r in Traits.progress(GameState.my_squad().ground):
		if bool(r["active"]):
			on.append(Traits.with_effect(str(r["key"])))
			lit[Traits.label(str(r["key"]))] = UiKit.GOOD
	# One pattern for both lines, one colour: the lead-in, the name, what it does or needs.
	var l := TraitLink.line("Your side has: " + ", ".join(on) + "." if not on.is_empty()
			else "No line synergies in this side.", UiKit.BODY, UiKit.TEXT, {}, lit)
	l.name = "SynergyLine"
	h.add_child(l)
	var short := Traits.short_words(GameState.my_squad().ground)
	if short != "":
		var s := TraitLink.line(short, UiKit.BODY, UiKit.TEXT)
		s.name = "SynergyShort"
		h.add_child(s)
	var rules := _link_btn("Synergies")
	rules.name = "SynergyRules"
	rules.pressed.connect(show_synergies)
	h.add_child(rules)
	return h


## Every synergy: what it is, what it does and exactly what it needs, with
## the ones this side has marked On.
func show_synergies() -> void:
	close_overlay()
	var box := UiKit.modal_box(host, 560.0, 0.0)
	_overlay = box["overlay"]
	_overlay.name = "SynergyGuide"
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.lbl("Line synergies", UiKit.H1, UiKit.TEXT, true))
	v.add_child(para("Players' traits combine when the right mix takes the field together.", 13, UiKit.MUTED))
	var active := {}
	for r in Traits.progress(GameState.my_squad().ground):
		active[str(r["key"])] = bool(r["active"])
	for key in Traits.SYNERGIES:
		var s: Dictionary = Traits.SYNERGIES[key]
		var row := UiKit.vbox(2)
		row.name = "Synergy_" + str(key)
		v.add_child(UiKit.spacer(6))
		v.add_child(row)
		var head := UiKit.hbox(8)
		row.add_child(head)
		var name_l := UiKit.lbl(str(s["label"]), UiKit.BODY, UiKit.TEXT, true)
		name_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		head.add_child(name_l)
		if bool(active.get(key, false)):
			head.add_child(UiKit.line("On", UiKit.SECONDARY, UiKit.GOOD, true))
		row.add_child(para("%s %s" % [str(s.get("about", "")), str(s.get("does", ""))], 13, UiKit.TEXT))
		var req := para(Traits.requirement_text(str(key)), 13, UiKit.MUTED)
		req.name = "Requires"
		row.add_child(req)
		# Who in your 18 carries each trait it needs: the facts behind On.
		var who := PackedStringArray()
		for c in Traits.carriers(str(key), GameState.my_squad().ground):
			var names: Array = []
			for p in c[1]:
				names.append(GameDB.player_display_name(p))
			var plural := str(Traits.PLURALS.get(str(c[0]), Traits.label(str(c[0])) + "s"))
			who.append("%s in your side: %s." % [plural, ", ".join(names) if not names.is_empty() else "none"])
		var wl := para("\n".join(who), 13, UiKit.TEXT)
		wl.name = "Carriers"
		row.add_child(wl)
		if not bool(active.get(key, false)):
			row.add_child(_complete_button(str(key)))
	var close := _outline_btn("Close")
	close.pressed.connect(close_overlay)
	box["footer"].add_child(close)


## Complete a synergy in one tap (director, 2026-10-07): the fewest swaps
## from your available list, then Undo if you want your side back. Disabled,
## with the reason, when your list can't do it.
func _complete_button(key: String) -> Control:
	var v := UiKit.vbox(2)
	var r: Dictionary = GameState.complete_synergy(key, GameState.current_side())
	var b := UiKit.btn("Complete %s" % str(Traits.SYNERGIES[key]["label"]).to_lower(), 14)
	b.name = "Complete_" + key
	b.custom_minimum_size = Vector2(0, 44)
	b.disabled = str(r["problem"]) != ""
	b.pressed.connect(func():
		var undo := GameState.current_side()
		var fresh: Dictionary = GameState.complete_synergy(key, GameState.current_side())
		var note := ""
		if str(fresh["problem"]) == "":
			GameState.set_selection(fresh["side"])
			note = str(fresh["note"])
		close_overlay()
		if side_changed.is_valid():
			side_changed.call(note, undo))
	v.add_child(b)
	if str(r["problem"]) != "":
		var why := para(str(r["problem"]), 12, UiKit.MUTED)
		why.name = "CompleteWhy_" + key
		v.add_child(why)
	return v


## Close the report or the synergy guide; true if one was open (Back).
func close_overlay() -> bool:
	var was := _overlay != null and is_instance_valid(_overlay)
	if was:
		_overlay.queue_free()
	_overlay = null
	return was



## The Assistant's report (director, 2026-10-07): how this week's opponent
## plays and who matters, each fact once (GameState.opponent_report). The
## line against line stays on the screen, where it moves with your side.
func show_report(code: String) -> void:
	close_overlay()
	var box := UiKit.modal_box(host, 560.0, 0.0)
	_overlay = box["overlay"]
	_overlay.name = "AssistantReportSheet"
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.lbl("Assistant's report: %s" % GameDB.club_name(code), UiKit.H1, UiKit.TEXT, true))
	var parts := GameState.opponent_report(code)
	for part in parts:
		v.add_child(UiKit.spacer(6))
		v.add_child(UiKit.lbl(str(part[0]), UiKit.BODY, UiKit.TEXT, true))
		for t in part[1]:
			v.add_child(para(str(t), 14, UiKit.TEXT))
	if parts.is_empty():
		v.add_child(para("Too early to say much about them: they have barely played.", 14, UiKit.MUTED))
	var close := _outline_btn("Close")
	close.pressed.connect(close_overlay)
	box["footer"].add_child(close)



## What you have promised: one line for each run you have given a player,
## said as a fact (Backing). Not part of the team sheet's outs: a promise to a
## player who is out still stands, and the line says it waits.
func _backing_lines(v: VBoxContainer) -> void:
	for f in GameState.backing_notes():
		var l := para(str(f["text"]), 13, UiKit.TEXT)
		l.name = "Backing_" + str(f["player_id"])
		v.add_child(l)



## Your lines against the league, in words, when there is no opponent to
## set them against (a bye, the season over).
func _strength_line() -> Control:
	var l := para(GameState.my_line_standing_text(), 14, UiKit.TEXT)
	l.name = "LineStanding"
	return l



func para(text: String, size: int, colour: Color) -> Control:
	var l := NameInk.label(text, _names(), size, colour)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


## Your players and this week's opponent's, by name, so a name in a sentence
## wears his club's colour (NameInk). Built from the lists, never from the text.
func _names() -> Dictionary:
	var nxt := GameState.my_next_opponent()
	var opp := str(nxt.get("code", ""))
	var key := "%s|%s|%d|%s" % [GameState.my_club, opp, GameState.my_list.size(), str(GameState.show_real_names)]
	if key != _name_key:
		_name_key = key
		var codes := [GameState.my_club]
		if opp != "" and opp != GameState.my_club:
			codes.append(opp)
		if GameState.season != null and GameState.season.lists.has(GameState.my_club):
			_name_index = NameInk.from_lists(GameState.season.lists, codes)
		else:
			_name_index = NameInk.from_squads([GameState.my_list], [GameState.my_club])
	return _name_index
