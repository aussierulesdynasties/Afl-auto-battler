class_name SkipTap
extends Node
## The skip rule's tap (director, 2026-11-25: "a tap anywhere else jumps to the
## final frame"; 2026-11-26: the full-time sheet and the awards night's winner).
## A tap is a press and a release inside `area` that land on no button and move
## no scroll: a finger dragging the sheet up is scrolling it, not tapping it,
## and a button keeps its own job. Something over the area on a higher layer
## (a farewell fading out over full time) has the touch, not the area. It goes
## with `area`.

var area: Control
var on_tap: Callable
var _down := false
## Each scroll's place at the press, to tell a tap from a drag.
var _at := {}


## Listen for a tap on `area` until it goes; `on_tap` runs on each one.
static func arm(on: Control, then: Callable) -> SkipTap:
	var n := SkipTap.new()
	n.name = "SkipTap"
	n.area = on
	n.on_tap = then
	on.add_child(n)
	return n


func _input(e: InputEvent) -> void:
	var mb := e as InputEventMouseButton
	if mb == null or mb.button_index != MOUSE_BUTTON_LEFT:
		return
	if not is_instance_valid(area) or not area.is_visible_in_tree():
		_down = false
		return
	if mb.pressed:
		_down = _here(mb.position)
		if _down:
			_at = _scrolls()
		return
	if not _down:
		return
	_down = false
	if _here(mb.position) and _scrolls() == _at:
		on_tap.call()


## Inside the area, on none of its buttons and under nothing on a higher layer.
func _here(p: Vector2) -> bool:
	if not area.get_global_rect().has_point(p):
		return false
	for b in area.find_children("*", "BaseButton", true, false):
		if (b as Control).is_visible_in_tree() and (b as Control).get_global_rect().has_point(p):
			return false
	return not _covered(p)


func _covered(p: Vector2) -> bool:
	var mine := 0
	var up: Node = area
	while up != null:
		if up is CanvasLayer:
			mine = (up as CanvasLayer).layer
			break
		up = up.get_parent()
	for n in area.get_tree().root.find_children("*", "CanvasLayer", true, false):
		var cl := n as CanvasLayer
		if not cl.visible or cl.layer <= mine:
			continue
		for k in cl.get_children():
			var c := k as Control
			if c != null and c.is_visible_in_tree() and c.mouse_filter != Control.MOUSE_FILTER_IGNORE \
					and c.get_global_rect().has_point(p):
				return true
	return false


func _scrolls() -> Dictionary:
	var out := {}
	for s in area.find_children("*", "ScrollContainer", true, false):
		out[s.get_instance_id()] = Vector2i((s as ScrollContainer).scroll_horizontal, (s as ScrollContainer).scroll_vertical)
	return out
