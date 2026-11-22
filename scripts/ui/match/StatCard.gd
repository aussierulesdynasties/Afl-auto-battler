class_name StatCard
extends VBoxContainer
## A player's stat card on the 3D picture, as a TV graphic (row 207): it sits on the
## bottom of the ground for a few seconds and hides the strip behind it (rule 2.94).
## It shows his name and club, then three numbers on one line (rule 2.95): his
## disposals with their disposal efficiency first ("18 disposals at 89%"), then the
## two highest of his role's numbers. It comes up for the man who kicked each goal,
## either side's, as the TV coverage names a goal kicker. It takes no tap.

const SHOW_S := 5.0        # real seconds a card stays up, at any match speed
const FADE_IN := 0.2
const FADE_OUT := 0.35
const NAME_FS := 16
const NUM_FS := 18
const WORD_FS := 13
const DARK := Color(0.07, 0.08, 0.09, 0.9)

## Each role's numbers after disposals (rule 2.95), in the order a tie is settled.
## A forward shows the bigger of his marks and tackles ("Whichever is more").
const ROLE_SETS := {
	"FWD": ["goals", "score_involvements", "marks|tackles"],
	"MID": ["clearances", "contested_possessions", "tackles", "inside50"],
	"DEF": ["intercepts", "rebounds", "marks", "contested_marks", "tackles", "spoils"],
	"RUCK": ["hitouts", "clearances", "contested_possessions", "marks"],
}
## What fills a card whose role numbers are still nought, in this order.
const FILL := ["goals", "marks", "tackles", "score_involvements", "contested_possessions", "inside50"]
const WORDS := {
	"goals": ["goal", "goals"], "score_involvements": ["score involvement", "score involvements"],
	"marks": ["mark", "marks"], "tackles": ["tackle", "tackles"],
	"clearances": ["clearance", "clearances"],
	"contested_possessions": ["contested possession", "contested possessions"],
	"inside50": ["inside 50", "inside 50s"], "intercepts": ["intercept", "intercepts"],
	"rebounds": ["rebound 50", "rebound 50s"], "contested_marks": ["contested mark", "contested marks"],
	"spoils": ["spoil", "spoils"], "hitouts": ["hitout", "hitouts"],
}

var _tween: Tween


## The card's three numbers as [count, words] pairs: disposals at their efficiency,
## then the role's two highest (a role outside the four counts as a midfielder's).
## A nought is never shown: FILL stands in for it, so a card can have fewer than three.
static func numbers(card: Dictionary) -> Array:
	var d := int(card.get("disposals", 0))
	var first := "disposal" if d == 1 else "disposals"
	if d > 0:
		first += " at %d%%" % int(round(100.0 * float(card.get("effective_disposals", 0)) / float(d)))
	var out := [[d, first]]
	var role := str(card.get("role", "MID"))
	var pool := []
	for key: String in ROLE_SETS.get(role, ROLE_SETS["MID"]):
		var k := key
		if key.contains("|"):
			var a := key.split("|")
			k = a[0] if int(card.get(a[0], 0)) >= int(card.get(a[1], 0)) else a[1]
		pool.append([int(card.get(k, 0)), k, pool.size()])
	# Highest first; a tie keeps the set's order.
	pool.sort_custom(func(x: Array, y: Array) -> bool:
		return x[0] > y[0] or (x[0] == y[0] and x[2] < y[2]))
	var used := []
	for p: Array in pool:
		if used.size() < 2 and int(p[0]) > 0:
			used.append(str(p[1]))
	# A card never shows a nought ("0 clearances" says nothing): early in a game the
	# gap is filled from what he has done, his goals first (a goal's card always has one).
	for k: String in FILL:
		if used.size() < 2 and int(card.get(k, 0)) > 0 and not used.has(k):
			used.append(k)
	for k: String in used:
		var n := int(card.get(k, 0))
		out.append([n, str((WORDS[k] as Array)[0 if n == 1 else 1])])
	return out


## The card as one line of text, for the tests and the feed's record of it.
static func text_of(who: String, club: String, card: Dictionary) -> String:
	var parts := []
	for p: Array in numbers(card):
		parts.append("%d %s" % [p[0], p[1]])
	return "%s, %s: %s" % [who, club, "   ".join(parts)]


func setup(who: String, code: String, card: Dictionary) -> StatCard:
	name = "StatCard"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_theme_constant_override("separation", 0)
	# His name and club on his club's colour, as the score bug carries each club.
	var top := PanelContainer.new()
	top.name = "Who"
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var tsb := UiKit.style(ScoreBug._club_colour(code), 0, UiKit.RADIUS)
	tsb.set_border_width_all(0)
	tsb.corner_radius_bottom_left = 0
	tsb.corner_radius_bottom_right = 0
	tsb.content_margin_left = 6
	tsb.content_margin_right = 10
	tsb.content_margin_top = 3
	tsb.content_margin_bottom = 3
	top.add_theme_stylebox_override("panel", tsb)
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 6)
	top.add_child(row)
	var crest := UiKit.club_marker(code, 22.0)
	crest.mouse_filter = Control.MOUSE_FILTER_IGNORE
	crest.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(crest)
	var name_l := UiKit.line(who, NAME_FS, Color.WHITE, true)
	name_l.name = "Name"
	ClubDuel.on_colour(name_l)
	UiKit.set_font_size(name_l, NAME_FS, "font_size", true)
	row.add_child(name_l)
	var club_l := UiKit.line(GameDB.club_short(code), WORD_FS, Color.WHITE)
	club_l.name = "Club"
	ClubDuel.on_colour(club_l)
	club_l.modulate.a = 0.85
	UiKit.set_font_size(club_l, WORD_FS, "font_size", true)
	club_l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(club_l)
	add_child(top)
	# The three numbers on one line, on a dark strip: the count in the scoreboard
	# face, its words beside it.
	var bottom := PanelContainer.new()
	bottom.name = "Numbers"
	bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bsb := UiKit.style(DARK, 0, UiKit.RADIUS)
	bsb.set_border_width_all(0)
	bsb.corner_radius_top_left = 0
	bsb.corner_radius_top_right = 0
	bsb.content_margin_left = 8
	bsb.content_margin_right = 10
	bsb.content_margin_top = 2
	bsb.content_margin_bottom = 3
	bottom.add_theme_stylebox_override("panel", bsb)
	var nums := HBoxContainer.new()
	nums.name = "Line"
	nums.mouse_filter = Control.MOUSE_FILTER_IGNORE
	nums.add_theme_constant_override("separation", 12)
	bottom.add_child(nums)
	for p: Array in numbers(card):
		var one := HBoxContainer.new()
		one.mouse_filter = Control.MOUSE_FILTER_IGNORE
		one.add_theme_constant_override("separation", 4)
		var n := UiKit.figure(str(p[0]), NUM_FS, Color.WHITE)
		UiKit.set_font_size(n, NUM_FS, "font_size", true)
		n.mouse_filter = Control.MOUSE_FILTER_IGNORE
		one.add_child(n)
		var w := UiKit.line(str(p[1]), WORD_FS, Color.WHITE)
		UiKit.set_font_size(w, WORD_FS, "font_size", true)
		w.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		w.mouse_filter = Control.MOUSE_FILTER_IGNORE
		one.add_child(w)
		nums.add_child(one)
	add_child(bottom)
	return self


## Up for SHOW_S real seconds, easing in and out; then it frees itself.
func run() -> void:
	if not UiKit.motion_on():
		modulate.a = 1.0
		get_tree().create_timer(SHOW_S).timeout.connect(queue_free)
		return
	modulate.a = 0.0
	_tween = create_tween()
	_tween.tween_property(self, "modulate:a", 1.0, FADE_IN)
	_tween.tween_interval(SHOW_S - FADE_IN - FADE_OUT)
	_tween.tween_property(self, "modulate:a", 0.0, FADE_OUT)
	_tween.tween_callback(queue_free)
