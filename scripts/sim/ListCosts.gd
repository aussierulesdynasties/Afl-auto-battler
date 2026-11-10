class_name ListCosts
extends RefCounted
## What the list's one-sided options cost (row T1.R26, L4; director 2026-11-10,
## "Costs in the rule's spirit"). Each cost lasts the coming season and ends
## when its off-season opens (GameState.open_offseason calls `season_over`).
## Every club pays them by the same rules: a rival that re-signs a player under
## his ask stings him just as you do.

## Re-signed under his ask: his morale reads this many points (of 100) lower
## all season ("morale -10% for the season").
const HAGGLE_STING := 10
## Released with seasons still to run: this share of what is left on his
## contract stays on the club's cap for the coming season.
const RELEASE_DEAD_SHARE := 0.5
## Asked to go around again, a retiree fit to play on says yes this often...
const ASK_AGAIN_YES := 0.4
## ...and his legs are this much down all season: he tires this much faster.
const OLD_LEGS := 1.15

const HAGGLE_GAIN := "you save %s a season, %s under his ask"
const HAGGLE_COST := "if he signs, his morale is %s lower all season"
const RELEASE_GAIN := "a list spot, and %s a season off your books"
const RELEASE_COST := "%s of his remaining contract (%s) stays on your cap next season"
const RELEASE_COST_NONE := "nothing stays on your cap: his contract is up"
const ASK_GAIN := "%s chance he says yes and plays one more season"
const ASK_GAIN_NONE := "none: %s"
const ASK_COST := "if he says yes, his legs are %s down all season (he tires %s faster)"


static func _pct(share: float) -> String:
	return "%d%%" % roundi(absf(share) * 100.0)


## Gain / Cost for an offer of `salary` to your own player whose ask is `ask`.
## [] when the offer is at or above his ask (no haggle, no sting).
static func haggle_lines(salary: int, ask: int) -> Array:
	if salary >= ask or ask <= 0:
		return []
	return [GateOdds.gain(HAGGLE_GAIN % [Contracts.money(ask - salary), _pct(float(ask - salary) / float(ask))]),
			GateOdds.cost(HAGGLE_COST % _pct(HAGGLE_STING / 100.0))]


## Seasons still to run on his contract after this one, from the off-season.
static func seasons_left(p: Dictionary) -> int:
	return maxi(0, int(p.get("contract_years", 1)) - 1)


## What stays on the cap if he is released now.
static func dead_money(p: Dictionary) -> int:
	return int(round(float(p.get("salary", 0)) * seasons_left(p) * RELEASE_DEAD_SHARE))


static func release_lines(p: Dictionary) -> Array:
	var g := GateOdds.gain(RELEASE_GAIN % Contracts.money(int(p.get("salary", 0))))
	var dead := dead_money(p)
	if dead <= 0:
		return [g, GateOdds.cost(RELEASE_COST_NONE)]
	return [g, GateOdds.cost(RELEASE_COST % [Contracts.money(dead), _pct(RELEASE_DEAD_SHARE)])]


## `no_reason`: why he would say no whatever you say ("" when he might say yes).
static func ask_lines(no_reason: String) -> Array:
	var g := ASK_GAIN_NONE % no_reason.trim_suffix(".").to_lower() if no_reason != "" \
			else ASK_GAIN % _pct(ASK_AGAIN_YES)
	return [GateOdds.gain(g), GateOdds.cost(ASK_COST % [_pct(OLD_LEGS - 1.0), _pct(OLD_LEGS - 1.0)])]


## The sting a player carries this season (0 when none).
static func sting(p: Dictionary) -> int:
	return HAGGLE_STING if p.has("haggle_sting") else 0


## Legs multiplier on his energy drain this season.
static func legs(p: Dictionary) -> float:
	return OLD_LEGS if p.has("old_legs") else 1.0


## The season these were for is over: clear them off `list`.
static func season_over(list: Array, finished: int) -> void:
	for p in list:
		for k in ["haggle_sting", "old_legs"]:
			if p.has(k) and int(p[k]) <= finished:
				p.erase(k)
