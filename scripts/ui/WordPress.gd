class_name WordPress
extends Node
## The long press on a football word (row T3.R43, P-61). Router keeps one. A
## finger held still for HOLD_SECONDS on words opens FootballWords' sheet for
## the word under it (a plain label), or for the football words in that line
## (a button or a rich line). Words with no rule do nothing, and the press
## carries on as a normal tap. A control that has a long press of its own
## (Training's bulk pick, the shortlist) sets meta OWN_HOLD and is left alone.
## The finger's lift after a sheet opens is swallowed, so the button under it
## does not act as well.

const HOLD_SECONDS := 0.45
## A finger that moves this far is a scroll, not a hold.
const SLOP := 12.0
const OWN_HOLD := "own_long_press"

var _down := false
var _at := Vector2.ZERO
var _serial := 0
var _swallow := false


func _input(event: InputEvent) -> void:
	var press := event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT
	if press:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			_down = true
			_at = mb.position
			_serial += 1
			_wait(_serial)
		else:
			_down = false
			_serial += 1
			if _swallow:
				_swallow = false
				get_viewport().set_input_as_handled()
				_release_buttons()
	elif event is InputEventMouseMotion and _down:
		if (event as InputEventMouseMotion).position.distance_to(_at) > SLOP:
			_down = false
			_serial += 1


func _wait(token: int) -> void:
	await get_tree().create_timer(HOLD_SECONDS).timeout
	if token != _serial or not _down:
		return
	var scene := get_tree().current_scene
	if scene == null:
		return
	var words := words_at(scene, _at)
	if words.is_empty():
		return
	if FootballWords.open(scene, words) != null:
		_swallow = true


## The football words under screen point `at` in `scene`: the topmost visible
## control with words there (an open sheet before the screen under it).
static func words_at(scene: Node, at: Vector2) -> Array:
	var hit := _control_at(scene, at)
	if hit == null:
		return []
	var n: Node = hit
	while n != null:
		if n.has_meta(OWN_HOLD):
			return []
		n = n.get_parent()
	if hit is Label:
		var l := hit as Label
		var local := l.get_global_transform().affine_inverse() * at
		for i in l.text.length():
			if l.get_character_bounds(i).has_point(local):
				var w := FootballWords.word_at(l.text, i)
				if w != "":
					return [w]
				break
		return FootballWords.find_in(l.text)
	if hit is RichTextLabel:
		return FootballWords.find_in((hit as RichTextLabel).get_parsed_text())
	if hit is Button:
		return FootballWords.find_in((hit as Button).text)
	return []


## The last-drawn visible control with words whose rect holds `at`, and that
## no clipping parent hides there.
static func _control_at(scene: Node, at: Vector2) -> Control:
	var best: Control = null
	for n in scene.find_children("*", "Control", true, false):
		var c := n as Control
		if not (c is Label or c is RichTextLabel or c is Button):
			continue
		if not c.is_visible_in_tree() or not c.get_global_rect().has_point(at):
			continue
		var clipped := false
		var p := c.get_parent()
		while p != null:
			if p is Control and ((p as Control).clip_contents or p is ScrollContainer) and not (p as Control).get_global_rect().has_point(at):
				clipped = true
				break
			p = p.get_parent()
		if not clipped:
			best = c
	return best


## A button the finger went down on stays drawn pressed when its lift is
## swallowed: let go of it.
func _release_buttons() -> void:
	var vp := get_viewport()
	if vp != null:
		vp.gui_release_focus()
		var held := vp.gui_get_focus_owner()
		if held is BaseButton:
			(held as BaseButton).button_pressed = false
