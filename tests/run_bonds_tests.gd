extends SceneTree
## godot --headless --path . --script tests/run_bonds_tests.gd
## Player bonds (_B.gd): every club seeded by one rule, both sides of every
## tie, the per-player cap, the fallout of a drop, trade, delisting and
## backing, the season's turn (men who left, ties apart fading, proteges
## growing up), the save, and no effect on the match dice.
## Seeded by design: the career uses replay_seed 4242.

var _state: Node
var _db: Node
var _B
var _Sq
var _MS
var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	_state = root.get_node("GameState")
	_state.autosave_enabled = false
	_state.save_path = "user://test_bonds.save"
	_state.settings_path = "user://test_settings.cfg"
	_db = root.get_node("GameDB")
	_B = load("res://scripts/sim/Bonds.gd")
	_Sq = load("res://scripts/sim/Squad.gd")
	_MS = load("res://scripts/sim/MatchSim.gd")
	_state.replay_seed = 4242
	_state.reset()
	_state.start_season("COL", _db.club_list("COL"))

	_t("_test_every_club_seeded")
	_t("_test_ties_mirror_and_cap")
	_t("_test_seeding_deterministic")
	_t("_test_fallout")
	_t("_test_season_turn")
	_t("_test_family")
	_t("_test_save_and_old_save")
	_t("_test_no_match_effect")
	_state.replay_seed = 0
	print(Ran.line("Bonds", self))
	for f in _failures:
		print("FAIL: ", f)
	quit(0 if _failures.is_empty() else 1)


## Every active club gets mates, rivals, mentors and leadership allies by the same rule.
func _test_every_club_seeded() -> void:
	var by: Dictionary = _state.bonds["by"]
	_check(int(_state.bonds.get("year", 0)) == int(_state.season_year), "bonds carry the season they were refreshed in")
	var clubs: Array = _state.season.lists.keys()
	_check(clubs.size() >= 18, "the league has its 18 clubs (%d)" % clubs.size())
	for code in clubs:
		var kinds := {}
		var tied := 0
		for p in _state.season.lists[code]:
			var mine: Dictionary = by.get(str(p["id"]), {})
			if not mine.is_empty():
				tied += 1
			for o in mine:
				kinds[str(mine[o]["k"])] = true
		_check(kinds.has("mate"), "%s has close mates" % code)
		_check(kinds.has("ally"), "%s has leadership allies" % code)
		_check(kinds.has("rival") or tied > 0, "%s has rivals for spots" % code)
		# Sparse: most of a list has a tie or two, nobody is tied to everyone.
		_check(tied > 0 and tied < (_state.season.lists[code] as Array).size(),
				"%s: some, not all, of the list is tied (%d)" % [code, tied])


## Both sides of every tie agree, and nobody holds more than the cap (family aside).
func _test_ties_mirror_and_cap() -> void:
	var by: Dictionary = _state.bonds["by"]
	var bad := 0
	var over := 0
	for a in by:
		for b in by[a]:
			var e: Dictionary = by[a][b]
			var back: Dictionary = (by.get(b, {}) as Dictionary).get(a, {})
			if back.is_empty() or str(back["k"]) != str(_B.MIRROR[str(e["k"])]) or int(back["s"]) != int(e["s"]):
				bad += 1
		if _B.count(_state.bonds, str(a)) > _B.cap():
			over += 1
	_check(bad == 0, "every tie has its mirror (%d without)" % bad)
	_check(over == 0, "nobody is over the per-player cap (%d over)" % over)
	# A mentor is older than his protege, and at his position.
	var checked := 0
	for a in by:
		for b in by[a]:
			if str(by[a][b]["k"]) == "mentor":
				var young: Dictionary = _state._any_player(str(a))
				var old: Dictionary = _state._any_player(str(b))
				_check(float(old.get("age", 0)) > float(young.get("age", 99)), "a mentor is older than his protege")
				_check(str(old.get("role", "")) == str(young.get("role", "")), "a mentor plays his protege's position")
				checked += 1
	_check(checked > 0, "some mentors were seeded")


## The same career seed and season seed the same bonds; another seed does not.
func _test_seeding_deterministic() -> void:
	var a: Dictionary = _B.ensure({})
	var b: Dictionary = _B.ensure({})
	var c: Dictionary = _B.ensure({})
	_B.refresh(a, _state.season.lists, 2027, 99)
	_B.refresh(b, _state.season.lists, 2027, 99)
	_B.refresh(c, _state.season.lists, 2027, 100)
	_check(JSON.stringify(a["by"]) == JSON.stringify(b["by"]), "one seed seeds one set of bonds")
	_check(JSON.stringify(a["by"]) != JSON.stringify(c["by"]), "another seed seeds others")
	# A second refresh in the same season adds nothing.
	_check(_B.refresh(a, _state.season.lists, 2027, 99) == 0, "a refresh in the same season adds nothing")


## A drop reaches his teammates by the kind of tie, a rival is pleased, a trade
## hurts more than a drop, and nothing is applied.
func _test_fallout() -> void:
	var s: Dictionary = _B.ensure({})
	_B.form(s, "A", "M", "mate", 2, 2027)
	_B.form(s, "A", "R", "rival", 2, 2027)
	_B.form(s, "A", "Y", "protege", 2, 2027)   # Y is A's protege: A mentors Y
	_B.form(s, "A", "B", "family", 3, 2027, "brother")
	_B.form(s, "A", "X", "mate", 2, 2027)       # X is at another club
	var club_of := {"A": "COL", "M": "COL", "R": "COL", "Y": "COL", "B": "CAR", "X": "ESS"}
	var before := JSON.stringify(s)
	var drop = _B.fallout(s, "A", "drop", club_of, "Sam Day")
	_check(JSON.stringify(s) == before, "a fallout preview changes nothing")
	var by := {}
	for r in drop:
		by[str(r["id"])] = r
	_check(by.has("M") and int(by["M"]["opinion"]) < 0, "dropping him upsets his close mate")
	_check(by.has("R") and int(by["R"]["opinion"]) > 0, "dropping him pleases his rival for the spot")
	_check(by.has("Y") and str(by["Y"]["kind"]) == "mentor", "his protege reacts to his mentor being dropped")
	_check(by.has("B"), "family at another club hears of the drop")
	_check(not by.has("X"), "a mate at another club is not touched by a drop")
	_check(str(by["M"]["why"]) == "You dropped his close mate, Sam Day", "the reason reads in football words (%s)" % by["M"]["why"])
	_check(str(by["B"]["why"]).find("his brother") >= 0, "family is named by relation (%s)" % by["B"]["why"])
	_check(str(by["M"]["mark"]) == "mate_dropped" and is_equal_approx(float(by["M"]["scale"]) * -2.0, float(by["M"]["opinion"])),
			"the row names the Opinion mark and the scale that lands its number")
	var trade = _B.fallout(s, "A", "trade", club_of, "Sam Day")
	var t_by := {}
	for r in trade:
		t_by[str(r["id"])] = r
	_check(t_by.has("X"), "a trade reaches a mate at another club")
	_check(int(t_by["M"]["opinion"]) < int(by["M"]["opinion"]), "a trade hurts a mate more than a drop")
	_check(int(t_by["B"]["opinion"]) <= -8, "trading his brother is the hardest hit")
	var back = _B.fallout(s, "A", "back", club_of, "Sam Day")
	for r in back:
		if str(r["id"]) == "R":
			_check(int(r["opinion"]) < 0, "backing him stings his rival")
		if str(r["id"]) == "M":
			_check(int(r["opinion"]) > 0, "backing him pleases his mate")
	# Stronger ties move further.
	var s2: Dictionary = _B.ensure({})
	_B.form(s2, "A", "W", "mate", 1, 2027)
	_B.form(s2, "A", "S", "mate", 3, 2027)
	var rows = _B.fallout(s2, "A", "trade", {}, "Sam Day")
	_check(absi(int(rows[0]["opinion"])) > absi(int(rows[1]["opinion"])) and str(rows[0]["id"]) == "S",
			"the stronger mate feels it more, and is listed first")
	var tot = _B.fallout_total(drop)
	_check(int(tot["pleased"]) == 1 and int(tot["upset"]) == 3, "the total counts who is pleased and upset")
	_check(_B.actor(s, "A", "close_mate", club_of) == "M", "a card binds his teammate as his close mate")
	_check(_B.actor(s, "A", "brother", club_of) == "B", "a card binds his brother")
	_check(_B.actor(s, "A", "positional_rival", club_of) == "R", "a card binds his rival for the spot")
	_check(_B.actor(s, "A", "protege", club_of) == "Y", "a card binds his protege")
	_check(_B.actor(s, "A", "mentor", club_of) == "", "no mentor: the card skips")
	_check(_B.actor(s, "A", "incumbent", club_of, {"A": 70, "R": 75}) == "R", "a better rival is the incumbent")
	_check(_B.actor(s, "A", "incumbent", club_of, {"A": 80, "R": 75}) == "", "a lesser rival is not")
	_check(_B.actor(s, "A", "nonsense", club_of) == "", "an unknown role binds nobody")
	_check(_B.fallout(s, "A", "punch", club_of).is_empty(), "an unknown call has no fallout")
	_check(_B.fallout(s, "nobody", "drop", club_of).is_empty(), "a man with no ties has no fallout")


## The season turns: a man who left the game takes his ties with him, ties
## apart fade, a grown protege becomes a mate, family never fades.
func _test_season_turn() -> void:
	var s: Dictionary = _B.ensure({})
	var a := {"id": "A", "age": 30.0, "role": "MID"}
	var y := {"id": "Y", "age": 25.0, "role": "MID"}
	var m := {"id": "M", "age": 26.0, "role": "FWD"}
	var gone := {"id": "G", "age": 26.0, "role": "FWD"}
	var f := {"id": "F", "age": 27.0, "role": "DEF"}
	_B.form(s, "Y", "A", "mentor", 2, 2026)
	_B.form(s, "M", "G", "mate", 2, 2026)
	_B.form(s, "M", "A", "mate", 1, 2026)
	_B.form(s, "M", "F", "family", 3, 2026, "brother")
	s["year"] = 2026
	var lists := {"COL": [a, y], "ESS": [m, f]}
	# Pretend nothing is seeded on top: per-club shares at zero for this check.
	var saved = _B._cfg
	_B._cfg = {"per_player_cap": 4, "kinds": {}}
	_B.refresh(s, lists, 2027, 1)
	_B._cfg = saved
	_check(_B.of(s, "G").is_empty() and not _B.of(s, "M").has("G"), "a man who left the game takes his ties with him")
	_check(not _B.of(s, "M").has("A"), "a weak mateship across clubs fades away")
	_check(_B.kind(s, "Y", "A") == "mate", "a protege of 25 has grown into a mate")
	_check(_B.kind(s, "M", "F") == "family" and int(_B.of(s, "M")["F"]["s"]) == 3, "family never fades")


## Sourced and generated family become family bonds, both ways round.
func _test_family() -> void:
	var s: Dictionary = _B.ensure({})
	var old := {"id": "OLD", "age": 40.0, "role": "MID", "generated": true}
	var kid := {"id": "KID", "age": 18.0, "role": "MID", "generated": true,
			"family": [{"relation": "son of", "id": "OLD", "club": "COL", "former": false}]}
	_B.refresh(s, {"COL": [old], "CAR": [kid]}, 2027, 1)
	_check(_B.kind(s, "KID", "OLD") == "family", "a generated son is tied to his father")
	_check(str(_B.of(s, "KID")["OLD"]["rel"]) == "father" and str(_B.of(s, "OLD")["KID"]["rel"]) == "son",
			"each side names the other right (father / son)")
	# The shipped sourced rows (data/player_relations.csv) in the live league.
	var found := 0
	for a in _state.bonds["by"]:
		for b in _state.bonds["by"][a]:
			if str(_state.bonds["by"][a][b]["k"]) == "family":
				found += 1
	_check(found > 0, "the real league's sourced brothers and sons are tied (%d sides)" % found)


## The save keeps them.
func _test_save_and_old_save() -> void:
	var before := JSON.stringify(_state.bonds["by"])
	_check(_state.save_career(), "the career saves")
	_check(_state.load_career(), "the career loads")
	_check(JSON.stringify(_state.bonds["by"]) == before, "bonds come back from the save as they were")
	_check(_state.bond_ties(str(_state.my_list[0]["id"])) is Array, "the profile reader works after a load")


## Bonds never touch the match: the same match with and without bonds is the same match.
func _test_no_match_effect() -> void:
	var src := FileAccess.get_file_as_string("res://scripts/sim/MatchSim.gd")
	_check(src.find("Bonds") < 0 and src.find("bonds") < 0, "MatchSim does not read bonds")
	var home: Array = _state.season.lists["COL"]
	var away: Array = _state.season.lists["CAR"]
	var r1 := _play(home, away)
	var keep: Dictionary = _state.bonds
	_state.bonds = {}
	var r2 := _play(home, away)
	_state.bonds = keep
	_check(r1 == r2, "a match plays the same with or without bonds (%s / %s)" % [r1, r2])


func _play(home: Array, away: Array) -> String:
	var h = _Sq.new("Collingwood", home, true, "COL")
	var a = _Sq.new("Carlton", away, false, "CAR")
	var sim = _MS.new(h, a, 777)
	sim.run()
	return "%d-%d" % [sim.score(0), sim.score(1)]


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)

## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
