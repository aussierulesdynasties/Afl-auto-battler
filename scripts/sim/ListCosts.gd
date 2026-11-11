class_name ListCosts
extends RefCounted
## What the list's one-sided options cost (row T1.R26, L4; director 2026-11-10,
## "Costs in the rule's spirit"). Each cost lasts the coming season and ends
## when its off-season opens (GameState.open_offseason calls `season_over`).
## Every club pays them by the same rules: a rival that re-signs a player under
## his ask stings him just as you do.

const HAGGLE_STING := ListStings.HAGGLE_STING
const RELEASE_DEAD_SHARE := ListStings.RELEASE_DEAD_SHARE
const ASK_AGAIN_YES := ListStings.ASK_AGAIN_YES
const OLD_LEGS := ListStings.OLD_LEGS

const HAGGLE_GAIN := "you save %s a season, %s under his ask"
const HAGGLE_COST := "if he signs, his morale is %s lower all season"
## Above his floor the sting is a share of the full one: the gate says both.
const HAGGLE_COST_PART := "if he signs, his morale is %s lower all season (%s at his lowest, %s)"
const HAGGLE_SHORT_GAIN := "none: he won't sign for under %s"
const HAGGLE_SHORT_COST := "it uses 1 of your %d offers left"
const HAGGLE_INSULT_COST := "he's insulted: it uses %d of your %d offers left and his morale drops %s"
const RELEASE_GAIN := "a list spot, and %s a season off your books"
const RELEASE_COST := "%s of his remaining contract (%s) stays on your cap next season"
const RELEASE_COST_NONE := "nothing stays on your cap: his contract is up"
const ASK_GAIN := "%s chance he says yes and plays one more season"
const ASK_GAIN_NONE := "0%% chance he says yes (%s)"
const ASK_COST := "if he says yes, his legs are %s down all season (he tires %s faster) and you can't release him until next off-season"
## Release refused for a man talked round this off-season.
const HELD_REASON := "%s said he'd go around again for you: he can't be released until next off-season."
## Under his card, in place of Release.
const HELD_LINE := "He said he'd go around again: you can't release him until next off-season."
const ASK_COST_NONE := "none: he retires either way"


static func _pct(share: float) -> String:
	return "%d%%" % roundi(absf(share) * 100.0)


## Gain / Cost for an offer of `salary` to your own player whose ask is `ask`,
## who signs at `floor` or more (Contracts.respond), with `left` offers to go.
## [] when the offer is at or above his ask (no haggle, no sting). Under his
## floor he does not sign, so the gate says what the offer costs instead.
## Between the two, the sting is sized by the share of the gap saved
## (ListStings.haggle_points), and the gate gives the full one beside it.
static func haggle_lines(salary: int, ask: int, floor_price := 0, left := Contracts.MAX_OFFERS) -> Array:
	if salary >= ask or ask <= 0:
		return []
	if salary < floor_price:
		var insult := salary * Contracts.INSULT_DEN < floor_price * Contracts.INSULT_NUM
		var cost := HAGGLE_INSULT_COST % [mini(Contracts.INSULT_STRIKES, left), left, _pct(Contracts.INSULT_MORALE / 100.0)] 				if insult else HAGGLE_SHORT_COST % left
		return [GateOdds.gain(HAGGLE_SHORT_GAIN % Contracts.money(floor_price)), GateOdds.cost(cost)]
	# With no floor given, the full sting (the size a deal at his floor carries).
	var pts := ListStings.haggle_points(salary, ask, floor_price) if floor_price > 0 else HAGGLE_STING
	var sting_line := HAGGLE_COST % _pct(pts / 100.0)
	if pts < HAGGLE_STING:
		sting_line = HAGGLE_COST_PART % [_pct(pts / 100.0), _pct(HAGGLE_STING / 100.0), Contracts.money(floor_price)]
	return [GateOdds.gain(HAGGLE_GAIN % [Contracts.money(ask - salary), _pct(float(ask - salary) / float(ask))]),
			GateOdds.cost(sting_line)]


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
	if no_reason != "":
		var why := no_reason.trim_suffix(".")
		return [GateOdds.gain(ASK_GAIN_NONE % (why.left(1).to_lower() + why.substr(1))), GateOdds.cost(ASK_COST_NONE)]
	return [GateOdds.gain(ASK_GAIN % _pct(ASK_AGAIN_YES)),
			GateOdds.cost(ASK_COST % [_pct(OLD_LEGS - 1.0), _pct(OLD_LEGS - 1.0)])]


## The sting a player carries this season (0 when none).
static func sting(p: Dictionary) -> int:
	return ListStings.sting(p)


## Legs multiplier on his energy drain this season.
static func legs(p: Dictionary) -> float:
	return ListStings.legs(p)


## The season these were for is over: clear them off `list`.
static func season_over(list: Array, finished: int) -> void:
	ListStings.season_over(list, finished)
