extends RefCounted
## Full-time motion (director, 2026-11-25): after the siren the result lands,
## then the ladder move arrives. The director chose the stakes-aware motion of
## the three he was shown (2026-11-25):
##   The verdict winds up (1.30 -> 1.36) and slams down (to 1.0, recoiling to
##   0.97); on the impact the sheet flashes the winner's colour (none on a loss
##   or a draw) and the score rows snap in under it.
##   A close win (under 12) or a finals win slams heavier (1.40 -> 1.48,
##   recoiling to 0.94) and shakes the sheet 3 px.
##   A big loss (40 or more) sinks into place, silent, and the rows fade up.
## The ladder move counts from where you were to where you are the first time
## it is in view, never before 0.9 s, and ends on a 1.08 pop and a pulse of the
## up or down colour. A final's outcome line stamps when you go through and
## settles when you're out.
##
## Presentation only: it moves what full time says, never a word of it, and
## every figure is true the moment it shows. Each tween is on the node it moves,
## so Continue (which frees the sheet) ends it at any frame, and nothing here
## takes a touch. Reduced motion (and a headless run) moves nothing: the sheet
## is all there at once and only the sting sounds. A loss gets no sting
## (director, 2026-11-25): there is no quieter sound to give it.


const CLOSE_WIN := 12          ## director, 2026-11-25: "close wins < 12 pts"
const BIG_LOSS := 40           ## the game's heavy loss (MediaConference, ClubLife)
const START := 0.20            ## the verdict's beat, once the sheet is up
const ROWS_GAP := 0.06         ## a big loss: the score rows, 0.06 s apart
const LADDER_AT := 0.9         ## the ladder move's beat, once it is in view
const SETTLE_FROM := 1.06      ## a final you lost
const DUR_SETTLE_FADE := 0.24
const DUR_SETTLE := 0.4
## The slam: [from, wound up to, recoil, recoil settle (s)].
const SLAM := [1.30, 1.36, 0.97, 0.22]
const SLAM_HEAVY := [1.40, 1.48, 0.94, 0.28]
const DUR_APPEAR := 0.06
const DUR_WIND := 0.10         ## the anticipation beat
const DUR_SLAM := 0.14
const DUR_RECOIL := 0.06
const DUR_SNAP := 0.12         ## a score row drops RISE px into place
const FLASH_PEAK := 0.30       ## the winner's colour over the sheet's wash
const DUR_FLASH_IN := 0.05
const DUR_FLASH_OUT := 0.40
const SHAKE := [3.0, -2.5, 2.0, -1.2, 0.6, 0.0]   ## px across, the sheet's micro-shake
const DUR_SHAKE := 0.22
## px above its place: the line above ("Full time - Round 3") ends 13 px over
## the verdict's letters, so the fall starts clear of it (5 px to spare).
const SINK_FROM := -8.0
const SINK_UNDER := 5.0        ## px under it at the bottom of the fall
const DUR_SINK := 0.34
const DUR_SINK_BACK := 0.40
const POP := 1.08              ## the ladder count's last beat
const DUR_POP := 0.08
const DUR_PULSE_HOLD := 0.16
const DUR_PULSE_BACK := 0.45


## Hide what is still to come the moment full time is built, so nothing sits on
## screen at rest and then pops. play() brings each one in.
static func prepare(f: Dictionary) -> void:
	if not UiKit.motion_on():
		return
	if bool(f.get("still", false)):
		var lad: Variant = f.get("ladder")
		if is_instance_valid(lad) and lad is Control:
			(lad as Control).modulate.a = 0.0
		return
	for c in _heroes(f):
		(c as Control).modulate.a = 0.0


## The sequence. `f` (MatchScene._ft_motion_facts): verdict, rows, ladder (only
## when it moved: from, to, say), finals (meta "through"), shell, scroll,
## result ("win", "loss", "draw", "neutral"), margin, final, flash.
static func play(f: Dictionary) -> void:
	var v: Variant = f.get("verdict")
	if not is_instance_valid(v) or not (v is Control) or not (v as Control).is_inside_tree():
		return
	if bool(f.get("still", false)):
		_still(f)
		return
	var result := str(f.get("result", ""))
	var sting := result != "loss"
	if not UiKit.motion_on():
		for c in _heroes(f):
			(c as Control).modulate.a = 1.0   # motion went off after prepare
		if sting:
			Feel.press("land")
		return
	var margin := int(f.get("margin", 0))
	if result == "loss" and margin >= BIG_LOSS:
		_sink(v, START)
		_reveal_rows(f.get("rows", []), START + DUR_SINK)
	else:
		var heavy := result == "win" and (margin < CLOSE_WIN or bool(f.get("final", false)))
		_slam(f, v, heavy, sting)
	var sc: ScrollContainer = f.get("scroll") as ScrollContainer
	var ladder: Variant = f.get("ladder")
	if is_instance_valid(ladder) and ladder is Label:
		_when_seen(ladder, sc, LADDER_AT, func() -> void: _ladder(ladder, f))
	var fin: Variant = f.get("finals")
	if is_instance_valid(fin) and fin is Label:
		_when_seen(fin, sc, LADDER_AT, func() -> void:
			if bool((fin as Label).get_meta("through", false)):
				UiKit.land(fin, 0.0, true, true)
			else:
				_settle(fin, 0.0, false))


## After the premiership ceremony (director, 2026-11-25: "open still"): the
## sheet is all there, with no slam, flash, shake or sting; only the ladder
## move still counts when it comes into view.
static func _still(f: Dictionary) -> void:
	Feel.moved.append("ft_still")
	var ladder: Variant = f.get("ladder")
	if not (is_instance_valid(ladder) and ladder is Label):
		return
	if not UiKit.motion_on():
		(ladder as Label).modulate.a = 1.0
		return
	_when_seen(ladder, f.get("scroll") as ScrollContainer, LADDER_AT, func() -> void: _ladder(ladder, f))


static func _heroes(f: Dictionary) -> Array:
	var out := []
	for k in ["verdict", "ladder", "finals"]:
		var c: Variant = f.get(k)
		if is_instance_valid(c) and c is Control:
			out.append(c)
	for r in f.get("rows", []):
		if is_instance_valid(r) and r is Control:
			out.append(r)
	return out


## A big loss's rows: each fades up, ROWS_GAP apart.
static func _reveal_rows(rows: Array, at: float) -> void:
	for i in range(rows.size()):
		if is_instance_valid(rows[i]) and rows[i] is Control:
			UiKit.reveal(rows[i], at + ROWS_GAP * i)


## A final you lost: up and in with no overshoot.
static func _settle(c: Control, delay: float, sting: bool) -> void:
	var tw := UiKit._own(c, "ft")
	if delay > 0.0:
		tw.tween_interval(delay)
	tw.tween_callback(func() -> void:
		Feel.moved.append("ft_settle")
		if sting:
			Feel.press("land")
		_aim(c)
		_put(c, "s", SETTLE_FROM))
	tw.tween_method(_setter(c, "s"), SETTLE_FROM, 1.0, DUR_SETTLE) \
			.set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE)
	tw.parallel().tween_property(c, "modulate:a", 1.0, DUR_SETTLE_FADE) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
	tw.tween_callback(func() -> void: _release(c))


## The verdict appears big, winds up a little bigger (the anticipation beat),
## slams down to its size, recoils under it and settles. The impact sounds,
## flashes and drops the score rows in.
static func _slam(f: Dictionary, v: Control, heavy: bool, sting: bool) -> void:
	var k: Array = SLAM_HEAVY if heavy else SLAM
	var tw := UiKit._own(v, "ft")
	tw.tween_interval(START)
	tw.tween_callback(func() -> void:
		Feel.moved.append("ft_slam_heavy" if heavy else "ft_slam")
		_aim(v)
		_put(v, "s", float(k[0])))
	tw.tween_method(_setter(v, "s"), float(k[0]), float(k[1]), DUR_WIND) \
			.set_trans(UiKit.Motion.TRANS_PULSE).set_ease(Tween.EASE_IN_OUT)
	tw.parallel().tween_property(v, "modulate:a", 1.0, DUR_APPEAR) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
	tw.tween_method(_setter(v, "s"), float(k[1]), 1.0, DUR_SLAM) \
			.set_trans(UiKit.Motion.TRANS_OUT).set_ease(UiKit.Motion.EASE_OUT)
	tw.tween_callback(func() -> void:
		if sting:
			Feel.press("land")
		_flash(f)
		if heavy:
			_shake(f)
		_snap_rows(f.get("rows", [])))
	tw.tween_method(_setter(v, "s"), 1.0, float(k[2]), DUR_RECOIL) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
	tw.tween_method(_setter(v, "s"), float(k[2]), 1.0, float(k[3])) \
			.set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE)
	tw.tween_callback(func() -> void: _release(v))


## A big loss: it comes up from above, falls heavily past its place and
## sinks back into it. No sound, no flash, no shake.
static func _sink(v: Control, delay: float) -> void:
	var tw := UiKit._own(v, "ft")
	tw.tween_interval(delay)
	tw.tween_callback(func() -> void:
		Feel.moved.append("ft_sink")
		_put(v, "dy", SINK_FROM))
	tw.tween_method(_setter(v, "dy"), SINK_FROM, SINK_UNDER, DUR_SINK) \
			.set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_OUT)
	tw.parallel().tween_property(v, "modulate:a", 1.0, DUR_SETTLE_FADE) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
	tw.tween_method(_setter(v, "dy"), SINK_UNDER, 0.0, DUR_SINK_BACK) \
			.set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE)
	tw.tween_callback(func() -> void: _release(v))


## On the slam's impact the score rows drop RISE px into place under the verdict, one after
## the other.
static func _snap_rows(rows: Array) -> void:
	for i in range(rows.size()):
		var r: Variant = rows[i]
		if not is_instance_valid(r) or not (r is Control):
			continue
		var tw := UiKit._own(r, "ft")
		if i > 0:
			tw.tween_interval(UiKit.Motion.STAGGER * i)
		tw.tween_callback(func() -> void:
			Feel.moved.append("ft_snap")
			_put(r, "dy", -UiKit.Motion.RISE))
		tw.tween_method(_setter(r, "dy"), -UiKit.Motion.RISE, 0.0, DUR_SNAP) \
				.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
		tw.parallel().tween_property(r, "modulate:a", 1.0, DUR_APPEAR) \
				.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
		tw.tween_callback(func() -> void: _release(r))


## On the impact the sheet's wash brightens in the winner's colour and fades. Drawn
## on the sheet itself, under the text: no node, nothing to take a touch.
static func _flash(f: Dictionary) -> void:
	var col: Color = f.get("flash", Color(0, 0, 0, 0))
	var shell: Variant = f.get("shell")
	if col.a <= 0.0 or not is_instance_valid(shell) or not (shell is Control):
		return
	var st := _flash_state(shell)
	st["col"] = Color(col, 1.0)
	Feel.moved.append("ft_flash")
	var tw := UiKit._own(shell, "ft_flash")
	tw.tween_method(_flash_setter(shell, st), 0.0, FLASH_PEAK, DUR_FLASH_IN) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
	tw.tween_method(_flash_setter(shell, st), FLASH_PEAK, 0.0, DUR_FLASH_OUT) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)


static func _flash_state(shell: Control) -> Dictionary:
	if shell.has_meta("_ft_flash"):
		return shell.get_meta("_ft_flash")
	var st := {"a": 0.0, "col": Color.WHITE}
	shell.set_meta("_ft_flash", st)
	# The same band as the wash modal_box draws: the top of the sheet, fading
	# out before the content needs the contrast.
	shell.draw.connect(func() -> void:
		var a := float(st["a"])
		if a <= 0.001:
			return
		var w := shell.size.x
		var h := minf(shell.size.y * 0.5, 220.0)
		var top := Color(st["col"] as Color, a)
		var none := Color(st["col"] as Color, 0.0)
		shell.draw_polygon(PackedVector2Array([Vector2(0, 0), Vector2(w, 0), Vector2(w, h), Vector2(0, h)]),
				PackedColorArray([top, top, none, none])))
	return st


static func _flash_setter(shell: Control, st: Dictionary) -> Callable:
	return func(a: float) -> void:
		st["a"] = a
		shell.queue_redraw()


## A close or finals win: the sheet shakes across, 3 px and dying away,
## on the impact. Screen shake Off (Settings) keeps it still.
static func _shake(f: Dictionary) -> void:
	var shell: Variant = f.get("shell")
	if not is_instance_valid(shell) or not (shell is Control) or not GameState.screen_shake_on():
		return
	var s := shell as Control
	if not s.has_meta("_ft_x0"):
		s.set_meta("_ft_x0", s.position.x)
	var x0 := float(s.get_meta("_ft_x0"))
	Feel.moved.append("ft_shake")
	var tw := UiKit._own(s, "ft_shake")
	var step := DUR_SHAKE / float(SHAKE.size())
	for dx in SHAKE:
		tw.tween_property(s, "position:x", x0 + float(dx), step) \
				.set_trans(UiKit.Motion.TRANS_PULSE).set_ease(Tween.EASE_IN_OUT)


## The ladder move: it comes up as it counts from where you were to where you
## are, ending on the true line with a small pop and a pulse of the up (GOOD)
## or down (BAD) colour.
static func _ladder(l: Label, f: Dictionary) -> void:
	var to := int(f.get("to", 0))
	var from := int(f.get("from", 0))
	var say: Callable = f.get("say")
	# The pop lands with the last number. The count eases out, so the true spot
	# shows about a third of the way into its 0.7 s (17th to 14th: at 0.25 s); a
	# pop timed to the count's end came half a second late.
	var st := {"counting": false, "popped": false}
	var shown := func(n: int) -> String:
		if n != to:
			st["counting"] = true
		elif bool(st["counting"]) and not bool(st["popped"]):
			st["popped"] = true
			_pop(l, to < from)
		return str(say.call(n))
	UiKit.count_up(l, to, shown, UiKit.Motion.DUR_COUNT, from)
	var tw := UiKit._own(l, "ft")
	tw.tween_property(l, "modulate:a", 1.0, UiKit.Motion.DUR_LAND_FADE) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)


## The ladder count's last number pops to 1.08 and pulses the up (GOOD)
## or down (BAD) colour, then settles back to its own.
static func _pop(l: Label, up: bool) -> void:
	if not is_instance_valid(l):
		return
	var base := l.get_theme_color("font_color")
	var hot := UiKit.margin_colour(up)
	Feel.moved.append("ft_pop")
	_aim(l)
	var tw := UiKit._own(l, "ft_pop")
	tw.tween_method(_setter(l, "s"), 1.0, POP, DUR_POP) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
	tw.parallel().tween_method(_ink(l), base, hot, DUR_POP) \
			.set_trans(UiKit.Motion.TRANS_IN).set_ease(UiKit.Motion.EASE_IN)
	tw.tween_method(_setter(l, "s"), POP, 1.0, UiKit.Motion.DUR_BASE) \
			.set_trans(UiKit.Motion.TRANS_SETTLE).set_ease(UiKit.Motion.EASE_SETTLE)
	tw.parallel().tween_method(_ink(l), hot, base, DUR_PULSE_BACK).set_delay(DUR_PULSE_HOLD) \
			.set_trans(UiKit.Motion.TRANS_PULSE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_callback(func() -> void:
		_release(l)
		l.add_theme_color_override("font_color", base))


static func _ink(l: Label) -> Callable:
	return func(c: Color) -> void: l.add_theme_color_override("font_color", c)


## Run `go` once `c` is in view in `sc` (its middle inside the scroll's visible
## rect), and never before `at` seconds: at `at` on a PC, where the line is
## already on screen; on a phone, when it scrolls up into view.
static func _when_seen(c: Control, sc: ScrollContainer, at: float, go: Callable) -> void:
	var st := {"ready": false, "fired": false}
	var check := func() -> void:
		if bool(st["fired"]) or not bool(st["ready"]) or not is_instance_valid(c) or not c.is_inside_tree():
			return
		if sc != null and is_instance_valid(sc) and not _in_view(c, sc):
			return
		st["fired"] = true
		go.call()
	if sc != null:
		_while_here(c, sc.get_v_scroll_bar().value_changed, func(_v: float) -> void: check.call())
		_while_here(c, sc.resized, check)
	var tw := UiKit._own(c, "ft_wait")
	tw.tween_interval(at)
	tw.tween_callback(func() -> void:
		st["ready"] = true
		check.call())


## Is the middle of `c` inside the scroll's window? Measured against the
## scroll's value, not the screen: a scroll moves its content a frame after the
## value changes, so the screen still shows where the line was.
static func _in_view(c: Control, sc: ScrollContainer) -> bool:
	var content: Control = null
	for k in sc.get_children():
		if k is Control and not (k is ScrollBar):
			content = k
			break
	if content == null:
		return true
	var mid := c.get_global_rect().get_center().y - content.get_global_rect().position.y
	var top := float(sc.scroll_vertical)
	return mid >= top and mid <= top + sc.size.y


## `f` on `sig` for as long as `c` is on screen: a tab switch frees the line
## while the scroll it listens to stays, so the link goes with the line.
static func _while_here(c: Node, sig: Signal, f: Callable) -> void:
	sig.connect(f)
	c.tree_exiting.connect(func() -> void:
		if sig.is_connected(f):
			sig.disconnect(f), CONNECT_ONE_SHOT)


# --- The pose -------------------------------------------------------------
## A box lays its children out again whenever one of them changes size (a line
## as the ladder counts, the scroll bar coming or going), and that puts their
## scale back to 1 and their position back in line. So a moving line's scale
## and lift are kept here and put back after every sort: it never jumps.
static func _pose(c: Control) -> Dictionary:
	if c.has_meta("_ft_pose"):
		return c.get_meta("_ft_pose")
	var p := {"s": 1.0, "dy": 0.0, "base": c.position.y}
	c.set_meta("_ft_pose", p)
	var box := c.get_parent() as Container
	if box != null:
		var resort := func() -> void:
			if is_instance_valid(c) and c.has_meta("_ft_pose"):
				p["base"] = c.position.y
				_apply(c, p)
		p["box"] = box
		p["resort"] = resort
		_while_here(c, box.sort_children, resort)
	return p


static func _put(c: Control, key: String, v: float) -> void:
	if not is_instance_valid(c):
		return
	var p := _pose(c)
	p[key] = v
	_apply(c, p)


static func _setter(c: Control, key: String) -> Callable:
	return func(v: float) -> void: _put(c, key, v)


static func _apply(c: Control, p: Dictionary) -> void:
	var s := float(p["s"])
	c.scale = Vector2(s, s)
	c.position.y = float(p["base"]) + float(p["dy"])


## At rest again: scale 1, in its place, and the sort link gone.
static func _release(c: Control) -> void:
	if not is_instance_valid(c) or not c.has_meta("_ft_pose"):
		return
	var p: Dictionary = c.get_meta("_ft_pose")
	p["s"] = 1.0
	p["dy"] = 0.0
	_apply(c, p)
	var box: Variant = p.get("box")
	if box is Container and is_instance_valid(box) and (box as Container).sort_children.is_connected(p["resort"]):
		(box as Container).sort_children.disconnect(p["resort"])
	c.remove_meta("_ft_pose")


## Where a line grows from: its text's own edge (UiKit's land uses the same).
static func _aim(c: Control) -> void:
	if is_instance_valid(c):
		c.pivot_offset = UiKit._pivot(c)
