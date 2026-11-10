class_name SeasonTale
extends RefCounted
## The shape of a season in one sentence, for the almanac's story of the season
## (row 145; procedural copy research §8, the second slice of the story layer).
## Built like the career story (CareerTale.gd): record() reads the results,
## beats() proves the angles the record supports, tell() keeps the strongest and
## sentence() writes it from the phrase bank (data/tales/season.json), in the
## senior coach's voice. No language model, no clock, no dice: one season
## always reads the same.
##
## What the almanac keeps (entry["arc"], Almanac.ARC_KEY):
##   form    your home-and-away results in order, one letter a game ("WWLDW...")
##   rounds  the round each of those games was played in (a bye leaves a gap)
##   finals  your finals in order, the same letters
##   angle   the angle told, and
##   facts   every number its sentence uses
## A season with no shape worth a sentence keeps the record and no angle, and
## nothing is said. Every number in a sentence is one of its facts, and every
## fact is counted from form, rounds and finals.
##
## Angles:
##   run_to_flag  won the last RUN or more games, the Grand Final the last
##   surge, fade  the win rate moved SWING points or more between the two
##                halves of the home-and-away season
##   won_first, lost_first, lost_last, win_run, lose_run
##                RUN or more wins or losses on end

const FILE := "res://data/tales/season.json"
## Fewer home-and-away games than this is too short a season to have a shape.
const MIN_GAMES := 10
## The halves' win rates differ by this many percentage points or more.
const SWING := 30
## This many wins or losses on end is a run worth a sentence.
const RUN := 6
## How much each angle matters when more than one is true.
const WEIGHT := {"run_to_flag": 10, "surge": 8, "fade": 8, "won_first": 7, "lost_first": 7,
		"lost_last": 7, "win_run": 6, "lose_run": 6}

static var _bank: Dictionary = {}


## The phrase bank's angles, loaded once. The same shape as the career story's
## bank, so CareerTale.validate checks it.
static func bank() -> Dictionary:
	if _bank.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if parsed is Dictionary and (parsed as Dictionary).get("angles") is Dictionary:
			_bank = parsed["angles"]
	return _bank


## Your season's record from its results. `rounds` is Season.results (one array
## of results a round), `finals_weeks` Season.finals["weeks"], `my` your club.
static func record(rounds: Array, finals_weeks: Array, my: String) -> Dictionary:
	var form := ""
	var played := []
	for i in rounds.size():
		for res in (rounds[i] if rounds[i] is Array else []):
			var c := _letter(res, my)
			if c != "":
				form += c
				played.append(i + 1)
	var fin := ""
	for week in finals_weeks:
		for res in (week if week is Array else []):
			fin += _letter(res, my)
	return {"form": form, "rounds": played, "finals": fin}


## "W", "L" or "D" for your side of a result; "" when it is not your match.
static func _letter(res, my: String) -> String:
	if not (res is Dictionary):
		return ""
	var s = res.get("score", [])
	if not (s is Array) or (s as Array).size() < 2:
		return ""
	var mine := -1
	if str(res.get("home", "")) == my:
		mine = 0
	elif str(res.get("away", "")) == my:
		mine = 1
	if mine < 0:
		return ""
	if int(s[mine]) > int(s[1 - mine]):
		return "W"
	return "L" if int(s[mine]) < int(s[1 - mine]) else "D"


## Every angle the record proves: [{angle, facts, weight}].
static func beats(rec: Dictionary, flag: bool) -> Array:
	var form := str(rec.get("form", ""))
	var rounds: Array = rec.get("rounds", []) if rec.get("rounds") is Array else []
	var n := form.length()
	if n < MIN_GAMES or rounds.size() != n:
		return []
	var out := []
	# The two halves of the home-and-away season.
	var half := n >> 1
	var first := form.substr(0, half)
	var late := form.substr(half)
	var fw := first.count("W")
	var lw := late.count("W")
	var swing := int(floor(lw * 100.0 / late.length()) - floor(fw * 100.0 / half))
	if absi(swing) >= SWING:
		out.append(_beat("surge" if swing > 0 else "fade", {"first_w": fw, "first_l": first.count("L"),
				"first_d": first.count("D"), "split_round": int(rounds[half - 1]), "late_w": lw,
				"late_n": late.length()}, absi(swing)))
	# The longest runs, finals included.
	var all := form + str(rec.get("finals", ""))
	var won := _longest(all, "W")
	if int(won["run"]) >= RUN:
		var run := int(won["run"])
		var at := int(won["at"])
		if flag and at + run == all.length():
			out.append(_beat("run_to_flag", {"run": run}, run))
		elif at == 0:
			out.append(_beat("won_first", {"run": run}, run))
		else:
			out.append(_beat("win_run", {"run": run, "from_round": int(rounds[at])}, run))
	var lost := _longest(all, "L")
	if int(lost["run"]) >= RUN:
		var run := int(lost["run"])
		var at := int(lost["at"])
		if at == 0:
			out.append(_beat("lost_first", {"run": run}, run))
		elif at + run == all.length():
			out.append(_beat("lost_last", {"run": run}, run))
		else:
			out.append(_beat("lose_run", {"run": run, "from_round": int(rounds[at])}, run))
	return out


## The longest run of `c` in `s`, the earliest when two are as long: {run, at}.
static func _longest(s: String, c: String) -> Dictionary:
	var best := {"run": 0, "at": 0}
	var run := 0
	for i in s.length():
		run = run + 1 if s[i] == c else 0
		if run > int(best["run"]):
			best = {"run": run, "at": i - run + 1}
	return best


## `size` separates two beats of one weight: the bigger swing or the longer run.
static func _beat(angle: String, facts: Dictionary, size: int) -> Dictionary:
	return {"angle": angle, "facts": facts, "weight": float(WEIGHT[angle]) + size / 1000.0}


## What the almanac keeps for the season: the record, and the strongest angle
## with its facts when there is one.
static func tell(rec: Dictionary, flag: bool) -> Dictionary:
	var out := rec.duplicate(true)
	var best := {}
	for b in beats(rec, flag):
		if best.is_empty() or float(b["weight"]) > float(best["weight"]):
			best = b
	if not best.is_empty():
		out["angle"] = str(best["angle"])
		out["facts"] = best["facts"]
	return out


## The sentence for a kept arc, "" when the season has none (or the page is
## from before this was kept). `year` and `club` pick the phrase, so a season
## always reads the same.
static func sentence(arc: Dictionary, year: int, club: String) -> String:
	var angle := str(arc.get("angle", ""))
	var f = arc.get("facts", {})
	var def: Dictionary = bank().get(angle, {}) if angle != "" else {}
	var phrases: Array = def.get("coach", [])
	if phrases.is_empty() or not (f is Dictionary):
		return ""
	var slots := {}
	for s in def.get("slots", []):
		slots[s] = _slot(str(s), f)
	return str(phrases[absi(hash("season|%d|%s|%s" % [year, club, angle])) % phrases.size()]).format(slots)


## A slot's words, made from the facts alone.
static func _slot(slot: String, f: Dictionary) -> String:
	match slot:
		"first_rec":
			var rec := "%d-%d" % [int(f.get("first_w", 0)), int(f.get("first_l", 0))]
			return rec if int(f.get("first_d", 0)) == 0 else "%s-%d" % [rec, int(f["first_d"])]
		"split":
			return "Round %d" % int(f.get("split_round", 0))
		"late_won":
			return "none" if int(f.get("late_w", 0)) == 0 else str(int(f["late_w"]))
		"late_n":
			return str(int(f.get("late_n", 0)))
		"run":
			return str(int(f.get("run", 0)))
		"from":
			return "Round %d" % int(f.get("from_round", 0))
	return ""
