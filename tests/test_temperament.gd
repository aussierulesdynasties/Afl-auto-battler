extends RefCounted
## Player temperaments (Temperament.gd, relationship overhaul phase 1): the
## data file, every player at every club holding one or two that never clash,
## the same ones every start, grounded in the record, the levers other
## systems read, and the save keeping them.
## Run through tests/run_temperament_tests.gd.

var failures: Array[String] = []
var checks := 0
const SUITE_SEED := 2027


func run() -> void:
	failures.clear()
	checks = 0
	GameState.replay_seed = SUITE_SEED
	_t("_test_data")
	_t("_test_scale")
	_t("_test_reactions")
	_t("_test_stored_values")
	_t("_test_every_player")
	_t("_test_same_every_start")
	_t("_test_grounded")
	_t("_test_saved")
	GameState.delete_saved_career()
	GameState.replay_seed = 0
	print(Ran.line("Temperament", self))


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)


## Eight temperaments, each with its words; levers are only the known ones,
## and a clash goes both ways.
func _test_data() -> void:
	var keys := Temperament.keys()
	_check(keys.size() == 8, "Eight temperaments (%d)" % keys.size())
	for k in ["clubman", "mercenary", "competitor", "mercurial", "professional", "fiery", "leader", "quiet_achiever"]:
		_check(keys.has(k), "%s is a temperament" % k)
	for k in keys:
		_check(Temperament.label(k) != "" and Temperament.describe(k) != "" and Temperament.ambition(k) != "",
				"%s has a label, a description and an ambition" % k)
		for c in Temperament.clashes(k):
			_check(Temperament.clashes(str(c)).has(k), "%s and %s clash both ways" % [k, c])
	var raw = JSON.parse_string(FileAccess.get_file_as_string(Temperament.PATH))
	for k in keys:
		for lever in (raw["temperaments"][k]["levers"] as Dictionary):
			_check(Temperament.LEVERS.has(lever), "%s's lever %s is one other systems know" % [k, lever])
	_check(Temperament.label("nonsense") == "" and not Temperament.is_key("nonsense"), "An unknown key has no words")


func _test_scale() -> void:
	var p := {"id": "t1", "temperament": ["clubman"]}
	_check(is_equal_approx(Temperament.scale(p, "promise_broken"), 1.4), "A clubman feels a broken promise 1.4x")
	_check(is_equal_approx(Temperament.scale(p, "dropped"), 1.0), "A lever his temperament doesn't move is 1.0")
	_check(is_equal_approx(Temperament.scale(p, "not_a_lever"), 1.0), "An unknown lever is 1.0")
	p["temperament"] = ["clubman", "leader"]
	_check(is_equal_approx(Temperament.scale(p, "promise_broken"), 1.4 * 1.25), "Two temperaments multiply")
	p["temperament"] = ["mercenary"]
	_check(Temperament.scale(p, "bond") < 1.0 and Temperament.scale(p, "decay") > 1.0,
			"A mercenary cares less for his mates and gets over things faster")
	_check(Temperament.has(p, "mercenary") and not Temperament.has(p, "clubman"), "has() reads his temperaments")


func _test_reactions() -> void:
	var p := {"id": "t2", "temperament": ["clubman"]}
	var r := Temperament.reactions(p)
	_check(not r.is_empty(), "A clubman's reactions are listed")
	var texts := r.map(func(e): return str(e["text"]))
	_check(texts.has("A broken promise counts 40% more with him."), "The broken-promise line gives the exact size (%s)" % [texts])
	_check(texts.has("He holds on to things 20% longer."), "The decay line reads in football words (%s)" % [texts])


## A stored list is cleaned: unknown keys and repeats go, and a player left
## with none is given his own.
func _test_stored_values() -> void:
	var p := {"id": "t3", "temperament": ["clubman", "clubman"]}
	_check(Temperament.of(p) == ["clubman"], "A repeat is dropped")
	p["temperament"] = ["nonsense"]
	var got := Temperament.of(p)
	_check(got.size() >= 1 and got.size() <= 2 and Temperament.is_key(str(got[0])), "An unknown key is replaced (%s)" % [got])
	var q := {"id": "t4"}
	_check(Temperament.ensure_all([q]) == 1 and q.get("temperament") is Array, "ensure_all() gives a bare player one")
	_check(Temperament.ensure_all([q]) == 0, "and leaves him alone the second time")


func _league() -> Array:
	var all: Array = []
	for code in GameState.season.lists:
		all.append_array(GameState.season.lists[code])
	return all


## Every player at all 18 clubs holds one or two, never a clashing pair, and
## no temperament is missing from the league or owns it.
func _test_every_player() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	_check(GameState.season.lists.size() >= 18, "Every club is listed (%d)" % GameState.season.lists.size())
	var count := {}
	var two := 0
	var bare := 0
	var bad := 0
	var all := _league()
	for p in all:
		var have = p.get("temperament")
		if not (have is Array) or (have as Array).is_empty() or (have as Array).size() > 2:
			bare += 1
			continue
		if have.size() == 2:
			two += 1
			if Temperament.clashes(str(have[0])).has(str(have[1])):
				bad += 1
		for k in have:
			count[k] = int(count.get(k, 0)) + 1
	_check(bare == 0, "Every listed player holds a temperament at the start (%d without, of %d)" % [bare, all.size()])
	_check(bad == 0, "No player holds two that clash (%d)" % bad)
	var share := float(two) / float(maxi(1, all.size()))
	_check(share > 0.3 and share < 0.7, "About half hold two (%.0f%%)" % (share * 100.0))
	for k in Temperament.keys():
		var s := float(count.get(k, 0)) / float(maxi(1, all.size()))
		_check(s > 0.04 and s < 0.4, "%s is held by a fair share of the league (%.0f%%)" % [k, s * 100.0])
	print("Temperament shares: %s of %d players, %d with two" % [count, all.size(), two])
	_check(GameState.free_agents.all(func(p): return p.get("temperament") is Array), "Free agents hold one")


## The same player gets the same temperaments each time a career starts.
func _test_same_every_start() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var first := {}
	for p in _league():
		first[str(p["id"])] = (p["temperament"] as Array).duplicate()
	GameState.reset()
	Temperament.reload()
	GameState.start_season("COL", GameDB.club_list("COL"))
	var same := 0
	var seen := 0
	for p in _league():
		var id := str(p["id"])
		if first.has(id):
			seen += 1
			if first[id] == p["temperament"]:
				same += 1
	_check(seen > 500 and same == seen, "Every player's temperament is the same on a second start (%d of %d)" % [same, seen])


## The record tilts it: named captains lead, poorly disciplined players run hot.
func _test_grounded() -> void:
	var all := _league()
	var caps := 0
	var cap_lead := 0
	var hot := 0
	var hot_fiery := 0
	var fiery := 0
	for p in all:
		var t: Array = p["temperament"]
		if t.has("fiery"):
			fiery += 1
		if Leadership.role_2026(p) == "captain":
			caps += 1
			if t.has("leader"):
				cap_lead += 1
		if float((p.get("attr", {}) as Dictionary).get("discipline", 50)) <= 25.0:
			hot += 1
			if t.has("fiery"):
				hot_fiery += 1
	_check(caps >= 10 and cap_lead == caps, "Every named captain is a leader (%d of %d)" % [cap_lead, caps])
	var league_fiery := float(fiery) / float(maxi(1, all.size()))
	_check(hot >= 5 and float(hot_fiery) / hot > 2.0 * league_fiery,
			"Poor discipline makes a fiery player far more likely (%d of %d, league %.0f%%)" % [hot_fiery, hot, league_fiery * 100.0])


## Temperaments are kept in the save, unchanged.
func _test_saved() -> void:
	GameState.reset()
	GameState.start_season("GEE", GameDB.club_list("GEE"))
	var want := {}
	for p in _league():
		want[str(p["id"])] = (p["temperament"] as Array).duplicate()
	_check(GameState.save_career() and GameState.load_career(), "The career saves and loads")
	var same := 0
	for p in _league():
		if want.get(str(p["id"])) == p.get("temperament"):
			same += 1
	_check(same == want.size(), "Every player keeps his temperaments through a reload (%d of %d)" % [same, want.size()])
