extends SceneTree
## P-77 "One sweep of every screen" (proposals pass 2, director yes 2026-10-18).
## Opens every screen in Router.SCENES on one seeded career in the dark theme
## and measures it. Per screen it records:
##   min_font     the smallest rendered font size in px (font size in UI units
##                times the window's pixels per unit), with the node that has it
##   offscreen    visible Controls whose rect leaves the viewport (sideways
##                always; up or down only outside a ScrollContainer)
##   clipped      labels and buttons whose text is cut, ellipsised or has lines
##                the box does not show
##   small        buttons and tappable rows under 44 px in either direction
##   inline       player names in running text that open his profile (NameLink);
##                reported, never gated, and not counted in `small`
##   overlap      pairs of words drawn on top of each other: two pieces of text
##                (labels, buttons, rich text) whose inked areas cross, neither
##                inside the other (row 118)
## Measurement only: it never changes a screen, and it never touches a real
## save. The pass/fail against the committed baseline is tools/screen_sweep.py.
##
##   godot --path . --rendering-method gl_compatibility --script tools/visual/sweep_screens.gd -- --size 390x844 --out out/sweep_phone.json
## Needs a real renderer (a virtual display on CI): fonts and layout are the
## ones a player sees. Run it once per size; 390x844 is the Android phone
## reference, 1920x1080 the wide desktop.
##   --text-size standard|larger|largest  the Settings text size (row 118);
##                                        standard when left out
##   --png DIR                            also saves each screen as DIR/<key>.png
##                                        (a windowed run: headless has no image)

const MIN_TARGET := 44.0
const TOL := 1.0
const EXAMPLES := 8
const SEED := 2031
const CLUB := "MEL"

var W := 390
var H := 844
var _factor := 1.0     # window pixels per UI unit
var _vr := Rect2()     # the visible rect, in UI units
var _results := {}
var _state
var _db
var _png := ""
const OVERLAP_MIN := 2.0   # UI units both ways before two texts count as crossing


func _initialize() -> void:
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


# --- measuring -------------------------------------------------------------

func _label_of(c: Node) -> String:
	var t := ""
	if c.get("text") != null:
		t = str(c.get("text")).replace("\n", " ").left(28)
	return "%s \"%s\"" % [c.name, t]


func _path(c: Node, scene: Node) -> String:
	var parts := []
	var n: Node = c
	while n != null and n != scene and parts.size() < 3:
		parts.push_front(str(n.name))
		n = n.get_parent()
	return "/".join(parts)


func _font_px(c: Control) -> float:
	var fs := 0
	if c is RichTextLabel:
		fs = c.get_theme_font_size("normal_font_size")
	elif c is Label and (c as Label).label_settings != null:
		fs = (c as Label).label_settings.font_size
	else:
		fs = c.get_theme_font_size("font_size")
	var sc: Vector2 = c.get_global_transform().get_scale()
	return float(fs) * absf(sc.y) * _factor


func _has_text(c: Control) -> bool:
	if c is RichTextLabel:
		return (c as RichTextLabel).get_parsed_text().strip_edges() != ""
	if c is Label:
		return (c as Label).text.strip_edges() != ""
	if c is Button:
		return (c as Button).text.strip_edges() != ""
	if c is LineEdit:
		return (c as LineEdit).text != "" or (c as LineEdit).placeholder_text != ""
	return false


## Text the box cannot show: trimmed with an ellipsis or clipped, or lines
## below the box. A line that wraps and fits is fine.
func _clipped(c: Control) -> bool:
	if c.size.x <= 1.0:
		return false
	if c is Label:
		var l := c as Label
		if l.text.strip_edges() == "":
			return false
		if l.autowrap_mode != TextServer.AUTOWRAP_OFF:
			return l.get_line_count() > l.get_visible_line_count()
		var trims: bool = l.clip_text or l.text_overrun_behavior != TextServer.OVERRUN_NO_TRIMMING
		if not trims:
			return false
		var font: Font = l.get_theme_font("font")
		var fs := l.label_settings.font_size if l.label_settings != null else l.get_theme_font_size("font_size")
		if l.label_settings != null and l.label_settings.font != null:
			font = l.label_settings.font
		var wide := font.get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		return wide > l.size.x + 0.5
	if c is Button:
		var b := c as Button
		if b.text.strip_edges() == "" or b.autowrap_mode != TextServer.AUTOWRAP_OFF:
			return false
		var trims_b: bool = b.clip_text or b.text_overrun_behavior != TextServer.OVERRUN_NO_TRIMMING
		if not trims_b:
			return false
		var sb := b.get_theme_stylebox("normal")
		var room := b.size.x - sb.get_margin(SIDE_LEFT) - sb.get_margin(SIDE_RIGHT)
		if b.icon != null:
			room -= float(b.icon.get_width()) + 4.0
		var wide_b := b.get_theme_font("font").get_string_size(b.text, HORIZONTAL_ALIGNMENT_LEFT, -1, b.get_theme_font_size("font_size")).x
		return wide_b > room + 0.5
	return false


## A player's name inside a running line (NameLink.wire): it opens his profile on
## a tap but is text at line height, like a web link, so it is counted in its own
## column ("inline name links"), which is reported and never compared to the floor.
func _inline_link(c: Control) -> bool:
	return c.has_meta("name_link_wired") or c.has_meta("name_link_hit")


func _tappable(c: Control) -> bool:
	if c.mouse_filter == Control.MOUSE_FILTER_IGNORE:
		return false
	if _inline_link(c):
		return false
	if c is BaseButton:
		return not (c as BaseButton).disabled
	if c is ScrollContainer or c is ScrollBar:
		return false
	return c.gui_input.get_connections().size() > 0


## Where a piece of text actually puts ink: a label's lines inside its box
## (by its alignment), rich text's content, a button's box. In UI units.
func _ink_rect(c: Control) -> Rect2:
	var gr := c.get_global_rect()
	var sc: Vector2 = c.get_global_transform().get_scale()
	if c is Label:
		var l := c as Label
		var font: Font = l.get_theme_font("font")
		var fs := l.get_theme_font_size("font_size")
		var gap := float(l.get_theme_constant("line_spacing"))
		if l.label_settings != null:
			fs = l.label_settings.font_size
			gap = l.label_settings.line_spacing
			if l.label_settings.font != null:
				font = l.label_settings.font
		var lines := maxi(1, mini(l.get_line_count(), l.get_visible_line_count()))
		var th := (font.get_height(fs) * lines + gap * (lines - 1)) * absf(sc.y)
		var tw := gr.size.x
		if l.autowrap_mode == TextServer.AUTOWRAP_OFF:
			tw = minf(gr.size.x, font.get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x * absf(sc.x))
		var x := gr.position.x
		match l.horizontal_alignment:
			HORIZONTAL_ALIGNMENT_CENTER:
				x += (gr.size.x - tw) * 0.5
			HORIZONTAL_ALIGNMENT_RIGHT:
				x += gr.size.x - tw
		var y := gr.position.y
		match l.vertical_alignment:
			VERTICAL_ALIGNMENT_CENTER:
				y += (gr.size.y - th) * 0.5
			VERTICAL_ALIGNMENT_BOTTOM:
				y += gr.size.y - th
		return Rect2(x, y, tw, minf(th, gr.size.y))
	if c is RichTextLabel:
		var rt := c as RichTextLabel
		var cw := minf(gr.size.x, float(rt.get_content_width()) * absf(sc.x))
		var ch := minf(gr.size.y, float(rt.get_content_height()) * absf(sc.y))
		return Rect2(gr.position, Vector2(cw, ch))
	return gr


func _walk(node: Node, scene: Node, in_scroll: bool, r: Dictionary, clip := Rect2(-1e6, -1e6, 2e6, 2e6)) -> void:
	if node is CanvasItem and not (node as CanvasItem).is_visible_in_tree():
		return
	if node is Window:
		return
	var scrolls := in_scroll or node is ScrollContainer
	if node is Control:
		var c := node as Control
		if c.modulate.a < 0.05 or c.self_modulate.a < 0.05 and not c is Container:
			return
		var gr := c.get_global_rect()
		var visible_size := gr.size.x > 2.0 and gr.size.y > 2.0
		if visible_size and not (c is ScrollContainer):
			var side: bool = gr.position.x < _vr.position.x - TOL or gr.end.x > _vr.end.x + TOL
			var vert: bool = (not in_scroll) and (gr.position.y < _vr.position.y - TOL or gr.end.y > _vr.end.y + TOL)
			if (side or vert) and not (c is Container):
				r["offscreen"].append("%s %s spans x %d..%d y %d..%d of %dx%d" % [_path(c, scene), _label_of(c).left(30),
						int(gr.position.x), int(gr.end.x), int(gr.position.y), int(gr.end.y), int(_vr.size.x), int(_vr.size.y)])
		if _has_text(c) and visible_size:
			var px := _font_px(c)
			if px < float(r["min_font"]):
				r["min_font"] = snappedf(px, 0.01)
				r["min_font_node"] = "%s %s" % [_path(c, scene), _label_of(c).left(36)]
			if _clipped(c):
				r["clipped"].append("%s %s needs more than %d" % [_path(c, scene), _label_of(c).left(36), int(c.size.x)])
			var ink := _ink_rect(c).intersection(clip)
			if ink.size.x > OVERLAP_MIN and ink.size.y > OVERLAP_MIN:
				r["_ink"].append([c, ink, r["_order"].size()])
		if visible_size and _opaque(c):
			r["_cover"].append([c, gr.intersection(clip), r["_order"].size()])
		r["_order"].append(c)
		if visible_size and c.has_meta("name_link_wired"):
			r["inline"].append("%s %s is %dx%d px" % [_path(c, scene), _label_of(c).left(30),
					int(round(gr.size.x * _factor)), int(round(gr.size.y * _factor))])
		if visible_size and _tappable(c):
			var wpx := gr.size.x * _factor
			var hpx := gr.size.y * _factor
			if minf(wpx, hpx) < MIN_TARGET - 0.5:
				r["small"].append("%s %s is %dx%d px" % [_path(c, scene), _label_of(c).left(30), int(round(wpx)), int(round(hpx))])
	var inner := clip
	if node is Control and ((node as Control).clip_contents or node is ScrollContainer):
		inner = clip.intersection((node as Control).get_global_rect())
	for ch in node.get_children():
		_walk(ch, scene, scrolls, r, inner)


## A control that paints a solid face: whatever was drawn before it, under
## it, is hidden (a sheet over a screen, the pre-bounce box over the controls).
func _opaque(c: Control) -> bool:
	if c is ColorRect:
		return (c as ColorRect).color.a >= 0.9
	if c is PanelContainer or c is Panel:
		var sb: StyleBox = c.get_theme_stylebox("panel")
		return sb is StyleBoxFlat and (sb as StyleBoxFlat).bg_color.a >= 0.9 and (sb as StyleBoxFlat).draw_center
	return false


## True when text `t` (drawn at `order`) is hidden at `area` by a solid face
## drawn after it that is not its own background.
func _hidden(r: Dictionary, t: Control, order: int, area: Rect2) -> bool:
	for cv in r["_cover"]:
		if int(cv[2]) <= order:
			continue
		var p: Control = cv[0]
		if p.is_ancestor_of(t):
			continue
		if (cv[1] as Rect2).encloses(area):
			return true
	return false


## Two texts whose ink crosses, neither inside the other, both in sight:
## words drawn over words.
func _overlaps(r: Dictionary, scene: Node) -> void:
	var ink: Array = r["_ink"]
	for i in range(ink.size()):
		var a: Control = ink[i][0]
		var ra: Rect2 = ink[i][1]
		for j in range(i + 1, ink.size()):
			var b: Control = ink[j][0]
			var rb: Rect2 = ink[j][1]
			var cross := ra.intersection(rb)
			if cross.size.x <= OVERLAP_MIN or cross.size.y <= OVERLAP_MIN:
				continue
			if a.is_ancestor_of(b) or b.is_ancestor_of(a):
				continue
			# The one drawn first is under a sheet the other sits on: hidden.
			if _hidden(r, a, int(ink[i][2]), cross) or _hidden(r, b, int(ink[j][2]), cross):
				continue
			r["overlap"].append("%s %s crosses %s %s by %dx%d" % [_path(a, scene), _label_of(a).left(24),
					_path(b, scene), _label_of(b).left(24), int(cross.size.x), int(cross.size.y)])


func _measure(scene: Node) -> Dictionary:
	var r := {"built": true, "min_font": 999.0, "min_font_node": "", "offscreen": [], "clipped": [], "small": [], "inline": [],
			"overlap": [], "_ink": [], "_cover": [], "_order": []}
	_walk(scene, scene, false, r)
	_overlaps(r, scene)
	if float(r["min_font"]) > 998.0:
		r["min_font"] = 0.0
	var out := {"built": true, "min_font": r["min_font"], "min_font_node": r["min_font_node"]}
	for k in ["offscreen", "clipped", "small", "inline", "overlap"]:
		var arr: Array = r[k]
		out[k] = arr.size()
		out[k + "_examples"] = arr.slice(0, EXAMPLES)
	# Something pushed off the side: name the deepest control whose own minimum
	# width is wider than the page, the one that forces the rest out.
	if int(out["offscreen"]) > 0:
		var wide := []
		_too_wide(scene, scene, _vr.size.x - 24.0, wide)
		out["too_wide_examples"] = wide.slice(0, EXAMPLES)
	return out


## Appends the deepest visible Controls under `node` whose combined minimum
## width exceeds `limit`; returns whether `node` or anything under it did.
func _too_wide(node: Node, scene: Node, limit: float, out: Array) -> bool:
	if node is CanvasItem and not (node as CanvasItem).is_visible_in_tree():
		return false
	if node is Window:
		return false
	var deeper := false
	for ch in node.get_children():
		# A scroll adds its bar to its page's width: the page has that much less.
		var lim := limit
		if node is ScrollContainer and ch is Control:
			lim -= maxf(0.0, (node as Control).get_combined_minimum_size().x - (ch as Control).get_combined_minimum_size().x)
		deeper = _too_wide(ch, scene, lim, out) or deeper
	if deeper:
		return true
	if node is Control:
		var w := (node as Control).get_combined_minimum_size().x
		if w > limit:
			# Its widest children say what adds up to it.
			var parts := []
			for ch in node.get_children():
				if ch is Control and (ch as Control).visible:
					parts.append([(ch as Control).get_combined_minimum_size().x, "%s %d" % [ch.get_class(), int((ch as Control).get_combined_minimum_size().x)]])
			parts.sort_custom(func(a, b): return a[0] > b[0])
			out.append("%s %s has a minimum width of %d (%s)" % [_path(node, scene), _label_of(node).left(30), int(w),
					", ".join(parts.slice(0, 4).map(func(x): return x[1]))])
			return true
	return false


func _record(key: String, scene: Node) -> void:
	await _frames(10)
	var m := _measure(scene)
	_results[key] = m
	print("SWEEP %s | min font %.1f px | off screen %d | clipped %d | small targets %d | overlap %d" % [
			key, float(m["min_font"]), int(m["offscreen"]), int(m["clipped"]), int(m["small"]), int(m["overlap"])])
	for k in ["clipped", "offscreen", "too_wide", "overlap"]:
		for ex in m.get(k + "_examples", []):
			print("  %s %s: %s" % [key, k, ex])
	if _png != "" and DisplayServer.get_name() != "headless":
		# The picture after the arrival fades (the hub's content fades up over half a second).
		await _frames(45)
		var img := root.get_viewport().get_texture().get_image()
		img.convert(Image.FORMAT_RGBA8)
		img.save_png(_png.path_join(key + ".png"))


func _open(key: String, path: String) -> Node:
	var scene: Node = load(path).instantiate()
	root.add_child(scene)
	await _record(key, scene)
	return scene


func _close(scene: Node) -> void:
	if scene != null:
		scene.queue_free()
	await _frames(3)


func _fail(key: String, why: String) -> void:
	_results[key] = {"built": false, "error": why}
	print("SWEEP %s | did not build: %s" % [key, why])


# --- the run ---------------------------------------------------------------

func _career(start := true) -> void:
	_state.reset()
	_state.career_seed = SEED
	_state.replay_seed = SEED
	# Every first-visit intro seen, so each screen is measured itself rather
	# than under its intro card.
	var seen := ["training", "weekly_loop", "season_stats", "momentum"]
	seen.append_array(load("res://scripts/ui/FirstVisitIntro.gd").TEXT.keys())
	for k in seen:
		_state.set_setting("seen_%s_intro" % k, true)
	if start:
		_state.start_season(CLUB, _db.club_list(CLUB))


func _run() -> void:
	var out := "sweep.json"
	var text_size := "standard"
	var cli := OS.get_cmdline_user_args()
	for i in range(cli.size() - 1):
		if str(cli[i]) == "--out":
			out = str(cli[i + 1])
		if str(cli[i]) == "--text-size":
			text_size = str(cli[i + 1])
		if str(cli[i]) == "--png":
			_png = str(cli[i + 1])
			DirAccess.make_dir_recursive_absolute(_png)
		if str(cli[i]) == "--size":
			var wh := str(cli[i + 1]).split("x")
			W = int(wh[0])
			H = int(wh[1])
	await process_frame
	_state = root.get_node("GameState")
	_db = root.get_node("GameDB")
	var UK = load("res://scripts/ui/UiKit.gd")
	_state.autosave_enabled = false
	_state.save_path = "user://sweep.save"
	_state.settings_path = "user://sweep.cfg"
	UK.apply_appearance("dark")
	UK.apply_text_size(text_size)
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	# ScreenLayout sets the logical size from the window on a resize.
	await _frames(10)
	# Measure as a plain 96-dpi screen does (CI's), so a run on a scaled
	# Windows display gives the same UI units: 390x844 is 390 units wide, not
	# the 320 a 150% display would leave.
	if DisplayServer.get_name() != "headless":
		var layout = root.get_node("ScreenLayout")
		var px := Vector2(root.size)
		var here: float = layout.desktop_density(px, DisplayServer.screen_get_scale(),
				DisplayServer.screen_get_dpi() if OS.get_name() == "Windows" else 0)
		var plain: float = layout.desktop_density(px, 1.0, 0)
		layout.ui_scale = plain / maxf(1.0, here)
		layout._update_scale()
		await _frames(10)
	_vr = root.get_visible_rect()
	_factor = float(W) / maxf(1.0, _vr.size.x)
	print("SWEEP window %dx%d, %dx%d UI units, %.3f px per unit" % [W, H, int(_vr.size.x), int(_vr.size.y), _factor])
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)

	# Fresh state: the front door and the club forge.
	_career(false)
	var scene: Node = await _open("main", "res://scenes/Main.tscn")
	await _close(scene)
	scene = await _open("forge", "res://scenes/ClubForgeScene.tscn")
	await _close(scene)

	# The League Draft, a club chosen.
	_career(false)
	_state.draft = load("res://scripts/sim/Draft.gd").new(_db.all_players_sorted(), _db.active_clubs(2026).duplicate(), 12345)
	scene = load("res://scenes/DraftScene.tscn").instantiate()
	root.add_child(scene)
	scene.call("_on_club_chosen", CLUB)
	await _record("draft", scene)
	await _close(scene)

	# The weekly screens on one seeded Melbourne career.
	_career(true)
	for key in ["hub", "selection", "training", "list", "coaching", "staff", "stats"]:
		scene = await _open(key, root.get_node("Router").SCENES[key])
		await _close(scene)

	# The live match, at the pre-bounce box.
	if _state.prepare_interactive_match():
		scene = await _open("match", "res://scenes/MatchScene.tscn")
		await _close(scene)
	else:
		_fail("match", "no match to prepare")

	# The pre-season stops.
	_career(true)
	_state.open_preseason()
	scene = await _open("preseason", "res://scenes/PreSeasonScene.tscn")
	await _close(scene)

	# The season played out: its review, then the off-season.
	_career(true)
	var guard := 0
	while not _state.season.is_season_over() and guard < 60:
		guard += 1
		_state.advance()
	if _state.season.is_season_over():
		scene = await _open("season_review", "res://scenes/SeasonReviewScene.tscn")
		await _close(scene)
		_state.open_offseason()
		scene = await _open("offseason", "res://scenes/OffseasonScene.tscn")
		await _close(scene)
	else:
		_fail("season_review", "the season did not finish")
		_fail("offseason", "the season did not finish")

	var data := {"size": "%dx%d" % [W, H], "text_size": UK.text_size(), "units": "%dx%d" % [int(_vr.size.x), int(_vr.size.y)],
			"px_per_unit": snappedf(_factor, 0.001), "screens": _results}
	var f := FileAccess.open(out, FileAccess.WRITE)
	if f == null:
		push_error("could not write " + out)
		quit(1)
		return
	f.store_string(JSON.stringify(data, "\t"))
	f.close()
	print("wrote ", out)
	quit(0)
