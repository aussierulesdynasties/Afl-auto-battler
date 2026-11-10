class_name ListStings
extends RefCounted
## The list costs' season-long effects and sizes (row T1.R26 L4, director
## 2026-11-10), with no dependencies, so the sim core (Workload, ClubLife,
## Retirement) can read them in a --script runner. The Gain / Cost copy is
## ListCosts.

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
