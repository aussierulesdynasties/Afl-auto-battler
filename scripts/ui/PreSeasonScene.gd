extends Control
## The pre-season (PreSeason.gd, rule 69a), between the off-season wrap and Round 1.
## One job per stop:
##   the meetings   each player's stat focus for the season, and any position
##                  he sets out to learn;
##   the plan       the season fitness plan, which books its weeks of running;
##   the week       one action: Running, Game plan drilling or Team bonding;
##   the time trial who ran well and who did not;
##   the match       the club you play, the side and plan you take and which
##                   prospects you trial, then what the match showed;
##   the papers     their ladder, and the story to answer.
## Every choice says what it gains and what it costs in words. Nothing is
## recommended. The hub sends the coach here while a pre-season is running and
## takes him back when Round 1 is next.

const WIDE := 900.0
## A primary button's fill must stand off the page by at least this much, or
## the club's readable ink carries it (Fremantle's purple on the dark page).
const FILL_MIN_CONTRAST := 2.0

var _root: VBoxContainer
var _settings: Control
var _last_stop := ""


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.season == null:
		Router.replace("main")
		return
	if not GameState.preseason_active():
		Router.replace("hub")
		return
	add_child(ClubBackdrop.new().setup(GameState.my_club).live())
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 12)
	add_child(margin)
	_root = UiKit.vbox(10)
	margin.add_child(_root)
	get_viewport().size_changed.connect(_on_resize)
	_build()
	# The Rookie Draft follows the National Draft: your pick waits here.
	if RookieList.waiting(GameState):
		RookieDraftSheet.open.call_deferred(self, _build)
	# Essendon's 2016 top-up players, when you coach them (Supplements saga).
	elif YearEvents.top_up_waiting(GameState):
		TopUpSheet.open.call_deferred(self, _build)
	FirstVisitIntro.show_if_due.call_deferred(self, "preseason")


func _on_resize() -> void:
	if is_inside_tree() and GameState.preseason_active() and not UiKit.keyboard_resize(self):
		_build()


func _wide() -> bool:
	return UiKit.view_width(self) >= WIDE


func _build() -> void:
	var stop: String = GameState.preseason_stop()
	# A rebuild after a tap keeps the page where the thumb left it; a new stop
	# starts at the top, with nothing picked.
	var places: Array = UiKit.scroll_places(_root) if stop == _last_stop else []
	if stop != _last_stop:
		_meet_open = ""
		_meet_sel = {}
		_focus_draft = {}
		_plan_draft = ""
		_drill_group_sel = ""
	_last_stop = stop
	UiKit.clear(_root)
	var settings := UiKit.btn("Settings", UiKit.SECONDARY)
	settings.name = "PreSeasonSettings"
	settings.flat = true
	settings.custom_minimum_size = Vector2(64, 44)
	settings.add_theme_color_override("font_color", UiKit.TEXT)
	settings.pressed.connect(func(): _settings = OptionsSheet.open(self, true))
	_root.add_child(UiKit.top_bar("Pre-season", false, settings))

	var page := UiKit.vbox(UiKit.SECTION)
	page.name = "PreSeasonPage"
	_root.add_child(UiKit.scroll(page))
	page.add_child(_header(stop))
	match stop:
		"meetings":
			page.add_child(_meetings_section())
		"plan":
			page.add_child(_plan_section())
		"week":
			page.add_child(_week_section())
		"story":
			page.add_child(_story_cards())
			page.add_child(_summer_strip())
		"practice":
			if GameState.practice_played():
				page.add_child(_match_report(GameState.preseason_practice().get("report", {}), "Practice", GameState.draftee_pool))
			else:
				page.add_child(_practice_setup())
		"trial":
			if _wide():
				# A PC: the time trial on the left, the summer so far beside it.
				var cols := UiKit.hbox(28)
				var left := _trial_section()
				left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				left.size_flags_stretch_ratio = 0.5
				cols.add_child(left)
				var right := _summer_strip()
				right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				right.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
				cols.add_child(right)
				page.add_child(cols)
			else:
				page.add_child(_trial_section())
				page.add_child(_summer_strip())
		"papers":
			if _wide():
				# A PC: the story on the left with the summer under it, the ladder
				# beside them (its 18 blurbs need the height).
				var pcols := UiKit.hbox(28)
				var pl := UiKit.vbox(8)
				pl.name = "PapersLeft"
				pl.add_child(_papers_story())
				pl.add_child(_summer_strip())
				pl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				pcols.add_child(pl)
				var pr := _papers_ladder()
				pr.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				# Three columns of six clubs, each with its whole blurb under it: the
				# ladder takes the wider share.
				pr.size_flags_stretch_ratio = PAPERS_LADDER_SHARE
				pcols.add_child(pr)
				page.add_child(pcols)
			else:
				page.add_child(_papers_story())
				page.add_child(_papers_ladder())
	if not _wide():
		# Air under the last row, so the page never ends hard against the footer.
		page.add_child(UiKit.spacer(12))
	_root.add_child(UiKit.rule())
	_sync_meeting_sheet()
	_root.add_child(_actions(stop))
	if not places.is_empty():
		UiKit.restore_places(_root, places)


## Whose pre-season it is and where it stands: the club's marker and colour,
## then the one big line.
func _header(stop: String) -> Control:
	var v := UiKit.vbox(4)
	v.name = "PreSeasonHeader"
	var who := UiKit.hbox(10)
	who.add_child(UiKit.club_marker(GameState.my_club, 32.0))
	var names := UiKit.vbox(0)
	names.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var club := UiKit.lbl(GameDB.club_name(GameState.my_club), UiKit.NAME, UiKit.club_name_colour(UiKit.club_ink(GameState.my_club)), true)
	club.name = "PreSeasonClub"
	names.add_child(club)
	names.add_child(UiKit.lbl("Before the %d season" % GameState.season_year, UiKit.SECONDARY, UiKit.TEXT))
	who.add_child(names)
	v.add_child(who)
	var hero := UiKit.heading(_hero(stop), UiKit.TITLE)
	hero.name = "PreSeasonHero"
	hero.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var sub := UiKit.lbl(_hero_sub(stop), UiKit.BODY, UiKit.TEXT)
	sub.name = "PreSeasonSub"
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	if _wide():
		# A PC is short: the club and the big line share one row.
		names.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		for n in names.get_children():
			(n as Label).autowrap_mode = TextServer.AUTOWRAP_OFF
		who.add_theme_constant_override("separation", 14)
		_hang_watch(stop, who, WATCH_WIDE)   # between the club and the big line it belongs to
		var words := UiKit.vbox(0)
		words.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		words.add_child(hero)
		words.add_child(sub)
		who.add_child(words)
	else:
		_hang_watch(stop, who, WATCH)   # at the end of the club's row, down beside the big line
		v.add_child(hero)
		v.add_child(sub)
	if stop == "meetings":
		# Every line ticked at once, top right, where the board had it.
		var every := UiKit.btn("Select every line", UiKit.SECONDARY)
		every.name = "MeetAllLines"
		every.custom_minimum_size = Vector2(0, 40)
		every.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		every.pressed.connect(func():
			var ids := []
			for p in GameState.my_list:
				ids.append(str(p["id"]))
			_tick_many(ids, true))
		who.add_child(every)
	v.add_child(_club_rule())
	return v


## The stopwatch at the time trial, hung from the top of the club's row in a
## slot with no height of its own: the header is exactly as tall as without
## it and nothing under it moves. Steel and white, never tinted; no tap.
func _hang_watch(stop: String, who: HBoxContainer, height: float) -> void:
	if stop != "trial":
		return
	var watch := UiArt.view("stopwatch", height)
	if watch == null:
		return
	watch.name = "TrialStopwatch"
	var slot := Control.new()
	slot.name = "TrialStopwatchSlot"
	slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	slot.custom_minimum_size = Vector2(watch.custom_minimum_size.x, 0)
	slot.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	watch.size = watch.custom_minimum_size
	slot.add_child(watch)
	who.add_child(slot)


## The stopwatch at the time trial stop (director, 2026-10-14: "Bigger, in
## real colours"). It may not move anything, so it is as tall as the words it
## stands beside: on a phone the club's row and the big line (56), on a wide
## screen the one row the header is (40).
const WATCH := 56.0
const WATCH_WIDE := 40.0


func _hero(stop: String) -> String:
	match stop:
		"meetings":
			return "Player meetings"
		"plan":
			return "The season fitness plan"
		"trial":
			return "The time trial"
		"practice":
			return "The practice match"
		"papers":
			return "The papers"
		"story":
			return "Team bonding, week %d" % GameState.preseason_week()
	return "Week %d of %d" % [mini(PreSeason.weeks(), GameState.preseason_week() + 1), PreSeason.weeks()]


func _hero_sub(stop: String) -> String:
	match stop:
		"meetings":
			return "Tap a name to open his meeting, or tick players to give them one stat focus together. A position change starts at the practice match."
		"plan":
			return "It runs through summer and the season. Each plan books its own weeks of running. The other weeks are ours to fill."
		"trial":
			return "Two kilometres at the end of week 3. This is the order they finished. No rating or fitness moved because of it."
		"practice":
			var opp := GameDB.club_name(GameState.practice_opponent())
			if GameState.practice_played():
				return "End of week 7, against %s. It counts for nothing on the ladder. What it showed is below. Week 8 is quiet: no training, and the papers come out." % opp
			return "End of week 7: one match against %s. It counts for nothing on the ladder." % opp
		"papers":
			return "Week 8. Training is done. The papers have printed their ladder. This is what they want to know."
		"story":
			return "This week's card. Pick how it goes."
	var w := GameState.preseason_week() + 1
	if w <= 3:
		return "One job this week. The time trial follows week 3."
	return "One job this week. The practice match follows week 7."


# ---------------------------------------------------------------------------
# The papers: the story to answer, and the ladder they printed
# ---------------------------------------------------------------------------
## The one story, with the three answers (back it, deflect, talk it up), each
## with what it gains and what it costs; or, once answered, what you said.
func _papers_story() -> Control:
	var v := UiKit.vbox(8)
	v.name = "PapersStory"
	var rec: Dictionary = GameState.papers_record()
	var card: Dictionary = GameState.papers_card()
	if card.is_empty():
		var none := UiKit.lbl("The papers have no question for you this year.", UiKit.BODY, UiKit.TEXT)
		none.name = "PapersNothing"
		none.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(none)
		return v
	# Every name in the story wears his club's colour (NameInk).
	var names := NameInk.from_lists(GameState.season.lists)
	var title := NameInk.label(str(card.get("title", "")), names, UiKit.HEADING, UiKit.TEXT, true)
	title.name = "PapersTitle"
	v.add_child(title)
	var text := NameInk.label(str(card.get("text", "")), names, UiKit.BODY, UiKit.TEXT)
	text.name = "PapersText"
	v.add_child(text)
	if bool(rec.get("answered", false)):
		v.add_child(UiKit.spacer(4))
		var said := NameInk.label(str(rec.get("result", "")), names, UiKit.BODY, UiKit.TEXT, true)
		said.name = "PapersResult"
		v.add_child(said)
		return v
	var silence := str((card.get("unanswered", {}) as Dictionary).get("hint", ""))
	if silence != "":
		var sl := NameInk.label(silence, names, UiKit.SECONDARY, UiKit.TEXT)
		sl.name = "PapersSilence"
		v.add_child(sl)
	var opts: Array = card.get("options", [])
	for i in range(opts.size()):
		var o: Dictionary = opts[i]
		var col := UiKit.vbox(3)
		var b := UiKit.btn(str(o.get("label", "")), UiKit.BODY, false)
		b.name = "Papers_%d" % i
		b.custom_minimum_size = Vector2(0, 48)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var index := i
		b.pressed.connect(func():
			GameState.papers_answer(index)
			GameState.autosave()
			_build())
		col.add_child(b)
		for line in StoryEngine.stakes_lines(o.get("effects", []), card.get("facts", {})):
			var mark := ""
			var kind := "Note"
			if line.begins_with(StoryEngine.GAIN_MARK):
				mark = "Gain:"
				kind = "Gain"
			elif line.begins_with(StoryEngine.COST_MARK):
				mark = "Cost:"
				kind = "Cost"
			var cl := NameInk.label(line.substr(mark.length()).strip_edges() if mark != "" else line, names, UiKit.SECONDARY, UiKit.TEXT)
			cl.name = "Papers%s_%d" % [kind, i]
			if mark == "":
				col.add_child(cl)
				continue
			var item := UiKit.hbox(6)
			var mk := UiKit.lbl(mark, UiKit.SECONDARY, UiKit.label_ink(), true)
			mk.name = "Papers%sMark_%d" % [kind, i]
			mk.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
			mk.autowrap_mode = TextServer.AUTOWRAP_OFF
			mk.custom_minimum_size = Vector2(40, 0)
			item.add_child(mk)
			cl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			item.add_child(cl)
			col.add_child(item)
		v.add_child(col)
	return v


## A PC prints the papers' ladder in this many columns, so every club and its
## whole blurb is in view at once.
const PAPERS_COLUMNS := 3
## The ladder's width on a PC, against the story's 1.
const PAPERS_LADDER_SHARE := 1.9
## A PC window shorter than this (1280x720) prints the blurbs at the fine-print
## size with tighter rows, so all 18 stay in view; a taller one has the room for
## the usual size.
const PAPERS_SHORT := 800.0


## The ladder the papers printed, best first: your club in bold, every club
## in its own colour, and under each its power-ranking blurb (its practice move
## the last sentence). A phone and a PC print the same words.
func _papers_ladder() -> Control:
	var v := UiKit.vbox(10)
	v.name = "PapersLadder"
	v.add_child(_section_head("The papers' ladder"))
	var order: Array = GameState.papers_record().get("order", [])
	var blurbs: Dictionary = GameState.papers_blurbs()
	var wide := _wide()
	var short := wide and get_viewport() != null and get_viewport().get_visible_rect().size.y < PAPERS_SHORT
	# A PC is short and wide: the ladder runs down side-by-side columns, so all
	# of it is in view without scrolling.
	var cols: Array = [v]
	if wide:
		var columns := UiKit.hbox(20)
		columns.name = "PapersLadderColumns"
		cols = []
		for c in range(PAPERS_COLUMNS):
			var col := UiKit.vbox(4 if short else 6)
			col.name = "PapersLadderColumn_%d" % c
			col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			columns.add_child(col)
			cols.append(col)
		v.add_child(columns)
	var per := int(ceil(float(order.size()) / float(cols.size())))
	for i in range(order.size()):
		var code := str(order[i])
		# The place, the club's marker and its name: one line.
		var head := UiKit.hbox(8 if wide else 10)
		var pos := UiKit.figure(str(i + 1), UiKit.HEADING if wide else UiKit.NUMBER)
		pos.custom_minimum_size = Vector2(22 if wide else 26, 0)
		pos.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		pos.size_flags_vertical = Control.SIZE_SHRINK_CENTER if wide else Control.SIZE_SHRINK_BEGIN
		head.add_child(pos)
		var mark := UiKit.club_marker(code, 18.0 if wide else 20.0)
		mark.size_flags_vertical = Control.SIZE_SHRINK_CENTER if wide else Control.SIZE_SHRINK_BEGIN
		head.add_child(mark)
		var mine := code == GameState.my_club
		var nm := UiKit.lbl(GameDB.club_name(code), UiKit.BODY, UiKit.club_name_colour(UiKit.club_ink(code)), mine)
		nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		nm.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var why := str(blurbs.get(code, GameState.papers_move_line(code)))
		var note: Label = null
		if why != "":
			note = UiKit.lbl(why, UiKit.FINE if short else UiKit.SECONDARY, UiKit.MUTED)
			note.name = "PapersBlurb_%d" % i
			note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var row: Control = head
		if wide:
			# A PC column is narrow: the blurb runs its full width under the
			# club's line, so it wraps to fewer rows.
			head.add_child(nm)
			if note != null:
				row = UiKit.vbox(0)
				row.add_child(head)
				row.add_child(note)
		else:
			head.custom_minimum_size = Vector2(0, 28)
			if note == null:
				head.add_child(nm)
			else:
				var stack := UiKit.vbox(0)
				stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				stack.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
				stack.add_child(nm)
				stack.add_child(note)
				head.add_child(stack)
		row.name = "PapersRow_%d" % i
		(cols[mini(i / per, cols.size() - 1)] as Control).add_child(row)
	return v


# ---------------------------------------------------------------------------
# The prospects on offer to a pre-season match
# ---------------------------------------------------------------------------


## This year's class in your recruiters' order, and their read of each:
## [prospects, reads by id] (GameState.prospect_reads).
func _prospects_by_rank() -> Array:
	var list: Array = GameState.preseason_prospects()
	var reads: Dictionary = GameState.prospect_reads(list)
	list = list.duplicate()
	list.sort_custom(func(a, b): return int(reads[str(a["id"])]["rank"]) < int(reads[str(b["id"])]["rank"]))
	return [list, reads]


## A prospect's button: who he is, then where your recruiters rank him and
## their read of his OVR and POT, as the draft board shows them.
func _prospect_text(p: Dictionary, reads: Dictionary) -> String:
	var r: Dictionary = reads.get(str(p["id"]), {})
	return "%s  ·  %s, age %d\nRanked %s  ·  %s OVR  ·  %s POT" % [GameDB.player_display_name(p),
			str(UiKit.ROLE_LABEL.get(str(p.get("role", "")), str(p.get("role", "")))), int(float(p.get("age", 18.0))),
			PreSeason.ordinal(int(r.get("rank", 0))), DraftScouting.range_text(r.get("overall", [0, 0])),
			DraftScouting.range_text(r.get("potential", [0, 0]))]


## A played pre-season match, in either kind: node names start with `prefix`.
func _match_report(rep: Dictionary, prefix: String, pool: Array) -> Control:
	var v := UiKit.vbox(6)
	v.name = prefix + "Report"
	var names: Array = rep.get("names", ["", ""])
	var goals: Array = rep.get("goals", [0, 0])
	var behinds: Array = rep.get("behinds", [0, 0])
	for side in range(2):
		var row := UiKit.hbox(8)
		# A practice match: each club's name in its own ink, the score right after it.
		var ink: Color = UiKit.TEXT
		if prefix == "Practice":
			ink = UiKit.club_name_colour(UiKit.club_ink(GameState.my_club if side == 0 else str(rep.get("opponent", ""))))
		var nm := UiKit.lbl(str(names[side]), UiKit.NAME, ink, true)
		nm.name = prefix + "Side_%d" % side
		nm.autowrap_mode = TextServer.AUTOWRAP_OFF
		nm.custom_minimum_size = Vector2(150, 0)
		row.add_child(nm)
		var fig := UiKit.figure(UiKit.scoreline(int(goals[side]), int(behinds[side])), UiKit.NUMBER)
		fig.name = prefix + "Score_%d" % side
		row.add_child(fig)
		v.add_child(row)
	# On a PC the sections sit in two columns, so the whole report is in view.
	var cols: BoxContainer = UiKit.hbox(28) if _wide() else UiKit.vbox(6)
	var left := UiKit.vbox(6)
	var right := UiKit.vbox(6)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(left)
	cols.add_child(right)
	v.add_child(cols)
	for part in [["Stood out", "stood", prefix + "Stood"], ["Struggled", "struggled", prefix + "Struggled"]]:
		var ids: Array = rep.get(str(part[1]), [])
		if ids.is_empty():
			continue
		left.add_child(UiKit.spacer(8))
		left.add_child(_report_head(str(part[0])))
		for i in range(ids.size()):
			left.add_child(_runner(str(ids[i]), "", "%s_%d" % [str(part[2]), i]))
	var hurt: Array = rep.get("hurt", [])
	if not hurt.is_empty():
		left.add_child(UiKit.spacer(8))
		left.add_child(_report_head("Hurt in the match"))
		for i in range(hurt.size()):
			var l := UiKit.lbl(str(hurt[i]), UiKit.BODY, UiKit.BAD)
			l.name = prefix + "Hurt_%d" % i
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			left.add_child(l)
	# The medical panel sat on one of yours after a concussion in this match.
	# A cleared player is good news: body ink, not the injury red.
	var medical: Array = rep.get("medical", [])
	var cleared: Array = rep.get("medical_cleared", [])
	if not medical.is_empty():
		left.add_child(UiKit.spacer(8))
		left.add_child(_report_head("Medical panel"))
		for i in range(medical.size()):
			var ok := i < cleared.size() and bool(cleared[i])
			var l := UiKit.lbl(str(medical[i]), UiKit.BODY, UiKit.TEXT if ok else UiKit.BAD)
			l.name = prefix + "Medical_%d" % i
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			left.add_child(l)
	var seen: Array = rep.get("prospects", [])
	if not seen.is_empty():
		var names_by_id := {}
		for p in pool:
			names_by_id[str(p["id"])] = GameDB.player_display_name(p)
		right.add_child(UiKit.spacer(8))
		right.add_child(_report_head("Prospects seen"))
		var note := UiKit.lbl("Each line is on his draft card from now on.", UiKit.SECONDARY, UiKit.TEXT)
		note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		right.add_child(note)
		for i in range(seen.size()):
			var row: Dictionary = seen[i]
			var box := UiKit.vbox(0)
			var n := UiKit.name_label(str(names_by_id.get(str(row["id"]), "A prospect")))
			n.name = prefix + "Seen_%d" % i
			box.add_child(n)
			var line := UiKit.lbl(str(row.get("line", "")), UiKit.SECONDARY, UiKit.TEXT)
			line.name = prefix + "SeenLine_%d" % i
			line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			box.add_child(line)
			box.add_child(UiKit.rule())
			right.add_child(box)
	return v


# ---------------------------------------------------------------------------
# The practice match: the club you play, your side and plan, who to trial
# ---------------------------------------------------------------------------
var _trial_count: Label
var _trial_cost: Label
var _trial_rows := {}       # prospect id -> Button


## Before it is played. Nothing is chosen for him: the side is the one he has
## named, the plan the one he has set, and the trial is his to fill or leave.
func _practice_setup() -> Control:
	var v := UiKit.vbox(UiKit.SECTION)
	v.name = "PracticeSetup"
	var opp := GameState.practice_opponent()
	var fixture := UiKit.vbox(6)
	fixture.add_child(_section_head("The match"))
	for side in [[GameState.my_club, "PracticeHome", "Home"], [opp, "PracticeAway", "Away"]]:
		var teams := UiKit.hbox(10)
		teams.add_child(UiKit.club_marker(str(side[0]), 28.0))
		var nm := UiKit.lbl(GameDB.club_name(str(side[0])), UiKit.NAME, UiKit.club_name_colour(UiKit.club_ink(str(side[0]))), true)
		nm.name = str(side[1])
		nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		nm.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		nm.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		teams.add_child(nm)
		var where := UiKit.lbl(str(side[2]), UiKit.SECONDARY, UiKit.TEXT)
		where.autowrap_mode = TextServer.AUTOWRAP_OFF
		where.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		teams.add_child(where)
		fixture.add_child(teams)
	var at_home := UiKit.lbl("Both clubs trial prospects of their own. Our listed players carry %d%% of a normal match's injury risk. A trialled prospect cannot be hurt." % roundi(float(PreSeason.tune("practice_injury_rate")) * 100.0),
			UiKit.SECONDARY, UiKit.TEXT)
	at_home.name = "PracticeRisk"
	at_home.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fixture.add_child(at_home)
	v.add_child(fixture)

	var mine := UiKit.vbox(6)
	mine.add_child(_section_head("Our side and plan"))
	var side := UiKit.lbl("Our side as named in Selection, or our best available. Injured players sit out.",
			UiKit.BODY, UiKit.TEXT)
	side.name = "PracticeSide"
	side.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	mine.add_child(side)
	var plan := UiKit.lbl("Game plan: %s" % CoachReport.plan_label(GameState.club_plan), UiKit.BODY, UiKit.TEXT, true)
	plan.name = "PracticePlan"
	mine.add_child(plan)
	var ways := UiKit.hbox(6)
	for nav in [["Selection", "selection", "PracticeSelection"], ["Game plan", "coaching", "PracticePlanGo"]]:
		var b := UiKit.btn(str(nav[0]), UiKit.BODY)
		b.name = str(nav[2])
		b.custom_minimum_size = Vector2(0, 44)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL if not _wide() else Control.SIZE_SHRINK_BEGIN
		var key := str(nav[1])
		b.pressed.connect(func(): Router.go(key))
		ways.add_child(b)
	mine.add_child(ways)
	v.add_child(mine)

	var guests := UiKit.vbox(6)
	guests.name = "PracticeInvites"
	guests.add_child(_section_head("Prospects to trial"))
	var gain := _stake(guests, "Gain:", "PracticeGain")
	gain.text = "His draft card gets a line on how he went against a senior side. Our recruiters' read of his rating gets %d%% tighter. He cannot be hurt." % roundi((1.0 - float(PreSeason.tune("seen_uncertainty"))) * 100.0)
	_trial_cost = _stake(guests, "Cost:", "PracticeCost")
	_trial_count = UiKit.lbl("", UiKit.BODY, UiKit.TEXT, true)
	_trial_count.name = "PracticeCount"
	# The spots you leave empty your recruiters fill when the match is played;
	# this fills them now, so you can see who they would take.
	var head := UiKit.hbox(8)
	_trial_count.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_trial_count.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(_trial_count)
	var fill := UiKit.btn("Recruiters fill the rest", UiKit.BODY)
	fill.name = "PracticeFill"
	fill.custom_minimum_size = Vector2(0, 44)
	fill.pressed.connect(func():
		GameState.practice_fill_invites()
		_refresh_trial())
	head.add_child(fill)
	guests.add_child(head)
	_trial_rows = {}
	var grid := GridContainer.new()
	grid.name = "PracticeProspects"
	grid.columns = 3 if _wide() else 1
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 6)
	var reads := _prospects_by_rank()
	for p in reads[0]:
		var id := str(p["id"])
		var b := UiKit.btn("", UiKit.BODY)
		b.name = "Trial_" + id
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		# The row is as wide as the column, never its words: long lines wrap.
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.custom_minimum_size = Vector2(0, 52)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.text = _prospect_text(p, reads[1])
		b.pressed.connect(func():
			GameState.toggle_practice_invite(id)
			_refresh_trial())
		_trial_rows[id] = b
		grid.add_child(b)
	guests.add_child(grid)
	v.add_child(guests)
	_refresh_trial()
	return v


func _refresh_trial() -> void:
	var invites: Array = GameState.practice_invites()
	for id in _trial_rows:
		_paint_choice(_trial_rows[id], invites.has(str(id)))
	if _trial_count != null and is_instance_valid(_trial_count):
		_trial_count.text = "%d of %d trialled" % [invites.size(), PreSeason.practice_guests()]
	if _trial_cost != null and is_instance_valid(_trial_cost):
		_trial_cost.text = _trial_cost_text(invites)


## The trial's cost, sized: how far below the players they replace the chosen
## prospects rate (every prospect on offer, before any is chosen).
func _trial_cost_text(invites: Array) -> String:
	var gap := GameState.practice_trial_gap_pct(invites)
	match invites.size():
		0:
			if gap <= 0:
				return "A prospect takes the place of our weakest player in his line. The prospects here rate no lower than the players they would replace."
			return "A prospect takes the place of our weakest player in his line. On average the prospects here rate about %d%% below the player they would replace. Our side is weaker on the day." % gap
		1:
			if gap <= 0:
				return "He takes the place of our weakest player in his line. He rates no lower than that player."
			return "He takes the place of our weakest player in his line. He rates about %d%% below that player. Our side is weaker on the day." % gap
	if gap <= 0:
		return "Each takes the place of our weakest player in his line. They rate no lower than the players they replace."
	return "Each takes the place of our weakest player in his line. On average they rate about %d%% below the players they replace. Our side is weaker on the day." % gap


## A 2 px rule in the club's colour: the section belongs to your club.
## The bonding week's card, answered here as on the hub.
func _story_cards() -> Control:
	var v := UiKit.vbox(10)
	v.name = "PreSeasonCards"
	var names := NameInk.from_lists(GameState.season.lists)
	for i in range(GameState.week_events.size()):
		v.add_child(EventCardView.build(i, not _wide(), func(): _build(),
				func(t: String): EventCardView.rule_sheet(self, t), names))
	return v


func _club_rule() -> Control:
	var r := ColorRect.new()
	r.color = UiKit.club_ink(GameState.my_club)
	r.custom_minimum_size = Vector2(0, 2)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


## A report section's head: a rule in the club's colour over its name in bold,
## so Stood out, Struggled and Prospects seen read as separate sections.
func _report_head(text: String) -> Control:
	var v := UiKit.vbox(4)
	v.add_child(_club_rule())
	v.add_child(UiKit.lbl(text, UiKit.HEADING, UiKit.club_name_colour(UiKit.club_ink(GameState.my_club)), true))
	return v


func _section_head(text: String) -> Label:
	return UiKit.lbl(text, UiKit.HEADING, UiKit.TEXT, true)


# ---------------------------------------------------------------------------
# The player meetings (director, 2026-11-17, rule 69a): each player's stat
# focus for the season, and any position he sets out to learn. A position
# change starts at the practice match. The focus picks are locked in together
# at "Meetings done"; a position change is set at its tap, as on Training.
# ---------------------------------------------------------------------------
var _meet_open := ""        # the player whose meeting is open, or ""
var _focus_draft := {}      # player id -> the stat focus picked this meeting
var _meet_sel := {}         # player id -> true: ticked for one stat focus together
var _plan_before := {}      # player id -> his own plan before a position change was set here


func _meetings_section() -> Control:
	# The whole list on one page, by line (director, 2026-11-24: "it should be
	# grouped together to fit on 1 page"; he picked "B Four lines"). A PC has the
	# four lines side by side; a phone two by two, surnames only.
	var wide := _wide()
	var lines: Container
	if wide:
		lines = UiKit.hbox(14)
	else:
		var grid := GridContainer.new()
		grid.columns = 2
		grid.add_theme_constant_override("h_separation", 10)
		grid.add_theme_constant_override("v_separation", 18)
		lines = grid
	lines.name = "PreSeasonMeetings"
	# A PC fills the page (director, 2026-11-25: "too small on pc too, too much
	# empty space"): big type for a list of up to 13 a line, a step down for longer lines.
	var longest := 0
	for g in PreSeason.GROUPS:
		var count := 0
		for p in GameState.my_list:
			if PreSeason.group_of(p) == g:
				count += 1
		longest = maxi(longest, count)
	_meet_big = wide and longest <= 13
	for g in PreSeason.GROUPS:
		var line := []
		for p in GameState.my_list:
			if PreSeason.group_of(p) == g:
				line.append(p)
		if line.is_empty():
			continue
		line.sort_custom(func(a, b): return int(Rating.ovr(a, 0)) > int(Rating.ovr(b, 0)))
		var col := UiKit.vbox(0)
		col.name = "MeetLine_" + str(g)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		col.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		var ids := []
		for q in line:
			ids.append(str(q["id"]))
		var head := UiKit.hbox(6)
		var head_lbl := _report_head(str(PreSeason.GROUP_LABEL[g]))
		head_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		head.add_child(head_lbl)
		head.add_child(_tick_button("MeetAll_" + str(g), "All", _all_ticked(ids), func():
			_tick_many(ids, not _all_ticked(ids))))
		col.add_child(head)
		col.add_child(UiKit.spacer(4))
		for p in line:
			col.add_child(_meeting_row(p, wide))
		lines.add_child(col)
	return lines


## One player. A PC: his name in the club's colour, where he plays and his
## rating, and under it what this meeting has set. A phone: his surname, and the
## focus word on the right. A tap opens his meeting over the page.
var _meet_big := false   # a PC with lines of 13 or fewer: the bigger type


func _meeting_row(p: Dictionary, wide: bool) -> Control:
	var pid := str(p["id"])
	var open := _meet_open == pid
	var box := UiKit.vbox(0)
	box.name = "Meet_" + pid
	var row := PanelContainer.new()
	row.name = "MeetRow_" + pid
	var sb := UiKit.style(UiKit.SURFACE if open else Color.TRANSPARENT, 0, UiKit.RADIUS)
	sb.set_border_width_all(0)
	sb.content_margin_left = 8.0 if wide else 0.0
	sb.content_margin_right = 8.0 if wide else 0.0
	sb.content_margin_top = 4.0 if _meet_big else 3.0
	sb.content_margin_bottom = 4.0 if _meet_big else 3.0
	row.add_theme_stylebox_override("panel", sb)
	var top := UiKit.hbox(8)
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(top)
	var ink := UiKit.club_name_colour(UiKit.club_ink(GameState.my_club))
	var n := UiKit.name_label(GameDB.player_display_name(p) if wide else GameDB.card_surname(p),
			(22 if _meet_big else 17) if wide else UiKit.SECONDARY, ink)
	n.name = "MeetName_" + pid
	n.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if not wide:
		# A phone's half-width line: one line, a long surname cut with an ellipsis.
		n.autowrap_mode = TextServer.AUTOWRAP_OFF
		n.clip_text = true
	var set_ink := UiKit.TEXT if _has_meeting_set(p) else UiKit.MUTED
	if wide:
		var left := UiKit.vbox(0)
		left.mouse_filter = Control.MOUSE_FILTER_IGNORE
		left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		left.add_child(n)
		var said := UiKit.ellipsis(_meeting_words(p), 17 if _meet_big else UiKit.SECONDARY, set_ink)
		said.name = "MeetSaid_" + pid
		said.mouse_filter = Control.MOUSE_FILTER_IGNORE
		said.clip_text = true
		left.add_child(said)
		top.add_child(left)
		var role := UiKit.line("%s %d" % [str(UiKit.ROLE_SHORT.get(str(p.get("role", "")), str(p.get("role", "")))),
				int(Rating.ovr(p, 0))], 18 if _meet_big else UiKit.SECONDARY, UiKit.TEXT, true)
		role.mouse_filter = Control.MOUSE_FILTER_IGNORE
		role.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		top.add_child(role)
	else:
		top.add_child(n)
		var word := UiKit.line(_meeting_word(p), UiKit.SMALL, set_ink)
		word.name = "MeetSaid_" + pid
		word.mouse_filter = Control.MOUSE_FILTER_IGNORE
		word.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		word.size_flags_horizontal = Control.SIZE_SHRINK_END
		word.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		top.add_child(word)
	var tap := Button.new()
	tap.name = "MeetTap_" + pid
	tap.flat = true
	tap.focus_mode = Control.FOCUS_NONE
	tap.mouse_filter = Control.MOUSE_FILTER_PASS
	tap.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var none := StyleBoxEmpty.new()
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
		tap.add_theme_stylebox_override(st, none)
	tap.pressed.connect(func():
		_meet_open = pid
		_build())
	row.add_child(tap)
	var with_tick := UiKit.hbox(2 if not wide else 4)
	with_tick.add_child(_tick_button("MeetTick_" + pid, "", _meet_sel.has(pid), func():
		_tick_many([pid], not _meet_sel.has(pid))))
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	with_tick.add_child(row)
	box.add_child(with_tick)
	box.add_child(UiKit.rule())
	return box


## A tick box (with a word beside it, or none) that a finger can hit: the
## whole button takes the tap, the box is drawn inside it.
func _tick_button(node_name: String, word: String, on: bool, on_press: Callable) -> Button:
	var b := Button.new()
	b.name = node_name
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var none := StyleBoxEmpty.new()
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
		b.add_theme_stylebox_override(st, none)
	b.set_meta("ticked", on)
	var h := UiKit.hbox(6)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var tick := TickBox.new()
	tick.on = on
	tick.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tick.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(tick)
	if word != "":
		var w := UiKit.line(word, UiKit.SMALL, UiKit.TEXT)
		w.mouse_filter = Control.MOUSE_FILTER_IGNORE
		w.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(w)
	b.add_child(h)
	b.custom_minimum_size = Vector2(28.0 + (34.0 if word != "" else 0.0), 24.0 if _wide() else 20.0)
	b.pressed.connect(on_press)
	return b


## The box itself: an outline, filled in the club's ink with a tick when on.
class TickBox extends Control:
	var on := false

	func _init() -> void:
		custom_minimum_size = Vector2(20, 20)

	func _draw() -> void:
		var r := Rect2(Vector2(1, 1), size - Vector2(2, 2))
		if on:
			draw_rect(r, UiKit.primary_fill(UiKit.club_ink(GameState.my_club)), true)
			var ink := UiKit.primary_label(UiKit.primary_fill(UiKit.club_ink(GameState.my_club)))
			draw_polyline(PackedVector2Array([Vector2(5, 10), Vector2(9, 14), Vector2(15, 6)]), ink, 2.5, true)
		else:
			draw_rect(r, UiKit.MUTED, false, 2.0)


func _all_ticked(ids: Array) -> bool:
	for id in ids:
		if not _meet_sel.has(str(id)):
			return false
	return not ids.is_empty()


func _tick_many(ids: Array, on: bool) -> void:
	for id in ids:
		if on:
			_meet_sel[str(id)] = true
		else:
			_meet_sel.erase(str(id))
	_build()


# ---------------------------------------------------------------------------
# One stat focus for every ticked player (director, 2026-11-25: "multi click
# players and set stat focus for multiple at once"; he picked tick boxes, and
# for mixed lines "All stats, skip some": a player who can't train the stat
# keeps his own, and the panel names him first).
# ---------------------------------------------------------------------------
var _group_box := {}
var _group_pick := ""


func _group_sheet_open() -> bool:
	return not _group_box.is_empty() and is_instance_valid(_group_box["overlay"]) \
			and not (_group_box["overlay"] as Control).is_queued_for_deletion()


func _close_group() -> void:
	if _group_sheet_open():
		(_group_box["overlay"] as Control).queue_free()
	_group_box = {}
	_group_pick = ""


## Whether this stat can be set for him now: his role trains it, nothing is
## locked in for the season and he is not learning a position.
func _can_take(p: Dictionary, key: String) -> bool:
	return not GameState.focus_locked(p) and GameState.project_job(p) == "" \
			and GameState.focus_options(p).has(key)


func _selected_players() -> Array:
	var out := []
	for p in GameState.my_list:
		if _meet_sel.has(str(p["id"])):
			out.append(p)
	return out


func _open_group_focus() -> void:
	_close_group()
	var picked := _selected_players()
	if picked.is_empty():
		return
	_group_box = UiKit.modal_box(self, 760.0 if _wide() else 560.0)
	var overlay: Control = _group_box["overlay"]
	overlay.name = "MeetGroupSheet"
	UiKit.close_on_outside_tap(_group_box, func():
		_group_box = {}
		_group_pick = "")
	var cancel := UiKit.btn("Cancel", UiKit.NAME)
	cancel.name = "MeetGroupCancel"
	cancel.custom_minimum_size = Vector2(0, 48)
	cancel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cancel.pressed.connect(_close_group)
	var set_it := _primary("Set")
	set_it.name = "MeetGroupSet"
	set_it.custom_minimum_size = Vector2(0, 48)
	set_it.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	set_it.pressed.connect(_on_group_set)
	var foot := UiKit.hbox(8)
	foot.add_child(cancel)
	foot.add_child(set_it)
	_group_box["footer"].add_child(foot)
	_fill_group_sheet()


func _fill_group_sheet() -> void:
	var picked := _selected_players()
	var body: VBoxContainer = _group_box["body"]
	UiKit.clear(body)
	body.add_child(UiKit.lbl("Stat focus for %d players" % picked.size(), UiKit.NAME,
			UiKit.club_name_colour(UiKit.club_ink(GameState.my_club)), true))
	var intro := UiKit.lbl("About a third of each one's training goes into it. Locked in at Meetings done.",
			UiKit.SECONDARY, UiKit.TEXT)
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(intro)
	var options := []
	for row in GameState.TRAIN_STATS:
		var key := str(row[0])
		var n := 0
		for p in picked:
			if _can_take(p, key):
				n += 1
		if n > 0:
			options.append([key, "%s  %d of %d" % [str(row[1]), n, picked.size()]])
	body.add_child(UiKit.choice_grid("MeetGroupFocus", options, _group_pick, 2, func(key: String):
		_group_pick = key
		_fill_group_sheet()))
	var set_it := _group_box["footer"].find_child("MeetGroupSet", true, false) as Button
	if _group_pick == "":
		set_it.text = "Set"
		set_it.disabled = true
		return
	var takers := 0
	var skipped := []
	for p in picked:
		if _can_take(p, _group_pick):
			takers += 1
		else:
			skipped.append(GameDB.card_surname(p))
	set_it.disabled = takers == 0
	set_it.text = "Set for %d" % takers
	if not skipped.is_empty():
		var who := ", ".join(skipped.slice(0, skipped.size() - 1)) + " and " + str(skipped[-1]) \
				if skipped.size() > 1 else str(skipped[0])
		var skip := UiKit.lbl("%s can't train %s and %s their own focus." % [who,
				GameState.train_stat_label(_group_pick).to_lower(), "keep" if skipped.size() > 1 else "keeps"],
				UiKit.SECONDARY, UiKit.TEXT)
		skip.name = "MeetGroupSkip"
		skip.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		body.add_child(skip)


func _on_group_set() -> void:
	if _group_pick == "":
		return
	for p in _selected_players():
		if _can_take(p, _group_pick):
			_focus_draft[str(p["id"])] = _group_pick
	_close_group()
	_meet_sel = {}
	_build()


## Whether this meeting has set him anything: a stat focus or a position.
func _has_meeting_set(p: Dictionary) -> bool:
	var pid := str(p["id"])
	return str(_focus_draft.get(pid, GameState.stat_focus(p))) != "" or GameState.project_job(p) != ""


## The phone's one word on the right: "kicking", "learning key forward", or "no focus".
func _meeting_word(p: Dictionary) -> String:
	var job := GameState.project_job(p)
	if job != "":
		return "learning %s" % str(GameState.LEARN_JOBS[job]["word"])
	var focus := str(_focus_draft.get(str(p["id"]), GameState.stat_focus(p)))
	return "no focus" if focus == "" else GameState.train_stat_label(focus).to_lower()


# ---------------------------------------------------------------------------
# The open meeting sits in a panel over the page; closing it (Close, a tap
# outside, Android Back) leaves the four lines as they were.
# ---------------------------------------------------------------------------
var _meet_box := {}


func _meet_sheet_open() -> bool:
	return not _meet_box.is_empty() and is_instance_valid(_meet_box["overlay"]) \
			and not (_meet_box["overlay"] as Control).is_queued_for_deletion()


func _close_meeting() -> void:
	if _meet_sheet_open():
		(_meet_box["overlay"] as Control).queue_free()
	_meet_box = {}
	if _meet_open != "":
		_meet_open = ""
		_build()


## Opens, refreshes or closes the meeting panel to match _meet_open. Runs at the
## end of every _build, so a pick inside it redraws its choices in place.
func _sync_meeting_sheet() -> void:
	var p: Dictionary = GameState.list_player(_meet_open) if _meet_open != "" else {}
	if p.is_empty() or GameState.preseason_stop() != "meetings":
		if _meet_sheet_open():
			(_meet_box["overlay"] as Control).queue_free()
		_meet_box = {}
		return
	if not _meet_sheet_open():
		_meet_box = UiKit.modal_box(self, 1180.0 if _wide() else 560.0)
		var overlay: Control = _meet_box["overlay"]
		overlay.name = "MeetSheet"
		UiKit.close_on_outside_tap(_meet_box, func():
			_meet_box = {}
			_meet_open = ""
			_build())
		var close := UiKit.btn("Close", UiKit.NAME, true)
		close.name = "MeetClose"
		close.custom_minimum_size = Vector2(0, 48)
		close.pressed.connect(_close_meeting)
		_meet_box["footer"].add_child(close)
	var body: VBoxContainer = _meet_box["body"]
	UiKit.clear(body)
	if not _wide():
		# A phone has no profile beside the choices: who this is, at the top.
		var who := UiKit.vbox(0)
		who.add_child(UiKit.name_label(GameDB.player_display_name(p), UiKit.NAME,
				UiKit.club_name_colour(UiKit.club_ink(GameState.my_club))))
		var who_row := UiKit.hbox(8)
		var role := UiKit.lbl("%s %d" % [str(UiKit.ROLE_SHORT.get(str(p.get("role", "")), str(p.get("role", "")))),
				int(Rating.ovr(p, 0))], UiKit.SECONDARY, UiKit.TEXT, true)
		role.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		role.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		who_row.add_child(role)
		var prof := UiKit.btn("Profile", UiKit.SECONDARY)
		prof.name = "MeetProfileOpen"
		prof.custom_minimum_size = Vector2(0, 44)
		prof.pressed.connect(func(): PlayerSheet.open(self, p))
		who_row.add_child(prof)
		who.add_child(who_row)
		body.add_child(who)
	body.add_child(_meeting(p))


## "Focus: kicking  ·  Learning key forward", or "No stat focus".
func _meeting_words(p: Dictionary) -> String:
	var pid := str(p["id"])
	var focus := str(_focus_draft.get(pid, GameState.stat_focus(p)))
	var parts := []
	if focus == "":
		parts.append("No stat focus")
	else:
		parts.append("Focus: %s %s" % [GameState.train_stat_label(focus).to_lower(), PlayerProfile.attr_text(p, focus)])
	var job := GameState.project_job(p)
	if job != "":
		parts.append("Learning %s" % str(GameState.LEARN_JOBS[job]["word"]))
	return "  ·  ".join(parts)


## What a man of each line is called in a sentence ("his rating as a midfielder").
const LINE_NOUN := {"RUCK": "ruck", "MID": "midfielder", "DEF": "defender", "FWD": "forward"}
const COUNT_WORD := ["none", "one", "two", "three", "four", "five", "six"]


## His meeting: the stat focus for the season, then a position to learn. On a
## PC the choices take the left half and his profile the right (director,
## 2026-11-24: "shrink them to fit half the space on the left, and put the
## player's profile on the right ... on pc anyway"); a phone keeps one column.
func _meeting(p: Dictionary) -> Control:
	var pid := str(p["id"])
	var v := _meeting_choices(p)
	if not _wide():
		v.name = "Meeting_" + pid
		return v
	var cols := UiKit.hbox(28)
	cols.name = "Meeting_" + pid
	v.name = "MeetChoices"
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	cols.add_child(v)
	var card := UiKit.panel(UiKit.PANEL)
	card.name = "MeetProfile"
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	var body := UiKit.vbox(6)
	card.add_child(body)
	PlayerSheet.profile_body(body, p, self)
	cols.add_child(card)
	return cols


func _meeting_choices(p: Dictionary) -> VBoxContainer:
	var pid := str(p["id"])
	var v := UiKit.vbox(8)
	var year := GameState.season_year
	v.add_child(UiKit.lbl("Stat focus for %d" % year, UiKit.SECONDARY, UiKit.label_ink(), true))
	var learning := GameState.project_job(p)
	if learning != "":
		var hold := UiKit.lbl("On hold while he learns a position. All his training goes into the new role.", UiKit.SECONDARY, UiKit.TEXT)
		hold.name = "MeetFocusHold"
		hold.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(hold)
	elif GameState.focus_locked(p):
		var locked := UiKit.lbl("%s, locked in for %d." % [GameState.train_stat_label(GameState.stat_focus(p)), year],
				UiKit.SECONDARY, UiKit.TEXT)
		locked.name = "MeetFocusLocked"
		v.add_child(locked)
	else:
		var intro := UiKit.lbl("About a third of his training goes into it. Locked in at Meetings done.", UiKit.SECONDARY, UiKit.TEXT)
		intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(intro)
		var options := []
		var keys: Array = GameState.focus_options(p)
		for key in keys:
			options.append([key, "%s %s" % [GameState.train_stat_label(key), PlayerProfile.attr_text(p, key)]])
		# The stats his position is rated on, in bold (director, 2026-11-24:
		# "stats that their position is rated on should be highlighted").
		var rated := []
		for key in PlayerProfile.rated_on(p):
			if keys.has(key):
				rated.append(key)
		if not rated.is_empty():
			var key_line := UiKit.lbl("His rating as a %s rests most on the %s in bold." % [
					str(LINE_NOUN.get(str(p.get("role", "MID")), "player")),
					COUNT_WORD[mini(rated.size(), COUNT_WORD.size() - 1)]], UiKit.SECONDARY, UiKit.TEXT)
			key_line.name = "MeetFocusRated"
			key_line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			v.add_child(key_line)
		v.add_child(UiKit.choice_grid("MeetFocus", options, str(_focus_draft.get(pid, GameState.stat_focus(p))), 2,
				func(key: String):
					_focus_draft[pid] = key
					_build(), rated))
	var learn := _meeting_learn(p)
	if learn != null:
		v.add_child(learn)
	return v


## The positions he could learn (GameState.open_jobs), or who holds the club's
## two projects when they are taken. Null when he cannot learn one.
func _meeting_learn(p: Dictionary) -> Control:
	var pid := str(p["id"])
	var learning := GameState.project_job(p)
	var open: Array = GameState.open_jobs(p)
	if learning == "" and open.is_empty():
		return null
	var v := UiKit.vbox(6)
	v.name = "MeetLearn"
	v.add_child(UiKit.lbl("Learn a new position", UiKit.SECONDARY, UiKit.label_ink(), true))
	var options := [["", "No change"]]
	for key in GameState.plans_for(p):
		if str(key).begins_with(GameState.LEARN_PREFIX):
			options.append([key, "Learn " + str(GameState.LEARN_JOBS[str(key).trim_prefix(GameState.LEARN_PREFIX)]["word"])])
	if options.size() == 1:
		var names := []
		for q in GameState.my_list:
			if GameState.project_job(q) != "":
				names.append(GameDB.player_display_name(q))
		var full := UiKit.lbl("Two of our players are learning a position already: %s." % " and ".join(names),
				UiKit.SECONDARY, UiKit.TEXT)
		full.name = "MeetLearnFull"
		full.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(full)
		return v
	var current := GameState.plan_for(p)
	if not current.begins_with(GameState.LEARN_PREFIX):
		current = ""
	v.add_child(UiKit.choice_grid("MeetLearnPick", options, current, 2, func(key: String):
		var q := GameState.list_player(pid)
		var now := GameState.plan_for(q)
		if key == "":
			if now.begins_with(GameState.LEARN_PREFIX):
				GameState.set_player_plan(pid, str(_plan_before.get(pid, "")))
		elif key != now:
			if not now.begins_with(GameState.LEARN_PREFIX):
				_plan_before[pid] = str(q.get("train_plan", ""))
			GameState.set_player_plan(pid, key)
		_build()))
	if current != "":
		var what := UiKit.lbl(GameState.train_plan_description(current) + " It starts at the practice match.",
				UiKit.SECONDARY, UiKit.TEXT)
		what.name = "MeetLearnWhat"
		what.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(what)
	return v


func _on_meetings_done() -> void:
	for pid in _focus_draft:
		GameState.set_stat_focus(str(pid), str(_focus_draft[pid]))
	_focus_draft = {}
	_plan_before = {}
	_meet_open = ""
	GameState.preseason_meetings_done()
	GameState.autosave()
	_build()


# ---------------------------------------------------------------------------
# The season fitness plan (rule 69a): it runs through the pre-season and the
# season beyond, and books its own weeks of running (Peak 5, Fast 4, Steady 3,
# Develop 2). The weeks it leaves free are for drilling or bonding.
# ---------------------------------------------------------------------------
var _plan_draft := ""


func _plan_section() -> Control:
	var v := UiKit.vbox(8)
	v.name = "PreSeasonPlans"
	var level: int = GameState.fitness_hp_level(GameState.my_club)
	var draft := _plan_draft if _plan_draft != "" else GameState.fitness_plan(GameState.my_club)
	for key in Conditioning.PLANS:
		v.add_child(_plan_option(str(key), draft == str(key), level))
	if int(GameState.preseason.get("extra_run", 0)) > 0:
		var flag := UiKit.lbl("The flag celebrations cost us a week. Every plan has one more running week.",
				UiKit.SECONDARY, UiKit.TEXT)
		flag.name = "PreSeasonFlagRun"
		flag.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(flag)
	return v


## One plan: its name, its running weeks as a row of weeks, what it does over
## the season, and one tap to pick it. The picked one is outlined.
func _plan_option(key: String, on: bool, level: int) -> Control:
	var row := PanelContainer.new()
	row.name = "PlanRow_" + key
	var sb := UiKit.style(UiKit.SURFACE, 12, UiKit.RADIUS, UiKit.TEXT if on else Color.TRANSPARENT)
	sb.set_border_width_all(2 if on else 0)
	row.add_theme_stylebox_override("panel", sb)
	var v := UiKit.vbox(4)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(v)
	var t := UiKit.lbl(str(Conditioning.PLAN_LABEL[key]), UiKit.NAME, UiKit.TEXT, true)
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(t)
	var runs: int = GameState.preseason_plan_runs(key)
	var free := PreSeason.train_weeks() - runs
	var weeks := UiKit.lbl("%d weeks of running. %d %s free for drilling or bonding." % [
			runs, free, "week" if free == 1 else "weeks"], UiKit.SECONDARY, UiKit.TEXT, true)
	weeks.name = "PlanRuns_" + key
	weeks.mouse_filter = Control.MOUSE_FILTER_IGNORE
	weeks.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(weeks)
	var plan_weeks := []
	for i in range(PreSeason.train_weeks()):
		plan_weeks.append("run" if i < runs else "")
	v.add_child(_week_cells(plan_weeks, -1, false))
	var e := UiKit.lbl(Conditioning.plan_effect(key, level), UiKit.SECONDARY, UiKit.TEXT)
	e.name = "PlanEffect_" + key
	e.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	e.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(e)
	var tap := Button.new()
	tap.name = "Plan_" + key
	tap.flat = true
	tap.focus_mode = Control.FOCUS_NONE
	tap.mouse_filter = Control.MOUSE_FILTER_PASS
	tap.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var none := StyleBoxEmpty.new()
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
		tap.add_theme_stylebox_override(st, none)
	tap.custom_minimum_size = Vector2(0, 44)
	tap.pressed.connect(func():
		_plan_draft = key
		_build())
	row.add_child(tap)
	return row


func _on_plan_set() -> void:
	var plan := _plan_draft if _plan_draft != "" else GameState.fitness_plan(GameState.my_club)
	if GameState.set_preseason_plan(plan):
		_plan_draft = ""
		GameState.autosave()
	_build()


# ---------------------------------------------------------------------------
# The week (rule 69a): one action. Running while the booked running is owed
# (the only one once the weeks left are only enough for it; never again once
# it is done), Game plan drilling, or Team bonding (one card from the deck).
# ---------------------------------------------------------------------------
const ACTION_SHORT := {"run": "Run", "drill": "Drill", "bond": "Bond"}
var _drill_group_sel := ""   # the position group the drill picker shows, or "" for the whole side


## The summer as a row of weeks: what each week did, the week being set, and
## the weeks still to come, in order. Week 8 is the papers' quiet week.
func _summer_strip() -> Control:
	var acts: Array = GameState.preseason_entry().get("acts", [])
	var cells := []
	for i in range(PreSeason.train_weeks()):
		if i < acts.size() and acts[i] is Dictionary:
			cells.append(str(acts[i].get("a", "")))
		else:
			cells.append("")
	var now := GameState.preseason_week()
	var next: Dictionary = GameState.preseason_next()
	if GameState.preseason_stop() == "week" and now < cells.size():
		cells[now] = str(next.get("a", ""))
	var v := UiKit.vbox(4)
	v.name = "PreSeasonSummer"
	var entry := GameState.preseason_entry()
	var need := int(entry.get("need", 0))
	var done := int(entry.get("run", 0))
	var head := UiKit.lbl("Running: %d of %d weeks done" % [mini(done, need), need], UiKit.BODY, UiKit.TEXT, true)
	head.name = "PreSeasonRunDone"
	v.add_child(head)
	v.add_child(_week_cells(cells, now if GameState.preseason_stop() == "week" else -1, true))
	return v


## A row of weeks, one cell each: the week's number over its action's short
## word ("Run", "Drill", "Bond"). Running is filled in the club's colour; the
## week being set is outlined. With `papers`, an eighth cell for the quiet week.
func _week_cells(cells: Array, current: int, papers: bool) -> Control:
	var h := UiKit.hbox(4)
	h.name = "WeekCells"
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var ink := UiKit.club_ink(GameState.my_club)
	var fill := UiKit.primary_fill(ink)
	var on_fill := UiKit.primary_label(fill)
	var all := cells.duplicate()
	if papers:
		all.append("papers")
	for i in range(all.size()):
		var a := str(all[i])
		var cell := PanelContainer.new()
		cell.name = "Week_%d" % (i + 1)
		cell.mouse_filter = Control.MOUSE_FILTER_IGNORE
		cell.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var run := a == "run"
		var sb := UiKit.style(fill if run else UiKit.SURFACE, 4, 4, UiKit.TEXT if i == current else Color.TRANSPARENT)
		sb.set_border_width_all(2 if i == current else 0)
		cell.add_theme_stylebox_override("panel", sb)
		var word := ""
		if a == "papers":
			word = "Papers"
		elif ACTION_SHORT.has(a):
			word = str(ACTION_SHORT[a])
		var l := UiKit.lbl("%d\n%s" % [i + 1, word], UiKit.SMALL, on_fill if run else UiKit.TEXT, run or i == current)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		cell.add_child(l)
		h.add_child(cell)
	return h


func _week_section() -> Control:
	var v := UiKit.vbox(10)
	v.name = "PreSeasonWeek"
	v.add_child(_summer_strip())
	var open: Array = GameState.preseason_actions()
	var chosen := str(GameState.preseason_next().get("a", ""))
	for a in PreSeason.ACTIONS:
		v.add_child(_action_option(str(a), chosen == str(a), open.has(a)))
	if chosen == "drill":
		v.add_child(_drill_picker())
	return v


## One action for the week: its name, then what it gains and what it costs,
## or, closed, why. A tap picks it; the picked one is outlined.
func _action_option(a: String, on: bool, open: bool) -> Control:
	var row := PanelContainer.new()
	row.name = "Action_" + a
	var sb := UiKit.style(UiKit.SURFACE, 12, UiKit.RADIUS, UiKit.TEXT if on else Color.TRANSPARENT)
	sb.set_border_width_all(2 if on else 0)
	row.add_theme_stylebox_override("panel", sb)
	var v := UiKit.vbox(4)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(v)
	var t := UiKit.lbl(str(PreSeason.ACTION_LABEL[a]), UiKit.NAME, UiKit.TEXT if open else UiKit.MUTED, true)
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(t)
	if not open:
		var why := UiKit.lbl(_closed_words(a), UiKit.SECONDARY, UiKit.MUTED)
		why.name = "ActionClosed_" + a
		why.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		why.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(why)
		return row
	var words := _action_words(a)
	var gain := _stake(v, "Gain:", "ActionGain_" + a)
	gain.text = str(words[0])
	var cost := _stake(v, "Cost:", "ActionCost_" + a)
	cost.text = str(words[1])
	for c in v.get_children():
		(c as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	var tap := Button.new()
	tap.name = "ActionTap_" + a
	tap.flat = true
	tap.focus_mode = Control.FOCUS_NONE
	tap.mouse_filter = Control.MOUSE_FILTER_PASS
	tap.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var none := StyleBoxEmpty.new()
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
		tap.add_theme_stylebox_override(st, none)
	tap.custom_minimum_size = Vector2(0, 44)
	tap.pressed.connect(func():
		if GameState.set_preseason_action(a):
			_build())
	row.add_child(tap)
	return row


## [gain, cost] for an open action, in the club's words.
func _action_words(a: String) -> Array:
	var entry := GameState.preseason_entry()
	var need := int(entry.get("need", 0))
	var done := int(entry.get("run", 0))
	match a:
		"run":
			return ["Running week %d of the %d in our plan." % [done + 1, need],
					"No drilling or bonding this week."]
		"drill":
			var plans: Array = GameState.preseason_drills()
			var plan := str(plans[0]) if not plans.is_empty() else GameState.card_drill_plan()
			var now := PreSeason.fluency_short(GameState.plan_fluency(GameState.my_club, plan))
			return ["A week on %s, known %s now. Two weeks lifts a plan a step." % [
					CoachReport.plan_label(plan).to_lower(), now],
					"No running or bonding this week." if GameState.preseason_run_left() > 0 else "No bonding this week."]
		"bond":
			return ["One card from the bonding deck. Each card has a small sure gain, or a bigger gain with a cost.",
					"No running or drilling this week." if GameState.preseason_run_left() > 0 else "No drilling this week."]
	return ["", ""]


## Why an action is closed this week.
func _closed_words(a: String) -> String:
	var left := GameState.preseason_run_left()
	var weeks_left := PreSeason.train_weeks() - GameState.preseason_week()
	if a == "run":
		return "Our booked running is done. No extra running."
	return "Closed. We still owe %d %s of running, and %d %s left." % [
			left, "week" if left == 1 else "weeks", weeks_left, "week is" if weeks_left == 1 else "weeks are"]


## The plan a drilling week drills: the whole side, or a position group of its
## own (director, 2026-11-06, row 101: "split it between position groups").
## Tabs pick whose drills are shown; a plan tap sets them.
func _drill_picker() -> Control:
	var h := UiKit.vbox(6)
	h.name = "DrillPicker"
	h.add_child(UiKit.lbl("Drill", UiKit.BODY, UiKit.TEXT, true))
	var key_line := UiKit.lbl("Under each plan: how well we know it now, and by Round 1 with this drilling.", UiKit.SECONDARY, UiKit.TEXT)
	key_line.name = "DrillKey"
	key_line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	h.add_child(key_line)
	var tabs := UiKit.hbox(0)
	tabs.name = "DrillFor"
	tabs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var keys: Array = [""]
	keys.append_array(PreSeason.GROUPS)
	for g in keys:
		var key := str(g)
		var t := UiKit.tab("All" if key == "" else str(PreSeason.GROUP_LABEL[key]), false)
		t.name = "DrillFor_%s" % ("ALL" if key == "" else key)
		t.custom_minimum_size = Vector2(36, 44)
		UiKit.set_font_size(t, UiKit.SECONDARY)
		t.add_theme_font_override("font", UiKit.BOLD)
		t.size_flags_stretch_ratio = UiKit.BOLD.get_string_size(t.text, HORIZONTAL_ALIGNMENT_LEFT, -1,
				UiKit.px(UiKit.SECONDARY)).x + 4.0
		_paint_group_tab(t, key == _drill_group_sel)
		t.pressed.connect(func():
			_drill_group_sel = key
			_build())
		tabs.add_child(t)
	h.add_child(tabs)
	var split_line := UiKit.lbl(_split_words(), UiKit.SECONDARY, UiKit.TEXT)
	split_line.name = "DrillSplit"
	split_line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	h.add_child(split_line)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 6)
	h.add_child(grid)
	var whole_split: bool = _drill_group_sel == "" and GameState.preseason_drills_split()
	var drills: Array = GameState.preseason_drills(_drill_group_sel)
	for plan in PreSeason.DRILL_PLANS:
		var key := str(plan)
		var b := UiKit.btn("%s\n%s" % [CoachReport.plan_label(key), _knows_words(key)], UiKit.SECONDARY)
		b.name = "Drill_%s" % key
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.clip_text = true
		b.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		b.custom_minimum_size = Vector2(0, 72)
		_paint_choice(b, drills.has(key) and not whole_split)
		b.pressed.connect(func():
			GameState.set_preseason_drills([key], _drill_group_sel)
			_build())
		grid.add_child(b)
	return h


## How well the side knows a plan, and on a line of its own where the drilling
## set leaves it: "medium", or "medium" then "Rd 1: 50% to high".
func _knows_words(plan: String) -> String:
	var now: float = GameState.plan_fluency(GameState.my_club, plan)
	var after: float = GameState.plan_fluency_after_drills(plan)
	var t := PreSeason.fluency_short(now)
	if after != now:
		t += "\nRd 1: %s" % PreSeason.fluency_short(after)
	return t


## The line under the group tabs: who the drills shown are for, and how the
## groups split when they do.
func _split_words() -> String:
	var group := _drill_group_sel
	if group != "":
		var n := 0
		for p in GameState.my_list:
			if PreSeason.group_of(p) == group:
				n += 1
		var share := 0 if GameState.my_list.is_empty() else roundi(100.0 * n / GameState.my_list.size())
		return "The %s: %d of our list, %d%% of our drilling." % [
				str(PreSeason.GROUP_LABEL[group]).to_lower(), n, share]
	if not GameState.preseason_drills_split():
		return "Every group drills the same. Pick a group to give it its own."
	var by := {}
	var order := []
	for g in PreSeason.GROUPS:
		var names := []
		for d in GameState.preseason_drills(str(g)):
			names.append(CoachReport.plan_label(str(d)))
		var k := " and ".join(names)
		if not by.has(k):
			by[k] = []
			order.append(k)
		by[k].append(str(PreSeason.GROUP_LABEL[g]))
	var parts := []
	for k in order:
		parts.append("%s: %s" % [_and_list(by[k]), k])
	return "Split. %s. A pick here sets every group." % ". ".join(parts)


## The kit's tab look, narrower at the sides so the five fit a phone's width;
## the chosen one bright and underlined (every tab is in the sign face).
static func _paint_group_tab(b: Button, active: bool) -> void:
	UiKit.paint_tab(b, active)
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		var sb := b.get_theme_stylebox(st) as StyleBoxFlat
		if sb != null:
			sb.content_margin_left = 2
			sb.content_margin_right = 2
	b.set_meta("chosen", active)


static func _and_list(names: Array) -> String:
	if names.size() <= 1:
		return "".join(names)
	return "%s and %s" % [", ".join(names.slice(0, names.size() - 1)), names[names.size() - 1]]


func _paint_choice(b: Button, on: bool) -> void:
	# The kit's choice look (STYLE-01): the rest outlined, the chosen one 2 px TEXT.
	var sb := UiKit._choice_box(on)
	for s in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		b.add_theme_stylebox_override(s, sb)
	b.add_theme_font_override("font", UiKit.BOLD if on else UiKit.FONT)
	for k in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(k, UiKit.TEXT)
	b.set_meta("chosen", on)


## A "Gain:" or "Cost:" line: the marker bold, the sentence regular, both at
## full strength (the card-stakes pattern).
func _stake(into: VBoxContainer, mark: String, node_name: String) -> Label:
	var item := UiKit.hbox(6)
	var mk := UiKit.lbl(mark, UiKit.SECONDARY, UiKit.label_ink(), true)
	mk.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	mk.autowrap_mode = TextServer.AUTOWRAP_OFF
	mk.custom_minimum_size = Vector2(40, 0)
	item.add_child(mk)
	var l := UiKit.lbl("", UiKit.SECONDARY, UiKit.TEXT)
	l.name = node_name
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	item.add_child(l)
	into.add_child(item)
	l.set_meta("row", item)
	return l


## The time trial: the order they came home, the first five and the last
## three, by name.
func _trial_section() -> Control:
	var v := UiKit.vbox(4)
	v.name = "TimeTrial"
	var trial: Dictionary = GameState.preseason_trial()
	v.add_child(_section_head("First five home"))
	var best: Array = trial.get("best", [])
	for i in range(best.size()):
		v.add_child(_runner(str(best[i]), "%d" % (i + 1), "TrialBest_%d" % i))
	var worst: Array = trial.get("worst", [])
	if not worst.is_empty():   # a list too short for a tail: no heading over no names
		v.add_child(UiKit.spacer(6))
		v.add_child(_section_head("Last three home" if worst.size() == 3 else "Last home"))
		for i in range(worst.size()):
			v.add_child(_runner(str(worst[i]), "", "TrialWorst_%d" % i))
	return v


## One runner on one line: his place (the first five), his name in bold, where
## he plays at the right.
func _runner(id: String, place: String, node_name: String) -> Control:
	var p: Dictionary = GameState.list_player(id)
	var box := UiKit.vbox(2)
	var h := UiKit.hbox(10)
	h.custom_minimum_size = Vector2(0, 22 if _wide() else 30)
	if place != "":
		var fig := UiKit.figure(place, UiKit.NUMBER)
		fig.custom_minimum_size = Vector2(26, 0)
		fig.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		fig.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(fig)
	# His name wears his club's colour, and where he plays sits beside it.
	var n := UiKit.lbl(GameDB.player_display_name(p) if not p.is_empty() else "A player who has left",
			UiKit.NAME, UiKit.club_name_colour(UiKit.club_ink(GameState.my_club)), true)
	n.name = node_name
	n.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	n.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	n.autowrap_mode = TextServer.AUTOWRAP_OFF
	h.add_child(NameLink.tappable(n, id) if not p.is_empty() else n)
	if not p.is_empty():
		var role := UiKit.lbl(str(UiKit.ROLE_LABEL.get(str(p.get("role", "")), str(p.get("role", "")))),
				UiKit.SECONDARY, UiKit.TEXT)
		role.autowrap_mode = TextServer.AUTOWRAP_OFF
		role.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(role)
	var rest := Control.new()
	rest.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rest.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(rest)
	box.add_child(h)
	box.add_child(UiKit.rule())
	return box


## The primary action, filled with the club's readable ink (UiKit.club_ink)
## and dark or light type by its brightness: the kit's own club fill sinks
## into the dark page for some clubs (Fremantle) and into the club's stripes
## for others (the Bulldogs' red).
func _primary(text: String) -> Button:
	var b := UiKit.btn(text, UiKit.NAME, true)
	var fill := UiKit.primary_fill(UiKit.club_ink(GameState.my_club))
	var ink := UiKit.primary_label(fill)
	var shades := {"normal": fill, "hover": fill.lightened(0.08),
			"pressed": fill.darkened(0.12), "hover_pressed": fill.darkened(0.12)}
	for state in shades:
		var sb := UiKit.style(shades[state], 8, UiKit.RADIUS)
		sb.set_border_width_all(0)
		b.add_theme_stylebox_override(str(state), sb)
	for k in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(k, ink)
	return b


## The way on, pinned under the page: one primary action with the quiet
## ones beside it.
func _actions(stop: String) -> Control:
	var v := UiKit.vbox(6)
	v.name = "PreSeasonActions"
	var setup := stop == "practice" and not GameState.practice_played()
	var label := "Back to training"
	var on_press: Callable = _on_go
	match stop:
		"meetings":
			label = "Meetings done"
			on_press = _on_meetings_done
		"plan":
			label = "Start training"
			on_press = _on_plan_set
		"week":
			label = "Train week %d" % (GameState.preseason_week() + 1)
		"papers":
			label = "On to Round 1"
		"practice":
			if setup:
				label = "Coach the match"
				on_press = _on_coach_practice
	var picking := stop == "meetings" and not _meet_sel.is_empty()
	if picking:
		label = "Set stat focus for %d" % _meet_sel.size()
		on_press = _open_group_focus
	var go := _primary(label)
	go.name = "PreSeasonGo"
	go.custom_minimum_size = Vector2(0, 48)
	go.pressed.connect(on_press)
	# A week trains only once its action is picked.
	go.disabled = stop == "week" and GameState.preseason_next().is_empty()
	var quiet := UiKit.hbox(6)
	quiet.name = "PreSeasonNav"
	if setup:
		var sim_it := UiKit.btn("Sim the match", UiKit.BODY)
		sim_it.name = "PracticeSim"
		sim_it.custom_minimum_size = Vector2(0, 44)
		sim_it.pressed.connect(_on_sim_practice)
		quiet.add_child(sim_it)
	if picking:
		var clear := UiKit.btn("Clear", UiKit.BODY)
		clear.name = "MeetClearTicks"
		clear.custom_minimum_size = Vector2(0, 44)
		clear.pressed.connect(func():
			_meet_sel = {}
			_build())
		quiet.add_child(clear)
	elif stop in ["meetings", "plan", "week"]:
		var sim := UiKit.btn("Sim to Round 1", UiKit.BODY)
		sim.name = "PreSeasonSim"
		sim.custom_minimum_size = Vector2(0, 44)
		sim.pressed.connect(_on_sim_pressed)
		quiet.add_child(sim)
	var navs := [] if picking else [["My list", "list", "PreSeasonList"]]
	# The meetings set each player's focus, so they need no Training button
	# (director, 2026-11-25: "this screen replaces the need for that button here").
	if stop != "meetings":
		navs.append(["Training", "training", "PreSeasonTraining"])
	for nav in navs:
		var b := UiKit.btn(str(nav[0]), UiKit.BODY)
		b.name = str(nav[2])
		b.custom_minimum_size = Vector2(0, 44)
		var key := str(nav[1])
		b.pressed.connect(func(): Router.go(key))
		quiet.add_child(b)
	if _wide():
		# A PC: every button together at the right with the way on last (no
		# full-width bar).
		var row := UiKit.hbox(8)
		var gap := Control.new()
		gap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(gap)
		quiet.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(quiet)
		go.custom_minimum_size = Vector2(240, 48)
		go.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(go)
		v.add_child(row)
	else:
		for c in quiet.get_children():
			(c as Control).size_flags_horizontal = Control.SIZE_EXPAND_FILL
		v.add_child(go)
		# The quiet ones as words on the club's ink bar, like the hub's foot (STYLE-01).
		v.add_child(UiKit.nav_bar(quiet))
	return v


func _on_go() -> void:
	_after(GameState.preseason_advance())


func _on_coach_practice() -> void:
	if GameState.prepare_practice_match():
		Router.go("match")


func _on_sim_practice() -> void:
	GameState.sim_practice_match()
	GameState.autosave()
	_build()


## Sim to Round 1 plays the weeks, the time trial, the practice match and the
## papers without you, so it says so first, the way the hub's Sim the week does
## (and, like it, not once Settings says don't ask).
func _on_sim_pressed() -> void:
	if not GameState.confirm_sim_round():
		_on_sim()
		return
	var open := get_node_or_null("PreSeasonSimConfirm")
	if open != null and not open.is_queued_for_deletion():
		return
	var box := UiKit.modal_box(self, 420.0, 340.0)
	var sheet: Control = box["overlay"]
	sheet.name = "PreSeasonSimConfirm"
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.heading("Sim to Round 1?", UiKit.H1))
	var why := UiKit.lbl("The weeks, the time trial, the practice match and the papers play out without you. Our booked running comes first, then drilling our game plan, then bonding. The practice match result goes in the news.", UiKit.BODY, UiKit.TEXT)
	why.name = "PreSeasonSimWhy"
	why.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(why)
	var go := UiKit.btn("Sim to Round 1", UiKit.NAME, true)
	go.name = "PreSeasonSimGo"
	go.custom_minimum_size = Vector2(0, 48)
	go.pressed.connect(func():
		sheet.queue_free()
		_on_sim())
	box["footer"].add_child(go)
	var cancel := UiKit.btn("Cancel", UiKit.NAME)
	cancel.name = "PreSeasonSimCancel"
	cancel.custom_minimum_size = Vector2(0, 44)
	cancel.pressed.connect(sheet.queue_free)
	box["footer"].add_child(cancel)


## Under the loading cover, like Sim the week: the set shot plays while the
## pre-season is simmed, then the hub. A browser draws nothing until the game
## hands control back, so there the weeks hand it back as they go (the
## practice matches on threads); elsewhere the matches' wait keeps the ball
## moving.
func _on_sim() -> void:
	ScreenTransition.run("Playing out the pre-season...", func():
		if OS.has_feature("web"):
			await GameState.preseason_sim_to_round1_async()
		else:
			GameState.preseason_sim_to_round1()
		_after("done"))


func _after(at: String) -> void:
	if at == "done" or not GameState.preseason_active():
		Router.replace("hub")
	else:
		_build()


## Android Back: an open sheet closes first; otherwise the router takes the
## coach to the main menu, as from the hub (the career is saved).
func handle_back() -> bool:
	if _group_sheet_open():
		_close_group()
		return true
	if _meet_sheet_open():
		_close_meeting()
		return true
	if FirstVisitIntro.close_open(self):
		return true
	if RookieDraftSheet.close_open(self):
		return true
	if TopUpSheet.close_open(self):
		return true
	var sim_sheet := get_node_or_null("PreSeasonSimConfirm")
	if sim_sheet != null and is_instance_valid(sim_sheet) and not sim_sheet.is_queued_for_deletion():
		sim_sheet.queue_free()
		return true
	var rule := get_node_or_null("RuleSheet")
	if rule != null and is_instance_valid(rule) and not rule.is_queued_for_deletion():
		rule.queue_free()
		return true
	if _settings != null and is_instance_valid(_settings):
		_settings.queue_free()
		_settings = null
		return true
	return false
