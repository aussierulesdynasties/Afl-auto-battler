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

## The press room on a phone: never shorter than this, never much taller than
## it is wide (the room is drawn to its frame's height).
const STAGE_MIN := 180.0
const STAGE_TALL := 1.25

var _root: VBoxContainer
## Outside the scroll: the page's one action never sits half under the fold.
var _foot: VBoxContainer
var _frame: VBoxContainer
## The press room (MediaConferenceVignette, the same room as every press
## conference), above the pages on a phone and beside them on a wide screen. It
## stays through every page, so the coach walks in and sits down once.
var _stage: Control
var _wide := false
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
	if _wide:
		var row := UiKit.hbox(24)
		row.name = "InterviewRow"
		margin.add_child(row)
		if _stage != null:
			var stage_w := minf(vw * 0.5, (vh - 120.0) * 1.6)
			_stage.custom_minimum_size = Vector2(stage_w, stage_w / 1.6)
			_stage.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			row.add_child(_stage)
		row.add_child(_frame)
	else:
		margin.add_child(_frame)
		if _stage != null:
			_stage.custom_minimum_size = Vector2(0, STAGE_MIN)
			_frame.add_child(_stage)
	var sc := UiKit.scroll(page)
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_frame.add_child(sc)
	if _stage == null:
		# No room drawn (scenes off): the page sits in the middle, not at the top
		# of an empty screen.
		page.size_flags_vertical = Control.SIZE_EXPAND_FILL
		page.alignment = BoxContainer.ALIGNMENT_CENTER
	_foot = UiKit.vbox(0)
	_frame.add_child(_foot)
	_root = page
	if _stage != null:
		MediaConferenceVignette.open(_stage, GameState.coach_club())
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


## On a phone the room takes the height the page leaves free (from STAGE_MIN to
## STAGE_TALL of its width), so the screen has no empty block under the answers.
func _fit() -> void:
	if _stage == null or _wide:
		return
	# A frame first, so the wrapped labels report their real height.
	await get_tree().process_frame
	if not is_instance_valid(_stage) or not is_inside_tree():
		return
	var need := _root.get_combined_minimum_size().y
	var room := _frame.size.y - _foot.get_combined_minimum_size().y - 2.0 * _frame.get_theme_constant("separation")
	_stage.custom_minimum_size.y = clampf(room - need, STAGE_MIN, maxf(STAGE_MIN, _frame.size.x * STAGE_TALL))


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


## The candidate you beat for the job: a free former senior coach, always by
## his fictional name (never a real person), the same one for the same club.
func _beaten() -> String:
	var ids := GameState.coaches.keys()
	ids.sort()
	for cid in ids:
		var c: Dictionary = GameState.coaches[cid]
		if str(c.get("status", "")) == "free" and bool(c.get("former_sc", false)) and str(c.get("generic_name", "")) != "":
			var held_here := false
			for st in c.get("stints", []):
				held_here = held_here or str(st[0]) == GameState.coach_club()
			if not held_here:
				return str(c["generic_name"])
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
