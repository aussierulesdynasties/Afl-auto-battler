class_name StatGuide
extends RefCounted
## The in-game stat guide: one short line per rated stat (what it is and what
## it changes in a match), grouped, plus a few lines on how ratings fit
## together. Kept short on purpose (director, 2026-10-14: "condense it, keep
## only the essential info"). Detail that changes with the engine lives in
## the screens that show it, not here.

## key -> [one line]
## The 18 attributes in card order, each from what it drives in the match
## (docs/RATING_REBUILD.md §2).
const STATS := {
	"speed": ["Pace. Breaks the lines in open play, gets clear of his man and runs down the ball carrier."],
	"endurance": ["Running power. He tires more slowly, so he stays at his best deeper into the game."],
	"strength": ["Body strength. Breaks tackles and holds his ground in one-on-one and ruck contests."],
	"work_rate": ["Runs both ways. Spreads from the contest to link up, then works back to keep the pressure on."],
	"kicking": ["Kicks the ball long and to a team-mate. Good kicks move it forward and find targets inside 50."],
	"handballing": ["Gets the handball away cleanly, most of all in a tackle. Fewer holding-the-ball frees."],
	"marking": ["Clean hands. Marks on the lead and on the switch, so team-mates can kick to him and we keep it."],
	"contested_marking": ["Wins the ball in the air in a pack or one-on-one, most of all inside 50. Key forwards live on it."],
	"one_on_one": ["Beats his man in the air. Spoils, and stops forwards marking in packs and on the lead."],
	"contested_ball": ["Wins the clearance and holds the ball in a tackle or the wet. Our inside mids win or lose the stoppages."],
	"goalkicking": ["Kicks straight. Turns his shots into goals instead of behinds."],
	"ruck": ["Wins the hit-outs at the bounce and stoppages. Our first ruck matters."],
	"vision": ["Finds the team-mate in the better spot. Hits targets going inside 50 and sets up shots."],
	"reading_play": ["Reads the play. Cuts off their kicks, roams off his man to intercept and starts our attack from half-back."],
	"pressure": ["Tackles and hurries the opposition. Most of our defence comes from it."],
	"forward_craft": ["Finds space inside 50. Leads, crumbs and gets to the right spot, so he is the one who gets the shot."],
	"discipline": ["Fewer clangers, free kicks against, 50s and reports. Higher is cleaner."],
	"durability": ["Stays on the park. Durable players get hurt less often."],
}

## [heading, [stat keys]] in the order they read.
const GROUPS := Attributes.GROUPS

const TOPICS := [
	["Overall (OVR)", "A player's rating, mostly from the stats his position relies on. Clubs value players by it at the draft and the trade table."],
	["Potential (POT)", "Where we expect him to peak. It is not a limit. His growth slows as he nears it."],
	["Team strengths", "Contest is our stoppage work. Attack is our forwards and our midfielders' running. Defence is our defenders' pressure and how they read the play."],
	["Traits and synergies", "A standout stat earns a trait. The right mix of them on the ground switches on a synergy. The Team screen shows ours, and when one is a player short (\"Lockdown unit: 1 lockdown player short\")."],
	["Injuries and legs", "Every player risks injury each game. Durability lowers the risk. Tired players win less ball. Rotate them from the coach's box."],
	["Development and training", "Players earn development every game. What each one is developing as decides where it goes. A stat costs more the higher it already is. Past POT it costs much more."],
	["Contracts", "After the Grand Final, re-sign or release players, sign free agents and trade."],
]


static func short(key: String) -> String:
	return str((STATS.get(key, [""]) as Array)[0])


static func _label_for(key: String) -> String:
	return Attributes.label(key)


## One line under each topic tile so a coach knows what's behind it.
const TEASERS := {
	"Overall (OVR)": "How a player is rated",
	"Potential (POT)": "Where he could peak",
	"Team strengths": "Contest, attack, defence",
	"Traits and synergies": "Standouts and the right mix",
	"Injuries and legs": "Durability and rotation",
	"Development and training": "How players improve",
	"Contracts": "Re-sign, release, trade",
}


## Every tile in the order it reads: [id, title, teaser]. The stat groups come
## first, then the topics. A tile's id names its button (Tile_<id>) and page.
static func tiles() -> Array:
	var out: Array = []
	for i in GROUPS.size():
		var g: Array = GROUPS[i]
		var names: Array = []
		for key in g[1]:
			names.append(_label_for(str(key)))
		out.append(["group%d" % i, str(g[0]), ", ".join(names)])
	for i in TOPICS.size():
		var t: Array = TOPICS[i]
		out.append(["topic%d" % i, str(t[0]), str(TEASERS.get(str(t[0]), ""))])
	return out


## Open the guide as a modal over `parent`: a grid of topic tiles, each
## opening a short page. Returns the overlay so the scene can close it from
## the back button; call `back(overlay)` first so Back steps a page to the grid.
static func show(parent: Control) -> Control:
	var vw := UiKit.view_width(parent)
	var landscape := not ScreenLayout.is_phone() and vw > UiKit.view_height(parent) * 1.2
	var cols_n := 3 if (landscape and vw >= 640.0) else 2
	var box := UiKit.modal_box(parent, 900.0 if cols_n == 3 else 720.0, 0.0)
	var overlay: Control = box["overlay"]
	overlay.name = "StatGuide"
	overlay.set_meta("cols", cols_n)
	UiKit.close_on_outside_tap(box)
	var v: VBoxContainer = box["body"]
	v.add_theme_constant_override("separation", UiKit.Space.ROOM)
	overlay.set_meta("body", v)
	var ok := UiKit.btn("Got it", UiKit.NAME, true)
	ok.name = "CloseStatGuide"
	ok.custom_minimum_size = Vector2(0, 44)
	ok.pressed.connect(func(): overlay.queue_free())
	box["footer"].add_child(ok)
	_show_grid(overlay)
	return overlay


## Back on an open page returns to the tiles and reports true; on the tiles
## (or a closed guide) it reports false so the caller closes the guide.
static func back(overlay: Control) -> bool:
	if not is_instance_valid(overlay) or str(overlay.get_meta("page", "")) == "":
		return false
	_show_grid(overlay)
	return true


static func open_page(overlay: Control, id: String) -> void:
	var v: VBoxContainer = overlay.get_meta("body")
	_clear(v)
	overlay.set_meta("page", id)
	var row := UiKit.hbox(UiKit.Space.ROOM)
	var all := UiKit.btn("‹ All topics", UiKit.NAME)
	all.name = "GuideAllTopics"
	all.custom_minimum_size = Vector2(0, 44)
	all.pressed.connect(func(): _show_grid(overlay))
	row.add_child(all)
	v.add_child(row)
	var page := UiKit.vbox(UiKit.Space.ROOM)
	page.name = "GuidePage_" + id
	v.add_child(page)
	if id.begins_with("group"):
		var g: Array = GROUPS[int(id.trim_prefix("group"))]
		page.add_child(UiKit.heading(str(g[0]), UiKit.H1))
		for key in g[1]:
			var item := UiKit.vbox(UiKit.Space.SLIM)
			item.name = "Guide_" + str(key)
			item.add_child(UiKit.lbl(_label_for(str(key)), UiKit.NAME, _ink(), true))
			item.add_child(_para(short(str(key)), 14, UiKit.TEXT))
			page.add_child(item)
	else:
		var t: Array = TOPICS[int(id.trim_prefix("topic"))]
		page.add_child(UiKit.heading(str(t[0]), UiKit.H1))
		page.add_child(_para(str(t[1]), 14, UiKit.TEXT))


static func _show_grid(overlay: Control) -> void:
	var v: VBoxContainer = overlay.get_meta("body")
	_clear(v)
	overlay.set_meta("page", "")
	v.add_child(UiKit.heading("Stat guide", UiKit.H1))
	var grid := GridContainer.new()
	grid.name = "GuideGrid"
	grid.columns = int(overlay.get_meta("cols", 2))
	grid.add_theme_constant_override("h_separation", UiKit.GAP)
	grid.add_theme_constant_override("v_separation", UiKit.GAP)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for t in tiles():
		grid.add_child(_tile(overlay, str(t[0]), str(t[1]), str(t[2])))
	v.add_child(grid)


## A tile: the topic in bold over its teaser, with a club-colour bar on the
## left. The whole tile is the button.
static func _tile(overlay: Control, id: String, title: String, teaser: String) -> Button:
	var b := UiKit.btn("", UiKit.NAME)
	b.name = "Tile_" + id
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.custom_minimum_size = Vector2(0, 64)
	b.clip_contents = true
	var m := MarginContainer.new()
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for edge in ["left", "right", "top", "bottom"]:
		m.add_theme_constant_override("margin_" + edge, 8)
	var col := UiKit.vbox(UiKit.Space.SLIM)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	var head := UiKit.lbl(title, UiKit.NAME, _ink(), true)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.autowrap_mode = TextServer.AUTOWRAP_OFF
	head.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	col.add_child(head)
	var sub := UiKit.lbl(teaser, 12, UiKit.MUTED)
	sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sub.autowrap_mode = TextServer.AUTOWRAP_OFF
	sub.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	col.add_child(sub)
	m.add_child(col)
	b.add_child(m)
	b.pressed.connect(func(): open_page(overlay, id))
	return b


## Your club's colour sets the topic names apart; from the menu, before a
## career, plain emphasis.
static func _ink() -> Color:
	var code := str(GameState.my_club)
	if code == "":
		return UiKit.EMPH
	return UiKit.club_name_colour(UiKit.club_ink(code))


static func _clear(v: Node) -> void:
	for c in v.get_children():
		v.remove_child(c)
		c.queue_free()


static func _para(text: String, size: int, colour: Color) -> Label:
	var l := UiKit.lbl(text, size, colour)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l
