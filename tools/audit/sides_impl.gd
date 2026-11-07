extends RefCounted
## Row 107 (event cards: every choice gets an upside and a downside): what each
## choice of every story card shows the coach under its button, sorted by kind.
## No career is played: each card is built for one club and one player at the
## start of a season, so it runs in seconds (`run_audit.gd -- sides_impl [club]`).
##
## The lines are the engine's own (StoryEngine.card_lines, the hub's lines), built
## with every choice the card is written with, so a choice a week's facts hide
## (finals_week_off/semi) is still sorted. Kinds:
##   both       its own effects state a gain and a cost
##   spared     its own effects cost something; its gain is the other choices'
##              cost it does not carry ("No 15% chance of a slow start.")
##   gain_only  a gain and no cost
##   cost_only  a cost and no gain, own or spared
##   spared_only  no cost; the only gain is a spared one
##   nothing    no gain and no cost line at all
## Prints SIDE <card> <choice> <kind> | <lines>, then SIDES <kind> <count> and a
## SUMMARY line. Measurement only: it never changes a rule.

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
			var shown := StoryEngine.card_lines(full_card(t, card.get("facts", {})), i)
			print("SIDE %s %s %s | %s" % [t["id"], t["choices"][i]["key"], k, " / ".join(shown)])
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
	var shown := StoryEngine.card_lines(full_card(t, facts), i)
	var own_gain := _has(own, StoryEngine.GAIN_MARK)
	var own_cost := _has(own, StoryEngine.COST_MARK)
	var gain := _has(shown, StoryEngine.GAIN_MARK)
	if own_gain and own_cost:
		return "both"
	if own_cost:
		return "spared" if gain else "cost_only"
	if own_gain:
		return "gain_only"
	return "spared_only" if gain else "nothing"


static func _has(lines: PackedStringArray, mark: String) -> bool:
	for l in lines:
		if l.begins_with(mark):
			return true
	return false
