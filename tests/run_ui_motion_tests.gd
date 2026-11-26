extends SceneTree
## godot --headless --path . --script tests/run_ui_motion_tests.gd
## Menu juice, first prototype (director 2026-11-04): the
## UiKit.Motion tokens, the hardened reveal / count_up / land, the Router's
## ease-out, sheet_in on every modal sheet, fill_bar, and the Sim the week
## result sheet (the Verdict lands on a win and a loss gets nothing; no text fades; the
## injury, MRO and Norm Smith lines come in one after another), and the round's list
## under it (each game one unit, the winner in full ink, the fade gone at the end). Proves: it ran
## (Feel.moved), it was skipped (Reduced motion), the figures are
## true on the first frame, and a real finger (tests/tap.gd) reaches Continue
## from frame 0, during the landing, and at the edge of a landing element.
## Classes are reached through load() and autoload nodes.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 2027

var _state: Node
var _uk: Object
var _feel: Object
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 6) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_uk = load("res://scripts/ui/UiKit.gd")
	_feel = load("res://scripts/ui/Feel.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://test_ui_motion.save"
	_state.settings_path = "user://test_ui_motion.cfg"
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_state.set_setting("seen_%s_intro" % key, true)
	_state.replay_seed = SUITE_SEED
	root.size = Vector2i(390, 844)
	_feel.test_motion = true
	_feel.force_phone = true
	await _settle()

	await _t("_test_tokens")
	await _t("_test_helpers_hardened")
	await _t("_test_router_ease")
	await _t("_test_fill_bar")
	await _t("_test_sheet_in")
	await _t("_test_result_sheet_win")
	await _t("_test_result_sheet_loss")
	await _t("_test_result_sheet_reduced")
	await _t("_test_land_edge_tap")
	await _t("_test_round_list")
	_t("_test_every_tween_checks_reduced")
	await _t("_test_dice_reduced")
	await _t("_test_rows_answer_a_finger")
	await _t("_test_count_waits_for_the_dots")
	await _t("_test_arrival_moves_once")
	await _t("_test_chemistry_figure_while_filling")
	await _t("_test_review_waits_for_awards")
	await _t("_test_land_hidden")
	await _t("_test_fulltime_win")
	await _t("_test_fulltime_loss_silent")
	await _t("_test_fulltime_close_win")
	await _t("_test_fulltime_big_loss")
	await _t("_test_fulltime_reduced")
	await _t("_test_fulltime_continue_frame1")
	await _t("_test_fulltime_tap_rest")
	await _t("_test_fulltime_tap_after_sting")
	await _t("_test_fulltime_drag_not_tap")
	await _t("_test_farewell_tap_holds")
	await _t("_test_farewell_back")

	_feel.test_motion = false
	_feel.force_phone = false
	_state.set_reduced_motion(false)
	print(Ran.line("UI motion", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(1 if not _failures.is_empty() else 0)


## A season started and round one played, so there is a real last match, then
## its score forced: your side wins or loses by a known margin.
## The simmed week every result sheet shows: one seeded career plays round 1
## once, and each sheet starts from a fresh copy of that round's results (a
## career and a round per sheet only replayed the same seeded week).
var _week: Dictionary = {}
var _ladder_beats: Dictionary = {}   ## _see_ladder: frame of the count's last number, frame of the pop


func _prime(win: bool, hurt := true) -> void:
	if _week.is_empty():
		_state.reset()
		_state.replay_seed = SUITE_SEED
		_state.start_season("COL", root.get_node("GameDB").club_list("COL"))
		_state.advance()
		_week = {"match": _state.last_match.duplicate(true), "results": _state.last_results.duplicate(true)}
	_state.last_match = (_week["match"] as Dictionary).duplicate(true)
	_state.last_results = (_week["results"] as Array).duplicate(true)
	var res: Dictionary = _state.last_match
	var me := 0 if str(res["home"]) == _state.my_club else 1
	var goals := [10, 10]
	var behinds := [5, 5]
	goals[me] = 13 if win else 8
	goals[1 - me] = 8 if win else 13
	res["goals"] = goals
	res["behinds"] = behinds
	res["score"] = [goals[0] * 6 + behinds[0], goals[1] * 6 + behinds[1]]
	_state.last_match = res
	var rest: Array = []
	for r in _state.last_results:
		if _state.is_my_match(r):
			rest.append(res)
		else:
			rest.append(r)
	_state.last_results = rest
	_state.last_injuries = []
	_state.last_mro = []
	if hurt:
		var pid := str((res["roster"][me] as Array)[0]["id"])
		_state.last_injuries = [{"club": _state.my_club, "id": pid, "kind": "Hamstring", "weeks": 3}]
		_state.last_mro = [{"club": _state.my_club, "id": "", "name": "Test Player", "outcome": "suspension", "weeks": 2}]


## The hub with the result sheet open. The clock starts as the sheet opens.
func _open_results(win: bool) -> Dictionary:
	_prime(win)
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	_feel.clear()
	var t0 := Time.get_ticks_msec()
	hub.call("_show_results", _state.last_results)
	return {"hub": hub, "t0": t0}


func _score_text_true(hub: Control) -> bool:
	var res: Dictionary = _state.last_match
	for side in [0, 1]:
		var row := hub.find_child("MyScore_%d" % side, true, false)
		if row == null:
			return false
		var want: String = _uk.scoreline(int(res["goals"][side]), int(res["behinds"][side]))
		var found := false
		for c in row.get_children():
			if c is Label and (c as Label).text == want:
				found = true
		if not found:
			return false
	return true


func _alpha_chain(n: Node) -> float:
	var a := 1.0
	while n != null:
		if n is CanvasItem:
			a *= (n as CanvasItem).modulate.a
		n = n.get_parent()
	return a


# ---------------------------------------------------------------------------

## Every Label under the node is fully opaque (own modulate and every ancestor's).
func _all_text_solid(root: Node) -> bool:
	if root == null:
		return false
	var ok := true
	for n in root.find_children("*", "Label", true, false):
		if not is_equal_approx(_alpha_chain(n), 1.0):
			ok = false
	return ok


func _test_tokens() -> void:
	var m = _uk.Motion
	_check(m.DUR_FAST == 0.18 and m.DUR_BASE == 0.32 and m.DUR_COUNT == 0.7 and m.DUR_HERO == 0.5
			and m.DUR_BAR == 0.45
			and m.RISE == 6.0 and m.LAND_FROM == 1.22 and m.DUR_MILESTONE == 0.9,
			"The Motion tokens hold the report's values")
	_check(m.TRANS_IN == Tween.TRANS_CUBIC and m.EASE_IN == Tween.EASE_OUT and m.TRANS_SETTLE == Tween.TRANS_QUART
			and m.TRANS_STAMP == Tween.TRANS_BACK and m.TRANS_PULSE == Tween.TRANS_SINE
			and m.TRANS_OUT == Tween.TRANS_CUBIC and m.EASE_OUT == Tween.EASE_IN,
			"The easing tokens are the report's (never linear)")


## A second call stops the first; a label that has not been laid out yet still
## grows from its own edge; the true figure always ends up on screen.
func _test_helpers_hardened() -> void:
	var host := Control.new()
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	# reveal twice: the first tween is killed, one runs, it ends visible.
	var a: Label = _uk.lbl("Reveal me", 20)
	host.add_child(a)
	_feel.clear()
	_uk.reveal(a)
	var first: Tween = a.get_meta("_motion_mod")
	_uk.reveal(a, 0.05)
	_check(not first.is_valid() and (a.get_meta("_motion_mod") as Tween).is_valid(),
			"reveal twice: the earlier tween on the node is killed")
	_check(_feel.moved == ["reveal", "reveal"], "reveal leaves a Feel.moved tag (%s)" % str(_feel.moved))
	await create_timer(0.6).timeout
	_check(is_equal_approx(a.modulate.a, 1.0), "reveal ends fully visible")
	# attention while a reveal runs: they do not fight; the node ends white.
	_uk.reveal(a)
	_uk.attention(a, 0.0)
	await create_timer(1.8).timeout
	_check(a.modulate == Color.WHITE, "attention after a reveal still ends at rest (%s)" % str(a.modulate))
	# count_up twice: ends on the second figure, exactly.
	var n: Label = _uk.lbl("", 20)
	host.add_child(n)
	_feel.clear()
	_uk.count_up(n, 50, func(v): return "%d pts" % v)
	_uk.count_up(n, 80, func(v): return "%d pts" % v)
	await create_timer(1.0).timeout
	_check(n.text == "80 pts", "count_up twice ends on the true figure (%s)" % n.text)
	_check(_feel.moved == ["count_up", "count_up"], "count_up leaves a tag (%s)" % str(_feel.moved))
	# land on a label with no layout yet: the pivot is set once it has a size.
	var l: Label = _uk.lbl("Won by 23", 30, _uk.TEXT, true)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	l.custom_minimum_size = Vector2(200, 40)
	_feel.clear()
	host.add_child(l)
	_uk.land(l)
	_check(l.size.x < 1.0 or l.size.x >= 1.0, "land on a fresh label does not fail")
	await _settle(4)
	_check(l.pivot_offset.x >= 150.0, "land's pivot is set after layout (x %s of %s)" % [str(l.pivot_offset.x), str(l.size.x)])
	_check(_feel.moved == ["land"], "land leaves a tag (%s)" % str(_feel.moved))
	var scale_tween: Tween = l.get_meta("_motion_scale")
	_uk.land(l)
	await _settle(4)
	_check(not scale_tween.is_valid(), "land twice: the earlier tween is killed")
	await create_timer(0.8).timeout
	_check(is_equal_approx(l.scale.x, 1.0), "land ends at rest")
	host.queue_free()
	await _settle()


## The screen fade eases out: a good way through it is well past the linear
## position.
func _test_router_ease() -> void:
	var router: Node = root.get_node("Router")
	var scene := Control.new()
	root.add_child(scene)
	current_scene = scene
	router.call("_ease_in")
	await _settle(3)
	await create_timer(0.10).timeout
	var sample: float = scene.modulate.a
	await create_timer(0.3).timeout
	_check(is_equal_approx(scene.modulate.a, 1.0), "The screen fade ends fully in")
	scene.queue_free()
	current_scene = null
	await _settle()
	_check(sample > 0.75, "The fade eases out (%.2f at ~0.1 s)" % sample)


func _test_fill_bar() -> void:
	var host := Control.new()
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	var fill := ColorRect.new()
	fill.set_anchors_preset(Control.PRESET_FULL_RECT)
	host.add_child(fill)
	_feel.clear()
	_uk.fill_bar(fill, 0.2, 0.8)
	_check(is_equal_approx(fill.anchor_right, 0.2), "fill_bar starts from the old value (%.2f)" % fill.anchor_right)
	_check(_feel.moved == ["fill_bar"], "fill_bar leaves a tag (%s)" % str(_feel.moved))
	await create_timer(0.2).timeout
	_check(fill.anchor_right > 0.2 and fill.anchor_right < 0.8 + 0.001, "fill_bar is part way after 0.2 s (%.2f)" % fill.anchor_right)
	await create_timer(0.6).timeout
	_check(is_equal_approx(fill.anchor_right, 0.8), "fill_bar ends on the true value (%.3f)" % fill.anchor_right)
	# Reduced motion: at the true value at once, no tag.
	_state.set_reduced_motion(true)
	_feel.clear()
	_uk.fill_bar(fill, 0.8, 0.3)
	_check(is_equal_approx(fill.anchor_right, 0.3) and _feel.moved.is_empty(),
			"Reduced motion: the bar is at its true value at once, no tag")
	_state.set_reduced_motion(false)
	host.queue_free()
	await _settle()


## Any modal sheet: the cover and panel are solid from frame 0 (no fade), the panel rises 6 px on a
## plain Control, nothing blocks Continue at frame 0, and every effect node
## lets a touch through.
func _test_sheet_in() -> void:
	var host := Control.new()
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	await _settle(2)
	_feel.clear()
	var box: Dictionary = _uk.modal_box(host, 400.0)
	var done: Button = _uk.btn("Close", _uk.NAME, true)
	box["footer"].add_child(done)
	box["body"].add_child(_uk.lbl("A sheet", 18))
	_check(_feel.moved == ["sheet_in"], "A modal sheet starts sheet_in once (%s)" % str(_feel.moved))
	var overlay: Control = box["overlay"]
	var rise: Control = box.get("rise")
	_check(rise != null and rise.get_parent() != null and not (rise.get_parent() is Container),
			"The panel sits on a plain Control, so its rise is not overwritten by a Container")
	_check(is_equal_approx(overlay.modulate.a, 1.0) and is_equal_approx(_alpha_chain(rise), 1.0), "The cover and panel are solid at frame 0 (%.2f)" % overlay.modulate.a)
	_check(is_equal_approx(rise.position.y, _uk.Motion.RISE), "The panel starts 6 px low (%.1f)" % rise.position.y)
	var wrap: Control = rise.get_parent()
	_check(wrap.mouse_filter == Control.MOUSE_FILTER_IGNORE, "The wrapper lets touches through")
	# A finger in the first frames closes it.
	var closed := [false]
	done.pressed.connect(func(): closed[0] = true; overlay.queue_free())
	var why: String = await Tap.tap(done)
	_check(why == "" and closed[0], "A real tap on the sheet's button works in its first frames (%s)" % why)
	await _settle(2)
	# A second sheet left to finish: at rest, in place, and the buttons stay put.
	var box2: Dictionary = _uk.modal_box(host, 400.0)
	box2["body"].add_child(_uk.lbl("Second", 18))
	await create_timer(0.5).timeout
	_check(is_equal_approx(box2["overlay"].modulate.a, 1.0) and is_equal_approx((box2["rise"] as Control).position.y, 0.0),
			"The sheet ends fully in and in place")
	var sz: Vector2 = (box2["shell"] as Control).size
	_check(sz.x >= 220.0 and sz.y > 40.0, "The sheet is laid out at its own size (%s)" % str(sz))
	# Reduced motion: no wrapper, no fade, no tag.
	_feel.clear()
	_state.set_reduced_motion(true)
	var b3: Dictionary = _uk.modal_box(host, 400.0)
	_check(_feel.moved.is_empty() and not b3.has("rise") and is_equal_approx(b3["overlay"].modulate.a, 1.0),
			"reduced: the sheet opens at once, no tag, no wrapper (%s)" % str(_feel.moved))
	b3["overlay"].queue_free()
	_state.set_reduced_motion(false)
	host.queue_free()
	await _settle()


func _test_result_sheet_win() -> void:
	var o: Dictionary = await _open_results(true)
	var hub: Control = o["hub"]
	# The scores are true on the very first frame, before any tween ticks.
	_check(_score_text_true(hub), "Win: both scorelines are true on the first frame")
	var verdict: Label = hub.find_child("MyVerdict", true, false)
	_check(verdict != null and verdict.text == "Won by 30" and verdict.get_theme_color("font_color") == _uk.margin_colour(true),
			"Win: the verdict says Won by 30 in the GOOD colour (%s)" % (verdict.text if verdict != null else "missing"))
	var cont: Button = hub.find_child("ResultsContinue", true, false)
	_check(cont != null and hub.find_child("SheetRise", true, false) != null, "The result sheet has Continue and the rise wrapper")
	# The notes: Injured and MRO are there, and every label on the sheet is solid from frame 0.
	var inj: Label = hub.find_child("MyInjured", true, false)
	var mro: Label = hub.find_child("MyMRO", true, false)
	_check(inj != null and mro != null, "Win: the Injured and MRO lines are there")
	_check(_all_text_solid(hub.find_child("RoundResults", true, false)),
			"Win: every line of text on the sheet is fully opaque at frame 0")
	var best: Label = hub.find_child("MyBest", true, false)
	_check(best != null and best.autowrap_mode != TextServer.AUTOWRAP_OFF and best.text_overrun_behavior == TextServer.OVERRUN_NO_TRIMMING,
			"The Best line wraps instead of trimming with an ellipsis")
	_check(hub.find_child("BarFade", true, false) != null, "The results list fades out above Continue, so no row is sliced by the button")
	await create_timer(1.2).timeout
	_check(_feel.moved.has("sheet_in") and _feel.moved.has("land") and not _feel.moved.has("stagger") and not _feel.moved.has("reveal"),
			"Win: Feel.moved shows sheet_in and land, no stagger, no reveal (%s)" % str(_feel.moved))
	_check(_all_text_solid(hub.find_child("RoundResults", true, false))
			and is_equal_approx(_alpha_chain(cont), 1.0) and is_equal_approx(verdict.scale.x, 1.0),
			"Win: by 1.3 s everything is in and at rest (sheet, text, verdict scale)")
	_check(not _feel.moved.has("burst"), "No particles on a win")
	hub.queue_free()
	await _settle()

	# A real tap on Continue in the first 0.1 s.
	o = await _open_results(true)
	hub = o["hub"]
	var c1: Button = hub.find_child("ResultsContinue", true, false)
	var spent := Time.get_ticks_msec() - int(o["t0"])
	var rising := (hub.find_child("SheetRise", true, false) as Control).position.y > 0.0
	var solid := is_equal_approx(_alpha_chain(c1), 1.0)
	var why: String = await Tap.tap(c1)
	await _settle(3)
	_check(why == "" and hub.find_child("RoundResults", true, false) == null,
			"A real tap on Continue at frame 0 closes the sheet (%s, %d ms in)" % [why, spent])
	# Headless frames are slow, so the proof is the state at touch start (still rising, already solid), not the clock.
	_check(rising and solid, "...and the touch began mid-rise, the sheet solid (%d ms in)" % spent)
	hub.queue_free()
	await _settle()

	# A real tap on Continue a moment later, still inside the verdict landing.
	o = await _open_results(true)
	hub = o["hub"]
	await create_timer(0.1).timeout
	var c2: Button = hub.find_child("ResultsContinue", true, false)
	var why2: String = await Tap.tap(c2)
	await _settle(3)
	_check(why2 == "" and hub.find_child("RoundResults", true, false) == null,
			"A real tap on Continue during the landing closes the sheet (%s)" % why2)
	hub.queue_free()
	await _settle()


func _test_result_sheet_loss() -> void:
	var o: Dictionary = await _open_results(false)
	var hub: Control = o["hub"]
	_check(_score_text_true(hub), "Loss: both scorelines are true on the first frame")
	var verdict: Label = hub.find_child("MyVerdict", true, false)
	_check(verdict != null and verdict.text == "Lost by 30" and verdict.get_theme_color("font_color") == _uk.margin_colour(false),
			"Loss: the verdict says Lost by 30 in the BAD colour (%s)" % (verdict.text if verdict != null else "missing"))
	await create_timer(0.7).timeout
	_check(_feel.moved.has("sheet_in") and not _feel.moved.has("reveal") and not _feel.moved.has("stagger") and not _feel.moved.has("land"),
			"Loss: sheet_in only, no reveal, stagger or land (%s)" % str(_feel.moved))
	_check(_all_text_solid(hub.find_child("RoundResults", true, false)), "Loss: every line of text is fully opaque")
	_check(not _feel.heard.has("land"), "Loss: no landing sting either (%s)" % str(_feel.heard))
	_check(is_equal_approx(verdict.scale.x, 1.0) and is_equal_approx(verdict.modulate.a, 1.0),
			"Loss: the verdict never scaled and ends fully visible")
	var why: String = await Tap.tap(hub.find_child("ResultsContinue", true, false))
	await _settle(3)
	_check(why == "" and hub.find_child("RoundResults", true, false) == null, "Loss: Continue closes the sheet (%s)" % why)
	hub.queue_free()
	await _settle()


func _test_result_sheet_reduced() -> void:
	# Reduced motion: no new tag at all, true scores at once.
	_state.set_reduced_motion(true)
	var o: Dictionary = await _open_results(true)
	var hub: Control = o["hub"]
	var verdict: Label = hub.find_child("MyVerdict", true, false)
	var mro: Label = hub.find_child("MyMRO", true, false)
	_check(_score_text_true(hub) and verdict.text == "Won by 30", "Reduced motion: true scores on the first frame")
	_check(_feel.moved.is_empty(), "Reduced motion: no tags at all (%s)" % str(_feel.moved))
	_check(is_equal_approx(_alpha_chain(hub.find_child("ResultsContinue", true, false)), 1.0)
			and is_equal_approx(mro.modulate.a, 1.0) and is_equal_approx(verdict.scale.x, 1.0)
			and hub.find_child("SheetRise", true, false) == null,
			"Reduced motion: the sheet, the notes and the verdict are fully in on the first frame")
	hub.queue_free()
	await _settle()
	_state.set_reduced_motion(false)


## A finger at the edge of a landing element, mid-overshoot: the scaled element
## is hit-tested by its drawn size, so a tap just inside its layout edge and a
## tap just outside it (inside the drawn edge) both reach it, and nothing else.
func _test_land_edge_tap() -> void:
	var host := Control.new()
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	var b: Button = _uk.btn("Edge", _uk.NAME, true)
	b.position = Vector2(120, 300)
	b.custom_minimum_size = Vector2(150, 56)
	b.size = Vector2(150, 56)
	host.add_child(b)
	await _settle(3)
	var presses := [0]
	b.pressed.connect(func(): presses[0] += 1)
	_feel.clear()
	Engine.time_scale = 0.05
	_uk.land(b)
	await _settle(2)
	var s1 := b.scale.x
	var why_in: String = await _tap_at(b, b.get_screen_transform() * Vector2(3, 28))
	var s2 := b.scale.x
	_check(why_in == "" and presses[0] == 1 and s1 > 1.05 and s2 > 1.0,
			"A real tap 3 px inside the edge of a landing button reaches it (%s; scale %.2f, %.2f)" % [why_in, s1, s2])
	# Just outside the layout edge, inside the drawn edge, mid-overshoot.
	_feel.clear()
	Engine.time_scale = 1.0
	await create_timer(0.8).timeout
	Engine.time_scale = 0.05
	_uk.land(b)
	await _settle(2)
	# 1.5 px left of the unscaled layout edge, in screen space: outside the layout,
	# inside the drawn (scaled) rect.
	var why_out: String = await _tap_at(b, Vector2(b.position.x - 1.5, b.position.y + 28.0))
	_check(why_out == "" and presses[0] == 2 and b.scale.x > 1.03,
			"A tap just outside the layout edge but inside the drawn edge also reaches it mid-overshoot (%s; scale %.2f)" % [why_out, b.scale.x])
	Engine.time_scale = 1.0
	await create_timer(0.8).timeout
	_check(is_equal_approx(b.scale.x, 1.0), "The button is back at rest")
	# Effect nodes never take a touch.
	var ok := true
	for c in host.get_children():
		if c is Control and not c is BaseButton and (c as Control).mouse_filter != Control.MOUSE_FILTER_IGNORE:
			ok = false
	_check(ok, "Every effect node in the host ignores the mouse")
	host.queue_free()
	await _settle()


## A touch at an exact screen point; "" when `c` was pressed.
func _tap_at(c: BaseButton, at: Vector2) -> String:
	var hit := [false]
	var on_press := func(): hit[0] = true
	c.pressed.connect(on_press)
	for down in [true, false]:
		var touch := InputEventScreenTouch.new()
		touch.index = 0
		touch.position = at
		touch.pressed = down
		Input.parse_input_event(touch)
		Input.flush_buffered_events()
		await _settle(2)
	c.pressed.disconnect(on_press)
	if hit[0]:
		return ""
	var top := root.gui_get_hovered_control()
	return "the tap at %s went to %s" % [str(at), top.name if top != null else "nothing"]


## The round's list (director, 2026-11-07: "really hard to read and know which game they
## belong to. And the bottom row is faded by the UI effect"). A simmed week lists your
## game with the rest; one other game is forced level.
func _test_round_list() -> void:
	_prime(true, false)
	var rest: Array = []
	var level := ""
	for r in _state.last_results:
		var res: Dictionary = r
		if level == "" and not _state.is_my_match(res):
			res["goals"] = [11, 12]
			res["behinds"] = [9, 3]
			res["score"] = [75, 75]
			level = str(res["home"])
		rest.append(res)
	_state.last_results = rest
	_state.last_match = {}
	var hub: Control = load("res://scenes/HubScene.tscn").instantiate()
	root.add_child(hub)
	await _settle()
	hub.call("_show_results", _state.last_results)
	await _settle(8)
	var sheet: Control = hub.find_child("RoundResults", true, false)
	var list: Control = sheet.find_child("ResultsList", true, false)
	_check(list != null, "The round's list is on the sheet")
	if list == null:
		hub.queue_free()
		return
	var games: Array = []
	for c in list.get_children():
		if str(c.name).begins_with("ResultGame_"):
			games.append(c)
	_check(games.size() == _state.last_results.size(),
			"One unit per game: %d of %d" % [games.size(), _state.last_results.size()])
	# Each unit holds exactly the two clubs of one game, styled by the result.
	var pairs := {}
	for r in _state.last_results:
		pairs[str(r["home"]) + "|" + str(r["away"])] = r
	var grouped := true
	var styled := true
	var saw_draw := false
	var why := ""
	for g in games:
		var rows: Array = (g as Node).find_children("ResultRow_*", "", true, false)
		if rows.size() != 2:
			grouped = false
			why = "%s holds %d rows" % [g.name, rows.size()]
			continue
		var key := str(rows[0].name).trim_prefix("ResultRow_") + "|" + str(rows[1].name).trim_prefix("ResultRow_")
		if not pairs.has(key):
			grouped = false
			why = "%s pairs %s, not a game" % [g.name, key]
			continue
		var res: Dictionary = pairs[key]
		for side in [0, 1]:
			var row: Node = rows[side]
			var a := int(res["score"][side])
			var b := int(res["score"][1 - side])
			var want := "draw" if a == b else ("win" if a > b else "lose")
			var code_l: Label = row.get_node("Code")
			var score_l: Label = row.get_node("Score")
			var ink: Color = _uk.MUTED if want == "lose" else _uk.TEXT
			var font: Font = _uk.BOLD if want == "win" else _uk.FONT
			if str(row.get_meta("result", "")) != want \
					or code_l.get_theme_color("font_color") != ink or score_l.get_theme_color("font_color") != ink \
					or code_l.get_theme_font("font") != font or score_l.get_theme_font("font") != font:
				styled = false
				why = "%s should read as %s" % [row.name, want]
			if want == "draw":
				saw_draw = true
	_check(grouped, "Each game's two clubs sit together in one unit (%s)" % why)
	_check(styled, "Winner in full ink and bold, loser muted, a draw both alike (%s)" % why)
	_check(saw_draw, "The level game reads as a draw on both lines")
	var rules := 0
	for c in list.get_children():
		if c is ColorRect:
			rules += 1
	_check(rules == games.size() - 1, "A rule between games (%d for %d games)" % [rules, games.size()])
	# Your game first, edged in your colour; no other game is edged.
	var edges_ok: bool = games.size() > 1 and bool(games[0].get_meta("mine", false)) \
			and (games[0].get_node("ClubBar") as ColorRect).color.a > 0.0
	for i in range(1, games.size()):
		if bool(games[i].get_meta("mine", false)) or (games[i].get_node("ClubBar") as ColorRect).color.a > 0.0:
			edges_ok = false
	_check(edges_ok, "Your game comes first, edged in your club's colour, and only yours")
	# The score sits by the code, not across the row.
	var r0: Node = (games[1] as Node).find_children("ResultRow_*", "", true, false)[0]
	var gap: float = (r0.get_node("Score") as Control).get_global_rect().position.x \
			- (r0.get_node("Code") as Control).get_global_rect().end.x
	_check(gap < 24.0, "The score starts within 24 px of the club code (%.0f px)" % gap)
	# The fade over Continue: there while there is more below, gone at the end.
	var sc := list.get_parent().get_parent() as ScrollContainer
	var fade: Control = sheet.find_child("BarFade", true, false)
	var bar := sc.get_v_scroll_bar()
	_check(bar.max_value - bar.page > 40.0 and fade.modulate.a > 0.9,
			"At the top the list runs on below Continue and the fade shows it (alpha %.2f)" % fade.modulate.a)
	# A real wheel at the list, the way a player scrolls on PC (a phone drag ends the same way).
	var at := list.get_global_rect().get_center()
	for i in range(80):
		if bar.value >= bar.max_value - bar.page - 0.5:
			break
		for down in [true, false]:
			var wheel := InputEventMouseButton.new()
			wheel.button_index = MOUSE_BUTTON_WHEEL_DOWN
			wheel.pressed = down
			wheel.factor = 1.0
			wheel.position = at
			wheel.global_position = at
			Input.parse_input_event(wheel)
		Input.flush_buffered_events()
		await process_frame
	await _settle(4)
	_check(bar.value >= bar.max_value - bar.page - 0.5, "Real wheel scrolling reaches the end of the list")
	_check(is_equal_approx(fade.modulate.a, 0.0), "At the end the fade is gone (alpha %.2f)" % fade.modulate.a)
	var last_row: Control = (games[games.size() - 1] as Node).find_children("ResultRow_*", "", true, false)[1]
	var view := sc.get_global_rect()
	var lr := last_row.get_global_rect()
	_check(lr.position.y >= view.position.y and lr.end.y <= view.end.y + 0.5,
			"The last row is wholly inside the list's window at the end (%s in %s)" % [str(lr), str(view)])
	# Back to the top: the fade returns.
	sc.scroll_vertical = 0
	await _settle(3)
	_check(fade.modulate.a > 0.9, "Scrolled back to the top, the fade is back (alpha %.2f)" % fade.modulate.a)
	var tapped: String = await Tap.tap(sheet.find_child("ResultsContinue", true, false))
	await _settle(3)
	_check(tapped == "" and hub.find_child("RoundResults", true, false) == null,
			"A real tap on Continue still closes the sheet (%s)" % tapped)
	# The hub's own page: its fade over the pinned bar also goes at the page's end.
	await _settle(4)
	var page_fade: Control = hub.find_child("BarFade", true, false)
	var page_sc: ScrollContainer = null
	for n in hub.find_children("*", "ScrollContainer", true, false):
		if not (n as Node).is_queued_for_deletion() and (n as Control).is_visible_in_tree():
			page_sc = n
			break
	_check(page_fade != null and page_sc != null, "The hub page has its scroll and its fade")
	if page_fade != null and page_sc != null:
		page_sc.scroll_vertical = int(page_sc.get_v_scroll_bar().max_value)
		await _settle(3)
		_check(is_equal_approx(page_fade.modulate.a, 0.0),
				"At the hub page's end its fade is gone too (alpha %.2f)" % page_fade.modulate.a)
	hub.queue_free()
	await _settle()


## Reduced motion keeps the screen still (Settings: "no fades, counting numbers,
## pulses, moving backgrounds or shake"), so every tween in the game's scripts sits
## in a function that asks first (UiKit.motion_on, Feel.reduced, a screen's own
## reduced check), or is on this list with the place that asks for it.
const TWEEN_GUARDS := ["motion_on()", "Feel.reduced", "reduced_motion()", "_reduced()", "should_run()"]
const TWEEN_ASKED_UPSTREAM := {
	"scripts/ui/DraftScene.gd:_show_beat": "draft night's stage plays only when _night_on() (motion_on)",
	"scripts/ui/DraftScene.gd:_end_beat": "fades the stage _show_beat put up",
	"scripts/ui/DraftScene.gd:_slide_recent": "called only when motion_on (_recent_rows)",
	"scripts/ui/UiKit.gd:_own": "the helpers' tween, made after each helper asks",
	"scripts/ui/UiKit.gd:_after": "a helper's delay, made after the helper asks",
	"scripts/ui/match/PremiershipCeremony.gd:_at": "a beat's delay; only _beats() calls it, after _start() asks",
	"scripts/ui/match/PremiershipCeremony.gd:_tw": "the beats' tween; reached only after _start() asks",
}


func _test_every_tween_checks_reduced() -> void:
	var files: Array = []
	var dirs: Array = ["res://scripts"]
	while not dirs.is_empty():
		var d: String = dirs.pop_back()
		var da := DirAccess.open(d)
		if da == null:
			continue
		for sub in da.get_directories():
			dirs.append(d + "/" + sub)
		for f in da.get_files():
			if f.ends_with(".gd"):
				files.append(d + "/" + f)
	_check(files.size() > 100, "the scan reads the game's scripts (%d)" % files.size())
	var seen := 0
	var bare: Array = []
	var used := {}
	for path in files:
		var lines: PackedStringArray = FileAccess.get_file_as_string(path).split("\n")
		var start := -1
		var fn := ""
		for i in range(lines.size()):
			var l: String = lines[i]
			if l.begins_with("func ") or l.begins_with("static func "):
				start = i
				fn = l.trim_prefix("static ").trim_prefix("func ").get_slice("(", 0)
			if not "create_tween(" in l or l.strip_edges().begins_with("#"):
				continue
			seen += 1
			var key := "%s:%s" % [str(path).trim_prefix("res://"), fn]
			var body := "\n".join(lines.slice(maxi(start, 0), i + 1))
			var asks := false
			for g in TWEEN_GUARDS:
				asks = asks or g in body
			if TWEEN_ASKED_UPSTREAM.has(key):
				used[key] = true
			elif not asks:
				bare.append("%s line %d" % [key, i + 1])
	_check(seen >= 20, "the scan finds the game's tweens (%d)" % seen)
	_check(bare.is_empty(), "every tween asks Reduced motion first (not: %s)" % ", ".join(bare))
	for k in TWEEN_ASKED_UPSTREAM:
		_check(used.has(k), "%s still makes a tween (else take it off the list)" % k)


## The dice at a break talk tumble; with Reduced motion they land at once.
func _test_dice_reduced() -> void:
	var host := Control.new()
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	var dice: Control = load("res://scripts/ui/match/TalkDice.gd").new()
	host.add_child(dice)
	var landed := [0]
	_state.set_reduced_motion(true)
	_feel.clear()
	dice.roll([3, 5], func() -> void: landed[0] += 1)
	_check(dice.is_landed() and dice.faces == [3, 5] and landed[0] == 1 and _feel.moved.is_empty(),
			"reduced: the dice land on the roll at once, no tumble (%s)" % str(_feel.moved))
	_state.set_reduced_motion(false)
	_feel.clear()
	dice.roll([6, 2], func() -> void: landed[0] += 1)
	_check(not dice.is_landed() and _feel.moved == ["dice"], "motion on: the dice tumble first (%s)" % str(_feel.moved))
	await create_timer(1.6).timeout
	_check(dice.is_landed() and dice.faces == [6, 2] and landed[0] == 2, "motion on: then land on the roll")
	host.queue_free()
	await _settle()


## Every button answers a finger (director, 2026-10-11): a player row on My list
## and a coach's row on Staff press in under a real tap, and still do their job.
func _test_rows_answer_a_finger() -> void:
	_prime(true, false)
	for case in [["res://scenes/ListScene.tscn", "Row_"], ["res://scenes/StaffScene.tscn", "StaffRow_"]]:
		var scene: Control = load(str(case[0])).instantiate()
		# My list opens on its shape; the rows are on the Full list tab.
		if "_pane" in scene:
			scene.set("_pane", "list")
		root.add_child(scene)
		await _settle(8)
		var row: Button = null
		for b in scene.find_children(str(case[1]) + "*", "Button", true, false):
			if (b as Control).is_visible_in_tree():
				row = b
				break
		_check(row != null, "%s: a row is on screen" % case[0])
		if row == null:
			scene.queue_free()
			continue
		# The list's row opens a profile screen: here only its press is wanted.
		for c in row.pressed.get_connections():
			if (c["callable"] as Callable).get_method() == "_open_profile":
				row.pressed.disconnect(c["callable"])
		var hit := [false]
		row.pressed.connect(func() -> void: hit[0] = true)
		await Tap.steady(row)
		_feel.clear()
		var why: String = await Tap.tap(row)
		_check(why == "" and hit[0], "%s: a real tap reaches %s (%s)" % [case[0], row.name, why])
		_check("press" in _feel.moved, "%s: %s presses in under the finger (%s)" % [case[0], row.name, str(_feel.moved)])
		_check(str(row.get_meta("feel", "")) == "soft", "%s: %s sounds as a button does" % [case[0], row.name])
		scene.queue_free()
		await _settle()


## An arriving screen's count waits for the dots between screens (UI Batch 4):
## built under the cover it shows the figure it counts from, and counts once
## the dots have gone, where it is seen.
func _test_count_waits_for_the_dots() -> void:
	var wipe: Node = root.get_node("ScreenTransition")
	var host := Control.new()
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	var got := {}
	_feel.clear()
	wipe.call("cover", func():
		var n: Label = _uk.lbl("", 20)
		host.add_child(n)
		got["label"] = n
		_uk.count_up(n, 80, func(v): return "%d pts" % v)
		got["under"] = n.text
		got["moved"] = _feel.moved.duplicate())
	await wipe.cleared
	var n: Label = got.get("label")
	_check(n != null and str(got.get("under", "")) == "0 pts",
			"Under the dots the count shows where it starts (%s)" % str(got.get("under", "")))
	_check((got.get("moved", ["x"]) as Array).is_empty(), "Under the dots it has not started (%s)" % str(got.get("moved", "")))
	var at_clear := int(n.text.split(" ")[0]) if n != null else 99
	_check(at_clear < 40, "It counts once the dots have gone (%s as they clear)" % (n.text if n != null else "no label"))
	await create_timer(1.0).timeout
	_check(n != null and n.text == "80 pts", "It ends on the true figure (%s)" % (n.text if n != null else "no label"))
	host.queue_free()
	await _settle()


## Stats, Team selection and the Season review move as you arrive (counts,
## the chemistry bar, a fade) and not again when the page is rebuilt by a
## tab, a sort, a pick or a resize.
func _test_arrival_moves_once() -> void:
	var db = root.get_node("GameDB")
	_state.start_season("COL", db.club_list("COL"))
	for i in range(3):
		_state.advance()
	var paths := ["res://scenes/StatsHubScene.tscn", "res://scenes/SelectionScene.tscn",
			"res://scenes/SeasonReviewScene.tscn"]
	_check(paths.size() == 3, "Three screens arrive with motion")
	for path in paths:
		_feel.clear()
		var scene: Control = load(path).instantiate()
		root.add_child(scene)
		await _settle()
		var moved: Array = _feel.moved.duplicate()
		_check(moved.has("count_up") or moved.has("fill_bar"), "%s: arriving, its figures move (%s)" % [path.get_file(), str(moved)])
		_feel.clear()
		scene.call("_build")
		await _settle()
		_check(_feel.moved.is_empty(), "%s: a rebuild does not move them again (%s)" % [path.get_file(), str(_feel.moved)])
		scene.queue_free()
		await _settle()


## Arriving at Team selection the chemistry figure counts up with its bar and
## sits where the meter puts that figure at every step: never to the left of
## the bar's start, over the words beside it (the short phone bar).
func _test_chemistry_figure_while_filling() -> void:
	var db = root.get_node("GameDB")
	_state.start_season("COL", db.club_list("COL"))
	var scene: Control = load("res://scenes/SelectionScene.tscn").instantiate()
	root.add_child(scene)
	var fill: Control = null
	var fig: Label = null
	var worst := INF
	var seen := {}
	for i in range(30):
		await process_frame
		if fill == null:
			fill = scene.find_child("ChemistryFill", true, false)
			fig = fill.get_node_or_null("ChemistryFigure") if fill != null else null
		if fig == null or fill.size.x <= 0.0 and fill.get_parent_control().size.x <= 0.0:
			continue
		seen[fig.text] = true
		worst = minf(worst, fig.get_global_rect().position.x - fill.get_global_rect().position.x)
	_check(fig != null, "Team selection has its chemistry figure")
	_check(seen.size() >= 3, "The figure counts up with the bar (%d figures seen)" % seen.size())
	_check(worst >= -0.5, "While it fills the figure never starts left of the bar (%.1f px)" % worst)
	scene.queue_free()
	await _settle()


## On a first visit awards night opens over the Season review: the review's
## figures wait under it and count once it has closed.
func _test_review_waits_for_awards() -> void:
	var db = root.get_node("GameDB")
	_state.start_season("COL", db.club_list("COL"))
	var season = _state.season
	season.round_index = season.fixture.size()
	_state.ensure_finals()
	var guard := 0
	while not season.is_season_over() and guard < 10:
		guard += 1
		_state.advance()
	_check(season.is_season_over() and not _state.season_awards.is_empty(), "The season is over with its awards")
	_state.season_awards["presentation_seen"] = false
	var scene: Control = load("res://scenes/SeasonReviewScene.tscn").instantiate()
	root.add_child(scene)
	await _settle()
	var night: Control = scene.find_child("SeasonAwards", true, false)
	var finish: Label = scene.find_child("SeasonFinish", true, false)
	_check(night != null and finish != null, "Awards night is up over the review")
	_check(finish != null and not finish.has_meta("_motion_text"), "Under awards night the review's figures wait")
	if night != null:
		night.queue_free()
	await _settle()
	finish = scene.find_child("SeasonFinish", true, false)
	_check(finish != null and finish.has_meta("_motion_text"), "Once it closes, the finish counts")
	_feel.clear()
	scene.call("_build")
	await _settle()
	_check(_feel.moved.is_empty(), "After that a rebuild moves nothing (%s)" % str(_feel.moved))
	scene.queue_free()
	await _settle()


# ---------------------------------------------------------------------------
# Full time (director, 2026-11-25): the result lands, then the ladder move
# (FullTimeMotion).

## land(hidden) (the full-time verdict): invisible from the call until its beat,
## then it fades up as it lands. Without `hidden` (the hub's sheet) the text is
## solid throughout; with Reduced motion it is there at once.
func _test_land_hidden() -> void:
	var host := Control.new()
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(host)
	var l: Label = _uk.lbl("Won by 23", 30, _uk.TEXT, true)
	host.add_child(l)
	await _settle(2)
	_feel.clear()
	_uk.land(l, 0.4, true, true)
	_check(is_equal_approx(l.modulate.a, 0.0), "land(hidden): invisible from the call (alpha %.2f)" % l.modulate.a)
	await create_timer(0.15).timeout
	_check(is_equal_approx(l.modulate.a, 0.0) and _feel.moved.is_empty() and not _feel.heard.has("land"),
			"land(hidden): still invisible, still and silent before its beat (alpha %.2f, %s)" % [l.modulate.a, str(_feel.moved)])
	await create_timer(1.0).timeout
	_check(is_equal_approx(l.modulate.a, 1.0) and is_equal_approx(l.scale.x, 1.0) and _feel.moved == ["land"] and _feel.heard.has("land"),
			"land(hidden): after its beat it has landed, solid and at rest, with the sting (alpha %.2f, scale %.2f, %s)"
			% [l.modulate.a, l.scale.x, str(_feel.moved)])
	var m: Label = _uk.lbl("Won by 9", 30, _uk.TEXT, true)
	host.add_child(m)
	await _settle(2)
	_uk.land(m, 0.3)
	_check(is_equal_approx(m.modulate.a, 1.0), "land without hidden leaves the text solid from the call (the hub's sheet)")
	_state.set_reduced_motion(true)
	var r: Label = _uk.lbl("Won by 4", 30, _uk.TEXT, true)
	host.add_child(r)
	_uk.land(r, 0.3, true, true)
	_check(is_equal_approx(r.modulate.a, 1.0), "Reduced motion: land(hidden) leaves it visible from the call")
	_state.set_reduced_motion(false)
	host.queue_free()
	await _settle()


## Full time as Review match opens it, your score and theirs forced as [goals,
## behinds]. The ladder spot before is forced four places away, so the ladder
## line has a count to make.
func _open_fulltime(mine: Array, theirs: Array) -> Control:
	_prime(true, false)
	var res: Dictionary = _state.last_match
	var me := 0 if str(res["home"]) == _state.my_club else 1
	var goals := [0, 0]
	var behinds := [0, 0]
	goals[me] = int(mine[0])
	behinds[me] = int(mine[1])
	goals[1 - me] = int(theirs[0])
	behinds[1 - me] = int(theirs[1])
	res["goals"] = goals
	res["behinds"] = behinds
	res["score"] = [goals[0] * 6 + behinds[0], goals[1] * 6 + behinds[1]]
	_state.last_match = res
	var now: int = _state.my_position()
	_state.last_pos_before = now + 4 if now <= 14 else now - 4
	_state.review_requested = true
	_feel.clear()
	var scene: Control = load("res://scenes/MatchScene.tscn").instantiate()
	root.add_child(scene)
	return scene


func _ft_shell(scene: Node) -> Control:
	var rise := scene.find_child("SheetRise", true, false)
	return rise.get_child(0) as Control if rise != null and rise.get_child_count() > 0 else null


func _ft_rows(scene: Node) -> Array:
	return [scene.find_child("FinalScore_0", true, false), scene.find_child("FinalScore_1", true, false)]


## Watch full time for `secs`, sampling every frame: the verdict's largest scale
## and drop, the flash's brightest, and the sheet's widest sideways move.
func _watch_fulltime(scene: Node, secs: float) -> Dictionary:
	var v: Control = scene.find_child("Verdict", true, false)
	var shell := _ft_shell(scene)
	var x0 := shell.position.x if shell != null else 0.0
	var out := {"max_s": 0.0, "max_dy": 0.0, "flash": 0.0, "max_dx": 0.0}
	var timer := create_timer(secs)
	while timer.time_left > 0.0:
		await process_frame
		if is_instance_valid(v):
			out["max_s"] = maxf(float(out["max_s"]), v.scale.x)
			if v.has_meta("_ft_pose"):
				out["max_dy"] = maxf(float(out["max_dy"]), absf(float((v.get_meta("_ft_pose") as Dictionary)["dy"])))
		if shell != null and is_instance_valid(shell):
			if shell.has_meta("_ft_flash"):
				out["flash"] = maxf(float(out["flash"]), float((shell.get_meta("_ft_flash") as Dictionary)["a"]))
			out["max_dx"] = maxf(float(out["max_dx"]), absf(shell.position.x - x0))
	return out


## The verdict and both score rows are solid, at scale 1 and back in their places.
func _ft_at_rest(scene: Node) -> bool:
	var v: Control = scene.find_child("Verdict", true, false)
	if v == null or not is_equal_approx(_alpha_chain(v), 1.0) or not is_equal_approx(v.scale.x, 1.0) or v.has_meta("_ft_pose"):
		return false
	for r in _ft_rows(scene):
		if r == null or not is_equal_approx((r as Control).modulate.a, 1.0) or (r as Node).has_meta("_ft_pose"):
			return false
	return true


## The ladder line counts the first time it is in view: on a phone, once it is
## scrolled up into the sheet's window. Returns the line once it has had time.
func _see_ladder(scene: Node, want: String) -> Label:
	var l: Label = scene.find_child("LadderMove", true, false)
	_check(l != null and l.text == want, "The ladder line holds the true words from the first frame (%s)" % (l.text if l != null else "missing"))
	if l == null:
		return null
	var sc := scene.find_child("FullTime", true, false).find_children("*", "ScrollContainer", true, false)[0] as ScrollContainer
	var mid := l.get_global_rect().get_center().y
	var view := sc.get_global_rect()
	if mid < view.position.y or mid > view.end.y:
		_check(is_equal_approx(l.modulate.a, 0.0) and not _feel.moved.has("count_up"),
				"Below the fold the ladder line waits, hidden, uncounted (alpha %.2f)" % l.modulate.a)
		sc.scroll_vertical += int(mid - view.get_center().y)
	else:
		_check(_feel.moved.has("count_up"), "In view, the ladder line counted at its beat (%s)" % str(_feel.moved))
	# Frame by frame: when the count's last number shows, and when the pop starts.
	_ladder_beats = {"last": -1, "pop": -1}
	var counted := false
	var frame := 0
	var t := create_timer(1.6)
	while t.time_left > 0.0:
		await process_frame
		frame += 1
		if l.text != want:
			counted = true
		elif counted and int(_ladder_beats["last"]) < 0:
			_ladder_beats["last"] = frame
		if _feel.moved.has("ft_pop") and int(_ladder_beats["pop"]) < 0:
			_ladder_beats["pop"] = frame
	_check(_feel.moved.has("count_up") and is_equal_approx(l.modulate.a, 1.0) and l.text == want and is_equal_approx(l.scale.x, 1.0),
			"Seen, the ladder line counts to the true spot and rests solid (%s, alpha %.2f)" % [l.text, l.modulate.a])
	return l


## A 30-point win: the verdict winds up and slams, the sheet flashes your club's
## colour, the rows snap in under it, and the ladder count ends on the pop.
func _test_fulltime_win() -> void:
	var scene := _open_fulltime([13, 5], [8, 5])
	var v: Label = scene.find_child("Verdict", true, false)
	var rows := _ft_rows(scene)
	var cont: Control = scene.find_child("FullTimeContinue", true, false)
	_check(v != null and v.text == "Won by 30", "Full time: the verdict says Won by 30 from the first frame (%s)" % (v.text if v != null else "missing"))
	_check(v != null and is_equal_approx(v.modulate.a, 0.0) and rows[0] != null and is_equal_approx((rows[0] as Control).modulate.a, 0.0)
			and is_equal_approx((rows[1] as Control).modulate.a, 0.0),
			"The verdict and the score rows are hidden until their beat, never at rest and then popping")
	_check(cont != null and is_equal_approx(_alpha_chain(cont), 1.0), "Continue is solid from the first frame")
	var want: String = _state.ladder_move_line(_state.last_pos_before)
	var w: Dictionary = await _watch_fulltime(scene, 1.3)
	_check(_feel.moved.has("ft_slam") and _feel.moved.has("ft_flash") and _feel.moved.count("ft_snap") == 2
			and not _feel.moved.has("ft_slam_heavy") and not _feel.moved.has("ft_shake") and not _feel.moved.has("land"),
			"A 30-point win: wind-up and slam, the flash, both rows snap in; no heavy slam or shake (%s)" % str(_feel.moved))
	_check(_feel.heard.has("land"), "A win: the sting on the impact")
	_check(float(w["max_s"]) > 1.3 and float(w["max_s"]) <= 1.361, "A win winds up toward 1.36 (largest %.3f)" % float(w["max_s"]))
	_check(float(w["flash"]) > 0.2 and float(w["flash"]) <= 0.301 and is_zero_approx(float(w["max_dx"])),
			"A win: the winner's colour flashes to 0.30 (%.2f); the sheet stays still" % float(w["flash"]))
	var shell := _ft_shell(scene)
	_check(_ft_at_rest(scene) and shell != null and is_zero_approx(float((shell.get_meta("_ft_flash") as Dictionary)["a"])),
			"A win: by 1.3 s everything is at rest and the flash gone")
	var ink: Color = _uk.club_ink(_state.my_club)
	_check(shell != null and (shell.get_meta("_ft_flash") as Dictionary)["col"] == Color(ink, 1.0),
			"A win: the flash is your club's name colour, which reads on the dark sheet (%s)" % str(ink))
	var l := await _see_ladder(scene, want)
	_check(_feel.moved.has("ft_pop") and l != null and l.get_theme_color("font_color") == Color("cfcabe"),
			"The ladder count ends on the pop and its colour comes back (%s)" % str(_feel.moved))
	var last := int(_ladder_beats.get("last", -1))
	var pop := int(_ladder_beats.get("pop", -1))
	_check(last > 0 and pop >= last and pop - last <= 1,
			"The pop lands with the count's last number (number on frame %d, pop on frame %d)" % [last, pop])
	_check(_all_text_solid(scene.find_child("FullTime", true, false)), "Every line of full time ends solid")
	scene.queue_free()
	await _settle()


## A 30-point loss: the plain slam, silent and without a flash (director,
## 2026-11-25: no celebratory sting on a loss, and no flash).
func _test_fulltime_loss_silent() -> void:
	var scene := _open_fulltime([8, 5], [13, 5])
	var v: Label = scene.find_child("Verdict", true, false)
	_check(v != null and v.text == "Lost by 30", "Loss: the verdict says Lost by 30 (%s)" % (v.text if v != null else "missing"))
	var w: Dictionary = await _watch_fulltime(scene, 1.2)
	_check(_feel.moved.has("ft_slam") and not _feel.moved.has("ft_slam_heavy") and not _feel.moved.has("ft_flash")
			and not _feel.moved.has("ft_shake") and not _feel.heard.has("land"),
			"A 30-point loss: the plain slam, no flash, no shake, no sting (%s, %s)" % [str(_feel.moved), str(_feel.heard)])
	_check(is_zero_approx(float(w["flash"])), "A loss: the sheet never flashes (%.2f)" % float(w["flash"]))
	_check(_ft_at_rest(scene), "A 30-point loss: it ends solid and at rest")
	scene.queue_free()
	await _settle()


## A close win (under 12): the heavy slam and the shake; Screen shake Off keeps
## the sheet still.
func _test_fulltime_close_win() -> void:
	_state.set_screen_shake_on(true)
	var scene := _open_fulltime([10, 5], [10, 0])
	var w: Dictionary = await _watch_fulltime(scene, 1.4)
	_check(_feel.moved.has("ft_slam_heavy") and _feel.moved.has("ft_shake") and _feel.moved.has("ft_flash"),
			"A 5-point win: the heavy slam, the shake, the flash (%s)" % str(_feel.moved))
	_check(float(w["max_s"]) > 1.4 and float(w["max_s"]) <= 1.481 and float(w["max_dx"]) > 1.5 and float(w["max_dx"]) <= 3.01,
			"A close win winds up toward 1.48 (%.3f) and shakes up to 3 px (%.2f)" % [float(w["max_s"]), float(w["max_dx"])])
	var shell := _ft_shell(scene)
	_check(_ft_at_rest(scene) and shell != null and is_zero_approx(shell.position.x), "A close win ends at rest, the sheet back in place")
	scene.queue_free()
	await _settle()
	_state.set_screen_shake_on(false)
	scene = _open_fulltime([10, 5], [10, 0])
	w = await _watch_fulltime(scene, 1.2)
	_check(_feel.moved.has("ft_slam_heavy") and not _feel.moved.has("ft_shake") and is_zero_approx(float(w["max_dx"])),
			"Screen shake Off: the heavy slam without the shake (%s)" % str(_feel.moved))
	scene.queue_free()
	await _settle()
	_state.set_screen_shake_on(true)


## A big loss (40 or more): the verdict sinks into place, silent, and the rows
## fade up.
func _test_fulltime_big_loss() -> void:
	_state.set_screen_shake_on(true)
	var scene := _open_fulltime([6, 5], [13, 8])
	var v: Label = scene.find_child("Verdict", true, false)
	_check(v != null and v.text == "Lost by 45", "Big loss: Lost by 45 (%s)" % (v.text if v != null else "missing"))
	var w: Dictionary = await _watch_fulltime(scene, 1.4)
	_check(_feel.moved.has("ft_sink") and not _feel.moved.has("ft_slam") and not _feel.moved.has("ft_flash")
			and not _feel.moved.has("ft_shake") and not _feel.heard.has("land") and _feel.moved.count("reveal") >= 2,
			"A 45-point loss: it sinks and the rows fade up; no slam, flash, shake or sting (%s, %s)" % [str(_feel.moved), str(_feel.heard)])
	_check(float(w["max_dy"]) >= 7.9 and float(w["max_dy"]) <= 8.01 and float(w["max_s"]) <= 1.001,
			"Big loss: it falls from 8 px above, clear of the line over it, without scaling (%.1f px)" % float(w["max_dy"]))
	_check(_ft_at_rest(scene), "Big loss: it ends solid and in its place")
	scene.queue_free()
	await _settle()


## Reduced motion (the director's rule): full time is all there at once, nothing
## moves, only the sting sounds on a win.
func _test_fulltime_reduced() -> void:
	_state.set_reduced_motion(true)
	var scene := _open_fulltime([10, 5], [10, 0])
	var l: Label = scene.find_child("LadderMove", true, false)
	var want: String = _state.ladder_move_line(_state.last_pos_before)
	_check(_ft_at_rest(scene) and l != null and is_equal_approx(l.modulate.a, 1.0) and l.text == want,
			"Reduced motion: the verdict, the rows and the ladder line are all there on the first frame")
	await create_timer(1.2).timeout
	_check(_feel.moved.is_empty(), "Reduced motion: nothing moves (%s)" % str(_feel.moved))
	_check(_feel.heard.has("land"), "Reduced motion: the win's sting still sounds")
	scene.queue_free()
	await _settle()
	scene = _open_fulltime([8, 5], [13, 5])
	await create_timer(0.6).timeout
	_check(not _feel.heard.has("land") and _feel.moved.is_empty(), "Reduced motion, a loss: silent and still (%s)" % str(_feel.heard))
	scene.queue_free()
	await _settle()
	_state.set_reduced_motion(false)


## A real finger on Continue from the first frame and mid-slam, on a close win
## (the heavy slam and the shake): nothing the motion draws takes the touch.
func _test_fulltime_continue_frame1() -> void:
	var router := root.get_node("Router")
	var stack: Array = (router.get("stack") as Array).duplicate()
	router.set("stack", [])   # Back has nowhere to go: the scene stays to be checked
	var scene := _open_fulltime([10, 5], [10, 0])
	var v: Control = scene.find_child("Verdict", true, false)
	var hidden := is_equal_approx(v.modulate.a, 0.0)
	var why: String = await Tap.tap(scene.find_child("FullTimeContinue", true, false))
	_check(why == "" and hidden, "A real tap on Continue at frame 1, the verdict still to come, reaches it (%s)" % why)
	await create_timer(0.3).timeout
	var mid := v.scale.x > 1.01 or v.modulate.a < 0.99
	var why2: String = await Tap.tap(scene.find_child("FullTimeContinue", true, false))
	_check(why2 == "" and mid, "...and mid-slam (scale %.2f) it still reaches it (%s)" % [v.scale.x, why2])
	_check(not _feel.moved.has("ft_rest"), "A tap on Continue is Continue's, not a tap on the sheet (%s)" % str(_feel.moved))
	var ok := true
	for n in scene.find_child("FullTime", true, false).find_children("*", "Control", true, false):
		if n is Label and (n as Control).mouse_filter != Control.MOUSE_FILTER_IGNORE and str(n.name).begins_with("Ft"):
			ok = false
	_check(ok, "Nothing full time's motion adds takes a touch")
	scene.queue_free()
	await _settle()
	router.set("stack", stack)


## A finger on the sheet away from its buttons: the verdict's place.
func _tap_sheet(scene: Node) -> String:
	var v: Control = scene.find_child("Verdict", true, false)
	if v == null:
		return "no verdict"
	return await Tap.tap_at(v, v.size / 2.0, false)


## The skip rule on full time (director, 2026-11-26: "Already at 6th", "Plays on
## the tap"): a real tap on the sheet at its first frame puts every line in its
## last place at once, the ladder line included, and a win's sting sounds on the
## tap, once. Nothing counts, pops or slams later, even when the ladder is
## scrolled to, and the tap does not leave full time.
func _test_fulltime_tap_rest() -> void:
	var router := root.get_node("Router")
	var stack: Array = (router.get("stack") as Array).duplicate()
	router.set("stack", [])
	var scene := _open_fulltime([10, 5], [10, 0])
	var v: Control = scene.find_child("Verdict", true, false)
	var hidden := v != null and is_equal_approx(v.modulate.a, 0.0)
	var why: String = await _tap_sheet(scene)
	_check(why == "" and hidden and _feel.moved.has("ft_rest") and _ft_at_rest(scene),
			"A real tap on the sheet at frame 1, the verdict still to come, puts it all in place (%s, %s)" % [why, str(_feel.moved)])
	_check(_feel.heard.count("land") == 1, "A win: the sting sounds on the tap, once (%s)" % str(_feel.heard))
	var l: Label = scene.find_child("LadderMove", true, false)
	var want: String = _state.ladder_move_line(_state.last_pos_before)
	_check(l != null and l.text == want and is_equal_approx(l.modulate.a, 1.0),
			"The ladder line is already at its spot, solid (%s)" % (l.text if l != null else "missing"))
	var shell := _ft_shell(scene)
	_check(shell != null and is_zero_approx(shell.position.x) and is_zero_approx(float((shell.get_meta("_ft_flash", {"a": 0.0}) as Dictionary)["a"])),
			"No flash and no shake after the tap")
	await create_timer(1.6).timeout
	if l != null:
		var sc := scene.find_child("FullTime", true, false).find_children("*", "ScrollContainer", true, false)[0] as ScrollContainer
		var mid := l.get_global_rect().get_center().y
		var view := sc.get_global_rect()
		if mid < view.position.y or mid > view.end.y:
			sc.scroll_vertical += int(mid - view.get_center().y)
	await create_timer(1.0).timeout
	for beat in ["count_up", "ft_pop", "ft_slam", "ft_slam_heavy", "ft_flash", "ft_shake", "ft_snap"]:
		_check(not _feel.moved.has(beat), "After the tap, nothing plays later: no %s (%s)" % [beat, str(_feel.moved)])
	_check(_feel.heard.count("land") == 1 and l != null and l.text == want and is_equal_approx(l.modulate.a, 1.0),
			"Scrolled to, the ladder line stays put and the sting never sounds again (%s)" % str(_feel.heard))
	_check(scene.is_inside_tree() and scene.find_child("FullTimeContinue", true, false) != null,
			"The tap stays on full time; only Continue leaves")
	scene.queue_free()
	await _settle()
	router.set("stack", stack)


## The sting once (director, 2026-11-26: "Plays on the tap"): a tap after the
## impact has sounded it adds no second one, and a loss stays silent on the tap.
func _test_fulltime_tap_after_sting() -> void:
	var router := root.get_node("Router")
	var stack: Array = (router.get("stack") as Array).duplicate()
	router.set("stack", [])
	var scene := _open_fulltime([13, 5], [8, 5])
	await create_timer(0.8).timeout
	var before: int = _feel.heard.count("land")
	var why: String = await _tap_sheet(scene)
	await create_timer(0.3).timeout
	_check(before == 1 and why == "" and _feel.moved.has("ft_rest") and _feel.heard.count("land") == 1,
			"A tap after the impact's sting: no second sting (%d before, %s)" % [before, str(_feel.heard)])
	scene.queue_free()
	await _settle()
	scene = _open_fulltime([8, 5], [13, 5])
	why = await _tap_sheet(scene)
	await create_timer(1.0).timeout
	_check(why == "" and _feel.moved.has("ft_rest") and _ft_at_rest(scene) and not _feel.heard.has("land"),
			"A loss: the tap puts it in place, silent (%s, %s)" % [str(_feel.moved), str(_feel.heard)])
	scene.queue_free()
	await _settle()
	router.set("stack", stack)


## A finger that drags the sheet up is scrolling it, not tapping it; the next
## plain tap still jumps.
func _test_fulltime_drag_not_tap() -> void:
	var router := root.get_node("Router")
	var stack: Array = (router.get("stack") as Array).duplicate()
	router.set("stack", [])
	var scene := _open_fulltime([13, 5], [8, 5])
	await _settle(2)
	var v: Control = scene.find_child("Verdict", true, false)
	var sc := scene.find_child("FullTime", true, false).find_children("*", "ScrollContainer", true, false)[0] as ScrollContainer
	var bar := sc.get_v_scroll_bar()
	var room := int(bar.max_value - bar.page)
	_check(room > 20, "At phone size the sheet scrolls (%d px of room), so a drag can be told from a tap" % room)
	var touch := InputEventScreenTouch.new()
	touch.index = 0
	touch.position = Tap.pixel_point(v, v.size / 2.0)
	touch.pressed = true
	Input.parse_input_event(touch)
	Input.flush_buffered_events()
	await _settle(2)
	sc.scroll_vertical += 40   # the finger drags the sheet up
	await _settle(2)
	var lift := touch.duplicate() as InputEventScreenTouch
	lift.pressed = false
	Input.parse_input_event(lift)
	Input.flush_buffered_events()
	await _settle(2)
	_check(sc.scroll_vertical > 0 and not _feel.moved.has("ft_rest"),
			"A finger that drags the sheet scrolls it; it is not a tap (%s)" % str(_feel.moved))
	sc.scroll_vertical = 0
	await _settle(2)
	var why: String = await _tap_sheet(scene)
	_check(why == "" and _feel.moved.has("ft_rest"), "...and the next plain tap still jumps the sheet (%s)" % str(_feel.moved))
	scene.queue_free()
	await _settle()
	router.set("stack", stack)


## A legend's farewell over full time, as Review match opens it (the premiership
## suite's way): his 200th, full time built under it and waiting.
func _open_farewell_match() -> Dictionary:
	_prime(true, false)
	var res: Dictionary = _state.last_match
	var opp := str(res["away"]) if str(res["home"]) == _state.my_club else str(res["home"])
	var sq: Object = _state.my_squad()
	var mine: Array = (sq.get("ground") as Array) + (sq.get("bench") as Array)
	var man: Dictionary = mine[0]
	_state.last_pos_before = _state.my_position()
	_state.review_requested = true
	_feel.clear()
	var scene: Control = load("res://scenes/MatchScene.tscn").instantiate()
	scene.set("_farewell", {"ms": {"player": "Smith", "games": 200, "id": str(man["id"])}, "man": man,
			"opp": opp, "mine": mine, "theirs": []})
	root.add_child(scene)
	await _settle(2)
	return {"scene": scene, "fw": root.find_child("FarewellVignette", true, false)}


func _close_match(scene: Node) -> void:
	if is_instance_valid(scene):
		scene.queue_free()
	await create_timer(0.3).timeout
	var left := root.find_child("Farewell", true, false)
	if left != null:
		left.queue_free()
	await _settle()


## The skip rule on a legend's farewell (director, 2026-11-26: "Continue, holds
## at end"): a real tap on the scene at its first frame jumps to its last frame,
## him up on two teammates' shoulders, and holds there until Continue; the strip
## beside Continue is the scene's too; untouched, it plays through and holds.
func _test_farewell_tap_holds() -> void:
	var end: float = load("res://scripts/ui/match/FarewellVignette.gd").get_script_constant_map()["END"]
	var o: Dictionary = await _open_farewell_match()
	var scene: Control = o["scene"]
	var fv: Control = o["fw"]
	var cont: Control = root.find_child("FarewellContinue", true, false)
	_check(fv != null and cont != null and float(fv.get("_t")) < 0.5 and is_equal_approx(_alpha_chain(cont), 1.0),
			"A legend's farewell opens with Continue under it, solid, at its first frame")
	if fv == null or cont == null:
		await _close_match(scene)
		return
	var why: String = await Tap.tap_at(fv, fv.size / 2.0)
	_check(why == "" and _feel.moved.has("fw_rest") and is_equal_approx(float(fv.get("_t")), end) and str(fv.call("phase")) == "chaired",
			"A real tap on the scene at its first frame jumps to its last frame, him chaired off (%s, t %.2f)" % [why, float(fv.get("_t"))])
	await create_timer(0.8).timeout
	_check(is_instance_valid(fv) and bool(fv.call("is_open")) and is_equal_approx(float(fv.get("_t")), end)
			and not _feel.moved.has("fw_leave") and not _feel.moved.has("ft_slam"),
			"...and holds there: the farewell stays up, full time waits under it (%s)" % str(_feel.moved))
	why = await Tap.tap(cont)
	await create_timer(1.3).timeout
	_check(why == "" and _feel.moved.has("fw_leave") and root.find_child("FarewellVignette", true, false) == null
			and _feel.moved.has("ft_slam") and _ft_at_rest(scene),
			"Continue on the held frame: the farewell goes and the result lands (%s, %s)" % [why, str(_feel.moved)])
	await _close_match(scene)
	# The black strip round Continue is the scene's: a tap there jumps too.
	o = await _open_farewell_match()
	scene = o["scene"]
	var strip: Control = root.find_child("FarewellFooter", true, false)
	why = await Tap.tap_at(strip, Vector2(6.0, strip.size.y / 2.0)) if strip != null else "no strip"
	_check(why == "" and _feel.moved.has("fw_rest") and not _feel.moved.has("fw_leave"),
			"A tap on the strip beside Continue jumps the scene; it does not leave it (%s, %s)" % [why, str(_feel.moved)])
	await _close_match(scene)
	# Untouched: it plays through and holds on the last frame until Continue.
	o = await _open_farewell_match()
	scene = o["scene"]
	fv = o["fw"]
	await create_timer(end + 0.6).timeout
	_check(is_instance_valid(fv) and bool(fv.call("is_open")) and is_equal_approx(float(fv.get("_t")), end)
			and not _feel.moved.has("fw_rest") and not _feel.moved.has("ft_slam"),
			"Untouched, it plays through and holds on him chaired off; full time still waits (%s)" % str(_feel.moved))
	await _close_match(scene)


## Continue and Back leave a legend's farewell from its first frame (the skip
## rule); Back stays on the match and full time lands. A second finger on the
## farewell as it fades is still the farewell's, not a tap on full time under it.
func _test_farewell_back() -> void:
	var o: Dictionary = await _open_farewell_match()
	var scene: Control = o["scene"]
	var fv: Control = o["fw"]
	_check(fv != null and float(fv.get("_t")) < 0.5, "A legend's farewell is up at its first frame")
	var back: Variant = scene.call("handle_back")
	await _settle()
	_check(back == true and _feel.moved.has("fw_leave") and not _feel.moved.has("fw_rest"),
			"Back at the first frame leaves the farewell (%s)" % str(_feel.moved))
	await create_timer(1.3).timeout
	var ft: Control = scene.find_child("FullTime", true, false)
	_check(root.find_child("FarewellVignette", true, false) == null and scene.is_inside_tree() and ft != null and ft.is_visible_in_tree(),
			"...and stays on the match: the farewell gone, full time up")
	_check(_feel.moved.has("ft_slam") and _ft_at_rest(scene), "...where the result lands (%s)" % str(_feel.moved))
	await _close_match(scene)
	o = await _open_farewell_match()
	scene = o["scene"]
	fv = o["fw"]
	var why: String = await Tap.tap(root.find_child("FarewellContinue", true, false))
	_check(why == "" and _feel.moved.has("fw_leave") and not _feel.moved.has("fw_rest"),
			"A real tap on Continue at the first frame leaves the farewell; it is Continue's, not a jump (%s, %s)" % [why, str(_feel.moved)])
	var up := is_instance_valid(fv) and fv.is_inside_tree()
	var ft2: Control = scene.find_child("FullTime", true, false)
	await Tap.tap_at(ft2, ft2.size / 2.0, false)
	_check(up and not _feel.moved.has("ft_rest"),
			"A second finger on the farewell as it fades is the farewell's: full time under it does not jump (%s)" % str(_feel.moved))
	await _close_match(scene)
