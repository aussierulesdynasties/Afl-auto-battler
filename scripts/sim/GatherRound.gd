class_name GatherRound
extends RefCounted
## Gather Round (TODO row 74, T5.Q11a; Director Bible rules 2.38, 5.127, 5.132):
## one home-and-away round a season is a shared league event, every match of it
## staged at the host city's grounds instead of the home club's.
##
## Policy, the same in every generated season (nothing tied to one year's dates,
## round number or match count):
##   - the round: one of rounds 3 to 7, the one with the fewest clubs on a bye,
##     ties settled by the season seed. With an odd club count (Tasmania,
##     Canberra, a created club) a club is always out of a round; that club sits
##     this one out like any other bye and nobody is forced to play.
##   - the grounds: the host's stored venues, the main ground taking the most
##     matches (VENUES shares, repeated in order for a bigger round, cut short for
##     a smaller one). A club whose own home ground is a host ground plays there.
##   - home advantage: a club has its home-ground edge only at its own ground
##     (as at the Grand Final); a relocated club has none (rule 2.38). The
##     weather is Adelaide's (Weather has no row for Norwood or Barossa, so all
##     three use the SA row, Adelaide Oval's). No event stat buffs.
##
## Derived from the season seed and the saved fixture: nothing is saved, and an
## old save gets its Gather Round from the same rule. Switch `gather_round`; off,
## every round is as before.

const SWITCH := "gather_round"
const NAME := "Gather Round"
## The host city and its grounds (the Adelaide grounds of the AFL's Gather Rounds).
const HOST_STATE := "SA"
const VENUES := [
	{"ground": "Adelaide Oval", "share": 5},
	{"ground": "Norwood Oval", "share": 2},
	{"ground": "Barossa Park", "share": 2},
]
## 0-based rounds it may fall in (Rounds 3 to 7), before the mid-season byes.
const FIRST := 2
const LAST := 6


static func active() -> bool:
	return Features.on(SWITCH)


## This season's Gather Round (0-based), or -1 (switch off, or too few rounds).
static func round_of(fixture: Array, clubs: Array, season_seed: int) -> int:
	if not active() or fixture.size() <= FIRST:
		return -1
	var best := -1
	var best_out := 0
	var best_tie := 0
	for r in range(FIRST, mini(LAST, fixture.size() - 1) + 1):
		var playing := {}
		for m in fixture[r]:
			playing[str(m["home"])] = true
			playing[str(m["away"])] = true
		var out := clubs.size() - playing.size()
		var tie := hash([season_seed, r, "gather"])
		if best < 0 or out < best_out or (out == best_out and tie < best_tie):
			best = r
			best_out = out
			best_tie = tie
	return best


## The ground for each match of the round, in the round's order.
static func venues_for(round_matches: Array, season_seed: int, home_ground: Callable) -> Array:
	var slots := []
	while slots.size() < round_matches.size():
		for v in VENUES:
			for i in range(int(v["share"])):
				slots.append(str(v["ground"]))
	var hosts := {}
	for v in VENUES:
		hosts[str(v["ground"])] = true
	# Matches with a host-ground club first (they take their own ground), the
	# rest in a seeded order.
	var order := range(round_matches.size())
	var rng := RandomNumberGenerator.new()
	rng.seed = hash([season_seed, "gather venues"])
	for i in range(order.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = order[i]
		order[i] = order[j]
		order[j] = t
	var local := []
	var rest := []
	for i in order:
		var m: Dictionary = round_matches[i]
		var own := ""
		for c in [str(m["home"]), str(m["away"])]:
			if hosts.has(str(home_ground.call(c))):
				own = str(home_ground.call(c))
		if own != "":
			local.append([i, own])
		else:
			rest.append(i)
	var out := []
	out.resize(round_matches.size())
	slots = slots.slice(0, round_matches.size())
	for pair in local:
		var at := slots.find(str(pair[1]))
		if at < 0:
			at = 0
		out[int(pair[0])] = slots[at]
		slots.remove_at(at)
	for i in rest:
		out[i] = slots.pop_front()
	return out
