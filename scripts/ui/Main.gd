extends Control
## Main menu: the title, Continue and New career, and a quiet How to play and
## Settings. New career opens a short setup (player names, the two difficulty dials); the
## club is chosen next, at the start of the draft, where each club's first
## pick is shown. The setup changes nothing until the career starts.

var _pitch: PitchView
var _content: VBoxContainer
## The setup's "Choose your club" button lives under the scrolling choices, so it
## stays in thumb reach however many choices the setup has.
var _footer: VBoxContainer
var _mode := "home"                 # "home" | "year" | "setup"
var _help_panel: PanelContainer
var _confirm_overlay: Control
var _guide_overlay: Control
var _settings_overlay: Control
var _load_error: Label
## "Last good save restored.", under Continue until the menu is left.
var _restore_note := ""
var _logo: TextureRect
## The setup's choices, applied only when the career starts.
var _pick_board := "fair"
var _pick_rivals := "shrewd"
var _pick_tutorials := true
## Canberra joins (in the 2027 redraft, or in 2030 on the real lists).
var _pick_canberra := false
var _canberra_row: VBoxContainer
## The coach has read and confirmed the 2030 warning for this setup (Canberra
## on the real lists plays 2027-2029 without you, director 2026-11-10).
var _sim_ahead_ok := false
## Your Club Forge club's row, and the line that replaces it when the start
## cannot take a created club (real 2026 lists, Rebuild).
var _forged_row: VBoxContainer
var _forged_note: VBoxContainer
var _setup_tight := false
## How the next career starts (ARD-M5-016): "redraft" or "real" (real 2026 lists).
var _pick_start := "redraft"
## A challenge start (row 114, Challenge.gd): "none", "youth", "rebuild" or
## "goal"; the goal itself starts unpicked (no recommended goal).
var _pick_challenge := "none"
var _pick_goal := ""
var _start_row: VBoxContainer
var _challenge_row: VBoxContainer
var _goal_row: VBoxContainer
var _start_btn: Button
var _pick_prospect := false
var _pick_club := false
## The season the career starts in (Datasets id; TODO row 142 L2): picked on the
## year step, which shows only when this build can start more than one.
var _pick_dataset := Datasets.DEFAULT
## The web build's one line when the browser refuses to keep the save (P-71), or "".
var _storage_line := ""

## The title art is GameLogo (the one place the logo file is named).
## The logo's widest and tallest on screen, and its share of a short window.
const LOGO_MAX_W := 560.0
const LOGO_MAX_H_SHARE := 0.26
const TAGLINE := "Build your dynasty."
## The promise, printed once on the menu (P-70). tools/check_android_permissions.py
## fails CI if the Android export ever asks for more than vibrate.
const OFFLINE_PROMISE := "Plays offline. No ads, no account."
## Where the career is kept, true on every platform: a browser build keeps it in the
## browser, the app and the desktop game on this device (it said "your phone" on all).
const KEPT_ON_DEVICE := "Your career stays on this device."
const KEPT_IN_BROWSER := "Your career stays in this browser."


## The promise as the menu prints it: two lines, the second naming where the save lives.
static func promise_text(web: bool) -> String:
	return OFFLINE_PROMISE + "\n" + (KEPT_IN_BROWSER if web else KEPT_ON_DEVICE)


## The title treatment: the logo, whole and undistorted. Its black ground
## adds nothing under an additive blend, so only the lettering shows over
## the menu's darkened oval - the file itself is left as supplied.
func _logo_art() -> TextureRect:
	_logo = TextureRect.new()
	_logo.name = "Logo"
	_logo.texture = GameLogo.art()
	_logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_logo.size_flags_horizontal = Control.SIZE_FILL
	_logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if UiKit.appearance() == "light":
		# The logo file has a black ground. In light mode key only
		# that near-black ground out so the lettering keeps its real colours.
		var shader := Shader.new()
		shader.code = "shader_type canvas_item;\nvoid fragment(){ vec4 c=texture(TEXTURE,UV); float hi=max(c.r,max(c.g,c.b)); c.a*=smoothstep(0.04,0.16,hi); COLOR=c; }"
		var mat := ShaderMaterial.new()
		mat.shader = shader
		_logo.material = mat
	else:
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		_logo.material = mat
	_fit_logo()
	return _logo


## Height from the width it can have (aspect kept), capped so a short
## window still shows the buttons.
func _fit_logo() -> void:
	if not is_instance_valid(_logo):
		return
	var aspect := GameLogo.aspect()
	var w := minf(LOGO_MAX_W, UiKit.view_width(self) - 32.0)
	var h := minf(w * aspect, UiKit.view_height(self) * LOGO_MAX_H_SHARE)
	_logo.custom_minimum_size = Vector2(0, roundf(h))


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_fit_logo()


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if GameState.new_career_setup_requested:
		GameState.new_career_setup_requested = false
		# Back from Choose your club: the options again, for the season picked.
		_pick_dataset = GameState.dataset if Datasets.ready(GameState.dataset) else Datasets.DEFAULT
		_mode = "setup"
	_pick_board = GameState.new_career_dial(DifficultyDials.BOARD)
	_pick_rivals = GameState.new_career_dial(DifficultyDials.RIVALS)
	_pick_tutorials = GameState.new_career_tutorials()
	# The oval stays as a faint ground; the logo and buttons carry the screen.
	_pitch = PitchView.new()
	_pitch.set_anchors_preset(Control.PRESET_FULL_RECT)
	_pitch.setup({"events": [], "roster": [[], []], "home": "", "away": ""})
	_pitch.modulate = Color(1, 1, 1, 0.22)
	_pitch.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_pitch)
	var shade := ColorRect.new()
	shade.color = UiKit.BG
	shade.color.a = 0.92 if UiKit.appearance() == "light" else 0.78
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	UiKit.apply_insets(margin, 16)
	add_child(margin)
	_content = UiKit.vbox(12)
	_content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var shell := UiKit.vbox(12)
	margin.add_child(shell)
	shell.add_child(UiKit.scroll(_content))
	_footer = UiKit.vbox(0)
	shell.add_child(_footer)
	get_viewport().size_changed.connect(func():
		if not UiKit.keyboard_resize(self):
			_render())
	_render()
	_patch_notes_once()
	if WebStorage.should_ask(WebStorage.on_web(), bool(GameState.get_setting(WebStorage.ASKED_KEY, false))):
		WebStorage.ask()
		_wait_for_storage_answer()


## Poll the browser's answer for a few seconds (a prompt may be open). A final answer is
## remembered so the browser is asked once; a refusal shows its line this visit only.
func _wait_for_storage_answer() -> void:
	for i in range(40):
		await get_tree().create_timer(0.5).timeout
		if not is_inside_tree():
			return
		var got := WebStorage.answer()
		if WebStorage.is_final(got):
			_on_storage_answer(got)
			return


func _on_storage_answer(got: String) -> void:
	GameState.set_setting(WebStorage.ASKED_KEY, true)
	if not WebStorage.notice_due(got, bool(GameState.get_setting(WebStorage.SHOWN_KEY, false))):
		return
	GameState.set_setting(WebStorage.SHOWN_KEY, true)
	_storage_line = WebStorage.REFUSED_LINE
	if _mode == "home":
		_render()


func _render() -> void:
	UiKit.clear(_footer)
	if _mode == "year":
		_show_year_step()
	elif _mode == "setup":
		_show_setup()
	else:
		_show_home()
	_footer.visible = _mode == "setup"
	_layout()


## The width of the button column and the setup form.
func _column_width(cap: float) -> float:
	return minf(cap, UiKit.view_width(self) - 48.0)


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
func _show_home() -> void:
	_mode = "home"
	UiKit.clear(_content)
	_content.alignment = BoxContainer.ALIGNMENT_CENTER
	_content.add_child(_logo_art())
	var tag := UiKit.subtitle(TAGLINE)
	tag.name = "Tagline"
	_content.add_child(tag)
	# A career file that cannot be continued says why, instead of the menu
	# quietly looking like there was never a career (T5.Q24). The space above
	# shrinks so the note sits as close to the tagline as to New career.
	var saved := not GameState.has_career() and GameState.has_saved_career()
	var why := "" if GameState.has_career() or saved else GameState.saved_career_problem()
	_content.add_child(UiKit.spacer(28 if why == "" else 6))

	var col := UiKit.vbox(10)
	col.name = "MenuButtons"
	col.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	col.custom_minimum_size.x = _column_width(320.0)
	_content.add_child(col)
	if not GameDB.loaded:
		var err := UiKit.lbl("Player data failed to load. Reinstall the game to play.",
				UiKit.SMALL, UiKit.BAD)
		err.name = "DataError"
		err.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		err.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		col.add_child(err)

	# A career in memory (back from the hub or the draft) or one on disk.
	var resume_draft := GameState.draft != null and not GameState.draft.user_club.is_empty() \
			and (GameState.season == null or GameState.club_yet_to_play())
	var live := resume_draft or GameState.season != null
	if live or saved:
		var cont := UiKit.btn("Continue", UiKit.H2, true)
		cont.name = "ResumeCareer" if live else "ContinueCareer"
		if live:
			cont.pressed.connect(func(): Router.go("draft" if resume_draft else "hub"))
		else:
			cont.pressed.connect(_on_continue)
		col.add_child(cont)
		var meta := GameState._save_meta() if live else GameState.saved_career_meta()
		if str(meta.get("club", "")) != "":
			# Which career Continue opens is what the coach decides on: TEXT, not MUTED.
			var info := UiKit.lbl(_meta_line(meta), UiKit.BODY, UiKit.TEXT)
			info.name = "CareerMeta"
			info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			col.add_child(info)
		if _restore_note != "":
			var note := UiKit.lbl(_restore_note, UiKit.BODY, UiKit.TEXT)
			note.name = "RestoreNote"
			note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			col.add_child(note)
	_load_error = UiKit.lbl("", UiKit.BODY, UiKit.BAD)
	_load_error.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_load_error.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_load_error.name = "SaveProblem"
	_load_error.visible = false
	col.add_child(_load_error)
	if why != "":
		_load_error.text = why
		_load_error.visible = true
		col.add_child(UiKit.spacer(10))
	var new_career := UiKit.btn("New career", UiKit.H2, not (live or saved))
	new_career.name = "NewCareer"
	# No career can start on missing or incomplete player data.
	new_career.disabled = not GameDB.loaded
	new_career.pressed.connect(_on_new_career)
	col.add_child(new_career)
	var forge := UiKit.btn("Club Forge", UiKit.NAME)
	forge.name = "ClubForge"
	forge.pressed.connect(func(): Router.go("forge"))
	col.add_child(forge)

	_content.add_child(UiKit.spacer(18))
	# A flow, so on a narrow window the last link wraps instead of leaving the screen.
	var quiet := HFlowContainer.new()
	quiet.add_theme_constant_override("h_separation", 4)
	quiet.alignment = FlowContainer.ALIGNMENT_CENTER
	quiet.add_child(_quiet_btn("How to play", "MenuHelp", _show_help))
	quiet.add_child(_quiet_btn("Settings", "MenuSettings", _show_settings))
	# The save from before the one Continue opens (row T7.R84). Only asked of a
	# career on disk: one in memory goes back through Settings, Earlier saves.
	if saved and CareerSave.has_backup(GameState.save_path):
		quiet.add_child(_quiet_btn(RESTORE_LAST_GOOD, "RestoreLastGood", _confirm_restore))
	# Last in the row, desktop only (director, 2026-10-12): Android Back already leaves
	# the app from this menu, iOS and the web have no quit of their own. The gate is the
	# platform (ScreenLayout.is_desktop), never the window width.
	if ScreenLayout.is_desktop():
		var exit := _quiet_btn("Exit game", "ExitGame", func(): Router.quit_game())
		exit.custom_minimum_size = Vector2(120, 48)
		quiet.add_child(exit)
	_content.add_child(quiet)
	_content.add_child(UiKit.spacer(10))
	var promise := UiKit.lbl(promise_text(WebStorage.on_web()), UiKit.SECONDARY, UiKit.MUTED)
	promise.name = "OfflinePromise"
	promise.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	promise.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_content.add_child(promise)
	if _storage_line != "":
		var storage := UiKit.lbl(_storage_line, UiKit.SECONDARY, UiKit.TEXT)
		storage.name = "StorageNotice"
		storage.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		storage.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_content.add_child(storage)
	# The quiet version line. When this version has patch notes it opens them
	# again (they open by themselves once, the first time the version runs).
	var build_text := "Build " + BuildInfo.label()
	if PatchNotes.lines().is_empty():
		var build := UiKit.lbl(build_text, UiKit.SMALL, UiKit.MUTED)
		build.name = "BuildLabel"
		build.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_content.add_child(UiKit.spacer(8))
		_content.add_child(build)
	else:
		var build := _quiet_btn("%s  ·  %s" % [build_text, PATCH_NOTES_TITLE], "BuildLabel", _show_patch_notes, UiKit.SMALL)
		build.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		_content.add_child(build)


## A secondary action that reads as text: no box, muted until pressed.
func _quiet_btn(text: String, node_name: String, cb := Callable(), fs := UiKit.BODY) -> Button:
	var b := UiKit.btn(text, fs)
	b.name = node_name
	b.flat = true
	b.custom_minimum_size = Vector2(120, 44)
	for state in ["normal", "hover", "pressed", "hover_pressed"]:
		b.add_theme_stylebox_override(state, StyleBoxEmpty.new())
	b.add_theme_color_override("font_color", UiKit.MUTED)
	b.add_theme_color_override("font_hover_color", UiKit.TEXT)
	b.add_theme_color_override("font_pressed_color", UiKit.TEXT)
	if cb.is_valid():
		b.pressed.connect(cb)
	return b


func _meta_line(meta: Dictionary) -> String:
	var club := str(meta.get("club", ""))
	var bits: PackedStringArray = []
	if club != "":
		# A created club is only registered once its career loads.
		bits.append(str(meta.get("club_name", "")) if str(meta.get("club_name", "")) != "" else GameDB.club_name(club))
	bits.append(str(meta.get("year", "")))
	if str(meta.get("stage", "")) != "":
		bits.append(str(meta["stage"]))
	return "  ·  ".join(bits)


func _on_continue() -> void:
	# Loading a career takes seconds on a phone: the cover and its line go up
	# first, and the screen change joins the same cover. Nothing here awaits
	# the cover: this screen is freed by the change, and a function resumed
	# after that errors ("class instance is gone").
	ScreenTransition.run("Loading your career...", func():
		if GameState.load_career():
			Router.go("hub" if GameState.season != null and not GameState.club_yet_to_play() else "draft")
		else:
			_show_load_error())


func _show_load_error() -> void:
	var why := GameState.saved_career_problem()
	_load_error.text = why if why != "" else GameState.SAVE_UNREADABLE
	_load_error.visible = true


func _on_new_career() -> void:
	_pick_board = GameState.new_career_dial(DifficultyDials.BOARD)
	_pick_rivals = GameState.new_career_dial(DifficultyDials.RIVALS)
	_pick_tutorials = GameState.new_career_tutorials()
	_pick_canberra = false
	_sim_ahead_ok = false
	_pick_challenge = "none"
	_pick_goal = ""
	_pick_prospect = not GameState.forge_player().is_empty()
	_pick_club = not GameState.forge_club().is_empty()
	_pick_dataset = Datasets.DEFAULT
	_mode = "year" if _has_year_step() else "setup"
	_render()


# ---------------------------------------------------------------------------
# New career: the year step (Legacy mode, TODO row 142 L2; director 2026-11-13,
# "Year step in setup")
# ---------------------------------------------------------------------------
## Each start's words: the heading and the one line under it. The figure is the
## first season the coach plays.
const YEAR_WORDS := {
	"2026": ["Today's league", "18 clubs. The real lists after the 2026 season, or a league redraft."],
	"2000": ["From the turn of the century", "16 clubs on their real lists. Take over from your club's senior coach and coach on through the years to today."],
	"1990": ["From the first AFL season", "14 clubs on their real lists. Take over from your club's senior coach and coach on through the years to today."],
}


## The step shows when this build has more than one start (Datasets.ready_ids).
func _has_year_step() -> bool:
	return Datasets.ready_ids().size() > 1


## A start in a past season (not today's league).
func _past_start() -> bool:
	return _pick_dataset != Datasets.DEFAULT


func _show_year_step() -> void:
	_mode = "year"
	UiKit.clear(_content)
	_content.alignment = BoxContainer.ALIGNMENT_BEGIN
	_content.add_child(UiKit.top_bar("", true, null, func():
		_close_setup()
		return true))
	var above := Control.new()
	above.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_content.add_child(above)
	var form := UiKit.vbox(UiKit.SECTION)
	form.name = "StartYear"
	form.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	# A wide screen sets the starts side by side; a phone stacks them.
	var wide := ScreenLayout.wide_view(UiKit.view_width(self), UiKit.view_height(self), 520.0)
	form.custom_minimum_size.x = _column_width(880.0 if wide else 440.0)
	_content.add_child(form)
	var head := UiKit.vbox(4)
	head.add_child(UiKit.lbl("New career", UiKit.H1, UiKit.TEXT, true))
	head.add_child(UiKit.lbl("Which season do you start in?", UiKit.NAME, UiKit.MUTED))
	form.add_child(head)
	var starts := GridContainer.new()
	starts.name = "Starts"
	starts.columns = 2 if wide else 1
	starts.add_theme_constant_override("h_separation", UiKit.SECTION)
	starts.add_theme_constant_override("v_separation", UiKit.SECTION)
	form.add_child(starts)
	# Today's league first, then back through the years.
	var ids := Datasets.ready_ids()
	ids.reverse()
	for id in ids:
		starts.add_child(_year_button(str(id), wide))
	var below := Control.new()
	below.size_flags_vertical = Control.SIZE_EXPAND_FILL
	below.size_flags_stretch_ratio = SETUP_BELOW
	_content.add_child(below)


## One start, the whole block one tap: the first season as a big figure, what
## it is, and one line on what you take on. Side by side (`tall`), the figure
## sits above the words.
func _year_button(id: String, tall := false) -> Button:
	var year := int(Datasets.get_set(id).get("start_year", 0))
	var words: Array = YEAR_WORDS.get(id, ["The %d season" % year, ""])
	var b := UiKit.btn("", UiKit.NAME)
	b.name = "StartYear_" + id
	# A button does not grow with its children: room for the figure above three lines when tall.
	b.custom_minimum_size = Vector2(0, 136 if tall else 104)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.tooltip_text = "Start in %d" % year
	var pad := MarginContainer.new()
	pad.set_anchors_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]:
		pad.add_theme_constant_override("margin_" + side, 14 if side in ["left", "right"] else 10)
	var row: BoxContainer = UiKit.vbox(6) if tall else UiKit.hbox(14)
	row.alignment = BoxContainer.ALIGNMENT_BEGIN if tall else BoxContainer.ALIGNMENT_CENTER
	pad.add_child(row)
	var fig := UiKit.figure(str(year), UiKit.HERO, UiKit.TEXT)
	fig.name = "Year"
	fig.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	row.add_child(fig)
	var text := UiKit.vbox(2)
	text.alignment = BoxContainer.ALIGNMENT_CENTER
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(text)
	text.add_child(UiKit.lbl(str(words[0]), UiKit.NAME, UiKit.TEXT, true))
	if str(words[1]) != "":
		var line := UiKit.lbl(str(words[1]), UiKit.SECONDARY, UiKit.MUTED)
		line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		text.add_child(line)
	for n in [pad, row, fig, text] + text.get_children():
		(n as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(pad)
	b.pressed.connect(_on_pick_year.bind(id))
	return b


func _on_pick_year(id: String) -> void:
	_pick_dataset = id
	_sim_ahead_ok = false
	if _past_start():
		# A past season starts on its real lists, or a League redraft of its
		# clubs (director 2026-11-13); a challenge, Canberra and your Club Forge
		# club or prospect belong to today's league.
		_pick_start = "real"
		_pick_challenge = "none"
		_pick_goal = ""
		_pick_canberra = false
	_mode = "setup"
	_render()


## Back from the setup: to the year step when there is one, else the menu.
func _back_from_setup() -> void:
	if _has_year_step():
		_mode = "year"
		_render()
	else:
		_close_setup()


# ---------------------------------------------------------------------------
# New career setup
# ---------------------------------------------------------------------------
## Space under the setup block relative to the space above it: a little
## more below, so the block sits just above the middle of the screen.
const SETUP_BELOW := 1.3

func _show_setup() -> void:
	_mode = "setup"
	UiKit.clear(_content)
	_content.alignment = BoxContainer.ALIGNMENT_BEGIN
	# Back stays where a thumb expects it; everything else is one block -
	# title, the two choices, the button right under them - centred on the
	# screen (a touch above the middle), over the faint oval.
	_content.add_child(UiKit.top_bar("", true, null, func():
		_back_from_setup()
		return true))
	var above := Control.new()
	above.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_content.add_child(above)
	# Six choices do not fit a phone at the usual spacing, and the button must
	# stay on screen: on a short screen the rows sit closer, close enough that
	# the whole setup fits a 390 x 844 phone without scrolling.
	_setup_tight = UiKit.view_height(self) < 900.0
	var form := UiKit.vbox(5 if _setup_tight else UiKit.SECTION)
	form.name = "NewCareerSetup"
	form.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	form.custom_minimum_size.x = _column_width(440.0)
	_content.add_child(form)
	var title := UiKit.lbl("New career", UiKit.H1, UiKit.TEXT, true)
	title.name = "SetupTitle"
	# A little more under the title than between the sections.
	title.custom_minimum_size.y = (UiKit.H1 * 1.15) if _setup_tight else (UiKit.H1 * 1.4 + 6)
	form.add_child(title)
	if _has_year_step():
		var yr := UiKit.lbl("Starting in %d" % int(Datasets.get_set(_pick_dataset).get("start_year", 0)),
				UiKit.NAME, UiKit.MUTED)
		yr.name = "SetupYear"
		form.add_child(yr)
	var first := int(Datasets.get_set(_pick_dataset).get("start_year", 2027))
	_start_row = _choice("Start", "StartMode",
			[["redraft", "League redraft"], ["real", "Real %d lists" % (first if _past_start() else 2026)]],
			_pick_start,
			func(k): return (_real_start_line() if k == "real"
					else "The whole league re-drafts from one player pool before %d, in a random snake order.%s" % [
						first, _past_coach_line()]),
			_on_pick_start)
	# A past start says up front that you replace your club's senior coach.
	(_start_row.get_node("StartModeNote") as Label).visible = _past_start()
	form.add_child(_start_row)
	# A challenge start (ruling 115): one rule, said here before you begin.
	_challenge_row = _choice("Challenge", "Challenge",
			[["none", "None"], ["youth", "Youth only"], ["rebuild", "Rebuild"], ["goal", "Your goal"]],
			_pick_challenge, func(k): return Challenge.rule_line(str(k)), _on_pick_challenge)
	(_challenge_row.get_node("ChallengeNote") as Label).visible = true
	form.add_child(_challenge_row)
	# Your goal: none is picked for you, and Choose your club waits for one.
	var goals := []
	for id in Challenge.GOAL_ORDER:
		goals.append([id, GOAL_BUTTONS.get(id, id)])
	_goal_row = _choice("Your goal", "Goal", goals, _pick_goal,
			func(k): return Challenge.goal_detail(str(k)) if str(k) != "" else "Pick the goal you are setting yourself.",
			func(k):
				_pick_goal = k
				_refresh_start())
	(_goal_row.get_node("GoalNote") as Label).visible = true
	_goal_row.visible = _pick_challenge == "goal" and not _past_start()
	form.add_child(_goal_row)
	# A past season: its real lists or a redraft, and no challenge (today's league only).
	_challenge_row.visible = not _past_start()
	form.add_child(_dial_choice(DifficultyDials.BOARD, "BoardPatience", _pick_board,
			func(k): _pick_board = k))
	form.add_child(_dial_choice(DifficultyDials.RIVALS, "RivalRecruiting", _pick_rivals,
			func(k): _pick_rivals = k))
	form.add_child(_choice("Tutorials", "Tutorials", [["on", "On"], ["off", "Off"]],
			"on" if _pick_tutorials else "off",
			func(k): return ("A short note the first time you open each screen, saying what it shows and how to use it." if k == "on"
					else "No notes open by themselves. You can change this later in Settings."),
			func(k): _pick_tutorials = k == "on"))
	# Canberra, the second new club: a choice made once, here (director,
	# 2026-10-14), asked as a question (2026-11-08). What Yes and No mean
	# depends on the start (_canberra_line).
	_canberra_row = _choice("Canberra joins?", "Canberra", [["yes", "Yes"], ["no", "No"]],
			"yes" if _pick_canberra else "no",
			func(k): return _canberra_line(str(k)),
			func(k):
				_pick_canberra = k == "yes"
				_repaint_canberra()
				if _pick_canberra and _plays_years_without_you() and not _sim_ahead_ok:
					_open_sim_ahead_sheet(false))
	_canberra_row.name = "Canberra"
	_canberra_row.visible = not _past_start()
	form.add_child(_canberra_row)
	# Your Club Forge player, if you made one: he enters this career's first
	# National Draft like any other prospect.
	var forged := GameState.forge_player()
	if not forged.is_empty() and not _past_start():
		var who := "%s %s" % [forged.get("first", ""), forged.get("last", "")]
		form.add_child(_choice("Your prospect", "Prospect", [["in", "Bring " + who], ["out", "Not this time"]],
				"in" if _pick_prospect else "out",
				func(_k): return "He enters this career's first National Draft. No club is told to take him; where he goes is up to the draft.",
				func(k): _pick_prospect = k == "in"))
	# Your Club Forge club, if you made one: an extra club in this career. It
	# only joins a League redraft (it has no real 2026 list): on the other
	# starts one line says so in place of the row, and the pick is kept for
	# when the start goes back to a redraft (director, 2026-11-08).
	_forged_row = null
	_forged_note = null
	var club := GameState.forge_club()
	if not club.is_empty() and not _past_start():
		_forged_row = _choice("Your club", "ForgedClub", [["in", "Bring " + str(club.get("name", ""))], ["out", "Not this time"]],
				"in" if _pick_club else "out",
				func(_k): return "It joins the competition as an extra club and drafts its list in the League Draft like everyone else. Choose it as your club next, or coach against it.",
				func(k):
					_pick_club = k == "in"
					_repaint_canberra())
		_forged_row.name = "ForgedClub"
		form.add_child(_forged_row)
		# In its place on the other starts: the same heading, and why.
		_forged_note = UiKit.vbox(2 if _setup_tight else 8)
		_forged_note.name = "ForgedClubOnly"
		_forged_note.add_child(UiKit.lbl("Your club", UiKit.H2, UiKit.TEXT, true))
		var why := UiKit.lbl(FORGED_REDRAFT_ONLY, UiKit.SMALL, UiKit.MUTED)
		why.name = "ForgedClubOnlyNote"
		why.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_forged_note.add_child(why)
		form.add_child(_forged_note)
		_show_forged_row()
	# The button sits under the scrolling choices, always on screen: with the two
	# dials the setup is taller than a phone, and the button was below the fold.
	var start := UiKit.btn("Choose your club", UiKit.H2, true)
	start.name = "StartCareer"
	start.custom_minimum_size = Vector2(_column_width(440.0), 52)
	start.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_start_btn = start
	_refresh_start()
	start.pressed.connect(_on_start)
	var cta := MarginContainer.new()
	cta.add_theme_constant_override("margin_top", 6)
	cta.add_child(start)
	_footer.add_child(cta)
	var below := Control.new()
	below.size_flags_vertical = Control.SIZE_EXPAND_FILL
	below.size_flags_stretch_ratio = SETUP_BELOW
	_content.add_child(below)


## The goal buttons' short names (the full goal is in Challenge.GOALS).
const GOAL_BUTTONS := {"flag_homegrown": "Home-grown flag", "coach_300": "300 games"}


## Rebuild takes over the bottom club of the real 2026 ladder, so it needs
## Real 2026 lists: choosing a League redraft drops it.
func _on_pick_start(k: String) -> void:
	_pick_start = k
	_sim_ahead_ok = false
	if k != "real" and _pick_challenge == "rebuild":
		_pick_challenge = "none"
		(_challenge_row.get_meta("select") as Callable).call("none")
	_show_forged_row()
	_repaint_canberra()
	_refresh_start()


func _on_pick_challenge(k: String) -> void:
	_pick_challenge = k
	_sim_ahead_ok = false
	if k == "rebuild" and _pick_start != "real":
		_pick_start = "real"
		(_start_row.get_meta("select") as Callable).call("real")
	if is_instance_valid(_goal_row):
		_goal_row.visible = k == "goal"
	_show_forged_row()
	_repaint_canberra()
	_refresh_start()


const FORGED_REDRAFT_ONLY := "Your club joins League redraft careers only."


## The Forge club's row shows on a League redraft; the other starts show the
## line saying why it is gone. The pick itself is untouched.
func _show_forged_row() -> void:
	var redraft := _pick_start != "real" and _pick_challenge != "rebuild"
	if is_instance_valid(_forged_row):
		_forged_row.visible = redraft
	if is_instance_valid(_forged_note):
		_forged_note.visible = not redraft


## Your Forge club comes into this career: brought, and the start takes it.
func _forged_joins() -> bool:
	return _pick_club and _pick_start != "real" and _pick_challenge != "rebuild" \
			and not GameState.forge_club().is_empty()


## The Canberra question's rule, for the start picked (director, 2026-11-08):
## a redraft takes Tasmania, and Canberra on Yes, into the 2027 draft as
## equals; the real lists with Canberra play 2027-2029 without you and start
## in 2030; Rebuild keeps its 2027 start.
func _canberra_line(k: String) -> String:
	var fixed := " It cannot be changed once the career starts."
	if _pick_start != "real" and _pick_challenge != "rebuild":
		var n := 19 + (1 if k == "yes" else 0) + (1 if _forged_joins() else 0)
		if k == "yes":
			return ("Tasmania and Canberra draft in the 2027 League redraft as equals: no priority picks and no extra cap room. %d clubs from 2027, and either new club can be yours." % n) + fixed
		return ("Tasmania drafts in the 2027 League redraft as an equal and can be yours. %d clubs from 2027; Canberra never join." % n) + fixed
	if _pick_challenge == "rebuild":
		if k == "yes":
			return "Rebuild starts in 2027, or take Tasmania (2028) or Canberra (2030) and build from nothing. 20 clubs from 2030." + fixed
		return "Rebuild starts in 2027, or take Tasmania (2028) and build from nothing. The league stays at 19 clubs." + fixed
	if k == "yes":
		return "2027 to 2029 play out without you, every club run by its own staff: Tasmania join in 2028 and Canberra build their first list. You then choose any of the 20 clubs and start in 2030. Take Canberra and you build their list with the same new-club picks and cap room a rival coach gets." + fixed
	return "You start in 2027, or take Tasmania and start in 2028, when they join. The league stays at 19 clubs." + fixed


## The real-lists start: with Canberra (and no Rebuild) the career starts in
## 2030, after three seasons played without you.
func _real_start_line() -> String:
	if _past_start():
		return "Every club keeps its real %d list.%s" % [
			int(Datasets.get_set(_pick_dataset).get("start_year", 0)), _past_coach_line()]
	if _pick_canberra and _pick_challenge != "rebuild":
		return "Every club keeps its real end-of-2026 list. The league plays 2027 to 2029 without you; then you choose your club and start in 2030."
	return "Every club keeps its real end-of-2026 list. You run your club through the 2026 National Draft, then play 2027; or take Tasmania and start in 2028."


## A past start, either way: you take over from your club's senior coach.
func _past_coach_line() -> String:
	if not _past_start():
		return ""
	return " You take over from your club's senior coach, and he joins the coaches any club can hire."


## The Canberra rule follows the start and the Forge club's pick.
func _repaint_canberra() -> void:
	if is_instance_valid(_canberra_row):
		(_canberra_row.get_meta("select") as Callable).call("yes" if _pick_canberra else "no")
	if is_instance_valid(_start_row):
		(_start_row.get_meta("select") as Callable).call(_pick_start)


## Choose your club waits for the data, and for a goal when you set one.
func _refresh_start() -> void:
	if not is_instance_valid(_start_btn):
		return
	_start_btn.disabled = not GameDB.loaded or (_pick_challenge == "goal" and _pick_goal == "")


## The challenge as GameState keeps it ({} for none).
func _challenge_state() -> Dictionary:
	match _pick_challenge:
		"youth":
			return {"kind": "youth"}
		"rebuild":
			return {"kind": "rebuild"}
		"goal":
			return {"kind": "goal", "goal": _pick_goal, "met_year": 0}
	return {}


## A labelled row of options, the current one outlined, with a "?" that
## shows the rule behind them on request instead of a permanent paragraph.
## `info` maps the current key to its explanation; `on_pick` records a pick.
func _choice(title: String, prefix: String, options: Array, current: String,
		info: Callable, on_pick: Callable) -> VBoxContainer:
	var v := UiKit.vbox(2 if _setup_tight else 8)
	var head := UiKit.hbox(4)
	var t := UiKit.lbl(title, UiKit.H2, UiKit.TEXT, true)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(t)
	var help := _quiet_btn("?", prefix.trim_suffix("Mode") + "Info")
	help.custom_minimum_size = Vector2(44, 44)
	help.tooltip_text = "What this means"
	head.add_child(help)
	v.add_child(head)
	var row := UiKit.hbox(8)
	v.add_child(row)
	var note := UiKit.lbl("", UiKit.SMALL, UiKit.MUTED)
	note.name = prefix + "Note"
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	note.visible = false
	v.add_child(note)
	help.pressed.connect(func(): note.visible = not note.visible)
	var buttons := {}
	var state := {"key": current}
	var paint := func():
		for k in buttons:
			UiKit.set_selected(buttons[k], k == state["key"])
		note.text = str(info.call(state["key"]))
	for opt in options:
		var key := str(opt[0])
		var b := UiKit.btn(str(opt[1]), UiKit.NAME)
		b.name = "%s_%s" % [prefix, key]
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.pressed.connect(func():
			state["key"] = key
			on_pick.call(key)
			paint.call())
		row.add_child(b)
		buttons[key] = b
	paint.call()
	# Another row may move this one's pick (Rebuild needs Real 2026 lists).
	v.set_meta("select", func(k):
		state["key"] = k
		paint.call())
	return v


## A difficulty dial (board patience, rival recruiting): its title, three
## named steps with the current one outlined, and under them one plain
## sentence saying what the picked step means - always shown, so nobody has to
## open a "?" to learn what they are choosing. Sizes stay in
## data/difficulty_dials.json and never reach the screen.
func _dial_choice(dial: String, prefix: String, current: String, on_pick: Callable) -> VBoxContainer:
	var v := UiKit.vbox(2 if _setup_tight else 8)
	# The title takes the height of the other rows' header (their "?" is 44 high),
	# so the setup keeps one rhythm.
	var head := UiKit.lbl(DifficultyDials.title(dial), UiKit.H2, UiKit.TEXT, true)
	head.custom_minimum_size.y = 44
	head.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	v.add_child(head)
	var row := UiKit.hbox(8)
	v.add_child(row)
	var note := UiKit.lbl("", UiKit.SMALL, UiKit.MUTED)
	note.name = prefix + "Note"
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(note)
	var buttons := {}
	var state := {"key": current}
	var paint := func():
		for k in buttons:
			UiKit.set_selected(buttons[k], k == state["key"])
		note.text = DifficultyDials.text(dial, str(state["key"]))
	for key in DifficultyDials.order(dial):
		var b := UiKit.btn(DifficultyDials.label(dial, key), UiKit.NAME)
		b.name = "%s_%s" % [prefix, key]
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.pressed.connect(func():
			state["key"] = key
			on_pick.call(key)
			paint.call())
		row.add_child(b)
		buttons[key] = b
	paint.call()
	return v


func _close_setup() -> void:
	_mode = "home"
	_render()


func _on_start() -> void:
	# Canberra on the real lists: the 2030 warning first, if the coach has not
	# confirmed it for this setup (the start may have changed since Yes).
	if _plays_years_without_you() and not _sim_ahead_ok:
		_open_sim_ahead_sheet(true)
		return
	if GameState.has_career() or GameState.has_saved_career():
		_confirm_new_career()
		return
	_start_new_career()


func _start_new_career() -> void:
	GameState.set_new_career_dial(DifficultyDials.BOARD, _pick_board)
	GameState.set_new_career_dial(DifficultyDials.RIVALS, _pick_rivals)
	GameState.set_new_career_tutorials(_pick_tutorials)
	# The old save stays on disk until the new career has a club and its first
	# save replaces it: backing out of Choose your club must not cost the player
	# the career they had (reset() clears memory only).
	GameState.reset(_pick_dataset)
	if _past_start():
		# A past season: its clubs on their real lists, or a League redraft of
		# its clubs, straight to Choose your club.
		GameState.set_canberra(false)
		GameState.interview_due = true
		GameState.challenge = {}
		if _pick_start == "real":
			GameState.begin_real_lists()
		else:
			GameState.begin_draft()
		Router.go("draft")
		return
	GameState.set_canberra(_pick_canberra)
	# A new career opens with the appointment interview (row 119).
	GameState.interview_due = true
	GameState.challenge = _challenge_state()
	if _pick_challenge == "rebuild":
		_pick_start = "real"
	# A created club has no real 2026 list, so it only joins a League redraft.
	if _pick_club and _pick_start != "real":
		var club := GameState.forge_club()
		if not club.is_empty():
			GameState.create_club(club)
	if _pick_prospect:
		var forged := GameState.forge_player()
		if not forged.is_empty():
			GameState.add_custom_prospect(forged)
	if _plays_years_without_you():
		_play_years_without_you()
		return
	if _pick_start == "real":
		GameState.begin_real_lists()
	else:
		GameState.begin_draft()
	Router.go("draft")


## This setup starts in 2030: real 2026 lists with Canberra, and no Rebuild.
func _plays_years_without_you() -> bool:
	return not _past_start() and _pick_start == "real" and _pick_canberra and _pick_challenge != "rebuild"


## The warning before a 2030 start commits (director, 2026-11-10: "if you click
## YES to canberra joining, you should be warned that the game will sim to
## 2030"). Back takes Canberra out again; the other button keeps it, and from
## the Choose your club button it starts the career at once.
func _open_sim_ahead_sheet(from_start: bool) -> void:
	_close_confirm()
	var first := GameState.SIM_AHEAD_TO
	var box := UiKit.modal_box(self, 460.0, 0.0)
	_confirm_overlay = box["overlay"]
	_confirm_overlay.name = "SimAheadWarning"
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.heading("Your first season is %d" % first, UiKit.H1))
	for line in [
			"Canberra join the league in %d. With them in, %d to %d play out without you." % [first, GameDB.START_YEAR, first - 1],
			"Every club is run by its own staff in those three seasons: they pick the sides, trade, sign free agents and draft. Tasmania join in %d, Canberra build their first list, and three premierships are decided." % GameDB.enter_year("TAS"),
			"At the %d National Draft you choose any of the 20 clubs, face the press as their new coach and start in %d." % [first - 1, first]]:
		var l := UiKit.lbl(line, UiKit.BODY, UiKit.TEXT)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(l)
	var row := UiKit.hbox(8)
	box["footer"].add_child(row)
	var back := UiKit.btn("Back", UiKit.NAME)
	back.name = "SimAheadBack"
	var go := UiKit.btn("Start in %d" % first, UiKit.NAME, true)
	go.name = "SimAheadConfirm"
	for b in [back, go]:
		(b as Control).custom_minimum_size = Vector2(0, 48)
		(b as Control).size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(b)
	back.pressed.connect(_cancel_sim_ahead)
	go.pressed.connect(func():
		_sim_ahead_ok = true
		_close_confirm()
		if from_start:
			_on_start())


## Back on the 2030 warning: Canberra stay out, and the setup is as it was.
func _cancel_sim_ahead() -> void:
	_close_confirm()
	_pick_canberra = false
	_repaint_canberra()


## Real 2026 lists with Canberra (director, 2026-11-08): 2027 to 2029 play out
## under the cover, a line for each round, then Choose your club opens at the
## 2029 National Draft.
func _play_years_without_you() -> void:
	ScreenTransition.run("Playing 2027 to 2029...", func():
		await ScreenTransition.drawn()
		if GameState.begin_from_history(GameState.SIM_AHEAD_TO):
			Router.go("draft")
			return
		GameState.begin_sim_ahead()
		while true:
			var line := GameState.sim_ahead_step()
			if line == "":
				break
			ScreenTransition.show_line(line)
			await ScreenTransition.drawn()
		Router.go("draft"))


func _confirm_new_career() -> void:
	var box := UiKit.modal_box(self, 460.0, 260.0)
	_confirm_overlay = box["overlay"]
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.lbl("Start a new career?", 20, UiKit.EMPH, true))
	var meta := GameState.saved_career_meta()
	var what := "your current career"
	if not meta.is_empty():
		what = "your saved career (%s)" % _meta_line(meta)
	var body := UiKit.lbl("This replaces %s. It cannot be undone." % what, 14, UiKit.TEXT)
	body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(body)
	var go := UiKit.btn("Start new career", UiKit.NAME, true)
	go.name = "ConfirmNewCareer"
	go.custom_minimum_size = Vector2(0, 44)
	go.pressed.connect(func():
		_close_confirm()
		_start_new_career())
	box["footer"].add_child(go)
	var cancel := UiKit.btn("Cancel", UiKit.NAME)
	cancel.custom_minimum_size = Vector2(0, 44)
	cancel.pressed.connect(_close_confirm)
	box["footer"].add_child(cancel)


# ---------------------------------------------------------------------------
# Restore last good save, and the patch notes (row T7.R84)
# ---------------------------------------------------------------------------
const RESTORE_LAST_GOOD := "Restore last good save"
const RESTORE_UNREADABLE := "The save before your last one could not be read.\nYour career is unchanged."
const RESTORED := "Last good save restored."
const PATCH_NOTES_TITLE := "What's new"


## Asks first, naming the save it goes back to. The two saves swap, so the
## same entry undoes it.
func _confirm_restore() -> void:
	_restore_note = ""
	var bak := CareerSave.backup(GameState.save_path)
	if not bool(bak["ok"]):
		_load_error.text = RESTORE_UNREADABLE
		_load_error.visible = true
		return
	_close_confirm()
	var box := UiKit.modal_box(self, 460.0, 320.0)
	_confirm_overlay = box["overlay"]
	_confirm_overlay.name = "RestoreConfirm"
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.lbl(RESTORE_LAST_GOOD + "?", 20, UiKit.EMPH, true))
	var lead := UiKit.lbl("This goes back to the save before your last one:", 14, UiKit.TEXT)
	lead.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(lead)
	var which := UiKit.lbl(OptionsSheet._save_line(bak["meta"]), 14, UiKit.TEXT, true)
	which.name = "RestoreWhich"
	which.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(which)
	var kept := UiKit.lbl("The save you have now is kept. Restore again to return to it.", 14, UiKit.TEXT)
	kept.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(kept)
	var go := UiKit.btn("Restore", UiKit.NAME, true)
	go.name = "ConfirmRestore"
	go.custom_minimum_size = Vector2(0, 44)
	go.pressed.connect(func():
		_close_confirm()
		var ok := CareerSave.restore_backup(GameState.save_path)
		_restore_note = RESTORED if ok else ""
		_render()
		if not ok:
			_load_error.text = RESTORE_UNREADABLE
			_load_error.visible = true)
	box["footer"].add_child(go)
	var cancel := UiKit.btn("Cancel", UiKit.NAME)
	cancel.name = "CancelRestore"
	cancel.custom_minimum_size = Vector2(0, 44)
	cancel.pressed.connect(_close_confirm)
	box["footer"].add_child(cancel)


## The first time a version runs on a device that has run an earlier one, its
## patch notes open over the menu; the version is recorded so they never open
## by themselves again. A first run only records the version.
func _patch_notes_once() -> void:
	if _mode != "home":
		return
	var seen := str(GameState.get_setting(PatchNotes.SEEN_KEY, ""))
	if seen == PatchNotes.version():
		return
	GameState.set_setting(PatchNotes.SEEN_KEY, PatchNotes.version())
	if PatchNotes.due(seen):
		_show_patch_notes()


func _show_patch_notes() -> void:
	_close_confirm()
	var box := UiKit.modal_box(self, 460.0)
	_confirm_overlay = box["overlay"]
	_confirm_overlay.name = "PatchNotes"
	var v: VBoxContainer = box["body"]
	v.add_child(UiKit.lbl(PATCH_NOTES_TITLE, 20, UiKit.EMPH, true))
	v.add_child(UiKit.lbl("Build %s" % PatchNotes.version(), UiKit.SMALL, UiKit.MUTED))
	var notes := UiKit.vbox(12)
	notes.name = "PatchNotesLines"
	for text in PatchNotes.lines():
		var line := UiKit.lbl(str(text), UiKit.BODY, UiKit.TEXT)
		line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		notes.add_child(line)
	v.add_child(UiKit.spacer(4))
	v.add_child(notes)
	v.add_child(UiKit.spacer(6))
	var close := UiKit.btn("Close", UiKit.NAME, true)
	close.name = "PatchNotesClose"
	close.custom_minimum_size = Vector2(0, 44)
	close.pressed.connect(_close_confirm)
	box["footer"].add_child(close)


func _close_confirm() -> void:
	if is_instance_valid(_confirm_overlay):
		_confirm_overlay.queue_free()
	_confirm_overlay = null


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
## Display preferences, which apply at once, and (outside the web build) a
## way to quit that does not compete with the menu.
func _show_settings() -> void:
	_settings_overlay = OptionsSheet.open(self, false, true)


func _close_settings() -> void:
	if is_instance_valid(_settings_overlay):
		_settings_overlay.queue_free()
	_settings_overlay = null


func _layout() -> void:
	if is_instance_valid(_help_panel):
		var viewport_size := get_viewport().get_visible_rect().size
		_help_panel.size = Vector2(minf(560, viewport_size.x - 24), minf(600, viewport_size.y - 24))
		_help_panel.position = (viewport_size - _help_panel.size) / 2


## Router back hook: close whatever is open, then leave the setup; on the
## menu itself Back does nothing.
func handle_back() -> bool:
	if is_instance_valid(_guide_overlay):
		if StatGuide.back(_guide_overlay):
			return true
		_guide_overlay.queue_free()
		_guide_overlay = null
		return true
	if is_instance_valid(_confirm_overlay):
		if _confirm_overlay.name == "SimAheadWarning":
			_cancel_sim_ahead()
		else:
			_close_confirm()
		return true
	if is_instance_valid(_settings_overlay):
		_close_settings()
		return true
	if is_instance_valid(_help_panel):
		var overlay := _help_panel.get_parent()
		_help_panel = null
		overlay.queue_free()
		return true
	if _mode == "setup":
		_back_from_setup()
		return true
	if _mode == "year":
		_close_setup()
		return true
	return false


func _show_help() -> void:
	var overlay := ColorRect.new()
	overlay.color = Color(0, 0, 0, 0.8)
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(overlay)
	_help_panel = UiKit.panel(UiKit.PANEL, 16, 12)
	overlay.add_child(_help_panel)
	var v := UiKit.vbox(12)
	_help_panel.add_child(v)
	v.add_child(UiKit.heading("How to play", UiKit.H1))
	var text := UiKit.lbl(
			("1. Choose your club. All %d clubs start with empty lists.\n\n"
			% GameDB.active_clubs(GameDB.START_YEAR).size())
			+ "2. Draft from one shared player pool under the same cap. The random order reverses each round. Rivals pick between your turns. Tap a player to see what kind of footballer he is; only the Draft button picks him.\n\n"
			+ "3. Track every selection in Picks. The position cards in the pool show your list's coverage; tap one to filter the pool. Carry at least two rucks.\n\n"
			+ "4. Play 24 rounds, with matches driven by your players' rated abilities. Set your tactics in the coach box. After each game every player develops: his development (By position to start) decides the kind of footballer he becomes, and fit players you leave out develop in the reserves at about half the senior rate. Choose each player's development in Training.\n\n"
			+ "5. Pick your own side on the Team screen, or let the best 23 be picked around injuries. Two of your five midfielders play the wings: a runner suits it, a ball-winner is wasted there. A tagger makes a tag bite.\n\n"
			+ ("6. Finish in the top %d to play finals and chase the flag. The top four start in the qualifying finals, 5-10 in the wildcards and eliminations. The season's awards, the honour roll and league records are in the Season Review.\n\n"
			% Season.FINALISTS)
			+ "7. In the off-season, re-sign, release, sign free agents and trade in Trades & Contracts, then draft the next class. The hub's League news follows the whole league.\n\n"
			+ "Two dials are set when you start a new career. Board patience is how many poor seasons the board puts up with before it warns you, and then moves on you. Rival recruiting is how hard the other clubs bargain when they trade with you. Players develop by the same rules whatever you pick.\n\n"
			+ "Rotate your device at any time. Your draft picks, search and filters stay intact.", 16)
	v.add_child(UiKit.scroll(text))
	var guide := UiKit.btn("Stat guide", UiKit.NAME)
	guide.name = "MenuStatGuide"
	guide.pressed.connect(func():
		_help_panel = null
		overlay.queue_free()
		_guide_overlay = StatGuide.show(self))
	v.add_child(guide)
	var ok := UiKit.btn("Got it", UiKit.NAME, true)
	ok.pressed.connect(func():
		_help_panel = null
		overlay.queue_free())
	v.add_child(ok)
	_layout()
