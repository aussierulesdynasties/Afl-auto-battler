extends SceneTree
## Every club's guernsey for every season 1990-2026 on one chart (Legacy mode, TODO row
## 142): a row per club, a cell per guernsey era with its years, the crest and the
## match figure from the front and behind, drawn by the game's own shaders. The bar
## under each row covers 1990-2026, one segment per era. Needs a real renderer:
##   godot --path . --script tools/visual/capture_era_chart.gd -- --out PATH.png
## Optional: --clubs ADE,WCE (only those rows), --scale 2.0 (bigger figures).

const FIRST := 1990
const LAST := 2026
const LEFT := 150.0
const CELL := 250.0
const ROW := 204.0


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
	var UK = load("res://scripts/ui/UiKit.gd")
	var SV: GDScript = load("res://scripts/ui/match/StoppageVignette.gd")
	db.reload("1990")  # the 1990 start keeps Fitzroy and the Bears
	var codes: Array = db.clubs.keys()
	codes.sort_custom(func(a, b): return str(db.club_era(a, LAST).get("name", a)) < str(db.club_era(b, LAST).get("name", b)))
	# Clubs that join after 2026 (Tasmania, Canberra) have no season on the chart.
	var played: Array = db.active_clubs(FIRST) + db.active_clubs(LAST)
	codes = codes.filter(func(c): return played.has(c))
	if not only.is_empty():
		codes = codes.filter(func(c): return only.has(c))
	# Each club's eras: the seasons it played, grouped where the guernsey and colours repeat.
	var rows := []
	var widest := 1
	for code in codes:
		var span := _span(db, code)
		var eras := []
		for y in range(span.x, span.y + 1):
			db.apply_era(y)
			var g: Dictionary = db.club_guernsey(code)
			var key := "%s|%s|%s|%s|%s|%s" % [_label(db.clubs[code]), g["design"], g["base"].to_html(),
					g["pattern"].to_html(), g["pattern2"].to_html(), g.get("pattern3", g["pattern2"]).to_html()]
			if not eras.is_empty() and eras[-1]["key"] == key:
				eras[-1]["to"] = y
			else:
				eras.append({"key": key, "from": y, "to": y, "kit": g.duplicate(), "name": _label(db.clubs[code])})
		widest = maxi(widest, eras.size())
		rows.append({"code": code, "eras": eras, "span": span})
	var cell := CELL * scale
	var row_h := ROW * scale
	var w := int(LEFT + cell * widest + 20)
	var h := int(64 + row_h * rows.size() + 10)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.content_scale_factor = 1.0
	root.size = Vector2i(w, h)
	DisplayServer.window_set_size(Vector2i(w, h))
	var bg := ColorRect.new()
	bg.color = UK.BG
	bg.size = Vector2(w, h)
	root.add_child(bg)
	var title := Label.new()
	title.text = "Home guernseys by season, %d-%d" % [FIRST, LAST]
	title.position = Vector2(16, 12)
	title.add_theme_font_size_override("font_size", 24)
	root.add_child(title)
	var y := 64.0
	for r in rows:
		_row(UK, SV, db, r, y, w, cell, row_h, scale)
		y += row_h
	db.apply_era(LAST)
	print("era chart: %d clubs, up to %d eras a club" % [rows.size(), widest])
	for i in range(6):
		await process_frame
	root.get_viewport().get_texture().get_image().save_png(out)
	print("wrote ", out)
	quit()


## A club's name as worn that season: "Brisbane Bears", "Footscray".
func _label(d: Dictionary) -> String:
	var n := str(d.get("name", ""))
	var s := str(d.get("short", ""))
	return n if n == s or n.ends_with(s) or s == "" else "%s %s" % [n, s]


## The first and last season a club played between FIRST and LAST.
func _span(db, code: String) -> Vector2i:
	var rows: Array = db._club_years.get(code, [])
	var lo := FIRST
	var hi := LAST
	if not rows.is_empty():
		lo = maxi(FIRST, int(rows[0]["from"]))
		var closed := rows.all(func(r): return int(r["to"]) != 0)
		if closed:
			var last := 0
			for r in rows:
				last = maxi(last, int(r["to"]))
			hi = mini(LAST, last)
	var enter := int(db._club_base.get(code, {}).get("enter", 0))
	if rows.is_empty() and enter > FIRST:
		lo = enter
	return Vector2i(lo, hi)


func _row(UK, SV: GDScript, db, r: Dictionary, y: float, w: int, cell: float, row_h: float, scale: float) -> void:
	var code: String = r["code"]
	var base := db.club_era(code, LAST) as Dictionary
	var name := Label.new()
	name.text = str(base.get("name", code)) if code != "FIT" else "Fitzroy"
	name.position = Vector2(16, y + 8)
	name.size = Vector2(LEFT - 24, 40)
	name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	name.add_theme_font_size_override("font_size", 17)
	root.add_child(name)
	var rule := ColorRect.new()
	rule.color = Color(1, 1, 1, 0.08)
	rule.position = Vector2(12, y + row_h - 3)
	rule.size = Vector2(w - 24, 1)
	root.add_child(rule)
	# The 1990-2026 bar: one segment per era, in its guernsey's colours; grey before entry or after leaving.
	var bar_y := y + row_h - 16.0
	var bar_w := float(w) - LEFT - 20.0
	var per := bar_w / float(LAST - FIRST + 1)
	var x := LEFT
	for era in r["eras"]:
		var c := Control.new()
		c.position = Vector2(LEFT + (era["from"] - FIRST) * per, bar_y)
		c.size = Vector2((era["to"] - era["from"] + 1) * per - 2.0, 8)
		var kit: Dictionary = era["kit"]
		c.draw.connect(func():
			c.draw_rect(Rect2(0, 0, c.size.x, 8), kit["base"])
			c.draw_rect(Rect2(0, 5, c.size.x, 3), kit["pattern"]))
		root.add_child(c)
		# The era cell: crest, then the figure from the front and from behind.
		var crest_box := CenterContainer.new()
		crest_box.position = Vector2(x, y + 4)
		crest_box.size = Vector2(86 * scale, 86 * scale)
		var crest = UK.colour_marker([kit["base"], kit["pattern"], kit["pattern2"]], 82.0 * scale, str(kit["design"]), code)
		crest.third = kit.get("pattern3", kit["pattern2"])
		crest_box.add_child(crest)
		root.add_child(crest_box)
		var fig := Control.new()
		fig.position = Vector2(x + 86 * scale, y)
		fig.size = Vector2(cell - 86 * scale, row_h)
		fig.material = SV.figure_material([kit])
		fig.draw.connect(func():
			var col: Color = SV.look_colour(0, {"skin": 1, "hair": 2, "hair_style": "short_crop"})
			var fx := 40.0 * scale
			for facing in ["front", "back"]:
				var info := VignetteFigures.strip("average", "idle", facing)
				SV.draw_frame(fig, Vector2(fx, 176.0 * scale), info, 0, 0.88 * scale, col, false,
						Color(0, 0, 0, 0), Transform2D.IDENTITY, "short_crop")
				fx += 78.0 * scale)
		root.add_child(fig)
		var years := Label.new()
		var span_text := str(era["from"]) if era["from"] == era["to"] else "%d-%d" % [era["from"], era["to"]]
		if era["to"] == LAST and era["from"] != LAST:
			span_text = "%d-now" % era["from"]
		years.text = span_text
		if era["name"] != _label(base):
			years.text += "\n" + era["name"]
		years.position = Vector2(x + 2, y + 94 * scale)
		years.size = Vector2(86 * scale, 60)
		years.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		years.add_theme_font_size_override("font_size", 14)
		years.add_theme_color_override("font_color", Color(1, 1, 1, 0.85))
		root.add_child(years)
		x += cell
