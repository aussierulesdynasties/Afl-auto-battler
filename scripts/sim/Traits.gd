class_name Traits
extends RefCounted
## Player traits and line synergies.
##
## A trait is earned from a player's current stats (so training can unlock
## one), and does one specific thing in a match. A player earns every good
## trait whose line he clears, up to five (director, 2026-11-12), plus Hothead
## if his discipline is poor. Synergies switch on
## when a line of the selected 18 carries the right mix of traits - so who
## you draft, trade for and pick matters beyond the overall rating.

## key -> label, the stat and threshold that earn it, the roles it counts
## for ([] = any), what it does, and how a recruiter would put it ("scout").
## "max" marks a bad trait (at or below).
const DEFS := {
	"ball_magnet": {"label": "Ball magnet", "stat": "disposal", "min": 86, "roles": ["MID", "DEF"],
			"text": "Wins 10% more of the ball in general play.",
			"scout": "Finds the footy all day."},
	"bull": {"label": "Contested bull", "stat": "contested", "min": 84, "roles": ["MID", "RUCK"],
			"text": "Wins 15% more clearances and keeps the ball when tackled more often.",
			"scout": "Wins it at the coalface and gets it out."},
	"ruck_king": {"label": "Ruck king", "stat": "ruck", "min": 84, "roles": ["RUCK"],
			"text": "Takes 5% more of the hit-outs.",
			"scout": "Dominates the hit-outs."},
	"aerial": {"label": "Aerial threat", "stat": "marking", "min": 76, "roles": ["FWD"],
			"text": "Marks 6% more of the forward-50 contests he leads to.",
			"scout": "A strong contested mark inside 50."},
	"crumber": {"label": "Crumber", "stat": "goalkicking", "min": 55, "roles": ["FWD"], "small": true,
			"text": "A small forward: twice as often the one at the fall of the ball, and kicks 12% more goals from ground balls.",
			"scout": "Lives at the feet of the pack."},
	"sharpshooter": {"label": "Sharpshooter", "stat": "accuracy", "min": 71, "roles": [],
			"text": "+6% goal chance on every shot.",
			"scout": "Reliable set shot."},
	"playmaker": {"label": "Playmaker", "stat": "creating", "min": 75, "roles": [],
			"text": "Shots from his inside-50 deliveries are 5% more likely to be goals.",
			"scout": "Sets up goals with his ball use going inside 50."},
	"interceptor": {"label": "Interceptor", "stat": "intercept", "min": 80, "roles": ["DEF"],
			"text": "Spoils 5% more of the forward-50 contests he is in.",
			"scout": "Reads the play and cuts off forward entries."},
	"lockdown": {"label": "Lockdown", "stat": "pressure", "min": 64, "roles": ["DEF", "MID"],
			"text": "His opponent's shots are 4% less likely to be goals (a midfielder picks up their best midfielder).",
			"scout": "Can shut down a dangerous opponent."},
	"def_forward": {"label": "Defensive forward", "stat": "pressure", "min": 44, "roles": ["FWD"], "own_role": true,
			"text": "Sent to their loose defender, he keeps him out of most contests (another forward follows him less well).",
			"scout": "Works up the ground and keeps a loose defender honest."},
	"engine": {"label": "Engine", "stat": "durability", "min": 91, "roles": [],
			"text": "Tires 25% slower.",
			"scout": "Runs all day."},
	"big_game": {"label": "Big-game player", "stat": "star", "min": 60, "roles": [],
			"text": "Lifts in the last quarter and in finals (+5% on every stat).",
			"scout": "Lifts when it matters: last quarters and finals."},
	"hothead": {"label": "Hothead", "stat": "discipline", "max": 20, "roles": [],
			"text": "Gives away 50% more clangers and free kicks.",
			"scout": "Gives away too many free kicks."},
}

## key -> label, the line it needs ("" = the whole 18), the traits needed,
## the match effect, and the same in football words ("about", "does").
const SYNERGIES := {
	"engine_room": {"label": "Engine room", "line": "", "needs": {"bull": 4}, "power": 0.05,
			"text": "+5% stoppage wins.",
			"about": "Contested bulls who win the stoppages together.", "does": "Wins more of the stoppages."},
	"tall_small": {"label": "Tall-small forward line", "line": "FWD", "needs": {"aerial": 2, "crumber": 2}, "power": 1.15,
			"text": "+15% goal chance on every forward-50 shot.",
			"about": "Aerial threats up forward with crumbers at their feet.", "does": "More goals from forward-50 entries."},
	"intercept_wall": {"label": "Intercept wall", "line": "DEF", "needs": {"interceptor": 2, "lockdown": 1}, "power": 0.84,
			"text": "-16% on the opposition's goal chance.",
			"about": "Interceptors who read the ball in the air down back, with a stopper on the lead.", "does": "The opposition kick fewer goals."},
	"lockdown_unit": {"label": "Lockdown unit", "line": "", "needs": {"lockdown": 3}, "power": 1.15,
			"text": "+15% pressure on the opposition.",
			"about": "A side full of stoppers who squeeze the opposition.", "does": "Puts more pressure on the ball."},
	"supply_line": {"label": "Supply line", "line": "", "needs": {"ball_magnet": 3, "playmaker": 1}, "power": 1.22,
			"text": "+22% metres gained per disposal.",
			"about": "Ball-users feeding a playmaker going forward.", "does": "Gains more ground with every disposal."},
	"running_machine": {"label": "Running machine", "line": "", "needs": {"engine": 3}, "power": 0.50,
			"text": "The whole side tires 50% slower.",
			"about": "A side of endurance runners.", "does": "The whole side tires more slowly."},
}

## Born, not trained (director, 2026-10-08): a player whose game defies his
## size - a key-position body with a small player's game, or one who plays
## every job - extremely rare. A hand-picked few (GameDB.UNICORNS) and about
## one tall prospect in two or three draft classes; flagged p["unicorn"]. He
## can be picked at forward, midfield and back. On the ground he also
## fills one missing slot in one synergy (director, 2026-10-06): the first, in
## SYNERGIES order, that it completes, in his line for a line synergy. He never
## switches on two, and never one that needs more than the one slot.
const EARNED := {
	"unicorn": {"label": "Unicorn", "text": "Plays forward, midfield and back. On the ground he can fill one missing place in one synergy.",
			"scout": "Can play anywhere on the ground."},
	"fine_wine": {"label": "Fine Wine",
			"text": "Ages three years slower: his decline starts three years later and is 30% gentler, and he retires up to three years later (40 at the latest).",
			"scout": "Gets better with age.",
			"earn": "Born with it, not trained: every real player who played 60 or more games in seasons he turned 32 or older, and about 1 draftee in 52."},
}
const UNICORN_LINES := ["FWD", "MID", "DEF"]

## The wet-weather player (ARD-M4-016, the director's call): a contested
## ball-winner with clean hands. Earned from the stats like any trait, but on
## top of the five, so it never pushes another trait or a synergy out; it does
## something only when it's wet.
const WET_WEATHER := {"label": "Wet-weather player", "contested": 78, "disposal": 72,
		"text": "In the wet: wins 10% more of the ball and makes 20% fewer clangers.",
		"scout": "Thrives when it's greasy."}
const WET_BALL := 1.10
const WET_CLANGERS := 0.80


## Real players the published evidence names as better in the wet
## (docs/research/WET_WEATHER_PLAYERS.md, #444). They have it by name; everyone
## else earns it by the stat rule (the director: "Evidence + stats",
## 2026-10-06). Their wet record isn't in their ratings.
## Keyed by the real list's id and name together, so a created player who
## happens to share a name never inherits it.
const WET_NAMED := {"GWS_6": "Lachie Whitfield", "GEE_35": "Patrick Dangerfield"}


static func wet_weather(p: Dictionary) -> bool:
	if str(WET_NAMED.get(str(p.get("id", "")), "-")) == str(p.get("real_name", "")):
		return true
	var attr: Dictionary = p.get("attr", {})
	return int(attr.get("contested", 0)) >= int(WET_WEATHER["contested"]) 			and int(attr.get("disposal", 0)) >= int(WET_WEATHER["disposal"])


## Fine Wine (director, 2026-11-13: "when a player has unnatural longevity
## like Zorko, Gawn, Pendlebury etc / every draftee should have a very slim
## chance of possessing the trait too"). Born, not trained, and on top of the
## five like Unicorn. A real player has it when the director approved him
## (2026-11-13: "research players who played a lot of games or significant
## numbers games past the age of 32 and bring me a list of players for my
## approval"): FINE_WINE_GAMES or more games in seasons he turned
## FINE_WINE_FROM_AGE or older, 72 players 1990-2026 (data/fine_wine.csv, built by
## tools/build_fine_wine.py). Every draftee whose career is still ahead of him
## rolls FINE_WINE_DRAFTEE_ODDS once (Prospects.roll_fine_wine) and carries
## p["fine_wine"]. Every club alike.
##
## The odds match the rate real draftees reached the same mark (director's
## choice): 54 of the 2,789 who joined a list at 21 or younger (1991 on, born by
## 1990, played or not), 1 in 52 (docs/FINE_WINE_EVIDENCE.md). Ageing and retirement read
## FINE_WINE_YEARS and FINE_WINE_SLOPE (Potential.age_step_for, Prospects.should_retire).
const FINE_WINE_FROM_AGE := 32
const FINE_WINE_GAMES := 60
const FINE_WINE_DRAFTEE_ODDS := 1.0 / 52.0
## His decline runs this many years behind his age, and every retirement age.
const FINE_WINE_YEARS := 3.0
## A yearly loss, once it starts, is this share of a normal one.
const FINE_WINE_SLOPE := 0.7
const FINE_WINE_CSV := "res://data/fine_wine.csv"
static var _fine_wine_real := {}
static var _fine_wine_loaded := false


## Whether he has Fine Wine: the flag a drafted roll set, or a real player whose
## real career is on the approved list (keyed by his real name and date of birth, so a created
## player who shares a name never inherits it).
static func fine_wine(p: Dictionary) -> bool:
	if bool(p.get("fine_wine", false)):
		return true
	if bool(p.get("generated", false)):
		return false
	var dob := str(p.get("dob", ""))
	if dob == "":
		return false
	if not _fine_wine_loaded:
		_load_fine_wine()
	var real := str(p.get("real_name", "%s %s" % [str(p.get("first", "")), str(p.get("last", ""))]))
	return _fine_wine_real.has("%s|%s" % [real, dob])


static func _load_fine_wine() -> void:
	_fine_wine_loaded = true
	_fine_wine_real = {}
	var f := FileAccess.open(FINE_WINE_CSV, FileAccess.READ)
	if f == null:
		push_error("Traits: %s is missing; no real player has Fine Wine." % FINE_WINE_CSV)
		return
	var header := f.get_csv_line()
	var at := {}
	for i in range(header.size()):
		at[header[i]] = i
	while not f.eof_reached():
		var row := f.get_csv_line()
		if row.size() < header.size():
			continue
		_fine_wine_real["%s %s|%s" % [row[at["first"]], row[at["last"]], row[at["dob"]]]] = true


## A synergy's match effect, as MatchSim applies it ("power" in SYNERGIES):
## an added stoppage-win share for the Engine room, a multiplier for the rest.
static func power(key: String) -> float:
	return float((SYNERGIES.get(key, {}) as Dictionary).get("power", 1.0))


## Good traits a player can carry (director, 2026-11-12: "at maximum 5 traits
## + unicorn"). Unicorn, Wet-weather player, Fine Wine and Hothead come on top.
## Past five, he keeps the five he clears by the most.
const MAX_GOOD := 5
## Good traits that come on top of the five.
const ON_TOP := ["unicorn", "wet_weather", "fine_wine"]
const LINE_NAMES := {"RUCK": "ruck", "MID": "midfield", "DEF": "defence", "FWD": "forward line"}


static func _def(key: String) -> Dictionary:
	if key == "wet_weather":
		return WET_WEATHER
	return DEFS.get(key, EARNED.get(key, SYNERGIES.get(key, {})))


static func label(key: String) -> String:
	return str(_def(key).get("label", key))


static func text(key: String) -> String:
	return str(_def(key).get("text", ""))


## The trait in a recruiter's words, for scouting a player (no numbers).
static func scout(key: String) -> String:
	return str(_def(key).get("scout", text(key)))


## His own position, second position and any learned (as Ratings.positions;
## kept here so Traits stays free of other scripts for the test runners).
static func _positions(p: Dictionary) -> Array:
	var out := [str(p.get("own_role", p.get("role", "")))]
	var r2 := str(p.get("role2", ""))
	if r2 != "" and not out.has(r2):
		out.append(r2)
	for r in p.get("learned", []):
		if not out.has(str(r)):
			out.append(str(r))
	if is_unicorn(p):
		for line in UNICORN_LINES:
			if not out.has(line):
				out.append(line)
	return out


## Every position he can be picked in.
static func positions_of(p: Dictionary) -> Array:
	return _positions(p)


## Whether he can be picked at `role`: his own, second or a learned position.
static func plays(p: Dictionary, role: String) -> bool:
	return _positions(p).has(role)


## Forward, midfield and back all among the positions he can be picked in.
static func is_unicorn(p: Dictionary) -> bool:
	return bool(p.get("unicorn", false))


static func is_bad(key: String) -> bool:
	return (DEFS.get(key, {}) as Dictionary).has("max")


## A player's traits: Unicorn, then every good trait whose line he clears, up
## to MAX_GOOD (the furthest past their line first), then the wet-weather
## player, Fine Wine and Hothead if they apply.
static func of(p: Dictionary) -> Array:
	var attr: Dictionary = p.get("attr", {})
	var roles := [str(p.get("role", "")), str(p.get("list_tag", ""))] + _positions(p)
	var good := []
	var bad := []
	for key in DEFS:
		var d: Dictionary = DEFS[key]
		var need_roles: Array = d["roles"]
		if not need_roles.is_empty():
			var ok := false
			# A forward's own job, not one he can also cover: a midfielder who
			# also plays forward isn't a Defensive forward.
			for r in ([str(p.get("role", ""))] if bool(d.get("own_role", false)) else roles):
				if need_roles.has(r):
					ok = true
			if not ok:
				continue
		var v := int(attr.get(str(d["stat"]), 0))
		if d.has("max"):
			if v <= int(d["max"]):
				bad.append(key)
			continue
		if v < int(d["min"]):
			continue
		if bool(d.get("small", false)) and int(attr.get("marking", 0)) >= 52:
			continue
		good.append([key, v - int(d["min"])])
	good.sort_custom(func(a, b): return int(a[1]) > int(b[1]))
	var out := []
	if is_unicorn(p):
		out.append("unicorn")
	for g in good.slice(0, MAX_GOOD):
		out.append(g[0])
	if wet_weather(p):
		out.append("wet_weather")
	if fine_wine(p):
		out.append("fine_wine")
	out.append_array(bad)
	return out


static func has(p: Dictionary, key: String) -> bool:
	return of(p).has(key)


## Trait counts per line for a set of on-ground players:
## {"": {trait: n}, "MID": {...}, ...}
static func _counts(ground: Array) -> Dictionary:
	var out := {"": {}, "RUCK": {}, "MID": {}, "DEF": {}, "FWD": {}}
	for p in ground:
		var line := str(p.get("role", "MID"))
		for t in of(p):
			out[""][t] = int(out[""].get(t, 0)) + 1
			if out.has(line):
				out[line][t] = int(out[line].get(t, 0)) + 1
	return out


## Synergies a side's on-ground players switch on.
static func active(ground: Array) -> Array:
	var counts := _counts(ground)
	var wild := wildcards(ground)
	var out := []
	for key in SYNERGIES:
		var s: Dictionary = SYNERGIES[key]
		var have: Dictionary = counts[str(s["line"])]
		var ok := true
		for t in s["needs"]:
			if int(have.get(t, 0)) + _filled(wild, key, str(t)) < int(s["needs"][t]):
				ok = false
		if ok:
			out.append(key)
	return out


## Which synergy slots the Unicorns on the ground fill: {synergy: [trait,
## player]}. Each Unicorn fills at most one slot, in the first synergy (in
## SYNERGIES order) that his slot completes and that is not already on; a
## line synergy only when he is playing in that line.
static func wildcards(ground: Array) -> Dictionary:
	var out := {}
	var unicorns := []
	for p in ground:
		if is_unicorn(p):
			unicorns.append(p)
	if unicorns.is_empty():
		return out
	var counts := _counts(ground)
	for u in unicorns:
		for key in SYNERGIES:
			if out.has(key):
				continue
			var s: Dictionary = SYNERGIES[key]
			var line := str(s["line"])
			if line != "" and str(u.get("role", "")) != line:
				continue
			var have: Dictionary = counts[line]
			var short := []
			for t in s["needs"]:
				var gap := int(s["needs"][t]) - int(have.get(t, 0))
				if gap > 0:
					short.append([str(t), gap])
			if short.size() == 1 and int(short[0][1]) == 1 and not of(u).has(str(short[0][0])):
				out[key] = [str(short[0][0]), u]
				break
	return out


static func _filled(wild: Dictionary, key: String, t: String) -> int:
	return 1 if wild.has(key) and str(wild[key][0]) == t else 0


## Every synergy with how close the side is: [{key, active, have: {t: n},
## needs: {t: n}}], active ones first, then the nearest.
static func progress(ground: Array) -> Array:
	var counts := _counts(ground)
	var wild := wildcards(ground)
	var out := []
	for key in SYNERGIES:
		var s: Dictionary = SYNERGIES[key]
		var have_line: Dictionary = counts[str(s["line"])]
		var have := {}
		var missing := 0
		for t in s["needs"]:
			have[t] = mini(int(have_line.get(t, 0)) + _filled(wild, key, str(t)), int(s["needs"][t]))
			missing += int(s["needs"][t]) - int(have[t])
		out.append({"key": key, "active": missing == 0, "missing": missing,
				"have": have, "needs": s["needs"]})
	out.sort_custom(func(a, b): return int(a["missing"]) < int(b["missing"]))
	return out


## The rule in full, no progress: "Requires 4 Contested bulls on the
## ground." / "Requires 2 Aerial threats and 2 Crumbers in the forward line."
static func requirement_text(key: String) -> String:
	var s: Dictionary = SYNERGIES.get(key, {})
	if s.is_empty():
		return ""
	var bits: PackedStringArray = []
	for t in s["needs"]:
		var n := int(s["needs"][t])
		var name := label(str(t))
		if n > 1:
			name = PLURALS.get(str(t), name + "s")
		bits.append("%d %s" % [n, name])
	var line := str(s["line"])
	var where := "in the %s" % str(LINE_NAMES.get(line, line)) if line != "" else "on the ground"
	return "Requires %s %s." % [" and ".join(bits), where]


## Who in a side carries each trait a synergy needs, in its line:
## [[trait, [players]]] - the facts behind "On" or not, never a to-do list.
static func carriers(key: String, ground: Array) -> Array:
	var s: Dictionary = SYNERGIES.get(key, {})
	if s.is_empty():
		return []
	var line := str(s["line"])
	var wild := wildcards(ground)
	var out := []
	for t in s["needs"]:
		var names := []
		for p in ground:
			if line != "" and str(p.get("role", "")) != line:
				continue
			if of(p).has(str(t)):
				names.append(p)
		if _filled(wild, key, str(t)) > 0:
			names.append(wild[key][1])
		out.append([str(t), names])
	return out


## "Engine room (wins more of the stoppages)" - a synergy and what it does.
static func with_effect(key: String) -> String:
	var s: Dictionary = SYNERGIES.get(key, {})
	var does := str(s.get("does", ""))
	if does == "":
		return label(key)
	return "%s (%s)" % [label(key), does.trim_suffix(".").to_lower()]


const PLURALS := {"lockdown": "Lockdown players", "big_game": "Big-game players"}


## A synergy the side is one player short of, as a fact: "Tall-small forward
## line: 1 crumber short." (director, 2026-10-06: "Build it"). The first in
## SYNERGIES order; "" when none is exactly one player short (on, or two or
## more short). No swap is suggested: who to bring in is the player's call.
static func short_text(ground: Array) -> String:
	var gap := _one_short(ground)
	if gap.is_empty():
		return ""
	var name := str(PLURALS.get(str(gap[1]), "")).trim_suffix("s")
	if name == "":
		name = label(str(gap[1]))
	return "%s: 1 %s short." % [label(str(gap[0])), name.to_lower()]


## The same fact in a coach's words, for the This week sheet: "One short:
## Running machine (needs one more runner who never tires)." "" when none.
static func short_words(ground: Array) -> String:
	var gap := _one_short(ground)
	if gap.is_empty():
		return ""
	return "One short: %s (needs one more %s)." % [label(str(gap[0])), str(SHORT_WHO.get(str(gap[1]), label(str(gap[1])).to_lower()))]


## Who a synergy still needs, as a coach would say him.
const SHORT_WHO := {
	"bull": "contested ball winner", "aerial": "key forward who marks overhead",
	"crumber": "small forward who crumbs the ball", "interceptor": "defender who reads the ball in the air",
	"lockdown": "stopper", "ball_magnet": "ball magnet", "playmaker": "playmaker",
	"engine": "runner who never tires",
}


## [synergy key, trait key] for the first synergy exactly one player short, or [].
static func _one_short(ground: Array) -> Array:
	var rows := {}
	for r in progress(ground):
		rows[str(r["key"])] = r
	for key in SYNERGIES:
		var r: Dictionary = rows[key]
		if int(r["missing"]) != 1:
			continue
		for t in r["needs"]:
			if int(r["have"][t]) < int(r["needs"][t]):
				return [str(key), str(t)]
	return []


## "2/2 Contested bull (midfield)" style summary for one synergy row.
static func needs_text(row: Dictionary) -> String:
	var s: Dictionary = SYNERGIES[str(row["key"])]
	var bits: PackedStringArray = []
	for t in row["needs"]:
		bits.append("%d/%d %s" % [int(row["have"][t]), int(row["needs"][t]), label(str(t))])
	var line := str(s["line"])
	var where := " in the %s" % str(LINE_NAMES.get(line, line)) if line != "" else ""
	return ", ".join(bits) + where


## How far a player is from each trait he does not have: [{key, gap}] for
## gaps of 1-6 points, nearest first - Training shows these.
static func near(p: Dictionary) -> Array:
	var attr: Dictionary = p.get("attr", {})
	var have := of(p)
	var out := []
	var roles := [str(p.get("role", "")), str(p.get("role2", ""))]
	for key in DEFS:
		var d: Dictionary = DEFS[key]
		if d.has("max") or have.has(key):
			continue
		var need_roles: Array = d["roles"]
		if not need_roles.is_empty() and not (need_roles.has(roles[0]) or need_roles.has(roles[1])):
			continue
		if bool(d.get("small", false)) and int(attr.get("marking", 0)) >= 52:
			continue
		var gap := int(d["min"]) - int(attr.get(str(d["stat"]), 0))
		if gap >= 1 and gap <= 6:
			out.append({"key": key, "gap": gap, "stat": str(d["stat"])})
	out.sort_custom(func(a, b): return int(a["gap"]) < int(b["gap"]))
	return out


## "4 Contested bulls", "1 Crumber": a count of a trait's carriers.
static func count_words(t: String, n: int) -> String:
	var name := label(t)
	if n != 1:
		name = str(PLURALS.get(t, name + "s"))
	return "%d %s" % [n, name]


## A recruit's synergy fit as a fact (row 103): "Completes Engine room: 4 of
## 4 Contested bulls with him." or "Engine room: 3 of 4 Contested bulls with
## him." Never whom to get. `row` is a GameState.synergy_fit row.
static func fit_text(row: Dictionary) -> String:
	var key := str(row["key"])
	var need := int(row["need"])
	var line := str((SYNERGIES[key] as Dictionary)["line"])
	var where := " in the %s" % str(LINE_NAMES.get(line, line)) if line != "" else ""
	var count := "%d of %s%s with him" % [int(row["have"]) + 1, count_words(str(row["trait"]), need), where]
	if bool(row["completes"]):
		return "Completes %s: %s." % [label(key), count]
	return "%s: %s." % [label(key), count]
