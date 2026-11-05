extends Control
## The club almanac (plan step 1c; Almanac.gd, switch "club_almanac"): the
## coach's career, one page per season, newest first. Read-only: everything
## here was written at a season's end from what the sim really did.

var _root: VBoxContainer
## The club whose records the records card shows: your club unless picked.
var _records_club := ""


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.season == null or not Almanac.on():
		Router.replace("hub" if GameState.season != null else "main")
		return
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	_root = UiKit.vbox(9)
	margin.add_child(_root)
	get_viewport().size_changed.connect(func():
		if is_inside_tree() and not UiKit.keyboard_resize(self):
			var places := UiKit.scroll_places(_root)
			_build()
			UiKit.restore_places(_root, places))
	_build()


func _build() -> void:
	UiKit.clear(_root)
	_root.add_child(UiKit.top_bar("Club Almanac", true))
	var page := UiKit.vbox(UiKit.SECTION)
	page.name = "AlmanacPage"
	_root.add_child(UiKit.scroll(page))
	var seasons := Almanac.rows(GameState.almanac, GameState.honour_roll)
	page.add_child(_coach_card(Almanac.coach_record(seasons)))
	if not GameState.club_records.is_empty():
		page.add_child(_records_card())
	var legends := _all_legends(seasons)
	if not legends.is_empty():
		page.add_child(_legends_card(legends))
	if seasons.is_empty():
		var none := UiKit.lbl("Your first season goes in the almanac when its Grand Final is played.",
				UiKit.BODY, UiKit.MUTED)
		none.name = "AlmanacEmpty"
		none.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		page.add_child(none)
	for e in seasons:
		var card := _season_card(e)
		card.name = "AlmanacSeason_%d" % int(e.get("year", 0))
		page.add_child(card)


## Club records (kept for every club; your club first, others by the picker).
func _records_card() -> Control:
	if _records_club == "" or not GameState.club_records.has(_records_club):
		_records_club = GameState.my_club
	var card := UiKit.panel(UiKit.PANEL, 14)
	card.name = "ClubRecords"
	var v := UiKit.vbox(4)
	card.add_child(v)
	v.add_child(UiKit.section("Club records"))
	var codes: Array = GameState.club_records.keys()
	codes.sort_custom(func(a, b): return GameDB.club_name(str(a)) < GameDB.club_name(str(b)))
	var pick := OptionButton.new()
	pick.name = "ClubRecordsPick"
	for i in range(codes.size()):
		pick.add_item(GameDB.club_name(str(codes[i])), i)
		pick.set_item_metadata(i, str(codes[i]))
		if str(codes[i]) == _records_club:
			pick.select(i)
	pick.item_selected.connect(func(i: int):
		_records_club = str(pick.get_item_metadata(i))
		var places := UiKit.scroll_places(_root)
		_build()
		UiKit.restore_places(_root, places))
	v.add_child(pick)
	for row in Almanac.club_record_rows(GameState, _records_club):
		var who := str(row.get("who", ""))
		_row(v, str(Almanac.CLUB_RECORD_NAMES[row["key"]]), "%d%s  ·  %s, %d" % [int(row.get("value", 0)),
				"  ·  " + who if who != "" else "", str(row.get("label", "")), int(row.get("year", 0))],
				"ClubRecord_" + str(row["key"]))
	return card


## Every legend on every page, newest season first.
func _all_legends(seasons: Array) -> Array:
	var out := []
	for e in seasons:
		for lg in e.get("legends", []):
			var row: Dictionary = (lg as Dictionary).duplicate()
			row["year"] = int(e.get("year", 0))
			out.append(row)
	return out


func _legends_card(legends: Array) -> Control:
	var card := UiKit.panel(UiKit.PANEL, 14)
	card.name = "LegendsCard"
	var v := UiKit.vbox(4)
	card.add_child(v)
	v.add_child(UiKit.section("Legends"))
	for lg in legends:
		var why: Array = lg.get("why", [])
		var tail := ", ".join(PackedStringArray(why.map(func(w): return str(w)))) if not why.is_empty() \
				else "%d games, %d goals" % [int(lg.get("games", 0)), int(lg.get("goals", 0))]
		_row(v, str(int(lg.get("year", 0))), "%s  ·  %s" % [str(lg.get("name", "")), tail],
				"LegendRow_" + str(lg.get("id", "")))
	return card


## The coach's own line: the one figure is the flags.
func _coach_card(t: Dictionary) -> Control:
	var card := UiKit.panel(UiKit.PANEL, 14)
	card.name = "CoachRecord"
	var v := UiKit.vbox(4)
	card.add_child(v)
	v.add_child(UiKit.section("Your record"))
	var flags := int(t["flags"])
	var head := UiKit.lbl("%d premiership%s" % [flags, "" if flags == 1 else "s"], UiKit.TITLE,
			UiKit.club_vivid(GameState.my_club), true)
	head.name = "CoachFlags"
	v.add_child(head)
	var n := int(t["seasons"])
	var line := UiKit.lbl("%d season%s  ·  %d-%d-%d  ·  finals in %d, won %d of %d" % [
			n, "" if n == 1 else "s", int(t["w"]), int(t["l"]), int(t["d"]),
			int(t["finals_years"]), int(t["finals_w"]), int(t["finals_w"]) + int(t["finals_l"])],
			UiKit.SECONDARY, UiKit.TEXT)
	line.name = "CoachLine"
	line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(line)
	return card


func _season_card(e: Dictionary) -> Control:
	var club := str(e.get("club", GameState.my_club))
	var flag := bool(e.get("flag", false))
	var card := UiKit.panel(UiKit.PANEL, 14)
	var v := UiKit.vbox(4)
	card.add_child(v)
	var head := UiKit.hbox(10)
	head.add_child(UiKit.figure(str(int(e.get("year", 0))), UiKit.H1, UiKit.club_vivid(club)))
	if club != "":
		var badge := UiKit.club_badge(club, UiKit.NAME, false, true)
		badge.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		head.add_child(badge)
	v.add_child(head)
	# The story of the season, under the header.
	var story := str(e.get(Almanac.STORY_KEY, ""))
	if story != "":
		var s := UiKit.lbl(story, UiKit.BODY, UiKit.TEXT)
		s.name = "StoryOfTheSeason"
		s.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(s)
	var bits := []
	if int(e.get("ladder", 0)) > 0:
		bits.append("%s on the ladder" % GameState.ordinal(int(e["ladder"])))
	if e.has("w"):
		bits.append("%d-%d-%d" % [int(e["w"]), int(e["l"]), int(e.get("d", 0))])
	if str(e.get("finals_text", "")) != "":
		bits.append(str(e["finals_text"]))
	if not bits.is_empty():
		var l := UiKit.lbl("  ·  ".join(PackedStringArray(bits)), UiKit.NAME,
				UiKit.club_vivid(club) if flag else UiKit.TEXT, flag)
		l.name = "SeasonLine"
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(l)
	if str(e.get("premier", "")) != "" and not flag:
		_row(v, "Premiers", GameDB.club_name(str(e["premier"])), "Premiers")
	_row(v, BestAndFairest.award_name(club), _first_name(e.get("bf", [])), "BestAndFairest")
	var sh: Array = e.get("season_hero", [])
	if not sh.is_empty():
		var n := int(sh[0].get("count", 0))
		_row(v, "Season hero", "%s, hero %d time%s" % [str(sh[0].get("name", "")), n, "" if n == 1 else "s"], "SeasonHero")
	var gk: Dictionary = e.get("goalkicker", {})
	if not gk.is_empty():
		_row(v, "Leading goalkicker", "%s, %d" % [str(gk.get("name", "")), int(gk.get("goals", 0))], "Goalkicker")
	var bl: Array = e.get("brownlow", [])
	if not bl.is_empty():
		var b: Dictionary = bl[0]
		_row(v, "Brownlow Medal", "%s (%s)" % [_name_of(b), GameDB.club_name(str(b.get("club", "")))], "Brownlow")
	var gfist: Array = e.get("golden_fist", [])
	if not gfist.is_empty():
		var f: Dictionary = gfist[0]
		_row(v, Awards.GOLDEN_FIST_SHORT, "%s (%s)" % [_name_of(f), GameDB.club_name(str(f.get("club", "")))], "GoldenFist")
	for r in e.get("records", []):
		_row(v, "Record", str(r), "Record")
	for lg in e.get("legends", []):
		_row(v, "Farewell", "%s  ·  %d games, %d goals" % [str(lg.get("name", "")), int(lg.get("games", 0)),
				int(lg.get("goals", 0))], "Legend")
	for r in e.get("club_records_broken", []):
		_row(v, "Club record", str(r), "ClubRecordBroken")
	if bool(e.get("partial", false)):
		var p := UiKit.lbl("Played before the almanac was kept: the honour roll's record only.",
				UiKit.SMALL, UiKit.MUTED)
		p.name = "PartialNote"
		p.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(p)
	return card


func _row(v: VBoxContainer, what: String, text: String, node: String) -> void:
	if text == "":
		return
	var h := UiKit.hbox(8)
	h.name = node
	var a := UiKit.lbl(what, UiKit.SECONDARY, UiKit.MUTED)
	a.custom_minimum_size.x = 150
	a.autowrap_mode = TextServer.AUTOWRAP_OFF
	h.add_child(a)
	var b := UiKit.lbl(text, UiKit.SECONDARY, UiKit.TEXT)
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(b)
	v.add_child(h)


func _first_name(rows) -> String:
	if not (rows is Array) or (rows as Array).is_empty():
		return ""
	return _name_of(rows[0])


func _name_of(r: Dictionary) -> String:
	return str(r["name"]) if r.has("name") else GameState.award_name(r)
