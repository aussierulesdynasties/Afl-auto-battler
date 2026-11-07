class_name ClubLink
extends RefCounted
## One way for a club's name to open its page (C-PC-15, P-53; director
## 2026-10-18, rulings 5.11 no. 113: "every club has a page reached by tapping
## any club name"). The same pattern as NameLink for a player: tapping the name
## opens ClubPage over whatever screen you are on; Back, Close or a tap outside
## returns you to the screen exactly as it was.
##
## Entry points, all ending in `open`:
##  - a club named in a running line: `url(shown, code)` wraps it for a
##    RichTextLabel; NameLink.wire (which every name-linked line already has)
##    takes its tap, so a line can carry player and club names together;
##  - a club name that is a label of its own: `tappable(label, code)`;
##  - anything else: `open(from, code)`.
## Look-up only; no effect on the game.

const SCHEME := "club:"


## BBCode for `shown` as a tappable club name.
static func url(shown: String, code: String) -> String:
	return "[url=%s%s]%s[/url]" % [SCHEME, code, shown]


## A club's name as a link wears its strongest real colour (director
## 2026-11-06, rulings 51a: never white, never a tint): the same club-code ink
## as the Season stats lists, read at 4.5:1 on the page, a panel and a pressed
## row. Every club's name reads in a colour, Essendon's red and Collingwood's
## grey included, so a name in white is never a club.
static func colour(code: String) -> Color:
	return StatsSide.code_ink(code)


## BBCode for a club's name in its ink, bold, as a tap.
static func ink(code: String, shown := "") -> String:
	var name := shown if shown != "" else GameDB.club_name(code)
	return url("[b][color=#%s]%s[/color][/b]" % [colour(code).to_html(false), name.replace("[", "[lb]")], code)


## Make a label that names one club open its page on a tap. A press that turns
## into a swipe does nothing, so it still scrolls the page.
static func tappable(c: Control, code: String) -> Control:
	c.set_meta("name_link_wired", true)
	c.set_meta("club_code", code)
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
			open(c, code))
	return c


## The top Control under the window `from` is in: where the page is laid.
static func host_of(from: Node) -> Control:
	var host: Control = null
	var n: Node = from
	while n != null and not (n is Window):
		if n is Control:
			host = n
		n = n.get_parent()
	return host


## Open the club's page over the screen `from` is on. Null for a club the game
## does not know. A club page already open is replaced, not stacked.
static func open(from: Node, code: String) -> Control:
	if code == "" or not GameDB.clubs.has(code) or from == null or not from.is_inside_tree():
		return null
	var host := host_of(from)
	if host == null:
		return null
	for c in host.get_children():
		if c.name == ClubPage.SHEET_NAME and not c.is_queued_for_deletion():
			c.queue_free()
			c.name = "ClubPageClosing"
	var page := ClubPage.open(host, code)
	page.set_meta("club_link", true)
	return keep(host, page)


## A screen with its own stack of sheets (the stats hub) closes them on its own
## Back as well: hand it the sheet. Returns the sheet.
static func keep(host: Control, sheet: Control) -> Control:
	if sheet != null and host != null and host.has_method("open_sheet"):
		host.call("open_sheet", sheet)
	return sheet


## Back closes the newest sheet a name opened (a club page, the honour board, a
## player's profile, a trait) before the screen sees it. True when it did.
static func close_open(scene: Node) -> bool:
	return NameLink.close_open(scene)
