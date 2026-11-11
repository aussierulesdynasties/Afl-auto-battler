class_name ListStings
extends RefCounted
## The list costs' season-long effects and sizes (row T1.R26 L4, director
## 2026-11-10), with no dependencies, so the sim core (Workload, ClubLife,
## Retirement) can read them in a --script runner. The Gain / Cost copy is
## ListCosts.

## Re-signed under his ask: his morale reads up to this many points (of 100)
## lower all season, the full sting for a deal at his floor (the least he
## takes) and in proportion to the share of the gap saved above it (director
## 2026-11-10, "Costs in the rule's spirit": a small haggle stings a little).
const HAGGLE_STING := 10
## Released with seasons still to run: this share of what is left on his
## contract stays on the club's cap for the coming season.
const RELEASE_DEAD_SHARE := 0.5
## Asked to go around again, a retiree fit to play on says yes this often...
const ASK_AGAIN_YES := 0.4
## ...and his legs are this much down all season: he tires this much faster.
const OLD_LEGS := 1.15

## Asked to go around again, a player who says yes cannot be released by his
## club until the next off-season (director 2026-11-10): the ask's other cost.

## The sting of a deal at `salary` against his `ask`, with `floor_price` the
## least he takes on that term: 0 at or above his ask, at least 1 under it,
## HAGGLE_STING at his floor or below.
static func haggle_points(salary: int, ask: int, floor_price: int) -> int:
	if salary >= ask or ask <= 0:
		return 0
	var span := ask - floor_price
	if span <= 0 or salary <= floor_price:
		return HAGGLE_STING
	return clampi(roundi(float(HAGGLE_STING) * float(ask - salary) / float(span)), 1, HAGGLE_STING)


## The sting a player carries this season (0 when none). A save from before
## the sting was sized carries the full one.
static func sting(p: Dictionary) -> int:
	return int(p.get("haggle_points", HAGGLE_STING)) if p.has("haggle_sting") else 0


## Talked round this off-season: his club cannot release him before the next
## one. `next_year` is the season the off-season leads into.
static func release_held(p: Dictionary, next_year: int) -> bool:
	return int(p.get("play_on", 0)) == next_year


## Legs multiplier on his energy drain this season.
static func legs(p: Dictionary) -> float:
	return OLD_LEGS if p.has("old_legs") else 1.0


## The season these were for is over: clear them off `list`.
static func season_over(list: Array, finished: int) -> void:
	for p in list:
		for k in ["haggle_sting", "old_legs"]:
			if p.has(k) and int(p[k]) <= finished:
				p.erase(k)
				if k == "haggle_sting":
					p.erase("haggle_points")
