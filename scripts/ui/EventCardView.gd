class_name EventCardView
extends RefCounted
## One story card as the coach answers it: title, text, a button per choice with
## its Gain and Cost lines under it, "See the rule" where a rule exists, and the
## outcome once answered. Shared by the hub (the week's cards) and the
## pre-season stops. `rebuild` redraws the host after an answer; `show_rule`
## opens the rule sheet. `bare`: the card without its own panel, its title
## larger, for the sheet a new card opens in over the hub (HubScene), so it is
## not a box inside a box.


static func build(index: int, narrow: bool, rebuild: Callable, show_rule: Callable, names := {}, bare := false) -> Control:
	var e: Dictionary = GameState.week_events[index]
	var card: Control = UiKit.vbox(0) if bare else UiKit.panel(UiKit.PANEL, 12)
	card.name = "WeekEvent" if index == 0 else "WeekEvent_%d" % index
	var v := UiKit.vbox(8 if bare else 6)
	card.add_child(v)
	# On the hub the card's title is a heading, so the card reads as its own
	# section above the week, not as one more line of it (T3.R9).
	var title := NameInk.label(str(e.get("title", "")), names, UiKit.TITLE if bare else UiKit.H2, UiKit.TEXT, true)
	if title is Label:
		(title as Label).autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(title)
	if not bool(e.get("resolved", false)):
		# The story itself is body copy: the coach decides on it (T3.R9; it was 12 px,
		# under the 13 px floor).
		var t := NameInk.label(str(e.get("text", "")), names, UiKit.BODY, UiKit.TEXT)
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(t)
		# What an authored stakes line adds, then what happens if he says
		# nothing, apart from the choices. Full-strength text: it is what a
		# coach decides on.
		if str(e.get("stakes", "")) != "":
			var sk := NameInk.label(str(e["stakes"]), names, UiKit.SECONDARY, UiKit.TEXT)
			sk.name = "EventStakes_%d" % index
			sk.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			v.add_child(sk)
		# What leaving it does, from the card's own data: its silent default and that
		# choice's cost, or the price of saying nothing (StoryEngine.silence_line).
		var silence := StoryEngine.silence_line(e) if bool(e.get("story", false)) else str((e.get("unanswered", {}) as Dictionary).get("hint", ""))
		if silence != "":
			var sl := NameInk.label(silence, names, UiKit.SECONDARY, UiKit.TEXT)
			sl.name = "EventSilence_%d" % index
			sl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			v.add_child(sl)
		var opts: Array = e.get("options", [])
		var row: BoxContainer = UiKit.vbox(22) if narrow else UiKit.hbox(8)
		v.add_child(row)
		for i in range(opts.size()):
			var o: Dictionary = opts[i]
			var b := UiKit.btn(str(o.get("label", "")), UiKit.NAME, false)
			b.name = "Event_%d" % i
			b.custom_minimum_size = Vector2(0, 48)
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			if not narrow:
				# Side by side, every choice gets an equal share and wraps its own words.
				b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				b.custom_minimum_size = Vector2(0, 48)
			b.pressed.connect(func():
				GameState.resolve_card(index, i)
				rebuild.call())
			# What this answer does, worded from its own effects: gains first,
			# then costs, one plain line each (a choice that does nothing
			# mechanical shows nothing under it). Same text, same weight on
			# every choice.
			var lines := StoryEngine.stakes_lines(o.get("effects", []), e.get("facts", {}))
			var rule_text := str(o.get("rule", ""))
			if lines.is_empty() and rule_text == "":
				row.add_child(b)
				continue
			var col := UiKit.vbox(3)
			col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			col.add_child(b)
			for line in lines:
				var mark := ""
				var kind := "Note"
				if line.begins_with(StoryEngine.GAIN_MARK):
					mark = "Gain:"
					kind = "Gain"
				elif line.begins_with(StoryEngine.COST_MARK):
					mark = "Cost:"
					kind = "Cost"
				var cl := NameInk.label(line.substr(mark.length()).strip_edges() if mark != "" else line, names, UiKit.SECONDARY, UiKit.TEXT)
				cl.name = "Event%s_%d_%d" % [kind, index, i]
				cl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				if mark == "":
					col.add_child(cl)
					continue
				# The marker is bold in your club's ink (STYLE-03); the sentence stays regular TEXT.
				var item := UiKit.hbox(6)
				var mk := UiKit.lbl(mark, UiKit.SECONDARY, UiKit.label_ink(), true)
				mk.name = "Event%sMark_%d_%d" % [kind, index, i]

				mk.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
				mk.autowrap_mode = TextServer.AUTOWRAP_OFF
				mk.custom_minimum_size = Vector2(40, 0)
				item.add_child(mk)
				cl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				item.add_child(cl)
				col.add_child(item)
			# The exact rule behind a line is one deliberate tap away.
			if rule_text != "":
				var more := UiKit.text_action("See the rule", UiKit.SMALL)
				more.name = "EventRule_%d" % i
				more.alignment = HORIZONTAL_ALIGNMENT_LEFT
				more.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
				more.pressed.connect(func(): show_rule.call(rule_text))
				col.add_child(more)
			row.add_child(col)
	else:
		# What the answer led to, in plain TEXT: an outcome can go either way, so
		# it never wears GOOD (T3.R9).
		var out := UiKit.lbl(str(e.get("outcome", "")), UiKit.BODY, UiKit.TEXT)
		out.name = "EventOutcome_%d" % index
		out.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(out)
	return card


## A host's rule sheet: the exact rule behind a line, closed with one tap.
static func rule_sheet(host: Control, text: String) -> void:
	if host.get_node_or_null("RuleSheet") != null:
		return
	var box := UiKit.modal_box(host, 460.0)
	(box["overlay"] as Control).name = "RuleSheet"
	var v: VBoxContainer = box["body"]
	var l := UiKit.lbl(text, 15, UiKit.TEXT)
	l.name = "RuleText"
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(l)
	var ok := UiKit.btn("Close", UiKit.NAME, true)
	ok.name = "RuleClose"
	ok.custom_minimum_size = Vector2(0, 48)
	ok.pressed.connect(func(): (box["overlay"] as Control).queue_free())
	(box["footer"] as VBoxContainer).add_child(ok)
