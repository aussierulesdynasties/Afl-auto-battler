extends RefCounted
## A finger's tap, for UI tests. emit_signal("pressed") proves the handler
## works; it can't show that a player's tap reaches the button. This one goes
## the way a phone's touch goes: a touch at the button's place on screen,
## turned into a mouse click by the engine (Project Settings > pointing), and
## routed through the window and GUI. Anything drawn over the button - a sheet,
## an overlay, the edge of a scroll - takes the tap instead, and the tap fails.
##
##   const Tap := preload("res://tests/tap.gd")
##   var why: String = await Tap.tap(button)   # "" when the button got it

## Frames to let the touch through: the engine passes it on at the next one.
const SETTLE_FRAMES := 2


## Tap c at its centre. Returns "" when c was pressed, else what went wrong.
static func tap(c: Control) -> String:
	if c == null or not is_instance_valid(c):
		return "no control"
	return await tap_at(c, c.size * 0.5, false)


## Tap c at `local`, a point in c's own pixels (a spot along a slider).
## For a control that isn't a button, "" means the touch reached c itself
## (it was the control under the finger); tap() leaves that unchecked.
static func tap_at(c: Control, local: Vector2, must_reach := true) -> String:
	if c == null or not is_instance_valid(c):
		return "no control"
	# The tap can close the screen the button is on; keep hold of the tree.
	var tree := c.get_tree()
	if not c.is_visible_in_tree():
		return "%s is hidden" % c.name
	# A player scrolls to a button below the fold before tapping it.
	var p := c.get_parent()
	while p != null:
		if p is ScrollContainer:
			(p as ScrollContainer).ensure_control_visible(c)
			await tree.process_frame
			break
		p = p.get_parent()
	var at := c.get_screen_transform() * local
	var win := c.get_window()
	if not Rect2(Vector2.ZERO, Vector2(win.size)).has_point(at):
		return "%s is off the screen at %s" % [c.name, str(at)]
	var hit := [false]
	var on_press := func(): hit[0] = true
	var watch := c is BaseButton
	if watch:
		(c as BaseButton).pressed.connect(on_press)
	var reached := [false]
	var on_input := func(e: InputEvent):
		if e is InputEventMouseButton and (e as InputEventMouseButton).pressed:
			reached[0] = true
	var strict := must_reach and not watch
	if strict:
		c.gui_input.connect(on_input)
	for down in [true, false]:
		var touch := InputEventScreenTouch.new()
		touch.index = 0
		touch.position = at
		touch.pressed = down
		Input.parse_input_event(touch)
		Input.flush_buffered_events()
		for i in SETTLE_FRAMES:
			await tree.process_frame
	if watch and is_instance_valid(c):
		(c as BaseButton).pressed.disconnect(on_press)
	if not watch and not strict:
		return ""
	if strict:
		if is_instance_valid(c):
			c.gui_input.disconnect(on_input)
		if reached[0]:
			return ""
		var under := win.gui_get_hovered_control()
		return "the tap on %s went to %s" % [c.name, under.name if under != null else "nothing"]
	if hit[0]:
		return ""
	var top := win.gui_get_hovered_control()
	return "the tap on %s went to %s" % [c.name, top.name if top != null else "nothing"]


## Wait until c has stopped moving: its place on screen the same for
## `still` frames running (at most `limit` frames). A player taps a screen
## that has settled; a card arriving late (a week's event) moves what is
## under it, and a tap computed before that lands on whatever moved in.
static func steady(c: Control, still := 10, limit := 600) -> void:
	if c == null or not is_instance_valid(c):
		return
	var tree := c.get_tree()
	var last := Rect2()
	var same := 0
	for i in range(limit):
		await tree.process_frame
		if not is_instance_valid(c):
			return
		var r := c.get_global_rect()
		same = same + 1 if r == last else 0
		last = r
		if same >= still:
			return


## Where c's centre is on the screen (window pixels, after stretching).
static func screen_point(c: Control) -> Vector2:
	return c.get_screen_transform() * (c.size * 0.5)


## Hold a finger still on c at `local` (its own pixels) for `seconds`, then
## lift it: a long press the way a phone sends one. Returns "" when the touch
## was on screen, else what went wrong. Whether c also acted is the caller's
## to check (a long press that opened a sheet must not tap the button too).
static func hold_at(c: Control, local: Vector2, seconds: float) -> String:
	if c == null or not is_instance_valid(c):
		return "no control"
	var tree := c.get_tree()
	if not c.is_visible_in_tree():
		return "%s is hidden" % c.name
	var at := c.get_screen_transform() * local
	var win := c.get_window()
	if not Rect2(Vector2.ZERO, Vector2(win.size)).has_point(at):
		return "%s is off the screen at %s" % [c.name, str(at)]
	for down in [true, false]:
		var touch := InputEventScreenTouch.new()
		touch.index = 0
		touch.position = at
		touch.pressed = down
		Input.parse_input_event(touch)
		Input.flush_buffered_events()
		if down:
			await tree.create_timer(seconds).timeout
		for i in SETTLE_FRAMES:
			await tree.process_frame
	return ""
