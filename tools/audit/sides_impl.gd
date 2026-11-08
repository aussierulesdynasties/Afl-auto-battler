extends RefCounted
## Row 107 (event cards: every choice gets an upside and a downside): what each
## choice of every story card shows the coach under its button, sorted by kind.
## No career is played: each card is built for one club and one player at the
## start of a season, so it runs in seconds (`run_audit.gd -- sides_impl [club]`).
##
## The lines are the ones the coach reads under each button: StoryEngine.stakes_lines
## of the choice's own effects, as EventCardView prints them on the hub and pre-season
## cards. Built with every choice the card is written with, so a choice a week's facts
## hide (finals_week_off/semi) is still sorted. StoryEngine.card_lines can add a
## "spared" gain (another choice's cost this one does not carry), but no screen has
## printed it since #837, so it is listed apart and never counted as a side. Kinds:
##   both       the screen shows a gain and a cost
##   spared     the screen shows a cost only; card_lines would add a spared gain
##              ("No 15% chance of a slow start.") that the coach does not see
##   gain_only  a gain and no cost
##   cost_only  a cost and no gain, not even a spared one
##   spared_only  no line on the screen; the only gain is an unshown spared one
##   nothing    no gain and no cost line at all
## Prints SIDE <card> <choice> <kind> | <screen lines> [|| unshown: <spared lines>],
## then SIDES <kind> <count> and a SUMMARY line. Measurement only: it never changes a rule.

const KINDS := ["both", "spared", "gain_only", "cost_only", "spared_only", "nothing"]


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var club := str(args[1]) if args.size() > 1 else "GEE"
	GameState.reset()
	GameState.replay_seed = 2031
	GameState.autosave_enabled = false
	GameState.start_season(club, GameDB.club_list(club))
	var p: Dictionary = GameState.my_list[4]
	var tally := {}
	for k in KINDS:
		tally[k] = 0
	var n := 0
	for t in StoryDeck.all():
		var player := str((t["subject"] as Dictionary).get("kind", "")) == "player"
		var card := GameState.story_card(str(t["id"]), p if player else {})
		for i in range((t["choices"] as Array).size()):
			var k := kind(t, card.get("facts", {}), i)
			tally[k] = int(tally[k]) + 1
			n += 1
			var facts: Dictionary = card.get("facts", {})
			var screen := StoryEngine.stakes_lines((t["choices"][i] as Dictionary).get("effects", []), facts)
			var unshown := spared_lines(t, facts, i)
			print("SIDE %s %s %s | %s%s" % [t["id"], t["choices"][i]["key"], k, " / ".join(screen),
					(" || unshown: " + " / ".join(unshown)) if not unshown.is_empty() else ""])
	for k in KINDS:
		print("SIDES %s %d" % [k, int(tally[k])])
	print("SUMMARY sides | cards %d | choices %d | both %d | spared %d | gain_only %d | cost_only %d | spared_only %d | nothing %d"
			% [StoryDeck.all().size(), n, tally["both"], tally["spared"], tally["gain_only"], tally["cost_only"],
			tally["spared_only"], tally["nothing"]])


## The card with every choice it is written with, on the facts it was built with.
static func full_card(t: Dictionary, facts: Dictionary) -> Dictionary:
	var opts := []
	for c in t["choices"]:
		opts.append({"key": str(c["key"]), "effects": (c.get("effects", []) as Array).duplicate(true)})
	return {"options": opts, "facts": facts}


static func kind(t: Dictionary, facts: Dictionary, i: int) -> String:
	var own := StoryEngine.stakes_lines((t["choices"][i] as Dictionary).get("effects", []), facts)
	var own_gain := _has(own, StoryEngine.GAIN_MARK)
	var own_cost := _has(own, StoryEngine.COST_MARK)
	var spared := not spared_lines(t, facts, i).is_empty()
	if own_gain and own_cost:
		return "both"
	if own_cost:
		return "spared" if spared else "cost_only"
	if own_gain:
		return "gain_only"
	return "spared_only" if spared else "nothing"


## The gain lines card_lines would add from the other choices' costs, which no
## screen prints (#837 dropped them from the hub card).
static func spared_lines(t: Dictionary, facts: Dictionary, i: int) -> PackedStringArray:
	var own := StoryEngine.stakes_lines((t["choices"][i] as Dictionary).get("effects", []), facts)
	var out := PackedStringArray()
	for l in StoryEngine.card_lines(full_card(t, facts), i):
		if not own.has(l):
			out.append(l)
	return out


static func _has(lines: PackedStringArray, mark: String) -> bool:
	for l in lines:
		if l.begins_with(mark):
			return true
	return false
