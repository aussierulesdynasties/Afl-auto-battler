class_name NameInk
extends RefCounted
## A player's name in running text wears his club's colour, so whose side he is
## on reads at a glance without "(Giants)" after it (design bible, readability:
## "a player's or club's allegiance is obvious at a glance"; director
## 2026-10-14, tester feedback).
##
## Appearance only. The club comes from the players' records for the screen
## (a match's squads, or a club's list), never from the sentence: build an index
## once with `from_squads` / `from_clubs`, then hand it to `label` with any
## line that names players. A name two clubs both carry is left plain rather
## than guessed. The colour is UiKit.club_ink (4.5:1 on the dark page); the
## weight and size are the line's own.

## Surnames that are also everyday words at the start of a sentence: a lone
## surname that is one of these is not tinted (the full name still is).
const COMMON_WORDS := ["Day", "Young", "Long", "Short", "Hall", "Will", "Rich", "Bird",
		"Free", "Wood", "Hill", "Gray", "Grey", "Brown", "Green", "White", "Black"]


## A name is never broken across two lines: its spaces are no-break spaces in the
## text shown ("Jacob van Rooyen" wraps before Jacob, never inside; the
## lead's capture check, 2026-10-18). `plain` metadata keeps the ordinary words for anything reading them.
const NBSP := "\u00A0"


## {name text -> club code} for the players in `squads`: an Array of Arrays of
## player dictionaries ("id", and the display name from GameDB), one per side,
## with `codes` the club for each side. Full names, and the surname alone where
## no one else in the index shares it.
static func from_squads(squads: Array, codes: Array) -> Dictionary:
	var lists := []
	for i in range(mini(squads.size(), codes.size())):
		lists.append({"club": str(codes[i]), "players": squads[i]})
	return _index(lists)


## The same from clubs' lists in the game data.
static func from_clubs(codes: Array) -> Dictionary:
	var lists := []
	for c in codes:
		lists.append({"club": str(c), "players": GameDB.club_list(str(c))})
	return _index(lists)


## The same from the season's lists (GameState.season.lists: code -> players),
## which follow trades and re-drafts; `codes` limits it to some clubs (all when
## empty).
static func from_lists(season_lists: Dictionary, codes := []) -> Dictionary:
	var lists := []
	for c in (codes if not codes.is_empty() else season_lists.keys()):
		if season_lists.has(c):
			lists.append({"club": str(c), "players": season_lists[c]})
	return _index(lists)


static func _index(lists: Array) -> Dictionary:
	var out := {}
	var clash := {}
	for entry in lists:
		var club := str(entry["club"])
		for p in entry["players"]:
			var full := GameDB.player_display_name(p)
			if full == "" or full == "Player":
				continue
			_add(out, clash, full, club, str(p.get("id", "")))
			var parts := full.split(" ", false)
			if parts.size() >= 2:
				var sur: String = parts[parts.size() - 1]
				if sur.length() >= 3 and not COMMON_WORDS.has(sur):
					_add(out, clash, sur, club, str(p.get("id", "")))
	for k in clash:
		out.erase(k)
		out.erase("#" + str(k))
	_add_clubs(out)
	return out


## Every club's name in the same index: in its colours and a tap to its page
## (ClubLink; rulings no. 113, "reached by tapping any club name"). All clubs,
## so "North Melbourne" claims its words before "Melbourne" can. A ground named
## for a city ("Adelaide Oval") is held as plain words so its city is not read
## as the club. A player's name already in the index keeps its place.
static func _add_clubs(out: Dictionary) -> void:
	for code in GameDB.clubs:
		var name := GameDB.club_name(str(code))
		if name.length() >= 3 and not out.has(name):
			out[name] = str(code)
			out["#" + name] = ClubLink.SCHEME + str(code)
	for code in GameDB.clubs:
		var ground := str((GameDB.clubs[code] as Dictionary).get("ground", ""))
		for g in [ground, GameDB.ground_shown(ground)]:
			if g != "" and not out.has(g):
				out[g] = ""


## `key` is a name that is his club's; "#<key>" beside it is his id, so a tap on
## the name can open his profile (NameLink). Keys starting "#" are not names.
## A surname two players of one club share keeps the club's ink but opens no one.
static func _add(out: Dictionary, clash: Dictionary, key: String, club: String, id := "") -> void:
	if out.has(key) and str(out[key]) != club:
		clash[key] = true
	if out.has("#" + key) and str(out["#" + key]) != id:
		out["#" + key] = ""
	elif id != "":
		out["#" + key] = id
	out[key] = club


## The colour of a player's name in running text: his club's ink, red clubs
## included (rulings: "Every name in running text is in club ink (UiKit.club_ink,
## never club_name_colour)"; director 2026-11-12, "sanders uncoloured?" of an
## Essendon player drawn white). Only a club heading's name turns white
## (UiKit.club_name_colour), so a player at Essendon, Melbourne, St Kilda,
## Sydney or Gold Coast still shows whose he is.
static func player_ink(club: String) -> Color:
	return UiKit.club_ink(club)


## `text` as BBCode: each name in `index` wrapped in its club's ink, the rest
## escaped. Empty when the text names no one in the index. `clubs` false leaves
## club names as plain words (a button, whose own tap is the point).
## `as_club` true puts each player in exactly his club's name colour, red clubs
## included (a list of club moves where every name wears its colours; director
## 2026-11-12, row 176: "no colour coding on names").
static func markup(text: String, index: Dictionary, clubs := true, as_club := false) -> String:
	var spans := spans_in(text, index)
	var out := ""
	var at := 0
	var named := false
	for s in spans:
		var shown := text.substr(int(s[0]), int(s[1]) - int(s[0]))
		var id := str(index.get("#" + shown, ""))
		if str(s[2]) == "" or (not clubs and id.begins_with(ClubLink.SCHEME)):
			continue   # plain words: a ground, or a club where clubs are off
		named = true
		out += _escape(text.substr(at, int(s[0]) - at))
		# A club's own name: its strongest real colour (ClubLink.colour); a
		# player's name: his club's ink (player_ink), or with `as_club` exactly his
		# club's name colour.
		var col := ClubLink.colour(str(s[2])) if id.begins_with(ClubLink.SCHEME) or as_club else player_ink(str(s[2]))
		var ink := "[color=#%s]%s[/color]" % [col.to_html(false), _escape(shown).replace(" ", NBSP)]
		out += NameLink.url(ink, id) if id != "" else ink
		at = int(s[1])
	if not named:
		return ""
	return out + _escape(text.substr(at))


## The names found, as [start, end, club] in text order. Longer names claim
## their place first ("Tom Stewart" before "Stewart").
static func spans_in(text: String, index: Dictionary) -> Array:
	var spans := []
	if index.is_empty() or text.is_empty():
		return spans
	var keys: Array = index.keys()
	keys.sort_custom(func(a, b): return str(a).length() > str(b).length())
	for k in keys:
		var key := str(k)
		if key.begins_with("#"):
			continue
		var from := 0
		while true:
			var i := text.find(key, from)
			if i < 0:
				break
			from = i + key.length()
			if not _edge(text, i - 1, true) or not _edge(text, i + key.length(), false):
				continue
			var free := true
			for s in spans:
				if i < int(s[1]) and i + key.length() > int(s[0]):
					free = false
					break
			if free:
				spans.append([i, i + key.length(), str(index[k])])
	spans.sort_custom(func(a, b): return int(a[0]) < int(b[0]))
	return spans


## Whether the character at `at` ends a word (so a name there is a whole word).
static func _edge(text: String, at: int, before: bool) -> bool:
	if at < 0 or at >= text.length():
		return true
	var ch := text.unicode_at(at)
	var letter := (ch >= 65 and ch <= 90) or (ch >= 97 and ch <= 122) or ch >= 192 or (ch >= 48 and ch <= 57)
	# An apostrophe after a name ("Worrell's") still ends it.
	return not letter


static func _escape(t: String) -> String:
	var out := ""
	for ch in t:
		out += "[lb]" if ch == "[" else ("[rb]" if ch == "]" else ch)
	return out


## A line of coach-facing text: a plain Label (UiKit.lbl) unless it names a
## player in `index`, then a RichTextLabel set the same (face, size, colour,
## wrap) with each name in its club's ink. Taps and swipes pass through it as
## they do a Label. `plain` rides on it as metadata for anything that reads the
## words.
static func label(text: String, index: Dictionary, fs := UiKit.BODY, color := UiKit.AUTO_COLOUR, bold := false, as_club := false) -> Control:
	var bb := markup(text, index, true, as_club)
	if bb == "":
		return UiKit.lbl(text, fs, color, bold)
	if color == UiKit.AUTO_COLOUR:
		color = UiKit.TEXT
	var r := rich(fs, color, bold)
	r.text = bb
	r.set_meta("plain", text)
	return r


## An empty RichTextLabel set up like UiKit.lbl, for a line whose words change
## (set them with `set_line`). `fs` is a role, grown with the text size; a size
## read back from a control that already has it passes `scaled`.
static func rich(fs := UiKit.BODY, color := UiKit.AUTO_COLOUR, bold := false, wrap := true, scaled := false) -> RichTextLabel:
	if color == UiKit.AUTO_COLOUR:
		color = UiKit.TEXT
	var r := RichTextLabel.new()
	r.bbcode_enabled = true
	r.fit_content = true
	r.scroll_active = false
	r.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# A name in a line opens his profile on a tap (NameLink) unless the line sits
	# inside a button, whose own tap it must not take. The club's ink says it is a
	# name; no underline.
	r.meta_underlined = false
	r.tree_entered.connect(func() -> void: _link_names(r))
	r.add_theme_font_override("normal_font", UiKit.BOLD if bold else UiKit.FONT)
	r.add_theme_font_override("bold_font", UiKit.BOLD)
	UiKit.set_font_size(r, fs, "normal_font_size", scaled)
	UiKit.set_font_size(r, fs, "bold_font_size", scaled)
	r.add_theme_color_override("default_color", color)
	return r


## Meta on a container whose whole area is one tap: names inside it open nothing.
const NO_LINKS := "name_links_off"


static func _link_names(r: RichTextLabel) -> void:
	var n := r.get_parent()
	while n != null:
		if n is BaseButton or n.has_meta(NO_LINKS):
			return
		n = n.get_parent()
	NameLink.wire(r)


## Set a `rich` line's words, each name in the index in its club's ink.
static func set_line(r: RichTextLabel, text: String, index: Dictionary) -> void:
	var bb := markup(text, index)
	r.text = bb if bb != "" else _escape(text)
	r.set_meta("plain", text)


## A button whose words name players: the names drawn in their clubs' ink over
## the button's own text, which stays as it is (its size, its `text`, what a
## screen reader or a test reads) with its colour made clear. Nothing changes
## for a button naming no one in the index. Call after the button is styled.
static func dress_button(b: Button, index: Dictionary) -> void:
	var bb := markup(b.text, index, false)
	if bb == "":
		return
	var fs := b.get_theme_font_size("font_size")
	var r := rich(fs, b.get_theme_color("font_color"), false, b.autowrap_mode != TextServer.AUTOWRAP_OFF, true)
	r.add_theme_font_override("normal_font", b.get_theme_font("font"))
	r.text = bb
	r.set_meta("plain", b.text)
	var margin := 0.0
	var sb := b.get_theme_stylebox("normal")
	if sb != null:
		margin = sb.get_content_margin(SIDE_LEFT)
	var col := VBoxContainer.new()
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(col)
	col.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	col.offset_left = margin
	col.offset_right = -margin
	col.add_child(r)
	for k in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color",
			"font_hover_pressed_color", "font_disabled_color"]:
		b.add_theme_color_override(k, Color(0, 0, 0, 0))


## The words a line shows, whichever kind of label carries it.
static func plain(c: Control) -> String:
	if c.has_meta("plain"):
		return str(c.get_meta("plain"))
	if c is Label:
		return (c as Label).text
	if c is RichTextLabel:
		return (c as RichTextLabel).get_parsed_text()
	return ""
