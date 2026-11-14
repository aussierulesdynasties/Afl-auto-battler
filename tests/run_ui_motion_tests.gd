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
