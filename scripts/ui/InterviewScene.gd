class_name InterviewScene
extends Control
## The new coach's appointment interview (row 119): his name, then seven
## questions from the press pack, one at a time. Answers show nothing while
## he gives them; at the end the two archetypes they add up to are named with
## everything they do. It cannot be skipped. It comes once the club is taken,
## before the first pick (director, 2026-11-11: "its meant to go before the
## draft"); the draft and the hub both route here while GameState.interview_due.

## Set by the draft board when it sends the coach here: Continue goes back to
## it, a finished draft included (its Finish step is still to come).
static var back_to_draft := false

## The room fills the screen behind the page, and the page sits on a dark sheet
## at the foot: the sheet never covers more than this share of the screen (a
## longer page scrolls inside it), so the coach above always shows.
const SHEET_MAX := 0.56
## The soft edge from the room into the sheet.
const FADE_H := 40.0
## The figure sheet is never drawn larger than its own pixels (screen units per
## sheet pixel): a bigger screen gets more room around the coach, not a blurred one.
const FIGURE_CAP := 1.0
## On a wide screen the page keeps to this width, in the middle of the sheet.
const SHEET_W := 900.0
## A page this much shorter than the last does not move the room's camera.
const SHEET_SLACK := 48.0

var _root: VBoxContainer
## Outside the scroll: the page's one action never sits half under the fold.
var _foot: VBoxContainer
var _frame: VBoxContainer
var _scroll: ScrollContainer
## The press room (MediaConferenceVignette, the same room as every press
## conference), behind the pages. Its size is the screen's, never the page's, and
## it stays through every page, so the coach walks in and sits down once.
var _stage: Control
var _room: MediaConferenceVignette
var _wide := false
## The sheet height the room is framed to, and the screen size it was for.
var _sheet_shown := -1.0
var _sheet_for := Vector2.ZERO
var _picks := []
var _name := ""


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	if not GameState.interview_due or GameState.coach_club() == "":
		_leave()
		return
	var bg := ColorRect.new()
	bg.color = UiKit.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	add_child(ClubBackdrop.new().setup(GameState.coach_club()))
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 16)
	add_child(margin)
	var page := UiKit.vbox(14)
	page.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var vw := UiKit.view_width(self)
	var vh := UiKit.view_height(self)
	_wide = ScreenLayout.roomy(vw, vh)
	_frame = UiKit.vbox(10)
	_frame.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if GameState.vignettes_on():
		_stage = Control.new()
		_stage.name = "InterviewStage"
		_stage.clip_contents = true
	var col := _frame
	if _stage != null:
		# The room behind, the whole screen; the page on a sheet at its foot (on a
		# wide screen too, its lines kept to a readable width in the middle).
		margin.add_child(_stage)
		margin.add_child(_frame)
		_frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_frame.add_theme_constant_override("separation", 0)
		var gap := Control.new()
		gap.name = "InterviewRoomView"
		gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
		gap.size_flags_vertical = Control.SIZE_EXPAND_FILL
		_frame.add_child(gap)
		var grad := Gradient.new()
		grad.set_color(0, Color(UiKit.BG, 0.0))
		grad.set_color(1, Color(UiKit.BG, 0.94))
		var tex := GradientTexture2D.new()
		tex.gradient = grad
		tex.fill_from = Vector2(0, 0)
		tex.fill_to = Vector2(0, 1)
		var fade := TextureRect.new()
		fade.texture = tex
		fade.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		fade.stretch_mode = TextureRect.STRETCH_SCALE
		fade.custom_minimum_size = Vector2(0, FADE_H)
		fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_frame.add_child(fade)
		var sheet := PanelContainer.new()
		sheet.name = "InterviewSheet"
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(UiKit.BG, 0.94)
		sb.content_margin_bottom = 2.0
		sheet.add_theme_stylebox_override("panel", sb)
		_frame.add_child(sheet)
		col = UiKit.vbox(10)
		if _wide:
			var mid := CenterContainer.new()
			sheet.add_child(mid)
			col.custom_minimum_size.x = minf(SHEET_W, vw - 32.0)
			mid.add_child(col)
		else:
			sheet.add_child(col)
	else:
		margin.add_child(_frame)
	var sc := UiKit.scroll(page)
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	col.add_child(sc)
	_scroll = sc
	if _stage == null:
		# No room drawn (scenes off): the page sits in the middle, not at the top
		# of an empty screen.
		page.size_flags_vertical = Control.SIZE_EXPAND_FILL
		page.alignment = BoxContainer.ALIGNMENT_CENTER
	_foot = UiKit.vbox(0)
	col.add_child(_foot)
	_root = page
	if _stage != null:
		_room = MediaConferenceVignette.open(_stage, GameState.coach_club())
		_room.figure_cap = FIGURE_CAP
		resized.connect(_fit)
	_name = GameState.coach_name
	if _name == "":
		_name_page()
	else:
		_question()


func _clear() -> void:
	# Out of the tree now, so the next page's nodes keep their names.
	for box in [_root, _foot]:
		for c in box.get_children():
			box.remove_child(c)
			c.queue_free()


## The sheet is as tall as its page (up to SHEET_MAX of the screen, then the
## page scrolls), so the room shows above it with no empty block. The room itself
## is the screen's size whatever the page; only its camera tilts.
func _fit() -> void:
	if _stage == null:
		return
	# A frame first, so the wrapped labels report their real height.
	await get_tree().process_frame
	if not is_instance_valid(_stage) or not is_inside_tree():
		return
	var frame_h := _frame.size.y
	var sheet_max := frame_h * SHEET_MAX
	var foot := _foot.get_combined_minimum_size().y
	var room_for_page := sheet_max - FADE_H - foot - 12.0
	_scroll.custom_minimum_size.y = minf(_root.get_combined_minimum_size().y, room_for_page)
	# The camera frames the room down to the sheet's edge. It holds still while a
	# page is within SHEET_SLACK of the last framing (the press pack's backs fill a
	# shorter page's edge), so most questions do not move it; a taller page, or one
	# much shorter (the name page, the verdict), tilts it there.
	var sheet := FADE_H + _scroll.custom_minimum_size.y + foot + 12.0
	if _sheet_for != Vector2(_frame.size):
		_sheet_for = Vector2(_frame.size)
		_sheet_shown = -1.0
	if _sheet_shown < 0.0 or sheet > _sheet_shown or sheet < _sheet_shown - SHEET_SLACK:
		_sheet_shown = sheet
	sheet = _sheet_shown
	_room.scene_bottom = frame_h - sheet + FADE_H * 0.5


func _title(text: String) -> void:
	var t := UiKit.heading(text, UiKit.TITLE)
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_root.add_child(t)


func _name_page() -> void:
	_clear()
	_title("%s want to announce their new senior coach" % GameDB.club_name(GameState.coach_club()))
	_root.add_child(UiKit.lbl("What's your name?", UiKit.BODY, UiKit.TEXT))
	var field := UiKit.search_field("", "Your name")
	field.name = "CoachName"
	field.max_length = 28
	_root.add_child(field)
	var go := UiKit.btn("Face the press", UiKit.BODY, true)
	go.name = "InterviewStart"
	go.disabled = true
	field.text_changed.connect(func(t: String): go.disabled = t.strip_edges() == "")
	go.pressed.connect(func():
		_name = field.text.strip_edges()
		GameState.coach_name = _name
		_question())
	_foot.add_child(go)
	_fit()


func _question() -> void:
	_clear()
	var i := _picks.size()
	if i >= Archetypes.QUESTIONS.size():
		_reveal()
		return
	var q: Dictionary = Archetypes.QUESTIONS[i]
	var j: Dictionary = MediaConference.JOURNALISTS.get(str(q["j"]), {})
	var byline := UiKit.lbl("%s, %s" % [str(j.get("name", "")), str(j.get("outlet", ""))],
			UiKit.SMALL, UiKit.club_name_colour(UiKit.club_ink(GameState.coach_club())), true)
	byline.name = "InterviewByline"
	_root.add_child(byline)
	var text := str(q["q"]).replace("<Name>", _name).replace("<Club>", GameDB.club_name(GameState.coach_club())) 			.replace("<Rival>", _beaten())
	var ql := UiKit.lbl(text, UiKit.H2, UiKit.TEXT, true)
	ql.name = "InterviewQuestion"
	ql.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_root.add_child(ql)
	var answers: Array = q["answers"]
	# A wide screen sets the answers two by two, so all four sit above the fold.
	var grid := GridContainer.new()
	grid.columns = 2 if get_viewport_rect().size.x > get_viewport_rect().size.y else 1
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 12)
	_root.add_child(grid)
	for a in range(answers.size()):
		var b := UiKit.btn(str(answers[a][1]), UiKit.BODY)
		b.name = "InterviewAnswer%d" % a
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(0, 52)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.pressed.connect(func():
			_picks.append(a)
			_question())
		grid.add_child(b)
	var count := UiKit.lbl("Question %d of %d" % [i + 1, Archetypes.QUESTIONS.size()], UiKit.SMALL, UiKit.MUTED)
	_root.add_child(count)
	_fit()


## The candidate you beat for the job: a free former senior coach, under the
## name every other screen gives him (real names only, director 2026-11-12),
## the same one for the same club.
func _beaten() -> String:
	var ids := GameState.coaches.keys()
	ids.sort()
	for cid in ids:
		var c: Dictionary = GameState.coaches[cid]
		if str(c.get("status", "")) == "free" and bool(c.get("former_sc", false)) and GameDB.player_display_name(c) != "Player":
			var held_here := false
			for st in c.get("stints", []):
				held_here = held_here or str(st[0]) == GameState.coach_club()
			if not held_here:
				return GameDB.player_display_name(c)
	return "a long list of names"


func _reveal() -> void:
	var arch := GameState.finish_interview(_picks)
	_title("The kind of coach you are")
	for set_key in ["s", "p"]:
		var id := str(arch["held"][set_key])
		var head := UiKit.lbl(str(Archetypes.NAME.get(id, id)), UiKit.H2, UiKit.club_name_colour(UiKit.club_ink(GameState.coach_club())), true)
		head.name = "Archetype_" + set_key
		_root.add_child(head)
		_root.add_child(_line(str(Archetypes.UPSIDE.get(id, "")), UiKit.GOOD))
		_root.add_child(_line(str(Archetypes.COST.get(id, "")), UiKit.BAD))
		if set_key == "s":
			_root.add_child(_line(Archetypes.OFF_PLAN, UiKit.MUTED))
	_root.add_child(_line("How you coach from here can change both, a season at a time.", UiKit.MUTED))
	var go := UiKit.btn("Continue", UiKit.BODY, true)
	go.name = "InterviewDone"
	go.pressed.connect(_leave)
	_foot.add_child(go)
	_fit()


## Back to the draft board when the draft is still to come, else the hub.
func _leave() -> void:
	var from_draft := back_to_draft and GameState.draft != null
	back_to_draft = false
	if from_draft or (GameState.draft != null and not GameState.draft.is_finished() and GameState.coach_club() != ""):
		Router.replace("draft")
	else:
		Router.replace("hub" if GameState.season != null else "main")


func _line(text: String, colour: Color) -> Label:
	var l := UiKit.lbl(text, UiKit.BODY, colour)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


## It cannot be skipped: Back does nothing here.
func handle_back() -> bool:
	return true
