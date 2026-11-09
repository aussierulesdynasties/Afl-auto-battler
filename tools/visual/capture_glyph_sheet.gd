extends SceneTree
## Row 6.29 (STYLE-02): a glyph sheet of ARD Signwriter's look-alike characters
## (1/I/l, 0/O/o, 6/8/9, 5/S, 2/Z) in all three cuts at the game's sizes, plus
## every score and money form inside a box the size of the label Godot gives it,
## so clipped ink shows as ink past the box. Needs a real renderer and a window
## (off screen via override.cfg):
##   godot --path . --script tools/visual/capture_glyph_sheet.gd -- --out <prefix>
## Writes <prefix>_confusables.png and <prefix>_fit.png.

## UiKit is loaded at run time: a preload compiles it before the autoloads exist.
var UiKit
const CONFUSE := "1Il|  0Oo  |  689  |  5S  |  2Z  |  il1 lI1 1l1  O0O 0o0 868 969 696"
const SIZES := [13, 14, 15, 16, 18, 22, 24, 30, 36]
const SCORES := ["0.0 (0)", "1.1 (7)", "12.8 (80)", "6.9 (45)", "19.11 (125)", "28.18 (186)", "10.10 (70)"]
const MONEY := ["$85k", "$111k", "$650k", "$1.1m", "$1.25m", "$11.85m", "$999k", "$16.6m"]

var _out := "glyph_sheet"


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var a := OS.get_cmdline_user_args()
	for i in range(a.size()):
		if str(a[i]) == "--out":
			_out = str(a[i + 1])
	await process_frame
	UiKit = load("res://scripts/ui/UiKit.gd")
	UiKit.apply_appearance("dark")
	await _sheet("confusables", _confusables())
	await _sheet("fit", _fit())
	quit()


func _cuts() -> Array:
	return [["Regular", UiKit.FONT], ["Bold", UiKit.BOLD], ["Display", UiKit.DISPLAY]]


func _lab(text: String, font: Font, fs: int, col := Color("f1eee6")) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", fs)
	l.add_theme_color_override("font_color", col)
	return l


func _confusables() -> Control:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	for cut in _cuts():
		v.add_child(_lab(str(cut[0]), UiKit.BOLD, 18, Color("e38b73")))
		var big := _lab("1Il 0Oo 689 5S 2Z", cut[1], 96)
		v.add_child(big)
		for fs in SIZES:
			var h := HBoxContainer.new()
			var tag := _lab("%d" % fs, UiKit.FONT, 13, Color("a39e93"))
			tag.custom_minimum_size = Vector2(28, 0)
			h.add_child(tag)
			h.add_child(_lab(CONFUSE, cut[1], fs))
			v.add_child(h)
	return v


## Each form in a box exactly the label's own size: ink past the outline is ink a
## clipping row or a tight column would cut off.
func _fit() -> Control:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	var rows := [
		["Display", UiKit.DISPLAY, [22, 24, 30, 36], SCORES],
		["Display", UiKit.DISPLAY, [22, 30], MONEY],
		["Bold", UiKit.BOLD, [15, 16, 18], MONEY],
		["Regular", UiKit.FONT, [13, 15], MONEY + SCORES],
	]
	for r in rows:
		for fs in r[2]:
			var h := HBoxContainer.new()
			h.add_theme_constant_override("separation", 10)
			var tag := _lab("%s %d" % [r[0], fs], UiKit.FONT, 13, Color("a39e93"))
			tag.custom_minimum_size = Vector2(90, 0)
			h.add_child(tag)
			for t in r[3]:
				var box := PanelContainer.new()
				var sb := StyleBoxFlat.new()
				sb.bg_color = Color(0, 0, 0, 0)
				sb.border_color = Color("e38b73")
				sb.set_border_width_all(1)
				sb.set_content_margin_all(0)
				sb.expand_margin_left = 1
				sb.expand_margin_right = 1
				sb.expand_margin_top = 1
				sb.expand_margin_bottom = 1
				box.add_theme_stylebox_override("panel", sb)
				var l := _lab(str(t), r[1], fs)
				if r[0] == "Display":
					UiKit.shade(l, fs)
				box.add_child(l)
				h.add_child(box)
			v.add_child(h)
	return v


## Drawn in its own SubViewport, so the sheet can be taller than any window.
func _sheet(name: String, body: Control) -> void:
	var vp := SubViewport.new()
	vp.transparent_bg = false
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	var bg := ColorRect.new()
	bg.color = Color("121110")
	var m := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		m.add_theme_constant_override("margin_" + side, 16)
	m.add_child(body)
	bg.add_child(m)
	vp.add_child(bg)
	root.add_child(vp)
	vp.size = Vector2i(64, 64)
	for i in 3:
		await process_frame
	var ms := m.get_combined_minimum_size()
	var sz := Vector2i(ceili(ms.x), ceili(ms.y))
	vp.size = sz
	bg.size = Vector2(sz)
	m.size = Vector2(sz)
	for i in 4:
		await process_frame
	# An off-screen window may never present a frame: draw it by hand.
	RenderingServer.force_draw(false)
	var img := vp.get_texture().get_image()
	var path := "%s_%s.png" % [_out, name]
	img.save_png(path)
	print("wrote ", path, " ", sz)
	vp.queue_free()
	await process_frame
