class_name RealFixture
extends RefCounted
## The real home-and-away fixtures 1990-2026 (Legacy mode, TODO row 142, phase
## L6): data/legacy/fixtures.csv, built from the AFL Tables season pages by
## tools/legacy_fixtures/build.py and checked by tools/check_legacy_fixtures.py.
##
## Director, 2026-11-13: every real season plays its real fixture (rounds,
## matchups, grounds, days); the generator draws the season after 2026, and
## whenever the sim's clubs differ from that year's real clubs (Fitzroy
## surviving the merger, a created club). So a season gets its real fixture
## only when its clubs are exactly the clubs that played that year.
##
## A round is an Array of matches {"home", "away", "ground", "date"}, the shape
## Season.build_fixture draws plus the real ground and date.

const PATH := "res://data/legacy/fixtures.csv"

static var _by_year := {}   # year -> Array of rounds, in round order
static var _clubs := {}     # year -> sorted Array of the clubs that played
static var _loaded := false


## Whether the table has a fixture for `year`.
static func has_year(year: int) -> bool:
	_load()
	return _by_year.has(year)


## The clubs that played `year`, sorted ([] for a year with no fixture).
static func clubs_for(year: int) -> Array:
	_load()
	return (_clubs.get(year, []) as Array).duplicate()


## `year`'s real rounds when `clubs` are exactly that year's clubs, else []
## (draw the season instead). A fresh copy: a season may edit its own.
static func for_season(year: int, clubs: Array) -> Array:
	_load()
	if not _by_year.has(year):
		return []
	var mine := clubs.map(func(c): return str(c))
	mine.sort()
	if mine != _clubs[year]:
		return []
	return (_by_year[year] as Array).duplicate(true)


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	_by_year = {}
	_clubs = {}
	if not FileAccess.file_exists(PATH):
		push_error("RealFixture: missing %s" % PATH)
		return
	var f := FileAccess.open(PATH, FileAccess.READ)
	if f == null:
		return
	var head := Array(f.get_csv_line())
	var rounds := {}   # year -> {round number -> Array of matches}
	var clubs := {}    # year -> {code: true}
	while not f.eof_reached():
		var cells := Array(f.get_csv_line())
		if cells.size() < head.size():
			continue
		var r := {}
		for i in range(head.size()):
			r[head[i]] = str(cells[i])
		var y := int(r["year"])
		var n := int(r["round"])
		if not rounds.has(y):
			rounds[y] = {}
			clubs[y] = {}
		if not (rounds[y] as Dictionary).has(n):
			rounds[y][n] = []
		(rounds[y][n] as Array).append({"home": r["home"], "away": r["away"],
				"ground": r["ground"], "date": r["date"]})
		clubs[y][r["home"]] = true
		clubs[y][r["away"]] = true
	f.close()
	for y in rounds:
		var nums: Array = (rounds[y] as Dictionary).keys()
		nums.sort()
		var out := []
		for n in nums:
			out.append(rounds[y][n])
		_by_year[y] = out
		var cs: Array = (clubs[y] as Dictionary).keys()
		cs.sort()
		_clubs[y] = cs
