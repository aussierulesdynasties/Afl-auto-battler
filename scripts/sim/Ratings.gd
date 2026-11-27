class_name Ratings
extends RefCounted
## Match tunables, squad selection and the salary curve. A player's rating
## is not made here: his 18 attributes are loaded as they are (GameDB) and
## his OVR is read from them (Rating.gd), director, Bible 4.2.30a.

## Tunables - single source of truth for match balance. The copy in
## tools/sim_harness.py (dict `T`) is stale since 2026-10-08; do not mirror
## match tunables there. Guard: tests/run_calibration_tests.gd.
const T := {
	"chains_per_game": 200,          # possession chains across BOTH teams
	"max_touches_per_chain": 14,
	"forward50_line": 35.0,          # metres from the centre square
	"goal_line": 85.0,
	"metres_gain_mean": 9.7,         # base metres per effective disposal
	"tackle_retention": 0.44,        # attacking team wins the ball back
	"pressure_base": 0.160,          # chance a touch is tackled
	"clanger_per_chain": 0.625,     # chance the chain ends in an error
	"clanger_is_free": 0.43,         # ...of which are free kicks against
	"mark_share_of_kicks": 0.240,    # 0.280 before the D50 chip (2026-11-14): chips are marked 2.8x as often; 0.327 before the D50 clearing kick (2026-11-07): marks per kick back to real (0.43)
	"handball_share": Attributes.HANDBALL_SHARE,
	"inside50_goal": 0.262,          # of inside-50 entries (0.279 before frees in 50 became set shots, backlog item 24; 0.269 before forward archetypes, ARD-M3-002)
	"inside50_behind": 0.180,
	"stoppage_share": 0.42,          # chains that begin at a genuine stoppage
	"hitouts_per_stoppage": 0.78,    # split between the two rucks
	"clearance_per_stoppage": 0.76,  # to the team that wins the stoppage (0.815 before every feature was on: 38.9 a team, real 36.1)
	"one_percenter_share": 0.72,     # of inside-50 entries that yield a 1% (0.78 before the row 136 spoils tuning added credits)
	"rebound_on_exit": 0.55,         # defensive-half chains that yield a reb50
	"shooter_power": 0.5,            # how strongly shots go to the best kicks
	"home_ground_bonus": 0.030,
	"contest_swing": 360.0,          # higher == less sensitive to strength
	"contest_clamp": 0.60,           # max stoppage win probability
}

## Match flow (row 11, director 2026-10-10): stoppages come from contests that
## lock up, a won ball is played on, chains are shorter and more numerous. These
## replace the same keys in T for every match. Measured against main's current calibration
## (after #885): docs/research/MATCH_FLOW_AUDIT_2026-11-04.md has the bands, and
## three still fall short. These are absolute values, not offsets: a later change
## to T for these keys does not reach a match until FLOW is updated too
## (tests/test_match_flow.gd checks every key here still exists in T).
const FLOW := {
	"chains_per_game": 255,         # 275 before kicks went longer (row 201 gap 6)
	"max_touches_per_chain": 10,
	"metres_gain_mean": 11.3,
	"tackle_retention": 0.25,
	"inside50_goal": 0.255,         # 0.235 before the D50 clearing kick (2026-11-07): goals per entry back to real (0.24)
	"inside50_behind": 0.175,
}

## On-ground structure: 18 players = 6 DEF, 6 MID, 6 FWD, where the ruck is
## counted with midfield (1 RUCK + 5 MID). Order matters - select_22() fills
## slots in this sequence.
const GROUND_SLOTS := [["RUCK", 1], ["MID", 5], ["DEF", 6], ["FWD", 6]]
## The match-day squad is 18 on the ground plus five interchange - 23, with
## no substitute role (ARD-M5-001, director 2026-10-06). Every bench player
## rotates, covers injuries and plays as fully as the other four.
const INTERCHANGE := 5
## The bench size selection uses: INTERCHANGE, changed only by audits that
## compare squad sizes on the same seeds (tools/audit/interchange_impl.gd).
static var bench_size := INTERCHANGE


## The season's bench: bench_size in the game's league, the year's interchange
## count in a Legacy season (EraRules: two to 1993, three 1994-97, four
## 1998-2010, three 2011-15, four 2016-25).
static func bench() -> int:
	return EraRules.interchange() if EraRules.is_era(EraRules.year) else bench_size


## Substitutes named beside the bench in a Legacy season (EraRules): one in
## 2011-15 and 2021-25, none in the game's league.
static func subs() -> int:
	return EraRules.substitutes()
## Audits only: false reproduces the old bench (best of the rest, no line
## cover, no dual ruck) for a before/after comparison.
static var bench_rules := true
## A second position (natural or learned) earns a spot on merit: a player
## left out who plays a line better than its weakest starter takes that spot
## (director, 2026-10-06). Audits only: false gives the old order, where a
## second position was used only once a line ran out of its own players.
static var merit_lines := true
## The lines an auto-picked bench covers before taking the best of the rest.
const BENCH_COVER := ["FWD", "DEF", "MID"]
## How close (OVR) a spare ruck must be for an AI club to run dual ruck.
const DUAL_RUCK_MARGIN := 5.0
const LIST_SIZE := 44

## Raw season columns every player dict carries. GameDB.STAT_KEYS must match;
## prospects (no AFL stats) get these zero-filled for the display rows.
const STATS_ZERO_KEYS := ["gm", "ki", "mk", "hb", "di", "gl", "bh", "ho", "tk", "rb",
		"if50", "cl", "cg", "ff", "fa", "br", "cp", "up", "cm", "mi",
		"onepct", "bo", "ga", "pctp"]

## Engine role -> the three-letter position tag used by the CSVs.
const ROLE_SHORT_TO_POS := {"RUCK": "RUC", "MID": "MID", "DEF": "DEF", "FWD": "FWD"}

static func role_tag(p: Dictionary) -> String:
	var primary := str(p.get("role", ""))
	var tag := primary
	for r in second_positions(p):
		if str(r) != primary:
			tag += "/" + str(r)
	return tag


## Every position he can be picked in: his own, his second, and any he has
## learned in training (GameState: learning another position).
static func positions(p: Dictionary) -> Array:
	var out := [str(p.get("own_role", p.get("role", "")))]
	for r in second_positions(p):
		if not out.has(r):
			out.append(r)
	return out


## His second position and any learned after it.
static func second_positions(p: Dictionary) -> Array:
	var out := []
	var r2 := str(p.get("role2", ""))
	if r2 != "":
		out.append(r2)
	for r in p.get("learned", []):
		if str(r) != "" and not out.has(str(r)):
			out.append(str(r))
	# A Unicorn plays forward, midfield and back (Traits.is_unicorn).
	if Traits.is_unicorn(p):
		var own := str(p.get("own_role", p.get("role", "")))
		for line in Traits.UNICORN_LINES:
			if line != own and not out.has(line):
				out.append(line)
	return out


static func plays_role(p: Dictionary, role: String) -> bool:
	if role == "":
		return true
	return str(p.get("role", "")) == role or second_positions(p).has(role)


## Plausible annual AFL salary from the overall rating. This is the simple
## list-management base salary used by the game, not a claim to reproduce
## every real AFL payment (match payments/ASAs are deliberately out of scope).
## The curve preserves the old 1-10 salary tiers while expressing them in
## football money: depth at the senior floor, established players in the
## hundreds of thousands, and genuine stars above $1m.
## The middle points sit on the stretched OVR scale (Rating.STRETCH): each pays
## what the same place in the 2026 league was paid before the rebuild (the
## median player, 58 then and 62 now, about $375k), so lists still fit the cap.
## From 79 up the points are the stretch's own stars (2025 Bontempelli 90).
static func salary_value(overall: int) -> int:
	# Annual salary the market pays for a rating: it rises smoothly between
	# these points (no cliff for one rating point), from the senior minimum.
	var points := [[40, 155000], [50, 255000], [58, 335000], [64, 415000],
			[70, 515000], [79, 740000], [85, 875000], [90, 1030000], [99, 1250000]]
	if overall <= int(points[0][0]):
		return int(points[0][1])
	for i in range(1, points.size()):
		if overall <= int(points[i][0]):
			var lo: Array = points[i - 1]
			var hi: Array = points[i]
			var t := float(overall - int(lo[0])) / float(int(hi[0]) - int(lo[0]))
			return int(round(lerpf(float(lo[1]), float(hi[1]), t) / 5000.0)) * 5000
	return int(points[points.size() - 1][1])


## His salary value, read from his OVR (never stored: Bible 4.2.30a, OVR is
## read-only and derived).
static func value_of(p: Dictionary) -> int:
	return salary_value(int(Rating.ovr(p, 50)))


# ---------------------------------------------------------------------------
# Squad selection
# ---------------------------------------------------------------------------
## Best 18 on the ground respecting the 1R/5M/6D/6F structure, plus
## INTERCHANGE (5) on the bench: the match-day 23. (The name predates the
## fifth interchange.) Structural shortfalls (a list with no recognised ruckman, say) are
## backfilled by overall rating so a team always fields 18.
## `dual`: run a second ruck on the bench - 1 yes (a coach's call: he takes
## the first bench spot), 0 no, -1 the AI's rule (only when the spare ruck is
## within DUAL_RUCK_MARGIN of the bench player he would replace).
static func select_22(list_players: Array, dual := -1) -> Dictionary:
	var pool := list_players.duplicate()
	# A player promised a game this week (a kid given his chance, a talk) or a
	# run (Backing) is first in line for his own position; then the best
	# available.
	var promised := {}
	for p in pool:
		if p.has("expects_game") or Backing.is_active(p):
			promised[p["id"]] = true
	# Each player's place in the queue is read once, not at every comparison
	# (a sort compares each player many times): the same order.
	if pool.size() > 1:
		var queue := []
		for p in pool:
			queue.append([promised.has(p["id"]), float(Rating.ovr(p)) * Workload.selection_factor(p), p])
		queue.sort_custom(func(a, b):
			if a[0] != b[0]:
				return a[0]
			return a[1] > b[1])
		pool = queue.map(func(e): return e[2])

	var ground: Array = []
	var used := {}
	for slot in GROUND_SLOTS:
		var role: String = slot[0]
		var need: int = slot[1]
		var added := 0
		# Ruck is a specialist job: among recognised primary/secondary rucks,
		# pick the best tap player rather than the highest overall. This keeps
		# a high-OVR part-timer from displacing the side's actual best ruck.
		if role == "RUCK":
			var recognised := []
			for p in pool:
				if plays_role(p, "RUCK") and not used.has(p["id"]):
					recognised.append(p)
			# The best tap player first, but a promised ruck is first in line.
			var first := []
			var others := []
			for p in by_ruck(recognised):
				if promised.has(p["id"]):
					first.append(p)
				else:
					others.append(p)
			for p in first + others:
				if added >= need:
					break
				ground.append(_for_slot(p, role))
				used[p["id"]] = true
				added += 1
		else:
			for p in pool:
				if added >= need:
					break
				if str(p["role"]) == role and not used.has(p["id"]):
					ground.append(_for_slot(p, role))
					used[p["id"]] = true
					added += 1
			# A MID/FWD can fill a forward slot once the primary forwards are gone.
			for p in pool:
				if added >= need:
					break
				if second_positions(p).has(role) and not used.has(p["id"]):
					ground.append(_for_slot(p, role))
					used[p["id"]] = true
					added += 1
		# No recognised ruck on the list: a backup key forward goes up
		# (backup_ruck), else the best tap player available, not simply the
		# best overall player.
		if role == "RUCK" and added < need:
			for p in ruck_fill_order(pool):
				if added >= need:
					break
				if not used.has(p["id"]):
					ground.append(_for_slot(p, role))
					used[p["id"]] = true
					added += 1
	if merit_lines:
		_merit_swaps(pool, ground, used, promised)
	for p in pool:
		if ground.size() >= 18:
			break
		if not used.has(p["id"]):
			ground.append(_for_slot(p, str(p["role"])))
			used[p["id"]] = true

	# The bench covers the lines first - a forward, a defender and a
	# midfielder, the best of each left - then the best of the rest, so a
	# tired forward is relieved by a forward, as on a real interchange bench.
	# Dual ruck: the second ruck takes the first spot.
	var bench: Array = []
	var spare_ruck: Dictionary = {}
	for p in by_ruck(pool):
		if not used.has(p["id"]) and str(p.get("role", "")) == "RUCK":
			spare_ruck = p
			break
	if dual == 1 and bench_rules and not spare_ruck.is_empty():
		bench.append(spare_ruck)
		used[spare_ruck["id"]] = true
	for line in (BENCH_COVER if bench_rules else []):
		for p in pool:
			if bench.size() >= bench():
				break
			if not used.has(p["id"]) and str(p.get("role", "")) == line:
				bench.append(p)
				used[p["id"]] = true
				break
	for p in pool:
		if bench.size() >= bench():
			break
		if not used.has(p["id"]):
			bench.append(p)
			used[p["id"]] = true

	# The AI's call: a second ruck earns the last spot when he is close to
	# the player he'd replace.
	if dual == -1 and bench_rules and not spare_ruck.is_empty() and not used.has(spare_ruck["id"]) \
			and bench.size() >= bench() and bench() > BENCH_COVER.size():
		var last: Dictionary = bench[bench.size() - 1]
		if float(Rating.ovr(spare_ruck)) >= float(Rating.ovr(last)) - DUAL_RUCK_MARGIN:
			used.erase(last["id"])
			bench[bench.size() - 1] = spare_ruck
			used[spare_ruck["id"]] = true

	ground = ground.slice(0, 18)
	key_posts(ground)
	Roles.mark_wings(ground)
	return {"ground": ground, "bench": bench}


## The auto-pick's key posts (Roles.key_post_order): each line's players are
## re-laid in their own places in `ground`, so the line reads in spot order.
static func key_posts(ground: Array) -> void:
	for line in ["DEF", "FWD"]:
		var at: Array = []
		var line_players: Array = []
		for i in range(ground.size()):
			if str(ground[i].get("role", "")) == line:
				at.append(i)
				line_players.append(ground[i])
		var laid := Roles.key_post_order(line_players, line)
		for k in range(at.size()):
			ground[at[k]] = laid[k]


## True when a player can take the field (not injured, suspended or rested).
static func available(p: Dictionary) -> bool:
	return int(p.get("injury_weeks", 0)) <= 0 \
			and int(p.get("suspension_weeks", 0)) <= 0 \
			and not p.has("season_ban") \
			and not bool(p.get("rested", false))


## The match-day 22. With an empty selection the best available side is
## picked automatically (select_22). A selection is
## {"RUCK": [ids], "MID": [...], "WING": [...], "DEF": [...], "FWD": [...],
## "BENCH": [...], "OUT": [ids]} - WING names two of the five midfielders
## (Roles), MID the centre square: named players take their slots (any player can be named in
## any position), and a gap - an injured or departed player, or a slot left
## short - goes to the best-suited fit player, from the named bench and the
## players not named alike (director, 2026-11-15: "best player suited gets
## the spot, idc whether they came from the bench or reserves"), and only as a
## last resort to one marked OUT (a promise's swap). Best suited is the
## automatic way: his own position first, then his second, then anyone, each
## by rating and freshness. Injured players never play.
static func select_side(list_players: Array, selection: Dictionary = {}) -> Dictionary:
	var pool: Array = []
	for p in list_players:
		if available(p):
			pool.append(p)
	# The dual-ruck call travels with the selection; a selection that is only
	# that call is still the auto-pick.
	var dual := -1
	if selection.has("DUAL_RUCK"):
		dual = 1 if bool(selection["DUAL_RUCK"]) else 0
		selection = selection.duplicate()
		selection.erase("DUAL_RUCK")
	# A role trial rides with the selection like the dual-ruck call: under the
	# auto-pick he plays his trial position (his own becomes his second).
	var trial: Dictionary = {}
	if selection.has("TRIAL"):
		trial = selection["TRIAL"]
		selection = selection.duplicate()
		selection.erase("TRIAL")
	if selection.is_empty():
		if not trial.is_empty():
			pool = _with_trial(pool, trial)
		return select_22(pool, dual)
	pool.sort_custom(func(a, b):
		return float(Rating.ovr(a)) * Workload.selection_factor(a) > float(Rating.ovr(b)) * Workload.selection_factor(b))
	var by_id := {}
	for p in pool:
		by_id[str(p["id"])] = p
	var ground: Array = []
	var used := {}
	for slot in GROUND_SLOTS:
		var role: String = slot[0]
		var added := 0
		# Wings are two of the five midfield spots.
		var named: Array = selection.get(role, [])
		if role == "MID":
			named = (selection.get("WING", []) as Array) + named
		for id in named:
			if added >= int(slot[1]):
				break
			var p = by_id.get(str(id))
			if p == null or used.has(str(id)):
				continue
			ground.append(_for_slot(p, role))
			used[str(id)] = true
			added += 1
	# Fill order for gaps: 0 the bench and the unnamed alike (best suited
	# wins), 1 players marked OUT.
	var tier := {}
	for id in selection.get("OUT", []):
		if by_id.has(str(id)) and not used.has(str(id)):
			tier[str(id)] = 1
	for pass_tier in [0, 1]:
		for slot in GROUND_SLOTS:
			var role: String = slot[0]
			var have := 0
			for g in ground:
				if str(g["role"]) == role:
					have += 1
			if role == "RUCK":
				# A missing named ruck is filled by the best available recognised
				# ruck in this selection tier, not whichever ruck has the best OVR.
				var recognised := []
				for p in pool:
					var id := str(p["id"])
					if not used.has(id) and int(tier.get(id, 0)) == pass_tier and plays_role(p, "RUCK"):
						recognised.append(p)
				for p in by_ruck(recognised):
					if have >= int(slot[1]):
						break
					var id := str(p["id"])
					ground.append(_for_slot(p, role))
					used[id] = true
					have += 1
			else:
				for key in ["role", "role2"]:
					for p in pool:
						if have >= int(slot[1]):
							break
						var id := str(p["id"])
						if used.has(id) or int(tier.get(id, 0)) != pass_tier:
							continue
						if (str(p.get("role", "")) == role) if key == "role" else second_positions(p).has(role):
							ground.append(_for_slot(p, role))
							used[id] = true
							have += 1
			for p in (ruck_fill_order(pool) if role == "RUCK" else pool):
				if have >= int(slot[1]):
					break
				var id := str(p["id"])
				if used.has(id) or int(tier.get(id, 0)) != pass_tier:
					continue
				ground.append(_for_slot(p, role))
				used[id] = true
				have += 1
	var bench: Array = []
	for id in selection.get("BENCH", []):
		if bench.size() >= bench():
			break
		if by_id.has(str(id)) and not used.has(str(id)):
			bench.append(by_id[str(id)])
			used[str(id)] = true
	for pass_tier in [0, 1]:
		for p in pool:
			if bench.size() >= bench():
				break
			var id := str(p["id"])
			if not used.has(id) and int(tier.get(id, 0)) == pass_tier:
				bench.append(p)
				used[id] = true
	Roles.mark_wings(ground, selection.get("WING", []))
	return {"ground": ground, "bench": bench}


## The side "Best side on form" names for a simmed week (director, 2026-11-15:
## "100% of the selection should be determined only by form, thats what the
## copy says it does"). `form`: player id -> his form, the match rating a game
## over his last games (PlayerCondition.form: seniors, else the twos; -1 when
## he has played neither this season). Each line takes the players in the best
## form who play it (his own position, then his second, then anyone); the
## bench the next best. Rating plays no part, except to order the players
## with no game yet, who come after everyone with form. A promised player
## (a run, a talk) is still first in line, as in select_22: a promise made
## stands. Returns a selection: {"RUCK", "MID", "DEF", "FWD", "BENCH": [ids]}.
static func select_on_form(list_players: Array, form: Dictionary) -> Dictionary:
	var pool: Array = []
	var promised := {}
	for p in list_players:
		if available(p):
			pool.append(p)
			if p.has("expects_game") or Backing.is_active(p):
				promised[str(p["id"])] = true
	var score := func(p: Dictionary) -> float:
		var v := float(form.get(str(p["id"]), -1))
		return v if v >= 0.0 else -1000.0 + float(Rating.ovr(p, 0))
	pool.sort_custom(func(a, b):
		var pa := promised.has(str(a["id"]))
		if pa != promised.has(str(b["id"])):
			return pa
		var sa: float = score.call(a)
		var sb: float = score.call(b)
		if sa != sb:
			return sa > sb
		return str(a["id"]) < str(b["id"]))
	var sel := {"RUCK": [], "MID": [], "DEF": [], "FWD": [], "BENCH": []}
	var used := {}
	for pass_kind in ["own", "second", "any"]:
		for slot in GROUND_SLOTS:
			var role: String = slot[0]
			for p in pool:
				if (sel[role] as Array).size() >= int(slot[1]):
					break
				var id := str(p["id"])
				if used.has(id):
					continue
				var fits: bool = (str(p.get("role", "")) == role or (role == "RUCK" and plays_role(p, "RUCK"))) if pass_kind == "own" 						else (second_positions(p).has(role) if pass_kind == "second" else true)
				if fits:
					(sel[role] as Array).append(id)
					used[id] = true
	for p in pool:
		if (sel["BENCH"] as Array).size() >= bench():
			break
		if not used.has(str(p["id"])):
			(sel["BENCH"] as Array).append(str(p["id"]))
			used[str(p["id"])] = true
	return sel


## His rating playing `line`: his OVR at the slot (Rating.at_line).
static func line_rating(p: Dictionary, line: String) -> float:
	if (p.get("attr", {}) as Dictionary).is_empty():
		return 0.0
	return float(Rating.at_line(p, line))


## The merit pass of the auto-pick: in the midfield, back and forward lines,
## the best player left out who can play the line (a second position) takes
## the place of its weakest starter when he rates higher there. A promised
## starter keeps his place; the ruck slot, the dual ruck and the bench's line
## cover are untouched (the dropped starter goes back to the pool and can make
## the bench).
static func _merit_swaps(pool: Array, ground: Array, used: Dictionary, promised: Dictionary) -> void:
	var by_id := {}
	for p in pool:
		by_id[p["id"]] = p
	for line in ["MID", "DEF", "FWD"]:
		# Who is left out and can play the line, valued once (most lines have
		# nobody, and the line is skipped without rating anyone).
		var cands := {}
		for p in pool:
			if not used.has(p["id"]) and second_positions(p).has(line):
				cands[p["id"]] = line_rating(p, line) * Workload.selection_factor(p)
		if cands.is_empty():
			continue
		var starters := {}
		for g in ground:
			if str(g["role"]) == line and not promised.has(g["id"]) and by_id.has(g["id"]):
				var q: Dictionary = by_id[g["id"]]
				starters[g["id"]] = line_rating(q, line) * Workload.selection_factor(q)
		for guard in range(6):
			var weak := -1
			var weak_v := INF
			for i in range(ground.size()):
				var id = ground[i]["id"]
				if str(ground[i]["role"]) == line and starters.has(id) and float(starters[id]) < weak_v:
					weak_v = float(starters[id])
					weak = i
			if weak < 0:
				break
			var best = null
			var best_v := weak_v
			for id in cands:
				if not used.has(id) and float(cands[id]) > best_v:
					best_v = float(cands[id])
					best = id
			if best == null:
				break
			used.erase(ground[weak]["id"])
			starters.erase(ground[weak]["id"])
			ground[weak] = _for_slot(by_id[best], line)
			used[best] = true
			starters[best] = best_v


## A key forward who goes up when no ruck is there (director, 2026-11-26:
## "allow key forwards to ruck in substitute IF they have done so IRL or are at
## a minimum height threshold as the default backup"): a key forward by his own
## position with a hit-out on his real AFL stats sheet (the real season he is
## rated on), or one BACKUP_RUCK_CM or taller, the height the game asks of a
## player learning the ruck (GameState.RUCK_CM).
const BACKUP_RUCK_CM := 196.0


static func backup_ruck(p: Dictionary) -> bool:
	var own := str(p.get("own_role", p.get("role", "")))
	if own != "FWD":
		return false
	var view := p
	if str(p.get("role", "")) != "FWD":
		view = p.duplicate()
		view["role"] = "FWD"
	if not Matchups.is_key_forward(view):
		return false
	return float(p.get("ho", 0.0)) > 0.0 or float(p.get("height_cm", 0.0)) >= BACKUP_RUCK_CM


## Who fills an empty ruck spot, in order: rucks, then the backup key
## forwards (backup_ruck), then everyone else, each by ruck work (by_ruck).
static func ruck_fill_order(players: Array) -> Array:
	var rucks := []
	var backups := []
	var rest := []
	for p in by_ruck(players):
		if plays_role(p, "RUCK"):
			rucks.append(p)
		elif backup_ruck(p):
			backups.append(p)
		else:
			rest.append(p)
	return rucks + backups + rest


## Players ordered by ruck work, best first (ties by overall), for filling
## an empty ruck spot with the nearest thing to a ruckman.
static func by_ruck(players: Array) -> Array:
	if players.size() < 2:
		return players.duplicate()
	# Each player's ruck work and overall read once, not at every comparison.
	var keyed := []
	for p in players:
		keyed.append([float(p["attr"]["ruck"]), int(Rating.ovr(p)), p])
	keyed.sort_custom(func(a, b):
		if a[0] != b[0]:
			return a[0] > b[0]
		return a[1] > b[1])
	return keyed.map(func(e): return e[2])


## The pool with each trial player listed in his trial position: his own
## position becomes his second, so every pick path treats him as a player of
## the new role. {id: role}.
static func _with_trial(pool: Array, trial: Dictionary) -> Array:
	var out := []
	for p in pool:
		var role := str(trial.get(str(p["id"]), ""))
		if role == "" or role == str(p.get("role", "")):
			out.append(p)
			continue
		var c: Dictionary = p.duplicate()
		c["own_role"] = str(p.get("own_role", p.get("role", "")))
		c["role2"] = str(p.get("role", ""))
		c["role"] = role
		out.append(c)
	return out


## Copy so the match-day slot does not rewrite the list player's natural role.
static func _for_slot(p: Dictionary, slot: String) -> Dictionary:
	var copy := p.duplicate()
	copy["list_tag"] = role_tag(p)
	# His own position, kept through every re-slotting (a copy of a copy
	# would otherwise take the last slot as his position). Display only.
	copy["own_role"] = str(p.get("own_role", p.get("role", "")))
	copy["role"] = slot
	return copy
