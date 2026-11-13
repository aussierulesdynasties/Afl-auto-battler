extends SceneTree
## Every club's home guernsey, picture by picture, 1990-2026 (Legacy mode, TODO row 142): a
## block per club, a cell per guernsey with its seasons, the crest and the match figure from
## the front and behind, drawn by the game's own shaders. A cell is one drawing in the kit
## atlas (seasons whose pictures differ only in sponsors share it), then 2026, clubs.csv's own.
## Needs a real renderer:
##   godot --path . --script tools/visual/capture_era_chart.gd -- --out PATH.png
## Optional: --clubs ADE,WCE (only those clubs), --scale 2.0 (bigger figures).

const FIRST := 1990
const LAST := 2026
const PER_LINE := 12
const CELL := 168.0
const LINE := 190.0
const HEAD := 34.0


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "era_chart.png"
	var only := []
	var scale := 1.0
	var cli := OS.get_cmdline_user_args()
	for i in range(cli.size() - 1):
		match str(cli[i]):
			"--out":
				out = str(cli[i + 1])
			"--clubs":
				only = str(cli[i + 1]).split(",")
			"--scale":
				scale = float(cli[i + 1])
	await process_frame
	var db = root.get_node("GameDB")
	var ui_kit = load("res://scripts/ui/UiKit.gd")
	var sv: GDScript = load("res://scripts/ui/match/StoppageVignette.gd")
	db.reload("1990")  # the 1990 start keeps Fitzroy and the Bears
	var pics := _pictures(db)
	var codes: Array = pics.keys()
	codes.sort_custom(func(a, b): return _now_name(db, a) < _now_name(db, b))
	if not only.is_empty():
		codes = codes.filter(func(c): return only.has(c))
	var blocks := []
	for code in codes:
		blocks.append({"code": code, "cells": _cells(db, code, pics[code])})
	var cell := CELL * scale
	var line_h := LINE * scale
	var w := int(16 + cell * PER_LINE + 16)
	var h := 64.0
	for b in blocks:
		h += HEAD + line_h * ceili(float((b["cells"] as Array).size()) / PER_LINE) + 10
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.content_scale_factor = 1.0
	root.size = Vector2i(w, int(h))
	DisplayServer.window_set_size(Vector2i(w, int(h)))
	var bg := ColorRect.new()
	bg.color = ui_kit.BG
	bg.size = Vector2(w, h)
	root.add_child(bg)
	var title := Label.new()
	title.text = "Home guernseys by season, %d-%d" % [FIRST, LAST]
	title.position = Vector2(16, 12)
	title.add_theme_font_size_override("font_size", 24)
	root.add_child(title)
	var y := 64.0
	var total := 0
	for b in blocks:
		y = _block(ui_kit, sv, db, b, y, w, cell, line_h, scale)
		total += (b["cells"] as Array).size()
	db.apply_era(LAST)
	print("era chart: %d clubs, %d guernseys" % [blocks.size(), total])
	for i in range(6):
		await process_frame
	root.get_viewport().get_texture().get_image().save_png(out)
	print("wrote ", out)
	quit()


func _now_name(db, code: String) -> String:
	return "Fitzroy" if code == "FIT" else str(db.club_era(code, LAST).get("name", code))


## kits.csv's rows by club, in file order: {from, to, cell, picture}. A row with no season
## (from 0) is a picture worn only part of a season; its year is the picture's.
func _pictures(db) -> Dictionary:
	var out := {}
	var year_re := RegEx.create_from_string("(19|20)\\d\\d")
	for r in db._read_dicts(db.KITS_CSV):
		var code := str(r["code"])
		if not out.has(code):
			out[code] = []
		var m := year_re.search(str(r["picture"]))
		(out[code] as Array).append({"from": int(r["from"]), "to": int(r["to"]), "cell": int(r["cell"]),
				"year": int(m.get_string()) if m != null else 0})
	return out


## A club's cells: one per run of seasons in the same drawing, part-season pictures as their
## own, then 2026 when the club plays it.
func _cells(db, code: String, rows: Array) -> Array:
	var cells := []
	for r in rows:
		var part: bool = r["from"] <= 0
		var y0: int = r["year"] if part else r["from"]
		var y1: int = r["year"] if part else mini(r["to"], LAST - 1)
		if not part and not cells.is_empty() and not cells[-1]["part"] and cells[-1]["cell"] == r["cell"] \
				and cells[-1]["to"] == y0 - 1:
			cells[-1]["to"] = y1
			continue
		cells.append({"from": y0, "to": y1, "cell": r["cell"], "part": part})
	if db.active_clubs(LAST).has(code):
		cells.append({"from": LAST, "to": LAST, "cell": -1, "part": false})
	for c in cells:
		db.apply_era(c["from"])
		var g: Dictionary = db.club_guernsey(code)
		if c["cell"] >= 0:
			g["kit_cell"] = c["cell"]
		c["kit"] = g.duplicate()
		c["club"] = (db.clubs[code] as Dictionary).duplicate()
	return cells


func _block(ui_kit, sv: GDScript, db, b: Dictionary, y: float, w: int, cell: float, line_h: float,
		scale: float) -> float:
	var code: String = b["code"]
	var now_name := _now_name(db, code)
	var name := Label.new()
	name.text = "%s  (%d guernseys)" % [now_name, (b["cells"] as Array).size()]
	name.position = Vector2(16, y + 4)
	name.add_theme_font_size_override("font_size", 19)
	root.add_child(name)
	var rule := ColorRect.new()
	rule.color = Color(1, 1, 1, 0.10)
	rule.position = Vector2(12, y + HEAD - 4)
	rule.size = Vector2(w - 24, 1)
	root.add_child(rule)
	var i := 0
	for c in b["cells"]:
		var x := 16.0 + (i % PER_LINE) * cell
		var top := y + HEAD + (i / PER_LINE) * line_h
		var kit: Dictionary = c["kit"]
		var crest = ui_kit.colour_marker([kit["base"], kit["pattern"], kit["pattern2"]], 40.0 * scale,
				str(kit["design"]))
		crest.third = kit.get("pattern3", kit["pattern2"])
		crest.kit_cell = int(kit.get("kit_cell", -1))
		crest.position = Vector2(x, top)
		crest.size = Vector2(40, 40) * scale
		root.add_child(crest)
		var fig := Control.new()
		fig.position = Vector2(x, top)
		fig.size = Vector2(cell, line_h - 36 * scale)
		fig.material = sv.figure_material([kit])
		fig.draw.connect(func():
			var col: Color = sv.look_colour(0, {"skin": 1, "hair": 2, "hair_style": "short_crop"})
			var fx := 70.0 * scale
			for facing in ["front", "back"]:
				var info := VignetteFigures.strip("average", "idle", facing)
				sv.draw_frame(fig, Vector2(fx, 150.0 * scale), info, 0, 0.78 * scale, col, false,
						Color(0, 0, 0, 0), Transform2D.IDENTITY, "short_crop")
				fx += 64.0 * scale)
		root.add_child(fig)
		var years := Label.new()
		var text := str(c["from"]) if c["from"] == c["to"] else "%d-%d" % [c["from"], c["to"]]
		if c["part"]:
			text += ", part"
		# The name worn that season, where it differs: "Footscray", "Bears", "Kangaroos".
		var then: Dictionary = c["club"]
		var now := db.club_era(code, LAST) as Dictionary
		if str(then.get("name", "")) != str(now.get("name", "")):
			text += "  " + str(then.get("name", ""))
		elif str(then.get("short", "")) != str(now.get("short", "")):
			text += "  " + str(then.get("short", ""))
		years.text = text
		years.position = Vector2(x, top + line_h - 36 * scale)
		years.size = Vector2(cell - 6, 30)
		years.clip_text = true
		years.add_theme_font_size_override("font_size", 14)
		years.add_theme_color_override("font_color", Color(1, 1, 1, 0.88))
		root.add_child(years)
		i += 1
	return y + HEAD + line_h * ceili(float(i) / PER_LINE) + 10
