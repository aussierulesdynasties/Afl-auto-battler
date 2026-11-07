extends SceneTree
## godot --headless --path . --script tests/run_text_size_tests.gd
## Text size (row 118, T3.R10): Standard, Larger or Largest from Settings grows
## the game's words through UiKit.px in one place, is kept in the settings file
## and read back on the next start, and never grows a size twice. No state
## shown by colour alone (P-10): every GOOD/BAD (or win/loss) colour choice in
## the screens is listed here with the word, mark or number that says the same
## thing, so a new one has to name its second cue.

const Tap := preload("res://tests/tap.gd")
const Ran := preload("res://tests/functions_ran.gd")

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
	await _t("_test_one_place")
	await _t("_test_colour_has_words")
	await _t("_test_weakness_mark")
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
## cue here: [part of the line, the cue that says the same thing].
const COLOUR_CUES := {
	"CaptaincySheet.gd": [["UiKit.BAD if off_bad", "the reason he can't lead, in words"]],
	"ClubPage.gd": [["UiKit.GOOD if us > them", "Won / Lost / Drew"]],
	"CoachingScene.gd": [
		["part[1] == \"hot\"", "the heading: In good form / In poor form"],
		["state in [\"Very secure\", \"Secure\"]", "the job security word"],
		["UiKit.TEXT if state == \"Stable\"", "the job security word"]],
	"DraftScene.gd": [
		["Traits.is_bad(str(t))", "the trait's scouting words"],
		["int(st[\"short\"]) > 0", "the need word (short of ...)"],
		["_draft.is_valid()", "the status line in words"]],
	"DraftSpotsSheet.gd": [["str(line[2]) == \"bad\"", "the line says who will pass"]],
	"DraftTradeSheet.gd": [["bool(verdict[\"ok\"])", "the club's reason in words"]],
	"HubScene.gd": [
		["\"You have retired\" if retired", "You have retired / You have been sacked"],
		["\"own_injury\"", "the note names the injury"],
		["UiKit.GOOD if done", "Done / To do"],
		["ch == \"W\"", "the W / L / D letters"],
		["return UiKit.GOOD", "the form line's words"],
		["return UiKit.BAD", "the form line's words"],
		["margin_colour(won)", "Won by / Lost by / Drew"]],
	"ListScene.gd": [["p.get(\"rehab\"", "the REHAB word"]],
	"MatchScene.gd": [
		["pts > 0", "the signed +/- points"],
		["bool(f[2])", "the legs word"],
		["tone == \"good\"", "the goal row names the club"],
		["margin_colour(winner == me)", "Won by / Lost by"]],
	"OffseasonScene.gd": [
		["room >= 0 else UiKit.BAD", "cap room / over the cap by"],
		["talk[\"stays\"]", "his reason in words"],
		["terms[\"refuse\"]", "his reason in words"],
		["room_after >= 0 else UiKit.BAD", "none, over the cap"],
		["verdict[\"ok\"]", "the club's reason in words"]],
	"OptionsSheet.gd": [["UiKit.BAD if bad", "the status line in words"]],
	"PlayerSheet.gd": [
		["weeks > 0", "Out for N weeks"],
		["Traits.is_bad(str(t))", "the trait's scouting words"],
		["return UiKit.GOOD", "the rating's number"],
		["return UiKit.BAD", "the rating's number"]],
	"SeasonReviewScene.gd": [
		["mine_won", "the result in words"],
		["\"met\"", "met / missed"],
		["col = UiKit.GOOD", "the W / L letters"],
		["col = UiKit.BAD", "the W / L letters"]],
	"TeamBuilder.gd": [
		["start_note != \"\"", "the note in words"],
		["Workload.NEEDS_BREAK", "the workload word"],
		["Ratings.available(p)", "why he is out, in words"]],
	"TrainingScene.gd": [
		["rise.size() > 0", "the rise mark and its words"],
		["Traits.is_bad(trait_keys[0])", "the weakness mark"],
		["useful else UiKit.BAD", "Does little for a ..."],
		["return UiKit.GOOD", "the rating's number"],
		["return UiKit.BAD", "the rating's number"]],
	"TraitLink.gd": [["Traits.is_bad(key)", "the sheet says Weakness"]],
	"UiKit.gd": [
		["BAD if danger", "the button's words"],
		["BAD if Traits.is_bad(t)", "the weakness mark"],
		["func margin_colour(", "callers write Won by / Lost by"],
		["GOOD if win else BAD", "callers write Won by / Lost by"]],
	"WeekPreview.gd": [
		["UiKit.BAD if bad", "the note in words"],
		["lit[Traits.label", "Your side has: ..."]],
}
const COLOUR_ONLY := "\\b(GOOD|BAD)\\s+if\\b|\\belse\\s+(UiKit\\.)?(GOOD|BAD)\\b|margin_colour\\(|return\\s+(UiKit\\.)?(GOOD|BAD)\\b|=\\s*(UiKit\\.)?(GOOD|BAD)\\s*$"


func _test_colour_has_words() -> void:
	var rx := RegEx.new()
	_check(rx.compile(COLOUR_ONLY) == OK, "the colour check compiles")
	var used := {}
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
					used["%s|%s" % [file, cue[0]]] = true
					named = true
					break
			if not named:
				bare.append("%s:%d %s" % [file, i + 1, line.strip_edges()])
	_check(found > 30, "the screens' state colours are read (%d)" % found)
	_check(bare.is_empty(), "a state shown by colour alone (add its word or mark, then list it): %s" % "; ".join(bare))
	var stale: Array = []
	for file in COLOUR_CUES:
		for cue in COLOUR_CUES[file]:
			if not used.has("%s|%s" % [file, cue[0]]):
				stale.append("%s: %s" % [file, cue[0]])
	_check(stale.is_empty(), "a listed colour no longer in the code (drop it): %s" % "; ".join(stale))


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
