extends SceneTree
## godot --headless --path . --script tests/run_contrast_tests.gd
## Row V4: the elevation scale and the automatic contrast test (ruling V-R2:
## "The primary button may be filled with club colour. A red club may clash
## with BAD, so a contrast and collision check is required.").
##
## - BG, PANEL, PANEL_ALT, INK and SURFACE are one ordered scale (UiKit.elevation).
## - Every club that ships, every colour a Club Forge club can take, and no
##   club at all: the primary button's fill reads against its label (TEXT_FLOOR),
##   stands off the page and the panel (FILL_FLOOR), and is not BAD's colour
##   (BAD_CLASH).
## - Every text token, and every club's ink, reads at TEXT_FLOOR on every step
##   of the scale.
##
## The floors: docs/VISUAL_STYLE_GUIDE.md names 4.5:1 for text against its
## panel (the screen lint rule). It names no floor for a fill, so a fill takes
## WCAG's 3:1 for a control's shape against what is beside it.

const TEXT_FLOOR := 4.5
const FILL_FLOOR := 3.0
## A fill this close to BAD (CIE76, in Lab) could be read as BAD: UiKit.INK_CLASH,
## the gap under which two club inks side by side look alike.
const BAD_CLASH := 25.0
## A float's rounding, so a hand-picked ink sitting exactly on the floor passes.
const EPS := 0.005

var UK
var CF
var _state: Node
var _db: Node
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


func _run() -> void:
	await process_frame
	UK = load("res://scripts/ui/UiKit.gd")
	CF = load("res://scripts/sim/ClubForge.gd")
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	_state.autosave_enabled = false
	_state.save_path = "user://test_contrast.save"
	_state.settings_path = "user://test_contrast.cfg"
	UK.apply_appearance("dark")
	_forge_clubs()
	_t("_test_scale_is_ordered")
	_t("_test_text_tokens_on_every_step")
	_t("_test_primary_fill_every_club")
	_t("_test_club_ink_on_every_step")
	_db.unregister_custom_clubs()
	print(Ran.line("Contrast", self))
	quit(0 if _failures.is_empty() else 1)


## One Club Forge club for each colour the Forge offers (ClubForge.PALETTE) as
## its main colour, with white and black beside it: every fill and ink a
## created club can end up with. Codes ZA, ZB, ...
var _forge: Array[String] = []
func _forge_clubs() -> void:
	var i := 0
	for c in CF.PALETTE:
		var code := "Z" + char(65 + i)
		i += 1
		var id := str(c[0])
		var spec := {"name": "Forge " + str(c[1]), "short": str(c[1]), "code": code,
				"location": "", "primary": str(c[2]),
				"secondary": "#111111" if id == "white" else "#F5F5F5",
				"accent": "#F5F5F5" if id == "black" else "#111111", "design": "plain"}
		_db.register_club(CF.row(spec))
		_forge.append(code)


func _hex(c: Color) -> String:
	return "#" + c.to_html(false)


func _clubs() -> Array:
	var out := []
	for code in _db.club_order:
		out.append(str(code))
	return out


func _test_scale_is_ordered() -> void:
	var steps: Array = UK.elevation()
	var names: Array = UK.ELEVATION
	_check(names == ["INK", "BG", "PANEL", "PANEL_ALT", "SURFACE"] and steps.size() == names.size(),
			"The scale is INK, BG, PANEL, PANEL_ALT, SURFACE (%s)" % str(names))
	for i in names.size():
		_check((steps[i] as Color).is_equal_approx(UK.get(names[i])),
				"Step %d of the scale is %s" % [i, names[i]])
	for i in range(1, steps.size()):
		var under: float = UK._relative_luminance(steps[i - 1])
		var over: float = UK._relative_luminance(steps[i])
		_check(over > under, "%s (%s) is lighter than %s (%s), the step under it" % [
				names[i], _hex(steps[i]), names[i - 1], _hex(steps[i - 1])])
		# A step you cannot see is not a step: each lifts by at least 1 part in 40.
		_check(UK.contrast(steps[i], steps[i - 1]) >= 1.025,
				"%s shows against %s (%.3f:1)" % [names[i], names[i - 1], UK.contrast(steps[i], steps[i - 1])])


## TEXT, MUTED, EMPH, GOOD and BAD are read as words. FAINT is a disabled
## control's ink only (guide 2.1), LINE and OUTLINE are rules, ACCENT is a fill:
## none of them is text, so none is held to the text floor.
func _test_text_tokens_on_every_step() -> void:
	var steps: Array = UK.elevation()
	for token in ["TEXT", "MUTED", "EMPH", "GOOD", "BAD"]:
		var ink: Color = UK.get(token)
		for i in steps.size():
			var r: float = UK.contrast(ink, steps[i])
			_check(r >= TEXT_FLOOR - EPS, "%s (%s) reads on %s (%s): %.2f:1, floor %.1f" % [
					token, _hex(ink), UK.ELEVATION[i], _hex(steps[i]), r, TEXT_FLOOR])


func _test_primary_fill_every_club() -> void:
	var was: String = _state.my_club
	var lines := []
	var who := _clubs()
	who.append("")  # no club yet: the main menu and Settings (ACCENT)
	_check(who.size() >= 18 + _forge.size() + 1, "Every club is walked (%d)" % who.size())
	for code in who:
		_state.my_club = code
		var fill: Color = UK.team_button()
		var label: Color = UK.primary_label(fill)
		var tag: String = code if code != "" else "no club"
		var on_label: float = UK.contrast(label, fill)
		var on_page: float = UK.contrast(fill, UK.BG)
		var on_panel: float = UK.contrast(fill, UK.PANEL)
		var from_bad: float = UK.colour_distance(fill, UK.BAD)
		lines.append("%s %s label %.1f page %.1f panel %.1f BAD %.0f" % [
				tag, _hex(fill), on_label, on_page, on_panel, from_bad])
		_check(on_label >= TEXT_FLOOR - EPS, "%s: the primary button's label (%s) reads on its fill (%s): %.2f:1, floor %.1f" % [
				tag, _hex(label), _hex(fill), on_label, TEXT_FLOOR])
		_check(on_page >= FILL_FLOOR - EPS, "%s: the primary fill (%s) stands off the page: %.2f:1, floor %.1f" % [
				tag, _hex(fill), on_page, FILL_FLOOR])
		_check(on_panel >= FILL_FLOOR - EPS, "%s: the primary fill (%s) stands off a panel: %.2f:1, floor %.1f" % [
				tag, _hex(fill), on_panel, FILL_FLOOR])
		_check(from_bad >= BAD_CLASH, "%s: the primary fill (%s) is clear of BAD (%s): %.1f apart, at least %.0f" % [
				tag, _hex(fill), _hex(UK.BAD), from_bad, BAD_CLASH])
		# The button as built wears exactly this fill and label.
		var b: Button = UK.btn("Play", UK.NAME, true)
		var sb := b.get_theme_stylebox("normal") as StyleBoxFlat
		_check(sb != null and sb.bg_color.is_equal_approx(fill)
				and b.get_theme_color("font_color").is_equal_approx(label),
				"%s: a primary button is built with the fill and label checked here" % tag)
		b.free()
		# Pre-season fills its primary with the club's ink (PreSeasonScene._primary).
		if code != "":
			var pre: Color = UK.primary_fill(UK.club_ink(code))
			var pre_label: Color = UK.primary_label(pre)
			_check(UK.contrast(pre_label, pre) >= TEXT_FLOOR - EPS
					and UK.min_contrast(pre, [UK.BG, UK.PANEL]) >= FILL_FLOOR - EPS,
					"%s: the pre-season primary (%s) reads under its label (%.2f:1) and off the page (%.2f:1)" % [
					tag, _hex(pre), UK.contrast(pre_label, pre), UK.min_contrast(pre, [UK.BG, UK.PANEL])])
			_check(UK.colour_distance(pre, UK.BAD) >= BAD_CLASH,
					"%s: the pre-season primary (%s) is clear of BAD: %.1f apart, at least %.0f" % [
					tag, _hex(pre), UK.colour_distance(pre, UK.BAD), BAD_CLASH])
			lines.append("%s pre-season %s was %s" % [tag, _hex(pre), _hex(UK.club_ink(code))])
	_state.my_club = was
	print("Primary fills: " + "; ".join(lines))


## A club's two inks (its name, a heading, a figure that is the club's) on
## every step of the scale, as each screen asks for them: club_ink(code, step).
func _test_club_ink_on_every_step() -> void:
	var steps: Array = UK.elevation()
	for code in _clubs():
		for i in steps.size():
			for which in 2:
				var ink: Color = UK.club_ink(code, steps[i]) if which == 0 else UK.club_ink_second(code, steps[i])
				var r: float = UK.contrast(ink, steps[i])
				_check(r >= TEXT_FLOOR - EPS, "%s: its %s ink (%s) reads on %s: %.2f:1, floor %.1f" % [
						code, "first" if which == 0 else "second", _hex(ink), UK.ELEVATION[i], r, TEXT_FLOOR])
	# The ink a screen takes without naming a surface sits on the page or a panel.
	for code in _clubs():
		var ink: Color = UK.club_ink(code)
		for sf in [UK.BG, UK.PANEL]:
			var r: float = UK.contrast(ink, sf)
			_check(r >= TEXT_FLOOR - EPS, "%s: its ink with no surface named (%s) reads on %s: %.2f:1" % [
					code, _hex(ink), _hex(sf), r])
