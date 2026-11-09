class_name InterviewScene
extends Control
## The new coach's appointment interview (row 119): his name, then seven
## questions from the press pack, one at a time. Answers show nothing while
## he gives them; at the end the two archetypes they add up to are named with
## everything they do. It cannot be skipped. The hub routes here while
## GameState.interview_due.

var _root: VBoxContainer
var _picks := []
var _name := ""


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	if not GameState.interview_due or GameState.my_club == "":
		Router.replace("hub" if GameState.season != null else "main")
		return
	var bg := ColorRect.new()
	bg.color = UiKit.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 16)
	add_child(margin)
	var page := UiKit.vbox(14)
	page.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	margin.add_child(UiKit.scroll(page))
	_root = page
	_name = GameState.coach_name
	if _name == "":
		_name_page()
	else:
		_question()


func _clear() -> void:
	for c in _root.get_children():
		c.queue_free()


func _title(text: String) -> void:
	var t := UiKit.heading(text, UiKit.TITLE)
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_root.add_child(t)


func _name_page() -> void:
	_clear()
	_title("%s want to announce their new senior coach" % GameDB.club_name(GameState.my_club))
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
	_root.add_child(go)


func _question() -> void:
	_clear()
	var i := _picks.size()
	if i >= Archetypes.QUESTIONS.size():
		_reveal()
		return
	var q: Dictionary = Archetypes.QUESTIONS[i]
	var j: Dictionary = MediaConference.JOURNALISTS.get(str(q["j"]), {})
	var byline := UiKit.lbl("%s, %s" % [str(j.get("name", "")), str(j.get("outlet", ""))],
			UiKit.SMALL, UiKit.club_ink(GameState.my_club), true)
	byline.name = "InterviewByline"
	_root.add_child(byline)
	var text := str(q["q"]).replace("<Name>", _name).replace("<Club>", GameDB.club_name(GameState.my_club))
	var ql := UiKit.lbl(text, UiKit.H2, UiKit.TEXT, true)
	ql.name = "InterviewQuestion"
	ql.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_root.add_child(ql)
	var answers: Array = q["answers"]
	for a in range(answers.size()):
		var b := UiKit.btn(str(answers[a][1]), UiKit.BODY)
		b.name = "InterviewAnswer%d" % a
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(0, 52)
		b.pressed.connect(func():
			_picks.append(a)
			_question())
		_root.add_child(b)
	var count := UiKit.lbl("Question %d of %d" % [i + 1, Archetypes.QUESTIONS.size()], UiKit.SMALL, UiKit.MUTED)
	_root.add_child(count)


func _reveal() -> void:
	var arch := GameState.finish_interview(_picks)
	_title("The kind of coach you are")
	for set_key in ["s", "p"]:
		var id := str(arch["held"][set_key])
		var head := UiKit.lbl(str(Archetypes.NAME.get(id, id)), UiKit.H2, UiKit.club_ink(GameState.my_club), true)
		head.name = "Archetype_" + set_key
		_root.add_child(head)
		_root.add_child(_line(str(Archetypes.UPSIDE.get(id, "")), UiKit.GOOD))
		_root.add_child(_line(str(Archetypes.COST.get(id, "")), UiKit.BAD))
		if set_key == "s":
			_root.add_child(_line(Archetypes.OFF_PLAN, UiKit.MUTED))
	_root.add_child(_line("How you coach from here can change both, a season at a time.", UiKit.MUTED))
	var go := UiKit.btn("Continue", UiKit.BODY, true)
	go.name = "InterviewDone"
	go.pressed.connect(func(): Router.replace("hub"))
	_root.add_child(go)


func _line(text: String, colour: Color) -> Label:
	var l := UiKit.lbl(text, UiKit.BODY, colour)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


## It cannot be skipped: Back does nothing here.
func handle_back() -> bool:
	return true
