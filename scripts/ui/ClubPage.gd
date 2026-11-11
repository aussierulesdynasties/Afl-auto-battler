class_name ClubPage
extends RefCounted
## A club's page (C-PC-15, P-53; rulings 5.11 no. 113): what a supporter knows
## about a club, opened by tapping its name anywhere (ClubLink). Its colours,
## ground, coach and captain, its trophies, the last five, the best 22 in words
## and the players it has swapped with you. Public facts only: a rival's
## ratings, moods and plans stay hidden (#759). Two places read the rival
## coach, in words only and never as numbers (RivalRead, director 2026-11-08):
## the Assistant's report on this week's opponent (WeekPreview: their list's
## fit and how well they know each plan, from hidden ratings; his habits and
## his box) and the match break sheet (MatchScene: what the scoreboard has
## him doing, from his box and his habits; why their legs are going). This
## page still shows none of it. Your own club's page leads to
## the honour board (rulings no. 112, HonourBoard). The trophies (ClubTrophies)
## moved here from Season stats (director, 2026-11-06). Under them, a club
## with a premiership side on record sets it against its list today
## (PremiershipSide, row T5.r158); a club without one shows nothing.
##
## Look-up only; nothing here touches a match or a player.

const SHEET_NAME := "ClubPage"
const BOARD_NAME := "HonourBoardSheet"
const FACTS_NAME := "HonourFacts"
const TROPHIES_NAME := "ClubTrophiesSheet"
## The best 22 in words, back to front as a team sheet reads.
const LINES := [["DEF", "Defence"], ["MID", "Midfield"], ["WING", "Wings"], ["RUCK", "Ruck"],
		["FWD", "Forwards"], ["BENCH", "Interchange"]]
const SWAPPED_SHOWN := 6
## The board's extra columns (Brownlow, All-Australian) fit from this width.
const BOARD_WIDE := 640.0


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------
static func open(host: Control, code: String) -> Control:
	var mine := code == GameState.my_club
	var box := UiKit.modal_box(host, 620.0, 0.0, _wash(code))
	var overlay: Control = box["overlay"]
	overlay.name = SHEET_NAME
	overlay.set_meta("club_code", code)
	UiKit.close_on_outside_tap(box)
	var body: VBoxContainer = box["body"]
	body.add_child(_strip(code))
	var title := UiKit.club_title(GameDB.club_name(code), UiKit.H1, code, UiKit.PANEL)
	title.name = "ClubName"
	body.add_child(title)
	var c: Dictionary = GameDB.clubs.get(code, {})
	var ground := str(c.get("ground", ""))
	if ground != "":
		body.add_child(_fact("Home ground", ground, "Ground"))
	body.add_child(_fact("Senior coach", _coach(code, mine), "Coach"))
	body.add_child(_leaders(code))

	body.add_child(UiKit.spacer(UiKit.SECTION - 8))
	var trophies := UiKit.section_link("Trophies", _flags(code) + "  ›", "TrophiesLink")
	trophies.pressed.connect(func(): open_trophies(host, code))
	body.add_child(trophies)
	var eras := _premiership_side(code)
	if eras != null:
		body.add_child(eras)

	body.add_child(UiKit.spacer(UiKit.SECTION - 8))
	body.add_child(UiKit.section("Last five"))
	body.add_child(_last_five(code))

	body.add_child(UiKit.spacer(UiKit.SECTION - 8))
	body.add_child(UiKit.section("Best 22" if not mine else "Your best 22"))
	_best22(body, code, mine)

	if not mine:
		_swapped(body, code)

	var footer: Control = box["footer"]
	if mine:
		var hb := UiKit.btn("Honour board", UiKit.BODY)
		hb.name = "HonourBoardButton"
		hb.custom_minimum_size = Vector2(0, 44)
		hb.pressed.connect(func(): open_board(host))
		footer.add_child(hb)
	var field := UiKit.btn("See the side on the ground", UiKit.BODY)
	field.name = "SideOnGround"
	field.custom_minimum_size = Vector2(0, 44)
	field.pressed.connect(func(): open_side(host, code))
	footer.add_child(field)
	var close := UiKit.btn("Close", UiKit.BODY)
	close.name = "CloseClub"
	close.custom_minimum_size = Vector2(0, 44)
	close.pressed.connect(func(): overlay.queue_free())
	footer.add_child(close)
	return overlay


## The wash at the top of a club's sheet: its vivid colour, or the black of a
## black-and-white club, never the grey of its third colour (director
## 2026-11-07, "fix Pies").
static func _wash(code: String) -> Color:
	return UiKit.club_black(code) if UiKit.club_is_black(code) else UiKit.club_vivid(code)


## The club's real colours as a band under the wash: the guernsey before the
## name. Black on the dark page keeps a light rim so it reads as black.
static func _strip(code: String) -> Control:
	var hb := UiKit.hbox(0)
	hb.name = "ClubColours"
	hb.custom_minimum_size = Vector2(0, 8)
	for c in GameDB.club_marker_colours(code):
		var col: Color = c
		var r := Panel.new()
		var sb := StyleBoxFlat.new()
		sb.bg_color = col
		if UiKit.contrast(col, UiKit.PANEL) < 1.5:
			sb.border_color = UiKit.TEXT
			sb.set_border_width_all(1)
		r.add_theme_stylebox_override("panel", sb)
		r.custom_minimum_size = Vector2(0, 8)
		r.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		hb.add_child(r)
	return hb


## "Label  value" on one line: the label muted, the fact in bold.
static func _fact(label: String, value: String, node_name: String) -> Control:
	var r := NameInk.rich(UiKit.BODY, UiKit.TEXT)
	r.name = node_name
	r.text = "[color=#%s]%s[/color]  [b]%s[/b]" % [UiKit.MUTED.to_html(false), _esc(label), value]
	NameLink.wire(r)
	return r


static func _esc(s: String) -> String:
	return s.replace("[", "[lb]")


static func _coach(code: String, mine: bool) -> String:
	if mine:
		return "You"
	var sc: Dictionary = GameState.club_staff(code).get("SC", {})
	return _esc(GameDB.player_display_name(sc)) if not sc.is_empty() else "Not named"


## Captain and vice-captain, each a tap to his profile.
static func _leaders(code: String) -> Control:
	var rec := GameState.captaincy_record(code)
	var list := _list(code)
	var parts := []
	for role in [["captain", "Captain"], ["vice", "Vice-captain"]]:
		var names := []
		for id in Captaincy.ids(rec, role[0]):
			var p := _in(list, str(id))
			if not p.is_empty():
				names.append(NameLink.url(_esc(GameDB.player_display_name(p)), str(id)))
		if not names.is_empty():
			parts.append("[color=#%s]%s[/color]  [b]%s[/b]" % [UiKit.MUTED.to_html(false), role[1], ", ".join(names)])
	var r := NameInk.rich(UiKit.BODY, UiKit.TEXT)
	r.name = "Captain"
	r.text = "\n".join(parts) if not parts.is_empty() else \
			"[color=#%s]Captain[/color]  [b]No captain named[/b]" % UiKit.MUTED.to_html(false)
	NameLink.wire(r)
	return r


## The club's last premiership side in this career against its list today
## (PremiershipSide, row T5.r158): null when none is on record. Each name
## opens his profile.
static func _premiership_side(code: String) -> Control:
	var list := _list(code)
	var r := PremiershipSide.remains(GameState.honour_roll, code, list, int(GameState.season_year))
	var words := PremiershipSide.line(r, func(id: String) -> String:
		return NameLink.url(_esc(GameDB.player_display_name(_in(list, id))), id))
	if words.is_empty():
		return null
	var l := NameInk.rich(UiKit.BODY, UiKit.TEXT)
	l.name = "PremiershipSide"
	l.text = "[color=#%s]%s[/color]" % [UiKit.MUTED.to_html(false), _esc(str(words[0]))]
	if str(words[1]) != "":
		l.text = "[color=#%s]%s:[/color]  [b]%s[/b]" % [UiKit.MUTED.to_html(false), _esc(str(words[0])), str(words[1])]
	NameLink.wire(l)
	return l


## How many flags: this career's and the club's history before it.
static func _flags(code: String) -> String:
	var years := {}
	for y in GameState.premiership_years(code):
		years[int(y)] = true
	var hist := ClubHistory.before_career(code)
	for y in hist.get("years", []):
		years[int(y)] = true
	if years.is_empty():
		return "No premierships on record"
	return "%d %s" % [years.size(), "premiership" if years.size() == 1 else "premierships"]


# ---------------------------------------------------------------------------
# Trophies (rulings 118, 118a)
# ---------------------------------------------------------------------------
## The club's trophies over its page: the flags and the players' honours of
## this career after the flags before it; for your club, your time there too.
static func open_trophies(host: Control, code: String) -> Control:
	var box := UiKit.modal_box(host, 760.0, 0.0, _wash(code))
	var overlay: Control = box["overlay"]
	overlay.name = TROPHIES_NAME
	overlay.set_meta("club_link", true)
	UiKit.close_on_outside_tap(box)
	ClubLink.keep(host, overlay)
	var body: VBoxContainer = box["body"]
	body.add_child(_strip(code))
	var title := UiKit.club_title(GameDB.club_name(code), UiKit.H1, code, UiKit.PANEL)
	title.name = "TrophiesTitle"
	body.add_child(title)
	var holder := UiKit.vbox(0)
	holder.name = "TrophiesBody"
	body.add_child(holder)
	# A filter lays the trophies out afresh in place.
	var fill := [Callable()]
	fill[0] = func() -> void:
		for c in holder.get_children():
			holder.remove_child(c)
			c.queue_free()
		holder.add_child(ClubTrophies.build(host, code, func(): (fill[0] as Callable).call_deferred()))
	(fill[0] as Callable).call()
	var close := UiKit.btn("Close", UiKit.BODY)
	close.name = "CloseTrophies"
	close.custom_minimum_size = Vector2(0, 44)
	close.pressed.connect(func(): overlay.queue_free())
	(box["footer"] as Control).add_child(close)
	return overlay


static func _list(code: String) -> Array:
	if code == GameState.my_club:
		return GameState.my_list
	var season: Season = GameState.season
	if season == null:
		return []
	return season.lists.get(code, [])


static func _in(list: Array, id: String) -> Dictionary:
	for p in list:
		if str(p.get("id", "")) == id:
			return p
	return {}


## This season's last five results, newest first; the opponent opens his page.
static func _last_five(code: String) -> Control:
	var v := UiKit.vbox(4)
	v.name = "LastFive"
	var season: Season = GameState.season
	var games := []
	if season != null:
		var rounds: Array = season.results.duplicate()
		rounds.append_array(season.finals.get("weeks", []))
		for rnd in rounds:
			for res in rnd:
				if str(res.get("home", "")) == code or str(res.get("away", "")) == code:
					games.append(res)
	if games.is_empty():
		v.add_child(UiKit.lbl("No games played yet this season.", UiKit.BODY, UiKit.MUTED))
		return v
	for i in range(games.size() - 1, maxi(-1, games.size() - 6), -1):
		var res: Dictionary = games[i]
		var side := 0 if str(res.get("home", "")) == code else 1
		var s: Array = res.get("score", [0, 0])
		var us := int(s[side])
		var them := int(s[1 - side])
		var opp := str(res.get("away" if side == 0 else "home", ""))
		var word := "Won" if us > them else ("Lost" if us < them else "Drew")
		var col := UiKit.GOOD if us > them else (UiKit.BAD if us < them else UiKit.TEXT)
		var r := NameInk.rich(UiKit.BODY, UiKit.TEXT)
		r.name = "Result%d" % (games.size() - 1 - i)
		r.text = "[color=#%s][b]%s[/b][/color] %d-%d %s %s  [color=#%s]%s[/color]" % [col.to_html(false), word, us, them,
				"v" if side == 0 else "at", ClubLink.ink(opp), UiKit.MUTED.to_html(false), _esc(str(res.get("label", "")))]
		NameLink.wire(r)
		v.add_child(r)
	return v


## The best 22 by line, in words: names only, never a rating.
static func _best22(body: VBoxContainer, code: String, mine: bool) -> void:
	var their: Dictionary
	if mine:
		their = {"side": GameState.current_side(), "list": GameState.my_list}
	else:
		their = GameState.opponent_side(code)
	var side: Dictionary = their.get("side", {})
	var list: Array = their.get("list", [])
	var season: Season = GameState.season
	var named: bool = mine or (season != null and not (season.selections.get(code, {}) as Dictionary).is_empty())
	var note := UiKit.lbl("Your side as it stands" if mine else \
			("Side named for this round" if named else "Projected side: picked on match day"), UiKit.SMALL, UiKit.MUTED)
	note.name = "SideNote"
	body.add_child(note)
	var v := UiKit.vbox(4)
	v.name = "BestSide"
	body.add_child(v)
	var ink := UiKit.club_ink(code, UiKit.PANEL)
	for ln in LINES:
		var names := []
		for id in side.get(ln[0], []):
			var p := _in(list, str(id))
			if not p.is_empty():
				names.append(NameLink.url(_esc(GameDB.player_display_name(p)), str(id)))
		if names.is_empty():
			continue
		var r := NameInk.rich(UiKit.BODY, UiKit.TEXT)
		r.name = "Line" + str(ln[0])
		r.text = "[color=#%s][b]%s[/b][/color]  %s" % [ink.to_html(false), ln[1], ", ".join(names)]
		NameLink.wire(r)
		v.add_child(r)
	if v.get_child_count() == 0:
		v.add_child(UiKit.lbl("No side named yet.", UiKit.BODY, UiKit.MUTED))


## Players who have crossed between the two clubs in this career, both ways.
static func _swapped(body: VBoxContainer, code: String) -> void:
	var season: Season = GameState.season
	if season == null:
		return
	var theirs := GameState.former_players(code)
	var ours := FormerPlayers.against(GameState.my_list, code, GameState.season_year)
	if theirs.is_empty() and ours.is_empty():
		return
	body.add_child(UiKit.spacer(UiKit.SECTION - 8))
	body.add_child(UiKit.section("Players swapped"))
	var v := UiKit.vbox(4)
	v.name = "Swapped"
	body.add_child(v)
	var mine_ink := UiKit.club_ink(GameState.my_club, UiKit.PANEL)
	var their_ink := UiKit.club_ink(code, UiKit.PANEL)
	for row in theirs.slice(0, SWAPPED_SHOWN):
		v.add_child(_swap_line(row, "Played %d for you" % int(row["games"]), their_ink))
	for row in ours.slice(0, SWAPPED_SHOWN):
		v.add_child(_swap_line(row, "Played %d for %s" % [int(row["games"]), _esc(GameDB.club_name(code))], mine_ink))


static func _swap_line(row: Dictionary, what: String, ink: Color) -> Control:
	var p: Dictionary = row["p"]
	var r := NameInk.rich(UiKit.BODY, UiKit.TEXT)
	r.name = "Swap_" + str(row["id"])
	var years := "%d" % int(row["from"]) if int(row["from"]) == int(row["to"]) else "%d-%d" % [int(row["from"]), int(row["to"])]
	r.text = "[b][color=#%s]%s[/color][/b]  %s, %s" % [ink.to_html(false),
			NameLink.url(_esc(GameDB.player_display_name(p)), str(row["id"])), what, years]
	NameLink.wire(r)
	return r


## The side as it would take the field, on the shared field view and read-only,
## over the page (moved from the ladder, which now opens the page). A player
## opens his profile over the side.
const SIDE_SHEET := "ClubSide"


static func open_side(host: Control, code: String) -> Control:
	var season: Season = GameState.season
	var mine := code == GameState.my_club
	var box := UiKit.modal_box(host, 900.0, 0.0, _wash(code))
	var overlay: Control = box["overlay"]
	overlay.name = SIDE_SHEET
	overlay.set_meta("club_link", true)
	UiKit.close_on_outside_tap(box)
	ClubLink.keep(host, overlay)
	var body: VBoxContainer = box["body"]
	if UiKit.club_is_black(code):
		body.add_child(UiKit.club_title(GameDB.club_name(code), UiKit.H2, code, UiKit.PANEL))
	else:
		body.add_child(UiKit.ellipsis(GameDB.club_name(code), UiKit.H2, UiKit.club_name_colour(UiKit.club_ink(code, UiKit.PANEL)), true))
	var outlook := GameState.team_outlook(code)
	if not outlook.is_empty():
		var tl := UiKit.lbl(str(outlook["line"]), UiKit.BODY, UiKit.TEXT)
		tl.name = "TeamOutlook"
		tl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		body.add_child(tl)
	var named: bool = mine or (season != null and not (season.selections.get(code, {}) as Dictionary).is_empty())
	var n := UiKit.lbl(_side_note(mine, named), UiKit.SMALL, UiKit.MUTED)
	n.name = "SideNote"
	body.add_child(n)
	var their: Dictionary
	if mine:
		their = {"side": GameState.current_side(), "list": GameState.my_list}
	else:
		their = GameState.opponent_side(code)
	var builder := TeamBuilder.new()
	builder.name = "TeamBuilder"
	builder.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(builder)
	var wide: bool = bool(host.call("wide")) if host.has_method("wide") 			else ScreenLayout.roomy(UiKit.view_width(host), UiKit.view_height(host))
	builder.setup(their["side"], wide, their["list"], true)
	builder.inspect.connect(func(id: String):
		for p in their["list"]:
			if str(p["id"]) == id:
				ClubLink.keep(host, NameLink.open(overlay, id))
				return)
	var close := UiKit.btn("Close", UiKit.BODY)
	close.name = "CloseSide"
	close.custom_minimum_size = Vector2(0, 44)
	close.pressed.connect(func(): overlay.queue_free())
	(box["footer"] as Control).add_child(close)
	return overlay


static func _side_note(mine: bool, named: bool) -> String:
	return "Your side as it stands" if mine else 			("Side named for this round" if named else "Projected side: picked on match day")


# ---------------------------------------------------------------------------
# The honour board (rulings no. 112)
# ---------------------------------------------------------------------------
## Every player who left your club with 150 games, a best and fairest, a
## Brownlow or a flag, newest departure first. A name opens his career facts.
static func open_board(host: Control) -> Control:
	var code := GameState.my_club
	var box := UiKit.modal_box(host, 760.0, 0.0, _wash(code))
	var overlay: Control = box["overlay"]
	overlay.name = BOARD_NAME
	overlay.set_meta("club_link", true)
	UiKit.close_on_outside_tap(box)
	ClubLink.keep(host, overlay)
	var body: VBoxContainer = box["body"]
	body.add_child(_strip(code))
	var title := UiKit.club_title("Honour board", UiKit.H1, code, UiKit.PANEL)
	title.name = "BoardTitle"
	body.add_child(title)
	var intro := UiKit.lbl("Players who left %s with 150 games, a best and fairest, a Brownlow or a flag." \
			% GameDB.club_name(code), UiKit.SMALL, UiKit.MUTED)
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(intro)
	var rows := HonourBoard.rows(GameState.honour_board, GameState.my_list)
	var table := UiKit.vbox(0)
	table.name = "BoardTable"
	body.add_child(table)
	if rows.is_empty():
		var none := UiKit.lbl("No one has left the club with 150 games, a best and fairest, a Brownlow or a flag yet.",
				UiKit.BODY, UiKit.MUTED)
		none.name = "BoardEmpty"
		none.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		table.add_child(none)
	else:
		var wide := UiKit.view_width(host) >= BOARD_WIDE
		table.add_child(_board_row(host, {}, wide, -1))
		for i in rows.size():
			table.add_child(_board_row(host, rows[i], wide, i))
	var close := UiKit.btn("Close", UiKit.BODY)
	close.name = "CloseBoard"
	close.custom_minimum_size = Vector2(0, 44)
	close.pressed.connect(func(): overlay.queue_free())
	(box["footer"] as Control).add_child(close)
	return overlay


## Column heads and widths: [key, head, width] after the name.
static func _columns(wide: bool) -> Array:
	# Narrow enough for a 320-wide phone with the sheet's margins.
	var out := [["years", "Years", 66.0], ["games", "Games", 46.0], ["goals", "Goals", 44.0],
			["bf", "B&F", 32.0], ["flags", "Flags", 38.0]]
	if wide:
		out.append_array([["brownlow", "Brownlow", 70.0], ["aa", "All-Aus", 58.0]])
	return out


static func _board_row(host: Control, row: Dictionary, wide: bool, i: int) -> Control:
	var head := i < 0
	var face := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1, 1, 1, 0.04 if i % 2 == 0 and not head else 0.0)
	sb.content_margin_left = 6
	sb.content_margin_right = 6
	if not head and not wide:
		# A phone row's name, honours and figures sit close as one block, with
		# its air at the edges of the row, not between its lines.
		sb.content_margin_top = 6
		sb.content_margin_bottom = 6
	face.add_theme_stylebox_override("panel", sb)
	# A row is a tap: 44 high at least, as every button in the game.
	face.custom_minimum_size = Vector2(0, 44 if wide and not head else (32 if wide else (24 if head else 44)))
	var hb := UiKit.hbox(4)
	var fs := UiKit.SMALL if head else UiKit.BODY
	var colour := UiKit.MUTED if head else UiKit.TEXT
	var name := UiKit.ellipsis("Player" if head else _row_name(row), UiKit.SMALL if head else UiKit.NAME,
			colour, not head)
	name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	if wide:
		face.add_child(hb)
		hb.add_child(name)
		if not head:
			name.custom_minimum_size = Vector2(0, 44)
	else:
		# A phone has no room for a name beside five figures: the name takes
		# its own line, the figures sit under it in the columns.
		var stack := UiKit.vbox(2)
		face.add_child(stack)
		if head:
			name.free()
		else:
			stack.add_child(name)
			# No room for the Brownlow and All-Australian columns: in words
			# under his name, so a medallist never reads as a blank row.
			var extra := _extra_honours(row)
			if extra != "":
				var el := UiKit.lbl(extra, UiKit.SMALL, UiKit.MUTED)
				el.name = "BoardHonours"
				el.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				stack.add_child(el)
		stack.add_child(hb)
		var pad := Control.new()
		pad.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		hb.add_child(pad)
	for col in _columns(wide):
		var t := str(col[1]) if head else _cell(row, str(col[0]))
		var l := UiKit.lbl(t, fs, colour)
		l.custom_minimum_size = Vector2(float(col[2]), 0)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		hb.add_child(l)
	if head:
		face.name = "BoardHead"
		return face
	face.name = "Board_" + str(row["id"])
	name.name = "BoardName"
	# The whole row opens him: on a phone the name alone is one short line.
	_tap(face, func(): open_row(host, row))
	return face


## "Brownlow 2031, All-Australian 2030, 2032": the honours a phone row has no column for.
static func _extra_honours(row: Dictionary) -> String:
	var parts := []
	for pair in [["brownlow", "Brownlow"], ["aa", "All-Australian"]]:
		var ys: Array = row.get(pair[0], [])
		if not ys.is_empty():
			parts.append("%s %s" % [pair[1], ", ".join(ys.map(func(y): return str(y)))])
	return ", ".join(parts)


static func _row_name(row: Dictionary) -> String:
	return GameDB.player_display_name(row.get("card", {}))


## Every empty cell on the board, whatever the column: none, or none on record.
const NONE := "-"


static func _cell(row: Dictionary, key: String) -> String:
	match key:
		"years":
			# His years with you: to his last season here, which a player who
			# left you and retired elsewhere later still reads right.
			var a := int(row.get("from", 0))
			var b := int(row.get("to", 0)) if int(row.get("to", 0)) > 0 else int(row.get("left", 0))
			if a <= 0:
				return "to %d" % b if b > 0 else NONE
			return str(a) if a == b else "%d-%02d" % [a, b % 100]
		"games", "goals":
			# Not on record (an old save's row) or none: the same dash.
			var n := int(row.get(key, 0))
			return NONE if n <= 0 else str(n)
		_:
			var n := (row.get(key, []) as Array).size()
			return str(n) if n > 0 else NONE


## A tap on a control that is not a button; a swipe still scrolls the board.
static func _tap(c: Control, fn: Callable) -> void:
	c.mouse_filter = Control.MOUSE_FILTER_PASS
	c.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var down := [Vector2.INF]
	c.gui_input.connect(func(ev: InputEvent) -> void:
		if not (ev is InputEventMouseButton and (ev as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT):
			return
		var at: Vector2 = (ev as InputEventMouseButton).global_position
		if ev.is_pressed():
			down[0] = at
		elif down[0] != Vector2.INF and at.distance_to(down[0]) <= 12.0:
			down[0] = Vector2.INF
			fn.call())


## His profile when he is still in the game (a list or the free agents); his
## career facts when he has left it. Never the league's data record, which
## would show a retired player as he was in his first season.
static func open_row(host: Control, row: Dictionary) -> Control:
	var id := str(row.get("id", ""))
	var gone: bool = ["retired", "medical"].has(str(row.get("how", ""))) or GameState.departed_names.has(id)
	if not gone and not GameState._any_player(id).is_empty():
		return ClubLink.keep(host, NameLink.open(host, id))
	return open_facts(host, row)


static func open_facts(host: Control, row: Dictionary) -> Control:
	var code := GameState.my_club
	var box := UiKit.modal_box(host, 520.0, 640.0, _wash(code))
	var overlay: Control = box["overlay"]
	overlay.name = FACTS_NAME
	overlay.set_meta("club_link", true)
	UiKit.close_on_outside_tap(box)
	ClubLink.keep(host, overlay)
	var v: VBoxContainer = box["body"]
	var name := UiKit.lbl(_row_name(row), 22, UiKit.TEXT, true)
	name.name = "FactsName"
	name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(name)
	var head := UiKit.club_title(_facts_head(row), UiKit.BODY, code, UiKit.PANEL)
	head.name = "FactsHead"
	v.add_child(head)
	var how := _how(row)
	if how != "":
		v.add_child(UiKit.lbl(how, UiKit.BODY, UiKit.TEXT))
	var honours := []
	for pair in [["bf", "Best and fairest"], ["brownlow", "Brownlow Medal"], ["flags", "Premiership"],
			["aa", "All-Australian"]]:
		var ys: Array = row.get(pair[0], [])
		if not ys.is_empty():
			honours.append("%s %s" % [pair[1], ", ".join(ys.map(func(y): return str(y)))])
	for h in honours:
		var l := UiKit.lbl(h, UiKit.BODY, UiKit.TEXT)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(l)
	var facts: Array = row.get("facts", [])
	if not facts.is_empty():
		v.add_child(UiKit.spacer(UiKit.SECTION - 8))
		v.add_child(UiKit.section("What the club remembers"))
		for f in facts:
			var l := UiKit.lbl(str(f), UiKit.BODY, UiKit.TEXT)
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			v.add_child(l)
	var close := UiKit.btn("Close", UiKit.BODY)
	close.name = "CloseFacts"
	close.custom_minimum_size = Vector2(0, 44)
	close.pressed.connect(func(): overlay.queue_free())
	(box["footer"] as Control).add_child(close)
	return overlay


static func _facts_head(row: Dictionary) -> String:
	var g := int(row.get("games", -1))
	var k := int(row.get("goals", -1))
	var years := _cell(row, "years")
	if g < 0:
		return "With the club until %d" % int(row.get("left", 0))
	return "%s: %d game%s, %d goal%s" % [years, g, "" if g == 1 else "s", k, "" if k == 1 else "s"]


static func _how(row: Dictionary) -> String:
	match str(row.get("how", "")):
		"retired":
			return "Retired after the %d season." % int(row.get("left", 0))
		"medical":
			return "Retired on medical advice during the %d season, after repeated concussions." % int(row.get("left", 0))
		"delisted":
			return "Delisted after the %d season." % int(row.get("left", 0))
		"free_agent":
			return "Left as a free agent after the %d season." % int(row.get("left", 0))
		"moved":
			var to := str(row.get("to_club", ""))
			return "Left for %s after the %d season." % [GameDB.club_name(to), int(row.get("left", 0))] if to != "" \
					else "Left the club after the %d season." % int(row.get("left", 0))
	return ""
