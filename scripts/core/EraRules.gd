class_name EraRules
extends RefCounted
## The league's rules as they stood in a given season, read from
## data/legacy/era_rules.csv (rule,value,from_year,to_year,quote,source_url,
## checked). Each row holds one rule for an inclusive span of years, with the
## quote and source it was taken from. Legacy mode reads it for the salary
## cap (Contracts.salary_cap_for_year) and, later, list sizes and the bench.
##
## A static class rather than GameDB code so sim scripts (Contracts) can read
## it without depending on an autoload; GameDB.era_rule is the front door.

const PATH := "res://data/legacy/era_rules.csv"

static var _rows := {}  # rule -> Array of [from_year, to_year, value]
static var _loaded := false


## The value of `rule` in `year`, or `fallback` when no row covers that year.
static func value(rule: String, year: int, fallback := 0.0) -> float:
	for span in _spans(rule):
		if year >= int(span[0]) and year <= int(span[1]):
			return float(span[2])
	return fallback


## Whether a row covers `rule` in `year`.
static func has(rule: String, year: int) -> bool:
	for span in _spans(rule):
		if year >= int(span[0]) and year <= int(span[1]):
			return true
	return false


## The years the CSV covers for `rule`: [first, last], or [] when it has none.
static func span(rule: String) -> Array:
	var spans := _spans(rule)
	if spans.is_empty():
		return []
	var lo := int(spans[0][0])
	var hi := int(spans[0][1])
	for s in spans:
		lo = mini(lo, int(s[0]))
		hi = maxi(hi, int(s[1]))
	return [lo, hi]


static func _spans(rule: String) -> Array:
	if not _loaded:
		_load()
	return _rows.get(rule, [])


static func _load() -> void:
	_loaded = true
	_rows = {}
	var f := FileAccess.open(PATH, FileAccess.READ)
	if f == null:
		push_warning("EraRules: cannot open %s" % PATH)
		return
	var head := f.get_csv_line()
	var col := {}
	for i in head.size():
		col[head[i]] = i
	while not f.eof_reached():
		var row := f.get_csv_line()
		if row.size() < 4 or str(row[0]).strip_edges() == "":
			continue
		var rule := str(row[int(col.get("rule", 0))])
		if not _rows.has(rule):
			_rows[rule] = []
		(_rows[rule] as Array).append([int(row[int(col.get("from_year", 2))]),
				int(row[int(col.get("to_year", 3))]), float(row[int(col.get("value", 1))])])
	# Earliest span first, so a lookup reads the file's years in order.
	for rule in _rows:
		(_rows[rule] as Array).sort_custom(func(a, b): return int(a[0]) < int(b[0]))
