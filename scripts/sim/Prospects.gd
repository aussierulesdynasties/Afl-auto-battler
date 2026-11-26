class_name Prospects
extends RefCounted
## End-of-season intake support: draft classes, the Forge's prospect,
## expansion lists and depth pools, and the season's ageing and retirements.
##
## Every prospect is one of 12 types (RATING_REBUILD §4): a talent percentile,
## his type's real first-season ranges read at it, ±6 on each attribute. His
## OVR is whatever those attributes make (Rating.ovr); nothing fits them to a
## number. The match engine treats prospects exactly like real players.
##
## The 2026 class ships from data/draftees_2026.csv; every later class is
## generated deterministically from its year so careers can loop forever.

const MAX_RETIRE_PER_CLUB := 8
## The youngest a real player of a Legacy start can be in his last real
## season for that season to count as his retirement (should_retire). Younger,
## he was delisted: his contract ends then (real_delisting_due).
const REAL_RETIRE_AGE := 27.0
## Generated forwards run from small (172 cm) to key (203 cm), about a third
## of each by MatchSim.fwd_size, as in a real draft class: from 184 cm there
## were no small forwards, and over a career the league's forward lines
## turned tall (ARD-M3-002).
const FWD_MIN_CM := 172

const ATTR_KEYS := Attributes.KEYS

## Future classes differ year to year as a cohort, not only player by
## player. Most years are ordinary; a strong crop lifts the top end most,
## the depth a little and the ceilings of its best prospects; a superdraft
## does that harder; a weak one the reverse. Busts, role spread and ordinary
## late picks stay, because each prospect's own rolls are unchanged.
##   [key, chance, top-end shift, depth shift, ceiling shift]
## The shifts move every attribute but Discipline evenly (so OVR by the
## same); the top-end shift is full at pick 1 and tapers to the depth shift by
## CLASS_TOP_RANKS; the ceiling shift (extra POT room) tapers to nothing by
## the same rank. The real 2026 class is data, never tiered.
const CLASS_TIERS := [
	["weak", 0.10, -3.0, -1.5, -3.0],
	["below", 0.20, -1.5, -0.5, -1.5],
	["normal", 0.50, 0.0, 0.0, 0.0],
	["strong", 0.17, 2.0, 1.0, 3.0],
	["super", 0.03, 4.5, 2.0, 9.0],
]
const CLASS_TOP_RANKS := 30

const JUNIOR_TEAMS := [
	["Sandringham Dragons", "Talent League", "VICM"],
	["Northern Knights", "Talent League", "VICM"],
	["Dandenong Stingrays", "Talent League", "VICC"],
	["Gippsland Power", "Talent League", "VICC"],
	["Eastern Ranges", "Talent League", "VICM"],
	["Calder Cannons", "Talent League", "VICM"],
	["Oakleigh Chargers", "Talent League", "VICM"],
	["GWV Rebels", "Talent League", "VICC"],
	["Bendigo Pioneers", "Talent League", "VICC"],
	["Geelong Falcons", "Talent League", "VICC"],
	["Murray Bushrangers", "Talent League", "VICM"],
	["Swan Districts", "WAFL", "WA"],
	["Claremont", "WAFL", "WA"],
	["East Perth", "WAFL", "WA"],
	["Subiaco", "WAFL", "WA"],
	["South Adelaide", "SANFL", "SA"],
	["North Adelaide", "SANFL", "SA"],
	["Woodville-West Torrens", "SANFL", "SA"],
	["Central District", "SANFL", "SA"],
	["Glenelg", "SANFL", "SA"],
	["West Adelaide", "SANFL", "SA"],
	["Lions Academy", "Talent League", "QLD"],
	["Suns Academy", "Talent League", "QLD"],
	["GIANTS Academy", "Talent League", "NSW"],
	["AS Academies", "Talent League", "NSW"],
	["Tasmania Devils", "Talent League", "TAS"],
]


# ---------------------------------------------------------------------------
# Types, talent and the projection (RATING_REBUILD §4)
# ---------------------------------------------------------------------------
## The 12 types' ranges: each attribute's 10th-90th percentile among real
## first-season players of that type, aged 18-20, Wheelo 2012-25 (a ruck's at
## any debut age), built by tools/wheelo/league.py.
const RANGES_CSV := "res://data/draftee_ranges.csv"
## A draftee's level by his pick (director 2026-11-26, question box): "derived
## starting OVRs land around ~58-64 for Pick 1, ~52-58 for First Rounders
## (2-18), and ~44-52 for later picks". [pick, OVR] points, a straight line
## between each pair and flat past the last: his archetype's rookie baseline
## is moved to this level, then each attribute varies on its own, and his OVR
## is read from what that makes (never drawn first).
## Example: pick 10 sits 57 - 4 x 8 / 16 = 55.
const PICK_LEVEL := [[1, 61.0], [2, 57.0], [18, 53.0], [19, 51.0], [60, 45.0]]
## How far each attribute varies around his baseline: this share of his
## type's p10-p90 range, uniform, each attribute drawn on its own.
## Example: a Wing's Kicking runs 17.2 to 60.4 (43.2 wide): ±8.6.
const SPREAD := 0.2

## [{"name", "line", "n", "ranges": {attribute: [p10, p90]}}], file order. A
## type's line is its first position's.
static var _types := []


static func types() -> Array:
	if not _types.is_empty():
		return _types
	var f := FileAccess.open(RANGES_CSV, FileAccess.READ)
	if f == null:
		return _types
	var head := f.get_csv_line()
	var col := {}
	for i in head.size():
		col[head[i]] = i
	var by_name := {}
	while not f.eof_reached():
		var r := f.get_csv_line()
		if r.size() < head.size() or str(r[0]) == "":
			continue
		var name := str(r[col["type"]])
		if not by_name.has(name):
			var first := str(r[col["positions"]]).split("|")[0]
			by_name[name] = {"name": name, "line": Rating.line_of(first), "n": int(r[col["n"]]), "ranges": {}}
			_types.append(by_name[name])
		(by_name[name]["ranges"] as Dictionary)[str(r[col["attribute"]])] = \
				[float(r[col["p10"]]), float(r[col["p90"]])]
	return _types


## The type called `name`; {} when there is none.
static func type_named(name: String) -> Dictionary:
	for t in types():
		if str(t["name"]) == name:
			return t
	return {}


## One of `line`'s types, each as likely as real first-season players of it
## were (its n). {} when the line has none.
static func draw_type(line: String, rng: RandomNumberGenerator) -> Dictionary:
	var pool := []
	var weights := []
	for t in types():
		if str(t["line"]) == line:
			pool.append(t)
			weights.append(float(t["n"]))
	if pool.is_empty():
		return {}
	return pool[_weighted_index(rng.randf(), weights)]


## The OVR level of the prospect ranked `rank` (PICK_LEVEL). A prospect with
## no rank (0) is a late pick's.
static func pick_level(rank: int) -> float:
	var last: Array = PICK_LEVEL[PICK_LEVEL.size() - 1]
	if rank <= 0 or rank >= int(last[0]):
		return float(last[1])
	for i in range(PICK_LEVEL.size() - 1):
		var a: Array = PICK_LEVEL[i]
		var b: Array = PICK_LEVEL[i + 1]
		if rank <= int(b[0]):
			return float(a[1]) + (float(rank) - float(a[0])) * (float(b[1]) - float(a[1])) / (float(b[0]) - float(a[0]))
	return float(last[1])


## His archetype's rookie baseline: each attribute in the middle of his type's
## p10-p90 range.
static func baseline(t: Dictionary) -> Dictionary:
	var out := {}
	var ranges: Dictionary = t.get("ranges", {})
	for key in ATTR_KEYS:
		var r: Array = ranges.get(key, [50.0, 50.0])
		out[key] = (float(r[0]) + float(r[1])) / 2.0
	return out


## A type's attributes for the prospect ranked `rank` at `apos`: the baseline
## moved evenly, every attribute but Discipline, to his pick's level, then
## each attribute ± SPREAD of its own range, drawn on its own, within 1-99.
## Example: pick 10's level 55 is a weighted sum of 48.1 (Rating.unstretch);
## a Wing whose baseline sums to 46.0 there, Discipline carrying 4 of the 100
## weight, moves every other attribute up 2.1 / 0.96 = 2.2; his Kicking then
## lands anywhere in ±8.6 of that.
static func attrs_for(t: Dictionary, rank: int, apos: String, rng: RandomNumberGenerator) -> Dictionary:
	var a := baseline(t)
	var w: Dictionary = Rating.WEIGHTS.get(apos, Rating.WEIGHTS["Midfielder"])
	var moved := 1.0 - float(w.get("discipline", 0)) / 100.0
	var lift := (Rating.unstretch(pick_level(rank)) - Rating.raw_of(a, apos)) / moved
	var ranges: Dictionary = t.get("ranges", {})
	for key in ATTR_KEYS:
		var r: Array = ranges.get(key, [50.0, 50.0])
		var v := float(a[key]) + (lift if key != "discipline" else 0.0)
		v += rng.randf_range(-SPREAD, SPREAD) * (float(r[1]) - float(r[0]))
		a[key] = clampf(v, 1.0, 99.0)
	return a


## A prospect's attributes, type and POT. His type is kept once he has one
## (the Forge sets it from his play style); otherwise drawn from his line's.
## His attributes are his pick's (attrs_for). A strong or weak class moves
## every attribute but Discipline evenly (`class_shift`); an international's
## code reshapes him at the same level (`attr_bias`). Seeded by the prospect
## alone.
static func project(p: Dictionary) -> void:
	var rng := _rng_for("%s|%s" % [str(p.get("id", "")), str(p.get("draft_year", 2026))])
	var role := str(p.get("role", "MID"))
	# The draw is made even when his type is kept, so a re-projection reads the
	# same talent and attributes off the same stream.
	var drawn := draw_type(role, rng)
	var t := type_named(str(p.get("type", "")))
	if t.is_empty() or str(t["line"]) != role:
		t = drawn
	var a := attrs_for(t, int(p.get("draft_rank", 0)), Rating.apos_of(p), rng)
	var shift := float(p.get("class_shift", 0.0))
	for key in a:
		if key != "discipline":
			a[key] = float(a[key]) + shift
	var bias: Dictionary = p.get("attr_bias", {})
	if not bias.is_empty():
		var apos := Rating.apos_of(p)
		var level := Rating.of_attrs(a, apos)
		for key in bias:
			a[key] = float(a.get(key, 50.0)) + float(bias[key])
		a = Rating.shift_to(a, apos, float(level))
	for key in a:
		a[key] = clampi(int(round(float(a[key]))), 1, 99)
	p["attr"] = a
	p["type"] = str(t.get("name", ""))
	p["projected"] = true
	p["sample"] = 14.0
	p.erase("potential")  # re-projection re-derives it (deterministically)
	Potential.assign(p)


# ---------------------------------------------------------------------------
# Season rollover: growth, decline, retirement
# ---------------------------------------------------------------------------
## Ages and redevelops every player on every list in place. Mutates the
## player dicts (they are shared with GameDB; a New Career resets via
## GameDB.reload()). Returns {"retired": [...], "developed": n, "declined": n}.
## `min_left` is the smallest a list may be left at: 0 after a National Draft,
## which refills every list; a rollover with no draft (start_next_season)
## keeps each list at Contracts.min_list(), as nobody drafts in their places.
static func age_league(lists: Dictionary, year: int, min_left := 0) -> Dictionary:
	var retired := []
	var developed := 0
	var declined := 0
	var breakouts := []
	for code in lists:
		var arr: Array = lists[code]
		for p in arr:
			age_player(p, year)
			# The summer after the season just played (Growth, the director's
			# design 2026-11-17): past his peak part of what he trained past
			# his potential goes; once his career is over he falls.
			var delta := Growth.summer(p, year - 1)
			if delta > 0:
				developed += 1
			elif delta < 0:
				declined += 1
		for b in Growth.breakouts(str(code), arr, year):
			breakouts.append([str(code)] + b)
		# Retire/trim pass, original order so it is deterministic.
		var keep: Array = []
		var dropped := 0
		for p in arr:
			# Decided at the off-season (Retirement) when it opened; a player
			# talked round plays one more season.
			var go := should_retire(p, year) or int(p.get("retiring", 0)) == year
			if int(p.get("play_on", 0)) == year:
				go = false
			# After a draft, never held back by the list size: the draft made
			# every club, yours included, fill the places its retirees leave
			# (Draft.leaving), so a list that passes at the minimum still
			# turns over (2026-11-13: a coach who passed every draft kept
			# the same 32 for 36 years).
			if go and dropped < MAX_RETIRE_PER_CLUB and arr.size() - dropped > min_left:
				dropped += 1
				retired.append({"id": str(p["id"]), "name": str(p.get("generic_name", p.get("name", "Player"))),
						"club": str(code), "age": float(p.get("age", 26.0)),
						"overall": int(Rating.ovr(p, 40))})
				p["retired"] = true
			else:
				# Held back by the cap on retirements or the list size: he
				# plays the season, so nothing reads him as retiring in it
				# (Contracts.payroll would leave his salary off the books).
				if int(p.get("retiring", 0)) == year:
					p.erase("retiring")
				keep.append(p)
		lists[code] = keep
	return {"retired": retired, "developed": developed, "declined": declined, "breakouts": breakouts}


static func should_retire(p: Dictionary, year: int) -> bool:
	var age := Potential.retire_age(p)   # Fine Wine: three years later
	var ov := int(Rating.ovr(p, 50))
	# Under 22 he is never retired for his rating (director 2026-11-26: "Exempt
	# players under age 22 from auto-retirement so rookies and 1991 foundation
	# players like Mark Bickley are never retired before Round 1").
	var under_22 := float(p.get("age", 26.0)) < 22.0
	# A real player of a Legacy start retires about when he did (director,
	# 2026-11-13: "make all historical players retirement start roughly when
	# it did irl"), a year either side, whatever his age or rating; a coach
	# can still talk him round (Retirement). Still listed in 2025: the sim's.
	# His last real season is a retirement only when he was REAL_RETIRE_AGE or
	# older in it: a younger man's career ended because his club delisted him,
	# so it ends as a delisting (real_delisting_due), not a retirement. (Read as
	# every last season, a 1990 start retired 12 a club, nine of them 26 or younger.)
	var last := int(p.get("real_last", 0))
	# A year early never ends a career before a season he really played for
	# the club that signed him (a new club's foundation man, real_first).
	if last > 0 and float(p.get("age", 26.0)) - float(year - last) >= REAL_RETIRE_AGE:
		return year > maxi(last + real_slack(p), int(p.get("real_first", 0)))
	if ov <= 32 and not under_22:
		return true
	if age >= 37.0:
		return true
	if age >= 35.0:
		return _rng_for("%s|r%d" % [str(p["id"]), year]).randf() < 0.70
	if age >= 33.0 and ov < 42:
		return _rng_for("%s|r%d" % [str(p["id"]), year]).randf() < 0.30
	return false


## A real player of a Legacy start whose real AFL career ended before he was
## REAL_RETIRE_AGE: his club delisted him then (director, 2026-11-13: careers
## end "about when he really did ... whatever the sim makes of his age or
## rating"). Due in the same season his retirement would be (should_retire,
## real_slack), for the off-season before season `year`.
static func real_delisting_due(p: Dictionary, year: int) -> bool:
	var last := int(p.get("real_last", 0))
	if last <= 0 or float(p.get("age", 26.0)) - float(year - last) >= REAL_RETIRE_AGE:
		return false
	return year > last + real_slack(p)


## How far his retirement falls from his real one: -1, 0 or +1 seasons
## (one in four early, one in four late), fixed for him by his id.
static func real_slack(p: Dictionary) -> int:
	var r := _rng_for("%s|real_last" % str(p.get("id", ""))).randf()
	return -1 if r < 0.25 else (1 if r >= 0.75 else 0)


## Age one player by a year. Everyone on a list has now played a full
## simulated season, so the 2026 small-sample confidence shrink lifts. His
## rating moves only by what he earns (Growth): no age step, no free points,
## no growth toward his potential in the summer (director, 2026-11-17).
static func age_player(p: Dictionary, _year: int) -> float:
	p["age"] = float(p.get("age", 26.0)) + 1.0
	if bool(p.get("projected", false)):
		p["sample"] = 16.0
	else:
		p["sample"] = maxf(18.0, float(p.get("gm", 0.0)))
	return 0.0


## Age the undrafted pool between seasons. Prospects re-enter next year's
## draft a year older; past draft age they drop out of the pool.
static func age_pool(pool: Array, year: int, drafted: Dictionary) -> Array:
	var out := []
	for p in pool:
		var id := str(p["id"])
		if drafted.has(id):
			continue
		if int(p.get("draft_year", 0)) == year:
			# A generated class is made a year ahead; that year in the pool ages it but does not
			# develop it, so it is drafted at the rating it was made with, as the real 2026 class
			# is (row 65: one pool year of growth put picks 1-5 at 65-69, above the 4.Q9 bands).
			# A prospect passed over in his own draft grows from then on, like anyone else.
			p["age"] = float(p.get("age", 18.0)) + 1.0
		else:
			age_player(p, year)
		# A real class's mature-age pick (a Legacy career) is in his own draft
		# whatever his age; passed over, he ages out like anyone else.
		var own_real := bool(p.get("real_class", false)) and int(p.get("draft_year", 0)) == year
		# A delisted man put back in the drafts (GameState._relist) waits for
		# the Rookie Draft, then ends his career if nobody takes him.
		var relisted := int(p.get("relisted", 0)) == year - 1
		if float(p.get("age", 18.0)) >= 22.0 and not own_real and not relisted:
			continue  # aged out of draft eligibility
		out.append(p)
	return out


# ---------------------------------------------------------------------------
# Future draft classes
# ---------------------------------------------------------------------------
## Deterministic fictional intake for years after the shipped data ends.
## Same projection as the real class (project: type, talent, ranges), so a
## 2031 career keeps getting plausible rookies without inventing anyone real.
## `career_seed` picks the class's quality tier (class_tier); everything
## else about the class is seeded by the year alone, as before.
static func generate_class(year: int, career_seed := 0) -> Array:
	var tier := class_tier(career_seed, year)
	var rng := _rng_for("class-%d" % year)
	var size := 46 + int(rng.randi_range(0, 10))
	# The real lists' mix (director, 2026-10-06: "Match real lists"): about
	# DEF 34%, FWD 30%, MID 28%, RUCK 7%. Every twelfth pick is a ruck (8%);
	# the rest come from this bag, so a class runs DEF 35, FWD 28, MID 28.
	var role_bag := ["DEF", "DEF", "DEF", "DEF", "DEF", "FWD", "FWD", "FWD", "FWD",
			"MID", "MID", "MID", "MID"]
	var out := []
	var rucks := 0
	for r in range(1, size + 1):
		var p := {}
		var role: String = str(role_bag[rng.randi_range(0, role_bag.size() - 1)])
		if r % 12 == 8:
			role = "RUCK"
		if role == "RUCK":
			rucks += 1
		p["role"] = role
		p["role2"] = _generated_secondary(role, rng)
		var height := 0.0
		match role:
			"RUCK": height = float(rng.randi_range(197, 208))
			"FWD": height = float(rng.randi_range(FWD_MIN_CM, 203))
			"DEF": height = float(rng.randi_range(182, 198))
			_: height = float(rng.randi_range(173, 192))
		p["height_cm"] = height
		var over_age := rng.randf() < 0.15
		var birth_year := year - (19 if over_age else 18)
		var m := rng.randi_range(1, 12)
		var dd := rng.randi_range(1, 28)
		p["dob"] = "%04d-%02d-%02d" % [birth_year, m, dd]
		p["age"] = float(days_between(str(p["dob"]), "%d-11-20" % year)) / 365.25
		# ^ drafted mid-November; the whole class shares one reference date.
		var team: Array = JUNIOR_TEAMS[rng.randi_range(0, JUNIOR_TEAMS.size() - 1)]
		p["club"] = str(team[0])
		p["draft_team"] = str(team[0])
		p["draft_league"] = str(team[1])
		p["draft_state"] = str(team[2])
		p["state"] = str(team[2])
		p["tied_club"] = ""
		p["tied_type"] = ""
		p["u18_gm"] = float(rng.randi_range(6, 16))
		p["u18_di"] = float(rng.randi_range(10, 26)) if role != "RUCK" else float(rng.randi_range(8, 18))
		p["u18_gl"] = float(rng.randi_range(3, 26)) / 10.0 if role == "FWD" \
				else float(rng.randi_range(0, 8)) / 10.0
		p["u18_mk"] = float(rng.randi_range(1, 7)) if role != "FWD" else float(rng.randi_range(3, 7))
		p["u18_tk"] = float(rng.randi_range(1, 7))
		p["u18_if50"] = float(rng.randi_range(1, 6))
		p["u18_ho"] = float(rng.randi_range(12, 28)) if role == "RUCK" else 0.0
		p["note"] = ""
		p["id"] = "D%d_%02d" % [year, r]
		p["real_name"] = ""
		p["generic_name"] = ""
		p["name"] = ""
		p["first"] = ""
		p["last"] = ""
		p["src"] = "U18"
		p["data_src"] = "generated"
		p["draft_year"] = year
		p["draft_rank"] = r
		p["generated"] = true
		p["num"] = r
		var shifts := class_shifts(tier, r)
		p["class_shift"] = shifts[0]
		p["class_ceiling"] = shifts[1]
		for key in Ratings.STATS_ZERO_KEYS:
			p[key] = 0.0
		p["weight_kg"] = 0.0
		p["real_pos"] = Ratings.ROLE_SHORT_TO_POS.get(str(p["role"]), "MID")
		project(p)
		out.append(p)
	# Guarantee the pool carries a few rucks without renumbering the class.
	if rucks < 3:
		for p in out:
			if rucks >= 3:
				break
			if float(p.get("height_cm", 0.0)) >= 198.0 and str(p["role"]) != "RUCK":
				p["role"] = "RUCK"
				p["role2"] = "FWD"
				p["u18_ho"] = 18.0
				p.erase("type")
				project(p)
				rucks += 1
	_maybe_unicorn(out, year, career_seed)
	roll_fine_wine(out, "class-%d-%d" % [year, career_seed])
	GameDB.assign_aliases(out)
	InternationalProspects.apply(out, year)
	return out


## About one class in UNICORN_CLASS_CHANCE has a Unicorn (director,
## 2026-10-08): its tallest prospect who isn't a ruck, if he stands 194 cm or
## more - a key-position body with a smaller player's game. Its own dice, so
## the class itself rolls as it always did.
const UNICORN_CLASS_CHANCE := 0.4
const UNICORN_MIN_CM := 194.0


static func _maybe_unicorn(cls: Array, year: int, career_seed: int) -> void:
	var rng := _rng_for("unicorn-%d-%d" % [year, career_seed])
	if rng.randf() >= UNICORN_CLASS_CHANCE:
		return
	var best: Dictionary = {}
	for p in cls:
		if str(p.get("role", "")) == "RUCK" or float(p.get("height_cm", 0.0)) < UNICORN_MIN_CM:
			continue
		if best.is_empty() or float(p["height_cm"]) > float(best["height_cm"]):
			best = p
	if not best.is_empty():
		best["unicorn"] = true
		best["note"] = "%d cm and moves like a much smaller player" % int(best["height_cm"])


## Every generated draftee rolls once for Fine Wine at Traits.FINE_WINE_DRAFTEE_ODDS
## (director, 2026-11-13: "every draftee should have a very slim chance").
## Its own dice, so the class itself rolls as it always did. A real draftee
## rolls too, unless his real career could already show it by the 2026 data
## (born 1991 or earlier, so 60 games at 32+ were within reach by 2025): then his
## record decides (Traits.fine_wine), as for any real player in a Legacy start.
const FINE_WINE_RECORD_BORN := 1991


static func roll_fine_wine(cls: Array, salt: String) -> void:
	var rng := _rng_for("fine-wine-" + salt)
	for p in cls:
		var roll := rng.randf()
		if not bool(p.get("generated", false)):
			var born := str(p.get("dob", "")).substr(0, 4)
			if not born.is_valid_int() or int(born) <= FINE_WINE_RECORD_BORN:
				continue
		if roll < Traits.FINE_WINE_DRAFTEE_ODDS:
			p["fine_wine"] = true


# ---------------------------------------------------------------------------
# A custom prospect (Club Forge, ARD-M7-008)
# ---------------------------------------------------------------------------
## Strengths and weaknesses a coach can name, in football words, and the
## attribute each moves. A play style is two strengths for one role.
const CUSTOM_TRAITS := {
	"marking": "contested_marking", "kicking": "kicking", "goalkicking": "goalkicking",
	"contested": "contested_ball", "pressure": "pressure", "reading": "reading_play",
	"running": "work_rate", "vision": "vision", "ruckwork": "ruck",
}
const CUSTOM_STYLES := {
	"FWD": {"key_forward": ["marking", "goalkicking"], "small_forward": ["goalkicking", "pressure"],
			"defensive_forward": ["pressure", "contested"], "leading_forward": ["running", "marking"]},
	"MID": {"inside": ["contested", "kicking"], "outside": ["running", "kicking"],
			"tagger": ["pressure", "reading"], "playmaker": ["vision", "kicking"]},
	"DEF": {"key_defender": ["marking", "reading"], "rebounder": ["running", "kicking"],
			"lockdown": ["pressure", "contested"], "interceptor": ["reading", "marking"]},
	"RUCK": {"tap_ruck": ["ruckwork", "contested"], "mobile_ruck": ["ruckwork", "running"]},
}
## A play style that names one of the 12 types (ClubForgeScene.STYLE_LABELS:
## "Small defender" is the rebounder) makes him that type; the others take
## one of his line's types, as any prospect does (project).
const STYLE_TYPES := {
	"key_forward": "Key forward", "small_forward": "Small forward", "inside": "Inside midfielder",
	"key_defender": "Key defender", "rebounder": "Small defender", "interceptor": "Interceptor",
	"tap_ruck": "Tap ruck", "mobile_ruck": "Mobile ruck",
}
const CUSTOM_HEIGHT := {"RUCK": [197, 210], "FWD": [168, 205], "DEF": [175, 202], "MID": [168, 195]}
## How hard a style, strength or weakness pushes its attribute before the
## whole profile moves back evenly to the same OVR (Rating.shift_to).
const CUSTOM_STYLE_PUSH := 5.0
const CUSTOM_TRAIT_PUSH := 7.0
## Where a custom prospect sits in his class, rolled once per career: a
## believable spread from late picks to the top three, so most are useful
## role players to good players, a star is uncommon and a generational
## ceiling (a top pick's room plus a good roll) is rare.
const CUSTOM_RANKS := [[1, 1, 1.0], [2, 3, 3.0], [4, 10, 14.0], [11, 20, 22.0], [21, 35, 35.0], [36, 45, 25.0]]


## Whether `spec` is a valid custom prospect: role, secondary, height,
## style, strengths and weaknesses. "" when it is, else what's wrong.
static func custom_problem(spec: Dictionary) -> String:
	var role := str(spec.get("role", ""))
	if not CUSTOM_STYLES.has(role):
		return "Pick a position."
	var role2 := str(spec.get("role2", ""))
	if role2 != "" and (role2 == role or not CUSTOM_STYLES.has(role2)):
		return "The second position must be a different one."
	var h := int(spec.get("height_cm", 0))
	var band: Array = CUSTOM_HEIGHT[role]
	if h < int(band[0]) or h > int(band[1]):
		return "Height for that position is %d to %d cm." % [band[0], band[1]]
	if str(spec.get("style", "")) != "" and not (CUSTOM_STYLES[role] as Dictionary).has(str(spec["style"])):
		return "That play style isn't one for this position."
	var strengths: Array = spec.get("strengths", [])
	var weaknesses: Array = spec.get("weaknesses", [])
	if strengths.size() > 2 or weaknesses.size() > 2:
		return "Up to two strengths and two weaknesses."
	for t in strengths + weaknesses:
		if not CUSTOM_TRAITS.has(str(t)):
			return "Unknown strength or weakness."
	for t in strengths:
		if weaknesses.has(t):
			return "A strength can't also be a weakness."
	if str(spec.get("first", "")).strip_edges() == "" or str(spec.get("last", "")).strip_edges() == "":
		return "He needs a first and last name."
	return ""


## The Club Forge rule on top of custom_problem (T8.Q12): exactly one
## weakness is compulsory and a second is optional. The weaknesses only
## reshape him; _shape_custom refits to the same overall, so no choice buys
## power. Kept apart from custom_problem so a player saved before the rule
## still enters a career; the Forge asks for one the next time he's edited.
static func forge_problem(spec: Dictionary) -> String:
	var weaknesses: Array = spec.get("weaknesses", [])
	if weaknesses.is_empty():
		return "Pick one weakness. A second is optional."
	return custom_problem(spec)

## The custom prospect for the class drafted in `year`, through the same
## projection as every generated prospect (project, Potential.assign). His
## standing in the class - and so his ceiling - is rolled once from the
## career's seed: the coach shapes his profile, never his OVR or POT. Nothing
## about him is special after this: same development, durability, ageing.
static func make_custom(spec: Dictionary, year: int, career_seed: int) -> Dictionary:
	var rng := _rng_for("custom|%d|%d" % [career_seed, year])
	rng.randi()
	var weights := []
	for b in CUSTOM_RANKS:
		weights.append(float(b[2]))
	var band: Array = CUSTOM_RANKS[_weighted_index(rng.randf(), weights)]
	var rank := rng.randi_range(int(band[0]), int(band[1]))
	var role := str(spec["role"])
	var p := {}
	p["id"] = "C%d_%d" % [year, career_seed]
	p["role"] = role
	p["role2"] = str(spec.get("role2", ""))
	p["height_cm"] = float(spec["height_cm"])
	p["dob"] = str(spec.get("dob", "%04d-06-15" % (year - 18)))
	p["age"] = float(days_between(str(p["dob"]), "%d-11-20" % year)) / 365.25
	var team: Array = JUNIOR_TEAMS[rng.randi_range(0, JUNIOR_TEAMS.size() - 1)]
	p["club"] = str(team[0])
	p["draft_team"] = str(team[0])
	p["draft_league"] = str(team[1])
	p["draft_state"] = str(team[2])
	p["state"] = str(team[2])
	p["tied_club"] = ""
	p["tied_type"] = ""
	for key in ["u18_gm", "u18_di", "u18_gl", "u18_mk", "u18_tk", "u18_if50", "u18_ho"]:
		p[key] = 0.0
	p["u18_gm"] = float(rng.randi_range(8, 16))
	p["note"] = ""
	var full := "%s %s" % [str(spec["first"]).strip_edges(), str(spec["last"]).strip_edges()]
	p["first"] = str(spec["first"]).strip_edges()
	p["last"] = str(spec["last"]).strip_edges()
	# A forged prospect has one name: the one you gave him.
	p["real_name"] = full
	p["generic_name"] = full
	p["name"] = full
	p["nickname"] = str(spec.get("nickname", "")).strip_edges()
	# FL-005: the club he grew up following, his choice ("" = not recorded).
	p["fav_club"] = str(spec.get("fav_club", "")).strip_edges()
	p["foot"] = "L" if str(spec.get("foot", "R")) == "L" else "R"
	p["number_pref"] = clampi(int(spec.get("number_pref", 0)), 0, 99)
	if spec.get("look") is Dictionary:
		p["look"] = (spec["look"] as Dictionary).duplicate(true)
	p["src"] = "U18"
	p["data_src"] = "generated"
	p["draft_year"] = year
	p["draft_rank"] = rank
	p["generated"] = true
	p["user_created"] = true
	p["num"] = 0
	p["class_shift"] = 0.0
	p["class_ceiling"] = 0.0
	if STYLE_TYPES.has(str(spec.get("style", ""))):
		p["type"] = str(STYLE_TYPES[str(spec["style"])])
	for key in Ratings.STATS_ZERO_KEYS:
		p[key] = 0.0
	p["weight_kg"] = 0.0
	p["real_pos"] = Ratings.ROLE_SHORT_TO_POS.get(role, "MID")
	project(p)
	_shape_custom(p, spec)
	return p


## Move the projected attributes toward his style and strengths and away from
## his weaknesses, then back evenly to the same OVR (Rating.shift_to): a
## different footballer, not a better one. Potential stays as projected.
static func _shape_custom(p: Dictionary, spec: Dictionary) -> void:
	var role := str(p["role"])
	var a: Dictionary = (p["attr"] as Dictionary).duplicate()
	var style := str(spec.get("style", ""))
	if style != "":
		for t in CUSTOM_STYLES[role][style]:
			var k: String = CUSTOM_TRAITS[str(t)]
			a[k] = float(a[k]) + CUSTOM_STYLE_PUSH
	for t in spec.get("strengths", []):
		var k: String = CUSTOM_TRAITS[str(t)]
		a[k] = float(a[k]) + CUSTOM_TRAIT_PUSH
	for t in spec.get("weaknesses", []):
		var k: String = CUSTOM_TRAITS[str(t)]
		a[k] = float(a[k]) - CUSTOM_TRAIT_PUSH
	p["attr"] = Rating.shift_to(a, Rating.apos_of(p), float(Rating.ovr(p)))
	p["potential"] = maxi(int(p.get("potential", Rating.ovr(p))), int(Rating.ovr(p)))


static func _weighted_index(roll: float, weights: Array) -> int:
	var total := 0.0
	for w in weights:
		total += float(w)
	var at := roll * total
	for i in range(weights.size()):
		at -= float(weights[i])
		if at < 0.0:
			return i
	return weights.size() - 1


## The quality tier of the class drafted in `year` in this career: one roll
## per career and year, so a reload never re-rolls it and two careers need
## not share their superdrafts.
static func class_tier(career_seed: int, year: int) -> String:
	var rng := _rng_for("class-tier|%d|%d" % [career_seed, year])
	rng.randi()  # the first draw from near-identical keys runs together
	var roll := rng.randf()
	for t in CLASS_TIERS:
		roll -= float(t[1])
		if roll < 0.0:
			return str(t[0])
	return "normal"


## [overall shift, extra POT room] for the prospect ranked `rank` in a class
## of this tier.
static func class_shifts(tier: String, rank: int) -> Array:
	for t in CLASS_TIERS:
		if str(t[0]) != tier:
			continue
		var fade := clampf(1.0 - float(rank - 1) / float(CLASS_TOP_RANKS - 1), 0.0, 1.0)
		var top := float(t[2])
		var depth := float(t[3])
		return [depth + (top - depth) * fade, float(t[4]) * fade]
	return [0.0, 0.0]


## The full list an expansion club fields in its first season: a real
## expansion roster mixes state-league youngsters with a core of seasoned
## players, so this one spans the full age range (unlike a rookie class) at
## overalls around the league baseline - competitive, but not a dynasty.
## Deterministic per club and year; the club's own state league supplies
## half the list when it has junior teams.
## `salt` (the career's seed, in words) gives each career its own players;
## without it the list is the same one every time, as it always was.
static func generate_expansion_list(code: String, year: int, size := 36, salt := "", first_rank := 1) -> Array:
	var rng := _rng_for("expansion-%s-%d%s" % [code, year, salt])
	var home_teams := []
	for team in JUNIOR_TEAMS:
		if str(team[2]) == str(code):
			home_teams.append(team)
	var role_bag := ["MID", "MID", "MID", "MID", "MID", "MID",
			"DEF", "DEF", "DEF", "DEF", "FWD", "FWD", "FWD", "FWD",
			"RUCK", "RUCK"]
	var out := []
	for r in range(first_rank, first_rank + size):
		var p := {}
		var role: String = str(role_bag[rng.randi_range(0, role_bag.size() - 1)])
		if r % 18 == 10:
			role = "RUCK"
		p["role"] = role
		p["role2"] = _generated_secondary(role, rng)
		var height := 0.0
		match role:
			"RUCK": height = float(rng.randi_range(197, 208))
			"FWD": height = float(rng.randi_range(FWD_MIN_CM, 203))
			"DEF": height = float(rng.randi_range(182, 198))
			_: height = float(rng.randi_range(173, 192))
		p["height_cm"] = height
		var band := rng.randf()
		var birth_year: int
		if band < 0.45:
			birth_year = year - rng.randi_range(18, 21)
		elif band < 0.80:
			birth_year = year - rng.randi_range(22, 26)
		else:
			birth_year = year - rng.randi_range(27, 30)
		p["dob"] = "%04d-%02d-%02d" % [birth_year, rng.randi_range(1, 12),
				rng.randi_range(1, 28)]
		# ^ already the right age for the season the club enters.
		p["age"] = float(days_between(str(p["dob"]), "%d-01-01" % year)) / 365.25
		var team: Array
		if not home_teams.is_empty() and rng.randf() < 0.5:
			team = home_teams[rng.randi_range(0, home_teams.size() - 1)]
		else:
			team = JUNIOR_TEAMS[rng.randi_range(0, JUNIOR_TEAMS.size() - 1)]
		p["club"] = code  # already listed; not a free agent or a draftee
		p["draft_team"] = str(team[0])
		p["draft_league"] = str(team[1])
		p["draft_state"] = str(team[2])
		p["state"] = str(team[2])
		p["tied_club"] = ""
		p["tied_type"] = ""
		p["u18_gm"] = float(rng.randi_range(12, 26))
		p["u18_di"] = float(rng.randi_range(10, 26)) if role != "RUCK" \
				else float(rng.randi_range(8, 18))
		p["u18_gl"] = float(rng.randi_range(3, 26)) / 10.0 if role == "FWD" \
				else float(rng.randi_range(0, 8)) / 10.0
		p["u18_mk"] = float(rng.randi_range(1, 7)) if role != "FWD" \
				else float(rng.randi_range(3, 7))
		p["u18_tk"] = float(rng.randi_range(1, 7))
		p["u18_if50"] = float(rng.randi_range(1, 6))
		p["u18_ho"] = float(rng.randi_range(12, 28)) if role == "RUCK" else 0.0
		p["note"] = "Expansion list, %d" % year
		p["id"] = ("EXP_%s_%02d" % [code, r]) if salt == "" else ("FND_%s_%s_%02d" % [code, salt, r])
		p["real_name"] = ""
		p["generic_name"] = ""
		p["name"] = ""
		p["first"] = ""
		p["last"] = ""
		p["src"] = "U18"
		p["data_src"] = "generated"
		p["draft_year"] = year
		p["draft_rank"] = r
		p["generated"] = true
		p["num"] = r
		for key in Ratings.STATS_ZERO_KEYS:
			p[key] = 0.0
		p["weight_kg"] = 0.0
		p["real_pos"] = Ratings.ROLE_SHORT_TO_POS.get(str(p["role"]), "MID")
		project(p)
		_age_into(p)
		_mature_entry(p)
		out.append(p)
	roll_fine_wine(out, "expansion-%s-%d%s-%d" % [code, year, salt, first_rank])
	GameDB.assign_aliases(out)
	return out


## The state-leaguers who fill out a League redraft: the real players run out
## short of full lists (director, 2026-11-09: "Full-size lists"). Ranked after
## the real class, unlisted until drafted.
const DEPTH_FIRST_RANK := 40

static func generate_depth_pool(count: int, year: int, salt: String) -> Array:
	var out := generate_expansion_list("DEPTH", year, count, salt, DEPTH_FIRST_RANK)
	for p in out:
		p["club"] = ""
		p["note"] = "State league, %d" % year
		p["draft_year"] = GameDB.DATA_SEASON
	return out


## Senior state-league clubs a mature-age expansion recruit comes from, by
## state (WA and SA's junior clubs are already their senior clubs).
## A VFL club is named by its code in data/state_leagues (GameDB.state_clubs),
## so a club that leaves the league (Aspley, 2026) drops out with the data.
## AFL Sydney and the TSL are outside the state leagues and stay named here.
const STATE_LEAGUE_CLUBS := {
	"VICM": ["BOX", "WIL", "PTM", "COB", "WER", "FRA"],
	"VICC": ["WER", "FRA", "WIL"],
	"QLD": ["SOU"],
	"NSW": [["Sydney University", "AFL Sydney"], ["Pennant Hills", "AFL Sydney"]],
	"TAS": [["Clarence", "TSL"], ["Glenorchy", "TSL"], ["North Launceston", "TSL"],
			["Launceston", "TSL"], ["Kingborough", "TSL"]],
}


## [name, league] pairs of the senior clubs a mature-age recruit from `state`
## can come from; a state code the dataset did not load is left out.
static func state_league_clubs(state: String) -> Array:
	var out := []
	for c in STATE_LEAGUE_CLUBS.get(state, []):
		if c is Array:
			out.append(c)
		elif GameDB.is_state_club(str(c)):
			var row: Dictionary = GameDB.state_clubs[str(c)]
			out.append([str(row["name"]), str(row["league"])])
	return out


## The type ranges are first-season players' (18 to 20): an expansion player
## older than that has played the seasons between, so his attributes move by
## the age curves of each (Growth.age_attrs, from FIRST_SEASON_AGE to his age)
## and his POT is worked out again at the new level.
## Example: a 24-year-old moves by his curves at 19, 20, 21, 22 and 23.
const FIRST_SEASON_AGE := 19


static func _age_into(p: Dictionary) -> void:
	var age := int(floor(float(p.get("age", 18.0))))
	if age <= FIRST_SEASON_AGE:
		return
	p["attr"] = Growth.age_attrs(p["attr"], FIRST_SEASON_AGE, age)
	p.erase("potential")
	Potential.assign(p)


## An expansion player of 20 or more did not come out of the under-18s in the
## club's first year: his record is a senior state-league season, and past
## draft age (Potential.MAX_PROSPECT_AGE) no draft-class ranking either. Only
## the history changes: his ratings and ceiling were already set (project,
## _age_into; a ceiling past 21 is his age's, never his rank's), and the pick
## of club is seeded by his id so no later player's rolls move.
static func _mature_entry(p: Dictionary) -> void:
	var age := float(p.get("age", 18.0))
	if age < 20.0:
		return
	var clubs: Array = state_league_clubs(str(p.get("draft_state", "")))
	if not clubs.is_empty():
		var club: Array = clubs[_rng_for("mature|%s" % str(p["id"])).randi_range(0, clubs.size() - 1)]
		p["draft_team"] = str(club[0])
		p["draft_league"] = str(club[1])
	if age > Potential.MAX_PROSPECT_AGE:
		p["draft_rank"] = 0


static func _generated_secondary(role: String, rng: RandomNumberGenerator) -> String:
	if rng.randf() > 0.30:
		return ""
	match role:
		"MID": return "FWD" if rng.randf() < 0.6 else "DEF"
		"DEF": return "MID"
		"FWD": return "MID" if rng.randf() < 0.7 else "RUCK"
		"RUCK": return "FWD"
	return ""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
static func _rng_for(key: String) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = int(key.hash()) * 2654435761 + 1013904223
	return rng


## Days between two ISO dates (Howard Hinnant's algorithm) - integer-exact,
## no Time API, no timezones.
static func days_between(from_iso: String, to_iso: String) -> int:
	return _days_from_civil(_parse_dto(to_iso)) - _days_from_civil(_parse_dto(from_iso))


static func _parse_dto(iso: String) -> Vector3i:
	if iso.length() < 10:
		return Vector3i(2026, 1, 1)
	return Vector3i(int(iso.substr(0, 4)), int(iso.substr(5, 2)), int(iso.substr(8, 2)))


static func _days_from_civil(d: Vector3i) -> int:
	var y := d.x
	if d.y <= 2:
		y -= 1
	var era := int(floor(float(y) / 400.0))
	var yoe := y - era * 400
	var doy := int(floor((153.0 * float(d.y + (9 if d.y <= 2 else -3)) + 2.0) / 5.0)) + d.z - 1
	var doe := yoe * 365 + int(floor(float(yoe) / 4.0)) - int(floor(float(yoe) / 100.0)) + doy
	return era * 146097 + doe - 719468
