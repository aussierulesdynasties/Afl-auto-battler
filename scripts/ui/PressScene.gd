class_name PressScene
extends Control
## The post-match press conference as its own full screen (ruling 3.52, director
## 2026-10-19 "why is press conference still not a full screen scene?", ruled
## again 2026-11-06 Q4): the 2.5D room, the journalist and his outlet, the
## question, each answer with its odds line, and the result shown here once
## the answer lands. Done, Skip or Back returns to the hub.
##
## The hub routes here (Router "press"). A hub that is not the running scene
## (a test or capture that builds one by hand) gets this screen laid over it
## instead, full size, through embed(); it closes the same way.

signal closed

var _embedded := false
var _root: VBoxContainer
var _column: VBoxContainer
var _answered := false


## This screen laid over `host` (full size, not routed); `closed` fires when it
## leaves.
static func embed(host: Control) -> PressScene:
	var s: PressScene = load("res://scripts/ui/PressScene.gd").new()
	s._embedded = true
	host.add_child(s)
	return s


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	if not GameState.media_conference_pending():
		if not _embedded:
			Router.replace("hub" if GameState.season != null else "main")
		else:
			queue_free.call_deferred()
		return
	var bg := ColorRect.new()
	bg.color = UiKit.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(bg)
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	_root = UiKit.vbox(10)
	_root.name = "MediaConference"
	margin.add_child(_root)
	_build()


func _build() -> void:
	_root.add_child(UiKit.top_bar("Press conference", true, null, func():
		return handle_back()))
	var vw := UiKit.view_width(self)
	var vh := UiKit.view_height(self)
	var wide := ScreenLayout.roomy(vw, vh)
	var page := UiKit.vbox(14)
	page.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_root.add_child(UiKit.scroll(page))
	_column = UiKit.vbox(16 if wide else 15)
	_column.name = "MediaAnswers"
	_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var scene: MediaConferenceVignette = null
	if wide:
		var row := UiKit.hbox(24)
		row.name = "MediaRow"
		page.add_child(row)
		if GameState.vignettes_on():
			var stage_w := minf(vw * 0.5, (vh - 120.0) * 1.6)
			var stage := Control.new()
			stage.name = "MediaConferenceStage"
			stage.custom_minimum_size = Vector2(stage_w, stage_w / 1.6)
			stage.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
			stage.clip_contents = true
			row.add_child(stage)
			scene = MediaConferenceVignette.open(stage, GameState.my_club)
		row.add_child(_column)
	else:
		if GameState.vignettes_on():
			var stage := Control.new()
			stage.name = "MediaConferenceStage"
			stage.custom_minimum_size = Vector2(0, minf(300.0, vh * 0.38))
			stage.clip_contents = true
			page.add_child(stage)
			scene = MediaConferenceVignette.open(stage, GameState.my_club)
		page.add_child(_column)
	var shown := _question(wide)
	for it in shown:
		(it as Control).visible = scene == null
	if scene != null:
		scene.ready_for_question.connect(func():
			for it in shown:
				if is_instance_valid(it):
					(it as Control).visible = true)


## The question and its answers; returns what the room reveals when it is
## ready.
func _question(wide: bool) -> Array:
	var prompt := UiKit.vbox(10 if wide else 6)
	prompt.name = "MediaPrompt"
	_column.add_child(prompt)
	var by := UiKit.lbl(str(GameState.media_conference.get("by", "Journalist")),
			UiKit.H2 if wide else UiKit.SMALL, UiKit.MUTED, true)
	by.name = "MediaByline"
	prompt.add_child(by)
	# How he stands with you, and what it does to every answer (director 2026-11-06).
	var standing := GameState.press_standing_line()
	if standing != "":
		var sl := UiKit.lbl(standing, UiKit.BODY if wide else UiKit.SMALL, UiKit.TEXT)
		sl.name = "MediaStanding"
		sl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		prompt.add_child(sl)
	var q := NameInk.label(GameState.press_question_text(), _league_names(), UiKit.H1 if wide else 16, UiKit.TEXT, wide)
	q.name = "MediaQuestion"
	q.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	prompt.add_child(q)
	# The Stats Geek reads your record (ruling 5.48): the record itself, shown.
	var record := GameState.press_record_line()
	if record != "":
		var rl := UiKit.lbl(record, UiKit.BODY if wide else UiKit.SMALL, UiKit.TEXT)
		rl.name = "MediaRecord"
		rl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		prompt.add_child(rl)
	var shown: Array = [prompt]
	var opts: Array = GameState.media_conference.get("options", [])
	for i in range(opts.size()):
		var group := UiKit.vbox(4 if wide else 3)
		group.name = "MediaAnswerGroup_%d" % i
		_column.add_child(group)
		shown.append(group)
		var b := UiKit.btn(str((opts[i] as Dictionary).get("label", "")), UiKit.H2 if wide else 15)
		b.name = "MediaAnswer_%d" % i
		b.custom_minimum_size = Vector2(0, 56 if wide else 48)
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		NameInk.dress_button(b, _league_names())
		b.pressed.connect(_answer.bind(i))
		group.add_child(b)
		# Both ways it can land, their odds and sizes (bible §4), in the page's
		# own ink: the coach is deciding on it.
		var effect := NameInk.label(GameState.press_odds_line(i),
				_league_names(), UiKit.BODY if wide else UiKit.SMALL, UiKit.TEXT)
		effect.name = "MediaAnswerLine_%d" % i
		effect.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		group.add_child(effect)
	var skip := UiKit.btn("Skip press conference", 14)
	skip.name = "MediaSkip"
	skip.flat = not wide
	skip.custom_minimum_size = Vector2(240 if wide else 0, 44)
	if wide:
		skip.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	skip.pressed.connect(func():
		GameState.skip_media_conference()
		_leave())
	_column.add_child(skip)
	shown.append(skip)
	return shown


## The answer lands here, in the room (ruling 3.52: result in-scene).
func _answer(i: int) -> void:
	if _answered:
		return
	var landed := GameState.resolve_media_conference(i)
	_answered = true
	UiKit.clear(_column)
	if landed.is_empty():
		_leave()
		return
	var out := UiKit.vbox(10)
	out.name = "MediaOutcome"
	_column.add_child(out)
	out.add_child(UiKit.heading("After the press conference", UiKit.TITLE))
	var l := UiKit.lbl(str(landed.get("line", "")), 15, UiKit.TEXT)
	l.name = "MediaOutcomeLine"
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	out.add_child(l)
	var extra := press_outcome_extra(landed)
	if extra != "":
		var e := UiKit.lbl(extra, UiKit.SMALL, UiKit.TEXT)
		e.name = "MediaOutcomeExtra"
		e.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		out.add_child(e)
	var ok := UiKit.btn("Done", UiKit.NAME, true)
	ok.name = "MediaOutcomeDone"
	ok.custom_minimum_size = Vector2(0, 48)
	ok.pressed.connect(_leave)
	out.add_child(ok)


## "Trish is warm to you now. The record backs this. It wears off over 2 rounds."
static func press_outcome_extra(landed: Dictionary) -> String:
	var bits: PackedStringArray = []
	var j := str(landed.get("journalist", ""))
	var st: Array = landed.get("standing", [])
	if st.size() == 2 and int(st[0]) != int(st[1]):
		bits.append("%s %s now." % [MediaConference.first_name(j), MediaConference.standing_word(int(st[1]), j)])
	var verdict := str(landed.get("verdict", ""))
	if MediaConference.RECORD_CLAUSE.has(verdict):
		bits.append(str(MediaConference.RECORD_CLAUSE[verdict]))
	var rounds := int(landed.get("fade_rounds", 0))
	if rounds > 0:
		bits.append("It wears off over %d round%s." % [rounds, "" if rounds == 1 else "s"])
	return " ".join(bits)


## Back skips the question (as Skip does) or, once answered, leaves.
func handle_back() -> bool:
	if not _answered:
		GameState.skip_media_conference()
	_leave()
	return true


func _leave() -> void:
	if _embedded:
		closed.emit()
		queue_free()
		return
	if Router.can_go_back():
		Router.back()
	else:
		Router.replace("hub")


var _name_index := {}


func _league_names() -> Dictionary:
	if _name_index.is_empty() and GameState.season != null:
		_name_index = NameInk.from_lists(GameState.season.lists)
	return _name_index
