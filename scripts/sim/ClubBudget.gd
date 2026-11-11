class_name ClubBudget
extends RefCounted
## Annual discretionary club spending. This is not a bank account: every
## off-season the board gives the same fixed departmental budget and the
## coach allocates it for the coming season.
##
## Three buckets, four funding levels each. The board gives $10.5m
## (director, 2026-11-06): Standard in all three costs $9.0m and leaves one
## step to spend, so any two lines can be Strong if the third is Minimal.
## High performance carries what the old
## Football department line did (TODO row 99, T9.Q14): one spend for the
## legs, the season peak and how sharply the game plan is carried out.

const ANNUAL_M := 10.5
const STANDARD := 1
const YOUNG_AGE := 22.0

const AREA_ORDER := ["recruiting", "development", "high_performance"]
const AREA_LABEL := {
	"recruiting": "Recruiting",
	"development": "Development",
	"high_performance": "High performance",
}
## The fourth area saves from before row 99 hold (fold_football).
const OLD_FOOTBALL := "football"
const LEVELS := [
	{"key": "minimal", "label": "Minimal", "cost_m": 1.5},
	{"key": "standard", "label": "Standard", "cost_m": 3.0},
	{"key": "strong", "label": "Strong", "cost_m": 4.5},
	{"key": "elite", "label": "Elite", "cost_m": 6.0},
]

## Multipliers relative to Standard. The final step is deliberately smaller
## than the first so Elite is specialization, not an automatic destination.
const SCOUT_UNCERTAINTY := [1.25, 1.00, 0.80, 0.65]
const DEVELOPMENT_XP := [0.90, 1.00, 1.10, 1.15]
const RECOVERY := [0.90, 1.00, 1.10, 1.20]
const TACTICS_EXEC := [0.95, 1.00, 1.05, 1.08]


static func defaults() -> Dictionary:
	return {
		"recruiting": STANDARD,
		"development": STANDARD,
		"high_performance": STANDARD,
	}


static func valid_area(area: String) -> bool:
	return AREA_ORDER.has(area)


static func clamp_level(level: int) -> int:
	return clampi(level, 0, LEVELS.size() - 1)


static func level_label(level: int) -> String:
	return str((LEVELS[clamp_level(level)] as Dictionary)["label"])


static func cost_m(level: int) -> float:
	return float((LEVELS[clamp_level(level)] as Dictionary)["cost_m"])


static func total_m(allocation: Dictionary) -> float:
	var total := 0.0
	for area in AREA_ORDER:
		total += cost_m(int(allocation.get(area, STANDARD)))
	return total


static func remaining_m(allocation: Dictionary) -> float:
	return ANNUAL_M - total_m(allocation)


static func scouting_mult(level: int) -> float:
	return float(SCOUT_UNCERTAINTY[clamp_level(level)])


static func development_mult(level: int) -> float:
	return float(DEVELOPMENT_XP[clamp_level(level)])


static func recovery_mult(level: int) -> float:
	return float(RECOVERY[clamp_level(level)])


## How sharply the coaches carry out the game plan, set by High performance.
static func tactics_mult(level: int) -> float:
	return float(TACTICS_EXEC[clamp_level(level)])


## An allocation saved before row 99 holds a fourth area, "football" (the
## Football department). It folds into High performance money for money:
## the board no longer funds that line's Standard $3m, and whatever the coach
## had moved above or below Standard there moves into High performance, one
## level a step (each step is $1.5m on every line). So the other two lines
## keep their exact funding, and High performance ends at its old level plus
## the Football department's steps from Standard, held to Minimal..Elite.
## An old save spent at most $12m on four lines, so the fold spends at most
## $9m, or $10.5m when both were Minimal (High performance cannot drop below
## Minimal): every legal old allocation fits the $10.5m, and what it leaves
## unspent is there to allocate next off-season. Only a hand-edited save can
## come out over budget; the best-funded line other than High performance then
## drops a step, Recruiting first on a tie, until it fits.
static func fold_football(allocation: Dictionary) -> Dictionary:
	var out := allocation.duplicate()
	if not out.has(OLD_FOOTBALL):
		return out
	var f := clamp_level(int(out[OLD_FOOTBALL]))
	out.erase(OLD_FOOTBALL)
	var hp := clamp_level(int(out.get("high_performance", STANDARD)))
	out["high_performance"] = clamp_level(hp + f - STANDARD)
	for area in AREA_ORDER:
		out[area] = clamp_level(int(out.get(area, STANDARD)))
	while total_m(out) > ANNUAL_M + 0.001:
		var top := ""
		for area in AREA_ORDER:
			if area != "high_performance" and int(out[area]) > 0 					and (top == "" or int(out[area]) > int(out[top])):
				top = area
		if top == "":
			break
		out[top] = int(out[top]) - 1
	return out


## The furthest a prospect's true rating fell outside the scouts' range, per
## funding level (measured, tools/measure_scout_miss.gd).
const SCOUT_WORST_MISS := [7, 6, 5, 4]

## Your recruiters' POT range on another club's player or a free agent, per
## funding level: about one read in this many has his true potential outside
## it, and by at most this much. Measured over 35 off-seasons of six seeded
## careers, every club as the reader, 457,871 reads a level
## (tools/balance/rival_reads.gd): 19.5%, 16.2%, 13.1% and 10.6% miss, the
## worst by 7, 5, 5 and 3. The worst is also the most the read can miss by
## (DraftScouting.pot_read). The reads sharpen as a player's games add up, so
## they miss a little more often early in a career (1 in 4 to 1 in 8 at the
## first off-season). tests/test_workload.gd holds both figures to the
## measured counts (tools/balance/rival_reads_measured.json) and to the reads.
const RIVAL_POT_MISS_IN := [5, 6, 8, 9]
const RIVAL_POT_WORST_MISS := [7, 5, 5, 3]
## The same reads on a player under 50 games: about one in this many misses,
## at every funding level (143,164 reads a level: 27.2%, 26.7%, 22.8% and
## 22.7%). Named in the same line so the coach sees the bigger miss on young
## players; held to the measured counts by tests/test_workload.gd.
const RIVAL_POT_YOUNG_MISS_IN := [4, 4, 4, 4]


## The UI uses these exact statements before the player spends.
static func benefit_text(area: String, level: int) -> String:
	level = clamp_level(level)
	if area == "recruiting":
		# The miss share and the worst miss are measured (tools/measure_scout_miss.gd,
		# ten draft classes, 514 prospects): funding narrows the scouts' ranges,
		# so about the same share of reads miss at every level, by less.
		var miss := "about 1 read in 7 misses his true rating, by up to %d. Other clubs' players: about 1 POT read in %d misses (1\u00a0in\u00a0%d under 50 games), by up to %d" 				% [SCOUT_WORST_MISS[level], RIVAL_POT_MISS_IN[level], RIVAL_POT_YOUNG_MISS_IN[level], RIVAL_POT_WORST_MISS[level]]
		if level == 0:
			return "Prospect scouts' ranges are 25% wider than standard: " + miss + "."
		if level == 1:
			return "Prospect scouts' ranges are the standard width: " + miss + "."
		if level == 2:
			return "Prospect scouts' ranges are 20% narrower than standard: " + miss + "."
		return "Prospect scouts' ranges are 35% narrower than standard: " + miss + "."
	if area == "development":
		if level == 0:
			return "Players aged 22 and under develop 10% slower."
		if level == 1:
			return "Players aged 22 and under develop at the standard rate."
		if level == 2:
			return "Players aged 22 and under develop 10% faster."
		return "Players aged 22 and under develop 15% faster."
	if area == "high_performance":
		# All it buys (recovery, the season peak's height and timing, the
		# game plan's edge) and what it costs, worked out from the constants
		# (Conditioning.department_words).
		return Conditioning.department_words(level)
	return ""
