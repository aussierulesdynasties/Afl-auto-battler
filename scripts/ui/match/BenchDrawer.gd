class_name BenchDrawer
extends Control
## The bench, out of the way until the coach wants it (director, 2026-11-12: "Bigger
## discs, bench drawer"). A small tab on the oval's bottom edge; a tap opens a panel
## of both benches (each player's jumper number on his club's disc, his name, and
## the tired or hurt mark with what it means), a tap anywhere else or Back shuts it.
##
## It lives inside the oval's view as its own layer, so the match screen needs no
## change. Shut, only the tab takes a finger: a long press on a disc still reaches
## the oval. Looks only: it reads the match's bench (MatchDirector.bench) and the
## marks the screen gave the oval, and changes nothing.

signal opened
signal closed

const TAB_SIZE := Vector2(92.0, 48.0)     # a thumb's target (48 px), the pill drawn inside it
const TAB_PILL_H := 34.0
const EDGE := 6.0
const ROW_H := 40.0
const HEAD_H := 30.0
const PAD := 10.0
const DISC_R := 13.0
const COLUMN_MAX := 230.0

var view: PitchView = null
var is_open := false
var _tab: Tab
var _shade: Shade
var _seen := ""
var _since := 0.0


## The tab: a button, drawn as a dark pill with the word and, when a player on
## the bench is hurt or tired, that mark (so it shows without a tap).
class Tab extends Button:
	var drawer: BenchDrawer

	func _draw() -> void:
		var pill := Rect2(0.0, size.y - BenchDrawer.TAB_PILL_H, size.x, BenchDrawer.TAB_PILL_H)
		var box := StyleBoxFlat.new()
		box.bg_color = Color(UiKit.BG, 0.92)
		box.border_color = Color(PitchView.RING_COLOUR, 0.55 if not drawer.is_open else 0.95)
		box.set_border_width_all(1)
		box.set_corner_radius_all(4)
		draw_style_box(box, pill)
		var fs := UiKit.px(UiKit.SECONDARY)
		var word := "Bench"
		var w := UiKit.BOLD.get_string_size(word, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var mark := drawer.worst_mark()
		var x := pill.position.x + (pill.size.x - w) * 0.5 - (9.0 if mark != "" else 0.0)
		var base := pill.position.y + pill.size.y * 0.5 + fs * 0.36
		draw_string(UiKit.BOLD, Vector2(x, base), word, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, PitchView.RING_COLOUR)
		if mark != "":
			# PlayerMarks.paint puts the badge on a disc's upper right: name the disc
			# whose badge lands beside the word.
			var r := 8.0
			var at := Vector2(x + w + 11.0, pill.position.y + pill.size.y * 0.5)
			PlayerMarks.paint(self, at - Vector2(r * 0.95, -r * 0.95), r, mark, true)


## Open, everything behind the panel: a tap on it shuts the drawer and goes no
## further, so shutting it never also pauses the match or presses a disc.
class Shade extends Control:
	var drawer: BenchDrawer

	func _gui_input(e: InputEvent) -> void:
		if e is InputEventMouseButton and (e as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
			accept_event()
			if (e as InputEventMouseButton).pressed and not drawer.panel_rect().has_point((e as InputEventMouseButton).position):
				drawer.close()

	func _draw() -> void:
		drawer._draw_panel(self)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_shade = Shade.new()
	_shade.name = "BenchShade"
	_shade.drawer = self
	_shade.mouse_filter = Control.MOUSE_FILTER_STOP
	_shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_shade.visible = false
	add_child(_shade)
	_tab = Tab.new()
	_tab.name = "BenchTab"
	_tab.drawer = self
	_tab.focus_mode = Control.FOCUS_NONE
	_tab.tooltip_text = ""
	for sb in ["normal", "hover", "pressed", "focus", "disabled"]:
		_tab.add_theme_stylebox_override(sb, StyleBoxEmpty.new())
	_tab.custom_minimum_size = TAB_SIZE
	_tab.size = TAB_SIZE
	_tab.pressed.connect(toggle)
	add_child(_tab)
	resized.connect(_place)
	_place()
	sync()


## Where the tab's pill is drawn on a view of `view_size`: the bottom-left corner,
## off the turf. One place for the drawer, the oval and the tests to read it.
static func pill_in(view_size: Vector2) -> Rect2:
	return Rect2(EDGE, view_size.y - EDGE - TAB_PILL_H, TAB_SIZE.x, TAB_PILL_H)


func _place() -> void:
	if _tab == null:
		return
	_tab.position = Vector2(EDGE, size.y - TAB_SIZE.y - EDGE)   # its pill: pill_in(size)
	_tab.size = TAB_SIZE
	_shade.queue_redraw()


func tab() -> Button:
	return _tab


func toggle() -> void:
	if is_open:
		close()
	else:
		open()


func open() -> void:
	if is_open or not has_bench():
		return
	is_open = true
	_shade.visible = true
	_shade.queue_redraw()
	_tab.queue_redraw()
	opened.emit()


## Shuts the drawer; true when it was open (so Back knows it was used up).
func close() -> bool:
	if not is_open:
		return false
	is_open = false
	_shade.visible = false
	_tab.queue_redraw()
	closed.emit()
	return true


func has_bench() -> bool:
	if view == null or view.director == null or view.director.bench.size() < 2:
		return false
	return not (view.director.bench[0] as Array).is_empty() or not (view.director.bench[1] as Array).is_empty()


## The bench changed, or a mark did: the tab shows only while the match says who
## is on the bench, and what is drawn follows.
func sync() -> void:
	if _tab == null:
		return
	var has := has_bench()
	_tab.visible = has
	if not has and is_open:
		close()
	var now := _signature()
	if now != _seen:
		_seen = now
		_tab.queue_redraw()
		_shade.queue_redraw()


func _process(delta: float) -> void:
	# An interchange changes the bench as the match plays: look a few times a second.
	_since += delta
	if _since >= 0.2:
		_since = 0.0
		sync()


func _signature() -> String:
	if not has_bench():
		return ""
	var parts := PackedStringArray()
	for row in rows():
		parts.append("%s:%s" % [str(row["num"]), str(row["mark"])])
	return ",".join(parts)


## Back (Escape on a PC, the phone's Back) shuts an open drawer first.
func _input(e: InputEvent) -> void:
	if is_open and is_visible_in_tree() and e.is_action_pressed("ui_cancel"):
		close()
		get_viewport().set_input_as_handled()


## "hurt" when a player on the bench is hurt, else "tired" when one is, else "".
func worst_mark() -> String:
	var worst := ""
	for row in rows():
		var m := str(row["mark"])
		if m == PlayerMarks.HURT:
			return m
		if m != "":
			worst = m
	return worst


## The panel on the view: over the tab, as wide as two columns need and the view allows.
func panel_rect() -> Rect2:
	var n := 0
	if has_bench():
		n = maxi((view.director.bench[0] as Array).size(), (view.director.bench[1] as Array).size())
	var w := minf(size.x - EDGE * 2.0, COLUMN_MAX * 2.0)
	var h := HEAD_H + float(n) * ROW_H + PAD * 1.5
	var y := maxf(EDGE, size.y - EDGE - TAB_SIZE.y - 4.0 - h)
	return Rect2(EDGE, y, w, h)


## What the panel shows, for drawing and for tests: [{side, num, pid, name, mark,
## words, rect, disc}], the home side's column on the left.
func rows() -> Array:
	var out := []
	if not has_bench():
		return out
	var pr := panel_rect()
	var col_w := pr.size.x * 0.5
	var fs := UiKit.px(UiKit.SECONDARY)
	var fine := UiKit.px(UiKit.FINE)
	for side in range(2):
		var list: Array = view.director.bench[side]
		for i in range(list.size()):
			var b: Dictionary = list[i]
			var pid := str(b.get("pid", ""))
			var rect := Rect2(pr.position.x + col_w * float(side), pr.position.y + HEAD_H + float(i) * ROW_H, col_w, ROW_H)
			var room := col_w - PAD - DISC_R * 2.0 - 12.0 - PAD * 0.5
			var state: Dictionary = view.marks.get(pid, {})
			var mark := str(state.get("mark", ""))
			var full := GameDB.player_display_name_by_id(pid, str(b.get("name", "")))
			out.append({"side": side, "num": int(b.get("num", 0)), "pid": pid,
					"name": _fit_name(full, room, fs), "mark": mark,
					"words": _fit_words(state, mark, room, fine) if mark != "" else "",
					"rect": rect, "disc": Vector2(rect.position.x + PAD + DISC_R, rect.position.y + ROW_H * 0.5)})
	return out


## His name as it fits: in full, then initial and surname, then the surname.
static func _fit_name(full: String, room: float, fs: int) -> String:
	var tries := [full]
	var bits := full.split(" ", false)
	if bits.size() >= 2:
		var surname := " ".join(bits.slice(1))
		tries.append("%s. %s" % [bits[0].left(1), surname])
		tries.append(surname)
	for t in tries:
		if UiKit.BOLD.get_string_size(str(t), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x <= room:
			return str(t)
	return str(tries[tries.size() - 1])


## What his mark means as it fits: the long press's words for a player on the
## bench ("hamstring strain, out for the day"), then the injury or "Tired" alone,
## then the one word.
static func _fit_words(state: Dictionary, mark: String, room: float, fs: int) -> String:
	var tries := [_cap(PlayerMarks.words(state, true)), _cap(str(state.get("words", ""))),
			"Hurt" if mark == PlayerMarks.HURT else "Tired"]
	for t in tries:
		if str(t) != "" and UiKit.FONT.get_string_size(str(t), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x <= room:
			return str(t)
	return str(tries[2])


static func _cap(s: String) -> String:
	return s.left(1).to_upper() + s.substr(1) if s != "" else s


func _draw_panel(ci: CanvasItem) -> void:
	if not is_open or not has_bench():
		return
	var pr := panel_rect()
	var box := StyleBoxFlat.new()
	box.bg_color = UiKit.BG      # solid: the discs behind must not show through the names
	box.border_color = UiKit.LINE
	box.set_border_width_all(1)
	box.set_corner_radius_all(4)
	ci.draw_style_box(box, pr)
	var col_w := pr.size.x * 0.5
	var fs := UiKit.px(UiKit.SECONDARY)
	var fine := UiKit.px(UiKit.FINE)
	var codes := [view.home_code, view.away_code]
	# Each side's column under its club's name in its own ink, a bar of its two
	# colours beneath: whose bench is whose reads before a name does.
	for side in range(2):
		var x := pr.position.x + col_w * float(side)
		var head := "%s bench" % GameDB.club_short(str(codes[side]))
		ci.draw_string(UiKit.BOLD, Vector2(x + PAD, pr.position.y + 20.0), head, HORIZONTAL_ALIGNMENT_LEFT,
				col_w - PAD * 1.5, fs, UiKit.club_ink(str(codes[side]), UiKit.BG))
		var cols: Array = GameDB.club_colours(str(codes[side]))
		var bar := Rect2(x + PAD, pr.position.y + HEAD_H - 4.0, col_w - PAD * 2.0, 3.0)
		if cols.size() >= 2:
			ci.draw_rect(Rect2(bar.position, Vector2(bar.size.x * 0.5, bar.size.y)), cols[0])
			ci.draw_rect(Rect2(bar.position + Vector2(bar.size.x * 0.5, 0.0), Vector2(bar.size.x * 0.5, bar.size.y)), cols[1])
		elif cols.size() == 1:
			ci.draw_rect(bar, cols[0])
	ci.draw_line(Vector2(pr.position.x + col_w, pr.position.y + PAD), Vector2(pr.position.x + col_w, pr.end.y - PAD), UiKit.LINE, 1.0)
	var kits: Array = view._kits
	for row in rows():
		var at: Vector2 = row["disc"]
		var kit: Dictionary = kits[int(row["side"])] if kits.size() == 2 else {}
		PitchView.paint_disc(ci, at, DISC_R, kit, str(row["num"]), int(clampf(DISC_R * 1.1, 9.0, 16.0)), true)
		var mark := str(row["mark"])
		var tx := at.x + DISC_R + 12.0
		if mark != "":
			PlayerMarks.paint(ci, at, DISC_R, mark, true)
			ci.draw_string(UiKit.BOLD, Vector2(tx, at.y - 2.0), str(row["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, fs, UiKit.TEXT)
			ci.draw_string(UiKit.FONT, Vector2(tx, at.y + float(fine) + 1.0), str(row["words"]), HORIZONTAL_ALIGNMENT_LEFT, -1, fine,
					UiKit.BAD if mark == PlayerMarks.HURT else UiKit.MUTED)
		else:
			ci.draw_string(UiKit.BOLD, Vector2(tx, at.y + float(fs) * 0.36), str(row["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, fs, UiKit.TEXT)
