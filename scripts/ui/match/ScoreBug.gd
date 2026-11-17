class_name ScoreBug
extends HBoxContainer
## The score on the 3D picture, as a TV score bug (rule 2.107, director 2026-11-17:
## "we can put an on screen scoreboard like in ss2"): each club's guernsey and its
## points on its own colour, the quarter and the minute between them. It sits at
## the foot of the picture, in the middle, and takes no tap.

# Sized as on the board he chose (rule 2.107, option C): beside the Bench tab, 1.6 times
# its width and a little lower than its pill. Fixed, like the tab, not by the text size.
const H := 28.0          # the bug's height
const CELL_W := 57.0     # each club's cell
const MID_W := 36.0      # the clock between them
const SCORE_FS := 22
const CLOCK_FS := 11
const MID_COLOUR := Color(0.204, 0.227, 0.259, 0.92)

var _home_score: Label
var _away_score: Label
var _top: Label
var _bottom: Label


func setup(home: String, away: String) -> ScoreBug:
	name = "ScoreBug"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_theme_constant_override("separation", 0)
	var h := H
	add_child(_cell(home, true, h))
	var mid := PanelContainer.new()
	mid.name = "Clock"
	mid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var msb := UiKit.style(MID_COLOUR, 0, 0)
	msb.set_border_width_all(0)
	mid.add_theme_stylebox_override("panel", msb)
	mid.custom_minimum_size = Vector2(MID_W, h)
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", -2)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	mid.add_child(v)
	_top = UiKit.line("", UiKit.SECONDARY, Color.WHITE, true)
	_bottom = UiKit.line("", UiKit.SECONDARY, Color.WHITE, true)
	for l: Label in [_top, _bottom]:
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		l.add_theme_font_size_override("font_size", CLOCK_FS)
		v.add_child(l)
	add_child(mid)
	add_child(_cell(away, false, h))
	return self


func _cell(code: String, home: bool, h: float) -> Control:
	var p := PanelContainer.new()
	p.name = "Home" if home else "Away"
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var r := UiKit.RADIUS
	var sb := UiKit.style(_club_colour(code), 0, r)
	sb.set_border_width_all(0)
	sb.content_margin_left = 3
	sb.content_margin_right = 3
	# Rounded on the outside only: the clock sits flush between the two cells.
	if home:
		sb.corner_radius_top_right = 0
		sb.corner_radius_bottom_right = 0
	else:
		sb.corner_radius_top_left = 0
		sb.corner_radius_bottom_left = 0
	p.add_theme_stylebox_override("panel", sb)
	p.custom_minimum_size = Vector2(CELL_W, h)
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 2)
	p.add_child(row)
	var crest := UiKit.club_marker(code, h - 4.0)
	crest.mouse_filter = Control.MOUSE_FILTER_IGNORE
	crest.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var score := UiKit.figure("0", UiKit.RATING, Color.WHITE)
	ClubDuel.on_colour(score)
	score.add_theme_font_size_override("font_size", SCORE_FS)
	score.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	score.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	score.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	score.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if home:
		row.add_child(crest)
		row.add_child(score)
		_home_score = score
	else:
		row.add_child(score)
		row.add_child(crest)
		_away_score = score
	return p


## The club's own first colour, the one its band leads with on the old scoreboard.
static func _club_colour(code: String) -> Color:
	var cols: Array = GameDB.club_colours(code)
	var c: Color = cols[0]
	c.a = 0.92
	return c


## Points only, as a TV bug shows them; the clock in two lines ("Q1" over "7'"),
## or a stoppage's name split over the two ("Half" over "time").
func show_score(home_pts: int, away_pts: int, clock: String) -> void:
	_home_score.text = str(home_pts)
	_away_score.text = str(away_pts)
	var at := clock.find(" ")
	if at < 0:
		at = clock.find("-")
		if at >= 0:
			_top.text = clock.substr(0, at)
			_bottom.text = clock.substr(at + 1)
			return
		_top.text = clock
		_bottom.text = ""
		return
	_top.text = clock.substr(0, at)
	_bottom.text = clock.substr(at + 1)
