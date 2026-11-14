class_name PlayerCondition
extends RefCounted
## A player's fatigue, morale and form as numbers (TODO row 183; director,
## 2026-11-14: team selection "should show a numerical value of their fatigue
## level", and "also need somewhere to display player morale and form as a
## number too"). Each number is the one the game keeps, never a copy:
## - Fatigue: the load in his legs, 0-100 (Workload.value). It caps the legs he
##   starts a match with (Workload.energy_cap).
## - Morale: 5-100, settled at 70 (ClubLife.morale, after any sting). The match
##   reads it as a nudge to his footy (ClubLife.form: +3% at 100, -3% at 40).
## - Form: his match rating a game over his last three (GameState.form_log,
##   the numbers behind the form marks), or his games in the twos when he has
##   no senior game this season. It never changes a match.
## A rival's numbers are his club's business: callers show none for them.

const KEYS := ["fatigue", "morale", "form"]
const WORDS := {"fatigue": "Fatigue", "morale": "Morale", "form": "Form"}
## The rating a game that fills the form bar. Ratings are not out of 100:
## a midfielder in good touch averages 120-160, so the bar fills at 200.
const FORM_FULL := 200.0
## A middling state: neither the good nor the bad colour.
const MID := Color(0.80, 0.76, 0.55)


static func fatigue(p: Dictionary) -> int:
	return int(round(Workload.value(p)))


static func morale(p: Dictionary) -> int:
	return ClubLife.morale(p)


## {"value": his last games' rating a game (-1 when he has played neither
## seniors nor twos this season), "season": the season's rating a game,
## "games": how many games "value" is over, "where": "seniors" or "reserves"}.
static func form(id: String, form_log: Dictionary, reserves_log: Dictionary) -> Dictionary:
	var f: Dictionary = form_log.get(id, {})
	var n := int(f.get("n", 0))
	if n > 0:
		var last: Array = f.get("last", [])
		return {"value": _mean(last), "season": int(round(float(f.get("sum", 0)) / float(n))),
				"games": last.size(), "where": "seniors"}
	var r: Dictionary = reserves_log.get(id, {})
	var rn := int(r.get("n", 0))
	if rn > 0:
		var pts := []
		for g in r.get("last", []):
			pts.append(float((g as Dictionary).get("pts", 0)))
		return {"value": _mean(pts), "season": int(round(float(r.get("sum", 0)) / float(rn))),
				"games": pts.size(), "where": "reserves"}
	return {"value": -1, "season": -1, "games": 0, "where": ""}


static func _mean(xs: Array) -> int:
	if xs.is_empty():
		return -1
	var t := 0.0
	for x in xs:
		t += float(x)
	return int(round(t / float(xs.size())))


## The three as shown: key -> {"value" (-1: none yet), "fill" 0..1, "colour", "word"}.
static func read(p: Dictionary, form_log: Dictionary, reserves_log: Dictionary) -> Dictionary:
	var fat := fatigue(p)
	var mor := morale(p)
	var fm := form(str(p.get("id", "")), form_log, reserves_log)
	var fv := int(fm["value"])
	var fat_c := UiKit.BAD if fat >= Workload.NEEDS_BREAK else (MID if fat >= Workload.CARRYING else UiKit.TEXT)
	var mor_c := UiKit.BAD if mor < 40 else (MID if mor < 65 else (UiKit.GOOD if mor >= 85 else UiKit.TEXT))
	var form_c := UiKit.MUTED
	if fv >= 0:
		form_c = UiKit.TEXT
		if fm["games"] >= ReservesForm.GAMES and fv >= int(fm["season"]) + 15:
			form_c = UiKit.GOOD
		elif fm["games"] >= ReservesForm.GAMES and fv <= int(fm["season"]) - 15:
			form_c = UiKit.BAD
	return {
		"fatigue": {"value": fat, "fill": fat / 100.0, "colour": fat_c, "word": Workload.label(p)},
		"morale": {"value": mor, "fill": mor / 100.0, "colour": mor_c, "word": ClubLife.mood(mor)},
		"form": {"value": fv, "fill": clampf(fv / FORM_FULL, 0.0, 1.0), "colour": form_c,
				"word": _form_word(fm), "season": int(fm["season"]), "where": str(fm["where"])},
	}


static func _form_word(fm: Dictionary) -> String:
	if int(fm["value"]) < 0:
		return "No game this season"
	var games := "last game" if int(fm["games"]) == 1 else "last %d games" % int(fm["games"])
	return "Rating a game, %s%s (season %d)" % [games,
			" in the twos" if str(fm["where"]) == "reserves" else "", int(fm["season"])]


## One line for a tooltip: "Fatigue 60 (Needs a break) · Morale 70 (Settled) · Form 64".
static func tooltip(c: Dictionary) -> String:
	var bits := PackedStringArray()
	for k in KEYS:
		var v := int(c[k]["value"])
		bits.append("%s %s (%s)" % [WORDS[k], str(v) if v >= 0 else "-", str(c[k]["word"])])
	return " · ".join(bits)


## The three side by side, each a number over a short bar: a tile's strip
## (unlabelled; the key under the oval names them) or, `labelled`, each with
## its word. Every number is named "<Key>_<id>" for the tests.
static func strip(p: Dictionary, form_log: Dictionary, reserves_log: Dictionary, size: int,
		labelled := false) -> HBoxContainer:
	var c := read(p, form_log, reserves_log)
	var id := str(p.get("id", ""))
	var h := UiKit.hbox(4 if not labelled else 10)
	h.name = "Condition_" + id
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for k in KEYS:
		var cell := UiKit.vbox(1)
		cell.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		cell.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var top := UiKit.hbox(4)
		top.alignment = BoxContainer.ALIGNMENT_CENTER if not labelled else BoxContainer.ALIGNMENT_BEGIN
		if labelled:
			var w := UiKit.lbl(WORDS[k], size, UiKit.MUTED)
			w.name = "Word"
			w.autowrap_mode = TextServer.AUTOWRAP_OFF
			top.add_child(w)
		var v := int(c[k]["value"])
		var n := UiKit.lbl(str(v) if v >= 0 else "-", size, c[k]["colour"], true)
		n.name = "%s_%s" % [WORDS[k], id]
		n.autowrap_mode = TextServer.AUTOWRAP_OFF
		top.add_child(n)
		cell.add_child(top)
		cell.add_child(_bar(float(c[k]["fill"]), c[k]["colour"]))
		h.add_child(cell)
	return h


## A thin bar the width of its cell, filled to `fill`.
static func _bar(fill: float, colour: Color) -> Control:
	var holder := Control.new()
	holder.custom_minimum_size = Vector2(0, 3)
	holder.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := ColorRect.new()
	bg.color = Color(1, 1, 1, 0.12)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(bg)
	var fg := ColorRect.new()
	fg.name = "Fill"
	fg.color = colour
	fg.anchor_bottom = 1.0
	fg.anchor_right = clampf(fill, 0.0, 1.0)
	fg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(fg)
	return holder


## The player sheet's block: a row each, the word, a bar, the number, and
## what it means in words. Your own players only.
static func sheet_block(p: Dictionary, form_log: Dictionary, reserves_log: Dictionary) -> VBoxContainer:
	var c := read(p, form_log, reserves_log)
	var id := str(p.get("id", ""))
	var v := UiKit.vbox(4)
	v.name = "ProfileCondition"
	for k in KEYS:
		var row := UiKit.hbox(8)
		var w := UiKit.lbl(WORDS[k], UiKit.SMALL, UiKit.MUTED, true)
		w.custom_minimum_size.x = 64
		w.autowrap_mode = TextServer.AUTOWRAP_OFF
		row.add_child(w)
		var val := int(c[k]["value"])
		var n := UiKit.lbl(str(val) if val >= 0 else "-", UiKit.NAME, c[k]["colour"], true)
		n.name = "Sheet%s_%s" % [WORDS[k], id]
		n.custom_minimum_size.x = 30
		n.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		n.autowrap_mode = TextServer.AUTOWRAP_OFF
		row.add_child(n)
		var bar := _bar(float(c[k]["fill"]), c[k]["colour"])
		bar.custom_minimum_size = Vector2(70, 6)
		bar.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(bar)
		var note := UiKit.lbl(str(c[k]["word"]), UiKit.SMALL, UiKit.MUTED)
		note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(note)
		v.add_child(row)
	return v
