extends Control
## A club's coaching staff: six jobs, one row each, then the list manager and
## the head of high performance (the Council's eight seats). At your club the
## senior coach is you; the other seven work for you, each pushing for his
## agenda, with his loyalty to you shown. Tap a coach for his profile.
## Other clubs' staffs are one tap away. After the season your open jobs
## show a shortlist (appoint or auto-fill) and assistants can be released.

var _root: VBoxContainer
var _club := ""
var _sheet: Control
var _others_open := false
## The open job whose shortlist is showing: one at a time, senior first.
var _open_job := ""


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.season == null:
		Router.replace("main")
		return
	_club = GameState.my_club
	# Your club's colour behind the page, as on the hub and match day
	# (director, 2026-10-10: every screen in the gameday style).
	add_child(ClubBackdrop.new().setup(GameState.my_club))
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	_root = UiKit.vbox(UiKit.Space.ROOM)
	margin.add_child(_root)
	get_viewport().size_changed.connect(func():
		if not UiKit.keyboard_resize(self):
			_build())
	_build()
	FirstVisitIntro.show_if_due.call_deferred(self, "staff")


func _build() -> void:
	if not is_inside_tree():
		return
	UiKit.clear(_root)
	var mine := _club == GameState.my_club
	_root.add_child(UiKit.top_bar("Staff", true))
	var body := UiKit.vbox(0)
	body.name = "StaffRows"
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	# Whose staff this is: the club's guernsey and, where its colour reads on
	# the page, its ink. A dark club is carried by the guernsey alone.
	var who_h := UiKit.hbox(UiKit.GAP)
	who_h.add_child(UiKit.club_marker(_club, 26.0))
	var head := UiKit.club_title(GameDB.club_name(_club), UiKit.H2, _club, UiKit.BG)
	head.name = "StaffClub"
	head.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	if head is Label:
		(head as Label).autowrap_mode = TextServer.AUTOWRAP_OFF
	who_h.add_child(head)
	body.add_child(who_h)
	body.add_child(UiKit.spacer(UiKit.Space.TIGHT))
	# What the figures on the cards are, once, for the whole page.
	if mine and not GameState.first_staff_open():
		var ctx := UiKit.lbl("Loyalty to you is out of 100. At %d or less, they leave after the season." % Council.WALK_LINE,
				UiKit.SECONDARY, UiKit.MUTED)
		ctx.name = "StaffContext"
		ctx.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		body.add_child(ctx)
	body.add_child(UiKit.spacer(UiKit.Space.ROOM))
	var staff := GameState.club_staff(_club)
	var open := {}
	if mine:
		for v in GameState.staff_vacancies:
			open[str(v["job"])] = v
	if not open.has(_open_job):
		_open_job = ""
		for job in Coaches.JOBS:
			if open.has(job):
				_open_job = job
				break
	# A created club's first staff (director 2026-11-15): we hire all five.
	if mine and GameState.first_staff_open():
		body.add_child(_first_staff_intro(open.size()))
		body.add_child(UiKit.spacer(UiKit.Space.CLOSE))
	# A PC lays the staff out as cards across the screen, not one stretched
	# column (director, 2026-10-10: no phone UI on a PC).
	var w := UiKit.view_width(self)
	var wide := ScreenLayout.roomy(w, UiKit.view_height(self))
	var grid: GridContainer = null
	if wide:
		grid = GridContainer.new()
		grid.name = "StaffGrid"
		# Each coach's grades on his card (director's pick B, 2026-11-26), on
		# two rows that fit the window: three across for the six coaching jobs,
		# four across since the Council's list manager and head of high
		# performance joined them (eight cards).
		grid.columns = 4
		grid.add_theme_constant_override("h_separation", UiKit.Space.PAD)
		grid.add_theme_constant_override("v_separation", UiKit.Space.PAD)
		body.add_child(grid)
	for job in Coaches.JOBS:
		var row: Control
		var coach := false
		if job == "SC" and mine:
			row = _you_row(grid != null)
		elif open.has(job) and job == _open_job:
			row = _vacancy_card(job, open[job])
		elif open.has(job):
			row = _vacancy_row(job)
		elif staff.has(job):
			row = _coach_row(job, staff[job], mine and GameState.can_release_staff())
			coach = true
		else:
			row = _empty_row(job)
		if grid != null:
			var card := _card(job == "SC" and mine)
			_lines_on_top(row)
			if coach:
				var cv := UiKit.vbox(UiKit.Space.ROOM)
				cv.add_child(row)
				cv.add_child(_grades(staff[job], job))
				card.add_child(cv)
			else:
				card.add_child(row)
			grid.add_child(card)
		else:
			body.add_child(row)
			body.add_child(UiKit.rule())
	# The two council seats beyond the coaching jobs: the list manager and the
	# head of high performance (Council.gd), at every club.
	for m in Council.members(GameState, _club):
		if not Council.OFFICE_JOBS.has(str(m["job"])):
			continue
		var orow := _office_row(m, mine)
		if grid != null:
			var ocard := _card(false)
			_lines_on_top(orow)
			ocard.add_child(orow)
			grid.add_child(ocard)
		else:
			body.add_child(orow)
			body.add_child(UiKit.rule())

	body.add_child(UiKit.spacer(UiKit.Space.LOOSE))
	var others := UiKit.btn("Our club" if not mine else "Another club's staff", UiKit.BODY)
	others.name = "OtherClubs"
	# On a PC it reads as a button (an outline), not a stray line of text.
	others.flat = not _others_open and not wide
	if wide:
		others.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		others.custom_minimum_size = Vector2(220, 44)
	others.pressed.connect(func():
		if not mine:
			_club = GameState.my_club
			_others_open = false
		else:
			_others_open = not _others_open
		_build())
	body.add_child(others)
	if _others_open and mine:
		var opts := []
		for code in GameDB.active_clubs(GameState.season_year):
			if code != GameState.my_club:
				opts.append([code, GameDB.club_short(code)])
		var cols := 3 if UiKit.view_width(self) < 520.0 else 6
		body.add_child(UiKit.choice_grid("StaffClubPick", opts, "", cols, func(code):
			_club = str(code)
			_others_open = false
			_build()))
	_root.add_child(UiKit.scroll(body))


## A PC card's lines start at its top, so the room a row keeps falls under them, not above.
func _lines_on_top(row: Control) -> void:
	var v := row as VBoxContainer
	if v == null:
		for vb in row.find_children("*", "VBoxContainer", true, false):
			v = vb
			break
	if v != null:
		v.alignment = BoxContainer.ALIGNMENT_BEGIN


## A PC card: the panel with a 2 px rule of the club's colour along its top.
## Yours, the senior coach's, carries the club's wash as well: the one card
## on the page that is you.
func _card(yours: bool) -> PanelContainer:
	var card := UiKit.panel(UiKit.PANEL, UiKit.Space.PAD)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var sb := (card.get_theme_stylebox("panel") as StyleBoxFlat).duplicate() as StyleBoxFlat
	sb.border_width_top = 2
	sb.border_color = _rule_ink()
	sb.content_margin_top = UiKit.Space.PAD + 2
	if yours:
		sb.bg_color = UiKit.PANEL.lerp(UiKit.team_wash(), 0.28)
		sb.border_width_top = 3
	card.add_theme_stylebox_override("panel", sb)
	return card


## The club's colour for a rule: its vivid colour, or for a black-and-white
## club the white of its stripes.
func _rule_ink() -> Color:
	if UiKit.club_is_black(_club):
		return UiKit.TEXT
	return UiKit.club_vivid(_club, UiKit.PANEL)


## His grades on his PC card, a line each under a rule, the grade at the
## card's right edge, and how he fits this job.
func _grades(c: Dictionary, job: String) -> Control:
	var g := UiKit.vbox(UiKit.Space.HAIR)
	g.name = "Grades_" + job
	g.add_child(UiKit.rule())
	g.add_child(UiKit.spacer(UiKit.Space.TIGHT))
	for key in Coaches.SKILLS:
		g.add_child(_grade_row(str(Coaches.SKILL_LABEL[key]), Coaches.grade(Coaches.skill(c, key))))
	if str(c.get("status", "")) == "club":
		g.add_child(_grade_row("Fit for this job", Coaches.grade(Coaches.role_fit(c, job))))
	return g


func _grade_row(label: String, value: String) -> Control:
	var row := UiKit.hbox(UiKit.GAP)
	var l := UiKit.lbl(label, UiKit.SMALL, UiKit.MUTED)
	l.autowrap_mode = TextServer.AUTOWRAP_OFF
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(l)
	var v := UiKit.line(value, UiKit.SMALL, UiKit.TEXT, true)
	v.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(v)
	return row


## A row's head: his job over his name, and at the right what the coach reads
## at a glance (loyalty to you, or your own standing).
func _head(role: String, who: String, who_ink: Color, right: Control, wide: bool, sub := "") -> HBoxContainer:
	var h := UiKit.hbox(UiKit.GAP)
	var v := UiKit.vbox(0)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	var r := UiKit.ellipsis(role, UiKit.SMALL, UiKit.MUTED, true)
	r.name = "Role"
	v.add_child(r)
	var n := UiKit.ellipsis(who, UiKit.HEADING if wide else UiKit.NAME, who_ink, true)
	n.name = "Name"
	v.add_child(n)
	if sub != "":
		v.add_child(UiKit.lbl(sub, UiKit.SECONDARY, UiKit.MUTED))
	h.add_child(v)
	if right != null:
		right.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		h.add_child(right)
	return h


## A figure in the scoreboard face over the word for it, right-aligned.
func _figure(value: int, word: String, ink := UiKit.TEXT) -> VBoxContainer:
	var v := UiKit.vbox(0)
	var f := UiKit.figure(str(value), UiKit.NUMBER, ink)
	f.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	v.add_child(f)
	var w := UiKit.lbl(word, UiKit.SMALL, ink if ink != UiKit.TEXT else UiKit.MUTED, ink != UiKit.TEXT)
	w.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	w.autowrap_mode = TextServer.AUTOWRAP_OFF
	v.add_child(w)
	return v


## You: the senior coach's calls are yours, so there are no grades to show;
## your standing with the club, Respect and Authority, takes their place.
func _you_row(framed := false) -> Control:
	var v := UiKit.vbox(UiKit.Space.CLOSE)
	v.name = "StaffRow_SC"
	var stand := UiKit.hbox(UiKit.Space.LOOSE if framed else UiKit.Space.ROOM)
	stand.name = "YourStanding"
	stand.add_child(_figure(Promises.respect(GameState), "Respect"))
	stand.add_child(_figure(Promises.authority(GameState), "Authority"))
	var you_ink := UiKit.TEXT if UiKit.club_is_black(GameState.my_club) else _ink(GameState.my_club)
	v.add_child(_head("Senior coach", "You", you_ink, stand, framed))
	var l := UiKit.lbl("Selection, tactics and training are your calls.", UiKit.SECONDARY, UiKit.TEXT)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(l)
	if not framed:
		return _padded(v)
	# On a PC card, what moves the two figures sits where a coach's grades do.
	var how := UiKit.vbox(UiKit.Space.HAIR)
	how.name = "StandingHow"
	how.add_child(UiKit.spacer(UiKit.Space.CLOSE))
	how.add_child(UiKit.rule())
	how.add_child(UiKit.spacer(UiKit.Space.TIGHT))
	for t in ["Keeping your word builds Respect.", "Hard calls build Authority."]:
		var hl := UiKit.lbl(t, UiKit.SMALL, UiKit.MUTED)
		hl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		how.add_child(hl)
	v.add_child(how)
	v.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	return v


func _coach_row(job: String, c: Dictionary, releasable := false) -> Control:
	var b := Button.new()
	b.name = "StaffRow_" + job
	b.flat = true
	b.custom_minimum_size.y = 68
	b.mouse_filter = Control.MOUSE_FILTER_PASS
	b.focus_mode = Control.FOCUS_NONE
	for state in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		b.add_theme_stylebox_override(state, StyleBoxEmpty.new())
	var wide := ScreenLayout.roomy(UiKit.view_width(self), UiKit.view_height(self))
	var mine := _club == GameState.my_club
	var m := _member(str(c.get("cid", "")))
	var v := UiKit.vbox(UiKit.Space.THIN)
	# A phone's row keeps a little air above and below its lines; a PC card's
	# lines start at the card's top, level with its neighbours'.
	var air := 0 if wide else UiKit.Space.CLOSE
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.offset_top = air
	v.offset_bottom = -air
	v.alignment = BoxContainer.ALIGNMENT_BEGIN if wide else BoxContainer.ALIGNMENT_CENTER
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(v)
	v.add_child(_head(str(Coaches.JOB_LABEL[job]), GameDB.player_display_name(c), UiKit.TEXT,
			_loyalty(job, m) if mine else null, wide, "" if wide else Coaches.headline(c)))
	# On a PC his grades are on the card; a phone's row says under his name what he is good at.
	for l in _council_lines(job, m, mine, wide):
		v.add_child(l)
	# What you have promised him, and what a broken promise cost (T5.Q16).
	var word := _word_line(c)
	if word != null:
		v.add_child(word)
	b.pressed.connect(func(): _sheet = CoachSheet.open(self, c))
	# It answers a finger as every button does: it presses in, sounds and buzzes.
	UiKit.feel(b, "soft")
	var expiring := releasable and GameState.expiring_staff().has(c)
	if expiring:
		var stance := CoachMarket.assistant_stance(c, GameState.season_year)
		var term := UiKit.lbl("Contract ends. " + str(stance["text"]), UiKit.SMALL, UiKit.EMPH)
		term.name = "ContractEnds_" + job
		term.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(term)
	for n in v.find_children("*", "Control", true, false):
		n.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# The row grows with its lines (a wrapped term, a promise): a Button does
	# not size to its children, so it follows the column's height, never
	# less than the plain row (bug-bash 7).
	var fit := func(): b.custom_minimum_size.y = maxf(0.0 if wide else 68.0, v.get_combined_minimum_size().y + 2.0 * air)
	v.minimum_size_changed.connect(fit)
	fit.call()
	if not releasable:
		return b
	# The offseason: an assistant can be let go (no payout, no negotiation);
	# one whose term is up can also be kept, on his terms.
	var h := UiKit.hbox(UiKit.GAP)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(b)
	# Re-sign stacks over Release, so his lines keep the row's width at
	# phone size instead of wrapping a word a line (bug-bash 7).
	var acts: BoxContainer = h
	if expiring:
		acts = UiKit.vbox(UiKit.GAP)
		acts.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(acts)
		var keep := UiKit.btn("Re-sign", 14)
		keep.name = "Resign_" + job
		keep.custom_minimum_size = Vector2(92, 44)
		keep.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		keep.pressed.connect(func():
			GameState.resign_staff(str(c["cid"]))
			_build())
		acts.add_child(keep)
	var rel := UiKit.btn("Release", 14)
	rel.name = "Release_" + job
	rel.custom_minimum_size = Vector2(92, 44)
	rel.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	rel.pressed.connect(func():
		GameState.release_staff(str(c["cid"]))
		_build())
	acts.add_child(rel)
	return h


func _word_line(c: Dictionary) -> Label:
	var mine := GameState.my_club
	if CoachMarket.holds_promise(c, mine):
		var l := UiKit.lbl("Promised senior assistant by %d" % int(c["promise"]["by"]), UiKit.SMALL, UiKit.EMPH, true)
		l.name = "Promise_" + str(c.get("job", ""))
		return l
	var n := CoachMarket.broken_by(c, mine)
	if n > 0:
		var l := UiKit.lbl("You broke %s to him. Our offers are %d%% less likely to land" % [
				"a promise" if n == 1 else "%d promises" % n, int(round(CoachMarket.BROKEN_TRUST * 100.0 * n))],
				UiKit.SMALL, UiKit.BAD, true)
		l.name = "Broken_" + str(c.get("job", ""))
		return l
	return null


## One of your jobs is open: why, a short list to choose from, or let the
## club pick (the same judgement the AI clubs use).
func _vacancy_card(job: String, vac: Dictionary) -> Control:
	var v := UiKit.vbox(UiKit.Space.CLOSE)
	v.name = "Vacancy_" + job
	v.add_child(UiKit.lbl("%s vacancy" % _job_title(job), UiKit.BODY, UiKit.TEXT, true))
	if str(vac.get("reason", "")) != "":
		var why := UiKit.lbl(str(vac["reason"]), UiKit.SMALL, UiKit.MUTED)
		why.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(why)
	var cap := UiKit.lbl("Each figure compares him with an average coach.", UiKit.SMALL, UiKit.MUTED)
	cap.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(cap)
	# By name, not by the club's ranking: the order says nothing about which
	# of them to take.
	var list := GameState.staff_shortlist(job)
	list.sort_custom(func(a, b): return GameDB.player_display_name(a) < GameDB.player_display_name(b))
	for i in range(list.size()):
		v.add_child(UiKit.rule())
		v.add_child(_candidate_row(job, list[i], i))
	var auto := UiKit.btn("Auto-fill", UiKit.BODY)
	auto.name = "AutoFill_" + job
	auto.custom_minimum_size = Vector2(0, 44)
	auto.pressed.connect(func():
		GameState.auto_fill_staff(job)
		_build())
	v.add_child(auto)
	return _padded(v)


func _candidate_row(job: String, c: Dictionary, i: int) -> Control:
	var h := UiKit.hbox(UiKit.GAP)
	h.name = "Candidate_%s_%d" % [job, i]
	var info := UiKit.vbox(UiKit.Space.HAIR)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(info)
	var who := Button.new()
	who.flat = true
	who.text = GameDB.player_display_name(c)
	who.alignment = HORIZONTAL_ALIGNMENT_LEFT
	who.add_theme_font_override("font", UiKit.BOLD)
	UiKit.set_font_size(who, UiKit.BODY)
	who.custom_minimum_size.y = 32
	who.pressed.connect(func(): _sheet = CoachSheet.open(self, c))
	info.add_child(who)
	var facts := UiKit.lbl("%s · %s · %s" % [Coaches.whereabouts(c), Coaches.rep_word(c),
			Coaches.experience_word(c, job)], UiKit.SMALL, UiKit.MUTED)
	facts.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_child(facts)
	# The gate: what he does in this job, and what he costs, with the size.
	var lines := CoachEffects.hire_lines(c, job, GameState.season_year)
	var k := 0
	for side in ["gain", "cost"]:
		for line in lines[side]:
			info.add_child(UiKit.stake_row("%s: %s" % ["Gain" if side == "gain" else "Cost", str(line)],
					"Stake_%s_%d_%d" % [job, i, k]))
			k += 1
	var pick := UiKit.btn("Appoint", 14)
	pick.name = "Appoint_%s_%d" % [job, i]
	pick.custom_minimum_size = Vector2(92, 44)
	pick.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	pick.pressed.connect(func():
		GameState.appoint_staff(job, str(c["cid"]))
		_build())
	h.add_child(pick)
	return h


## The first-staff step's heading: what is open and what happens if we wait.
func _first_staff_intro(n: int) -> Control:
	var v := UiKit.vbox(UiKit.Space.SLIM)
	v.name = "FirstStaff"
	v.add_child(UiKit.lbl("Hire our first staff", UiKit.HEADING, _ink(GameState.my_club), true))
	for t in ["A new club: nobody on our staff yet.",
			"%s to fill before Round 1." % ("One job" if n == 1 else "%d jobs" % n),
			"Any job still open at the first bounce gets the club's pick."]:
		var l := UiKit.lbl(t, UiKit.SMALL, UiKit.TEXT)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(l)
	return v


## An open job whose shortlist is closed: one tap opens it.
func _vacancy_row(job: String) -> Control:
	var h := UiKit.hbox(UiKit.GAP)
	h.name = "Vacancy_" + job
	var v := UiKit.vbox(UiKit.Space.HAIR)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_child(UiKit.lbl(str(Coaches.JOB_LABEL[job]), UiKit.SMALL, UiKit.TEXT, true))
	v.add_child(UiKit.lbl("Vacant", UiKit.BODY, UiKit.EMPH, true))
	h.add_child(v)
	var see := UiKit.btn("See the shortlist", 14)
	see.name = "Shortlist_" + job
	see.custom_minimum_size = Vector2(0, 44)
	see.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	see.pressed.connect(func():
		_open_job = job
		_build())
	h.add_child(see)
	return _padded(h)


func _job_title(job: String) -> String:
	var label := str(Coaches.JOB_LABEL[job])
	return label if job == "SC" or job == "SA" else label + " coach"


## A list manager or head of high performance: the seat, the name, what they
## push for and (at your club) where their loyalty stands. On a PC card, what
## the seat looks after sits where a coach's grades do.
const OFFICE_ABOUT := {
	"LM": "Looks after the list: the draft, trades and contracts.",
	"HP": "Looks after the bodies: fitness, loads and injuries.",
}


func _office_row(m: Dictionary, mine: bool) -> Control:
	var job := str(m["job"])
	var wide := ScreenLayout.roomy(UiKit.view_width(self), UiKit.view_height(self))
	var v := UiKit.vbox(UiKit.Space.THIN)
	v.name = "StaffRow_" + job
	v.add_child(_head(str(Council.OFFICE_LABEL[job]), str(m["name"]), UiKit.TEXT,
			_loyalty(job, m) if mine else null, wide))
	for l in _council_lines(job, m, mine, wide):
		v.add_child(l)
	if wide:
		var about := UiKit.vbox(UiKit.Space.HAIR)
		about.name = "About_" + job
		about.add_child(UiKit.spacer(UiKit.Space.CLOSE))
		about.add_child(UiKit.rule())
		about.add_child(UiKit.spacer(UiKit.Space.TIGHT))
		var t := UiKit.lbl(str(OFFICE_ABOUT.get(job, "")), UiKit.SMALL, UiKit.MUTED)
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		about.add_child(t)
		v.add_child(about)
		return v
	return _padded(v)


## The council member in a seat at this club, by id.
func _member(id: String) -> Dictionary:
	for x in Council.members(GameState, _club):
		if str(x["id"]) == id:
			return x
	return {}


## Loyalty to you as a figure, the word for it under: the fact on his card the
## coach reads first. Restless or worse, it is in bold.
func _loyalty(job: String, m: Dictionary) -> Control:
	if m.is_empty():
		return null
	var lv := Council.loyalty(GameState, m)
	var f := _figure(lv, Council.loyalty_word(lv).replace(" to you", ""))
	f.name = "Loyalty_" + job
	if lv <= Council.RESTLESS_LINE:
		var w := f.get_child(1) as Label
		w.add_theme_color_override("font_color", UiKit.TEXT)
		w.add_theme_font_override("font", UiKit.BOLD)
	return f


## What a council member pushes for, and at your club the biggest reason
## behind his loyalty to you now (a rival club's loyalties stay theirs).
func _council_lines(job: String, m: Dictionary, mine: bool, wide: bool) -> Array:
	var out := []
	if m.is_empty():
		return out
	var ag := UiKit.lbl("Pushes to " + Council.agenda_label(str(m["agenda"])).to_lower(), UiKit.SECONDARY, UiKit.TEXT)
	ag.name = "Agenda_" + job
	ag.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	out.append(ag)
	if not mine:
		return out
	var marks := Opinion.breakdown(GameState.relations, str(m["key"]))
	if not marks.is_empty():
		# On a PC card the reason keeps to one line, so eight cards still fit
		# two rows at 960x540 without scrolling; a phone row has the room for
		# how long it lasts.
		var text := "%s, %+d" % [str(marks[0]["why"]), int(marks[0]["points"])] if wide \
				else Opinion.mark_text(marks[0])
		var why := UiKit.lbl(text, UiKit.SMALL, UiKit.MUTED)
		why.name = "LoyaltyWhy_" + job
		why.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		out.append(why)
	return out


## A job nobody holds (an expansion club before it has hired).
func _empty_row(job: String) -> Control:
	var v := UiKit.vbox(UiKit.Space.HAIR)
	v.name = "StaffRow_" + job
	v.custom_minimum_size.y = 52
	v.add_child(UiKit.lbl(str(Coaches.JOB_LABEL[job]), UiKit.SMALL, UiKit.MUTED))
	v.add_child(UiKit.lbl("Vacant", UiKit.BODY, UiKit.MUTED))
	return _padded(v)


## A club's colour as ink when it reads and is not red or orange (BAD, the
## primary action); else TEXT, the guernsey beside it carrying the side.
func _ink(code: String) -> Color:
	var col := UiKit.club_vivid(code, UiKit.BG)
	if col.s > 0.4 and (col.h < 0.09 or col.h > 0.96):
		return UiKit.TEXT
	return col


func _padded(c: Control) -> Control:
	var m := MarginContainer.new()
	m.add_theme_constant_override("margin_top", UiKit.Space.CLOSE)
	m.add_theme_constant_override("margin_bottom", UiKit.Space.CLOSE)
	m.add_child(c)
	return m


## Router back hook: close a profile first, then return to your own staff,
## then leave.
func handle_back() -> bool:
	if FirstVisitIntro.close_open(self):
		return true
	if is_instance_valid(_sheet):
		_sheet.queue_free()
		_sheet = null
		return true
	if _club != GameState.my_club:
		_club = GameState.my_club
		_build()
		return true
	return false
