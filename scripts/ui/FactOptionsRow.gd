class_name FactOptionsRow
extends HFlowContainer
## The responses beside one opposition fact (FactOptions), as a short row under
## it: each its name in bold, what it does for you and what it costs; an
## unsuitable one is dimmed and disabled, its reason in the phrase's place. A
## fixed order, nothing marked best. A tap chooses that response (or lets it go
## again) and shows it chosen; it never starts the match. The hub's Play match
## button starts it, opening on the chosen call (HubScene._on_fact_option).

const MIN_W_NARROW := 130.0
const MIN_W_WIDE := 330.0


## `options` are FactOptions.options; `on_pick` gets the option's dictionary.
## `fact` is the fact's own words, which the chosen intent names.
func setup(fact_index: int, options: Array, narrow: bool, on_pick: Callable, fact := "") -> FactOptionsRow:
	name = "FactOptions_%d" % fact_index
	set_meta("fact", fact)
	add_theme_constant_override("h_separation", 5)
	add_theme_constant_override("v_separation", 5)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for o in options:
		add_child(_button(fact_index, o, narrow, on_pick))
	return self


func _button(fact_index: int, o: Dictionary, narrow: bool, on_pick: Callable) -> Control:
	var key := str(o["plan"]) if str(o["call"]) == "plan" else str(o["call"])
	var wrap := MarginContainer.new()
	wrap.name = "FactOptionWrap_%d_%s" % [fact_index, key]
	wrap.custom_minimum_size.x = MIN_W_NARROW if narrow else MIN_W_WIDE
	wrap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	# The button is the background and the tap target; the words sit over it.
	var b := UiKit.btn("", UiKit.SECONDARY)
	b.name = "FactOption_%d_%s" % [fact_index, key]
	b.custom_minimum_size.y = 44 if narrow else 36
	b.set_meta("option", o)
	var enabled := bool(o["enabled"])
	b.disabled = not enabled
	wrap.add_child(b)
	var pad := MarginContainer.new()
	pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["left", "right"]:
		pad.add_theme_constant_override("margin_" + side, 10)
	for side in ["top", "bottom"]:
		pad.add_theme_constant_override("margin_" + side, 5 if narrow else 3)
	wrap.add_child(pad)
	# The name, then what it does for you and what it costs, each sized
	# (GateOdds): on a phone and a PC alike, a column the option's width wraps.
	var col: BoxContainer = UiKit.vbox(1)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	pad.add_child(col)
	var head := UiKit.lbl(str(o["label"]), UiKit.BODY, UiKit.TEXT, true)
	head.name = "OptionName"
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(head)
	if enabled and str(o.get("gain", "")) != "":
		var up := UiKit.lbl(str(o["gain"]), UiKit.SMALL, UiKit.TEXT)
		up.name = "OptionGain"
		up.mouse_filter = Control.MOUSE_FILTER_IGNORE
		up.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		col.add_child(up)
	var sub := UiKit.lbl(str(o["cost"]) if enabled else str(o["reason"]), UiKit.SMALL, UiKit.TEXT if enabled else UiKit.MUTED)
	sub.name = "OptionSub"
	sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(sub)
	if not enabled:
		# Dimmed, not hidden: the reason still reads.
		head.modulate.a = 0.6
		sub.modulate.a = 0.8
	b.pressed.connect(func(): on_pick.call(o))
	return wrap


## Whether option `o` is the response `intent` (GameState.call_intent) holds.
static func is_chosen(o: Dictionary, intent: Dictionary) -> bool:
	return not intent.is_empty() and str(o["call"]) == str(intent.get("call", "")) \
			and str(o["plan"]) == str(intent.get("plan", "")) \
			and str(o["player_id"]) == str(intent.get("player_id", ""))


## Paint every option card under `root`: the one `intent` holds (under the fact
## `fact_text` it answers) chosen, the rest as built.
static func paint_chosen(root: Node, intent: Dictionary) -> void:
	for n in root.find_children("FactOption_*", "Button", true, false):
		var b := n as Button
		var row := b.get_parent().get_parent() as FactOptionsRow
		var on := row != null and str(row.get_meta("fact", "")) == str(intent.get("fact", "")) \
				and is_chosen(b.get_meta("option"), intent)
		if on == bool(b.get_meta("chosen", false)):
			continue
		b.set_meta("chosen", on)
		if on:
			UiKit.set_selected(b, true)
		else:
			# Back to the card as built (style_button raises a card's height to 44).
			var tall := b.custom_minimum_size.y
			UiKit.style_button(b, UiKit.SECONDARY)
			b.custom_minimum_size.y = tall
