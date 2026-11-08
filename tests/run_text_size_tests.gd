extends SceneTree
## godot --headless --path . --script tests/run_text_size_tests.gd
## Text size (row 118, T3.R10): Standard, Larger or Largest from Settings grows
## the game's words through UiKit.px in one place, is kept in the settings file
## and read back on the next start, and never grows a size twice. No state
## shown by colour alone (P-10): every GOOD/BAD (or win/loss) colour choice in
## the screens is listed here with the word, mark or number that says the same
## thing, so a new one has to name its second cue. The career screens are
## walked at Largest on one seeded Melbourne career (SUITE_SEED).

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")
const SUITE_SEED := 2031
const CLUB := "MEL"

var _checks := 0
var _failures: Array = []
var _gs: Node
var _router: Node
## Loaded once the autoloads are up: these classes name GameDB and GameState,
## which a --script runner has not made yet when it compiles.
var UK
var NI
var NL
var TL
var TR
var PS
var MN
var OFF
var CT


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _settle(n := 6) -> void:
	for i in range(n):
		await process_frame


func _run() -> void:
	await process_frame
	_gs = root.get_node("GameState")
	_router = root.get_node("Router")
	UK = load("res://scripts/ui/UiKit.gd")
	NI = load("res://scripts/ui/NameInk.gd")
	NL = load("res://scripts/ui/NameLink.gd")
	TL = load("res://scripts/ui/TraitLink.gd")
	TR = load("res://scripts/sim/Traits.gd")
	PS = load("res://scripts/ui/PlayerSheet.gd")
	MN = load("res://scripts/ui/match/MatchNotes.gd")
	OFF = load("res://scripts/ui/OffseasonScene.gd")
	CT = load("res://scripts/sim/Contracts.gd")
	_gs.autosave_enabled = false
	_gs.save_path = "user://test_text_size.save"
	_gs.settings_path = "user://test_text_size.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(_gs.settings_path))
	for key in load("res://scripts/ui/FirstVisitIntro.gd").TEXT:
		_gs.set_setting("seen_%s_intro" % key, true)
	await _t("_test_scale")
	await _t("_test_kept")
	await _t("_test_no_double_scale")
	await _t("_test_settings_tap", [Vector2i(390, 844)])
	await _t("_test_career_settings_tap")
	await _t("_test_screens_at_largest")
	await _t("_test_one_place")
	await _t("_test_colour_has_words")
	await _t("_test_weakness_mark")
	await _t("_test_state_words")
	UK.apply_text_size("standard")
	print(Ran.line("Text size", self))
	for f in _failures:
		print("  FAIL: " + f)
	quit(0 if _failures.is_empty() else 1)


## Each size is its step; anything unknown reads as Standard.
func _test_scale() -> void:
	for row in UK.TEXT_SIZES:
		var key := str(row[0])
		UK.apply_text_size(key)
		var s := float(UK.TEXT_SCALE[key])
		_check(is_equal_approx(UK.text_scale, s), "%s: scale %.2f (got %.2f)" % [key, s, UK.text_scale])
		_check(UK.text_size() == key, "%s: UiKit reports it" % key)
		for fs in [UK.FINE, UK.BODY, UK.NAME, UK.H1, 44]:
			_check(UK.px(fs) == roundi(fs * s), "%s: %d px renders at %d" % [key, fs, UK.px(fs)])
			_check(UK.px(fs) >= fs, "%s: no size shrinks (%d)" % [key, fs])
	_check(is_equal_approx(UK.TEXT_SCALE["standard"], 1.0), "Standard leaves every size as it was")
	UK.apply_text_size("huge")
	_check(UK.text_size() == "standard" and is_equal_approx(UK.text_scale, 1.0), "an unknown size reads as Standard")
	UK.apply_text_size("standard")


## The choice is saved under ui/text_size and the next start reads it back.
func _test_kept() -> void:
	_check(_gs.text_size() == "standard", "a new settings file starts at Standard")
	_check(not _gs.set_text_size("huge"), "an unknown size is refused")
	_check(_gs.text_size() == "standard", "a refused size changes nothing")
	_check(_gs.set_text_size("larger"), "Standard to Larger is a change")
	_check(not _gs.set_text_size("larger"), "Larger again is no change (no rebuild)")
	_check(_gs.set_text_size("largest"), "Larger to Largest is a change")
	var cfg := ConfigFile.new()
	_check(cfg.load(_gs.settings_path) == OK, "the settings file is written")
	_check(str(cfg.get_value("ui", "text_size", "")) == "largest", "ui/text_size holds largest")
	# The next start: the static scale begins at Standard, as in a new process.
	UK.apply_text_size("standard")
	var gs_script: GDScript = load("res://scripts/state/GameState.gd")
	var next = gs_script.new()
	next.settings_path = _gs.settings_path
	next._ready()
	_check(UK.text_size() == "largest" and is_equal_approx(UK.text_scale, 1.3),
			"the next start opens at Largest (%s, %.2f)" % [UK.text_size(), UK.text_scale])
	next.free()
	# A file holding a size the game no longer knows opens at Standard.
	cfg.set_value("ui", "text_size", "giant")
	cfg.save(_gs.settings_path)
	_check(_gs.text_size() == "standard", "an unknown saved size reads as Standard")
	var odd = gs_script.new()
	odd.settings_path = _gs.settings_path
	odd._ready()
	_check(is_equal_approx(UK.text_scale, 1.0), "an unknown saved size starts at Standard")
	odd.free()
	_gs.set_text_size("standard")


func _fs(c: Object, key := "font_size") -> int:
	return int(c.call("get_theme_font_size", key))


## Every builder grows a size once: a size read back from a control that already
## has it (a button's words redrawn over it) is not grown again.
func _test_no_double_scale() -> void:
	UK.apply_text_size("largest")
	var made: Array = []
	var l: Control = UK.lbl("Kick", UK.BODY)
	_check(_fs(l) == UK.px(UK.BODY), "a label: %d, want %d" % [_fs(l), UK.px(UK.BODY)])
	var nl: Control = UK.name_label("Marcus Bontempelli")
	_check(_fs(nl) == UK.px(UK.NAME), "a name: %d, want %d" % [_fs(nl), UK.px(UK.NAME)])
	var h: Control = UK.heading("Settings", UK.H1)
	_check(_fs(h) == UK.px(mini(UK.H1, 30)), "a heading: %d, want %d" % [_fs(h), UK.px(mini(UK.H1, 30))])
	var b: Control = UK.btn("Play", 16)
	_check(_fs(b) == UK.px(16), "a button: %d, want %d" % [_fs(b), UK.px(16)])
	var r: Control = NI.rich(UK.BODY)
	for k in ["normal_font_size", "bold_font_size"]:
		_check(_fs(r, k) == UK.px(UK.BODY), "a name line's %s: %d, want %d" % [k, _fs(r, k), UK.px(UK.BODY)])
	var link: Control = NL.line("Kicked by Jack Smith", {}, UK.BODY, UK.TEXT)
	_check(_fs(link, "normal_font_size") == UK.px(UK.BODY), "a linked line: %d, want %d"
			% [_fs(link, "normal_font_size"), UK.px(UK.BODY)])
	# A button naming a player: his name drawn over it at the button's own size.
	var named: Control = UK.btn("Pick Jack Smith", 16)
	NI.dress_button(named, {"Jack Smith": "MEL"})
	var over := named.find_children("*", "RichTextLabel", true, false)
	_check(over.size() == 1, "a button naming a player carries his name in ink")
	if over.size() == 1:
		_check(_fs(over[0], "normal_font_size") == _fs(named) and _fs(named) == UK.px(16),
				"the inked name matches its button (%d and %d, want %d)" % [_fs(over[0], "normal_font_size"), _fs(named), UK.px(16)])
	# Already at size: passed through as it is.
	var kept := Label.new()
	UK.set_font_size(kept, 21, "font_size", true)
	_check(_fs(kept) == 21, "a size already grown is not grown again (%d)" % _fs(kept))
	# A button's drop-down menu is a window, not a control.
	var menu := PopupMenu.new()
	UK.set_font_size(menu, UK.BODY)
	_check(_fs(menu) == UK.px(UK.BODY), "a drop-down menu: %d, want %d" % [_fs(menu), UK.px(UK.BODY)])
	made.append_array([l, nl, h, b, r, link, named, kept, menu])
	# A name line fits its tap strip on the next frame (NameLink._fit_slop):
	# let that run before the controls go.
	await process_frame
	for n in made:
		n.free()
	UK.apply_text_size("standard")


func _named(from: Node, name: String) -> Control:
	return from.find_child(name, true, false) as Control


func _settings_title(sheet: Node) -> Label:
	for n in sheet.find_children("*", "Label", true, false):
		if (n as Label).text == "Settings":
			return n
	return null


## A real touch on the main menu's Settings, then on Largest: the setting is
## saved, the screen rebuilds at the new size, and Standard brings it back.
func _test_settings_tap(sz: Vector2i) -> void:
	var tag := "%dx%d" % [sz.x, sz.y]
	root.size = sz
	_gs.reset()
	_gs.set_text_size("standard")
	_router.stack = []
	_router.go("main")
	await _settle(8)
	for step in [["largest", 1.3], ["standard", 1.0]]:
		var key := str(step[0])
		var scene := current_scene
		var before := scene.get_instance_id()
		var why: String = await Tap.tap(_named(scene, "MenuSettings"))
		_check(why == "", "%s: a touch on Settings lands (%s)" % [tag, why])
		await _settle(8)
		var sheet := _named(scene, "Settings")
		_check(sheet != null, "%s: Settings opens" % tag)
		if sheet == null:
			return
		var choice := _named(sheet, "SettingsTextSize_" + key)
		_check(choice != null, "%s: Settings offers %s" % [tag, key])
		if choice == null:
			return
		why = await Tap.tap(choice)
		_check(why == "", "%s: a touch on %s lands (%s)" % [tag, key, why])
		await _settle(12)
		_check(str(_gs.get_setting("text_size", "")) == key, "%s: %s is saved" % [tag, key])
		_check(is_equal_approx(UK.text_scale, float(step[1])), "%s: the words are at %s (%.2f)" % [tag, key, UK.text_scale])
		_check(current_scene != null and current_scene.get_instance_id() != before,
				"%s: the screen rebuilds at %s" % [tag, key])
		_check(_router.current() == "main", "%s: still on the main menu" % tag)
		# Open it again: its own words are at the new size and it shows the choice.
		why = await Tap.tap(_named(current_scene, "MenuSettings"))
		_check(why == "", "%s: a touch on Settings lands again at %s (%s)" % [tag, key, why])
		await _settle(8)
		sheet = _named(current_scene, "Settings")
		_check(sheet != null, "%s: Settings opens again at %s" % [tag, key])
		if sheet == null:
			return
		var title := _settings_title(sheet)
		var want: int = UK.px(mini(UK.H1, 30))
		_check(title != null and _fs(title) == want, "%s: the sheet's title is %d px at %s (got %d)"
				% [tag, want, key, _fs(title) if title != null else -1])
		var shown := _named(sheet, "SettingsTextSize_" + key) as Button
		_check(shown != null and _fs(shown) == UK.px(14), "%s: the %s choice's words are %d px" % [tag, key, UK.px(14)])
		sheet.queue_free()
		await _settle(4)
	root.size = Vector2i(390, 844)


## A seeded career at Melbourne, every first-visit intro already seen.
func _career() -> void:
	_gs.reset()
	_gs.career_seed = SUITE_SEED
	_gs.replay_seed = SUITE_SEED
	_gs.start_season(CLUB, root.get_node("GameDB").club_list(CLUB))
	_gs.set_setting("seen_weekly_loop_intro", true)


## In a career: a real touch on the hub's Settings, then on Largest. The hub
## rebuilds at the new size on the same round of the same career, and
## Standard brings it back.
func _test_career_settings_tap() -> void:
	root.size = Vector2i(390, 844)
	_gs.set_text_size("standard")
	_career()
	_router.stack = []
	_router.go("hub")
	await _settle(10)
	var club: String = _gs.my_club
	var season_was: Object = _gs.season
	var round_was: int = _gs.season.round_index
	var list_was: int = _gs.my_list.size()
	for step in [["largest", 1.3], ["standard", 1.0]]:
		var key := str(step[0])
		var scene := current_scene
		var before := scene.get_instance_id()
		var why: String = await Tap.tap(_named(scene, "HubSettings"))
		_check(why == "", "hub: a touch on Settings lands (%s)" % why)
		await _settle(8)
		var sheet := _named(scene, "Settings")
		_check(sheet != null, "hub: Settings opens")
		if sheet == null:
			return
		var choice := _named(sheet, "SettingsTextSize_" + key)
		_check(choice != null, "hub: Settings offers %s" % key)
		if choice == null:
			return
		why = await Tap.tap(choice)
		_check(why == "", "hub: a touch on %s lands (%s)" % [key, why])
		await _settle(12)
		_check(str(_gs.get_setting("text_size", "")) == key, "hub: %s is saved" % key)
		_check(is_equal_approx(UK.text_scale, float(step[1])), "hub: the words are at %s (%.2f)" % [key, UK.text_scale])
		_check(current_scene != null and current_scene.get_instance_id() != before, "hub: the hub rebuilds at %s" % key)
		_check(_router.current() == "hub", "hub: still on the hub at %s (%s)" % [key, _router.current()])
		_check(_gs.my_club == club and _gs.season == season_was and _gs.season.round_index == round_was
				and _gs.my_list.size() == list_was,
				"hub: the career is as it was at %s (%s, round %d)" % [key, _gs.my_club, _gs.season.round_index])
		var again := _named(current_scene, "HubSettings") as Button
		_check(again != null and _fs(again) == UK.px(14), "hub: its Settings button's words are %d px at %s (got %d)"
				% [UK.px(14), key, _fs(again) if again != null else -1])


## The words on `scene` that carry no size of their own, and drop-down lists
## not at the game's name size: with no project theme, a bare control stays at
## the engine's 16 px whatever the setting.
func _unsized(scene: Node) -> Array:
	var out: Array = []
	for n in scene.find_children("*", "Control", true, false):
		var c := n as Control
		if not c.is_visible_in_tree():
			continue
		var key := "font_size"
		var words := ""
		if c is RichTextLabel:
			key = "normal_font_size"
			words = (c as RichTextLabel).get_parsed_text()
		elif c is Label:
			words = (c as Label).text
		elif c is Button:
			words = (c as Button).text
		elif c is LineEdit:
			words = (c as LineEdit).text + (c as LineEdit).placeholder_text
		if words.strip_edges() != "" and not c.has_theme_font_size_override(key):
			out.append("%s %s \"%s\"" % [c.get_class(), c.name, words.strip_edges().left(24)])
		var pop: PopupMenu = null
		if c is OptionButton:
			pop = (c as OptionButton).get_popup()
		elif c is MenuButton:
			pop = (c as MenuButton).get_popup()
		if pop != null and pop.get_theme_font_size("font_size") != UK.px(UK.NAME):
			out.append("%s's list at %d px" % [c.name, pop.get_theme_font_size("font_size")])
	return out


## Every career screen at Largest, a round played: each word carries its own
## size, so the setting reaches it, and every drop-down's list (the stats
## filters, the almanac's club picker) is at the name size.
func _test_screens_at_largest() -> void:
	root.size = Vector2i(390, 844)
	_career()
	var guard := 0
	while _gs.season.round_index < 1 and guard < 4:
		guard += 1
		_gs.advance()
	_check(_gs.season.round_index >= 1, "a round is played (%d)" % _gs.season.round_index)
	_gs.set_text_size("largest")
	var stats_script: GDScript = load("res://scripts/ui/StatsHubScene.gd")
	var stats_was := str(stats_script.get("current"))
	var seen := {}
	for key in ["hub", "selection", "training", "list", "coaching", "staff", "almanac", "stats:ladder", "stats:players"]:
		var screen := str(key).get_slice(":", 0)
		if str(key).contains(":"):
			stats_script.set("current", str(key).get_slice(":", 1))
		_router.stack = []
		_router.go(screen)
		await _settle(10)
		var scene := current_scene
		_check(scene != null and _router.current() == screen, "%s opens at Largest" % key)
		if scene == null:
			continue
		var bare := _unsized(scene)
		_check(bare.is_empty(), "%s at Largest: words with no size of their own: %s" % [key, "; ".join(bare.slice(0, 12))])
		seen.merge(_seen(scene))
		# The players' filters and the stat list are sheets over the list: a
		# real touch opens each.
		if key == "stats:players":
			for opener in ["FiltersToggle", "StatPick"]:
				_router.stack = []
				_router.go(screen)
				await _settle(10)
				var why: String = await Tap.tap(_named(current_scene, opener))
				_check(why == "", "stats: a touch on %s lands (%s)" % [opener, why])
				await _settle(8)
				var in_sheet := _unsized(current_scene)
				_check(in_sheet.is_empty(), "stats %s at Largest: words with no size of their own: %s"
						% [opener, "; ".join(in_sheet.slice(0, 12))])
				seen.merge(_seen(current_scene))
	stats_script.set("current", stats_was)
	for nm in ["ClubRecordsPick", "Filter_club", "Filter_trait", "StatSheet"]:
		_check(seen.has(nm), "the walk reaches %s" % nm)
	_gs.set_text_size("standard")
	_router.stack = []


func _seen(scene: Node) -> Dictionary:
	var out := {}
	for nm in ["ClubRecordsPick", "Filter_club", "Filter_trait", "StatSheet"]:
		if scene.find_child(nm, true, false) != null:
			out[nm] = true
	return out


func _gd_files(dir: String) -> Array[String]:
	var out: Array[String] = []
	var d := DirAccess.open(dir)
	if d == null:
		return out
	d.list_dir_begin()
	var f := d.get_next()
	while f != "":
		if d.current_is_dir():
			if not f.begins_with("."):
				out.append_array(_gd_files(dir + "/" + f))
		elif f.ends_with(".gd"):
			out.append(dir + "/" + f)
		f = d.get_next()
	return out


## Only UiKit sets a font size on a control; everything else asks it, so the
## text size reaches every word.
func _test_one_place() -> void:
	var files := _gd_files("res://scripts")
	_check(files.size() > 50, "the scripts are read (%d)" % files.size())
	var outside: Array = []
	for path in files:
		if path.ends_with("/ui/UiKit.gd"):
			continue
		var text := FileAccess.get_file_as_string(path)
		if text.contains("add_theme_font_size_override"):
			outside.append(path)
	_check(outside.is_empty(), "a font size set outside UiKit: %s" % ", ".join(outside))


## Where only GOOD/BAD (or win/loss) colour would carry a state, a word, mark or
## number says it too (P-10). Each such line in the screens names its second
## cue here: [part of the line, the cue that says the same thing, how many
## lines it is on]. The count pins each part to its lines, so a new line that
## happens to contain one still has to be read and counted.
const COLOUR_CUES := {
	"CaptaincySheet.gd": [["UiKit.BAD if off_bad", "the reason he can't lead, in words", 1]],
	"ClubPage.gd": [["UiKit.GOOD if us > them", "Won / Lost / Drew", 1]],
	"CoachingScene.gd": [
		["part[1] == \"hot\"", "the heading: In good form / In poor form", 1],
		["state in [\"Very secure\", \"Secure\"]", "the job security word", 1],
		["UiKit.TEXT if state == \"Stable\"", "the job security word", 1]],
	"DraftScene.gd": [
		["Traits.is_bad(str(t))", "the weakness mark", 1],
		["\"On your list\"", "On your list, pick N", 1],
		["int(st[\"short\"]) > 0", "the need word (short of ...)", 1],
		["_draft.is_valid()", "the status line in words", 1]],
	"DraftSpotsSheet.gd": [["str(line[2]) == \"bad\"", "the line says who will pass", 1]],
	"DraftTradeSheet.gd": [["bool(verdict[\"ok\"])", "the club's reason in words", 1]],
	"HubScene.gd": [
		["\"You have retired\" if retired", "You have retired / You have been sacked", 1],
		["\"own_injury\"", "the note names the injury", 1],
		["UiKit.GOOD if done", "Done / To do", 1],
		["ch == \"W\"", "the W / L / D letters", 1],
		["return UiKit.GOOD", "the form line's words", 1],
		["return UiKit.BAD", "the form line's words", 1],
		["margin_colour(won)", "Won by / Lost by / Drew", 2]],
	"ListScene.gd": [
		["concussion_text(p), UiKit.BAD", "the concussion in words", 1],
		["\"Out %s\"", "Out N weeks", 1],
		["\"Unhappy\"", "Unhappy", 1]],
	"MatchScene.gd": [
		["pts > 0", "the signed +/- points", 1],
		["bool(f[2])", "the legs word", 1],
		["tone == \"good\"", "the goal row names the club", 1],
		["margin_colour(winner == me)", "Won by / Lost by", 1]],
	"OffseasonScene.gd": [
		["room >= 0 else UiKit.BAD", "cap room / over the cap by", 1],
		["talk[\"stays\"]", "his reason in words", 1],
		["terms[\"refuse\"]", "his reason in words", 1],
		["room_after >= 0 else UiKit.BAD", "none, over the cap", 1],
		["verdict[\"ok\"]", "the club's reason in words", 1]],
	"OptionsSheet.gd": [["UiKit.BAD if bad", "the status line in words", 1]],
	"PlayerSheet.gd": [
		["weeks > 0", "Out for N weeks", 1],
		["Traits.is_bad(str(t))", "the weakness mark", 1],
		["return UiKit.GOOD", "the rating's number", 1],
		["return UiKit.BAD", "the rating's number", 1]],
	"SeasonReviewScene.gd": [
		["mine_won", "the result in words", 1],
		["\"met\"", "met / missed", 1],
		["col = UiKit.GOOD", "the W / L letters", 1],
		["col = UiKit.BAD", "the W / L letters", 1]],
	"TeamBuilder.gd": [
		["start_note != \"\"", "the note in words", 1],
		["Workload.NEEDS_BREAK", "the workload word", 1],
		["Ratings.available(p)", "why he is out, in words", 1]],
	"TrainingScene.gd": [
		["rise.size() > 0", "the rise mark and its words", 2],
		["Traits.is_bad(trait_keys[0])", "the weakness mark", 1],
		["\"Injured %d wk%s\"", "Injured N wks", 1],
		["useful else UiKit.BAD", "Does little for a ...", 1],
		["return UiKit.GOOD", "the rating's number", 1],
		["return UiKit.BAD", "the rating's number", 1]],
	"TraitLink.gd": [["Traits.is_bad(key)", "the sheet says Weakness", 1]],
	"UiKit.gd": [
		["BAD if danger", "the button's words", 1],
		["BAD if Traits.is_bad(t)", "the weakness mark", 1],
		["func margin_colour(", "callers write Won by / Lost by", 1],
		["GOOD if win else BAD", "callers write Won by / Lost by", 1]],
	"WeekPreview.gd": [
		["UiKit.BAD if bad", "the note in words", 2],
		["lit[Traits.label", "Your side has: ...", 1]],
}
## A colour chosen by a state: "GOOD if", "else BAD", "return GOOD", "= BAD", a
## margin colour, or handed back beside its words as [text, GOOD].
const COLOUR_ONLY := "\\b(GOOD|BAD)\\s+if\\b|\\belse\\s+(UiKit\\.)?(GOOD|BAD)\\b|margin_colour\\(|return\\s+(UiKit\\.)?(GOOD|BAD)\\b|=\\s*(UiKit\\.)?(GOOD|BAD)\\s*$|\\b(GOOD|BAD)\\s*\\]"


func _test_colour_has_words() -> void:
	var rx := RegEx.new()
	_check(rx.compile(COLOUR_ONLY) == OK, "the colour check compiles")
	var counted := {}
	var found := 0
	var bare: Array = []
	for path in _gd_files("res://scripts/ui"):
		var file := path.get_file()
		var lines := FileAccess.get_file_as_string(path).split("\n")
		for i in range(lines.size()):
			var line := str(lines[i])
			if line.strip_edges().begins_with("#") or rx.search(line) == null:
				continue
			found += 1
			var named := false
			for cue in COLOUR_CUES.get(file, []):
				if line.contains(str(cue[0])):
					var at := "%s|%s" % [file, cue[0]]
					counted[at] = int(counted.get(at, 0)) + 1
					named = true
					break
			if not named:
				bare.append("%s:%d %s" % [file, i + 1, line.strip_edges()])
	_check(found > 30, "the screens' state colours are read (%d)" % found)
	_check(bare.is_empty(), "a state shown by colour alone (add its word or mark, then list it): %s" % "; ".join(bare))
	var off: Array = []
	for file in COLOUR_CUES:
		for cue in COLOUR_CUES[file]:
			var n := int(counted.get("%s|%s" % [file, cue[0]], 0))
			if n != int(cue[2]):
				off.append("%s: %s on %d lines, listed for %d" % [file, cue[0], n, int(cue[2])])
	_check(off.is_empty(), "a listed colour on a different number of lines (read each, then fix its count or drop it): %s"
			% "; ".join(off))


## The words that now carry a state beside its colour: the goal row names the
## club, and money past the cap says so.
func _test_state_words() -> void:
	var short := str(root.get_node("GameDB").club_short("MEL"))
	_check(MN.goal_head("Petracca", "MEL") == "Goal  Petracca (%s)" % short,
			"a goal row names the club: %s" % MN.goal_head("Petracca", "MEL"))
	_check(MN.goal_head("", "MEL") == "Goal  " + short, "a goal with no kicker names the club: %s" % MN.goal_head("", "MEL"))
	var ev := {"kind": "goal", "side": 1, "name": "Petracca", "score": [6, 6]}
	var fl: Dictionary = MN.feed_line(ev, "SYD", "MEL")
	_check(str(fl.get("text", "")) == MN.goal_head("Petracca", "MEL") and str(fl.get("tier", "")) == "goal",
			"the feed's goal row names the club: %s" % str(fl))
	_check(OFF.cap_room_words(120000) == "cap room " + CT.money(120000), "cap room: %s" % OFF.cap_room_words(120000))
	_check(OFF.cap_room_words(-120000) == "over the cap by " + CT.money(120000),
			"over the cap says so: %s" % OFF.cap_room_words(-120000))
	_check(OFF.room_after_words(80000) == CT.money(80000), "room left: %s" % OFF.room_after_words(80000))
	_check(OFF.room_after_words(-80000) == "none, %s over the cap" % CT.money(80000),
			"an offer past the cap says so: %s" % OFF.room_after_words(-80000))


## A weakness reads as one without its colour: "- Hothead", and its sheet says
## Weakness; a trait carries no mark.
func _test_weakness_mark() -> void:
	var bad := ""
	var good := ""
	for key in TR.DEFS:
		if TR.is_bad(str(key)) and bad == "":
			bad = str(key)
		elif not TR.is_bad(str(key)) and good == "":
			good = str(key)
	_check(bad != "" and good != "", "there is a weakness and a trait to show")
	_check(UK.trait_label(bad) == UK.WEAKNESS_MARK + TR.label(bad), "a weakness carries its mark: %s" % UK.trait_label(bad))
	_check(UK.trait_label(good) == TR.label(good), "a trait carries none: %s" % UK.trait_label(good))
	_check(TL.sheet_lines(bad).has("Weakness"), "a weakness's sheet says Weakness")
	_check(not TL.sheet_lines(good).has("Weakness"), "a trait's sheet does not")
	for ch in [UK.WEAKNESS_MARK.strip_edges(), "▲"]:
		_check(UK.FONT.has_char(ch.unicode_at(0)), "the game's face draws %s" % ch)
	# On his profile (and the draft's detail, built the same way) the trait line
	# starts with the mark too: "- Hothead. ..."
	if _gs.season == null:
		_career()
	var who: Dictionary = {}
	var his_bad := ""
	for code in _gs.season.lists:
		for p in _gs.season.lists[code]:
			for t in TR.of(p):
				if TR.is_bad(str(t)):
					who = p
					his_bad = str(t)
					break
			if his_bad != "":
				break
		if his_bad != "":
			break
	_check(his_bad != "", "a league player carries a weakness")
	if his_bad != "":
		var host := Control.new()
		host.size = Vector2(390, 844)
		root.add_child(host)
		PS.open(host, who)
		await process_frame
		var line := host.find_child("Trait_" + his_bad, true, false) as Label
		_check(line != null and line.text.begins_with(UK.WEAKNESS_MARK + TR.label(his_bad)),
				"his profile marks the weakness: %s" % (line.text if line != null else "none"))
		for t in TR.of(who):
			if not TR.is_bad(str(t)):
				var tl := host.find_child("Trait_" + str(t), true, false) as Label
				_check(tl != null and not tl.text.begins_with(UK.WEAKNESS_MARK), "his trait carries no mark")
		host.queue_free()
		await process_frame
	var draft := FileAccess.get_file_as_string("res://scripts/ui/DraftScene.gd")
	_check(draft.contains("UiKit.trait_label(str(t)), Traits.scout(str(t))"), "the draft's trait line marks a weakness too")
