class_name HubSearch
extends RefCounted
## Search any player or club from the hub, and keep a shortlist (row T3.R43,
## P-65). One sheet: an empty field shows your shortlist; typing shows the
## players and clubs whose names match. A tap opens his profile or the club's
## page over the sheet (Back returns to it); a held finger puts the name on the
## shortlist, or takes it off. The coming draft class has its own list
## (My list > Scouting list, row 130), so prospects are not searched here.
## Look-up only; no effect on the game.

const SHEET_NAME := "HubSearch"
## Fewest letters before names are searched (one letter matches half the league).
const MIN_LETTERS := 2
## Most matches listed; a longer name narrows it.
const MAX_RESULTS := 30
const ROW_H := 48


## Open the sheet over the screen `from` is on. Returns the overlay.
static func open(from: Node, text := "") -> Control:
	var host := ClubLink.host_of(from)
	if host == null:
		return null
	close_open(host)
	var box := UiKit.modal_box(host, 480.0, 0.0)
	var overlay: Control = box["overlay"]
	overlay.name = SHEET_NAME
	UiKit.close_on_outside_tap(box)
	var v: VBoxContainer = box["body"]
	v.add_theme_constant_override("separation", 6)
	var field := UiKit.search_field(text, "Search players and clubs")
	field.name = "SearchField"
	v.add_child(field)
	var results := UiKit.vbox(2)
	results.name = "SearchResults"
	v.add_child(results)
	field.text_changed.connect(func(_t: String): _fill(results, field.text))
	_fill(results, text)
	var close := UiKit.btn("Close", UiKit.NAME, true)
	close.name = "SearchClose"
	close.custom_minimum_size = Vector2(0, 48)
	close.pressed.connect(func() -> void: overlay.queue_free())
	box["footer"].add_child(close)
	return overlay


## Back closes an open search before the screen sees it. True when it did.
static func close_open(scene: Node) -> bool:
	if scene == null:
		return false
	for c in scene.get_children():
		if c.name == SHEET_NAME and not c.is_queued_for_deletion():
			c.queue_free()
			c.name = "HubSearchClosing"
			return true
	return false


## The ids whose names match `text`: clubs first, then players; names that
## start with it before names that only contain it, then by name.
static func matches(text: String) -> Array:
	var q := text.strip_edges().to_lower()
	if q.length() < MIN_LETTERS:
		return []
	var clubs: Array = []
	# Only clubs in the league this season: Tasmania is not a name to find before it joins.
	for code in GameDB.active_clubs(GameState.season_year):
		var nm := GameDB.club_name(str(code))
		if nm.to_lower().contains(q) or GameDB.club_short(str(code)).to_lower().contains(q) or str(code).to_lower() == q:
			clubs.append([0 if nm.to_lower().begins_with(q) else 1, nm, ClubLink.SCHEME + str(code)])
	var players: Array = []
	if GameState.season != null:
		for code in GameState.season.lists:
			for p in GameState.season.lists[code]:
				var nm := str(p.get("name", ""))
				var low := nm.to_lower()
				if not low.contains(q):
					continue
				var starts := low.begins_with(q) or low.contains(" " + q)
				players.append([0 if starts else 1, nm, str(p.get("id", ""))])
	var by := func(a, b): return a[0] < b[0] or (a[0] == b[0] and str(a[1]) < str(b[1]))
	clubs.sort_custom(by)
	players.sort_custom(by)
	var out: Array = []
	for r in clubs + players:
		if out.size() >= MAX_RESULTS:
			break
		out.append(str(r[2]))
	return out


## What a row says and the ink it is in: [name, the line after it, club code].
static func describe(id: String) -> Array:
	if id.begins_with(ClubLink.SCHEME):
		var code := id.substr(ClubLink.SCHEME.length())
		return [GameDB.club_name(code), "Club", code]
	var p := NameLink.find(id)
	if p.is_empty():
		return []
	var code := _club_of(id, p)
	var bits := [GameDB.club_short(code) if code != "" else "", DraftNight.position_words(p)]
	if p.has("age"):
		bits.append("%d" % int(p["age"]))
	return [str(p.get("name", "")), "  ·  ".join(bits.filter(func(s): return str(s) != "")), code]


static func _club_of(id: String, p: Dictionary) -> String:
	if GameState.season != null:
		for code in GameState.season.lists:
			for q in GameState.season.lists[code]:
				if str(q.get("id", "")) == id:
					return str(code)
	return str(p.get("club", ""))


static func _fill(results: VBoxContainer, text: String) -> void:
	UiKit.clear(results)
	var q := text.strip_edges()
	var ids: Array
	if q.length() < MIN_LETTERS:
		var head := UiKit.lbl("Your shortlist", UiKit.NAME, UiKit.TEXT, true)
		head.name = "ShortlistHead"
		results.add_child(head)
		ids = GameState.shortlist.duplicate()
		if ids.is_empty():
			var none := UiKit.lbl("Hold a name in the results to keep it here.", UiKit.SMALL, UiKit.MUTED)
			none.name = "ShortlistEmpty"
			none.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			results.add_child(none)
	else:
		ids = matches(q)
		if ids.is_empty():
			var none := UiKit.lbl("No player or club by that name.", UiKit.SMALL, UiKit.MUTED)
			none.name = "SearchNone"
			results.add_child(none)
	for id in ids:
		var row := _row(results, str(id), text)
		if row != null:
			results.add_child(row)


## One name: a tap opens it, a hold keeps it (or lets it go).
static func _row(results: VBoxContainer, id: String, text: String) -> Button:
	var d := describe(id)
	if d.is_empty():
		return null
	var b := UiKit.text_action("", UiKit.NAME)
	b.name = "Result_" + id.replace(":", "_")
	b.set_meta("id", id)
	b.set_meta(WordPress.OWN_HOLD, true)
	b.custom_minimum_size = Vector2(0, ROW_H)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	# One line each (lbl wraps by default, and a wrapping label in a row
	# shrinks to nothing): the name gives way first, trimmed.
	var h := UiKit.hbox(8)
	h.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(h)
	var nm := UiKit.lbl(str(d[0]), UiKit.NAME, UiKit.club_ink(str(d[2])) if str(d[2]) != "" else UiKit.TEXT, true)
	nm.name = "Name"
	nm.mouse_filter = Control.MOUSE_FILTER_IGNORE
	nm.autowrap_mode = TextServer.AUTOWRAP_OFF
	nm.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	nm.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	nm.clip_text = true
	h.add_child(nm)
	var sub := UiKit.lbl(str(d[1]), UiKit.SMALL, UiKit.MUTED)
	sub.name = "Line"
	sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sub.autowrap_mode = TextServer.AUTOWRAP_OFF
	sub.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(sub)
	var kept := UiKit.lbl("Kept", UiKit.SMALL, UiKit.TEXT, true)
	kept.name = "Kept"
	kept.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kept.autowrap_mode = TextServer.AUTOWRAP_OFF
	kept.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	kept.visible = GameState.shortlist.has(id) and text.strip_edges().length() >= MIN_LETTERS
	h.add_child(kept)
	var hold := {"serial": 0, "held": false, "at": Vector2.ZERO}
	b.button_down.connect(func() -> void:
		hold["serial"] = int(hold["serial"]) + 1
		hold["held"] = false
		hold["at"] = b.get_global_mouse_position()
		var token: int = hold["serial"]
		b.get_tree().create_timer(WordPress.HOLD_SECONDS).timeout.connect(func() -> void:
			if not is_instance_valid(b) or int(hold["serial"]) != token or not b.button_pressed and not b.is_pressed():
				return
			if b.get_global_mouse_position().distance_to(hold["at"]) > WordPress.SLOP:
				return
			hold["held"] = true
			var on := GameState.toggle_shortlist(id)
			kept.visible = on
			if text.strip_edges().length() < MIN_LETTERS and not on:
				# Taken off the shortlist view: the row goes.
				_fill.call_deferred(results, text)))
	b.button_up.connect(func() -> void: hold["serial"] = int(hold["serial"]) + 1)
	b.pressed.connect(func() -> void:
		if bool(hold["held"]):
			hold["held"] = false
			return
		NameLink.open(b, id))
	return b
