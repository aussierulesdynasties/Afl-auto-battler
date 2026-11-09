extends Control
## Live match view: scoreboard, the animated oval, a commentary feed and
## playback controls. Your own match (home-and-away or final) is simulated a
## quarter at a time around the coach box; any other result is a replay of
## the event log GameState.advance() recorded.

const FEED_LIMIT := 60
const SPEEDS := [1.0, 2.0, 4.0, 8.0]
## Routine play drives the animation but would drown the feed; the feed
## keeps what MatchNotes.FEED_KINDS names (goals, behinds, breaks, calls).
const QUIET_KINDS := ["kick", "handball", "sub", "ballup", "throwin", "mark", "tackle", "smother", "spoil", "pressure", "inside50",
		"rebound", "clanger", "free", "fifty", "last_disposal", "out_on_full"]
## A run of goals worth a line in the feed.
const RUN_LINE := 3
## MatchSim's minutes per quarter (it stamps Q2 from 31, Q3 from 61...).
const QUARTER_MINUTES := 30

var _res := {}
var _pitch: PitchView
var _root: VBoxContainer
var _score_home: Label
var _score_away: Label
## The band behind both scores: its width is what the two scores must share.
var _score_band: Control
var _clock: Label
var _feed: VBoxContainer
var _feed_scroll: ScrollContainer
var _play_btn: Button
var _speed_btns: Array = []
var _finished := false
var _side_panel: Control
var _body: BoxContainer
var _interactive := false
## Reviewing a match already played (Sim round, or Review last match): straight
## to full time, nothing played or applied again.
var _review := false
var _event_cursor := 0
## Your side's legs (id -> energy) when the stretch now playing was simulated:
## the tired marks read these until the oval catches up with the sim.
var _legs_seen := {}
var _my_side := 0
var _margin: MarginContainer
var _stacked := false
var _last_tactics := {}
var _skipping := false
## Skip to the next break (director, 2026-11-06): beside Skip to full time in
## the first three quarters. Quarter breaks opened so far (set as each opens).
var _break_skip: Button
var _breaks_played := 0
const BREAK_NAMES := ["quarter time", "half time", "three-quarter time"]
var _crowd: CrowdSound = null    # FL-004: the crowd (presentation only)
var _fulltime_shown := false
## FL-007: the milestone this match honours after the siren (GameState's banner
## milestone, read before full time counts the game), or {} for none.
var _farewell := {}
var _coach_overlay: Control
var _sheet_overlay: Control
var _over: Control   # T3.R42: every sheet, call and scene opens here, under the scoreboard
var _reflow_queued := false
var _shown_goals := [0, 0]
var _shown_behinds := [0, 0]
var _shown_q := 1
var _shown_min := 0
var _moment_overlay: Control
## Broadcast vignettes sit over the live oval and never touch MatchSim. They
## are deliberately sparse: at most three ordinary close-ups per watched
## match, with the final-kick set shot allowed as a separate special beat.
var _broadcast_overlay: Control
var _broadcast_pending := false
var _broadcast_busy := false
var _broadcast_finish_waiting := false
var _broadcast_seen := {}
var _broadcast_count := 0
var _broadcast_speccies := 0
var _broadcast_last_event := -1000
var _playback_event_index := 0
var _momentum := 0.0            # the engine's momentum as shown: -1 (away on top) .. 1 (home on top)
var _mom_meter: Control       # MomentumMeter: draws the engine's momentum
var _mom_word: Label          # who has it, in words
var _mom_note: Label          # first match only: what it is
## The break is the PC sheet (four columns): player cards say their detail
## on one line and choices sit 40 tall (a mouse, not a thumb).
var _pc_break := false
var _pos_before := 0          # your ladder spot before this match
var _lead: Label
var _setup_line: RichTextLabel
var _report_overlay: Control
var _ft_box := {}               # the full-time review: overlay, body, footer
var _ft_tabs: HBoxContainer
var _ft_tab := "summary"        # summary (home), stats or report
var _run_side := -1            # who kicked the last goal, and how many in a row
var _run_len := 0
var _press_said := [false, false]  # the Defensive Press line, once a side
var _call_mem := MatchNotes.call_state()  # the structural calls' lines (MatchNotes.call_lines)
var _name_index := {}           # name -> club for NameInk, built once per match
var _duel_mem := {}             # the feed's memory of the forward-50 duels (MatchNotes.duel_feed_line)
var _break_refresh := Callable()   # the one-line break: say each call's answer again after a pick
var _break_sheets: Array = []      # the one-line break: open sheets, the top one last ({overlay, close})


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_interactive = GameState.pending_sim != null and not GameState.pending_match.is_empty()
	if _interactive and GameState.side_from_match:
		# Back from Change the side: the match is made again from the new side.
		GameState.rebuild_pending_side()
	if _interactive:
		_res = GameState.pending_sim.result()
		_res["home"] = GameState.pending_match["home"]
		_res["away"] = GameState.pending_match["away"]
		_res["label"] = GameState.pending_match["label"]
		_res["venue"] = str(GameState.pending_match.get("venue", ""))
		_res["events"] = []
		_my_side = 0 if str(_res["home"]) == GameState.my_club else 1
		_pos_before = GameState.my_position()
		# A pre-season practice match is nobody's debut, farewell or first goal.
		_farewell = {} if _is_practice(GameState.pending_match) else _farewell_for(GameState.pending_match)
	else:
		_res = GameState.last_match
		_review = GameState.review_requested
		GameState.review_requested = false
		if not _res.is_empty() and GameState.my_club != "":
			_my_side = 0 if str(_res.get("home", "")) == GameState.my_club else 1
		_pos_before = GameState.last_pos_before
	if _res.is_empty():
		Router.replace("hub")
		return
	# Report a problem (Settings) quotes this match's last feed lines.
	ProblemReport.start_feed("%s, %s v %s" % [str(_res.get("label", "")),
			GameDB.club_name(str(_res["home"])), GameDB.club_name(str(_res["away"]))])
	# The ground the vignettes draw: the MCG has its own stands (FL-003); every other
	# venue keeps the plain ground. Set every match, as the static outlives the scene.
	VignetteGround.use_match(_res)
	_crowd = CrowdSound.new()
	_crowd.name = "Crowd"
	add_child(_crowd)
	_build()
	_pitch.setup(_res)
	_refresh_rings()
	# Whose first AFL goal the feed can say, if it comes today (MatchNotes).
	if _interactive and not _is_practice(_res):
		_duel_mem["first_goal"] = GameState.first_goal_candidates()
		_duel_mem["career_high"] = GameState.career_high_candidates()
	_pitch.event_played.connect(_on_event)
	_pitch.finished.connect(_on_finished)
	_pitch.ends_changed.connect(_on_ends_changed)
	_update_scoreboard({"q": 1, "min": 0, "score": [0, 0], "kind": "info"})
	if _interactive and GameState.match_way_live == "skip":
		# Skip (the poster): straight to full time on the plan you took in,
		# as Skip to full time before the first bounce.
		GameState.match_way_live = "watch"
		_on_skip.call_deferred()
	elif _interactive:
		_show_coach_box()
	elif _review:
		_on_finished()
	else:
		# Give the eye a beat to find the oval before the bounce.
		get_tree().create_timer(0.55).timeout.connect(func():
			if not _finished:
				_pitch.play()
				_sync_controls())


func _build() -> void:
	_margin = MarginContainer.new()
	_margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(_margin, 10)
	add_child(_margin)

	_root = UiKit.vbox(8)
	_margin.add_child(_root)

	_root.add_child(_scoreboard())
	_mount_body(UiKit.view_width(self) < 640.0)
	_root.add_child(_body)
	# T3.R42 (P-26): on a phone the score and the clock never leave the screen.
	# Breaks, sheets, calls and scenes open in the space under the scoreboard.
	_over = Control.new()
	_over.name = "UnderScoreboard"
	_over.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_over)
	_over.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)


## The overlays' top: the scoreboard's foot on a phone; a wide screen's break
## keeps the whole height (its band carries the score).
func _fit_over() -> void:
	if _over == null or _root == null or _root.get_child_count() == 0:
		return
	var board := _root.get_child(0) as Control
	_over.offset_top = board.get_global_rect().end.y - get_global_rect().position.y if _stacked else 0.0


func _mount_body(stack: bool) -> void:
	# Stack the feed under the oval on a narrow phone. Landscape keeps the
	# oval beside the feed, and the pitch itself is never rebuilt.
	_stacked = stack
	if stack:
		_body = UiKit.vbox(8)
	else:
		_body = HBoxContainer.new()
		_body.add_theme_constant_override("separation", 10)
	_body.size_flags_vertical = Control.SIZE_EXPAND_FILL

	if _pitch == null:
		_pitch = PitchView.new()
		_pitch.speed = GameState.match_speed()
	# A phone follows the ball close up because its screen is small (and so does
	# any narrow, stacked window); a wide window shows the whole ground whatever
	# the platform (director, 2026-10-09; the web build on a PC, 2026-10-12).
	_orient_pitch(stack)
	_pitch.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_pitch.size_flags_vertical = Control.SIZE_EXPAND_FILL
	# The feed is a handful of lines (scores, breaks, calls): on a phone the
	# oval gets the height.
	_pitch.size_flags_stretch_ratio = 2.2 if stack else 1.5
	_body.add_child(_pitch)

	if _side_panel == null:
		_side_panel = UiKit.panel(UiKit.PANEL, 10)
		var sv := UiKit.vbox(6)
		_side_panel.add_child(sv)
		# Your match: the calls you have on, so the setup is never a guess.
		# Every call in full: a long name or several calls wrap, never trim.
		_setup_line = NameInk.rich(UiKit.SMALL, UiKit.MUTED)
		_setup_line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_setup_line.name = "SetupLine"
		_setup_line.visible = false
		sv.add_child(_setup_line)
		_feed = UiKit.vbox(4)
		_feed.name = "Feed"
		_feed_scroll = UiKit.scroll(_feed)
		# Following the play, a line cut off at the top would leave a stray end of
		# a sentence ("time.") over the newest lines: see _hide_cut_rows.
		var bar := _feed_scroll.get_v_scroll_bar()
		bar.value_changed.connect(func(_v: float) -> void: _hide_cut_rows())
		bar.changed.connect(_hide_cut_rows)
		sv.add_child(_feed_scroll)
		sv.add_child(_controls())
	_fit_side_panel()
	_body.add_child(_side_panel)


## A phone held upright shows the whole ground running top to bottom, goals at
## the top and the bottom, nothing cut off (director, 2026-10-14). A phone on its
## side, and any narrow window wider than it is tall, keeps the close-up that
## follows the ball; a wide window shows the whole ground left to right.
func _orient_pitch(stack: bool) -> void:
	if _pitch == null:
		return
	var tall := UiKit.view_height(self) > UiKit.view_width(self)
	_pitch.upright = stack and tall
	_pitch.camera_enabled = (stack or ScreenLayout.is_phone()) and not _pitch.upright


func _fit_side_panel() -> void:
	if _side_panel == null:
		return
	if _stacked:
		var short := UiKit.view_height(self) < 520.0
		# Grown with the text size (Settings), so a larger size keeps the same
		# lines of the feed in view above the buttons.
		_side_panel.custom_minimum_size = Vector2(0, UiKit.px(120 if short else 168))
		_side_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_side_panel.size_flags_stretch_ratio = 1.0
	else:
		_side_panel.custom_minimum_size = Vector2(220, 0)
		_side_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_side_panel.size_flags_stretch_ratio = 0.7
	_side_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL


## Names sit above the score, not beside it. A wrapping label in a tight hbox
## collapses to one character per line and pushes the oval off the phone.
func _scoreboard() -> Control:
	var narrow := UiKit.view_width(self) < 640.0
	# Both clubs' colours behind the score (director, 2026-10-08: not boring).
	var v := UiKit.vbox(4)
	var p := ClubDuel.band(str(_res["home"]), str(_res["away"]), v, 8, 0.35)
	var h := UiKit.hbox(6)
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(h)
	h.add_child(_score_column(str(_res["home"]), true, narrow))
	h.add_child(_score_middle(narrow))
	h.add_child(_score_column(str(_res["away"]), false, narrow))
	v.add_child(_momentum_bar())
	p.item_rect_changed.connect(_fit_over)
	p.item_rect_changed.connect(_fit_scores)
	_score_band = p
	return p


## Who has the run of play: the engine's momentum (MatchSim.momentum), which
## goals swing, time fades and a goal the other way turns. The side it
## favours wins a little more of the ball at stoppages and loose balls.
## Director, 2026-10-07: always labelled, the club on top named in words and
## its colour growing from the centre toward it (one colour at a time, so
## like colours cannot confuse it); a tap explains it, and the first match
## you watch says so once, under it.
const MOMENTUM_EVEN := 0.12
## Row 78: a side well ahead can run away with it, so the sheet says what a runaway does.
const MOMENTUM_INFO_RUNAWAY := [
	"Momentum is the run of play. A goal swings it toward the side that kicked it, a behind a little; it fades as play goes on and halves at every break.",
	"The side on top wins a little more of the ball at centre bounces, stoppages and loose balls - never a guarantee. A goal the other way turns it.",
	"A side more than four goals up with the run of play can run away with it: the further ahead, the more of the ball it wins, the longer the run lasts and the more goals it takes to turn. A call to win the ball back still counts in full.",
]


static func momentum_info() -> Array:
	return MOMENTUM_INFO_RUNAWAY


func _momentum_bar() -> Control:
	var b := Button.new()
	b.name = "MomentumBar"
	b.flat = true
	b.custom_minimum_size = Vector2(0, 30)
	b.pressed.connect(_show_momentum_info)
	var v := UiKit.vbox(2)
	v.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(v)
	var h := UiKit.hbox(6)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var label := UiKit.line("Momentum", UiKit.SMALL, UiKit.MUTED)
	ClubDuel.on_colour(label)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(label)
	_mom_word = UiKit.ellipsis("", UiKit.SMALL, UiKit.TEXT, true)
	_mom_word.name = "MomentumWord"
	_mom_word.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_mom_word.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(_mom_word)
	v.add_child(h)
	_mom_meter = MomentumMeter.new()
	_mom_meter.call("setup", UiKit.score_colour(str(_res["home"])), UiKit.score_colour(str(_res["away"])))
	v.add_child(_mom_meter)
	var box := UiKit.vbox(2)
	box.add_child(b)
	_mom_note = UiKit.lbl("", UiKit.SMALL, UiKit.MUTED)
	_mom_note.name = "MomentumNote"
	_mom_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_mom_note.visible = false
	box.add_child(_mom_note)
	_paint_momentum()
	return box


func _paint_momentum() -> void:
	if _mom_meter == null or not is_instance_valid(_mom_meter):
		return
	_mom_meter.call("show_value", _momentum)
	if absf(_momentum) < MOMENTUM_EVEN:
		_mom_word.text = "Even"
		ClubDuel.on_colour(_mom_word)
	else:
		var code := str(_res["home"] if _momentum > 0.0 else _res["away"])
		_mom_word.text = "%s on top" % GameDB.club_short(code)
		ClubDuel.on_colour(_mom_word)
	# The first match you watch: once it first moves, one line says what it is.
	if _interactive and not _mom_note.visible and absf(_momentum) >= MOMENTUM_EVEN \
			and GameState.intro_due("momentum"):
		GameState.set_setting("seen_momentum_intro", true)
		_mom_note.text = "Momentum swings with each goal and fades with time; the side on top wins a little more of the ball. %s it for more." % ScreenLayout.tap_word()
		_mom_note.visible = true


func _show_momentum_info() -> void:
	_close_sheet()
	var box := UiKit.modal_box(_over, 520.0, 0.0, _wash())
	var overlay: Control = box["overlay"]
	overlay.name = "MomentumInfo"
	_sheet_overlay = overlay
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.heading("Momentum", UiKit.TITLE))
	for line in momentum_info():
		var l := UiKit.lbl(line, UiKit.BODY, UiKit.TEXT)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(l)
	var ok := UiKit.btn("Got it", UiKit.NAME, true)
	ok.name = "MomentumInfoOk"
	ok.custom_minimum_size = Vector2(0, 44)
	ok.pressed.connect(_close_sheet)
	box["footer"].add_child(ok)


## A centre line; the club on top's colour grows from it toward his end, as
## far as the engine's momentum (-1 away .. 1 home).
class MomentumMeter extends Control:
	var _home := Color.WHITE
	var _away := Color.WHITE
	var _v := 0.0

	func setup(home: Color, away: Color) -> void:
		_home = home
		_away = away
		custom_minimum_size = Vector2(0, 8)
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func show_value(v: float) -> void:
		_v = v
		queue_redraw()

	func _draw() -> void:
		var w := size.x
		var mid := w / 2.0
		var y := size.y / 2.0
		draw_rect(Rect2(0, y - 1.0, w, 2.0), UiKit.LINE)
		var reach := mid * clampf(absf(_v), 0.0, 1.0)
		if reach >= 1.0:
			if _v > 0.0:
				draw_rect(Rect2(mid - reach, 0, reach, size.y), _home)
			else:
				draw_rect(Rect2(mid, 0, reach, size.y), _away)
		draw_rect(Rect2(mid - 1.0, 0, 2.0, size.y), UiKit.TEXT)


## Every event carries the engine's momentum as it stood ("mom"): the meter
## shows exactly that, nothing of its own.
func _track_momentum(ev: Dictionary) -> void:
	if not ev.has("mom"):
		return
	_momentum = clampf(float(ev["mom"]), -1.0, 1.0)
	if not _skipping:
		_paint_momentum()


func _score_column(code: String, home: bool, narrow: bool) -> Control:
	var v := UiKit.vbox(1)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var name_text := GameDB.club_short(code) if narrow else GameDB.club_name(code)
	var name := UiKit.ellipsis(name_text, UiKit.SECONDARY if narrow else 16, UiKit.TEXT, true)
	name.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT if home \
			else HORIZONTAL_ALIGNMENT_LEFT
	ClubDuel.on_colour(name)
	v.add_child(name)
	var score := UiKit.figure("0.0 (0)", UiKit.RATING if narrow else 36, Color.WHITE)
	ClubDuel.on_colour(score)
	score.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT if home \
			else HORIZONTAL_ALIGNMENT_LEFT
	# A fixed minimum wider than the phone column is what shoved the oval
	# off screen. Let the score take its own width in portrait.
	if not narrow:
		score.custom_minimum_size = Vector2(136, 0)
	v.add_child(score)
	if home:
		_score_home = score
	else:
		_score_away = score
	return v


## The clock and who leads, between the two scores. The round and the
## ground are for the build-up (the first coach box), not the live glance.
func _score_middle(narrow: bool) -> Control:
	var mid := UiKit.vbox(0)
	mid.alignment = BoxContainer.ALIGNMENT_CENTER
	mid.custom_minimum_size = Vector2(84 if narrow else 132, 0)
	_clock = UiKit.line("Q%d %d'" % [_shown_q, _shown_min], 17 if narrow else 20, UiKit.TEXT, true)
	_clock.name = "Clock"
	_clock.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ClubDuel.on_colour(_clock)
	mid.add_child(_clock)
	_lead = UiKit.ellipsis("", UiKit.SMALL, UiKit.MUTED)
	_lead.name = "LeadLine"
	_lead.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ClubDuel.on_colour(_lead)
	mid.add_child(_lead)
	return mid


## A final names its venue (the Grand Final is always at the MCG); any
## other match is at the home club's ground.
func _venue() -> String:
	return VignetteGround.ground_of(_res)


func _controls() -> Control:
	var v := UiKit.vbox(6)

	var row := UiKit.hbox(5)
	v.add_child(row)
	_play_btn = UiKit.btn("Pause", UiKit.SECONDARY)
	_play_btn.custom_minimum_size = Vector2(0, 44)
	_play_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_play_btn.clip_text = true
	_play_btn.pressed.connect(_on_toggle)
	row.add_child(_play_btn)

	for s in SPEEDS:
		var b := UiKit.btn("%dx" % int(s), UiKit.SECONDARY)
		b.custom_minimum_size = Vector2(0, 44)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.clip_text = true
		b.pressed.connect(_on_speed.bind(s))
		_speed_btns.append(b)
		row.add_child(b)

	var row2 := UiKit.hbox(5)
	v.add_child(row2)
	var skip := UiKit.btn("Skip to full time", UiKit.SECONDARY)
	skip.custom_minimum_size = Vector2(0, 44)
	skip.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	skip.pressed.connect(_on_skip)
	row2.add_child(skip)

	# The rest of this quarter at once, then the break and its calls as ever.
	# Only in a match you coach, and not in the last quarter (it would be
	# Skip to full time).
	if _interactive:
		_break_skip = UiKit.btn("Skip to quarter time", UiKit.SECONDARY)
		_break_skip.name = "SkipToBreak"
		_break_skip.custom_minimum_size = Vector2(0, 44)
		_break_skip.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_break_skip.clip_text = true
		_break_skip.pressed.connect(_on_skip_to_break)
		_break_skip.ready.connect(_fit_break_skip, CONNECT_ONE_SHOT)
		row2.add_child(_break_skip)
		row2.move_child(_break_skip, 0)

	# Your own match cannot be left half way (Back says so); a replay can.
	if not _interactive:
		var leave := UiKit.btn("Back to hub", UiKit.SECONDARY)
		leave.custom_minimum_size = Vector2(0, 44)
		leave.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		leave.pressed.connect(func(): Router.back())
		row2.add_child(leave)

	_sync_controls()
	return v


## The break button is never narrower than its longest name: on a 320-wide
## screen half the row would cut "Skip to three-quarter time" short, so it
## takes what it needs and Skip to full time the rest.
func _fit_break_skip() -> void:
	var fnt := _break_skip.get_theme_font("font")
	var fs := _break_skip.get_theme_font_size("font_size")
	var sty := _break_skip.get_theme_stylebox("normal")
	var pad := (sty.get_margin(SIDE_LEFT) + sty.get_margin(SIDE_RIGHT)) if sty else 0.0
	var need := 0.0
	for n in BREAK_NAMES:
		need = maxf(need, fnt.get_string_size("Skip to " + str(n), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x)
	_break_skip.custom_minimum_size.x = ceilf(need + pad + 4.0)


func _sync_controls() -> void:
	if _play_btn == null:
		return
	_play_btn.text = "Play" if not _pitch.playing else "Pause"
	for i in range(SPEEDS.size()):
		UiKit.set_selected(_speed_btns[i], is_equal_approx(_pitch.speed, SPEEDS[i]))
	if _break_skip != null:
		var at := _breaks_played + 1
		_break_skip.visible = at < 4 and not _finished
		if at < 4:
			_break_skip.text = "Skip to " + str(BREAK_NAMES[at - 1])


func _on_toggle() -> void:
	_pitch.toggle()
	_sync_controls()


func _on_speed(s: float) -> void:
	_pitch.set_speed(s)
	_sync_controls()


func _on_skip() -> void:
	_skipping = true
	_close_coach()
	_close_moment()
	if _interactive and GameState.pending_sim != null:
		_simulate_remaining()
	if _pitch != null:
		_pitch.skip_to_end()


## Skip to the break: this quarter is rolled to its end exactly as watching it
## would roll it (MatchSim.run_quarter; a call still to come takes its default,
## as Skip to full time does), every event reaches the feed and the
## scoreboard without the animation, and the break comes up with every call.
func _on_skip_to_break() -> void:
	var sim: MatchSim = GameState.pending_sim
	if not _interactive or sim == null or _pitch == null or _skipping or _finished or _breaks_played >= 3:
		return
	if _coach_overlay != null and is_instance_valid(_coach_overlay):
		return
	_close_moment()
	# A close-up queued for this frame is dropped with the play it would show.
	_broadcast_pending = false
	# The rest of the quarter takes a moment on a phone: the button says so
	# and the oval holds still while it is played.
	_pitch.pause()
	_skipping = true
	_break_skip.disabled = true
	_break_skip.text = "Playing on..."
	await get_tree().process_frame
	await get_tree().process_frame
	# Skip to full time in those two frames has already ended the match.
	if not is_inside_tree() or GameState.pending_sim != sim or _finished:
		return
	if sim.quarter_in_progress():
		_res = sim.run_quarter()
		_stamp_match_meta()
		_append_new_events()
	# No crowd or close-ups on the way.
	_pitch.release_all()
	_skipping = false
	_break_skip.disabled = false
	_refresh_rings()
	_paint_momentum()
	_on_finished()


func _close_moment() -> void:
	if _moment_overlay != null and is_instance_valid(_moment_overlay):
		if _moment_overlay.has_meta("scene") and not _skipping:
			# Cut back to the match: the scene fades out over play resuming.
			var leaving := _moment_overlay
			leaving.name = "MomentLeaving"
			leaving.mouse_filter = Control.MOUSE_FILTER_IGNORE
			for c in leaving.find_children("*", "Control", true, false):
				(c as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
			var tw := leaving.create_tween()
			tw.tween_property(leaving, "modulate:a", 0.0, 0.3)
			tw.tween_callback(leaving.queue_free)
		else:
			_moment_overlay.queue_free()
	_moment_overlay = null


func _close_coach() -> void:
	_close_sheet()
	_close_break_sheets()
	_break_refresh = Callable()
	if _coach_overlay != null and is_instance_valid(_coach_overlay):
		# The closing break stays in the tree until the frame ends; a quarter that
		# ends in the same frame (its play skipped through) opens the next break beside it, which would
		# then be named CoachBox2. The closing one gives the name up first.
		_coach_overlay.name = "CoachBoxClosing"
		_coach_overlay.queue_free()
		_coach_overlay = null


## Finish every quarter that has not been rolled yet, using the last plan the
## coach set. Skip used to drain only the events already on the pitch, which
## stopped at the quarter break.
func _simulate_remaining() -> void:
	var sim: MatchSim = GameState.pending_sim
	if sim == null or sim.current_quarter > 4:
		return
	# A quarter paused on a moment finishes first; the moment takes the
	# default call.
	if sim.quarter_in_progress():
		_res = sim.run_quarter()
		_stamp_match_meta()
	var t := _last_tactics
	if t.is_empty():
		# Skipped before the first bounce: the plan you took in still plays.
		t = {"gameplan": _current_plan(sim), "tag_id": "", "pep": "steady"}
	while sim.current_quarter <= 4:
		_apply_quarter_tactics(t)
		_res = sim.run_quarter()
		_stamp_match_meta()
	if sim.needs_extra_time():
		_res = sim.run_extra_time()
		_stamp_match_meta()
	_append_new_events()


# ---------------------------------------------------------------------------
# Quarter-by-quarter coaching
# ---------------------------------------------------------------------------
const GAMEPLANS := [
	["balanced", "Balanced"], ["attacking", "Attack Corridor"],
	["defensive", "Defensive Press"], ["contest", "Win Contest"],
	["controlled", "Controlled Tempo"],
]
const PEP_TALKS := [
	["steady", "Stay composed"], ["fire_up", "Fire them up"], ["calm", "Calm the group"],
	["heat", "Bring the heat"],
]


## The break: what happened, then your calls for the next quarter. It
## surfaces the problem - their midfield on top, a forward hurting you - and
## leaves the answer to you. No advice, no expected points.
func _show_coach_box() -> void:
	if _coach_overlay != null and is_instance_valid(_coach_overlay):
		return
	# A new break: nothing to pack again until this one is built.
	_break_pack_cols = []
	_break_reading = []
	_pitch.pause()
	var sim: MatchSim = GameState.pending_sim
	var q := sim.current_quarter
	# The skip button names the next break from here. Counted when the break
	# opens, not at the siren: in the moment between the two, a tap still
	# lands on the break that has just sounded, and the button says so.
	_breaks_played = q - 1
	_sync_controls()
	# The calls fill the screen at every break, so the actions sit at the
	# bottom with the choices just above them.
	# On a PC the break is a wide landscape sheet with every call in view
	# (director, 2026-10-09: "it looks like we are using a mobile UI on a PC").
	var wide := _wide_break()
	_pc_break = wide
	var stats_pc: Button = null
	var box := UiKit.modal_box(_over, minf(UiKit.view_width(self) - 48.0, 1560.0) if wide else 640.0, 0.0, _wash())
	var overlay: Control = box["overlay"]
	overlay.name = "CoachBox"
	_coach_overlay = overlay
	var v: VBoxContainer = box["body"]
	var titles := {1: "Before the first ball-up", 2: "Quarter time", 3: "Half time", 4: "Three-quarter time"}
	# The break leads with both clubs' colours (director, 2026-10-08).
	# On a PC the title and the score share one line: the band is wide.
	var bv: BoxContainer = UiKit.hbox(16) if wide else UiKit.vbox(2)
	var band := ClubDuel.band(str(_res["home"]), str(_res["away"]), bv, 14)
	band.name = "BreakBand"
	(band.get_child(0) as ClubDuel).live()   # match day's atmosphere settles in (Feel)
	v.add_child(band)
	# Wide (PC, director 2026-10-11: no column scrolls at 1280x720): the
	# quarter just played and the play-through calls, then the calls in three
	# columns - the plan, the tag and the talk; the defensive set-up. A phone keeps one column, every call
	# in it.
	# Below 1200 units the first column sits above the other three.
	var rep: VBoxContainer = v
	var col_a: VBoxContainer = v
	var col_b: VBoxContainer = v
	var col_c: VBoxContainer = v
	var cols: HBoxContainer = null
	# How many from the game so far each player call shows before "Other
	# player...": two on a wide screen, so every call fits without scrolling.
	var quick := 0
	# From quarter time on the break is one line a call (director, 2026-10-14):
	# every call is built as before, into a store, and laid out by
	# _mount_one_line. The menu before the first ball-up is unchanged.
	var one_line := q > 1
	var store: VBoxContainer = null
	if one_line:
		quick = 2 if wide else 0
		store = UiKit.vbox(6)
		store.name = "CallStore"
		store.visible = false
		rep = store
		col_a = store
		col_b = store
		col_c = store
	if wide and not one_line:
		var four := UiKit.view_width(self) >= 1200.0
		quick = 2
		cols = HBoxContainer.new()
		cols.name = "BreakColumns"
		cols.add_theme_constant_override("separation", 24 if four else 32)
		col_a = UiKit.vbox(6)
		col_b = UiKit.vbox(6)
		col_c = UiKit.vbox(6)
		if four:
			rep = UiKit.vbox(6)
			v.add_child(cols)
		for c in ([rep, col_a, col_b, col_c] if four else [col_a, col_b, col_c]):
			c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			c.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
			cols.add_child(c)
	# The calls of the PC pre-bounce break (three columns once dealt), by what they are, for _deal_calls.
	var calls_by := {}
	var group := func(key: String, node: Node) -> void:
		if node != null:
			if not calls_by.has(key):
				calls_by[key] = []
			(calls_by[key] as Array).append(node)
	var title := UiKit.heading(str(titles.get(q, "Quarter %d" % q)), UiKit.H1)
	title.name = "BreakTitle"
	if wide:
		title.autowrap_mode = TextServer.AUTOWRAP_OFF
		title.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	ClubDuel.on_colour(title)
	bv.add_child(title)
	if q == 1:
		# Gather Round: the event's name stands for the round number, and the line
		# may wrap, so the host ground is never cut short on a phone.
		var label := str(_res.get("label", "Match"))
		var gather := label.ends_with(GatherRound.NAME)
		if gather:
			label = GatherRound.NAME
		var where := UiKit.ellipsis("%s  ·  %s v %s  ·  %s" % [label,
				GameDB.club_short(str(_res["home"])), GameDB.club_short(str(_res["away"])), _venue()], UiKit.BODY, UiKit.TEXT, true)
		where.name = "BreakWhere"
		if gather:
			where.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			where.text_overrun_behavior = TextServer.OVERRUN_NO_TRIMMING
		ClubDuel.on_colour(where)
		if wide:
			where.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			where.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		bv.add_child(where)
	else:
		var sc := UiKit.lbl(MatchNotes.break_score(str(_res["home"]), str(_res["away"]),
				_res.get("goals", [0, 0]), _res.get("behinds", [0, 0]), not wide), UiKit.NAME, UiKit.TEXT, true)
		sc.name = "BreakScore"
		sc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		ClubDuel.on_colour(sc)
		if wide:
			sc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			sc.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		bv.add_child(sc)
		# The full numbers, both clubs, at every break (director's PC
		# playtest, 2026-10-07): a tap, never a compulsory report.
		# On a PC it is a word in the actions row, beside Skip to full time.
		var stats := UiKit.text_action("Match stats", UiKit.BODY)
		stats.name = "BreakStats"
		stats.custom_minimum_size = Vector2(0, 48)
		stats.pressed.connect(_show_break_stats)
		if wide:
			stats_pc = stats
		else:
			rep.add_child(stats)
			rep.add_child(UiKit.spacer(UiKit.GAP))
		var played := UiKit.section(str({2: "First quarter", 3: "Second quarter",
				4: "Third quarter"}.get(q, "Last quarter")))
		played.name = "QuarterHeading"
		played.set_meta("break_unit", true)
		rep.add_child(played)
		rep.add_child(_quarter_view(q - 1))
		var did := MatchNotes.calls_lines(_res, _my_side, q - 1) \
				+ MatchNotes.tag_drop_lines(_res, _my_side, q - 1) \
				+ MatchNotes.lasting_moment_lines(_res, q - 1)
		if not did.is_empty():
			rep.add_child(UiKit.spacer(UiKit.GAP))
			var did_head := UiKit.section("What your calls did")
			did_head.name = "CallsDidHeading"
			did_head.set_meta("break_unit", true)
			rep.add_child(did_head)
			var dnote := UiKit.lbl(MatchNotes.CALLS_DID_NOTE, UiKit.SMALL, UiKit.MUTED)
			dnote.name = "CallsDidNote"
			dnote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			rep.add_child(dnote)
			var dv := UiKit.vbox(4)
			dv.name = "CallsDid"
			for t in did:
				var dl := _say(str(t), UiKit.BODY, UiKit.TEXT)
				dl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				dv.add_child(dl)
			rep.add_child(dv)
	rep.add_child(UiKit.spacer(UiKit.GAP))
	if cols != null and cols.get_parent() == null:
		v.add_child(cols)
	var calls_head := UiKit.section("Your calls" if q == 1 else "Next quarter")
	calls_head.set_meta("break_unit", true)
	col_a.add_child(calls_head)
	group.call("gameplan", calls_head)

	# Your calls, as taps: nothing here is a settings form. Short lists sit
	# in plain view; a player list shows the few in the game so far and
	# keeps everyone else one tap away.
	# The plan in force is the engine's: your club plan before the first
	# bounce (GameState.prepare_interactive_match), your last call after.
	var calls := {
		"gameplan": _current_plan(sim),
		"tag_id": str((sim.tactics[_my_side] as Dictionary).get("tag_id", _last_tactics.get("tag_id", ""))),
		"tagger_id": str((sim.tactics[_my_side] as Dictionary).get("tagger_id", _last_tactics.get("tagger_id", ""))),
		"interceptor_id": str(sim.interceptor[_my_side]),
		"minder_id": str((sim.tactics[_my_side] as Dictionary).get("spare_minder_id", "")) 				if bool((sim.tactics[_my_side] as Dictionary).get("spare_accountable", false)) else "",
		"focus_mid": str((sim.tactics[_my_side] as Dictionary).get("focus_mid", _last_tactics.get("focus_mid", ""))),
		"focus_fwd": str((sim.tactics[_my_side] as Dictionary).get("focus_fwd", _last_tactics.get("focus_fwd", ""))),
		"focus_def": str((sim.tactics[_my_side] as Dictionary).get("focus_def", _last_tactics.get("focus_def", ""))),
		# Before the bounce, a talk you set before Change the side is kept.
		"pep": str((sim.tactics[_my_side] as Dictionary).get("pep", "steady")) if q == 1 else "steady",
	}
	calls["defence"] = MatchNotes.defence_key(str(calls["interceptor_id"]) != "", str(calls["minder_id"]) != "")
	var loose_was := str(calls["interceptor_id"])
	# A tag or a minder you change here is yours from then on: the assistant
	# stops making that call at the breaks (MatchSim._assistant_calls).
	var tag_was := str(calls["tag_id"])
	var minder_was := str(calls["minder_id"])
	var narrow := UiKit.view_width(self) < 560.0

	var plan_known := UiKit.lbl("", UiKit.SECONDARY, UiKit.TEXT, true)
	plan_known.name = "PlanKnown"
	plan_known.visible = false
	# The plan under the buttons, in short separate lines: what it does, what
	# it gains and costs, what it beats, and who makes it work.
	var plan_note := UiKit.vbox(3)
	plan_note.name = "PlanNote"
	var my_ground: Array = (sim.squads[_my_side] as Squad).ground
	var sync_note := func(key: String) -> void:
		for c in plan_note.get_children():
			plan_note.remove_child(c)
			c.queue_free()
		var d := CoachReport.plan_parts(key)
		var does := UiKit.lbl(str(d["does"]), UiKit.BODY, UiKit.TEXT, true)
		does.name = "PlanDoes"
		does.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		plan_note.add_child(does)
		for part in [["gain", "Gain:", "PlanGain"], ["cost", "Cost:", "PlanCost"]]:
			if d.has(part[0]):
				plan_note.add_child(_plan_row(str(part[1]), str(d[part[0]]), str(part[2])))
		if d.has("beats"):
			var beats := UiKit.lbl(str(d["beats"]), UiKit.SECONDARY, UiKit.TEXT)
			beats.name = "PlanBeats"
			beats.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			plan_note.add_child(beats)
		# Who makes it work: the plan's upside rests on them (PlanFit).
		var fit := GameState.plan_fit_short(my_ground, key)
		if not fit.is_empty():
			var who := UiKit.vbox(0)
			who.name = "PlanWho"
			var judged := _say(str(fit["judged"]), UiKit.SECONDARY, UiKit.TEXT)
			judged.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			who.add_child(judged)
			who.add_child(_plan_row("Best for it:", str(fit["names"]), "PlanBest"))
			plan_note.add_child(UiKit.spacer(2))
			plan_note.add_child(who)
		# How well the side knows it (plan familiarity): a decision, so at full strength.
		var known := GameState.plan_known_line(key)
		plan_known.text = known
		plan_known.visible = known != ""
	var plan := _choice_grid("PlanPicker", GAMEPLANS, calls, "gameplan", 2 if narrow else 3, sync_note)
	# The heading and the plan under it stay together.
	var plan_block := _call_block("Gameplan", plan)
	plan_block.remove_meta("break_unit")
	col_a.add_child(plan_block)
	col_a.add_child(plan_known)
	col_a.add_child(plan_note)
	for n in [plan_block, plan_known, plan_note]:
		group.call("gameplan", n)
	sync_note.call(str(calls["gameplan"]))

	# Tag: their most influential so far first, anyone on the ground a tap away.
	# A tag is a midfield job: only their midfielders can be tagged.
	# Only players still in the match: the roster keeps anyone hurt and gone.
	var opp := _roster_side(1 - _my_side).filter(func(r): return _taggable_now(sim, r))
	# Who goes to him - a fact, not advice (Roles: a tagger makes a tag bite
	# harder than a midfielder doing the job). With no tag, say that instead.
	# Who does the job is the coach's call too (director, 2026-10-10: the
	# side's best player was sent to tag, with no say in it). Any of your
	# midfielders on the ground can go; your assistant's man is the default.
	var tagger = MatchSim.tagger_for(my_ground)
	var my_mids := {}
	for p in my_ground:
		if MatchSim.midfielder_on_ground(p):
			my_mids[str(p["id"])] = p
	# The tagger the coach named stays his call at every break (director,
	# 2026-10-14); only a man gone from the match hands the job back.
	if not my_mids.has(str(calls["tagger_id"])) and not sim.taking_part(_my_side, str(calls["tagger_id"])):
		calls["tagger_id"] = ""
	var others := _roster_side(_my_side).filter(func(r):
		return my_mids.has(str(r["id"])) and (tagger == null or str(r["id"]) != str(tagger["id"])))
	# Most able first, by the number on the card: Pressure.
	var press := func(r: Dictionary) -> float:
		return float((my_mids.get(str(r["id"]), r) as Dictionary).get("attr", {}).get("pressure", 0.0))
	others.sort_custom(func(a, b): return press.call(a) > press.call(b))
	# What he gives up: his Player rating for the season so far, the figure the
	# Ratings screen shows (a game's average); -1 before he has played.
	var season_rating := func(id: String) -> float:
		var book: Dictionary = GameState.season_stats.get(id, {})
		var games := int(book.get("games", 0))
		return StatsPlayers.season_rating(book.get("s", {}) as Dictionary) / float(games) if games > 0 else -1.0
	var tag_detail := func(r: Dictionary, wide: bool) -> String:
		var p: Dictionary = my_mids.get(str(r["id"]), r)
		return MatchNotes.tagger_card_detail(p, float(sim.energy.get(str(r["id"]), 100.0)), wide, season_rating.call(str(r["id"])))
	var tag_note := NameInk.rich(UiKit.NOTE, UiKit.MUTED)
	tag_note.name = "TagNote"
	tag_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	# On a phone the note with a tag ("X tags Y: he gives up...") runs to two
	# lines and "No tag..." to one: it keeps room for two, so a tag tap never
	# pushes the calls below it down (A2).
	if not _pc_break:
		tag_note.custom_minimum_size.y = ceilf(UiKit.FONT.get_height(UiKit.px(UiKit.NOTE)) * 2.0)
	# Who goes to him is only a question once there is a him: shown faded and
	# shut with no tag, so it never appears and shoves the calls below it.
	var who_block: Array = []
	var who_wb: Control = null
	var who_hook: Array = [Callable()]
	var sync_tag := func(_key: String) -> void:
		if (who_hook[0] as Callable).is_valid():
			(who_hook[0] as Callable).call()
		# Who tags is always there, under the tag (A2, director 2026-10-14: the
		# tag screen jumping about was "heinous, awful UI design"): faded and
		# shut until there is a man to tag, so picking one moves nothing, not
		# sideways and not down.
		var has_tag := str(calls["tag_id"]) != ""
		for b in who_block:
			(b as Control).modulate.a = 1.0 if has_tag else 0.4
			for wbtn in (b as Node).find_children("*", "Button", true, false):
				(wbtn as Button).disabled = not has_tag
		var who = my_mids.get(str(calls["tagger_id"]), tagger)
		var target := GameDB.player_display_name_by_id(str(calls["tag_id"]), "")
		if str(calls["tag_id"]) == "":
			NameInk.set_line(tag_note, "No tag: your midfielders play their own game.", _names())
		elif who == null:
			NameInk.set_line(tag_note, "No midfielder on the ground to tag with.", _names())
		elif str(calls["tagger_id"]) != "" and not my_mids.has(str(calls["tagger_id"])):
			NameInk.set_line(tag_note, "%s, your tagger, is on the bench. %s tags %s until he is back." % [
					GameDB.player_display_name_by_id(str(calls["tagger_id"]), "Your tagger"), GameDB.player_display_name(who), target], _names())
		else:
			NameInk.set_line(tag_note, GateOdds.tag_note(GameDB.player_display_name(who), target), _names())
	# The tag is offered on their listed midfielders only (director, 2026-10-14:
	# "Only listed midfielders"): the names, and "Other midfielder..." for the
	# listed midfielders not already shown, which is not drawn when none is
	# left. A ruck or a defender running through the middle is not offered, so
	# "Tag which midfielder?" stays true.
	var opp_listed := opp.filter(func(r): return _can_play_midfield(sim, r))
	var tag_first := _in_the_game(opp_listed, quick if quick > 0 else 4)
	# The player the break names as their best is always on offer, if he can
	# play midfield at all.
	for best_p in MatchNotes.standouts(_res, 1 - _my_side, 1):
		var bid := str(best_p.get("id", ""))
		for r in opp_listed:
			if str(r["id"]) == bid and not tag_first.any(func(x): return str(x["id"]) == bid):
				tag_first.append(r)
	var tag := _player_choice("TagPicker", "No tag", opp_listed, tag_first, calls, "tag_id",
			MatchNotes.tag_question(), sync_tag, Callable(), Callable(), "Other player…", true)
	# The question is drawn over the choices, as the loose interceptor's is.
	var tag_block := _call_block("Tag", tag)
	var tag_ask := UiKit.lbl(MatchNotes.tag_question(), UiKit.BODY, UiKit.TEXT, true)
	tag_ask.name = "TagQuestion"
	tag_ask.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tag_block.add_child(tag_ask)
	tag_block.move_child(tag_ask, 1)
	col_a.add_child(tag_block)
	group.call("tag", tag_block)
	if tagger != null and not others.is_empty():
		# Your assistant's man carries the same facts as the others, so
		# they can be compared card for card.
		# On a PC two alternatives beside his card (two rows, so the fullest
		# break still fits 1280x720); the rest are behind Other player....
		var card := func(b: Button, id: String) -> void:
			var who: Dictionary = tagger if id == "" else my_mids.get(id, {})
			if who.is_empty():
				return
			var pid := str(who.get("id", ""))
			_dress_tagger_card(b, _short_name(who), MatchNotes.tagger_card(who, float(sim.energy.get(pid, 100.0)), season_rating.call(pid)), id == "")
		var who_tags := _player_choice("TaggerPicker", _card_text(tagger, tag_detail) + "\nYour assistant's pick", others,
				others.slice(0, 2 if _pc_break else 3),
				calls, "tagger_id", "Who goes to him?", sync_tag, tag_detail, card, "Other tagger…")
		var wb := _call_block("Who tags", who_tags)
		# The follow-up to Tag: packed with its question, never ahead of it.
		wb.set_meta("break_follow", true)
		if not one_line:
			who_block.append(wb)
		who_wb = wb
		col_a.add_child(wb)
		group.call("tag", wb)
	sync_tag.call("")
	col_a.add_child(tag_note)
	group.call("tag", tag_note)

	# Play through, three calls (director, 2026-10-07; back 2026-11-07): each
	# offers the men who fill that job now, and says what it does or that it
	# waits. They sit where Key match-ups sat (director, 2026-11-07: "Roles
	# replace match-ups"): in three columns under the quarter just played, so
	# no column stands half empty (director, 2026-10-10).
	var mine := _roster_side(_my_side)
	for slot in MatchNotes.FOCUS_ORDER:
		var fits := mine.filter(func(r): return (MatchSim.FOCUS_SLOT_ROLES[slot] as Array).has(
				str(_focus_player(str(r["id"])).get("role", r.get("role", "")))))
		var note := UiKit.lbl("", UiKit.NOTE, UiKit.MUTED)
		note.name = "FocusNote_" + slot
		note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var sync := func(id: String) -> void:
			note.text = _focus_note_text(slot, id)
		var text: Array = MatchNotes.FOCUS_SLOT_TEXT[slot]
		var pick := _player_choice("FocusPicker_" + slot, "No one", fits, _in_the_game(fits, quick if quick > 0 else 3), calls, slot,
				"Play through: %s" % str(text[0]).to_lower(), sync)
		var block := _call_block("Play through: %s" % str(text[0]).to_lower(), pick)
		sync.call(str(calls[slot]))
		block.add_child(note)
		(rep if rep != v else col_a).add_child(block)
		group.call("pt", block)

	# Defensive set-up (director, 2026-11-03: Defensive forward and Loose
	# interceptor fold into one call). The coach picks the shape; the men are
	# the ones a coach would send: your loose man stays the one in the job
	# (your assistant's pick), else your best reader of the ball; a forward on
	# their loose man is the best one for it (Matchups.minder_candidates).
	var opp_spare := sim._roaming_interceptor(1 - _my_side)
	var def_ground: Array = []
	for p in my_ground:
		if str(p.get("role", "")) == "DEF":
			def_ground.append(p)
	var interceptors := Matchups.interceptor_candidates(def_ground)
	var loose_pick := str(calls["interceptor_id"])
	if loose_pick == "" and not interceptors.is_empty():
		loose_pick = str(interceptors[0]["id"])
	var fwds := Matchups.minder_candidates(my_ground)
	var minder_pick := str(calls["minder_id"])
	if minder_pick == "" and not fwds.is_empty():
		minder_pick = str(fwds[0]["id"])
	var def_opts: Array = []
	for o in MatchNotes.DEFENCE_SETUPS:
		var k := str(o[0])
		if (k == "cover" or k == "both") and (opp_spare.is_empty() or minder_pick == ""):
			continue
		if (k == "loose" or k == "both") and loose_pick == "":
			continue
		def_opts.append(o)
	if not def_opts.any(func(o): return str(o[0]) == str(calls["defence"])):
		calls["defence"] = "loose" if str(calls["defence"]) == "both" and loose_pick != "" else "man"
	var def_note := UiKit.lbl("", UiKit.NOTE, UiKit.MUTED)
	def_note.name = "DefenceNote"
	def_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var df_how: Array = [null]
	var sync_def := func(key: String) -> void:
		var loose_on := key == "loose" or key == "both"
		var cover_on := key == "cover" or key == "both"
		calls["interceptor_id"] = loose_pick if loose_on else ""
		calls["minder_id"] = minder_pick if cover_on else ""
		def_note.text = MatchNotes.defence_setup_line(key,
				GameDB.player_display_name_by_id(loose_pick, "your best interceptor"),
				GameDB.player_display_name_by_id(minder_pick, "a forward"),
				GameDB.player_display_name(opp_spare) if not opp_spare.is_empty() else "")
		if df_how[0] != null and is_instance_valid(df_how[0]):
			(df_how[0] as Control).visible = cover_on
			if cover_on:
				_fill_df_duel(df_how[0], sim, calls, opp_spare)
	var def_pick := _choice_grid("DefenceSetupPicker", def_opts, calls, "defence", 2, sync_def)
	var def_block := _call_block("Defensive set-up", def_pick)
	def_block.name = "DefenceBlock"
	var def_ask := UiKit.lbl(MatchNotes.defence_question(), UiKit.BODY, UiKit.TEXT, true)
	def_ask.name = "DefenceQuestion"
	def_ask.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	def_block.add_child(def_ask)
	def_block.move_child(def_ask, 1)
	def_block.add_child(def_note)
	# From quarter time on: how your loose man and your forward on theirs are going.
	var loose_now := str(sim.interceptor[_my_side])
	if q > 1 and loose_now != "":
		var tally := _say(MatchNotes.loose_tally_line(GameDB.player_display_name_by_id(loose_now, "Your loose man"),
				maxi(0, sim.intercepts_since_call(_my_side))), UiKit.NOTE, UiKit.TEXT)
		tally.name = "LooseTally"
		tally.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		def_block.add_child(tally)
	if q > 1 and not opp_spare.is_empty():
		var how := UiKit.vbox(4)
		how.name = "DfHowItsGoing"
		def_block.add_child(how)
		df_how[0] = how
	sync_def.call(str(calls["defence"]))

	# The rest of the calls, all in view (director, 2026-10-09: no "More
	# calls" button).
	var more: VBoxContainer = col_c
	var syn_label: Control = _synergy_block()
	if syn_label != null:
		syn_label.set_meta("break_unit", true)
		more.add_child(syn_label)
		group.call("facts", syn_label)
	more.add_child(def_block)
	group.call("df", def_block)

	# Wide: the pep talk sits under the tag, so every column fits a 720-unit
	# screen. Rotations are no longer a call (director, 2026-11-03): they
	# follow the season plan and the legs (MatchSim.auto_rotation).
	var tail: VBoxContainer = col_b
	var pep_note := UiKit.vbox(3)
	pep_note.name = "PepNote"
	var sync_pep := func(key: String) -> void:
		_fill_note_lines(pep_note, CoachReport.pep_summary(key))
	# Four talks: a two-column grid of their full names, which fits a 360 phone
	# and the PC column alike (one row of four ran off a phone).
	var pep := _choice_grid("PepPicker", PEP_TALKS, calls, "pep", 2, sync_pep)
	var pep_block := _call_block("Pep talk", pep)
	col_a.add_child(pep_block)
	col_a.add_child(pep_note)
	group.call("pep", pep_block)
	group.call("pep", pep_note)
	sync_pep.call(str(calls["pep"]))

	if wide:
		def_block.get_parent().remove_child(def_block)
		tail.add_child(def_block)
	var legs := _legs_view()
	(rep if rep != v else tail).add_child(legs)
	group.call("facts", legs)
	if calls_by.has("facts"):
		(calls_by["facts"] as Array).erase(legs)
		(calls_by["facts"] as Array).push_front(legs)
	# The synergies line is about the two sides' strengths, like the legs line:
	# on a PC sheet it sits right under it, never alone at the top of a column
	# without a heading (BOSS QC, 2026-10-11).
	if wide and syn_label != null and syn_label.get_parent() != null:
		syn_label.get_parent().remove_child(syn_label)
		syn_label.remove_meta("break_unit")
		(rep if rep != v else tail).add_child(syn_label)
	# Who is playing well, on the break (director, 2026-10-11): on a PC in the
	# report column; on a phone below the choices, so nothing the next quarter
	# depends on is pushed under the pinned Start button.
	# Before the first ball-up nobody has played: no zeros (director, 2026-10-14).
	if q > 1:
		(rep if rep != v else tail).add_child(_best_so_far())

	# Every pre-match call sits before Start, the side included (TODO row 25).
	var start := UiKit.btn("Start quarter" if q > 1 else "Start", UiKit.HEADING, true)
	start.name = "StartQuarter"
	start.custom_minimum_size = Vector2(0, 48)
	var take_calls := func() -> Dictionary:
		return {
			"gameplan": str(calls["gameplan"]),
			"focus_mid": str(calls["focus_mid"]),
			"focus_fwd": str(calls["focus_fwd"]),
			"focus_def": str(calls["focus_def"]),
			"tag_id": str(calls["tag_id"]),
			"tagger_id": str(calls["tagger_id"]),
			"interceptor_id": str(calls["interceptor_id"]),
			"interceptor_set": str(calls["interceptor_id"]) != loose_was,
			"spare_accountable": str(calls["minder_id"]) != "",
			"spare_minder_id": str(calls["minder_id"]),
			"tag_set": str(calls["tag_id"]) != tag_was,
			"minder_set": str(calls["minder_id"]) != minder_was,
			"pep": str(calls["pep"]),
		}
	start.pressed.connect(func():
		var t: Dictionary = take_calls.call()
		_close_coach()
		_simulate_next_quarter(t))
	# One primary action on the break; the way out is said as words.
	var skip := UiKit.text_action("Skip to full time", UiKit.BODY)
	skip.pressed.connect(_on_skip)
	if one_line:
		_mount_one_line({"box": box, "store": store, "calls": calls, "wide": wide, "start": start, "skip": skip,
				"stats_pc": stats_pc, "tagger": tagger, "my_mids": my_mids, "who_wb": who_wb, "who_hook": who_hook,
				"opp_spare": opp_spare, "sim": sim, "syn": syn_label})
	elif wide:
		# A PC sheet's actions sit together at the right, not as full-width bars.
		var acts := UiKit.hbox(12)
		acts.alignment = BoxContainer.ALIGNMENT_END
		acts.add_child(_skip_note(sim.current_quarter, true))
		skip.custom_minimum_size = Vector2(220, 48)
		start.custom_minimum_size = Vector2(300, 48)
		if stats_pc != null:
			stats_pc.custom_minimum_size = Vector2(180, 48)
			acts.add_child(stats_pc)
		acts.add_child(skip)
		acts.add_child(start)
		box["footer"].add_child(acts)
		# A mouse, not a thumb: the choices sit 34 tall on the PC sheet, so the
		# fullest break (both loose men, a tag card, your tally) fits 1280x720.
		for b in cols.find_children("*", "Button", true, false):
			if (b as Button).custom_minimum_size.y == 44.0:
				(b as Button).custom_minimum_size.y = 40.0
		_break_pack_cols = [rep, col_a, col_b, col_c] if rep != v else [col_a, col_b, col_c]
		_break_reading = []
		if rep != v:
			# The pane's scrollbar is always there: with a tag picked, Who tags opens and the
			# pane may scroll, and a bar appearing then would narrow every column (director,
			# 2026-10-14: nothing moves sideways after the tag tap).
			var pane_up: Node = cols
			while pane_up != null and not (pane_up is ScrollContainer):
				pane_up = pane_up.get_parent()
			if pane_up != null:
				(pane_up as ScrollContainer).vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_ALWAYS
			_deal_calls.call_deferred(_break_pack_cols, calls_by)
		else:
			_balance_break_columns.call_deferred(_break_pack_cols)
	else:
		box["footer"].add_child(start)
		box["footer"].add_child(skip)
		v.add_child(_skip_note(q, false))
	if q == 1 and GameState.match_day_setup_open():
		var side := UiKit.text_action("Change the side", UiKit.BODY)
		side.name = "ChangeSide"
		side.custom_minimum_size = skip.custom_minimum_size
		side.pressed.connect(func():
			# Your calls go into the match before you leave, so they are still
			# set when you come back (GameState.rebuild_pending_side).
			var t: Dictionary = take_calls.call()
			if bool(t["interceptor_set"]):
				sim.coach_interceptor(_my_side, str(t["interceptor_id"]))
			sim.set_tactics(_my_side, t)
			GameState.side_from_match = true
			_close_coach()
			Router.go("selection"))
		var at := skip.get_parent()
		at.add_child(side)
		at.move_child(side, skip.get_index())
	# A call the quarter broke brightens twice (Feel; never a nag).
	for picker in MatchNotes.broken_calls(_res, sim.injuries, _my_side, q, _last_tactics):
		var found := overlay.find_child(str(picker) + "*", true, false)
		if found != null and one_line:
			# The call's row brightens: its picker is behind the row.
			var up: Node = found
			while up != null and not str(up.name).begins_with("CallBody_"):
				up = up.get_parent()
			var row: Node = overlay.find_child("CallRow_" + str(up.name).trim_prefix("CallBody_"), true, false) if up != null else null
			if row != null:
				UiKit.attention(row as CanvasItem)
		elif found != null:
			UiKit.attention(found.get_parent() as CanvasItem)


# ---------------------------------------------------------------------------
# The break from quarter time on: one line a call (director, 2026-10-14)
# ---------------------------------------------------------------------------
## What a call's sheet is headed, and what its row says it is.
const CALL_TITLES := {"plan": "Game plan", "pep": "Pep talk", "tag": "Tag",
		"def": "Defensive set-up", "pt": "Play through"}
const CALL_ROW_LABELS := {"pt": "Play through (forward, midfield, back)"}


## "How it's going" for the Defensive forward and their loose defender, this
## match so far: both ratings side by side in the scoreboard face under their
## names in club colour, then the contests between them and his intercepts.
func _fill_df_duel(box: VBoxContainer, sim: MatchSim, calls: Dictionary, roamer: Dictionary) -> void:
	UiKit.clear(box)
	var df_id := str(calls["minder_id"])
	var roamer_id := str(roamer.get("id", ""))
	var d := MatchNotes.df_duel(_res, df_id, roamer_id)
	var inks := UiKit.club_ink_pair(str(_res["home"]), str(_res["away"]))
	var head := UiKit.lbl("How it's going", UiKit.SMALL, UiKit.TEXT, true)
	head.name = "DfHeading"
	box.add_child(head)
	var row := UiKit.hbox(12)
	row.name = "DfRatings"
	var who := [[df_id, _my_side], [roamer_id, 1 - _my_side]]
	for w in who:
		if str(w[0]) == "":
			continue
		var col := UiKit.vbox(0)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var nm := UiKit.ellipsis(_surname(GameDB.player_display_name_by_id(str(w[0]), "Player")), UiKit.NAME,
				UiKit.club_name_colour(inks[int(w[1])]), true)
		nm.name = "DfName_" + str(w[0])
		col.add_child(nm)
		var rr := UiKit.figure(MatchNotes.rating_text(MatchNotes.match_rating(_res, str(w[0]))), UiKit.NUMBER)
		rr.name = "DfRating_" + str(w[0])
		var rrow := UiKit.hbox(6)
		rrow.add_child(rr)
		var rtag := UiKit.lbl("rating", UiKit.SECONDARY, UiKit.MUTED)
		rtag.size_flags_vertical = Control.SIZE_SHRINK_END
		rrow.add_child(rtag)
		col.add_child(rrow)
		row.add_child(col)
	box.add_child(row)
	var lines := MatchNotes.df_duel_lines(d,
			_surname(GameDB.player_display_name_by_id(df_id, "")),
			_surname(GameDB.player_display_name_by_id(roamer_id, "")))
	for i in range(lines.size()):
		if str(lines[i]) == "":
			continue
		var l := UiKit.lbl(str(lines[i]), UiKit.BODY, UiKit.TEXT)
		l.name = "DfLine_%d" % i
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(l)


## Lays the break out as one line a call. Every call was built by
## _show_coach_box into c["store"]; here each becomes a body (its choices, its
## follow-up and its words) behind a row that shows its answer. A phone opens a
## call as its own sheet; a PC shows the chosen call beside the list, in room
## kept for the tallest, so nothing appears or shoves the page. "Who tags" lives
## inside the Tag call: a line with Change on a phone (its cards are their own
## sheet), its cards in the pane on a PC, there from the start.
func _mount_one_line(c: Dictionary) -> void:
	var box: Dictionary = c["box"]
	var v: VBoxContainer = box["body"]
	var overlay: Control = box["overlay"]
	var store: VBoxContainer = c["store"]
	var calls: Dictionary = c["calls"]
	var wide: bool = c["wide"]
	var sim: MatchSim = c["sim"]
	var take := func(nm: String, parent := false) -> Control:
		var n: Control = store.find_child(nm, true, false)
		if n != null and parent:
			n = n.get_parent() as Control
		return n
	var bodies := {}
	var order: Array = []
	var body := func(key: String, parts: Array) -> void:
		var b := UiKit.vbox(4 if wide else 6)
		b.name = "CallBody_" + key
		for p in parts:
			if p == null:
				continue
			if (p as Node).get_parent() != null:
				(p as Node).get_parent().remove_child(p)
			b.add_child(p)
		if b.get_child_count() == 0:
			b.free()
			return
		# The sheet or the pane says what the call is: its own small heading
		# goes (the three play-through calls keep theirs: one heading each).
		if key != "pt":
			var h: Node = b.find_child("CallHeading", true, false)
			if h != null:
				(h as Control).visible = false
		bodies[key] = b
		order.append(key)
		store.add_child(b)

	# Who tags, inside the Tag call from the start.
	var who_wb: Control = c["who_wb"]
	var who_line: HBoxContainer = null
	var who_name: Label = null
	var who_sub: Label = null
	var who_change: Button = null
	if who_wb != null and not wide:
		who_line = UiKit.hbox(8)
		who_line.name = "WhoTagsLine"
		var wc := UiKit.vbox(0)
		wc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		wc.add_child(UiKit.line("Who tags", UiKit.SECONDARY, UiKit.MUTED))
		who_name = UiKit.ellipsis("", UiKit.NAME, UiKit.TEXT, true)
		who_name.name = "WhoTagsName"
		wc.add_child(who_name)
		who_sub = UiKit.line("", UiKit.SECONDARY, UiKit.MUTED)
		who_sub.name = "WhoTagsSub"
		wc.add_child(who_sub)
		who_line.add_child(wc)
		who_change = UiKit.text_action("Change", UiKit.SECONDARY)
		who_change.name = "WhoTagsChange"
		who_change.pressed.connect(func():
			_open_break_sheet("who", "Who tags %s?" % GameDB.player_display_name_by_id(str(calls["tag_id"]), "him"),
					[who_wb], store))
		who_line.add_child(who_change)
		var wh: Node = who_wb.find_child("CallHeading", true, false)
		if wh != null:
			(wh as Control).visible = false
	if who_wb != null:
		who_wb.visible = true
	(c["who_hook"] as Array)[0] = func() -> void:
		var has_tag := str(calls["tag_id"]) != ""
		if who_name != null and is_instance_valid(who_name):
			var who = (c["my_mids"] as Dictionary).get(str(calls["tagger_id"]), c["tagger"])
			who_name.text = GameDB.player_display_name(who) if has_tag and who != null else "Nobody"
			who_sub.text = "There is no tag." if not has_tag else ("Your assistant's pick" if str(calls["tagger_id"]) == "" else "Your pick")
			who_change.disabled = not has_tag
		elif who_wb != null and is_instance_valid(who_wb):
			who_wb.modulate.a = 1.0 if has_tag else 0.4
			for b in who_wb.find_children("*", "Button", true, false):
				(b as Button).disabled = not has_tag

	var fact: Label = null
	var fact_text := _tag_fact_line(sim)
	if fact_text != "":
		fact = UiKit.lbl(fact_text, UiKit.BODY, UiKit.TEXT)
		fact.name = "TagFact"
		fact.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.call("plan", [take.call("PlanPicker", true), take.call("PlanNote"), _calls_record("gameplan"), c["syn"]])
	body.call("pep", [take.call("PepPicker", true), take.call("PepNote"), _calls_record("pep")])
	body.call("tag", [fact, take.call("TagPicker", true), who_wb if wide else who_line, take.call("TagNote")])
	var through: Array = []
	for slot in MatchNotes.FOCUS_ORDER:
		through.append(take.call("FocusPicker_" + str(slot), true))
	body.call("pt", through)
	body.call("def", [take.call("DefenceBlock")])
	((c["who_hook"] as Array)[0] as Callable).call()

	# The rows: what each call is, and its answer now.
	var rows := UiKit.vbox(0)
	rows.name = "CallRows"
	var row_of := {}
	for key in order:
		var r := _call_row(str(key), str(CALL_ROW_LABELS.get(key, CALL_TITLES[key])))
		row_of[key] = r
		rows.add_child(r)
		rows.add_child(UiKit.rule())
	var first := {}
	for key in order:
		first[key] = _call_answer(str(key), calls, c)
	_break_refresh = func() -> void:
		if not is_instance_valid(rows):
			return
		for key in order:
			var r: Button = row_of[key]
			var a := _call_answer(str(key), calls, c)
			NameInk.set_line(r.get_meta("answer") as RichTextLabel, a, _names_named(_answer_ids(str(key), calls, c)))
			var changed := a != str(first[key])
			(r.get_meta("changed") as Label).visible = changed
			(r.get_meta("rule") as ColorRect).color = UiKit.club_vivid(str(GameState.my_club), UiKit.SURFACE) if changed else Color.TRANSPARENT
	_break_refresh.call()

	var quarter_head: Control = take.call("QuarterHeading")
	var facts: Control = take.call("QuarterFacts")
	var did_head: Control = take.call("CallsDidHeading")
	var did: Control = take.call("CallsDid")
	var legs: Control = take.call("LegsView")
	var best: Control = take.call("BestSoFar")
	var start: Button = c["start"]
	var skip: Button = c["skip"]
	var put := func(to: Control, n: Control) -> void:
		if n == null:
			return
		if n.get_parent() != null:
			n.get_parent().remove_child(n)
		to.add_child(n)
	if not wide:
		# A phone: the quarter, what your calls did, the rows. Best so far and
		# the full numbers are one tap away, beside the heading.
		var head := UiKit.hbox(8)
		if quarter_head != null:
			quarter_head.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			put.call(head, quarter_head)
		var stats: Control = take.call("BreakStats")
		var open_best := UiKit.text_action("Best so far", UiKit.BODY)
		open_best.name = "BestSoFarOpen"
		# In the sheet the two ways to the full numbers share one row of text
		# links, not two more bars above Done.
		var links := UiKit.hbox(8)
		links.name = "BreakLinks"
		var all_link: Control = best.find_child("BestSoFarAll", true, false) if best != null else null
		for lk in [stats, all_link]:
			if lk == null:
				continue
			if lk.get_parent() != null:
				lk.get_parent().remove_child(lk)
			lk.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			_outline_link(lk as Button)
			links.add_child(lk)
		open_best.pressed.connect(func(): _open_break_sheet("best", "", [best, links], store))
		head.add_child(open_best)
		v.add_child(head)
		for n in [facts, legs]:
			put.call(v, n)
		# What your calls did can run long (every call, tag and lasting moment):
		# on a phone it is one row that opens the lot in a sheet, so the break
		# keeps the same height whatever the quarter threw up.
		if did != null:
			if did_head != null and did_head.get_parent() != null:
				did_head.get_parent().remove_child(did_head)
			if did.get_parent() != null:
				did.get_parent().remove_child(did)
			store.add_child(did)
			var open_did := UiKit.text_action("What your calls did", UiKit.BODY)
			open_did.name = "CallsDidOpen"
			open_did.alignment = HORIZONTAL_ALIGNMENT_LEFT
			var did_note: Node = store.find_child("CallsDidNote", true, false)
			open_did.pressed.connect(func(): _open_break_sheet("did", "What your calls did", [did_note, did], store))
			v.add_child(open_did)
		v.add_child(rows)
		for key in order:
			var k := str(key)
			(row_of[key] as Button).pressed.connect(func(): _open_break_sheet(k, str(CALL_TITLES[k]), [bodies[k]], store))
		var one := UiKit.hbox(8)
		start.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		skip.custom_minimum_size = Vector2(0, 48)
		one.add_child(skip)
		one.add_child(start)
		box["footer"].add_child(one)
		v.add_child(_skip_note(sim.current_quarter, false))
	else:
		# A PC: the quarter and Best so far, the rows, and the chosen call beside
		# them. The pane keeps the room of its tallest call, so choosing another
		# row never moves the sheet.
		var cols := UiKit.hbox(28)
		cols.name = "BreakColumns"
		var left := UiKit.vbox(6)
		var mid := UiKit.vbox(6)
		var right := UiKit.vbox(6)
		for col in [left, mid, right]:
			col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			col.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
			cols.add_child(col)
		right.size_flags_stretch_ratio = 1.15
		for n in [quarter_head, facts, legs]:
			put.call(left, n)
		if did_head != null:
			left.add_child(UiKit.spacer(4))
		for n in [did_head, did]:
			put.call(left, n)
		left.add_child(UiKit.spacer(4))
		put.call(left, best)
		var next_head := UiKit.section("Next quarter")
		mid.add_child(next_head)
		mid.add_child(rows)
		var pane_title := UiKit.section("")
		pane_title.name = "CallPaneTitle"
		right.add_child(pane_title)
		var pane := MarginContainer.new()
		pane.name = "CallPane"
		right.add_child(pane)
		for key in order:
			put.call(pane, bodies[key])
		v.add_child(cols)
		var plain := UiKit.style(Color.TRANSPARENT, 8, 0)
		plain.set_border_width_all(0)
		var chosen_sb := UiKit.style(Color.TRANSPARENT, 8, UiKit.RADIUS, UiKit.TEXT)
		chosen_sb.set_border_width_all(2)
		var select := func(key: String) -> void:
			pane_title.text = str(CALL_TITLES[key])
			pane.set_meta("call", key)
			for k in order:
				(bodies[k] as Control).visible = str(k) == key
				# A flat button draws no surface: the chosen row needs its outline.
				(row_of[k] as Button).flat = false
				for state in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
					(row_of[k] as Button).add_theme_stylebox_override(state, chosen_sb if str(k) == key else plain)
		for key in order:
			var k := str(key)
			(row_of[key] as Button).pressed.connect(func(): select.call(k))
		var acts := UiKit.hbox(12)
		acts.alignment = BoxContainer.ALIGNMENT_END
		acts.add_child(_skip_note(sim.current_quarter, true))
		skip.custom_minimum_size = Vector2(220, 48)
		start.custom_minimum_size = Vector2(300, 48)
		var stats_pc: Button = c["stats_pc"]
		if stats_pc != null:
			stats_pc.custom_minimum_size = Vector2(180, 48)
			acts.add_child(stats_pc)
		acts.add_child(skip)
		acts.add_child(start)
		box["footer"].add_child(acts)
		# A mouse, not a thumb: the choices sit a little shorter on the PC sheet.
		for b in cols.find_children("*", "Button", true, false):
			if (b as Button).custom_minimum_size.y == 44.0 and not str(b.name).begins_with("CallRow_"):
				(b as Button).custom_minimum_size.y = 40.0
		# Every call is laid out once, unseen, so the pane can keep the room of
		# the tallest; then only the first shows.
		pane.modulate.a = 0.0
		_settle_call_pane.call_deferred(pane, select, str(order[0]) if not order.is_empty() else "")
	v.add_child(store)
	overlay.set_meta("one_line", true)


## The PC pane measures every call once, keeps the tallest one's room and shows
## the first call.
func _settle_call_pane(pane: MarginContainer, select: Callable, first_key: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	if not is_instance_valid(pane):
		return
	pane.custom_minimum_size.y = pane.get_combined_minimum_size().y
	if first_key != "":
		select.call(first_key)
	pane.modulate.a = 1.0


## One call as one row: what it is, quietly, and its answer in bold under it.
## A call changed at this break carries your club's colour down its edge and
## says so. The whole row is the tap.
func _call_row(key: String, label: String) -> Button:
	var b := UiKit.text_action("", UiKit.NAME)
	b.name = "CallRow_" + key
	b.custom_minimum_size = Vector2(0, 44)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var h := UiKit.hbox(8)
	b.add_child(h)
	h.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 2.0
	h.offset_right = -6.0
	var rule := ColorRect.new()
	rule.name = "RowRule"
	rule.custom_minimum_size = Vector2(4, 0)
	rule.color = Color.TRANSPARENT
	h.add_child(rule)
	var col := UiKit.vbox(0)
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var top := UiKit.hbox(6)
	var what := UiKit.line(label, UiKit.SECONDARY, UiKit.MUTED)
	what.name = "RowLabel"
	top.add_child(what)
	var changed := UiKit.line("· changed this break", UiKit.SECONDARY, UiKit.TEXT)
	changed.name = "RowChanged"
	changed.visible = false
	top.add_child(changed)
	col.add_child(top)
	var answer := NameInk.rich(UiKit.NAME, UiKit.TEXT, true, false)
	answer.name = "RowAnswer"
	answer.clip_contents = true
	answer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_child(answer)
	h.add_child(col)
	var chev := UiKit.line("›", UiKit.HEADING, UiKit.MUTED)
	chev.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	chev.size_flags_vertical = Control.SIZE_EXPAND_FILL
	h.add_child(chev)
	for n in b.find_children("*", "Control", true, false):
		(n as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.set_meta("answer", answer)
	b.set_meta("changed", changed)
	b.set_meta("rule", rule)
	return b


## "Max Gawn" as "M. Gawn": a row has one line for two names.
static func _initial_name(full: String) -> String:
	var parts := full.split(" ", false, 1)
	return full if parts.size() < 2 else "%s. %s" % [parts[0].left(1), parts[1]]


static func _surname(full: String) -> String:
	var parts := full.split(" ", false, 1)
	return full if parts.size() < 2 else parts[1]


## A call's answer as its row says it, from the calls as they stand.
func _call_answer(key: String, calls: Dictionary, c: Dictionary) -> String:
	var sim: MatchSim = c["sim"]
	var named := func(id: String, none: String) -> String:
		return none if id == "" else _initial_name(GameDB.player_display_name_by_id(id, none))
	match key:
		"plan":
			for g in GAMEPLANS:
				if str(g[0]) == str(calls["gameplan"]):
					return str(g[1])
			return str(calls["gameplan"])
		"pep":
			for t in PEP_TALKS:
				if str(t[0]) == str(calls["pep"]):
					return str(t[1])
			return str(calls["pep"])
		"tag":
			if str(calls["tag_id"]) == "":
				return "No tag"
			var target: String = named.call(str(calls["tag_id"]), "their player")
			var who = (c["my_mids"] as Dictionary).get(str(calls["tagger_id"]), c["tagger"])
			return target if who == null else "%s, by %s" % [target, _initial_name(GameDB.player_display_name(who))]
		"def":
			return MatchNotes.defence_answer(str(calls["defence"]))
		"pt":
			# Same order as the row's label: forward, midfield, back. An empty
			# slot says "no one", so each name stays under its own heading.
			var who_through := PackedStringArray()
			var any_through := false
			for slot in MatchNotes.FOCUS_ORDER:
				any_through = any_through or str(calls[slot]) != ""
				who_through.append(named.call(str(calls[slot]), "no one"))
			return ", ".join(who_through) if any_through else "No one"
	return ""


## The players a call's answer names (by id), so its row can ink a surname two
## clubs share ("McDonald on van Rooyen") from who he is, not from the word.
func _answer_ids(key: String, calls: Dictionary, c: Dictionary) -> Array:
	var sim: MatchSim = c["sim"]
	var ids: Array = []
	match key:
		"tag":
			ids = [str(calls["tag_id"]), str(calls["tagger_id"])]
		"def":
			ids = [str(calls["interceptor_id"]), str(calls["minder_id"])]
		"pt":
			for slot in MatchNotes.FOCUS_ORDER:
				ids.append(str(calls[slot]))
	return ids.filter(func(i): return str(i) != "")


## `_names()` with the surname of each of these players pinned to his own club:
## a surname both clubs carry is left plain by the index (a guess could be
## wrong), but a line that says which player it means can say whose he is. Two
## of them sharing one surname across the clubs stay plain.
func _names_named(ids: Array) -> Dictionary:
	var out := _names().duplicate()
	var seen := {}
	var clash := {}
	for id in ids:
		var code := _club_code_of(str(id))
		var sur := _surname(GameDB.player_display_name_by_id(str(id), ""))
		if code == "" or sur == "":
			continue
		if seen.has(sur) and str(seen[sur]) != code:
			clash[sur] = true
		seen[sur] = code
	for sur in seen:
		if not clash.has(sur):
			out[sur] = seen[sur]
	return out


## The club (code) a player of this match plays for, "" if he is in neither side.
func _club_code_of(id: String) -> String:
	for side in [0, 1]:
		for r in _roster_side(side):
			if str(r.get("id", "")) == id:
				return str(_res["home"] if side == 0 else _res["away"])
	return ""


## The fact beside the tag: their busiest midfielder so far ("" before anyone
## has had the ball). A fact, never a suggestion.
func _tag_fact_line(sim: MatchSim) -> String:
	var top := ""
	var most := 0
	for r in _roster_side(1 - _my_side):
		if not _taggable_now(sim, r) or not _listed_midfielder(sim, r):
			continue
		var st: Dictionary = (_res.get("players", {}) as Dictionary).get(str(r["id"]), {})
		var n := int(float(st.get("disposals", 0.0)))
		if n > most:
			most = n
			top = GameDB.player_display_name(r)
	return "" if top == "" else "%s has had %d disposal%s, the most of their midfielders." % [
			top, most, "" if most == 1 else "s"]


## A sheet over the break: one call (or who tags, or Best so far) with Done.
## Its parts are the break's own blocks, lent to the sheet and handed back to
## `home` when it closes, so a pick made here is the pick the quarter starts
## with. Back closes the top sheet (handle_back).
## What Skip to full time keeps and drops (G11; GateOdds.skip_line): beside
## the actions on a PC, at the foot of the calls on a phone.
func _skip_note(q: int, wide: bool) -> Label:
	var l := UiKit.lbl(GateOdds.skip_line(q), UiKit.NOTE, UiKit.TEXT)
	l.name = "SkipNote"
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	if wide:
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return l


func _open_break_sheet(node_name: String, title: String, parts: Array, home: Node) -> void:
	# Best so far is a bottom sheet: the thumb's end of the screen, not floating.
	var box := UiKit.modal_box(_over, 640.0, 0.0, _wash(), node_name == "best", node_name == "best")
	var ov: Control = box["overlay"]
	ov.name = "CallSheet_" + node_name
	# The break behind a sheet is out of sight: nothing of it reads, or shows
	# half-cut, past the sheet's edge.
	(ov as ColorRect).color = Color(0, 0, 0, 1.0)
	var v: VBoxContainer = box["body"]
	if title != "":
		var t := UiKit.heading(title, UiKit.H1)
		t.name = "CallSheetTitle"
		v.add_child(t)
	for p in parts:
		if p == null or not is_instance_valid(p):
			continue
		if (p as Node).get_parent() != null:
			(p as Node).get_parent().remove_child(p)
		# Best so far: the links sit at the thumb's end with Done, the votes above.
		(box["footer"] as Node if node_name == "best" and (p as Node).name == "BreakLinks" else v).add_child(p)
	var done := UiKit.btn("Done", UiKit.HEADING, true)
	done.name = "CallDone"
	done.custom_minimum_size = Vector2(0, 48)
	done.pressed.connect(_close_top_break_sheet)
	if node_name == "best":
		# Done is the one primary action, in the club fill.
		_club_fill_button(done)
		box["footer"].add_child(done)
		var wash_best := UiKit.team_wash() if _wash() == UiKit.AUTO_COLOUR else _wash()
		UiKit.edge_fade(box["body"].get_parent() as ScrollContainer, Color(wash_best, 0.2))
		_break_sheets.append({"overlay": ov, "close": _best_close(parts, home, ov)})
		return
	# Done stands 16 px clear of the links above it (the body's own gap is 8).
	v.add_child(UiKit.spacer(8))
	_club_fill_button(done)
	box["footer"].add_child(done)
	var wash_col := UiKit.team_wash() if _wash() == UiKit.AUTO_COLOUR else _wash()
	UiKit.edge_fade(box["body"].get_parent() as ScrollContainer, Color(wash_col, 0.2))
	_break_sheets.append({"overlay": ov, "close": _best_close(parts, home, ov)})


## A club-colour button on a sheet washed in a club colour needs an edge, and
## a fill that stands off the sheet: the club colour lifted until it reads
## 3:1 or better against the panel (never a dark purple on dark purple).
func _club_fill_button(done: Button) -> void:
	var lead := UiKit.team_colour()
	var fill := lead
	var v_up := lead.v
	for i in 20:
		if UiKit.contrast(fill, UiKit.tinted("sheet", lead)) >= 3.0:
			break
		v_up = minf(1.0, v_up + 0.05)
		fill = Color.from_hsv(lead.h, lead.s, v_up)
	for state in ["normal", "hover", "pressed", "hover_pressed"]:
		var sb := done.get_theme_stylebox(state).duplicate() as StyleBoxFlat
		sb.bg_color = fill if state == "normal" else (fill.lightened(0.08) if state == "hover" else fill.darkened(0.08))
		sb.set_border_width_all(2)
		sb.border_color = Color(UiKit.TEXT, 0.55)
		done.add_theme_stylebox_override(state, sb)
	for k in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		done.add_theme_color_override(k, Color.WHITE if UiKit.contrast(fill, Color.WHITE) >= UiKit.contrast(fill, Color("161512")) else Color("161512"))


## Closing a break sheet hands its parts back to the break they came from.
func _best_close(parts: Array, home: Node, ov: Control) -> Callable:
	return func() -> void:
		for p in parts:
			if p == null or not is_instance_valid(p):
				continue
			if (p as Node).get_parent() != null:
				(p as Node).get_parent().remove_child(p)
			if is_instance_valid(home):
				home.add_child(p)
		ov.queue_free()
		if _break_refresh.is_valid():
			_break_refresh.call()


## A text link made a real button: a 48 px outlined bar, easy to hit.
func _outline_link(b: Button) -> void:
	b.flat = false
	b.custom_minimum_size = Vector2(0, 48)
	var sb := UiKit.style(UiKit.SURFACE, 8, UiKit.RADIUS, Color(UiKit.TEXT, 0.45))
	sb.set_border_width_all(1)
	var hover := sb.duplicate() as StyleBoxFlat
	hover.bg_color = UiKit.SURFACE.lightened(0.06)
	var pressed := sb.duplicate() as StyleBoxFlat
	pressed.bg_color = UiKit.SURFACE.lightened(0.12)
	b.add_theme_stylebox_override("normal", sb)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("hover_pressed", pressed)
	b.add_theme_color_override("font_pressed_color", UiKit.TEXT)


func _close_top_break_sheet() -> void:
	if _break_sheets.is_empty():
		return
	var s: Dictionary = _break_sheets.pop_back()
	if is_instance_valid(s["overlay"]):
		(s["close"] as Callable).call()


func _close_break_sheets() -> void:
	while not _break_sheets.is_empty():
		_close_top_break_sheet()


## The PC break's call columns and its calls in the order it was built, so a
## call shown later (Who tags, once there is a tag) packs the break again.
var _break_pack_cols: Array = []
var _break_reading: Array = []


## A PC break's calls read in one order down and across the call columns;
## where each column ends follows what is in it this break (a loose defender
## of theirs, a second ruck), so the tallest column is as short as it can be
## and nothing scrolls on a 720-unit screen. A call keeps its words under it.
func _balance_break_columns(cols: Array, again := false) -> void:
	if not again:
		await get_tree().process_frame
	if not is_instance_valid(cols[0]):
		return
	# Packed again (a call shown or hidden since): from the reading order the
	# break was built in, never from the last packing.
	if _break_reading.is_empty():
		for c in cols:
			for n in (c as Node).get_children():
				_break_reading.append(n)
	else:
		for n in _break_reading:
			if is_instance_valid(n):
				(n as Node).get_parent().remove_child(n)
				(cols[0] as Node).add_child(n)
	# Calls in reading order: a call starts a unit; its notes go with it.
	var units := _break_units(cols)
	var sep := float((cols[0] as VBoxContainer).get_theme_constant("separation"))
	var h: Array = _unit_heights(units, sep)
	# Where each column ends, so the tallest column is as short as it can be
	# (every split of the units, in order, into that many columns).
	var n_units := units.size()
	var ends := _best_split(h, cols.size())
	var col := 0
	for k in range(n_units):
		while col < cols.size() - 1 and k >= int(ends[col]):
			col += 1
		var dest: Node = cols[col]
		for n in units[k]:
			(n as Node).get_parent().remove_child(n)
			dest.add_child(n)
	# The reading order is kept while it fits. When even the best run of units
	# is too tall for the screen (both loose men, a tag card, your tally), pack
	# by height instead: the tallest call goes to the shortest column, and each
	# column still lists its calls in reading order.
	if not again:
		await get_tree().process_frame
	if not is_instance_valid(cols[0]):
		return
	var sc: ScrollContainer = null
	var up: Node = cols[0]
	while up != null and sc == null:
		sc = up as ScrollContainer
		up = up.get_parent()
	# Tight counts too: under 8 px to spare, the next line or a longer name
	# would tip it over, so look for the shorter deal.
	if sc == null or (sc.get_child(0) as Control).get_combined_minimum_size().y <= sc.size.y - 8.0:
		return
	var order := range(n_units)
	order.sort_custom(func(a, b): return float(h[a]) > float(h[b]))
	var load_h: Array = []
	var picks: Array = []
	for c in range(cols.size()):
		load_h.append(0.0)
		picks.append([])
	for k in order:
		var lo := 0
		for c in range(1, cols.size()):
			if float(load_h[c]) < float(load_h[lo]):
				lo = c
		load_h[lo] = float(load_h[lo]) + float(h[k])
		(picks[lo] as Array).append(k)
	# Then improve it: move or swap units out of the tallest column while that
	# lowers the tallest column.
	var improved := true
	while improved:
		improved = false
		var tall := 0
		for c in range(1, cols.size()):
			if float(load_h[c]) > float(load_h[tall]):
				tall = c
		var top := float(load_h[tall])
		for k in (picks[tall] as Array).duplicate():
			for c in range(cols.size()):
				if c == tall:
					continue
				if float(load_h[c]) + float(h[k]) < top - 0.5:
					(picks[tall] as Array).erase(k)
					(picks[c] as Array).append(k)
					load_h[tall] = float(load_h[tall]) - float(h[k])
					load_h[c] = float(load_h[c]) + float(h[k])
					improved = true
					break
				for k2 in (picks[c] as Array).duplicate():
					var d := float(h[k]) - float(h[k2])
					if d > 0.5 and float(load_h[c]) + d < top - 0.5:
						(picks[tall] as Array).erase(k)
						(picks[c] as Array).erase(k2)
						(picks[tall] as Array).append(k2)
						(picks[c] as Array).append(k)
						load_h[tall] = float(load_h[tall]) - d
						load_h[c] = float(load_h[c]) + d
						improved = true
						break
				if improved:
					break
			if improved:
				break
	# The greedy answer can sit a whole call above the best there is (Best so
	# far on the fullest PC break: 551 against 532 with the same blocks), so
	# look for the true shortest tallest column before placing anything.
	var exact := _shortest_tallest(h, cols.size(), load_h.max())
	if not exact.is_empty():
		picks = exact
	for c in range(cols.size()):
		(picks[c] as Array).sort()
		for k in picks[c]:
			for n in units[k]:
				(n as Node).get_parent().remove_child(n)
				(cols[c] as Node).add_child(n)
	# Best so far shows three a side on a PC, as on a phone, while the break
	# still fits 720 high; when even the best deal overflows, the third of each
	# side goes (the older two-a-side break) and the calls are dealt again.
	if _coach_overlay == null or not is_instance_valid(_coach_overlay):
		return
	if (sc.get_child(0) as Control).get_combined_minimum_size().y > sc.size.y - 8.0:
		var dropped := false
		for r in _coach_overlay.find_children("BestRow_*", "", true, false):
			if (r as Node).has_meta("best_third"):
				(r as Node).get_parent().remove_child(r)
				(r as Node).queue_free()
				dropped = true
		if dropped:
			_balance_break_columns(cols, true)
			return


## Before the first ball-up on a three-column PC sheet the calls are dealt by what
## they are (director, 2026-10-15: empty space is a defect; "PC is not a big
## phone"): the game plan leads the first column and the tag the second. The
## rest (the pep talk, the defensive set-up, the three play-through calls, and
## the legs and synergies lines) go where they make the three columns most
## alike in height, under what fits 720 high (director, 2026-11-03: three
## columns, none more than a fifth empty).
## Where a call sits is dealt once: a call that opens later (Who tags) grows its
## own column and never moves another call.
const DEAL_FIRST := {"gameplan": 0, "tag": 1}
const DEAL_ORDER := ["gameplan", "tag", "pep", "df", "pt", "facts"]


func _deal_calls(cols: Array, groups: Dictionary) -> void:
	await get_tree().process_frame
	if not is_instance_valid(cols[0]):
		return
	var sep := float((cols[0] as VBoxContainer).get_theme_constant("separation"))
	var keys: Array = []
	for k in DEAL_ORDER:
		if groups.has(k):
			keys.append(k)
	# Anything that was not named (a spacer) is left out of the columns.
	var named := {}
	for k in keys:
		for n in groups[k]:
			named[n] = true
	for c in cols:
		for n in (c as Node).get_children():
			if not named.has(n):
				(n as Control).visible = false
	# What each kind of call takes up: its visible parts and the gaps between.
	var h := {}
	for k in keys:
		var t := 0.0
		for n in groups[k]:
			if (n as Control).visible:
				t += (n as Control).get_combined_minimum_size().y + sep
		h[k] = t
	# The room the columns have: the pane's, less everything else in it.
	var budget := INF
	var sc: ScrollContainer = null
	var up: Node = cols[0]
	while up != null and sc == null:
		sc = up as ScrollContainer
		up = up.get_parent()
	if sc != null:
		var inner := sc.get_child(0) as Control
		var around: float = inner.get_combined_minimum_size().y - (cols[0] as Node).get_parent().get_combined_minimum_size().y
		budget = sc.size.y - around - 8.0
	var free: Array = []
	for k in keys:
		if not DEAL_FIRST.has(k):
			free.append(k)
	# Three columns before the first ball-up (director, 2026-11-03: with four
	# match calls cut, four columns left one 378 tall beside one of 161). The
	# last column built is emptied into the others and leaves the row.
	var n := mini(3, cols.size())
	var base := []
	for i in range(n):
		base.append(0.0)
	for k in keys:
		if DEAL_FIRST.has(k):
			base[int(DEAL_FIRST[k])] += float(h[k])
	# Every way of placing the free kinds: the one that fits the pane and leaves the
	# least empty room under the shortest column (else the shortest tallest).
	var best := []
	var best_score := [INF, INF, INF]
	var total := int(pow(n, free.size()))
	for code in range(total):
		var load_h := base.duplicate()
		var at := []
		var rest := code
		for k in free:
			var c := rest % n
			rest = int(floorf(rest / float(n)))
			at.append(c)
			load_h[c] += float(h[k])
		var mx := float(load_h.max())
		var mn := float(load_h.min())
		var over := 1.0 if mx > budget else 0.0
		var score := [over, mx if over > 0.0 else mx - mn, mx]
		if score < best_score:
			best_score = score
			best = at
	var where := {}
	for k in keys:
		if DEAL_FIRST.has(k):
			where[k] = int(DEAL_FIRST[k])
	for i in range(free.size()):
		where[free[i]] = int(best[i]) if not best.is_empty() else n - 1
	for k in keys:
		for nd in groups[k]:
			if (nd as Node).get_parent() != null:
				(nd as Node).get_parent().remove_child(nd)
			(cols[int(where[k])] as Node).add_child(nd)
	for i in range(n, cols.size()):
		var spare: Node = cols[i]
		if spare.get_parent() != null:
			spare.get_parent().remove_child(spare)
		spare.queue_free()
	cols.resize(n)


func _unit_heights(units: Array, sep: float) -> Array:
	var h: Array = []
	for u in units:
		var t := 0.0
		for n in u:
			# Who tags keeps its room hidden or not, so showing it later never
			# moves a call to another column (director, 2026-10-14).
			if (n as Control).visible or (n as Node).has_meta("break_follow"):
				t += (n as Control).get_combined_minimum_size().y + sep
		h.append(t)
	return h


## Every way of dealing the units (heights h) into `parts` columns, searched
## for the one whose tallest column is shortest; tallest calls first, and a
## branch is dropped the moment it cannot beat the best so far. Returns the
## unit numbers in each column, or an empty array when nothing beats `above`
## (the answer the caller already has).
static func _shortest_tallest(h: Array, parts: int, above: float) -> Array:
	var order := range(h.size())
	order.sort_custom(func(a, b): return float(h[a]) > float(h[b]))
	var state := {"best": above - 0.5, "picks": [], "steps": 0}
	var load_h: Array = []
	var cur: Array = []
	for c in range(parts):
		load_h.append(0.0)
		cur.append([])
	_deal(order, 0, h, load_h, cur, state)
	return state["picks"] as Array


static func _deal(order: Array, i: int, h: Array, load_h: Array, cur: Array, state: Dictionary) -> void:
	state["steps"] = int(state["steps"]) + 1
	if int(state["steps"]) > 400000:
		return
	if i == order.size():
		var top := 0.0
		for l in load_h:
			top = maxf(top, float(l))
		if top < float(state["best"]):
			state["best"] = top
			var copy := []
			for col in cur:
				copy.append((col as Array).duplicate())
			state["picks"] = copy
		return
	var k: int = order[i]
	var seen := []
	for c in range(load_h.size()):
		# Two columns with the same load so far are the same choice.
		if seen.has(float(load_h[c])):
			continue
		seen.append(float(load_h[c]))
		var after := float(load_h[c]) + float(h[k])
		if after >= float(state["best"]):
			continue
		load_h[c] = after
		(cur[c] as Array).append(k)
		_deal(order, i + 1, h, load_h, cur, state)
		(cur[c] as Array).pop_back()
		load_h[c] = after - float(h[k])


## The break's calls as units in reading order: a node marked "break_unit"
## starts one, and the nodes after it (its notes) go with it. A node marked
## "break_follow" is the follow-up to the question before it (Tag, then who
## tags; a loose man, then his cards): it never starts a unit, so a packing
## pass can never put the answer before its question or in another column.
static func _break_units(cols: Array) -> Array:
	var units: Array = []
	for c in cols:
		for n in (c as Node).get_children():
			if units.is_empty() or ((n as Node).has_meta("break_unit") and not (n as Node).has_meta("break_follow")):
				units.append([n])
			else:
				(units[-1] as Array).append(n)
	return units


## Split heights h, in order, into `parts` runs so the largest run is
## smallest; returns where each run ends (exclusive).
static func _best_split(h: Array, parts: int) -> Array:
	var n := h.size()
	var pre := [0.0]
	for x in h:
		pre.append(float(pre[-1]) + float(x))
	# best[p][i]: the tallest column splitting the first i units into p columns.
	var best: Array = []
	var cut: Array = []
	for p in range(parts + 1):
		best.append([])
		cut.append([])
		for i in range(n + 1):
			(best[p] as Array).append(INF)
			(cut[p] as Array).append(0)
	best[0][0] = 0.0
	for p in range(1, parts + 1):
		for i in range(n + 1):
			for j in range(i + 1):
				var top := maxf(float(best[p - 1][j]), float(pre[i]) - float(pre[j]))
				if top < float(best[p][i]) - 0.5:
					best[p][i] = top
					cut[p][i] = j
	var ends: Array = []
	ends.resize(parts)
	var i := n
	for p in range(parts, 0, -1):
		ends[p - 1] = i
		i = int(cut[p][i])
	return ends


## A landscape PC window wide enough for the break sheet's columns (the
## Large and TV screen sizes included).
func _wide_break() -> bool:
	var w := UiKit.view_width(self)
	return ScreenLayout.roomy(w, UiKit.view_height(self))


## The quarter just played: what stood out, what they ran, how your calls
## and your tag came off. Facts only.
func _quarter_view(q: int) -> Control:
	var v := UiKit.vbox(4)
	v.name = "QuarterFacts"
	# The few things that stood out, readable in a glance: no more than
	# three, their plan kept (it is what the next quarter's calls answer).
	# Moments already played out in the feed are not replayed here; the
	# ones that carry on are under "What your calls did".
	var lines: Array = MatchNotes.quarter_facts(_res, _my_side, q, _break_answers())
	var opp_last := _opp_last_plan()
	if opp_last != "":
		lines = lines.slice(0, MatchNotes.MAX_FACTS - 1)
		# What they played, their answer to yours, their mood (RivalRead).
		lines.append(RivalRead.break_line(GameState.pending_sim, _my_side))
	if lines.is_empty():
		lines.append("An even quarter.")
	for t in lines:
		var l := _say(str(t), UiKit.BODY, UiKit.TEXT)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(l)
	return v


## What a call can do about each of their players now: the defender on a key
## forward, your tag, or a midfielder you could tag (only with a midfielder
## of yours on the ground to send). Facts for the break, never advice.
func _break_answers() -> Dictionary:
	var out := {}
	var sim: MatchSim = GameState.pending_sim
	if sim == null:
		return out
	var tagger = sim.tagger_of(_my_side)
	if tagger != null:
		var tag_id := str((sim.tactics[_my_side] as Dictionary).get("tag_id", ""))
		for r in _roster_side(1 - _my_side):
			if not _taggable_now(sim, r):
				continue
			var id := str(r["id"])
			out[id] = {"kind": "tagged", "who": GameDB.player_display_name(tagger)} if id == tag_id 					else {"kind": "tag"}
	return out


## A "Gain:" / "Cost:" style row: the marker bold, the sentence beside it, both
## in full ink (the card-stakes pattern).
func _plan_row(mark: String, text: String, node_name: String, traits := false) -> Control:
	var item := UiKit.hbox(6)
	item.name = node_name
	var mk := UiKit.lbl(mark, UiKit.SECONDARY, UiKit.TEXT, true)
	mk.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	mk.autowrap_mode = TextServer.AUTOWRAP_OFF
	item.add_child(mk)
	# Synergies named here explain themselves on a tap (TraitLink).
	var l: Control = TraitLink.line(text, UiKit.SECONDARY, UiKit.TEXT) if traits else _say(text, UiKit.SECONDARY, UiKit.TEXT)
	l.name = "Text"
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	item.add_child(l)
	return item


## A call's words as short separate lines in full ink: the first bold, then one
## line for each clause ("; " and ": " break a line).
func _fill_note_lines(into: VBoxContainer, text: String) -> void:
	for c in into.get_children():
		into.remove_child(c)
		c.queue_free()
	var bits := text.replace(": ", "|").replace("; ", "|").split("|", false)
	for i in range(bits.size()):
		var piece := str(bits[i]).strip_edges()
		piece = piece.substr(0, 1).to_upper() + piece.substr(1)
		var l := UiKit.lbl(piece, UiKit.BODY if i == 0 else UiKit.SECONDARY, UiKit.TEXT, i == 0)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		into.add_child(l)


## The calls so far this match, one line a quarter played, under a call's words:
## "Q1  Demons: Defensive Press  ·  Crows: Attack Corridor". Game plans are
## shown for both clubs (the break already tells you theirs). Pep talks and
## rotations of the other club are hidden from the coach, so those show only
## yours. Nothing before the first bounce.
func _calls_record(kind: String) -> Control:
	var hist: Array = GameState.pending_sim.tactics_history
	if hist.is_empty():
		return null
	var inks := UiKit.club_ink_pair(str(_res["home"]), str(_res["away"]))
	var v := UiKit.vbox(3)
	v.name = "CallsRecord_" + kind
	v.add_child(UiKit.spacer(6))
	v.add_child(UiKit.lbl("Calls so far", UiKit.SECONDARY, UiKit.TEXT, true))
	for e in hist:
		var plans: Array = e["plans"]
		var side_words := func(side: int) -> String:
			if kind == "gameplan":
				return CoachReport.plan_label(str((plans[side] as Dictionary).get("gameplan", "balanced")))
			return CoachReport.pep_label(str((plans[side] as Dictionary).get("pep", "steady")))
		var sides: Array = [_my_side, 1 - _my_side] if kind == "gameplan" else [_my_side]
		var row := HFlowContainer.new()
		row.add_theme_constant_override("h_separation", 0)
		row.name = "CallsRecordRow_Q%d" % int(e["quarter"])
		var qn := UiKit.lbl("Q%d  " % int(e["quarter"]), UiKit.SECONDARY, UiKit.TEXT, true)
		qn.autowrap_mode = TextServer.AUTOWRAP_OFF
		row.add_child(qn)
		for i in range(sides.size()):
			var side: int = sides[i]
			var code := str((sim_squad_code(side)))
			if i > 0:
				var dot := UiKit.lbl("  ·  ", UiKit.SECONDARY, UiKit.TEXT)
				dot.autowrap_mode = TextServer.AUTOWRAP_OFF
				row.add_child(dot)
			# The club in its own ink, both clubs alike (director A1, 2026-10-14), and
			# named in full as the break's title names it (Fremantle, not Dockers).
			var nm := UiKit.lbl(GameDB.club_name(code) + ": ", UiKit.SECONDARY, UiKit.club_name_colour(inks[side]), true)
			nm.name = "ClubName%d" % i
			nm.autowrap_mode = TextServer.AUTOWRAP_OFF
			row.add_child(nm)
			var w := UiKit.lbl(str(side_words.call(side)), UiKit.SECONDARY, UiKit.TEXT)
			w.name = "CallWords%d" % i
			w.autowrap_mode = TextServer.AUTOWRAP_OFF
			row.add_child(w)
		v.add_child(row)
	return v


func sim_squad_code(side: int) -> String:
	return str((GameState.pending_sim.squads[side] as Squad).code)


func _synergy_names(keys: Array) -> String:
	var out: PackedStringArray = []
	for k in keys:
		out.append(Traits.with_effect(str(k)))
	return ", ".join(out) if not out.is_empty() else "none"


## The two sides' synergies, a block of their own under a heading: yours, then theirs.
func _synergy_block() -> Control:
	var syn: Array = GameState.pending_sim.synergies
	var v := UiKit.vbox(3)
	v.name = "SynergyBlock"
	v.add_child(UiKit.lbl("Synergies", UiKit.SECONDARY, UiKit.TEXT, true))
	v.add_child(_plan_row("Yours:", _synergy_names(syn[_my_side]), "SynYours", true))
	v.add_child(_plan_row("Theirs:", _synergy_names(syn[1 - _my_side]), "SynTheirs", true))
	return v


## The opposition's plan in the quarter just played ("" before the bounce).
func _opp_last_plan() -> String:
	var hist: Array = GameState.pending_sim.tactics_history
	if hist.is_empty():
		return ""
	return str(((hist[hist.size() - 1]["plans"] as Array)[1 - _my_side] as Dictionary).get("gameplan", "balanced"))


## "Your calls" for quarter `q` (0 = the whole match): what each cause was
## worth in expected points, the moments and how they came off, and the tag.
func _calls_view(q: int) -> Control:
	var v := UiKit.vbox(3)
	v.name = "CallsReadout"
	var snaps: Array = _res.get("quarter_teams", [])
	var now: Array = _res.get("impact", [{}, {}])
	var before: Array = [{}, {}]
	if q > 0 and snaps.size() >= q:
		now = (snaps[q - 1] as Dictionary).get("impact", now)
		if q >= 2:
			before = (snaps[q - 2] as Dictionary).get("impact", [{}, {}])
	v.add_child(UiKit.section("What your calls did" + (" in Q%d" % q if q > 0 else "")))
	var lines := CoachReport.impact_lines(now, before, _my_side)
	if not lines.is_empty():
		var wnote := UiKit.lbl(MatchNotes.CALLS_WORTH_NOTE, UiKit.SMALL, UiKit.MUTED)
		wnote.name = "CallsWorthNote"
		wnote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(wnote)
	# Each cause beside what it was worth (director, 2026-10-14: a figure at the far
	# end of the row "divorces the number from the source").
	var worth := GridContainer.new()
	worth.name = "CallsWorth"
	worth.columns = 2
	worth.add_theme_constant_override("h_separation", 24)
	worth.add_theme_constant_override("v_separation", 3)
	worth.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	for l in lines.slice(0, 5):
		var pts := float(l["pts"])
		worth.add_child(UiKit.line(str(l["label"]), UiKit.SECONDARY, UiKit.TEXT))
		worth.add_child(UiKit.line("%+.1f pts" % pts, UiKit.SECONDARY, UiKit.GOOD if pts > 0 else UiKit.BAD, true))
	if worth.get_child_count() > 0:
		v.add_child(worth)
	# The calls, a quarter at a time.
	var moments: Array = _res.get("moments", [])
	var last_q := -1
	for m in moments:
		if q > 0 and int(m.get("q", 0)) != q:
			continue
		var mq := int(m["q"])
		if q == 0 and mq != last_q:
			last_q = mq
			var qh := UiKit.lbl("Q%d" % mq if mq <= 4 else "Extra time", UiKit.SMALL, UiKit.MUTED, true)
			qh.name = "CallsQuarter_%d" % mq
			v.add_child(UiKit.spacer(4))
			v.add_child(qh)
		var clock := _clock_text(mq, int(m["min"]))
		if q == 0:
			clock = clock.substr(clock.find(" ") + 1) if clock.contains(" ") else clock
		var l2 := _say("%s  %s: %s. %s" % [clock,
				str(m.get("title", "")), str(m.get("choice_label", "")), str(m.get("outcome", ""))],
				UiKit.SMALL, UiKit.EMPH if int(m.get("points", 0)) >= 6 else UiKit.TEXT)
		l2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(l2)
	var tag_line := _tag_line(q)
	if tag_line != "":
		v.add_child(_say(tag_line, UiKit.SMALL, UiKit.TEXT))
	if lines.is_empty() and v.get_child_count() == 1:
		v.add_child(UiKit.lbl("An even quarter: no call moved the needle much.", UiKit.SMALL, UiKit.MUTED))
	return v


## How your tag went in quarter q (or the match): the tagged player's line.
func _tag_line(q: int) -> String:
	var hist: Array = _res.get("tactics_history", [])
	var snaps: Array = _res.get("quarter_teams", [])
	var tag_id := ""
	for h in hist:
		if q > 0 and int(h.get("quarter", 0)) != q:
			continue
		var t := str(((h["plans"] as Array)[_my_side] as Dictionary).get("tag_id", ""))
		if t != "":
			tag_id = t
	if tag_id == "":
		return ""
	var d := 0.0
	var g := 0.0
	if q > 0 and snaps.size() >= q:
		var now: Dictionary = ((snaps[q - 1] as Dictionary)["players"] as Dictionary).get(tag_id, {})
		var was: Dictionary = {}
		if q >= 2:
			was = ((snaps[q - 2] as Dictionary)["players"] as Dictionary).get(tag_id, {})
		d = float(now.get("disposals", 0.0)) - float(was.get("disposals", 0.0))
		g = float(now.get("goals", 0.0)) - float(was.get("goals", 0.0))
	else:
		var st: Dictionary = (_res.get("players", {}) as Dictionary).get(tag_id, {})
		d = float(st.get("disposals", 0.0))
		g = float(st.get("goals", 0.0))
	return "Your tag on %s: %d disposal%s, %d goal%s." % [
			GameDB.player_display_name_by_id(tag_id, "their player"), int(d), "" if int(d) == 1 else "s",
			int(g), "" if int(g) == 1 else "s"]


## Legs in words: how both midfields are going, and who is running on empty.
func _legs_view() -> Control:
	var v := UiKit.vbox(2)
	v.name = "LegsView"
	var l := UiKit.lbl(MatchNotes.legs_line(_group_energy(_my_side), _group_energy(1 - _my_side),
			_opp_legs_reason()), UiKit.NOTE, UiKit.MUTED)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(l)
	var cooked := MatchNotes.cooked(GameState.pending_sim.legs(_my_side))
	if not cooked.is_empty():
		var c := UiKit.lbl("Running on empty: %s." % ", ".join(cooked), UiKit.NOTE, UiKit.TEXT)
		c.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(c)
	return v


## Why their legs are going (RivalRead.legs_reason): the plans and fire-ups
## that cost them legs, when their calls cost more than yours. "" otherwise.
func _opp_legs_reason() -> String:
	var sim: MatchSim = GameState.pending_sim
	return RivalRead.legs_reason(RivalRead.calls_of(sim, 1 - _my_side), RivalRead.calls_of(sim, _my_side))


func _group_energy(side: int) -> float:
	var total := 0.0
	var n := 0
	for r in GameState.pending_sim.legs(side):
		if bool(r["on"]) and (str(r["role"]) == "MID" or str(r["role"]) == "RUCK"):
			total += float(r["energy"])
			n += 1
	return total / float(maxi(1, n))


# ---------------------------------------------------------------------------
# Match moments
# ---------------------------------------------------------------------------
func _show_moment() -> void:
	_close_moment()
	_pitch.pause()
	var m: Dictionary = GameState.pending_sim.pending_moment
	# The late centre ball-up call, and the run of goals against (row 14), both
	# put to the coach over a centre ball-up.
	var bounce := str(m.get("kind", "")) == "bounce" or bool(m.get("moves", false))
	if bounce and GameState.vignettes_on():
		_show_bounce_moment(m)
		return
	# Row 13: every other call with a scene is a scene too.
	if GameState.vignettes_on() and DecisionVignette.has_scene(str(m.get("kind", ""))):
		_show_bounce_moment(m)
		return
	# Sized for its few lines, not the whole phone.
	var box := UiKit.modal_box(_over, 560.0, 440.0, _wash())
	_moment_overlay = box["overlay"]
	_moment_overlay.name = "MomentCard"
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.lbl("Coach's call  ·  %s" % _clock_text(int(m.get("q", 1)), int(m.get("min", 0))),
			UiKit.SMALL, UiKit.MUTED))
	var title := UiKit.lbl(str(m.get("title", "")), 20, UiKit.EMPH, true)
	title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(title)
	if bounce and not bool(m.get("moves", false)):
		# Vignettes off: the centre ball-up call without its scene, the same
		# facts the scene would have put over it.
		for f in StoppageVignette.call_facts(GameState.pending_sim, _my_side):
			var fl := _say(str(f), UiKit.BODY, UiKit.TEXT, true)
			fl.name = "BounceFact"
			fl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			v.add_child(fl)
	var text := _say(str(m.get("text", "")), 14, UiKit.TEXT)
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(text)
	var options: Array = m.get("options", [])
	for i in range(options.size()):
		var o: Dictionary = options[i]
		# Every choice stands equal: no filled first button that reads as the
		# recommended one (director's PC playtest, 2026-10-07).
		var b := UiKit.btn(str(o.get("label", "")), 16, false)
		b.name = "Moment_%d" % i
		b.custom_minimum_size = Vector2(0, 46)
		b.pressed.connect(_on_moment_choice.bind(i))
		v.add_child(b)
		_moment_lines(v, o)


## The late centre-bounce call as a scene (ARD-M8-007 prototype): the match
## cuts to a close-up of that stoppage, the players set up, the ball goes up
## and it freezes; the call slides up over the frozen scene; the choice cuts
## back to the match. The options and what they do are MatchSim's; the scene
## only shows the state of the match.
func _show_bounce_moment(m: Dictionary) -> void:
	var overlay := UiKit.cover(_over)
	overlay.color = Color(0, 0, 0, 0)
	overlay.name = "MomentCard"
	overlay.set_meta("scene", true)
	_moment_overlay = overlay
	var vignette: StoppageVignette
	if str(m.get("kind", "")) == "bounce" or bool(m.get("moves", false)):
		vignette = StoppageVignette.new()
		vignette.name = "StoppageVignette"
	else:
		vignette = DecisionVignette.new()
		vignette.name = "DecisionVignette"
	overlay.add_child(vignette)
	vignette.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	vignette.clip_contents = true   # its stand and light towers stay off the scoreboard
	if vignette is DecisionVignette:
		(vignette as DecisionVignette).setup_decision(GameState.pending_sim, _my_side, m)
	else:
		vignette.setup(GameState.pending_sim, _my_side, str(m.get("title", "")))
	# The call, held below the screen until the scene freezes.
	var margin := MarginContainer.new()
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	overlay.add_child(margin)
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var hold := UiKit.vbox(0)
	hold.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(hold)
	var spacer := Control.new()
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	hold.add_child(spacer)
	var panel := UiKit.panel(UiKit.PANEL, 14)
	panel.name = "BounceCall"
	hold.add_child(panel)
	var call := UiKit.vbox(6)
	panel.add_child(call)
	# The run-of-goals call is about the goals, not the stoppages: no ruck line.
	for f in ([] if bool(m.get("moves", false)) else vignette.facts):
		var fl := _say(str(f), UiKit.BODY, UiKit.TEXT, true)
		fl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		call.add_child(fl)
	var text := _say(str(m.get("text", "")), UiKit.SMALL, UiKit.MUTED)
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	call.add_child(text)
	var buttons: Array = []
	var options: Array = m.get("options", [])
	for i in range(options.size()):
		var o: Dictionary = options[i]
		# Every choice stands equal: no filled first button that reads as the
		# recommended one (director's PC playtest, 2026-10-07).
		var b := UiKit.btn(str(o.get("label", "")), 16, false)
		b.name = "Moment_%d" % i
		b.custom_minimum_size = Vector2(0, 46)
		b.disabled = true
		b.pressed.connect(_on_moment_choice.bind(i))
		call.add_child(b)
		buttons.append(b)
		_moment_lines(call, o)
	panel.modulate.a = 0.0
	margin.add_theme_constant_override("margin_bottom", -600)
	vignette.ready_for_call.connect(func() -> void:
		for b in buttons:
			if is_instance_valid(b):
				b.disabled = false
		if not is_instance_valid(margin):
			return
		panel.modulate.a = 1.0
		vignette.call_room = panel.size.y
		var tw := margin.create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		tw.tween_method(func(v: float) -> void: margin.add_theme_constant_override("margin_bottom", int(v)),
				-600.0, 0.0, 0.3))


## Under a call's choice: what it does for you and what it costs, sized
## (GateOdds; "gain" and "cost" on the option), or its one line of words.
func _moment_lines(to: Container, o: Dictionary) -> void:
	var lines: Array = [str(o["gain"]), str(o["cost"])] if o.has("gain") else [str(o.get("detail", ""))]
	for i in range(lines.size()):
		var d := UiKit.lbl(str(lines[i]), UiKit.SMALL, UiKit.TEXT if o.has("gain") else UiKit.MUTED)
		d.name = ("MomentGain" if i == 0 else "MomentCost") if o.has("gain") else "MomentDetail"
		d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		to.add_child(d)


func _on_moment_choice(i: int) -> void:
	_close_moment()
	var sim: MatchSim = GameState.pending_sim
	if sim == null or sim.pending_moment.is_empty():
		return
	# The call and how it came off reach the feed as the "moment" event,
	# when play reaches it.
	sim.resolve_moment(i)
	_advance_segment()


## A call and its choices, heading above.
## A call's heading on the break: bold, in the text colour rather than
## muted, so it reads at a glance (director, 2026-10-11); the lines under it
## stay regular.
func _call_heading(label: String) -> Label:
	var l := UiKit.lbl(label, UiKit.SMALL, UiKit.TEXT, true)
	l.name = "CallHeading"
	return l


func _call_block(label: String, control: Control) -> Control:
	var v := UiKit.vbox(4 if _pc_break else 6)
	v.set_meta("break_unit", true)
	v.add_child(_call_heading(label))
	v.add_child(control)
	return v


## One tap picks one (UiKit.choice_grid); the key lands in calls[field]
## and on_change(key) runs.
func _choice_grid(node_name: String, options: Array, calls: Dictionary, field: String, columns: int,
		on_change: Callable = Callable()) -> Control:
	var grid_box := [null]
	var grid := UiKit.choice_grid(node_name, options, str(calls[field]), columns, func(key: String):
		calls[field] = key
		_ink_choices(grid_box[0])
		if on_change.is_valid():
			on_change.call(key)
		if _break_refresh.is_valid():
			_break_refresh.call())
	grid_box[0] = grid
	_ink_choices(grid)
	return grid


## The choices of a call are what the coach is deciding between: every one
## reads at body-text strength, and only the chosen one is outlined (lead's QC,
## 2026-10-14: the names not chosen read as faint grey; design bible, second
## pillar: nothing he decides on sits in grey). UiKit.paint_choice greys the
## rest for the screens where the rest can be skipped; not here.
func _ink_choices(grid: Node) -> void:
	if grid == null or not is_instance_valid(grid):
		return
	for b in grid.get_children():
		if b is Button:
			(b as Button).add_theme_color_override("font_color", UiKit.TEXT)


## A player call: "none", the few in the game so far, whoever is chosen,
## and "Other player..." for everyone in `roster` (the caller's choice: the
## whole side for a tag, only forwards for their loose defender). Nobody in
## it is left out; the list is just ordered.
## `detail` (optional): player, wide -> the lines under his name on his card
## ("" for none); wide is the list sheet's one-line form.
func _player_choice(node_name: String, none_label: String, roster: Array, first: Array,
		calls: Dictionary, field: String, sheet_title: String, on_change: Callable = Callable(),
		detail: Callable = Callable(), card: Callable = Callable(), other_label := "Other player…",
		rest_only := false) -> Control:
	var box := UiKit.vbox(0)
	box.name = node_name
	var rebuild := func(self_ref: Callable) -> void:
		UiKit.clear(box)
		var shown := [["", none_label]]
		var ids := {}
		for r in first:
			shown.append([str(r["id"]), _card_text(r, detail)])
			ids[str(r["id"])] = true
		var cur := str(calls[field])
		if cur != "" and not ids.has(cur):
			for r in roster:
				if str(r["id"]) == cur:
					shown.append([cur, _card_text(r, detail)])
		var grid := _choice_grid(node_name + "Grid", shown, calls, field, 2, on_change)
		box.add_child(grid)
		# rest_only: the list behind the button is who is not already a button
		# here, and with nobody left there is no button.
		var listed: Array = roster
		if rest_only:
			var on_show := {}
			for o in shown:
				on_show[str(o[0])] = true
			listed = roster.filter(func(r): return not on_show.has(str(r["id"])))
		var other: Button = null
		if not (rest_only and listed.is_empty()):
			other = UiKit.btn(other_label, 14)
			other.name = node_name + "Other"
			other.custom_minimum_size = Vector2(0, 44)
			other.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			other.pressed.connect(func():
				_player_sheet(sheet_title, listed, str(calls[field]), detail, func(id: String):
					calls[field] = id
					if on_change.is_valid():
						on_change.call(id)
					self_ref.call(self_ref)
					if _break_refresh.is_valid():
						_break_refresh.call()))
			grid.add_child(other)
		if card.is_valid():
			# Cards set their own facts (_dress_tagger_card): one man to a
			# row, the column's full width, so his facts never wrap a word to a
			# line (A2); "Other player..." last.
			grid.columns = 1
			for gb in grid.get_children().duplicate():
				if gb is Button and gb != other:
					card.call(gb, str(gb.name).trim_prefix(node_name + "Grid_"))
			return
		# On a PC, cards with a detail line sit together in their own row and
		# "Other player..." beside the none choice: two short buttons share a
		# row instead of each standing beside a tall card.
		if _pc_break and detail.is_valid() and not none_label.contains("\n") and other != null:
			grid.move_child(other, 1)
		if _pc_break:
			for gb in grid.get_children():
				(gb as Control).custom_minimum_size.y = 38.0
	rebuild.call(rebuild)
	return box


## A player's card text: his name, then what `detail` says about him.
func _card_text(r: Dictionary, detail: Callable) -> String:
	# A card keeps its groups on their own lines (MatchNotes.card_detail).
	var extra := str(detail.call(r, false)) if detail.is_valid() else ""
	return _short_name(r) if extra == "" else "%s
%s" % [_short_name(r), extra]


## A "Who tags" card (director, 2026-10-13: it must read at a glance): his name
## in bold with where he plays small beside it, then his Pressure and his legs
## along one line (label quiet, value clear), their man's touches with him on
## (row 120) and what he gives up of his own game under them. One man to a row, the column's full
## width (A2). Your club's colour is the rule down the left edge;
## selection stays the button's own text outline. The button stays the card's
## background and its tap target, under the words; its words are kept in the
## "card_text" meta for the tests.
func _dress_tagger_card(b: Button, who_name: String, c: Dictionary, is_pick: bool) -> void:
	var gives_value := str(c["gives"]).left(1).to_upper() + str(c["gives"]).substr(1)
	var press_value := "%s · their man: %s" % [c["pressure"], c["holds"]]
	var plain := "%s\n%s\nPressure %s\nLegs %s\n%s %s" % [who_name, c["where"], press_value, c["legs"],
			c["gives_label"], gives_value]
	if is_pick:
		plain += "\nYour assistant's pick"
	b.set_meta("card_text", plain)
	b.text = ""
	var grid := b.get_parent()
	var at := b.get_index()
	var wrap := MarginContainer.new()
	wrap.name = "Card_" + str(b.name)
	wrap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.remove_child(b)
	grid.add_child(wrap)
	grid.move_child(wrap, at)
	wrap.add_child(b)
	var pad := MarginContainer.new()
	pad.add_theme_constant_override("margin_left", 10)
	pad.add_theme_constant_override("margin_right", 10)
	pad.add_theme_constant_override("margin_top", 10)
	pad.add_theme_constant_override("margin_bottom", 10)
	wrap.add_child(pad)
	var row := UiKit.hbox(10)
	pad.add_child(row)
	# Your side's colour, in the shade of it that reads on the card.
	var rule := ColorRect.new()
	rule.name = "ClubRule"
	rule.color = UiKit.club_vivid(str(GameState.my_club), UiKit.SURFACE)
	rule.custom_minimum_size = Vector2(4, 0)
	row.add_child(rule)
	var col := UiKit.vbox(6)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(col)
	var head := HFlowContainer.new()
	head.add_theme_constant_override("h_separation", 8)
	head.add_theme_constant_override("v_separation", 0)
	var nm := UiKit.line(who_name, UiKit.NAME, UiKit.TEXT, true)
	nm.name = "CardName"
	if _names().has(who_name):
		nm.add_theme_color_override("font_color", UiKit.club_name_colour(UiKit.club_ink(str(_names()[who_name]))))
	head.add_child(nm)
	var where := UiKit.line(str(c["where"]), UiKit.SECONDARY, UiKit.MUTED)
	where.name = "CardWhere"
	head.add_child(where)
	col.add_child(head)
	# The short facts flow along one line, each label quiet beside its value,
	# and wrap whole (never a word to a line, A2); their man's touches and what
	# he gives up are the long ones, a line of their own each under them.
	var rows := [["Pressure", str(c["pressure"]), false], ["Legs", str(c["legs"]), bool(c["legs_bad"])]]
	var facts := HFlowContainer.new()
	facts.name = "CardFacts"
	facts.add_theme_constant_override("h_separation", 16)
	facts.add_theme_constant_override("v_separation", 0)
	for f in rows:
		var one := UiKit.hbox(5)
		one.add_child(UiKit.line(str(f[0]), UiKit.SECONDARY, UiKit.MUTED))
		one.add_child(UiKit.line(str(f[1]), UiKit.BODY, UiKit.BAD if bool(f[2]) else UiKit.TEXT))
		facts.add_child(one)
	col.add_child(facts)
	# Their man's touches: the label quiet, the counts clear, wrapping inside
	# the card rather than pushing it past the screen's edge.
	var holds := UiKit.hbox(5)
	holds.name = "CardHolds"
	holds.add_child(UiKit.line(str(c["holds_label"]), UiKit.SECONDARY, UiKit.MUTED))
	var holds_value := UiKit.lbl(str(c["holds"]), UiKit.BODY, UiKit.TEXT)
	holds_value.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	holds_value.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	holds.add_child(holds_value)
	col.add_child(holds)
	var gives := UiKit.lbl("%s %s" % [c["gives_label"], c["gives"]], UiKit.SECONDARY, UiKit.TEXT)
	gives.name = "CardGives"
	gives.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(gives)
	if is_pick:
		var pick := UiKit.line("Your assistant's pick", UiKit.SECONDARY, UiKit.MUTED)
		pick.name = "CardPick"
		pick.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		head.add_child(pick)
	for n in wrap.find_children("*", "Control", true, false):
		if n != b:
			(n as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	pad.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _short_name(r: Dictionary) -> String:
	return GameDB.player_display_name_by_id(str(r.get("id", "")), str(r.get("name", "Player")))


## Everyone on the ground for one side, one tap each; the current choice is
## marked. Back or Close leaves it as it was.
func _player_sheet(title: String, roster: Array, current: String, detail: Callable, on_pick: Callable) -> void:
	_close_sheet()
	var box := UiKit.modal_box(_over, 480.0, 0.0, _wash())
	var overlay: Control = box["overlay"]
	overlay.name = "PlayerSheet"
	_sheet_overlay = overlay
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.ellipsis(title, UiKit.H2, UiKit.TEXT, true))
	var players: Dictionary = _res.get("players", {})
	var ordered := roster.duplicate()
	ordered.sort_custom(func(a, b): return int(a.get("num", 0)) < int(b.get("num", 0)))
	for r in ordered:
		var id := str(r["id"])
		var st: Dictionary = players.get(id, {})
		var line := "#%d  %s" % [int(r.get("num", 0)), _short_name(r)]
		var extra := str(detail.call(r, true)) if detail.is_valid() else ""
		var game := "" if st.is_empty() else MatchNotes.game_line(st)
		if extra == "":
			if game != "":
				line += "  ·  " + game
		elif game != "":
			extra += "  ·  " + game
		var b := UiKit.btn(line if extra == "" else line + "
" + extra, 14)
		b.name = "Sheet_" + id
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		if extra == "":
			b.clip_text = true
			b.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		else:
			# Two lines of facts about him: wrapped in full, never cut.
			b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.custom_minimum_size = Vector2(0, 44 if extra == "" else 60)
		UiKit.paint_choice(b, id == current)
		NameInk.dress_button(b, _names())
		b.pressed.connect(func():
			_close_sheet()
			on_pick.call(id))
		v.add_child(b)
	var close := UiKit.btn("Close", UiKit.NAME)
	close.custom_minimum_size = Vector2(0, 44)
	close.pressed.connect(_close_sheet)
	box["footer"].add_child(close)


## Match-day sheets wash in the opponent's colour (director, 2026-10-08);
## a match you are not in keeps the usual wash.
func _wash() -> Color:
	var mine := str(GameState.my_club)
	var home := str(_res.get("home", ""))
	var away := str(_res.get("away", ""))
	var w := UiKit.AUTO_COLOUR
	if mine == home:
		w = UiKit.opponent_wash(away)
	elif mine == away:
		w = UiKit.opponent_wash(home)
	# No usable opponent colour (opponent_wash answers plain text): the sheet
	# carries your own club's colour instead of a neutral grey.
	return UiKit.AUTO_COLOUR if w == UiKit.TEXT else w


## The sheet's wash colour, resolved (AUTO is your club's colour).
func _wash_col() -> Color:
	return UiKit.team_wash() if _wash() == UiKit.AUTO_COLOUR else _wash()


func _close_sheet() -> void:
	if _sheet_overlay != null and is_instance_valid(_sheet_overlay):
		_sheet_overlay.queue_free()
	_sheet_overlay = null


## The players most in the game so far (before the bounce, the best rated):
## ordered, never filtered.
func _in_the_game(roster: Array, n: int) -> Array:
	var players: Dictionary = _res.get("players", {})
	var out := roster.duplicate()
	out.sort_custom(func(a, b):
		var x := CoachReport.influence(players.get(str(a["id"]), {}))
		var y := CoachReport.influence(players.get(str(b["id"]), {}))
		if x != y:
			return x > y
		return int(a["overall"]) > int(b["overall"]))
	return out.slice(0, n)


## Their midfielders only, by where each plays now (the roster copy carries
## the slot but not the position, so the sim's live copy decides).
func _taggable_now(sim: MatchSim, r: Dictionary) -> bool:
	return sim.tag_target_ok(1 - _my_side, str(r["id"]))


## A listed midfielder of theirs: midfield is his own position, wherever he
## lines up now. The break's tag names offer only these (director, 2026-10-14:
## a ruck in a midfield slot and a defender with midfield second were offered
## under "Tag which midfielder?"). The sim's own rule (MatchSim.tag_target_ok)
## is untouched; the tag's names and "Other midfielder..." both offer only these.
func _can_play_midfield(sim: MatchSim, r: Dictionary) -> bool:
	return sim.tag_target_ok(1 - _my_side, str(r["id"]))


func _listed_midfielder(sim: MatchSim, r: Dictionary) -> bool:
	var id := str(r["id"])
	var p := sim._on_ground(1 - _my_side, id)
	if p.is_empty():
		for b in (sim.squads[1 - _my_side] as Squad).bench:
			if str(b["id"]) == id:
				p = b
	return str(p.get("own_role", p.get("role", ""))) == "MID"


func _roster_side(side: int) -> Array:
	var roster: Array = _res.get("roster", [[], []])
	if roster.size() <= side:
		return []
	var out: Array = roster[side].duplicate()
	out.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
	return out


# ---------------------------------------------------------------------------
# Match stats at a break
# ---------------------------------------------------------------------------
## The match so far in full, over the break: team and player stats for both
## clubs, any quarter on its own. Close (or Back) returns to your calls.
func _show_break_stats(players_first := false) -> void:
	_close_report()
	var box := UiKit.modal_box(_over, SHEET_MAX_W if _stats_wide() else 640.0, 0.0, _wash())
	var overlay: Control = box["overlay"]
	overlay.name = "BreakStatsSheet"
	_report_overlay = overlay
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.ellipsis("Match stats", UiKit.H1, UiKit.TEXT, true))
	var box_score := _stats_page(v, true, players_first)
	box_score.name = "BreakBoxScore"
	var close := UiKit.btn("Back to your calls", UiKit.NAME, true)
	close.custom_minimum_size = Vector2(0, 44)
	close.pressed.connect(_close_report)
	box["footer"].add_child(close)


## Best so far, on the break: the three best of each side by match rating so
## far (yours first), each with the numbers that stand out, as full time's best
## players read, but no votes (they come at full time); "All player stats"
## opens the full table.
# A PC break is tight (the fullest one, GWS with both loose men, has 8 px to
# spare and Best so far may be at most ~213 px tall), so the rows sit 4 px apart
# there; a phone scrolls and has room for more.
const BEST_ROW_GAP_PC := 2


func _best_so_far() -> Control:
	var box := UiKit.vbox(4 if _pc_break else VOTES_STEP)
	box.name = "BestSoFar"
	box.set_meta("break_unit", true)
	var head := UiKit.hbox(8)
	var title := UiKit.section("Best so far")
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title)
	var all := UiKit.text_action("All player stats", UiKit.BODY)
	all.name = "BestSoFarAll"
	all.custom_minimum_size = Vector2(0, 24 if _pc_break else 48)
	all.pressed.connect(func(): _show_break_stats(true))
	# On a PC the way to the table sits in the heading row (shorter block: the
	# fullest break still fits 1280x720); a phone has it under the list.
	if _pc_break:
		head.add_child(all)
	box.add_child(head)
	# Your club first, then theirs, each under its own name, best rated first;
	# the same number each side: three, as on a phone, and on a PC the third
	# goes (row meta best_third) when the break would not fit 720 high with it.
	# Allegiance (director 2026-10-13): each side carries its club's colour (bar,
	# guernsey, name, rating) where it reads; see UiKit.club_heading.
	# One screen, both clubs: the pair helper gives the away side its second ink
	# when the two first inks look alike (a clash guernsey).
	var inks := UiKit.club_ink_pair(str(_res["home"]), str(_res["away"]))
	# No votes yet: the coaches give theirs once, at full time (director,
	# 2026-11-08). The break ranks each side by match rating so far.
	for side in [_my_side, 1 - _my_side]:
		var code := str(_res["home"] if side == 0 else _res["away"])
		var players := MatchNotes.best_so_far(_res, side, 3)
		var wrap := _votes_side(code, inks[side], players, {}, _pc_break)
		wrap.name = "BestSide_%d" % side
		(wrap.find_child("ClubName", true, false) as Node).name = "BestClub_%d" % side
		(wrap.get_child(1) as Node).name = "BestSideBox_%d" % side
		box.add_child(wrap)
	if not _pc_break:
		box.add_child(UiKit.spacer(8))   # with the body's 8: 16 clear of the buttons
		box.add_child(all)
	return box


func _glance_section(v: VBoxContainer, title: String, node_name: String, lines: Array, traits := false) -> void:
	if lines.is_empty():
		return
	v.add_child(UiKit.spacer(UiKit.GAP))
	v.add_child(UiKit.section(title))
	var box := UiKit.vbox(4)
	box.name = node_name
	for t in lines:
		var l: Control = TraitLink.line(str(t), UiKit.BODY, UiKit.TEXT) if traits else _say(str(t), UiKit.BODY, UiKit.TEXT)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(l)
	v.add_child(box)


func _glance_people(v: VBoxContainer, title: String, node_name: String, people: Array) -> void:
	if people.is_empty():
		return
	v.add_child(UiKit.spacer(UiKit.GAP))
	v.add_child(UiKit.section(title))
	var box := UiKit.vbox(6)
	box.name = node_name
	for p in people:
		var row := UiKit.vbox(0)
		row.add_child(_say(str(p["name"]), UiKit.BODY, UiKit.TEXT, true))
		row.add_child(_say(str(p["line"]), UiKit.SMALL, UiKit.MUTED))
		box.add_child(row)
	v.add_child(box)


func _close_report() -> void:
	if _report_overlay != null and is_instance_valid(_report_overlay):
		_report_overlay.queue_free()
	_report_overlay = null


## The plan your side is playing right now, as the engine has it.
func _current_plan(sim: MatchSim) -> String:
	var plan := str((sim.tactics[_my_side] as Dictionary).get("gameplan", ""))
	if plan == "":
		plan = str(_last_tactics.get("gameplan", ""))
	return plan if plan != "" else "balanced"


func _simulate_next_quarter(t: Dictionary) -> void:
	_last_tactics = t.duplicate()
	_apply_quarter_tactics(t)
	_show_setup(t)
	GameState.pending_sim.begin_quarter()
	_advance_segment()


## Simulate on to the end of the quarter or the next moment, then play it.
func _advance_segment() -> void:
	var sim: MatchSim = GameState.pending_sim
	_legs_seen = _legs_now(sim)
	if sim.continue_quarter():
		_res = sim.end_quarter()
	else:
		_res = sim.result()
	_stamp_match_meta()
	_append_new_events()
	# Your calls are in force from here, so the rings are up for the bounce.
	_refresh_rings()
	_pitch.play()
	_sync_controls()


func _apply_quarter_tactics(t: Dictionary) -> void:
	var sim: MatchSim = GameState.pending_sim
	# A loose defender you picked yourself stays your call; one left as the
	# assistant set it stays his to change at the breaks.
	if bool(t.get("interceptor_set", false)):
		sim.coach_interceptor(_my_side, str(t.get("interceptor_id", "")))
	sim.set_tactics(_my_side, t)
	# Rotations are the assistant's (director, 2026-11-03): the season plan
	# and the legs set them each quarter (MatchSim.auto_rotation).
	sim.set_rotation_policy(_my_side, sim.auto_rotation(_my_side, GameState.fitness_plan(str(GameState.my_club))))
	# The rival coach plays its usual game, protects a lead, chases a
	# deficit, and tags your best midfielder after half time.
	sim.set_tactics(1 - _my_side, sim.ai_tactics(1 - _my_side))
	# Every club rotates as a competent coach would, the rival included.
	var rival := str((sim.squads[1 - _my_side] as Squad).code)
	sim.set_rotation_policy(1 - _my_side, sim.auto_rotation(1 - _my_side, GameState.fitness_plan(rival)))


## The player you play through, with his job this match: the slot he fills on
## the ground (or filled last, off it) - "Matthew Jefferson our key forward target".
func _focus_player(id: String) -> Dictionary:
	var sim: MatchSim = GameState.pending_sim
	if sim != null:
		var sq: Squad = sim.squads[_my_side]
		for p in sq.ground + sq.bench:
			if str(p["id"]) == id:
				return p
	for r in _roster_side(_my_side):
		if str(r["id"]) == id:
			return r
	return {}


func _focus_text(id: String) -> String:
	var p := _focus_player(id)
	return MatchNotes.focus_role_text(GameDB.player_display_name_by_id(id, "your player"), str(p.get("role", "")))


## Under a Play through control: his job and what it does for him; the
## general description with nobody picked; that it waits while he is off the spot.
func _focus_note_text(slot: String, id: String) -> String:
	if id == "":
		return MatchNotes.focus_slot_note(slot, "", false, false)
	var who := GameDB.player_display_name_by_id(id, "your player")
	var on := false
	var working := false
	var sim: MatchSim = GameState.pending_sim
	if sim != null:
		for p in (sim.squads[_my_side] as Squad).ground:
			if str(p["id"]) == id:
				on = true
				working = (MatchSim.FOCUS_SLOT_ROLES[slot] as Array).has(str(p["role"]))
	return MatchNotes.focus_slot_note(slot, who, working, not on)


## "Defensive Press · tagging Walsh": your calls for this quarter, one line.
func _show_setup(t: Dictionary) -> void:
	if _setup_line == null or not is_instance_valid(_setup_line):
		return
	var bits := PackedStringArray(["Your plan: " + CoachReport.plan_label(str(t.get("gameplan", "balanced")))])
	var tag_id := str(t.get("tag_id", ""))
	if tag_id != "":
		bits.append("tagging " + GameDB.player_display_name_by_id(tag_id, "their player"))
	for slot in MatchNotes.FOCUS_ORDER:
		var fid := str(t.get(slot, ""))
		if fid != "":
			bits.append("%s %s" % [GameDB.player_display_name_by_id(fid, "your player"),
					str(MatchNotes.FOCUS_SLOT_TEXT[slot][1])])
	var legacy := str(t.get("focus_id", ""))
	if legacy != "":
		bits.append(_focus_text(legacy))
	var intercept_id := str(t.get("interceptor_id", ""))
	if intercept_id != "":
		bits.append(GameDB.player_display_name_by_id(intercept_id, "your defender") + " loose behind the ball")
	if bool(t.get("spare_accountable", false)):
		# Whoever is on him now: the named forward, or his stand-in if he's off.
		var sim_now = GameState.pending_sim
		var on_him: Dictionary = sim_now._spare_minder(_my_side) if sim_now != null else {}
		var who := GameDB.player_display_name(on_him) if not on_him.is_empty() 				else GameDB.player_display_name_by_id(str(t.get("spare_minder_id", "")), "a forward")
		bits.append(who + " on their spare")
	NameInk.set_line(_setup_line, "  ·  ".join(bits), _names())
	_setup_line.visible = true


func _stamp_match_meta() -> void:
	_res["home"] = GameState.pending_match["home"]
	_res["away"] = GameState.pending_match["away"]
	_res["label"] = GameState.pending_match["label"]
	_res["venue"] = str(GameState.pending_match.get("venue", ""))


func _append_new_events() -> void:
	var all_events: Array = _res.get("events", [])
	var new_events := all_events.slice(_event_cursor)
	_event_cursor = all_events.size()
	if not new_events.is_empty():
		_pitch.append_events(new_events, _res.get("timeline", []))


# ---------------------------------------------------------------------------
# Playback hooks
# ---------------------------------------------------------------------------
## Tired and hurt players carry a short mark on the oval and the bench strip
## (PlayerMarks): the hurt from the injuries played so far, either side; the
## tired from your own side's legs, in a match you coach.
func _refresh_marks() -> void:
	var injuries: Array = _res.get("injuries", [])
	var energy := {}
	var sim_now = GameState.pending_sim if _interactive else null
	if sim_now != null:
		injuries = sim_now.injuries
		# The sim has run ahead of the oval: its legs now are the end of the stretch
		# still playing, so the marks use the legs from when that stretch began.
		energy = _legs_now(sim_now) if _pitch.current_index() >= _pitch.events.size() else _legs_seen
	_pitch.set_marks(PlayerMarks.build(_pitch.events, _pitch.current_index(), injuries, energy))


## Your side's legs in the sim right now: id -> energy.
func _legs_now(sim: MatchSim) -> Dictionary:
	var out := {}
	for r in sim.legs(_my_side):
		out[str(r["id"])] = float(r["energy"])
	return out


## The ring on the oval: the players of yours you have made a call on or
## promised a run (MatchRings). Calls change at the breaks and at the moments,
## so it is read again with every event: a few lookups, and the view only
## redraws when the set moved. Only a match you coach has calls to show.
func _refresh_rings() -> void:
	if _pitch == null:
		return
	_refresh_marks()
	if _interactive and GameState.pending_sim != null:
		_pitch.set_rings(MatchRings.ids(GameState.pending_sim, _my_side, GameState.my_list))
	else:
		_pitch.set_rings([])


func _on_event(ev: Dictionary) -> void:
	var event_index := _playback_event_index
	_playback_event_index += 1
	# Skipping to the break releases a quarter's events at once: the rings and
	# the meter are painted once at the end, not for every event.
	if not _skipping:
		_refresh_rings()
	_update_scoreboard(ev)
	_track_momentum(ev)
	_feed_add(ev)
	# A career best at a goal is that goal's one extra line: no battle or
	# story line stacks on it.
	if not _career_high_feed(ev) or str(ev.get("kind", "")) != "goal":
		_duel_feed(ev)
		_story_feed(ev)
	_press_feed(event_index, ev)
	_call_feed(event_index, ev)
	if str(ev.get("kind", "")) == "goal":
		_flash_score(int(ev.get("side", 0)))
		_track_run(int(ev.get("side", 0)))
	if _crowd != null and not _skipping:
		_crowd.event(str(ev.get("kind", "")))
	_queue_broadcast(ev, event_index)


## A vignette reads the positions the presentation has already staged. It
## cannot alter those positions, the event log, the score or any match RNG.
func _broadcast_snapshot(ev: Dictionary) -> Dictionary:
	if _pitch == null or _pitch.director == null:
		return {}
	var d: MatchDirector = _pitch.director
	var ball: Vector2 = d.ball.get("pos", Vector2.ZERO)
	var actor_pos := ball
	var actor_id := d.actor
	if actor_id >= 0 and actor_id < d.tokens.size():
		actor_pos = d.tokens[actor_id].get("pos", ball)
	var at: Vector2 = actor_pos if str(ev.get("kind", "")) == "mark" else ball
	var nearby := 0
	for token in d.tokens:
		if (token.get("pos", Vector2.ZERO) as Vector2).distance_to(at) <= 8.0:
			nearby += 1
	return {"actor_pos": actor_pos, "ball_pos": ball, "nearby": nearby}


## Trigger selection is deterministic and presentation-only. Categories are
## sparse, with enough football between them that a watched game does not
## become a highlights reel interrupting itself.
func _queue_broadcast(ev: Dictionary, event_index: int) -> void:
	if _skipping or _finished or _broadcast_pending or _broadcast_busy or _pitch == null:
		return
	# Vignettes off (Settings): no replays. They decide nothing.
	if not GameState.vignettes_on():
		return
	var prev_ev := {}
	var next_ev := {}
	if event_index > 0 and event_index - 1 < _pitch.events.size():
		prev_ev = _pitch.events[event_index - 1]
	if event_index + 1 < _pitch.events.size():
		next_ev = _pitch.events[event_index + 1]
	var snap := _broadcast_snapshot(ev)
	var kind := BroadcastVignette.pick_kind(ev, prev_ev, next_ev, snap)
	if kind == "":
		return
	var special := kind == BroadcastVignette.AFTER_SIREN
	var cat := BroadcastVignette.category(kind)
	if cat == "speccy":
		# MatchSim now owns whether the mark was actually spectacular and
		# enforces the 0/1/2 distribution. Presentation only guards the hard cap.
		if _broadcast_speccies >= 2:
			return
	elif _broadcast_seen.has(cat):
		return
	if not special and (_broadcast_count >= 3 or event_index - _broadcast_last_event < 70):
		return
	if cat == "speccy":
		_broadcast_speccies += 1
	else:
		_broadcast_seen[cat] = true
	if not special:
		_broadcast_count += 1
		_broadcast_last_event = event_index
	_broadcast_pending = true
	_pitch.pause()
	_show_broadcast.call_deferred(kind, ev.duplicate(true), snap)



func _show_broadcast(kind: String, ev: Dictionary, snap: Dictionary) -> void:
	if not _broadcast_pending or _finished:
		_broadcast_pending = false
		return
	_broadcast_pending = false
	_broadcast_busy = true
	var overlay := UiKit.cover(_over)
	overlay.name = "BroadcastVignetteOverlay"
	overlay.color = Color(0.015, 0.018, 0.02, 1.0)
	_broadcast_overlay = overlay
	var vignette := BroadcastVignette.new()
	vignette.name = "BroadcastVignette"
	overlay.add_child(vignette)
	vignette.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	vignette.setup(kind, ev, snap, _res)
	vignette.finished.connect(_finish_broadcast)


func _finish_broadcast() -> void:
	if _broadcast_overlay != null and is_instance_valid(_broadcast_overlay):
		_broadcast_overlay.queue_free()
	_broadcast_overlay = null
	_broadcast_busy = false
	if _broadcast_finish_waiting:
		_broadcast_finish_waiting = false
		_on_finished()
		return
	if not _finished and _coach_overlay == null and _moment_overlay == null and _pitch != null:
		_pitch.play()
		_sync_controls()


## "Carlton have kicked three in a row." - a fact from the goals in the log.
func _track_run(side: int) -> void:
	if side == _run_side:
		_run_len += 1
	else:
		_run_side = side
		_run_len = 1
	if _run_len >= RUN_LINE:
		var code := str(_res["home"] if side == 0 else _res["away"])
		_feed_text(MatchNotes.run_line(code, _run_len), UiKit.TEXT, true, "RunLine")


## A goal in the feed: the scoring club's colour down the side, "Goal" and
## the kicker in large type, then the score. Nothing else in the feed looks
## like it.
func _goal_row(ev: Dictionary, stamp: String) -> Control:
	var side := int(ev.get("side", 0))
	var code := str(_res["home"] if side == 0 else _res["away"])
	var row := UiKit.hbox(8)
	row.name = "GoalRow"
	row.set_meta("feed_kind", "goal")
	var stripe := ColorRect.new()
	stripe.color = (GameDB.club_colours(code) as Array)[0]
	if stripe.color.get_luminance() < 0.12:
		stripe.color = (GameDB.club_colours(code) as Array)[2]
	stripe.custom_minimum_size = Vector2(4, 0)
	row.add_child(stripe)
	var v := UiKit.vbox(0)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(v)
	var who := str(ev.get("name", ""))
	var head := MatchNotes.goal_head(who, code)
	# The scorer's club is the event's own, whatever the index knows.
	var names := _names().duplicate()
	if who != "":
		names[who] = code
	var tone := MatchNotes.feed_tone(ev, _my_side)
	row.set_meta("tone", tone)
	var head_col: Color = UiKit.GOOD if tone == "good" else (UiKit.BAD if tone == "bad" else UiKit.TEXT)
	var hl := NameInk.label(head, names, UiKit.NAME, head_col, true)
	hl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(hl)
	var g: Array = ev.get("goals", [0, 0])
	var b: Array = ev.get("behinds", [0, 0])
	# A Crumber's goal off the deck is his trait at work: say so.
	if str(ev.get("trait", "")) == "crumber":
		stamp = "Crumbing goal  ·  " + stamp
	v.add_child(UiKit.lbl("%s  ·  %s %s  %s %s" % [stamp,
			GameDB.club_short(str(_res["home"])), UiKit.scoreline(int(g[0]), int(b[0])),
			GameDB.club_short(str(_res["away"])), UiKit.scoreline(int(g[1]), int(b[1]))],
			UiKit.SMALL, UiKit.MUTED))
	return row


## The scoring side's score swells for a moment on a goal.
func _flash_score(side: int) -> void:
	var l: Label = _score_home if side == 0 else _score_away
	if l == null or not is_instance_valid(l) or _skipping:
		return
	l.pivot_offset = l.size / 2.0
	l.scale = Vector2(1.35, 1.35)
	var tw := create_tween()
	tw.tween_property(l, "scale", Vector2.ONE, 0.6).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _update_scoreboard(ev: Dictionary) -> void:
	if ev.has("goals") and ev.has("behinds"):
		var g: Array = ev["goals"]
		var b: Array = ev["behinds"]
		_shown_goals = [int(g[0]), int(g[1])]
		_shown_behinds = [int(b[0]), int(b[1])]
	_shown_q = int(ev.get("q", _shown_q))
	_shown_min = int(ev.get("min", _shown_min))
	_paint_scoreboard()


## The sides have changed ends: the next period is starting, so the clock shows
## it from its first minute rather than the last minute of the one before.
func _on_ends_changed(_period: int) -> void:
	if _finished or _skipping:
		return
	_shown_q += 1
	_shown_min = (_shown_q - 1) * QUARTER_MINUTES
	_paint_scoreboard()


func _paint_scoreboard() -> void:
	if _score_home == null or _score_away == null:
		return
	_score_home.text = UiKit.scoreline(_shown_goals[0], _shown_behinds[0])
	_score_away.text = UiKit.scoreline(_shown_goals[1], _shown_behinds[1])
	_fit_scores()
	if _clock != null:
		_clock.text = _clock_text(_shown_q, _shown_min)
	if _lead != null and is_instance_valid(_lead):
		var narrow := UiKit.view_width(self) < 640.0
		var name_of := func(c): return GameDB.club_short(str(c)) if narrow else GameDB.club_name(str(c))
		_lead.text = MatchNotes.lead_text(str(_res["home"]), str(_res["away"]), [
				_shown_goals[0] * 6 + _shown_behinds[0], _shown_goals[1] * 6 + _shown_behinds[1]], name_of)


## Both scores at one size: the largest at which the longer one fits its half
## of the band (row 6.29; a phone's 28.18 (186) ran past the band's clipped
## edge). They step down together, so neither club's score reads smaller.
func _fit_scores() -> void:
	if _score_band == null or not is_instance_valid(_score_band) or _score_home == null:
		return
	var narrow := UiKit.view_width(self) < 640.0
	var band := minf(_score_band.size.x, UiKit.view_width(self) - 2.0 * _score_band.global_position.x)
	# The band's padding (8 a side), the row's two gaps (6) and the clock between.
	var room := (band - 16.0 - 12.0 - (84.0 if narrow else 132.0)) / 2.0
	var sizes := [UiKit.RATING, UiKit.SCORE, UiKit.NUMBER] if narrow else [36, UiKit.RATING, UiKit.SCORE]
	var font: Font = _score_home.get_theme_font("font")
	var fs: int = sizes[-1]
	for s: int in sizes:
		var wide := maxf(font.get_string_size(_score_home.text, HORIZONTAL_ALIGNMENT_LEFT, -1, UiKit.px(s)).x,
				font.get_string_size(_score_away.text, HORIZONTAL_ALIGNMENT_LEFT, -1, UiKit.px(s)).x)
		if wide <= room:
			fs = s
			break
	for l: Label in [_score_home, _score_away]:
		UiKit.set_font_size(l, fs)


## "Q3 12'": the minute of the quarter, like a ground's clock. MatchSim
## stamps each quarter 30 minutes on from the last; extra time counts its
## own minutes from zero.
func _clock_text(q: int, minute: int) -> String:
	if q >= 5:
		return "ET %d'" % clampi(minute - 120, 0, 99)
	return "Q%d %d'" % [q, clampi(minute - (q - 1) * QUARTER_MINUTES, 0, QUARTER_MINUTES)]


func _feed_add(ev: Dictionary) -> void:
	var kind := str(ev.get("kind", ""))
	if QUIET_KINDS.has(kind):
		return
	var line := MatchNotes.feed_line(ev, str(_res["home"]), str(_res["away"]))
	if line.is_empty():
		return
	var stamp := _clock_text(int(ev.get("q", 1)), int(ev.get("min", 0)))
	if str(line["tier"]) == "goal":
		_feed.add_child(_goal_row(ev, stamp))
		ProblemReport.note_feed("%s  %s" % [stamp, str(line["text"])])
		_trim_feed()
	elif str(line["tier"]) == "break":
		_feed_text(str(line["text"]), UiKit.TEXT, true, "BreakLine")
	else:
		_feed_text("%s  %s" % [stamp, str(line["text"])], UiKit.TEXT, false, "PlayLine")


## The players of both clubs in this match, by name, so a name in a sentence can
## wear his club's colour (NameInk). Built from the squads, never from the text.
func _names() -> Dictionary:
	if not _name_index.is_empty():
		return _name_index
	var lists := []
	var codes := []
	var sim: MatchSim = GameState.pending_sim
	if sim != null and sim.squads.size() == 2:
		for sq in sim.squads:
			lists.append((sq as Squad).list + (sq as Squad).ground + (sq as Squad).bench)
			codes.append(str((sq as Squad).code))
	else:
		var roster: Array = _res.get("roster", [])
		for side in range(mini(2, roster.size())):
			lists.append(roster[side])
			codes.append(str(_res["home"]) if side == 0 else str(_res["away"]))
	_name_index = NameInk.from_squads(lists, codes)
	return _name_index


## A line whose words change later: always tinted-capable.
func _say_live(text: String, fs: int, col: Color, ids := []) -> RichTextLabel:
	var r := NameInk.rich(fs, col)
	NameInk.set_line(r, text, _names_named(ids) if not ids.is_empty() else _names())
	return r


## A line of the match's talk: plain, or with each player's name in his club's ink.
## `ids`: the players the line means, so a surname two clubs share still wears
## his club's ink (see _names_named).
func _say(text: String, fs: int, col: Color, bold := false, ids := []) -> Control:
	return NameInk.label(text, _names_named(ids) if not ids.is_empty() else _names(), fs, col, bold)


func _feed_text(text: String, col: Color, strong: bool, node_name: String) -> void:
	if _feed == null:
		return
	var l := _say(text, UiKit.SMALL, col, strong)
	l.name = node_name
	# Siblings cannot share a name, so the row's kind rides as metadata.
	l.set_meta("feed_kind", node_name)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_feed.add_child(l)
	ProblemReport.note_feed(text)
	_trim_feed()


func _trim_feed() -> void:
	while _feed.get_child_count() > FEED_LIMIT:
		var first := _feed.get_child(0)
		_feed.remove_child(first)
		first.queue_free()
	# Wait a frame: the scroll range only grows once the new row is laid out.
	await get_tree().process_frame
	if is_instance_valid(_feed_scroll):
		_feed_scroll.scroll_vertical = int(_feed_scroll.get_v_scroll_bar().max_value)
		_hide_cut_rows()


## While the feed sits at its newest line, a row whose top has scrolled out of
## view is not drawn, so the feed never opens on the tail of a wrapped line
## (at a larger text size a two-line row showed only its last word). Scrolled
## back up by the coach, every row shows as it is.
func _hide_cut_rows() -> void:
	if not is_instance_valid(_feed_scroll) or not is_instance_valid(_feed):
		return
	var bar := _feed_scroll.get_v_scroll_bar()
	var top := float(_feed_scroll.scroll_vertical)
	var following := top >= bar.max_value - bar.page - 1.0
	for c in _feed.get_children():
		if c is CanvasItem:
			var cut := following and (c as Control).position.y < top - 0.5
			(c as CanvasItem).modulate.a = 0.0 if cut else 1.0


func _on_finished() -> void:
	# A quarter/final can be released in the same PitchView frame as a close-up
	# candidate. Let the vignette finish before opening the next modal.
	if _broadcast_pending or _broadcast_busy:
		_broadcast_finish_waiting = true
		return
	if _fulltime_shown:
		return
	if _interactive and not _skipping and GameState.pending_sim != null \
			and not GameState.pending_sim.pending_moment.is_empty():
		_sync_controls()
		_show_moment()
		return
	# Skip sims the rest of the match first, then drains the pitch. Without
	# this flag the quarter-end signal reopens the coach box.
	if _interactive and not _skipping and GameState.pending_sim != null \
			and GameState.pending_sim.current_quarter <= 4:
		_sync_controls()
		_show_coach_box()
		return
	# A level final plays on: extra time is rolled now and fed to the pitch.
	if _interactive and not _skipping and GameState.pending_sim != null \
			and GameState.pending_sim.needs_extra_time():
		_legs_seen = _legs_now(GameState.pending_sim)
		_res = GameState.pending_sim.run_extra_time()
		_stamp_match_meta()
		_append_new_events()
		_pitch.play()
		_sync_controls()
		return
	_skipping = false
	_finished = true
	if _crowd != null:
		_crowd.full_time()
	_fulltime_shown = true
	_close_coach()
	if _res.has("goals") and _res.has("behinds"):
		var end_q := 4
		var end_min := 4 * QUARTER_MINUTES
		var evs: Array = _res.get("events", [])
		if bool(_res.get("extra_time", false)) and not evs.is_empty():
			end_q = 5
			end_min = int((evs[evs.size() - 1] as Dictionary).get("min", 128))
		_update_scoreboard({
			"q": end_q, "min": end_min, "kind": "final",
			"goals": _res["goals"], "behinds": _res["behinds"],
		})
	if _interactive:
		GameState.finish_interactive_match(_res)
	_sync_controls()
	# Full time is built at once (its controls exist and work the moment the siren goes);
	# a milestone game's farewell plays over it on its own layer, and a tap or its end
	# shows full time underneath.
	_show_fulltime()
	if not _farewell.is_empty():
		var v := FarewellVignette.open(get_tree().root, _farewell["ms"], _farewell["man"],
				GameState.my_club, str(_farewell["opp"]), _farewell["mine"], _farewell["theirs"],
				"Full time", str(GameState.pending_match.get("weather", "")) == "wet")
		v.offset_top = _over.offset_top   # under the scoreboard, as every scene (T3.R42)
		v.clip_contents = true            # its stand's roof stays off the scoreboard
		_farewell = {}
		var wv: WeakRef = weakref(v)   # not the node: it frees itself when it ends
		tree_exiting.connect(func():            # Back out of the match: it goes too
			var n = wv.get_ref()
			if n != null:
				n.finish_now())


## Who the scene after the siren honours, and both sides' players: {} unless your
## side has a milestone man (FarewellVignette.caption) who is in the side today.
## The pre-season practice match (GameState.prepare_practice_match): played
## for its own sake, so it carries no ladder, finals, debut or milestone talk.
func _is_practice(m: Dictionary) -> bool:
	return str(m.get("label", "")) == "Practice match"


func _farewell_for(match: Dictionary) -> Dictionary:
	# Vignettes off (Settings) means no scene at all, this one included.
	if GameState.season == null or GameState.my_club == "" or not GameState.vignettes_on():
		return {}
	var ms: Dictionary = GameState.banner_context(match).get("milestone", {})
	if FarewellVignette.caption(ms) == "":
		return {}
	var sq := GameState.my_squad()
	var mine: Array = sq.ground + sq.bench
	var man := {}
	for p in mine:
		if str(p.get("id", "")) == str(ms.get("id", "")):
			man = p
	if man.is_empty():
		return {}
	var opp := str(match["away"]) if str(match["home"]) == GameState.my_club else str(match["home"])
	var season: Season = GameState.season
	var theirs: Array = []
	if season.lists.has(opp):
		var osq := Squad.new(opp, season.lists[opp], false, opp, season.selections.get(opp, {}))
		theirs = osq.ground + osq.bench
	return {"ms": ms, "man": man, "opp": opp, "mine": mine, "theirs": theirs}


# ---------------------------------------------------------------------------
# Full time
# ---------------------------------------------------------------------------
## Full time is one review with two tabs - the Summary (the one coaching
## report) and Stats - and one way out: Continue. Back on Stats returns to
## Summary. Review match (Sim round) opens the same screen.
func _show_fulltime() -> void:
	# A PC's Stats tab holds the score and the team numbers side by side, so the
	# sheet is wider there; the Summary keeps its own reading width inside it.
	var box := UiKit.modal_box(_over, SHEET_MAX_W if _stats_wide() else 640.0, 0.0, _wash())
	var overlay: Control = box["overlay"]
	overlay.name = "FullTime"
	_ft_box = box
	_ft_tab = "summary"
	# The tabs sit above the scrolling body, so they never scroll away.
	var outer: Node = (box["body"] as Control).get_parent().get_parent()
	_ft_tabs = UiKit.hbox(2)
	_ft_tabs.name = "ReviewTabs"
	outer.add_child(_ft_tabs)
	outer.move_child(_ft_tabs, 0)
	var wash_col := UiKit.team_wash() if _wash() == UiKit.AUTO_COLOUR else _wash()
	UiKit.edge_fade(box["body"].get_parent() as ScrollContainer, Color(wash_col, 0.2))

	var home: String = _res["home"]
	var away: String = _res["away"]
	var mine := GameState.my_club != "" and (home == GameState.my_club or away == GameState.my_club)
	# On a PC the two actions sit side by side at the sheet's right, one row tall, so the
	# stats page keeps the height (a phone stacks them).
	var actions: Control = box["footer"]
	if _stats_wide():
		var row := HBoxContainer.new()
		row.name = "FullTimeActions"
		row.alignment = BoxContainer.ALIGNMENT_END
		row.add_theme_constant_override("separation", 12)
		actions.add_child(row)
		actions = row
	if mine and (_interactive or _review):
		var train := UiKit.btn("Training", UiKit.BODY)
		train.name = "FullTimeTraining"
		train.custom_minimum_size = Vector2(240 if _stats_wide() else 0, 48)
		train.pressed.connect(func():
			overlay.queue_free()
			Router.replace("training"))
		actions.add_child(train)
	# The week is over: back to the hub, where next week starts.
	var leave := UiKit.btn("Continue", UiKit.HEADING, true)
	leave.name = "FullTimeContinue"
	leave.custom_minimum_size = Vector2(240 if _stats_wide() else 0, 48)
	_club_fill_button(leave)
	leave.pressed.connect(func(): Router.back())
	UiKit.feel(leave, "end")     # the end of the match: the siren
	actions.add_child(leave)
	_render_ft()
	UiKit.land(overlay.find_child("Verdict", true, false) as Control, 0.3)   # the result lands (Feel)
	UiKit.land(overlay.find_child("LadderMove", true, false) as Control, 1.0, false)   # then the ladder move


func _ft_tab_list() -> Array:
	return [["summary", "Summary"], ["stats", "Stats"]]


func _render_ft() -> void:
	var v: VBoxContainer = _ft_box["body"]
	UiKit.clear(v)
	UiKit.clear(_ft_tabs)
	for t in _ft_tab_list():
		var key := str(t[0])
		var b := UiKit.tab(str(t[1]), key == _ft_tab)
		b.name = "ReviewTab_" + key
		b.custom_minimum_size.y = 48
		b.pressed.connect(func():
			_ft_tab = key
			_render_ft())
		_ft_tabs.add_child(b)
	match _ft_tab:
		"stats":
			_ft_stats(v)
		_:
			if _stats_wide():
				var inner := UiKit.vbox(8)
				v.add_child(UiKit.reading_column(inner, 640.0))
				_ft_summary(inner)
			else:
				_ft_summary(v)
	var sc := v.get_parent() as ScrollContainer
	if sc != null:
		sc.scroll_vertical = 0


## The match story at the top of the Summary: the hero and his game, the
## turning point, and why it was won or lost. Read from MatchStory; it never
## changes the result. Returns what it told (MatchStory.told_facts), so the
## sections below say each fact once.
func _ft_story(v: VBoxContainer, me: int) -> Dictionary:
	var st := MatchStory.build(_res, me)
	if st.is_empty():
		return {}
	var box := UiKit.vbox(4)
	box.name = "MatchStory"
	box.add_child(UiKit.spacer(UiKit.GAP))
	# Best players above already gives a player's numbers: the hero's line
	# keeps only what it adds (director's bug report, 2026-11-06).
	var shown := {}
	var votes := MatchNotes.coaches_votes(_res)
	for side in [0, 1]:
		for p in MatchNotes.standouts_by_votes(_res, side, 99, votes):
			shown[str(p["id"])] = str(p["line"])
	var hero: Dictionary = st["hero"]
	if not hero.is_empty():
		box.add_child(UiKit.section("Hero of the match"))
		var hl := UiKit.lbl(str(hero["name"]), UiKit.NAME,
				UiKit.club_name_colour(UiKit.club_ink(str(hero["club"]))), true)
		hl.name = "MatchHero"
		hl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(hl)
		var hero_line := MatchStory.line_less(hero, str(shown.get(str(hero["id"]), "")))
		if hero_line != "":
			var gl := UiKit.lbl(hero_line, UiKit.BODY, UiKit.TEXT)
			gl.name = "MatchHeroLine"
			gl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			box.add_child(gl)
	# A loss: your best player too (director, 2026-11-03).
	if int(st["margin"]) < 0:
		var mb := MatchStory.my_best(_res, me)
		if not mb.is_empty():
			var mb_line := MatchStory.line_less(mb, str(shown.get(str(mb["id"]), "")))
			var ml := UiKit.lbl("Your best: %s" % str(mb["name"]) + (", " + mb_line.left(1).to_lower() + mb_line.substr(1) if mb_line != "" else ""),
					UiKit.BODY, UiKit.TEXT)
			ml.name = "MatchMyBest"
			ml.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			box.add_child(ml)
	if str(st["turning_point"]) != "":
		box.add_child(UiKit.section("Turning point"))
		var tl := UiKit.lbl(str(st["turning_point"]), UiKit.BODY, UiKit.TEXT)
		tl.name = "TurningPoint"
		tl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(tl)
	var why: Array = st["reasons"]
	if not why.is_empty():
		box.add_child(UiKit.section("Why you won" if bool(st["won"])
				else ("Why it was a draw" if bool(st["drawn"]) else "Why you lost")))
		var rv := UiKit.vbox(4)
		rv.name = "WhyReasons"
		for r in why:
			var rl := UiKit.lbl(str(r["text"]), UiKit.BODY, UiKit.TEXT)
			rl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			rv.add_child(rl)
		box.add_child(rv)
	v.add_child(box)
	return MatchStory.told_facts(st)


## The Summary tab: the result, what it means, how it went, the best
## players, a few numbers and your week.
func _ft_summary(v: VBoxContainer) -> void:

	var s: Array = _res["score"]
	var home: String = _res["home"]
	var away: String = _res["away"]
	var mine := GameState.my_club != "" and (home == GameState.my_club or away == GameState.my_club)
	var me := 0 if home == GameState.my_club else 1
	var margin := absi(int(s[0]) - int(s[1]))
	var winner := -1 if int(s[0]) == int(s[1]) else (0 if int(s[0]) > int(s[1]) else 1)

	var head := "Full time  ·  %s" % str(_res.get("label", "Match"))
	if bool(_res.get("extra_time", false)):
		head += "  ·  after extra time"
	v.add_child(UiKit.ellipsis(head, UiKit.SECONDARY, VOTES_SUB))

	# The result first, big: who won and by how much.
	var verdict := "Draw"
	var col := UiKit.TEXT
	if winner >= 0 and mine:
		verdict = ("Won by %d" if winner == me else "Lost by %d") % margin
		col = UiKit.margin_colour(winner == me)
	elif winner >= 0:
		verdict = "%s by %d" % [GameDB.club_name(home if winner == 0 else away), margin]
	var vl := UiKit.lbl(verdict, 30, col, true)
	vl.name = "Verdict"
	v.add_child(vl)
	var score_inks := UiKit.club_ink_pair(home, away)
	for side in [0, 1]:
		var row := UiKit.hbox(8)
		row.name = "FinalScore_%d" % side
		# Both clubs read in full text; the winner is bold, the loser plain, and
		# each name carries its club's colour (a red club's is white).
		var nm := UiKit.ellipsis(GameDB.club_name(home if side == 0 else away), UiKit.NAME,
				UiKit.readable_ink(UiKit.club_name_colour(score_inks[side]), UiKit.tinted("sheet", _wash_col())), winner != 1 - side)
		nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(nm)
		var fig := UiKit.figure(UiKit.scoreline(int(_res["goals"][side]), int(_res["behinds"][side])),
				UiKit.SCORE, UiKit.TEXT)
		row.add_child(fig)
		# The same right edge as the votes below: clear of the scrollbar.
		var edge := Control.new()
		edge.name = "ScoreGutter"
		edge.custom_minimum_size.x = VOTES_GUTTER
		row.add_child(edge)
		v.add_child(row)

	# Best players and the coaches' votes, first under the result (director's
	# review 2026-11-04: they were below the fold). Yours first, then their
	# best, each club in its colour with its crest.
	_ft_best_players(v, me, mine, winner)

	# The match story: the hero, the turning point and why.
	var told_above := {}
	if mine:
		told_above = _ft_story(v, me)

	# What it means: finals, the ladder, who is next. (Nothing, for a practice match.)
	if mine and not _is_practice(_res):
		# A clear section gap after the votes, so the ladder lines do not run on.
		v.add_child(UiKit.spacer(UiKit.GAP * 2))
		var outlook := GameState.finals_outcome_line(_res)
		if outlook != "":
			var tag_now := str(_res.get("tag", ""))
			var slots: Dictionary = GameState.season.finals.get("slots", {})
			var through: bool = str(slots.get("W_" + tag_now, "")) == GameState.my_club
			var ol := UiKit.lbl(outlook, 20 if tag_now == "GF" else UiKit.BODY,
					UiKit.EMPH if through else UiKit.MUTED, true)
			ol.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			v.add_child(ol)
		# A debut is said once, here, in the fuller words ("kicked a goal on
		# debut"); the payoff lines below leave it out (director, 2026-11-06).
		var debut_ids := {}
		if Milestones.shown():
			var ms_texts := []
			for e in Milestones.summary_items(GameState, _res):
				if str(e.get("kind", "")) == "debut" and str(e.get("id", "")) != "":
					debut_ids[str(e["id"])] = true
					var kicked := int(((_res.get("players", {}) as Dictionary).get(str(e["id"]), {}) as Dictionary).get("goals", 0))
					ms_texts.append(Firsts.debut_line(str(e.get("name", "")), kicked))
				else:
					ms_texts.append(str(e.get("text", "")))
			if not ms_texts.is_empty():
				# A heading, then the milestone in plain weight: the ladder and the next game follow it.
				v.add_child(UiKit.section("Milestones"))
				var msl := UiKit.lbl(" ".join(ms_texts), UiKit.BODY, UiKit.TEXT)
				msl.name = "MilestoneLine"
				msl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				v.add_child(msl)
		if (_interactive or _review) and str(_res.get("tag", "")) == "":
			var moved := GameState.ladder_move_line(_pos_before)
			if moved != "":
				var ml := UiKit.lbl(moved, UiKit.BODY, VOTES_SUB)
				ml.name = "LadderMove"
				v.add_child(ml)
			var nxt := GameState.next_fixture_line()
			if nxt != "":
				var nl := UiKit.lbl(nxt, UiKit.NAME, UiKit.TEXT, true)
				nl.name = "NextFixture"
				v.add_child(nl)
		# The people it was about: a debut, a first goal, a promised run done.
		# Said only when the facts kept on the players say it; otherwise silent.
		if _interactive or _review:
			var told := []
			for it in GameState.payoff_items(_res):
				if not (str(it["kind"]) == "debut" and debut_ids.has(str(it["id"]))):
					told.append(str(it["text"]))
			told = told.slice(0, Firsts.MAX_LINES)
			if not told.is_empty():
				v.add_child(UiKit.spacer(UiKit.GAP))
				var payoffs := UiKit.vbox(4)
				payoffs.name = "PayoffLines"
				for line in told:
					var pl := UiKit.lbl(str(line), UiKit.BODY, UiKit.TEXT)
					pl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
					payoffs.add_child(pl)
				v.add_child(payoffs)

	# The Grand Final's best on ground, from either side.
	var medal := GameState.norm_smith_for(_res)
	if not medal.is_empty():
		v.add_child(UiKit.spacer(UiKit.GAP))
		v.add_child(UiKit.section("Norm Smith Medal"))
		var mc := UiKit.club_ink(str(medal["club"]))
		var ml := UiKit.lbl("%s (%s)" % [str(medal["name"]), GameDB.club_name(str(medal["club"]))],
				UiKit.NAME, UiKit.club_name_colour(mc), true)
		ml.name = "NormSmithMedal"
		ml.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(ml)
		var ms := UiKit.lbl(str(medal["line"]), UiKit.BODY, UiKit.TEXT)
		ms.name = "NormSmithLine"
		ms.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(ms)

	# How it went: the few things that decided it, in football words, less
	# what the story above already said (director, 2026-11-06).
	var hiw_gap := UiKit.spacer(UiKit.GAP)
	v.add_child(hiw_gap)
	var hiw_head := UiKit.section("How it went")
	hiw_head.name = "HowItWentHead"
	v.add_child(hiw_head)
	var factors := VBoxContainer.new()
	factors.name = "MatchFactors"
	factors.add_theme_constant_override("separation", 4)
	var shown_factors := MatchNotes.match_factors(_res, me if mine else 0, told_above)
	# What is now said on the screen, for the notes below to leave out.
	var said_now := told_above.duplicate()
	for it in MatchNotes.match_factor_items(_res, me if mine else 0):
		if shown_factors.has(str(it["text"])):
			said_now[str(it["fact"])] = true
	for f in shown_factors:
		var fl := _say(str(f), UiKit.BODY, UiKit.TEXT)
		fl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		factors.add_child(fl)
	# The one who got away (P-16): what a former player of yours did against
	# you, when he played most of it or kicked a goal.
	if mine:
		var opp_code := str(_res["away"] if me == 0 else _res["home"])
		var gone := FormerPlayers.report_lines(_res, me, GameState.former_players(opp_code))
		for i in range(gone.size()):
			var gl := NameInk.label(str(gone[i]["text"]), _names(), UiKit.BODY, UiKit.TEXT)
			gl.name = "FormerAgainst_%d" % i
			factors.add_child(gl)
	v.add_child(factors)
	# Everything was said above: no empty heading. The node stays, hidden.
	if factors.get_child_count() == 0:
		hiw_gap.visible = false
		hiw_head.visible = false
		factors.visible = false

	# The coach's side of it: who needs a lift, and what to work on. Only
	# for your match, and only what the result above does not already say.
	if mine and (_res.get("quarter_teams", []) as Array).size() >= 2:
		var g := CoachReport.glance(CoachReport.match_report(_res, me), true)
		_glance_people(v, "Needs a lift", "ReportLift", g["lift"])
		_glance_section(v, "Coaching notes", "ReportNotes",
				CoachReport.notes_not_told(g["notes"], said_now).slice(0, 2))

	if mine:
		# Your synergies: the stat each one shows up in, from this match.
		_glance_section(v, "Your synergies", "FullTimeSynergies", MatchNotes.synergy_lines(_res, me).slice(0, 3), true)

	# Your calls, quarter by quarter: what each was about and how that went.
	if mine and _interactive:
		var did := []
		for qq in range(1, 5):
			for t in MatchNotes.calls_lines(_res, me, qq):
				# The call the Why section already quoted is not said again.
				if told_above.has("q%d" % qq) and told_above.has("call:" + str(t)):
					continue
				did.append("Q%d  ·  %s" % [qq, str(t)])
		if not did.is_empty():
			_glance_section(v, "Your calls", "FullTimeCalls", did.slice(0, 5))

	# A handful of numbers worth a glance; the full table is a tap away.
	v.add_child(UiKit.spacer(UiKit.GAP))
	v.add_child(_key_stats_view(me if mine else 0))

	# Your week: who is hurt, who improved.
	if mine and (_interactive or _review):
		var week := UiKit.vbox(4)
		week.name = "YourWeek"
		var hurt := GameState.my_new_injuries()
		if not hurt.is_empty():
			var inj := UiKit.lbl("Injured: " + ", ".join(hurt), UiKit.BODY, UiKit.BAD, true)
			inj.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			week.add_child(inj)
		var report: Dictionary = GameState.last_training_report
		if str(report.get("home", "")) == home and str(report.get("away", "")) == away:
			# Who improved, and how, lives in Training (a tap below); here
			# just that it happened.
			var rises: Array = (report.get("auto", {}) as Dictionary).get("rises", [])
			if not rises.is_empty():
				var gl := UiKit.lbl("%d %s at training." % [rises.size(),
						"player improved" if rises.size() == 1 else "players improved"], UiKit.SMALL, UiKit.TEXT)
				gl.name = "TrainingCount"
				week.add_child(gl)
		if week.get_child_count() > 0:
			v.add_child(UiKit.spacer(UiKit.GAP))
			v.add_child(UiKit.section("Your week"))
			v.add_child(week)


## The votes lists at the break and at full time are one piece: a club's
## crest (and its name, at the break), then every player the coaches voted for,
## best-voted first, each a white name with his votes on the same baseline at
## the right, and his two best numbers under it. One line over both clubs says
## what the votes are (_votes_header). Club colour is the bar and the crest
## only, so a name can never pass for a button.
const VOTES_BAR_W := 5.0        # the club's bar down its block
const VOTES_MARKER := 44.0      # the crest's height: about 32 px wide
const VOTES_SUB := Color("cfcabe")   # the stat line under a name: a step dimmer than the name
const VOTES_GUTTER := 8.0       # plus the row's 8 gap: 16 clear of the scrollbar and the card's edge; the score lines use it too
const VOTES_STEP := 12          # one spacing step between blocks and rows


## One club's block: its crest (and name when `named`), then its voted players.
func _votes_side(code: String, ink: Color, players: Array, votes: Dictionary, pc := false, named := true) -> Control:
	var side_box := UiKit.vbox(4 if pc else VOTES_STEP)
	var rows_box := UiKit.vbox(BEST_ROW_GAP_PC if pc else VOTES_STEP)
	var sh := UiKit.club_heading(code, null, UiKit.BODY if pc else UiKit.NAME, 22.0 if pc else VOTES_MARKER, ink, false, named)
	side_box.add_child(sh)
	var shown := 0
	for p in players:
		shown += 1
		var row := UiKit.vbox(0)
		row.name = "BestRow_%s" % str(p["id"])
		if pc and shown == 3:
			row.set_meta("best_third", true)
		# Name and votes share one line, bottom-aligned so their baselines meet.
		var top := UiKit.hbox(8)
		var pn := UiKit.lbl(str(p["name"]), UiKit.BODY if pc else UiKit.NAME, UiKit.TEXT, true)
		pn.name = "StandoutName"
		pn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		pn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		pn.size_flags_vertical = Control.SIZE_SHRINK_END
		top.add_child(pn)
		var fig := _votes_figure(votes, str(p["id"]))
		fig.size_flags_vertical = Control.SIZE_SHRINK_END
		top.add_child(fig)
		var gap := Control.new()
		gap.name = "VotesGutter"
		gap.custom_minimum_size.x = VOTES_GUTTER
		top.add_child(gap)
		row.add_child(top)
		# The line sits on the sheet's wash (the opponent's colour) and near its
		# club's bar; lift it only as far as 4.5:1 against both needs.
		var sub_ink := UiKit.readable_ink(VOTES_SUB, UiKit.tinted("sheet", ink))
		sub_ink = UiKit.readable_ink(sub_ink, UiKit.tinted("sheet", _wash_col()))
		var sub := UiKit.lbl(str(p["line"]), UiKit.SECONDARY, sub_ink)
		sub.name = "StandoutLine"
		sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		row.add_child(sub)
		rows_box.add_child(row)
	# At full time a club neither coach voted for still has its block, saying so.
	if players.is_empty() and not votes.is_empty():
		var none := UiKit.lbl("No votes", UiKit.BODY, UiKit.MUTED)
		none.name = "NoVotes"
		rows_box.add_child(none)
	side_box.add_child(rows_box)
	return UiKit.club_section_body(code, side_box, ink, VOTES_BAR_W)


## What the votes are, said once over both clubs: who voted, how the list runs.
func _votes_header() -> Control:
	var l := UiKit.lbl("Coaches' votes: each coach gives his best five 5, 4, 3, 2, 1", UiKit.BODY, UiKit.TEXT)
	l.name = "VotesHeading"
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


## A player's coaches' votes at the right of his row, as the AFL publishes
## them: every player either coach voted for, with his total ("10 votes",
## "1 vote"). Hidden on a row with none (Best so far at a break). Plain text
## colour: club colour says who, not how well.
func _votes_figure(votes: Dictionary, id: String) -> Label:
	var n := int(votes.get(id, 0))
	var l := UiKit.line("%d vote%s" % [n, "" if n == 1 else "s"] if n > 0 else "", UiKit.BODY, UiKit.TEXT, true)
	l.name = "StandoutVotes"
	l.visible = n > 0
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	return l


## Best players, from the coaches' votes, as the AFL publishes them (director,
## 2026-11-08: "One ranked list"): every player either coach voted for, from
## both clubs in one list, most votes first (his side's match-rating order
## breaks a tie). Each name is in its club's colour beside its club's bar.
func _ft_best_players(v: VBoxContainer, _me: int, _mine: bool, _winner: int) -> void:
	v.add_child(UiKit.spacer(UiKit.GAP))
	v.add_child(UiKit.section("Best players"))
	v.add_child(_votes_header())
	var best_box := UiKit.vbox(VOTES_STEP)
	best_box.name = "BestPlayers"
	var votes := MatchNotes.coaches_votes(_res)
	var inks := UiKit.club_ink_pair(str(_res["home"]), str(_res["away"]))
	for r in _ranked_votes(votes):
		best_box.add_child(_ranked_row(r, votes, inks[int(r["side"])]))
	v.add_child(best_box)


## Both clubs' voted players in one list: most votes first; a tie keeps each
## side's own order (match rating) and, between sides, the home club first.
func _ranked_votes(votes: Dictionary) -> Array:
	var all := []
	for side in [0, 1]:
		var k := 0
		for p in MatchNotes.standouts_by_votes(_res, side, 99, votes):
			var r: Dictionary = (p as Dictionary).duplicate()
			r["side"] = side
			r["order"] = k
			k += 1
			all.append(r)
	all.sort_custom(func(a, b):
		var va := int(votes.get(str(a["id"]), 0))
		var vb := int(votes.get(str(b["id"]), 0))
		if va != vb:
			return va > vb
		if int(a["order"]) != int(b["order"]):
			return int(a["order"]) < int(b["order"])
		return int(a["side"]) < int(b["side"]))
	return all


## One row of the ranked list: the club's bar, the name in the club's colour
## with the votes at the right, and the player's two best stats under it.
func _ranked_row(p: Dictionary, votes: Dictionary, ink: Color) -> Control:
	var side := int(p["side"])
	var code := str(_res["home"] if side == 0 else _res["away"])
	var row := UiKit.vbox(0)
	row.name = "BestRow_%s" % str(p["id"])
	row.set_meta("side", side)
	var top := UiKit.hbox(8)
	var name_ink := UiKit.readable_ink(UiKit.club_name_colour(ink), UiKit.tinted("sheet", _wash_col()))
	var pn := UiKit.lbl(str(p["name"]), UiKit.NAME, name_ink, true)
	pn.name = "StandoutName"
	pn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	pn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pn.size_flags_vertical = Control.SIZE_SHRINK_END
	top.add_child(pn)
	var fig := _votes_figure(votes, str(p["id"]))
	fig.size_flags_vertical = Control.SIZE_SHRINK_END
	top.add_child(fig)
	var gap := Control.new()
	gap.name = "VotesGutter"
	gap.custom_minimum_size.x = VOTES_GUTTER
	top.add_child(gap)
	row.add_child(top)
	var sub_ink := UiKit.readable_ink(VOTES_SUB, UiKit.tinted("sheet", ink))
	sub_ink = UiKit.readable_ink(sub_ink, UiKit.tinted("sheet", _wash_col()))
	var sub := UiKit.lbl("%s  ·  %s" % [GameDB.club_short(code), str(p["line"])], UiKit.SECONDARY, sub_ink)
	sub.name = "StandoutLine"
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	row.add_child(sub)
	var wrap := UiKit.club_section_body(code, row, ink, VOTES_BAR_W)
	wrap.name = "BestRank_%s" % str(p["id"])
	return wrap


func _key_stats_view(me: int) -> Control:
	var v := UiKit.vbox(2)
	v.name = "KeyStats"
	var codes := [str(_res["home"]), str(_res["away"])]
	var h0 := UiKit.hbox(4)
	h0.add_child(_qcell(GameDB.club_short(codes[me]), 64, UiKit.MUTED, UiKit.SMALL, true))
	var gap := UiKit.line("", UiKit.SMALL, UiKit.MUTED)
	gap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h0.add_child(gap)
	h0.add_child(_qcell(GameDB.club_short(codes[1 - me]), 64, UiKit.MUTED, UiKit.SMALL, true))
	v.add_child(h0)
	for row in MatchNotes.key_stats(_res, me):
		var h := UiKit.hbox(4)
		var a := int(row[1])
		var b := int(row[2])
		h.add_child(_qcell(str(a), 64, UiKit.TEXT, UiKit.BODY, a > b))
		var lab := UiKit.ellipsis(str(row[0]), UiKit.SMALL, UiKit.MUTED)
		lab.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lab.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(lab)
		h.add_child(_qcell(str(b), 64, UiKit.TEXT, UiKit.BODY, b > a))
		v.add_child(h)
	return v


## A PC (landscape, roomy) shows the score and the team numbers side by side on one
## page, so nothing needs scrolling to reach the stats (director, 2026-10-14: "having to
## scroll down to see the stats part is bad"); a phone stacks them and scrolls.
func _stats_wide() -> bool:
	return ScreenLayout.roomy(UiKit.view_width(self), UiKit.view_height(self))


## The sheet on a PC grows with the screen (the canvas the player's window gives, which
## ScreenLayout sizes: a 2560x1440 window is a 1280x720 canvas at twice the pixels), up
## to its margins.
const SHEET_MAX_W := 4096.0
## The three columns of a PC stats page: the score (box score), the team numbers and, at
## full time, what the calls did. Each keeps its own width and shares what is left.
const COL_SCORE_W := 400.0
const COL_CALLS_W := 270.0
const SCORE_SHARE := 1.0
const TEAM_SHARE := 1.4
const CALLS_SHARE := 0.9


func _stats_page(host: VBoxContainer, live: bool, players_first: bool, calls: Control = null) -> BoxScore:
	var bs := BoxScore.new()
	var msv := MatchStatsView.new()
	msv.players_first = players_first
	if _stats_wide():
		bs.compact = true
		msv.compact = true
		var cols := UiKit.hbox(20)
		cols.name = "StatsColumns"
		var gaps := 20.0 * (2.0 if calls != null else 1.0)
		var room := UiKit.view_width(self) - 24.0 - 40.0 - gaps
		var shares := SCORE_SHARE + TEAM_SHARE + (CALLS_SHARE if calls != null else 0.0)
		# The width the team numbers will have: how many groups sit across, and how wide each is.
		msv.room = room * TEAM_SHARE / shares
		bs.custom_minimum_size.x = COL_SCORE_W if calls != null else 460.0
		bs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		bs.size_flags_stretch_ratio = SCORE_SHARE
		bs.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		msv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		msv.size_flags_stretch_ratio = TEAM_SHARE
		msv.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		cols.add_child(bs.setup(_res, live))
		cols.add_child(msv.setup(_res, _my_side, live))
		if calls != null:
			calls.custom_minimum_size.x = COL_CALLS_W
			calls.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			calls.size_flags_stretch_ratio = CALLS_SHARE
			calls.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
			cols.add_child(calls)
		host.add_child(cols)
	else:
		host.add_child(bs.setup(_res, live))
		host.add_child(UiKit.spacer(UiKit.GAP))
		host.add_child(msv.setup(_res, _my_side, live))
		if calls != null:
			host.add_child(UiKit.spacer(UiKit.GAP))
			host.add_child(calls)
	return bs


## The Stats tab: the box score (BoxScore), then team and player stats a tab apart
## (MatchStatsView, the same view as at the breaks), and what your calls did - on a
## PC a third column beside them, so the whole page shows at once.
func _ft_stats(v: VBoxContainer) -> void:
	var box := UiKit.vbox(8)
	box.name = "MatchStats"
	v.add_child(box)
	_stats_page(box, false, false, _calls_view(0) if _interactive else null)


func _qcell(text: String, w: int, col: Color, fs: int, bold := false) -> Label:
	var l := UiKit.line(text, fs, col, bold)
	l.custom_minimum_size = Vector2(w, 0)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l


## Router back hook. A live match cannot be abandoned half way (the rest of
## the round is already on the ladder), so back is swallowed until full time.
func handle_back() -> bool:
	# A player list opened from the break closes first.
	if _sheet_overlay != null and is_instance_valid(_sheet_overlay):
		_close_sheet()
		return true
	# An open report closes first, live or at full time.
	if _report_overlay != null and is_instance_valid(_report_overlay):
		_close_report()
		return true
	# A call's sheet on the break closes next, the top one first; the break stays.
	if not _break_sheets.is_empty():
		_close_top_break_sheet()
		return true
	# In the full-time review, Stats and Report go back to Summary.
	if _fulltime_shown and _ft_tab != "summary" and not _ft_box.is_empty() \
			and is_instance_valid(_ft_box["overlay"]):
		_ft_tab = "summary"
		_render_ft()
		return true
	if _interactive and not _finished:
		_feed_hint("Finish the match first - use Skip to full time to jump ahead.")
		return true
	return false


func _feed_hint(text: String) -> void:
	_feed_text(text, UiKit.MUTED, false, "Hint")


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED and _pitch != null and is_inside_tree():
		if not _reflow_queued:
			_reflow_queued = true
			_reflow.call_deferred()
	elif what == NOTIFICATION_EXIT_TREE and _pitch != null:
		_pitch.pause()
		# A farewell shown at full time lives on the root: leaving by Back must not
		# leave it standing over the next screen.
		var tree := get_tree()
		if tree != null:
			var fv := tree.root.find_child("FarewellVignette", true, false)
			if fv != null:
				var holder := fv.get_parent()
				(holder if holder is CanvasLayer else fv).queue_free()


func _reflow() -> void:
	_reflow_queued = false
	if not is_inside_tree() or _pitch == null or _root == null or _body == null:
		return
	if _margin != null:
		UiKit.apply_insets(_margin, 10)
	var stack := UiKit.view_width(self) < 640.0
	if stack != _stacked:
		_body.remove_child(_pitch)
		_body.remove_child(_side_panel)
		var idx := _body.get_index()
		_root.remove_child(_body)
		_body.queue_free()
		_mount_body(stack)
		_root.add_child(_body)
		_root.move_child(_body, idx)
	else:
		_orient_pitch(stack)
		_fit_side_panel()
	var old := _root.get_child(0)
	_root.remove_child(old)
	old.queue_free()
	var board := _scoreboard()
	_root.add_child(board)
	_root.move_child(board, 0)
	_paint_scoreboard()



## Injuries and the odd turning point in the feed (MatchNotes.story_feed_line).
func _story_feed(ev: Dictionary) -> void:
	var text := MatchNotes.story_feed_line(_duel_mem, ev)
	if text != "":
		_feed_text("%s  %s" % [_clock_text(int(ev.get("q", 1)), int(ev.get("min", 0))), text],
				UiKit.TEXT, false, "StoryLine")


## A career best for one of yours, in bold so a once-in-a-career moment is
## not lost among routine lines (MatchNotes.career_high_lines). True when a
## line was added.
func _career_high_feed(ev: Dictionary) -> bool:
	var sim = GameState.pending_sim
	var extra := int(ev.get("q", 1)) == 4 and (bool(_res.get("extra_time", false))
			or (_interactive and sim != null and sim.needs_extra_time()))
	var lines := MatchNotes.career_high_lines(_duel_mem, ev, _res, extra)
	for text in lines:
		_feed_text("%s  %s" % [_clock_text(int(ev.get("q", 1)), int(ev.get("min", 0))), str(text)],
				UiKit.TEXT, true, "CareerHighLine")
	return not lines.is_empty()


## The Defensive Press taking hold, once a side a match: the first time the
## side whose plan it is defends after setting it (V2, press pilot).
func _press_feed(event_index: int, ev: Dictionary) -> void:
	var presser := MatchNotes.press_trigger(_res.get("timeline", []), event_index, ev, _press_said)
	if presser < 0:
		return
	_press_said[presser] = true
	var code := str(_res["home"] if presser == 0 else _res["away"])
	_feed_text("%s  %s" % [_clock_text(int(ev.get("q", 1)), int(ev.get("min", 0))), MatchNotes.press_line(code)],
			UiKit.TEXT, false, "PressLine")


## A side's game plan starting, carrying on over a break or ending, and a short
## call running out (P-12, MatchNotes.call_lines). A break's line comes after
## the break's own score line. A plan dropped at the break is said at the
## next bounce, once the break's calls are made, without the new quarter's clock.
func _call_feed(event_index: int, ev: Dictionary) -> void:
	var lines := MatchNotes.call_lines(_res.get("timeline", []), event_index, ev, _call_mem,
			str(_res["home"]), str(_res["away"]))
	var unstamped := int(_call_mem.get("break_lines", 0))
	for i in range(lines.size()):
		var stamp := "" if i < unstamped else "%s  " % _clock_text(int(ev.get("q", 1)), int(ev.get("min", 0)))
		_feed_text(stamp + str(lines[i]), UiKit.TEXT, false, "CallLine")


## The battle in the feed, rarely (MatchNotes.duel_feed_line).
func _duel_feed(ev: Dictionary) -> void:
	var text := MatchNotes.duel_feed_line(_duel_mem, ev)
	if text != "":
		_feed_text("%s  %s" % [_clock_text(int(ev.get("q", 1)), int(ev.get("min", 0))), text],
				UiKit.TEXT, false, "DuelLine")
