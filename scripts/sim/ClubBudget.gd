class_name ClubBudget
extends RefCounted
## Annual discretionary club spending. This is not a bank account: every
## off-season the board gives the same fixed departmental budget and the
## coach allocates it for the coming season.
##
## Three buckets, four funding levels each. Standard in all three costs
## exactly the full annual budget. High performance carries what the old
## Football department line did (TODO row 99, T9.Q14): one spend for the
## legs, the season peak and how sharply the game plan is carried out.

const ANNUAL_M := 9.0
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
## Both at Minimal is the one legal old allocation it may not pay for ($1.5m
## short when the other two hold more than $7.5m): the best-funded other line
## drops a step, Recruiting first on a tie. Any allocation still over budget
## (a hand-edited save) is trimmed the same way until it fits.
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


## The UI uses these exact statements before the player spends.
static func benefit_text(area: String, level: int) -> String:
	level = clamp_level(level)
	if area == "recruiting":
		if level == 0:
			return "Prospect scouting uncertainty is 25% wider than standard."
		if level == 1:
			return "Prospect scouting uncertainty is at the standard level."
		if level == 2:
			return "Prospect scouting uncertainty is 20% narrower than standard."
		return "Prospect scouting uncertainty is 35% narrower than standard."
	if area == "development":
		if level == 0:
			return "Players aged 22 and under earn 10% less development XP."
		if level == 1:
			return "Players aged 22 and under earn standard development XP."
		if level == 2:
			return "Players aged 22 and under earn 10% more development XP."
		return "Players aged 22 and under earn 15% more development XP."
	if area == "high_performance":
		# All it buys (recovery, the season peak's height and timing, the
		# game plan's edge) and what it costs, worked out from the constants
		# (Conditioning.department_words).
		return Conditioning.department_words(level)
	return ""
