extends Control
## The club almanac (plan step 1c; Almanac.gd, switch "club_almanac"): the
## coach's career, one page per season, newest first. Read-only: everything
## here was written at a season's end from what the sim really did.

var _root: VBoxContainer


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
	_row(v, "Best and fairest", _first_name(e.get("bf", [])), "BestAndFairest")
	var gk: Dictionary = e.get("goalkicker", {})
	if not gk.is_empty():
		_row(v, "Leading goalkicker", "%s, %d" % [str(gk.get("name", "")), int(gk.get("goals", 0))], "Goalkicker")
	var bl: Array = e.get("brownlow", [])
	if not bl.is_empty():
		var b: Dictionary = bl[0]
		_row(v, "Brownlow Medal", "%s (%s)" % [_name_of(b), GameDB.club_name(str(b.get("club", "")))], "Brownlow")
	for r in e.get("records", []):
		_row(v, "Record", str(r), "Record")
	for lg in e.get("legends", []):
		_row(v, "Farewell", "%s  ·  %d games, %d goals" % [str(lg.get("name", "")), int(lg.get("games", 0)),
				int(lg.get("goals", 0))], "Legend")
	# The story of the season: plan step 1a fills this slot at the wrap.
	var story := str(e.get(Almanac.STORY_KEY, ""))
	if story != "":
		var s := UiKit.lbl(story, UiKit.BODY, UiKit.TEXT)
		s.name = "StoryOfTheSeason"
		s.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(s)
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
