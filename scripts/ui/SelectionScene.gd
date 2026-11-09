extends Control
## Team selection: your match-day 23, built on the field (TeamBuilder; the
## director's PC playtest, 2026-10-07). Until you move someone the best side
## is picked for you each week; your first move makes the side yours, and it
## stays yours until you choose an Auto-pick strategy again. A gap (an
## injured player) is filled automatically on match day.
##
## No scrolling (director, 2026-10-13: "team selection being scrollable doesnt
## feel good"): "The side" is the oval, the interchange and the players not
## picked; "This week" (WeekPreview) is what the choice rests on. A PC shows
## both, side by side; a phone shows the side, and the week has its own step
## between Play match and the setup (the match preview, director 2026-11-07). Player roles,
## game plan and tags are not asked here: they are set on the match-day setup
## before Start (director, 2026-10-13), which opens this screen through
## Change the side and comes back to it with the new side (TODO row 25).

const WEEK_W_MIN := 460.0
const WEEK_W_MAX := 600.0

var _root: VBoxContainer
var _notice := ""
var _week: WeekPreview          # the week beside the side (a wide screen), and its sheets
var _sheet: Control             # a player's profile, open over the list
var _undo := {}            # the side before the last Auto-pick, for Undo
var _view := "mine"        # "mine" or "opp": the oval shows them, read-only
var _line_cache := {}      # the other clubs' lines, built once a visit
var _wide := false
var _chemistry: Control           # the Team Chemistry sheet, open over the side


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.season == null or GameState.my_list.is_empty():
		Router.replace("main")
		return
	# Your club's colour behind the page, as on the hub and match day
	# (director, 2026-10-10: every screen in the gameday style).
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	_root = UiKit.vbox(8)
	margin.add_child(_root)
	_week = WeekPreview.new(self, func(note: String, undo: Dictionary):
		_undo = undo
		if note != "":
			_notice = note
		_build())
	get_viewport().size_changed.connect(func():
		if is_inside_tree() and not UiKit.keyboard_resize(self):
			_build())
	_build()
	FirstVisitIntro.show_if_due.call_deferred(self, "selection")


func _build() -> void:
	# A move or a resize rebuilds the page: keep your place in the list.
	var places := UiKit.scroll_places(_root)
	UiKit.clear(_root)
	_wide = ScreenLayout.wide_view(UiKit.view_width(self), UiKit.view_height(self), 900.0)
	# Auto-pick is an action, never a mode: choose a strategy and it sets the
	# side; your moves after that stay yours (director, 2026-10-07). It is
	# the top bar's right control (audit §8 Phase 1.4): the board comes first.
	var pick := MenuButton.new()
	pick.name = "AutoPick"
	pick.text = "Auto-pick"
	pick.flat = false
	UiKit.style_button(pick, UiKit.BODY)
	pick.custom_minimum_size = Vector2(0, 44)
	var menu := pick.get_popup()
	menu.add_theme_font_override("font", UiKit.FONT)
	UiKit.set_font_size(menu, UiKit.NAME)
	var strategies := [["best", "Best side"], ["rest", "Rest tired players"], ["youth", "Blood the youth"],
			["mine", "My Selected Best 23"]]
	for i in range(strategies.size()):
		menu.add_item(str(strategies[i][1]), i)
	# One ruck or two only changes who Auto-pick names on the bench, so it sits
	# in this menu, ticked when on.
	menu.add_separator()
	menu.add_check_item("Dual ruck", 100)
	menu.set_item_checked(menu.get_item_index(100), GameState.dual_ruck())
	menu.id_pressed.connect(func(idx: int):
		if idx == 100:
			var on := not GameState.dual_ruck()
			GameState.set_dual_ruck(on)
			_notice = "Dual ruck on: Auto-pick names a second ruck on the bench." if on else "One ruck: Auto-pick fills the bench with the best of the rest."
			_build()
			return
		_apply_strategy(str(strategies[idx][0])))
	var bar := UiKit.top_bar("Team selection", true, pick)
	_root.add_child(bar)
	var auto := GameState.my_selection().is_empty()
	# A side named before the wings existed: split its midfield once.
	if not auto and not GameState.my_selection().has("WING"):
		GameState.set_selection(GameState.current_side())
	if _wide:
		var cols := UiKit.hbox(14)
		cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
		_root.add_child(cols)
		cols.add_child(_scroller(_side_page(auto), "SelectionScroll"))
		# The week keeps a readable measure: it does not stretch with the window.
		var right := _scroller(_week.page(), "WeekScroll")
		right.size_flags_horizontal = Control.SIZE_FILL
		right.custom_minimum_size.x = clampf(UiKit.view_width(self) * 0.4, WEEK_W_MIN, WEEK_W_MAX)
		cols.add_child(right)
	else:
		_root.add_child(_scroller(_side_page(auto), "SelectionScroll"))
	var confirm := _confirm_row()
	if confirm != null:
		_root.add_child(confirm)
	if GameState.side_from_match and GameState.match_day_setup_open():
		# Reached from the match-day setup: the way back is the primary action.
		var row := UiKit.hbox(8)
		row.alignment = BoxContainer.ALIGNMENT_END
		var back := UiKit.btn("Back to match day", UiKit.NAME, true)
		back.name = "BackToMatchDay"
		back.custom_minimum_size = Vector2(minf(240.0, UiKit.view_width(self) - 24.0), 48)
		back.pressed.connect(Router.back)
		row.add_child(back)
		_root.add_child(row)
	UiKit.restore_places(_root, places)


## "Confirm side" ticks the Hub checklist's "Look over the side" job
## (director, 2026-11-03: an explicit button, not merely opening Team).
## Only with the weekly_checklist setting on; off, nothing shows or writes.
func _confirm_row() -> Control:
	if not WeekChecklist.on(GameState) or GameState.season.is_season_over():
		return null
	var row := UiKit.hbox(8)
	row.name = "ConfirmRow"
	row.alignment = BoxContainer.ALIGNMENT_END
	var done := WeekChecklist.is_done(GameState, "team")
	var b := UiKit.btn("Side confirmed" if done else "Confirm side", UiKit.NAME, not done)
	b.name = "ConfirmSide"
	b.custom_minimum_size = Vector2(minf(220.0, UiKit.view_width(self) - 24.0), 44)
	b.disabled = done
	b.pressed.connect(func():
		WeekChecklist.mark(GameState, "team")
		_notice = "Side confirmed for this week."
		_build())
	row.add_child(b)
	return row


## A page fills the space and scrolls only if something abnormal (a very long
## week) outgrows it; a normal side and week never show a scroll bar.
func _scroller(page: Control, node_name: String) -> ScrollContainer:
	var sc := UiKit.scroll(page)
	sc.name = node_name
	page.size_flags_vertical = Control.SIZE_EXPAND_FILL
	return sc


## The side: the oval you can look at theirs on, your 18 and the bench, and
## the players not picked, with what acts on the side beside the interchange.
func _side_page(auto: bool) -> Control:
	var page := UiKit.vbox(8)
	page.name = "SidePage"
	var nxt := GameState.my_next_opponent()
	if not nxt.is_empty():
		# Look at them on the same oval (director, 2026-10-07).
		var opp_name := GameDB.club_short(str(nxt["code"]))
		page.add_child(UiKit.segmented("OvalView", [["mine", "Your team"], ["opp", opp_name]], _view, func(k):
			_view = k
			_build()))
	var builder := TeamBuilder.new()
	builder.name = "TeamBuilder"
	builder.stacked = true
	builder.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	builder.size_flags_vertical = Control.SIZE_EXPAND_FILL
	builder.start_note = _notice
	var opp_code := str(nxt.get("code", ""))
	if _view == "opp" and opp_code != "":
		var proj := _week.para("%s as they would take the field this week (projected: they name their side on match day). They kick the other way." % GameDB.club_name(opp_code), 13, UiKit.MUTED)
		proj.name = "OppProjected"
		page.add_child(proj)
		page.add_child(builder)
		var their: Dictionary = GameState.opponent_side(opp_code)
		builder.setup(their["side"], _wide, their["list"], true)
		builder.inspect.connect(_open_opponent.bind(their["list"]))
	else:
		var actions := HBoxContainer.new()
		actions.name = "SideActions"
		actions.add_theme_constant_override("separation", 8)
		_fill_actions(actions)
		builder.interchange_actions = actions
		builder.hint_extra = "Picked for you each week until you move someone." if auto else ""
		# Team Chemistry (row 125), read at a glance above the oval; a tap says why.
		page.add_child(ChemistryMeter.meter(_open_chemistry))
		page.add_child(builder)
		builder.setup(GameState.current_side(), _wide)
	builder.inspect.connect(_open_profile)
	builder.changed.connect(func(note: String):
		_notice = note
		builder.start_note = note
		_undo = {}
		var hint: Label = builder.find_child("BuilderHint", true, false)
		if hint != null:
			hint.text = note
			hint.add_theme_color_override("font_color", UiKit.GOOD)
		_refresh_facts())
	return page


## Save as my Best 23 and Undo, beside the interchange they act on.
func _fill_actions(actions: HBoxContainer) -> void:
	var save := UiKit.text_action("Save as my Best 23", UiKit.SECONDARY)
	save.name = "SaveBest23"
	save.pressed.connect(func():
		GameState.set_best23(GameState.current_side())
		_notice = "Saved as your Best 23. Choose it any week from Auto-pick."
		_build())
	actions.add_child(save)
	if not _undo.is_empty():
		var undo := UiKit.text_action("Undo", UiKit.SECONDARY)
		undo.name = "UndoPick"
		undo.pressed.connect(func():
			GameState.set_selection(_undo)
			_undo = {}
			_notice = "Back to your side before the auto-pick."
			_build())
		actions.add_child(undo)


func _open_chemistry() -> void:
	_close_chemistry()
	_chemistry = ChemistryMeter.open(self, func(): _chemistry = null)


func _close_chemistry() -> bool:
	var was := _chemistry != null and is_instance_valid(_chemistry)
	if was:
		_chemistry.queue_free()
	_chemistry = null
	return was


## After a move: the week and the actions beside the interchange, without
## rebuilding the builder (or losing your place in it).
func _refresh_facts() -> void:
	var v: VBoxContainer = _root.find_child("WeekPage", true, false)
	if v != null:
		UiKit.clear(v)
		_week.fill(v)
	var actions: HBoxContainer = _root.find_child("SideActions", true, false)
	if actions != null:
		UiKit.clear(actions)
		_fill_actions(actions)
	var meter: Button = _root.find_child("ChemistryMeter", true, false)
	if meter != null:
		ChemistryMeter.refresh(meter)


## Their player's profile: who he is and how he plays, nothing to change.
func _open_opponent(id: String, list: Array) -> void:
	for p in list:
		if str(p["id"]) == id:
			_close_profile()
			_sheet = PlayerSheet.open(self, p, func(): _sheet = null, [])
			return


func _apply_strategy(key: String) -> void:
	var r: Dictionary = GameState.auto_pick(key)
	if (r["side"] as Dictionary).is_empty():
		_notice = str(r["note"])
		_build()
		return
	_undo = GameState.my_selection()
	GameState.set_selection(r["side"])
	_notice = str(r["note"])
	_build()


## A player's profile over the list; closing it leaves the list untouched. A
## player with few senior games can be backed from here (Backing).
func _open_profile(id: String) -> void:
	var p := GameState.list_player(id)
	if p.is_empty():
		return
	_close_profile()
	var actions := []
	if GameState.can_back(p):
		var run := MatchNotes.count_word(Backing.RUN_GAMES)
		actions.append({"name": "BackRun", "label": "Back for %s games" % run,
				"detail": "A run of %s senior games, starting with the next. Leave a fit player out and the promise breaks, and it stings." % run,
				"run": _back.bind(id)})
	_sheet = PlayerSheet.open(self, p, func(): _sheet = null, actions)


## Promise a player a run: the profile closes and the screen says what changed.
func _back(id: String) -> void:
	var out := GameState.back_player(id)
	_close_profile()
	if out != "":
		_notice = out
	_build()


func _close_profile() -> void:
	if _sheet != null and is_instance_valid(_sheet):
		_sheet.queue_free()
	_sheet = null


## Android Back closes a profile, then the report or the synergy guide, then leaves.
func handle_back() -> bool:
	if FirstVisitIntro.close_open(self):
		return true
	if _sheet != null and is_instance_valid(_sheet):
		_close_profile()
		return true
	if _close_chemistry():
		return true
	return _week != null and _week.close_overlay()


## The club's readable ink on the dark page (4.5:1 or better, UiKit.club_ink):
## the heading text must always read, and the guernsey beside it carries
## whose side it is (director, 2026-10-14).
func _side_ink(code: String) -> Color:
	return UiKit.club_name_colour(UiKit.club_ink(code))


func _side_name(code: String, fs: int, marker := 18.0) -> Control:
	var h := UiKit.hbox(6)
	h.add_child(UiKit.club_marker(code, marker))
	h.add_child(UiKit.line(GameDB.club_name(code), fs, _side_ink(code), true))
	return h


