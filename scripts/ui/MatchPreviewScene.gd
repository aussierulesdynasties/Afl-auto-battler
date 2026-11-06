extends Control
## The match preview: this week's facts on a page of their own, between Play
## match and the match-day setup (director, 2026-11-07: "This is really good
## info inside there but no one will click it. It deserves its own place in the
## pre game flow"; he chose "Own step before setup"). The page is WeekPreview,
## the same builder as Team selection's week column. Continue starts the match
## (MatchKickoff): the pre-match scene, then the setup (game plan, matchups) and
## Start. Back, or Android Back, returns to the hub with nothing started.

const MEASURE := 600.0      # the page keeps a readable measure on a wide window

var _week: WeekPreview
var _page: VBoxContainer
var _continue: Button


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	MatchKickoff.reset()
	if GameState.season == null or MatchKickoff.upcoming_match().is_empty():
		Router.replace("hub")
		return
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	# One column, centred, never wider than a readable measure (_fit).
	var root := UiKit.vbox(8)
	root.name = "PreviewColumn"
	margin.add_child(root)
	_week = WeekPreview.new(self, func(_note: String, _undo: Dictionary): _refill())
	root.add_child(UiKit.top_bar("Match preview", true))
	_page = _week.page()
	var sc := UiKit.scroll(_page)
	sc.name = "PreviewScroll"
	root.add_child(sc)
	UiKit.edge_fade(sc)
	_continue = UiKit.btn("Continue", UiKit.HEADING, true)
	_continue.name = "PreviewContinue"
	_continue.custom_minimum_size = Vector2(0, 56)
	_continue.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_continue.pressed.connect(_on_continue)
	root.add_child(_continue)
	_fit(margin)
	get_viewport().size_changed.connect(func():
		if is_inside_tree():
			_fit(margin))


## A wide window: the column stays at the measure, centred, the club's colour either side.
func _fit(margin: MarginContainer) -> void:
	var spare := maxf(0.0, UiKit.view_width(self) - 24.0 - MEASURE)
	var side := int(spare / 2.0)
	UiKit.apply_insets(margin, 12)
	if side > 0:
		margin.add_theme_constant_override("margin_left", margin.get_theme_constant("margin_left") + side)
		margin.add_theme_constant_override("margin_right", margin.get_theme_constant("margin_right") + side)


## A synergy completed from the guide changed the side: the page says the new side.
func _refill() -> void:
	UiKit.clear(_page)
	_week.fill(_page)


func _on_continue() -> void:
	if MatchKickoff.busy:
		return
	_continue.disabled = true
	if not await MatchKickoff.start(get_tree(), true):
		# Nothing to play live after all (the week moved on): the hub says what is next.
		Router.replace("hub")


## Android Back closes the report or the synergy guide first, waits while the side
## is on its way out, and otherwise leaves for the hub (Router's own back).
func handle_back() -> bool:
	if FirstVisitIntro.close_open(self):
		return true
	if _week != null and _week.close_overlay():
		return true
	return MatchKickoff.busy
