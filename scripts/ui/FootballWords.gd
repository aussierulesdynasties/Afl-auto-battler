class_name FootballWords
extends RefCounted
## Long-press any football word for its exact rule (row T3.R43, P-61; director
## bible 43: "one source shared with the stat guide"). The rule words come from
## the places that already define them, so a word reads the same here as in the
## stat guide, the coach box and the trait sheet:
##   the rated stats    StatGuide.STATS (the stat guide's own line)
##   the guide's topics StatGuide.TOPICS (OVR, POT, XP...)
##   game plans         CoachReport.PLAN_PARTS (does, gain, cost, what beats it)
##   pep talks          CoachReport.PEP_EFFECTS
##   traits, synergies  TraitLink (its own sheet: effect and what earns it)
## A long press anywhere (WordPress.gd) finds the word under the finger, or the
## words in that line, and opens one sheet. Look-up only; no effect on the game.

const SHEET_NAME := "WordRule"

static var _cache := {}


## Every word: {shown word -> {"title", "kind", "lines": [...], "trait": key or ""}}.
static func entries() -> Dictionary:
	if not _cache.is_empty():
		return _cache
	var out := {}
	for row in GameState.TRAIN_STATS:
		var key := str(row[0])
		out[str(row[1])] = {"title": str(row[1]), "kind": "Rating", "lines": [StatGuide.short(key)], "trait": ""}
	for t in StatGuide.TOPICS:
		var title := str(t[0])
		var e := {"title": title, "kind": "How it works", "lines": [str(t[1])], "trait": ""}
		out[title] = e
		# "Overall (OVR)" is said as OVR on the screens.
		var short := title.get_slice("(", 1).trim_suffix(")") if title.contains("(") else ""
		if short != "":
			out[short] = e
	for k in CoachReport.PLAN_NAMES:
		var part: Dictionary = CoachReport.PLAN_PARTS.get(k, {})
		var lines := [str(part.get("does", ""))]
		if part.has("gain"):
			lines.append("Gain: " + str(part["gain"]))
		if part.has("cost"):
			lines.append("Cost: " + str(part["cost"]))
		if part.has("beats"):
			lines.append(str(part["beats"]))
		out[str(CoachReport.PLAN_NAMES[k])] = {"title": str(CoachReport.PLAN_NAMES[k]), "kind": "Game plan", "lines": lines, "trait": ""}
	for k in CoachReport.PEP_NAMES:
		out[str(CoachReport.PEP_NAMES[k])] = {"title": str(CoachReport.PEP_NAMES[k]), "kind": "Pep talk",
				"lines": [str(CoachReport.PEP_EFFECTS.get(k, ""))], "trait": ""}
	var traits := TraitLink.names()
	for shown in traits:
		out[str(shown)] = {"title": str(shown), "kind": "", "lines": [], "trait": str(traits[shown])}
	_cache = out
	return out


## The words found in `text`, longest first where two overlap, in reading
## order. A word matches whole (not inside a longer word), in any case.
static func find_in(text: String) -> Array:
	var all := entries()
	var keys: Array = all.keys()
	keys.sort_custom(func(a, b): return str(a).length() > str(b).length())
	var low := text.to_lower()
	var spans: Array = []
	for k in keys:
		var w := str(k).to_lower()
		var from := 0
		while w != "":
			var i := low.find(w, from)
			if i < 0:
				break
			from = i + w.length()
			var j := i + w.length()
			if (i > 0 and _letter(low[i - 1])) or (j < low.length() and _letter(low[j])):
				continue
			var free := true
			for s in spans:
				if i < int(s[1]) and j > int(s[0]):
					free = false
			if free:
				spans.append([i, j, str(k)])
	spans.sort_custom(func(a, b): return int(a[0]) < int(b[0]))
	var out: Array = []
	for s in spans:
		if not out.has(str(s[2])):
			out.append(str(s[2]))
	return out


## The word whose letters sit under character `at` of `text`, or "".
static func word_at(text: String, at: int) -> String:
	var all := entries()
	var keys: Array = all.keys()
	keys.sort_custom(func(a, b): return str(a).length() > str(b).length())
	var low := text.to_lower()
	for k in keys:
		var w := str(k).to_lower()
		var from := 0
		while w != "":
			var i := low.find(w, from)
			if i < 0 or i > at:
				break
			from = i + 1
			var j := i + w.length()
			if at >= j:
				continue
			if (i > 0 and _letter(low[i - 1])) or (j < low.length() and _letter(low[j])):
				continue
			return str(k)
	return ""


static func _letter(ch: String) -> bool:
	return ch.to_lower() != ch.to_upper() or ch.is_valid_int()


## Open the rule sheet for `words` over the screen holding `from`: one word
## that is a trait or synergy opens the trait sheet; otherwise each word is a
## title, what kind of rule it is, and its lines. Returns the sheet or null.
static func open(from: Node, words: Array) -> Control:
	if words.is_empty() or from == null or not from.is_inside_tree():
		return null
	var all := entries()
	if words.size() == 1 and str((all.get(str(words[0]), {}) as Dictionary).get("trait", "")) != "":
		return TraitLink.open(from, str(all[str(words[0])]["trait"]))
	var host: Control = null
	var n: Node = from
	while n != null and not (n is Window):
		if n is Control:
			host = n
		n = n.get_parent()
	if host == null:
		return null
	close_open(host)
	var box := UiKit.modal_box(host, 480.0, 0.0)
	var overlay: Control = box["overlay"]
	overlay.name = SHEET_NAME
	UiKit.close_on_outside_tap(box)
	var v: VBoxContainer = box["body"]
	v.add_theme_constant_override("separation", 6)
	var shown := 0
	for w in words:
		var e: Dictionary = all.get(str(w), {})
		if e.is_empty():
			continue
		var title := str(e["title"])
		var kind := str(e["kind"])
		var lines: Array = e["lines"]
		if str(e["trait"]) != "":
			var rows := TraitLink.sheet_lines(str(e["trait"]))
			kind = str(rows[1])
			lines = rows.slice(2)
		if shown > 0:
			v.add_child(UiKit.spacer(8))
		var t := UiKit.lbl(title, UiKit.H1 if words.size() == 1 else UiKit.NAME, UiKit.TEXT, true)
		t.name = "WordTitle_%d" % shown
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(t)
		var k := UiKit.lbl(kind, UiKit.SMALL, UiKit.MUTED)
		k.name = "WordKind_%d" % shown
		v.add_child(k)
		for i in lines.size():
			if str(lines[i]).strip_edges() == "":
				continue
			var l := UiKit.lbl(str(lines[i]), UiKit.BODY if i == 0 else UiKit.SMALL, UiKit.TEXT if i == 0 else UiKit.MUTED)
			l.name = "WordRule_%d_%d" % [shown, i]
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			v.add_child(l)
		shown += 1
	var close := UiKit.btn("Close", UiKit.NAME, true)
	close.name = "WordClose"
	close.custom_minimum_size = Vector2(0, 48)
	close.pressed.connect(func() -> void: overlay.queue_free())
	box["footer"].add_child(close)
	return overlay


## Back closes an open rule sheet before the screen sees it. True when it did.
static func close_open(scene: Node) -> bool:
	if scene == null:
		return false
	for c in scene.get_children():
		if c.name == SHEET_NAME and not c.is_queued_for_deletion():
			c.queue_free()
			c.name = "WordRuleClosing"
			return true
	return false
