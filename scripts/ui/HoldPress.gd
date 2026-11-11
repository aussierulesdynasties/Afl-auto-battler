class_name HoldPress
extends Control
## A second job for a button, on a long press (director, 2026-11-12: the season
## skips "should be long presses of the SKIP button in the bottom right"). A tap
## does what the button always did. A finger (or mouse) held still on it fills
## the button from the left, and its words change to say what the hold does;
## once the fill reaches the right edge the hold acts. Lifting early, moving off
## the button or dragging further than SLOP stops the fill, and nothing happens.
## The lift after a hold has acted does not tap the button as well.
##
##   HoldPress.attach(button, "Skip home and away", _open_bulk_skip)
##
## The button's own pressed connections become the tap: attach takes them over.

## How long the hold takes. A tap is over long before.
const SECONDS := 0.5
## The fill shows only after this, so a quick tap never flashes it.
const CUE_AFTER := 0.12
## A finger that travels this far is a drag or a scroll, not a hold.
const SLOP := 12.0

var _button: Button
var _taps: Array = []
var _on_hold: Callable
var _hold_text := ""
var _text_was := ""
var _down := false
var _at := Vector2.ZERO
## Seconds held, counted by frames (the same clock as the engine's timers).
var _held := 0.0
var _fired := false
## How full the cue is, 0 to 1 (tests and captures read it).
var progress := 0.0


static func attach(b: Button, hold_text: String, on_hold: Callable) -> HoldPress:
	var h := HoldPress.new()
	h.name = "HoldCue"
	h._button = b
	h._on_hold = on_hold
	h._hold_text = hold_text
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for c in b.pressed.get_connections():
		h._taps.append(c["callable"])
		b.pressed.disconnect(c["callable"])
	b.add_child(h)
	# The football-words long press (WordPress) leaves this button alone.
	b.set_meta(WordPress.OWN_HOLD, true)
	b.gui_input.connect(h._on_input)
	b.pressed.connect(h._on_pressed)
	h.set_process(false)
	return h


## The hold's words while the finger is down.
func hold_text() -> String:
	return _hold_text


func holding() -> bool:
	return _down


func _on_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and (e as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var mb := e as InputEventMouseButton
		if mb.pressed:
			if _button.disabled:
				return
			_fired = false
			_down = true
			_at = mb.position
			_held = 0.0
			set_process(true)
		else:
			_stop()
	elif e is InputEventMouseMotion and _down:
		var p := (e as InputEventMouseMotion).position
		if p.distance_to(_at) > SLOP or not Rect2(Vector2.ZERO, _button.size).has_point(p):
			_stop()


func _process(delta: float) -> void:
	if not _down:
		return
	if not _button.is_visible_in_tree() or _button.disabled:
		_stop()
		return
	_held += delta
	var t := _held
	if t >= CUE_AFTER and _text_was == "" and _hold_text != "":
		_text_was = _button.text
		_button.text = _hold_text
		_fit_text()
	progress = clampf((t - CUE_AFTER) / (SECONDS - CUE_AFTER), 0.0, 1.0)
	queue_redraw()
	if t >= SECONDS:
		_fired = true
		_stop()
		_on_hold.call()


## The hold's words in full on a half-width phone button: a size or two
## smaller while held, never below FIT_MIN, rather than cut off.
const FIT_MIN := 12
var _size_was := 0


func _fit_text() -> void:
	var font: Font = _button.get_theme_font("font")
	var fs: int = _button.get_theme_font_size("font_size")
	_size_was = fs if _button.has_theme_font_size_override("font_size") else 0
	var sb := _button.get_theme_stylebox("normal")
	var room := _button.size.x - (sb.get_margin(SIDE_LEFT) + sb.get_margin(SIDE_RIGHT) if sb != null else 16.0) - 2.0
	var n := fs
	while n > FIT_MIN and font.get_string_size(_hold_text, HORIZONTAL_ALIGNMENT_LEFT, -1, n).x > room:
		n -= 1
	if n != fs:
		_button.add_theme_font_size_override("font_size", n)


func _stop() -> void:
	_down = false
	set_process(false)
	progress = 0.0
	if _text_was != "" and is_instance_valid(_button):
		_button.text = _text_was
		_button.remove_theme_font_size_override("font_size")
		if _size_was > 0:
			_button.add_theme_font_size_override("font_size", _size_was)
		_size_was = 0
	_text_was = ""
	queue_redraw()


## The button's release: a tap, unless the hold already acted.
func _on_pressed() -> void:
	if _fired:
		_fired = false
		return
	for cb in _taps:
		(cb as Callable).call()


func _draw() -> void:
	if progress <= 0.0:
		return
	var w := size.x * progress
	var fill := StyleBoxFlat.new()
	fill.bg_color = Color(1, 1, 1, 0.22)
	var sb := _button.get_theme_stylebox("normal")
	if sb is StyleBoxFlat:
		var f := sb as StyleBoxFlat
		fill.corner_radius_top_left = f.corner_radius_top_left
		fill.corner_radius_bottom_left = f.corner_radius_bottom_left
		fill.corner_radius_top_right = f.corner_radius_top_right if progress >= 1.0 else 0
		fill.corner_radius_bottom_right = f.corner_radius_bottom_right if progress >= 1.0 else 0
	draw_style_box(fill, Rect2(0, 0, w, size.y))
	# A solid edge along the bottom says how far there is to go.
	draw_rect(Rect2(0, size.y - 3.0, w, 3.0), Color(1, 1, 1, 0.9))
