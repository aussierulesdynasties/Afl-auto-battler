class_name TrainingScene
extends Control
## Training. Every listed player is here. XP is personal and earned every
## game; each player's training plan spends it automatically after the game.

const ROLES := ["", "DEF", "MID", "RUCK", "FWD"]
const ROLE_NOUN := {"RUCK": "ruck", "MID": "midfielder", "DEF": "defender", "FWD": "forward"}
# As Team selection names them: the positions' own short forms.
const ROLE_TABS := [["", "All"], ["DEF", "DEF"], ["MID", "MID"], ["RUCK", "RUCK"], ["FWD", "FWD"]]
const LONG_PRESS_SECONDS := 0.45

## Set by the training report: open this player's page when Training opens.
static var open_player_id := ""
var _role := ""
var _query := ""
var _built_width := 0.0
var _selected := ""
var _showing_detail := false
var _notice := ""
var _advanced := false
## The stat focus tapped but not yet locked in (row 97).
var _focus_choice := ""
var _focus_notice := ""
var _wide := false
## Long-press one player to enter group selection. Once active, ordinary
## taps add/remove players; the group picker only offers plans valid for all.
var _bulk_selected := {}
var _hold_tokens := {}
var _suppress_open := {}
var _hold_serial := 0
## Where the finger went down: a press that turns into a scroll is neither
## a tap nor a long press.
var _press_scroll := 0
var _press_pos := Vector2.ZERO
const GRID_TAB_NAMES := {"": "All", "DEF": "Def", "MID": "Mid", "RUCK": "Ruck", "FWD": "Fwd"}
const GRID_POS_NAME := {"RUCK": "Ruck", "MID": "Mid", "DEF": "Def", "FWD": "Fwd"}
const GRID_TRADE_OFF_LINE := "Each game earns XP, and what he is developing as decides the stats it buys."
const GRID_TOUCH := 48.0         # a thumb target: tabs, back, Stat guide
const CARD_PAD := 10             # inside a card, left and right
const CARD_PAD_V := 6            # inside a card, top and bottom
const CARD_BAR := 6.0            # the club's colour down a card's left edge
# The card surface carries UiKit.TINT_SHARE["card"] of the club's colour (UiKit.tinted).
const CARD_FS := 14              # position line on a card
const CARD_FS_LOW := 13          # trait and status lines on a card
const CARD_NAME_FS := 15         # every name, whatever its length; only the longest drop a size
const BAR_SLOT := 60.0           # the group bar's room, kept whether or not it is showing
const DRAG_SLOP := 12.0   # the list's scroll deadzone
var _root: VBoxContainer
var _list_scroll: ScrollContainer
var _rows: VBoxContainer
var _detail_scroll: ScrollContainer
var _overlay: Control


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.my_club == "" or GameState.my_list.is_empty():
		Router.replace("main")
		return
	# Opening it ticks the job on the Hub's weekly checklist (when on).
	WeekChecklist.mark(GameState, "training")
	if not GameState.player_names_changed.is_connected(_on_names):
		GameState.player_names_changed.connect(_on_names)
	# Your club's colour behind the page, as on the hub and match day
	# (director, 2026-10-10: every screen in the gameday style).
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	_root = UiKit.vbox(8)
	margin.add_child(_root)
	get_viewport().size_changed.connect(func():
		if is_inside_tree() and not UiKit.keyboard_resize(self, _built_width):
			_build())
	_build()
	if open_player_id != "":
		var want := open_player_id
		open_player_id = ""
		if not GameState.list_player(want).is_empty():
			_open_player(want)
	if GameState.intro_due("training"):
		GameState.set_setting("seen_training_intro", true)
		_show_intro()


## Router back hook: close the stat guide or intro, or step out of the
## player detail back to the list, before leaving Training. Returning false
## lets the router take the scene back to whatever was viewed before.
func handle_back() -> bool:
	if TrainingReportSheet.close_top(self):
		return true
	var plan_sheet := get_node_or_null("SeasonPlanSheet")
	if plan_sheet != null and is_instance_valid(plan_sheet) and not plan_sheet.is_queued_for_deletion():
		plan_sheet.queue_free()
		_build()
		return true
	if is_instance_valid(_overlay):
		if StatGuide.back(_overlay):
			return true
		_overlay.queue_free()
		_overlay = null
		return true
	if not _bulk_selected.is_empty():
		_bulk_selected.clear()
		_notice = ""
		_build()
		return true
	if _showing_detail:
		_showing_detail = false
		_build()
		return true
	return false


func _open_guide() -> void:
	if is_instance_valid(_overlay):
		_overlay.queue_free()
	_overlay = StatGuide.show(self)


## Shown once, the first time Training is opened.
func _show_intro() -> void:
	var box := UiKit.modal_box(self, 560.0, 0.0)
	_overlay = box["overlay"]
	_overlay.name = "TrainingIntro"
	UiKit.close_on_outside_tap(box)
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.heading("How training works", UiKit.TITLE))
	for line in [
		"Pick what kind of footballer each player should become. The XP he earns after every game goes on exactly that - an inside midfielder on winning the ball, a key forward on marking and goals.",
		"By position is the safe default: it trains what his position is judged on. Change it whenever you like; banked XP is spent straight away.",
		"Playing senior football develops a player fastest. Fit players you leave out develop in the reserves at about half the rate; injured and rested players barely at all.",
		"Young players with room below their potential improve quickest.",
	]:
		var l := UiKit.lbl(line, 14, UiKit.TEXT)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(l)
	var guide := UiKit.btn("Open stat guide", UiKit.NAME)
	guide.custom_minimum_size = Vector2(0, 44)
	guide.pressed.connect(func():
		_overlay.queue_free()
		_open_guide())
	box["footer"].add_child(guide)
	var ok := UiKit.btn("Got it", UiKit.NAME, true)
	ok.custom_minimum_size = Vector2(0, 44)
	ok.pressed.connect(func():
		_overlay.queue_free()
		_overlay = null)
	box["footer"].add_child(ok)


func _on_names() -> void:
	if is_inside_tree():
		_build()


func _build() -> void:
	_wide = ScreenLayout.wide_view(UiKit.view_width(self), 0.0, 760.0, false)
	_built_width = UiKit.view_width(self)
	var list_y := UiKit.scroll_place(_list_scroll) if is_instance_valid(_list_scroll) else 0
	var detail_y := UiKit.scroll_place(_detail_scroll) if is_instance_valid(_detail_scroll) else 0
	UiKit.clear(_root)
	_list_scroll = null
	_rows = null
	_detail_scroll = null
	var guide := UiKit.btn("Stat guide", UiKit.SECONDARY)
	guide.name = "StatGuideButton"
	guide.custom_minimum_size = Vector2(96, 44)
	guide.pressed.connect(_open_guide)
	# The top-bar back steps out of the player detail first, then leaves.
	var bar := UiKit.top_bar("Training", true, guide, Callable(self, "handle_back"))
	# Opaque behind the title and the button so the club's stripes never
	# show through the words, and a back and a Stat guide a thumb can hit.
	guide.custom_minimum_size = Vector2(96, GRID_TOUCH)
	var back := bar.find_child("TopBarBack", true, false) as Control
	if back != null:
		back.custom_minimum_size = Vector2(GRID_TOUCH, GRID_TOUCH)
	var backing := UiKit.panel(UiKit.PANEL, 4, UiKit.RADIUS)
	backing.name = "TrainingHeader"
	backing.add_child(bar)
	_root.add_child(backing)
	if _paged():
		# Training grid on a phone: the news, the tabs and the cards are one
		# page that scrolls as a whole (no list scrolling inside a page).
		var page := UiKit.vbox(8)
		page.add_child(_summary())
		page.add_child(_list_panel())
		_list_scroll = UiKit.scroll(page)
		_list_scroll.name = "ListScroll"
		_list_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
		_root.add_child(_list_scroll)
		if not _bulk_selected.is_empty():
			# The group bar is docked under the page: it takes room from the
			# page's foot, so no card moves when it comes and goes.
			_root.add_child(_bulk_bar())
	else:
		_root.add_child(_summary())
	if _paged():
		pass
	elif _wide:
		var body := UiKit.hbox(10)
		body.size_flags_vertical = Control.SIZE_EXPAND_FILL
		_root.add_child(body)
		body.add_child(_list_panel())
		body.add_child(_detail_panel())
	elif _showing_detail and _selected != "":
		_root.add_child(_detail_panel())
	else:
		_root.add_child(_list_panel())
	UiKit.restore_scroll(_list_scroll, list_y)
	UiKit.restore_scroll(_detail_scroll, detail_y)


## The grid on a phone with the list open: one page, one scroll.
func _paged() -> bool:
	return not _wide and not (_showing_detail and _selected != "")


## The training gear beside the week's news (director, 2026-10-14: "Bigger,
## in real colours"): a blue tackle bag with a stack of orange cones, in its
## own colours. It may not push the list down or squeeze the news, so on a
## phone it is as tall as the news it stands beside and no wider than before;
## on a wide screen it leads the news from the left.
const HERO_NARROW := 72.0
const HERO_WIDE := 96.0


func _summary() -> Control:
	var panel := UiKit.panel(UiKit.PANEL, 10, 8)
	var v := UiKit.vbox(3)
	# Training grid on a phone with the list open: the news in a line or two,
	# no picture and no standing explanation, so the cards get the screen.
	var compact := not _wide and not (_showing_detail and _selected != "")
	# Decoration: it stands on the panel's foot at the right and takes no tap.
	# Without the picture the news has the whole width, as before.
	var hero := UiArt.view("training_gear", HERO_WIDE if _wide else HERO_NARROW) if not compact else null
	if hero == null:
		panel.add_child(v)
	else:
		hero.name = "TrainingHero"
		hero.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var h := UiKit.hbox(14 if _wide else 12)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		v.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		if _wide:
			h.add_child(hero)
			h.add_child(v)
		else:
			h.add_child(v)
			h.add_child(hero)
		panel.add_child(h)
	var report: Dictionary = GameState.last_training_report
	if int(report.get("count", 0)) > 0:
		v.add_child(UiKit.lbl(str(report.get("label", "Last game")), 15, UiKit.EMPH, true))
		var line := GameState.training_summary_line()
		var what: Control
		if line != "":
			what = _news_line(line)
		else:
			what = UiKit.lbl("Training: no rating changes from the last game.", UiKit.SECONDARY, UiKit.MUTED)
			what.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		what.name = "TrainingNews"
		v.add_child(what)
		var rises := GameState.training_rise_lines()
		if not rises.is_empty():
			v.add_child(_rise_list(rises))
		var month := TrainingReportSheet.link(self, _open_player)
		if month != null:
			v.add_child(month)
		else:
			var reserves := GameState.reserves_summary_line()
			if reserves != "":
				v.add_child(UiKit.lbl(reserves, UiKit.SECONDARY, UiKit.MUTED))
	# The season plan in words, one tap from the season line.
	var plan_line := SeasonPlanSheet.line(self, func(): _build())
	if int(report.get("count", 0)) <= 0 and not (compact and plan_line != null):
		v.add_child(UiKit.lbl("No game played yet. Players develop after every match.", UiKit.BODY, UiKit.EMPH, true))
	if plan_line != null:
		if compact:
			_plan_as_button(plan_line as Button)
		v.add_child(plan_line)
	# What it costs and what it buys, in one line (P-63). The compact phone
	# list leaves it to the intro and the player's page.
	if not compact:
		var trade := UiKit.lbl(GRID_TRADE_OFF_LINE, UiKit.SMALL, UiKit.TEXT)
		trade.name = "TrainingTradeOff"
		trade.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(trade)
	return panel


## This player's plans as taps: Position plan, his roles' archetypes,
## then positions he could learn. The chosen one is outlined.
func _plan_picker(p: Dictionary, on_pick: Callable) -> Control:
	# A dual-role player's Position plan trains his first role: say which.
	var first := str(p.get("role", ""))
	var dual := str(p.get("role2", "")) != "" and str(p.get("role2", "")) != first
	var options := []
	for key in GameState.plans_for(p):
		var label := GameState.train_plan_label(key)
		if key == "position" and dual:
			label = "By position (%s)" % PlayerProfile.role_word(first).to_lower()
		elif key.begins_with(GameState.LEARN_PREFIX):
			label = "Learn " + str(GameState.LEARN_JOBS[key.trim_prefix(GameState.LEARN_PREFIX)]["word"])
		options.append([key, label])
	return UiKit.choice_grid("PlayerPlan", options, GameState.plan_for(p), 2, on_pick)


func _spend_notice(gains: Dictionary, ov_before: int, ov_after: int) -> String:
	if ov_after > ov_before:
		return "Development changed. Banked XP lifted him from %d to %d." % [ov_before, ov_after]
	if not gains.is_empty():
		return "Development changed. Banked XP went straight into it."
	return "Development changed. It takes effect after the next game."


## The season plan row as a button: outlined, a thumb tall, its second line in
## the text colour (it is a choice the coach makes, not small print).
func _plan_as_button(b: Button) -> void:
	b.flat = false
	_outline(b)
	b.custom_minimum_size.y = GRID_TOUCH + 8
	var inner := b.get_child(0) as Control
	if inner != null:
		inner.offset_left = 12
		inner.offset_right = -12
	var sub := b.find_child("SeasonPlanSub", true, false) as Label
	if sub != null:
		sub.add_theme_color_override("font_color", _soft())


## Helper text and quiet tabs that still read: between the muted grey and the
## text colour, nearer the text.
static func _soft() -> Color:
	return UiKit.MUTED.lerp(UiKit.TEXT, 0.7)


func _list_panel() -> Control:
	var panel := UiKit.panel(UiKit.PANEL, 10, 8)
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var paged := _paged()
	panel.size_flags_vertical = Control.SIZE_SHRINK_BEGIN if paged else Control.SIZE_EXPAND_FILL
	if _wide:
		panel.custom_minimum_size.x = 280
	var v := UiKit.vbox(6)
	panel.add_child(v)
	var tabs := UiKit.hbox(2)
	tabs.name = "RoleTabs"
	v.add_child(tabs)
	for item in ROLE_TABS:
		var key := str(item[0])
		# Grid: sentence-case names, a thumb tall.
		var b := UiKit.tab(str(GRID_TAB_NAMES[key]), _role == key)
		_strengthen_tab(b, _role == key)
		b.pressed.connect(_set_role.bind(key))
		tabs.add_child(b)
	var search := UiKit.search_field(_query)
	search.text_changed.connect(func(text: String):
		_query = text
		_refresh_rows())
	v.add_child(search)
	if paged:
		var hint := UiKit.lbl(("Touch and hold a player to pick several." if UiKit.view_width(self) < 600.0
				else "Press and hold a player to pick several.") if _bulk_selected.is_empty()
				else "Tap a player to add him or take him out.", UiKit.SECONDARY, _soft())
		hint.name = "GroupHint"
		v.add_child(hint)
	else:
		# One slot for the hint and for the group bar: choosing players swaps
		# one for the other and the cards stay where they are.
		var slot := UiKit.vbox(0)
		slot.name = "GroupSlot"
		slot.custom_minimum_size.y = BAR_SLOT
		slot.alignment = BoxContainer.ALIGNMENT_CENTER
		v.add_child(slot)
		if _bulk_selected.is_empty():
			var hint := UiKit.lbl("Touch and hold a player to pick several." if UiKit.view_width(self) < 600.0
					else "Press and hold a player to pick several.", UiKit.SECONDARY, _soft())
			hint.name = "GroupHint"
			slot.add_child(hint)
		else:
			slot.add_child(_bulk_bar())
	var rows := UiKit.vbox(4)
	rows.name = "TrainingRows"
	_rows = rows
	if paged:
		v.add_child(rows)
	else:
		_list_scroll = UiKit.scroll(rows)
		_list_scroll.name = "ListScroll"
		v.add_child(_list_scroll)
	_fill_rows(rows)
	return panel


## A role tab a thumb tall, its words readable when it is not the chosen one
## and a firmer rule under the one that is.
static func _strengthen_tab(b: Button, active: bool) -> void:
	b.custom_minimum_size.y = GRID_TOUCH
	b.add_theme_color_override("font_color", UiKit.TEXT if active else _soft())
	if active:
		for state_name in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
			var sb := b.get_theme_stylebox(state_name).duplicate() as StyleBoxFlat
			sb.border_width_bottom = 4
			b.add_theme_stylebox_override(state_name, sb)


func _set_role(role: String) -> void:
	_role = role
	_build()


## Grid: the group bar on one row. The count, one outlined button per plan he
## can all take, Clear; it wraps only if the plans do not fit across.
func _bulk_bar() -> Control:
	var panel := UiKit.panel(UiKit.PANEL_ALT, 6, 6)
	panel.name = "BulkTraining"
	var v := UiKit.vbox(4)
	panel.add_child(v)
	panel.custom_minimum_size.y = BAR_SLOT
	var flow := HFlowContainer.new()
	flow.name = "BulkRow"
	flow.add_theme_constant_override("h_separation", 4)
	flow.add_theme_constant_override("v_separation", 4)
	v.add_child(flow)
	var count := _bulk_selected.size()
	var head := UiKit.line("%d selected" % count, UiKit.SECONDARY, UiKit.TEXT, true)
	head.custom_minimum_size = Vector2(0, GRID_TOUCH)
	head.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	flow.add_child(head)
	for key in _bulk_plans():
		var b := UiKit.btn(_group_button_word(str(key)), UiKit.SECONDARY)
		b.name = "GroupPlan_%s" % str(key)
		b.custom_minimum_size.y = GRID_TOUCH
		_outline(b, 5)
		b.pressed.connect(_apply_bulk_plan.bind(str(key)))
		flow.add_child(b)
	var clear := UiKit.btn("Clear", UiKit.SECONDARY)
	clear.name = "ClearBulk"
	clear.custom_minimum_size.y = GRID_TOUCH
	_outline(clear, 5)
	clear.pressed.connect(func():
		_bulk_selected.clear()
		_notice = ""
		_build())
	flow.add_child(clear)
	if _notice != "":
		var note := UiKit.lbl(_notice, UiKit.SECONDARY, UiKit.GOOD)
		note.name = "BulkNotice"
		note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(note)
	return panel


## What a group button says: "By position" as it is; a role plan as the job
## it is, "Train as ruck", so it cannot be read as "set them to Ruck".
func _group_button_word(key: String) -> String:
	var label := GameState.train_plan_label(key)
	if key == "position":
		return label
	return "Train as %s" % label.to_lower()


## A secondary button that reads as a button on a dark panel: an outline, no
## fill.
static func _outline(b: Button, margin := 8) -> void:
	var rest := UiKit.style(Color.TRANSPARENT, margin, UiKit.RADIUS, UiKit.MUTED)
	var down := UiKit.style(UiKit.SURFACE, margin, UiKit.RADIUS, UiKit.TEXT)
	b.add_theme_stylebox_override("normal", rest)
	b.add_theme_stylebox_override("focus", rest)
	for state in ["hover", "pressed", "hover_pressed"]:
		b.add_theme_stylebox_override(state, down)


func _bulk_plans() -> Array:
	var ids: Array = _bulk_selected.keys()
	if ids.is_empty():
		return []
	var first := GameState.list_player(str(ids[0]))
	if first.is_empty():
		return []
	var common: Array = GameState.plans_for(first).duplicate()
	for raw_id in ids.slice(1):
		var p := GameState.list_player(str(raw_id))
		if p.is_empty():
			continue
		var valid: Array = GameState.plans_for(p)
		common = common.filter(func(key): return valid.has(key))
	return common


func _apply_bulk_plan(key: String) -> void:
	var changed := 0
	var spent := 0
	for raw_id in _bulk_selected.keys():
		var id := str(raw_id)
		var p := GameState.list_player(id)
		if p.is_empty() or not GameState.plan_valid_for(p, key):
			continue
		var before_xp := int(p.get("xp", 0))
		GameState.set_player_plan(id, key)
		spent += maxi(0, before_xp - int(GameState.list_player(id).get("xp", 0)))
		changed += 1
	var label := GameState.train_plan_label(key)
	_notice = "%s applied to %d %s." % [label, changed, "player" if changed == 1 else "players"]
	if spent > 0:
		_notice += " Banked XP was spent under the new focus."
	if is_inside_tree():
		_build()


func _toggle_bulk(id: String) -> void:
	if _bulk_selected.has(id):
		_bulk_selected.erase(id)
	else:
		_bulk_selected[id] = true
	_showing_detail = false
	_notice = ""
	if is_inside_tree():
		_build()


## The held button may be rebuilt as soon as the long press fires. A
## suppression flag prevents its eventual pressed signal from immediately
## undoing the selection; the next fresh button-down clears that flag.
func _begin_player_hold(id: String) -> void:
	_suppress_open.erase(id)
	_hold_serial += 1
	var token := _hold_serial
	_hold_tokens[id] = token
	_press_scroll = _list_scroll.scroll_vertical if is_instance_valid(_list_scroll) else 0
	_press_pos = get_global_mouse_position()
	await get_tree().create_timer(LONG_PRESS_SECONDS).timeout
	if int(_hold_tokens.get(id, -1)) != token:
		return
	_hold_tokens.erase(id)
	if _moved_since_press():
		return
	_suppress_open[id] = true
	_toggle_bulk(id)


func _end_player_hold(id: String) -> void:
	_hold_tokens.erase(id)


func _press_player(id: String) -> void:
	# The press that opened his profile also reaches the row under it.
	var tap := find_child("Profile_" + id, true, false)
	if tap is Control and (tap as Control).is_visible_in_tree() and (tap as Control).get_global_rect().has_point(get_global_mouse_position()):
		return
	if _suppress_open.has(id):
		_suppress_open.erase(id)
		return
	if _moved_since_press():
		return
	if not _bulk_selected.is_empty():
		_toggle_bulk(id)
		return
	_open_player(id)


## The list scrolled, or the finger travelled, since it went down.
func _moved_since_press() -> bool:
	if is_instance_valid(_list_scroll) and absi(_list_scroll.scroll_vertical - _press_scroll) > 2:
		return true
	return get_global_mouse_position().distance_to(_press_pos) > DRAG_SLOP


func _refresh_rows() -> void:
	if not is_instance_valid(_rows):
		_build()
		return
	_fill_rows(_rows)


func _fill_rows(rows: Node) -> void:
	UiKit.clear(rows)
	var shown := 0
	for role in ["RUCK", "MID", "DEF", "FWD"]:
		if _role != "" and _role != role:
			continue
		var group: Array = []
		for p in GameState.my_list:
			# All: each player once, under his own position. A position tab:
			# everyone who can play there (Ratings.plays_role, the rule the
			# draft and selection use), so a MID/FWD is in both.
			if _role == "" and str(p.get("role", "")) != role:
				continue
			if _role != "" and not Ratings.plays_role(p, role):
				continue
			if not _matches(p):
				continue
			group.append(p)
		if group.is_empty():
			continue
		group.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
		# A plain heading in the text colour: position is not a state, so
		# no green or gold here.
		var head := UiKit.lbl("%s (%d)" % [UiKit.ROLE_LABEL[role], group.size()], UiKit.SECONDARY + 1, UiKit.TEXT, true)
		head.name = "GroupHead"
		var air := Control.new()
		air.name = "GroupAir"
		air.custom_minimum_size.y = 6
		air.mouse_filter = Control.MOUSE_FILTER_IGNORE
		rows.add_child(air)
		rows.add_child(head)
		var grid := UiKit.vbox(6)
		grid.name = "TrainingGrid"
		rows.add_child(grid)
		# Two across; an odd one out keeps a half-width card at the left and
		# its row leaves the other half empty, so every card is one width.
		for i in range(0, group.size(), 2):
			var pair: Array = group.slice(i, i + 2)
			var line := UiKit.hbox(6)
			line.name = "GridRow"
			grid.add_child(line)
			for p in pair:
				line.add_child(_player_card(p))
				shown += 1
			if pair.size() == 1:
				var hole := Control.new()
				hole.name = "GridHole"
				hole.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				hole.mouse_filter = Control.MOUSE_FILTER_IGNORE
				line.add_child(hole)
	if shown == 0:
		rows.add_child(UiKit.lbl("No players match.", UiKit.NAME, UiKit.TEXT, true))


func _matches(p: Dictionary) -> bool:
	var q := _query.strip_edges().to_lower()
	if q == "":
		return true
	return GameDB.player_search_text(p).to_lower().contains(q)


## Training grid: player cards, two across, every one
## the same width and height. Top to bottom: his position and rating, his name
## (two lines at most, one size), his best trait, then where he is in his
## development, which is always the bottom line, so statuses sit level across
## a row whatever the names above them do. The club's colour tints the card and
## runs down its left edge. A tap on the card selects him, a
## long press starts a group (the chosen ones carry a tick), and his
## profile is one more tap away from his plan page.
func _player_card(p: Dictionary) -> Control:
	var id := str(p["id"])
	var in_group := _bulk_selected.has(id)
	var selected := in_group or (_bulk_selected.is_empty() and id == _selected)
	var card := UiKit.panel(UiKit.PANEL_ALT, 0, UiKit.RADIUS)
	card.add_theme_stylebox_override("panel", _card_style(selected, UiKit.club_ink(GameState.my_club)))
	card.name = "Card_" + id
	card.custom_minimum_size.y = _card_height()
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card.size_flags_vertical = Control.SIZE_FILL
	var text_w := _card_text_width()
	var line_h := _card_line_h()
	var row := UiKit.hbox(0)
	card.add_child(row)
	var bar := ColorRect.new()
	bar.name = "ClubBar"
	bar.color = UiKit.club_ink(GameState.my_club)
	bar.custom_minimum_size = Vector2(CARD_BAR, 0)
	row.add_child(bar)
	var pad := MarginContainer.new()
	pad.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pad.add_theme_constant_override("margin_left", CARD_PAD)
	pad.add_theme_constant_override("margin_right", CARD_PAD)
	pad.add_theme_constant_override("margin_top", CARD_PAD_V)
	pad.add_theme_constant_override("margin_bottom", CARD_PAD_V)
	row.add_child(pad)
	var v := UiKit.vbox(0)
	pad.add_child(v)
	# Row 1: where he plays, and his rating.
	var top := UiKit.hbox(4)
	top.custom_minimum_size.y = 22
	v.add_child(top)
	if in_group:
		var tick := _Tick.new()
		tick.name = "Ticked"
		top.add_child(tick)
	var pos := UiKit.line(_card_position(p), CARD_FS, UiKit.TEXT)
	pos.name = "Position"
	pos.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pos.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	top.add_child(pos)
	var rise := _last_rise(id)
	var ovr_word := UiKit.line("OVR", CARD_FS, UiKit.MUTED)
	ovr_word.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	top.add_child(ovr_word)
	var ovr := UiKit.line(("▲ " if rise.size() > 0 else "") + str(int(p["overall"])), UiKit.NAME,
			UiKit.GOOD if rise.size() > 0 else UiKit.TEXT, true)
	ovr.name = "Rating"
	ovr.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	top.add_child(ovr)
	# Middle: his name, and his trait under it, centred in the room between the
	# top row and the status, so a short name does not leave a hole.
	var mid := UiKit.vbox(2)
	mid.name = "CardMiddle"
	mid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	mid.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(mid)
	var full_name := GameDB.player_display_name(p)
	var fitted := _fit_name(full_name, text_w)
	var nm := UiKit.name_label(str(fitted[0]), int(fitted[1]))
	nm.tooltip_text = full_name
	mid.add_child(nm)
	var trait_keys := Traits.of(p)
	if not trait_keys.is_empty():
		var tr := UiKit.ellipsis(UiKit.trait_label(trait_keys[0]), CARD_FS_LOW,
				UiKit.BAD if Traits.is_bad(trait_keys[0]) else UiKit.TEXT, true)
		tr.name = "Trait"
		mid.add_child(tr)
	# Bottom: one status line, always last, in a lighter weight than the trait.
	var status := _card_status(p, id, text_w)
	var st := UiKit.ellipsis(str(status[0]), CARD_FS_LOW, status[1])
	st.name = "Status"
	st.custom_minimum_size.y = line_h
	st.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	v.add_child(st)
	_ignore_mouse(row)
	var b := UiKit.btn("", 14)
	b.name = "Trainee_" + id
	b.set_anchors_preset(Control.PRESET_FULL_RECT)
	var clear := UiKit.style(Color.TRANSPARENT, 0, UiKit.RADIUS)
	clear.set_border_width_all(0)
	for state_name in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		b.add_theme_stylebox_override(state_name, clear)
	b.button_down.connect(_begin_player_hold.bind(id))
	b.button_up.connect(_end_player_hold.bind(id))
	b.pressed.connect(_press_player.bind(id))
	card.add_child(b)
	return card


## A tick in a light disc: the mark of a player picked for the group.
class _Tick extends Control:
	func _init() -> void:
		custom_minimum_size = Vector2(20, 20)
		size_flags_vertical = Control.SIZE_SHRINK_CENTER
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		draw_circle(size * 0.5, 10.0, UiKit.TEXT)
		draw_polyline(PackedVector2Array([Vector2(5.5, 10.5), Vector2(8.8, 13.8), Vector2(14.5, 6.8)]),
				UiKit.PANEL_ALT, 2.4, true)


## The card's surface: the club's colour tinted into the card, square on the
## left where the club's bar sits; the chosen one is outlined in the text colour.
static func _card_style(selected: bool, club: Color) -> StyleBoxFlat:
	var surface := UiKit.tinted("card", club)
	var sb := UiKit.style(surface, 0, UiKit.RADIUS, UiKit.TEXT if selected else surface)
	sb.set_border_width_all(2 if selected else 0)
	sb.corner_radius_top_left = 0
	sb.corner_radius_bottom_left = 0
	return sb


## One line of card text, with its breathing room.
static func _card_line_h() -> float:
	return ceilf(UiKit.FONT.get_height(UiKit.px(CARD_FS_LOW))) + 1.0


## The same for every card: the room the fullest one needs (two lines of name,
## a trait, a status, and the top row), so no row differs from another.
static func _card_height() -> float:
	# Two lines of the label, with the gap the label puts between them.
	var name_h := ceilf(UiKit.BOLD.get_height(UiKit.px(CARD_NAME_FS))) * 2.0 + 4.0
	return ceilf(2.0 * CARD_PAD_V + UiKit.px(22) + name_h + 2.0 + _card_line_h() + _card_line_h())


## How wide a card's words can run: the page less its margins and the list
## panel's padding, shared between the two cards, less the bar and the padding.
func _card_text_width() -> float:
	var row := UiKit.view_width(self) - 24.0 - 20.0
	if _wide:
		row = maxf(260.0, (UiKit.view_width(self) - 34.0) * 0.5 - 30.0)
	var card := (row - 6.0) * 0.5
	return card - CARD_BAR - 2.0 * CARD_PAD


## "Mid +1": his own position, then how many more he can play. The full list
## is on his profile.
static func _card_position(p: Dictionary) -> String:
	var tags := Ratings.role_tag(p).split("/")
	var text: String = GRID_POS_NAME.get(tags[0], str(tags[0]).capitalize())
	if tags.size() > 1:
		text += " +%d" % (tags.size() - 1)
	return text


## [text, colour] for the status line: an injury first; otherwise where he is
## in the match-day squad and what he is training as, as much as fits.
func _card_status(p: Dictionary, id: String, width: float) -> Array:
	if int(p.get("injury_weeks", 0)) > 0:
		var wks := int(p["injury_weeks"])
		return ["Injured %d wk%s" % [wks, "" if wks == 1 else "s"], UiKit.BAD]
	var plan := GameState.plan_for(p)
	var texts: Array = []
	if plan == "position":
		texts.append(GameState.development_state(p).replace(" projected peak", " peak"))
	elif plan.begins_with(GameState.LEARN_PREFIX):
		var word := str(GameState.LEARN_JOBS[plan.trim_prefix(GameState.LEARN_PREFIX)]["word"])
		texts.append("Learning to play %s" % word)
		texts.append("Learning %s" % word)
	else:
		var label := GameState.train_plan_label(plan)
		texts.append("Training: %s" % label.to_lower())
		texts.append("Training: %s" % label.to_lower().split(" ")[-1])
		texts.append(label)
	var duty := str({"Interchange": "Bench", "Reserves": "Reserves", "Not selected": "Omitted"}.get(GameState.last_duty(id), ""))
	var options: Array = []
	if duty != "":
		for t in texts:
			options.append("%s · %s" % [duty, t])
		options.append(duty)
	options.append_array(texts)
	for o in options:
		if UiKit.FONT.get_string_size(str(o), HORIZONTAL_ALIGNMENT_LEFT, -1, UiKit.px(CARD_FS_LOW)).x <= width:
			return [o, _soft()]
	return [options.back(), _soft()]


## [name, size]: the whole name at the largest size that keeps it to two
## lines with no word cut; else his first names as initials; else the smallest
## size, where the label's own trim is the last resort.
static func _fit_name(text: String, width: float) -> Array:
	var sizes := [CARD_NAME_FS, 14, 13]
	var tries := [text]
	var parts := text.split(" ")
	if parts.size() > 1:
		var short := ""
		for i in range(parts.size() - 1):
			short += parts[i].substr(0, 1) + ". "
		tries.append(short + parts[parts.size() - 1])
	for t in tries:
		for fs in sizes:
			var size := UiKit.BOLD.get_multiline_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, width, UiKit.px(fs))
			if size.x <= width + 0.5 and size.y <= UiKit.BOLD.get_height(UiKit.px(fs)) * 2.0 + 1.0:
				return [t, fs]
	return [tries.back(), 13]


## His name at the head of the plan: tap it for his profile.
func _name_header(p: Dictionary) -> Control:
	var b := UiKit.btn(GameDB.player_display_name(p) + "  ›", 20)
	b.name = "PlayerNameLink"
	b.flat = true
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	for state in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		var flat := UiKit.style(Color.TRANSPARENT, 0, 0)
		flat.set_border_width_all(0)
		flat.content_margin_top = 6
		flat.content_margin_bottom = 6
		b.add_theme_stylebox_override(state, flat)
	b.clip_text = true
	b.custom_minimum_size.y = 44
	b.add_theme_color_override("font_color", UiKit.TEXT)
	b.pressed.connect(func(): NameLink.open(self, str(p["id"])))
	return b


## The last game's training news with each name a tap to his profile.
func _news_line(line: String) -> Control:
	var ids := {}
	for q in GameState.my_list:
		ids[GameDB.player_display_name(q)] = str(q["id"])
	return TraitLink.line(line, UiKit.SECONDARY, UiKit.GOOD, ids)


## Everyone who rose, one "Name 76 to 77" each, as many to a row as fit, so
## a long list stays short; each name a tap to his profile.
func _rise_list(lines: PackedStringArray) -> Control:
	var ids := {}
	for q in GameState.my_list:
		ids[GameDB.player_display_name(q)] = str(q["id"])
	# A flow of equal cells: as many to a row as the width holds (one on a
	# phone, so "74 to 76" never breaks; three on a PC), the columns aligned.
	var grid := HFlowContainer.new()
	grid.name = "TrainingRises"
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 2)
	for l in lines:
		var r := NameLink.line(l, ids, UiKit.SECONDARY, UiKit.GOOD)
		r.custom_minimum_size = Vector2(220, 0)
		grid.add_child(r)
	return grid


## [from, to] if training lifted his OVR after the last game, else [].
func _last_rise(id: String) -> Array:
	for r in (GameState.last_training_report.get("auto", {}) as Dictionary).get("rises", []):
		if str(r[0]) == id:
			return [int(r[1]), int(r[2])]
	return []


## A full senior game at this career's difficulty, to set the reserves
## figure against.
func _senior_game_xp() -> int:
	return GameState.XP_SENIOR_GAME


func _open_player(id: String) -> void:
	_selected = id
	_showing_detail = true
	_notice = ""
	_advanced = false
	_focus_choice = ""
	_focus_notice = ""
	_build()


func _detail_panel() -> Control:
	var panel := UiKit.panel(UiKit.PANEL, 10, 8)
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	panel.custom_minimum_size.x = 280
	var outer := UiKit.vbox(6)
	panel.add_child(outer)
	var p := GameState.list_player(_selected)
	if p.is_empty() and _wide and not GameState.my_list.is_empty():
		# A wide screen opens your best player rather than an empty panel
		# (director, 2026-10-10: no empty space on a PC).
		var best: Dictionary = GameState.my_list[0]
		for q in GameState.my_list:
			if int(q.get("overall", 0)) > int(best.get("overall", 0)):
				best = q
		_selected = str(best["id"])
		p = best
	if p.is_empty():
		outer.add_child(UiKit.lbl("Choose a player from the list.", UiKit.NAME, UiKit.TEXT, true))
		outer.add_child(UiKit.lbl("Open a player to choose what kind of footballer he develops into.", UiKit.SECONDARY, UiKit.MUTED))
		return panel
	if not _wide:
		var back := UiKit.btn("‹ All players", UiKit.BODY)
		back.pressed.connect(func():
			_showing_detail = false
			_build())
		outer.add_child(back)
	var body := UiKit.vbox(6)
	_detail_scroll = UiKit.scroll(body)
	_detail_scroll.name = "DetailScroll"
	outer.add_child(_detail_scroll)
	# Who he is and where he stands.
	body.add_child(_name_header(p))
	var duty := GameState.last_duty(_selected)
	body.add_child(UiKit.lbl("%s  ·  %s" % [Ratings.role_tag(p), duty if duty != "" else "Not yet played"],
			13, UiKit.MUTED))
	var standing := UiKit.hbox(10)
	body.add_child(standing)
	standing.add_child(UiKit.line("OVR %d" % int(p["overall"]), 22, UiKit.EMPH, true))
	var rise := _last_rise(_selected)
	var state := GameState.development_state(p)
	var state_l := UiKit.lbl(state + ("  ·  up from %d last game" % int(rise[0]) if rise.size() > 0 else ""), 14,
			UiKit.GOOD if rise.size() > 0 else UiKit.TEXT)
	state_l.name = "DevState"
	state_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	state_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	standing.add_child(state_l)
	if not Traits.of(p).is_empty():
		body.add_child(UiKit.trait_chips(p))
	# The decision: what kind of footballer he becomes.
	var focus := UiKit.panel(UiKit.PANEL_ALT, 10, 8)
	body.add_child(focus)
	var fv := UiKit.vbox(4)
	focus.add_child(fv)
	fv.add_child(UiKit.lbl("Development focus", 12, UiKit.MUTED, true))
	var plan := GameState.plan_for(p)
	var plan_name := UiKit.lbl(GameState.train_plan_label(plan), UiKit.HEADING, UiKit.EMPH, true)
	plan_name.name = "FocusName"
	fv.add_child(plan_name)
	var meaning := UiKit.lbl(GameState.train_plan_description(plan, str(p.get("role", "MID"))), 13, UiKit.TEXT)
	meaning.name = "FocusMeaning"
	meaning.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fv.add_child(meaning)
	var progress := _project_line(p)
	if progress != "":
		var pl := UiKit.lbl(progress, UiKit.SECONDARY, UiKit.TEXT, true)
		pl.name = "ProjectProgress"
		pl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		fv.add_child(pl)
	var working := _working_on(p)
	if working != "":
		fv.add_child(UiKit.lbl("Working on: " + working, 12, UiKit.MUTED))
	var pid := _selected
	var pick := _plan_picker(p, func(key: String):
		var q := GameState.list_player(pid)
		var before := int(q.get("overall", 0))
		var gains := GameState.set_player_plan(pid, key)
		_notice = _spend_notice(gains, before, int(GameState.list_player(pid).get("overall", 0)))
		_build())
	fv.add_child(pick)
	if _notice != "":
		fv.add_child(UiKit.lbl(_notice, UiKit.SECONDARY, UiKit.GOOD, true))
	body.add_child(_stat_focus_panel(p))
	# What is close, and what happened.
	var close: Array = Traits.near(p)
	if not close.is_empty():
		var n: Dictionary = close[0]
		# "4 more durability and he's an Engine: tires 25% slower."
		var t_text := Traits.text(str(n["key"]))
		var hint := UiKit.lbl("%d more %s and he's %s %s: %s" % [int(n["gap"]), GameState.train_stat_label(str(n["stat"])).to_lower(),
				"an" if "AEIOU".contains(Traits.label(str(n["key"])).left(1)) else "a", Traits.label(str(n["key"])),
				t_text.left(1).to_lower() + t_text.substr(1)], 12, UiKit.EMPH)
		hint.name = "TraitHint"
		hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		TraitLink.tappable(hint, str(n["key"]))
		body.add_child(hint)
	if duty == "Reserves":
		var res_line := UiKit.lbl("Developing in the reserves: +%d XP last game (a senior game is worth up to %d)." % [
				GameState.xp_gain_for(_selected), _senior_game_xp()], 13, UiKit.MUTED)
		res_line.name = "ReservesLine"
		res_line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		body.add_child(res_line)
	# Everything else sits behind one button.
	var adv := UiKit.btn("Hide stats" if _advanced else "Stats", 13)
	adv.name = "AdvancedToggle"
	adv.custom_minimum_size = Vector2(0, 44)
	adv.pressed.connect(func():
		_advanced = not _advanced
		_build())
	body.add_child(adv)
	if _advanced:
		var pot := UiKit.lbl("Potential %d  ·  %s" % [int(p.get("potential", p["overall"])), _potential_note(p)],
				12, UiKit.MUTED)
		pot.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		body.add_child(pot)
		var background := _background_line(p)
		if background != "":
			var bl := UiKit.lbl(background, 12, UiKit.MUTED)
			bl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			body.add_child(bl)
		var rows := []
		for row in GameState.TRAIN_STATS:
			rows.append([str(row[0]), str(row[1]), GameState.stat_useful_for(p, str(row[0]))])
		rows.sort_custom(func(a, b): return bool(a[2]) and not bool(b[2]))
		for r in rows:
			body.add_child(_stat_row(p, str(r[0]), str(r[1]), bool(r[2])))
	return panel


## One stat a season gets extra work (row 97, director 2026-11-06: "one stat
## focus per player per season, drills do the rest"). Tap a stat, then lock it
## in; it stays until the next season opens.
func _stat_focus_panel(p: Dictionary) -> Control:
	var box := UiKit.panel(UiKit.PANEL_ALT, 10, 8)
	box.name = "StatFocus"
	var v := UiKit.vbox(6)
	box.add_child(v)
	var year := GameState.season_year
	v.add_child(UiKit.lbl("Stat focus  ·  %d season" % year, 12, UiKit.MUTED, true))
	var current := GameState.stat_focus(p)
	if GameState.project_job(p) != "" and GameState.plan_for(p) == GameState.LEARN_PREFIX + GameState.project_job(p):
		var hold := UiKit.lbl("On hold while he learns a position: all his training goes into the new role.", 13, UiKit.TEXT)
		hold.name = "StatFocusHold"
		hold.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(hold)
		return box
	var attr: Dictionary = p.get("attr", {})
	if GameState.focus_locked(p) and current != "":
		var name_l := UiKit.lbl("%s  %d" % [GameState.train_stat_label(current), int(attr.get(current, 0))],
				UiKit.HEADING, UiKit.EMPH, true)
		name_l.name = "StatFocusName"
		v.add_child(name_l)
		var locked := UiKit.lbl("Locked in for %d. About a third of his training goes into %s; his development drills get the rest. You can change it when the %d season opens." % [
				year, GameState.train_stat_label(current).to_lower(), year + 1], 13, UiKit.TEXT)
		locked.name = "StatFocusLocked"
		locked.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(locked)
		_focus_trait_line(v, p, current)
		if _focus_notice != "":
			v.add_child(UiKit.lbl(_focus_notice, UiKit.SECONDARY, UiKit.GOOD, true))
		return box
	var intro := "Extra work on one stat: about a third of his training goes into it, the rest into his development drills. Points on one stat get dearer as it climbs, so his OVR grows more slowly than on his plan alone. Locked in until the %d season." % [
			year + 1]
	if current != "":
		intro = "Last season's focus, %s, carries on until you lock one in for %d. " % [
				GameState.train_stat_label(current).to_lower(), year] + intro
	var il := UiKit.lbl(intro, 13, UiKit.TEXT)
	il.name = "StatFocusIntro"
	il.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(il)
	var options := []
	for key in GameState.focus_options(p):
		options.append([key, "%s %d" % [GameState.train_stat_label(key), int(attr.get(key, 0))]])
	var chosen := _focus_choice if _focus_choice != "" else current
	v.add_child(UiKit.choice_grid("StatFocusPick", options, chosen, 2, func(key: String):
		_focus_choice = key
		_build()))
	_focus_trait_line(v, p, chosen)
	if chosen != "":
		var lock := UiKit.btn("Lock in %s for %d" % [GameState.train_stat_label(chosen).to_lower(), year], 15, true)
		lock.name = "StatFocusLock"
		lock.custom_minimum_size = Vector2(0, GRID_TOUCH)
		var pid := str(p["id"])
		lock.pressed.connect(func():
			var before := int(GameState.list_player(pid).get("overall", 0))
			if GameState.set_stat_focus(pid, chosen):
				var after := int(GameState.list_player(pid).get("overall", 0))
				_focus_notice = "Banked XP lifted him from %d to %d." % [before, after] if after > before else ""
			_focus_choice = ""
			_build())
		v.add_child(lock)
	return box


## The trait a focus grows him toward, as a fact (row 103): "Contested bull
## at 84 contested: 4 to go." Over seasons: the focus carries on until changed.
func _focus_trait_line(v: Control, p: Dictionary, stat: String) -> void:
	var ft := GameState.focus_trait(p, stat)
	if ft.is_empty():
		return
	var key := str(ft["key"])
	var gap := int(ft["gap"])
	var text := "%s at %d %s: %s." % [Traits.label(key), int(ft["min"]),
			GameState.train_stat_label(stat).to_lower(),
			"he is there" if gap == 0 else "%d to go" % gap]
	if bool(ft["crowded"]):
		text += " He carries two traits already, so it shows only once he is further past its line than he is past one of them."
	var l := UiKit.lbl(text, 13, UiKit.EMPH, true)
	l.name = "StatFocusTrait"
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	TraitLink.tappable(l, key)
	v.add_child(l)


## "Week 3 of 8. As a key forward he rates 66, his own game 71: within 3 by
## week 8 and he can be picked there." The standard he is chasing, plainly.
static func _project_line(p: Dictionary) -> String:
	var job := GameState.project_job(p)
	if job == "":
		return ""
	var role := GameState.project_role(p)
	var there := GameState.rating_as(p, role)
	var own := int(p.get("overall", 0))
	var head := "%s. As a %s he rates %d, his own game %d: " % [
		GameState.project_progress(p), str(GameState.LEARN_JOBS[job]["word"]), there, own]
	if there >= own - GameState.PROJECT_PASS:
		return head + "up to the standard, so he can be picked there after week %d." % GameState.PROJECT_WEEKS
	return head + "within %d by week %d and he can be picked there." % [GameState.PROJECT_PASS, GameState.PROJECT_WEEKS]


## "Contested 72 · Disposal 64": what his plan is spending on.
func _working_on(p: Dictionary) -> String:
	var w: Dictionary = GameState.plan_weights(p)
	var keys := w.keys()
	keys.sort_custom(func(a, b): return float(w[a]) > float(w[b]))
	var bits: PackedStringArray = []
	for k in keys.slice(0, 3):
		bits.append("%s %d" % [GameState.train_stat_label(str(k)), int((p["attr"] as Dictionary).get(k, 0))])
	return "  ·  ".join(bits)


func _stat_row(p: Dictionary, key: String, label: String, useful := true) -> Control:
	var card := UiKit.panel(UiKit.PANEL_ALT, 8, 6)
	var v := UiKit.vbox(4)
	card.add_child(v)
	var cur := int((p["attr"] as Dictionary).get(key, 1))
	var h := UiKit.hbox(8)
	v.add_child(h)
	var name := UiKit.ellipsis(label, UiKit.BODY, UiKit.TEXT, true)
	name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(name)
	var value := UiKit.line(str(cur), UiKit.HEADING, _attr_colour(float(cur)), true)
	value.custom_minimum_size.x = 32
	value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	h.add_child(value)
	var what := UiKit.lbl(StatGuide.short(key) if useful
			else "Does little for a %s in a match." % ROLE_NOUN.get(str(p.get("role", "MID")), "player"),
			12, UiKit.MUTED if useful else UiKit.BAD)
	what.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(what)
	v.add_child(_bar(cur))
	return card


func _bar(value: int) -> Control:
	var holder := Control.new()
	holder.custom_minimum_size = Vector2(0, 8)
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var track := ColorRect.new()
	track.color = Color(1, 1, 1, 0.10)
	track.set_anchors_preset(Control.PRESET_FULL_RECT)
	holder.add_child(track)
	var fill := ColorRect.new()
	fill.color = _attr_colour(float(value))
	fill.set_anchors_preset(Control.PRESET_FULL_RECT)
	fill.anchor_right = clampf(float(value) / 99.0, 0.0, 1.0)
	holder.add_child(fill)
	for bar_part in [track, fill]:
		bar_part.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return holder


func _attr_colour(v: float) -> Color:
	if v >= 75.0:
		return UiKit.GOOD
	if v >= 55.0:
		return UiKit.EMPH
	if v >= 40.0:
		return Color(0.80, 0.76, 0.55)
	return UiKit.BAD


func _ignore_mouse(node: Control) -> void:
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for child in node.get_children():
		if child is Control:
			_ignore_mouse(child)


## Why this player trains cheap (or dear): potential sets the price.
func _potential_note(p: Dictionary) -> String:
	var mult := Potential.training_multiplier(p)
	if bool(p.get("rehab", false)):
		return "Rehab: back near his %d POT after this season. Training is cheaper until then." % int(p["potential"])
	if mult < 0.95:
		return "Room to grow: training is cheaper while he is below his potential."
	var gap := int(p.get("potential", p["overall"])) - int(p["overall"])
	if gap < 0:
		return "Past his projected peak: every point costs far more."
	if mult > 1.0:
		return "Close to his projected peak: training costs more."
	return ""


## Where his POT comes from: draft pedigree and recent rated seasons.
func _background_line(p: Dictionary) -> String:
	var bits: PackedStringArray = []
	if p.has("drafted_pick"):
		var kind := str(p.get("drafted_type", "national"))
		bits.append("Pick %d, %d %s draft" % [int(p["drafted_pick"]), int(p.get("drafted_year", 0)),
				"national" if kind == "national" else kind])
	var seasons: PackedStringArray = []
	for season in p.get("history", []):
		if int(season[0]) >= 2023:
			seasons.append("%d  %d" % [int(season[0]), int(season[1])])
	if not seasons.is_empty():
		bits.append("Rated " + " · ".join(seasons))
	return "  ·  ".join(bits)
