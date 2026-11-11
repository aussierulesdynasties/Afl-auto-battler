class_name SimOrdersSheet
extends RefCounted
## The "When I sim the week" sheet (row T3.R43, P-66): every standing order on
## one sheet, each answer with what it does for you and what it costs
## (SimOrders), the one you set outlined. A tap sets the line at once and it is
## kept with the career. Opened from Coaching and from the Sim the week
## question. Look-up and set-up only; the orders act when the week is simmed.

const SHEET_NAME := "SimOrders"


## Open the sheet over the screen `from` is on. `on_close` runs when it shuts.
static func open(from: Node, on_close := Callable()) -> Control:
	var host := ClubLink.host_of(from)
	if host == null:
		return null
	close_open(host)
	var box := UiKit.modal_box(host, 520.0, 0.0)
	var overlay: Control = box["overlay"]
	overlay.name = SHEET_NAME
	UiKit.close_on_outside_tap(box)
	# However it shuts (Done, a tap outside, Back), the screen under it hears.
	if on_close.is_valid():
		overlay.tree_exited.connect(func() -> void: on_close.call_deferred())
	var v: VBoxContainer = box["body"]
	v.add_theme_constant_override("separation", 6)
	var head := UiKit.heading("When I sim the week", UiKit.H1)
	head.name = "SimOrdersTitle"
	v.add_child(head)
	var plan := UiKit.lbl("Every match starts on our game plan: %s.\nWe can change it in How we play." % CoachReport.plan_label(GameState.club_plan),
			UiKit.SMALL, UiKit.MUTED)
	plan.name = "SimOrdersPlan"
	plan.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(plan)
	for q in SimOrders.questions():
		var key := str(q["key"])
		v.add_child(UiKit.spacer(6))
		var title := UiKit.lbl(str(q["title"]), UiKit.NAME, UiKit.TEXT, true)
		title.name = "SimOrderTitle_" + key
		v.add_child(title)
		var lead := UiKit.lbl(str(q["lead"]), UiKit.SMALL, UiKit.MUTED)
		lead.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(lead)
		var group := UiKit.vbox(6)
		group.name = "SimOrderOptions_" + key
		v.add_child(group)
		for o in q["options"]:
			group.add_child(_option(key, o as Dictionary, group))
	var done := UiKit.btn("Done", UiKit.NAME, true)
	done.name = "SimOrdersDone"
	done.custom_minimum_size = Vector2(0, 48)
	done.pressed.connect(func() -> void: overlay.queue_free())
	box["footer"].add_child(done)
	return overlay


## Back closes the sheet before the screen sees it. True when it did.
static func close_open(scene: Node) -> bool:
	if scene == null:
		return false
	for c in scene.get_children():
		if c.name == SHEET_NAME and not c.is_queued_for_deletion():
			c.queue_free()
			c.name = "SimOrdersClosing"
			return true
	return false


## The lines as they stand, one short line each: "Selection: Best side on form".
static func summary() -> Array:
	var out: Array = []
	for k in SimOrders.KEYS:
		out.append("%s: %s" % [str(SimOrders.SHORT[k]), SimOrders.label(k, GameState.sim_order(k))])
	return out


## One answer: its name, then what it does for you and what it costs; a tap
## sets it (outlined).
static func _option(q: String, o: Dictionary, group: Control) -> Control:
	var key := str(o["key"])
	var wrap := MarginContainer.new()
	wrap.name = "SimOrderWrap_%s_%s" % [q, key]
	wrap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var b := UiKit.btn("", UiKit.SECONDARY)
	b.name = "SimOrder_%s_%s" % [q, key]
	b.custom_minimum_size.y = 48
	b.set_meta("key", key)
	wrap.add_child(b)
	var pad := MarginContainer.new()
	pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["left", "right"]:
		pad.add_theme_constant_override("margin_" + side, 12)
	for side in ["top", "bottom"]:
		pad.add_theme_constant_override("margin_" + side, 8)
	wrap.add_child(pad)
	var col := UiKit.vbox(2)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pad.add_child(col)
	var name_l := UiKit.lbl(str(o["label"]), UiKit.NAME, UiKit.TEXT, true)
	name_l.name = "OptionName"
	name_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(name_l)
	for part in [["Gain", "gain"], ["Cost", "cost"]]:
		var row := UiKit.hbox(6)
		row.name = "Option" + str(part[0])
		row.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var tag := UiKit.lbl(str(part[0]), UiKit.SECONDARY, UiKit.MUTED, true)
		tag.custom_minimum_size.x = 38
		tag.autowrap_mode = TextServer.AUTOWRAP_OFF
		tag.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		var words := UiKit.lbl(str(o[part[1]]), UiKit.SECONDARY, UiKit.TEXT)
		words.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		words.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		for l in [tag, words]:
			(l as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
			row.add_child(l)
		col.add_child(row)
	b.pressed.connect(func() -> void:
		GameState.set_sim_order(q, key)
		_paint(group, q))
	UiKit.set_selected(b, GameState.sim_order(q) == key)
	return wrap


static func _paint(group: Control, q: String) -> void:
	for n in group.find_children("SimOrder_*", "Button", true, false):
		UiKit.set_selected(n as Button, str((n as Button).get_meta("key", "")) == GameState.sim_order(q))
