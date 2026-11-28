class_name StoryEngine
extends RefCounted
## Picks the week's story cards and keeps the story's memory: what came up and
## when, the flags choices set, and the arcs those flags start. Pure rules over
## the facts GameState hands in; GameState applies the effects.
##
## The week: a due arc beat comes first (it does not wait for a busy week),
## then, in about seven weeks of ten, a new arc start or else a one-off. A big
## week (round 1, the last home-and-away round, each finals week) may bring a
## second card from another category, about a different player.
##
## Nothing repeats too soon: each card has its own cooldown, each player one
## too (no player on two cards within his card's subject cooldown), and no
## category comes up more than twice in five weeks. Cards of one series (the
## international cards) count that player cooldown from the last card of their
## own series about him, and wait SERIES_GAP weeks after any other card about
## him: counted from any card, another card about him every ten weeks kept a
## twelve-week wait from ever ending (director 2026-11-11: a story that can
## never fire is a bug).
##
## Arcs: a choice can set a flag on its player or on the club, stamped with
## the week. A follow-up card names the flag and a window ("after" weeks, up to
## "within"), plus live conditions, so which beat comes depends on what has
## happened since. An end beat closes the arc; an arc nobody returns to before
## its window shuts closes as lapsed. Either way it never starts again for him.
##
## Randomness: a story stream of its own, seeded from the save seed, the year
## and the week, so drawing cards never moves the match dice or the draft.

const EVENT_CHANCE := 0.7
## A big week's second card comes this often.
const SECOND_CHANCE := 0.5
const DIVERSITY_WEEKS := 5
const DIVERSITY_MAX := 2
## Played weeks a card of a series waits after any other card about its player.
const SERIES_GAP := 4
## Weeks counted per season, finals included (24 rounds and up to 5 finals
## weeks fit inside), so a cooldown runs on across seasons.
const SEASON_WEEKS := 30
## The pre-season's own block of weeks, after last season's finals and before
## Round 1 (director 2026-11-03): pre-season weeks -9..0 (week_in_season) sit
## here, so they never share a week with any season's rounds or finals.
const PRESEASON_WEEKS := 10
## The off-season between last season's last week and the pre-season block, so
## September's cards are well behind the pre-season's (DIVERSITY_WEEKS). Cooldowns
## skip it: they count played weeks only (played_between).
const OFFSEASON_WEEKS := 12
## One year on the stories' calendar (52 weeks): off-season, pre-season block,
## then rounds and finals. Week 1 of year Y is (Y-2000)*52 + 22 + 1.
const YEAR_SPAN := OFFSEASON_WEEKS + PRESEASON_WEEKS + SEASON_WEEKS
## The calendar's version in a saved story; saves without it used year * 30 + week.
const CALENDAR := 2
const NEVER := -99999
const TIERS := ["beat", "start", "one_off"]
## A result line may name players from a ranked list: {best3}, {worst2}.
const RANKED_TOKEN := "\\{(best|worst)([1-9])\\}"


static func week_abs(year: int, week: int) -> int:
	return (year - 2000) * YEAR_SPAN + OFFSEASON_WEEKS + PRESEASON_WEEKS + week


## Played weeks in a year: the pre-season's weeks, then rounds and finals.
static func played_per_year() -> int:
	return PreSeason.weeks() + 1 + SEASON_WEEKS


## An absolute week as a count of played weeks (director 2026-11-03): the
## off-season and unused pre-season slots count for nothing, so a card's
## cooldown means what it was written to mean.
static func played_index(w: int) -> int:
	# Each year counted from its first pre-season week; its off-season weeks clamp to the next year's start.
	var first := OFFSEASON_WEEKS + PRESEASON_WEEKS - PreSeason.weeks()
	var y := floori(float(w - first) / float(YEAR_SPAN))
	return y * played_per_year() + mini(w - first - y * YEAR_SPAN, played_per_year())


## Played weeks from `from` to `to` (cooldowns). NEVER stays far away.
static func played_between(from: int, to: int) -> int:
	if from <= NEVER / 2:
		return to - from
	return played_index(to) - played_index(from)


## An absolute week from the old calendar (year * 30 + week, pre-season
## overlapping last season's last weeks) on the new one. An old pre-season
## week reads as last season's late weeks: older, so it blocks less.
static func from_old_week(v: int) -> int:
	if v <= NEVER / 2:
		return v
	var y := floori(float(v) / float(SEASON_WEEKS))
	return y * YEAR_SPAN + OFFSEASON_WEEKS + PRESEASON_WEEKS + (v - y * SEASON_WEEKS)


## Is this saved story on the old calendar?
static func is_old_calendar(story: Variant) -> bool:
	return story is Dictionary and not (story as Dictionary).is_empty() and not (story as Dictionary).has("calendar")


## Moves every stored week of an old save's story onto the new calendar.
static func migrate_calendar(story: Dictionary) -> void:
	if story.has("calendar"):
		return
	for key in ["last", "subj"]:
		var d: Variant = story.get(key)
		if d is Dictionary:
			for k in (d as Dictionary).keys():
				d[k] = from_old_week(int(d[k]))
	var flags: Variant = story.get("flags")
	if flags is Dictionary:
		for who in (flags as Dictionary).keys():
			var f: Variant = flags[who]
			if f is Dictionary:
				for k in (f as Dictionary).keys():
					f[k] = from_old_week(int(f[k]))
	var cats: Variant = story.get("cats")
	if cats is Array:
		for row in (cats as Array):
			if row is Array and (row as Array).size() > 0:
				row[0] = from_old_week(int(row[0]))
	var arcs: Variant = story.get("arcs")
	if arcs is Dictionary:
		for k in (arcs as Dictionary).keys():
			var rec: Variant = arcs[k]
			if rec is Dictionary:
				for f2 in ["start", "until", "ended"]:
					if (rec as Dictionary).has(f2):
						rec[f2] = from_old_week(int(rec[f2]))
	story["calendar"] = CALENDAR


static func new_state() -> Dictionary:
	return {"flags": {}, "last": {}, "subj": {}, "cats": [], "seen": {}, "season": {}, "arcs": {}, "calendar": CALENDAR}


## An older save, or a partial one: every key present.
static func ensure(story: Dictionary) -> Dictionary:
	var fresh := new_state()
	for k in fresh:
		if not story.has(k) or typeof(story[k]) != typeof(fresh[k]):
			story[k] = fresh[k]
	return story


## A new season: the per-season counts start again; cooldowns and arcs run on.
static func new_season(story: Dictionary) -> void:
	ensure(story)
	story["season"] = {}


## The week's cards (0, 1 or 2). `ctx`: seed, year, week (1.. in season),
## phase ("regular" or "finals"), big (bool), club (club facts), players
## (one fact dict per player of yours, with "id"). Records what it picks.
static func pick_week(deck: Array, ctx: Dictionary, story: Dictionary) -> Array:
	ensure(story)
	var w := week_abs(int(ctx.get("year", 2000)), int(ctx.get("week", 0)))
	lapse_arcs(story, w)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("story|%d|%d|%d" % [int(ctx.get("seed", 0)), int(ctx.get("year", 0)), int(ctx.get("week", 0))])
	# September always has something to say (finals weeks); the rest of the year is as quiet as it was.
	# The week your season ends always has its card too (finals_cards_2).
	var quiet := rng.randf() >= EVENT_CHANCE and not ["finals", "season_end"].has(str(ctx.get("phase", "regular")))
	# A card written to come every time takes the week, quiet or not.
	var due := _due_cards(deck, ctx, story, rng, w)
	if not due.is_empty():
		return due
	var out := []
	var first := _pick_one(deck, ctx, story, rng, w, quiet, "", "")
	if first.is_empty():
		return out
	out.append(first)
	_record_pick(story, first, w)
	var second_chance := 1.0 if int((ctx.get("club", {}) as Dictionary).get("finals_week", 0)) == 5 else SECOND_CHANCE
	if bool(ctx.get("big", false)) and rng.randf() < second_chance:
		var second := _pick_one(deck, ctx, story, rng, w, false, str(first["category"]), str(first.get("player_id", "")))
		if not second.is_empty():
			out.append(second)
			_record_pick(story, second, w)
	return out


## The cards marked `always` (director 2026-11-08, the running-again card "comes every
## time"): one for each player who fits, each player once a season. Never drawn or held
## back by the week's mix; the season's counts hold who has had his.
static func _due_cards(deck: Array, ctx: Dictionary, story: Dictionary, rng: RandomNumberGenerator, w: int) -> Array:
	var out := []
	for t in deck:
		if not bool(t.get("always", false)):
			continue
		var subj := eligible_subject(t, ctx, story, w, rng)
		while not subj.is_empty():
			var card := build(deck, t, subj, ctx.get("club", {}), rng, w)
			out.append(card)
			_record_pick(story, card, w)
			story["season"][_always_key(str(t["id"]), str(subj["id"]))] = 1
			subj = eligible_subject(t, ctx, story, w, rng)
	return out


static func _always_key(id: String, pid: String) -> String:
	return "%s|%s" % [id, pid]


static func _pick_one(deck: Array, ctx: Dictionary, story: Dictionary, rng: RandomNumberGenerator, w: int,
		quiet: bool, skip_cat: String, skip_pid: String) -> Dictionary:
	var tiers := {"beat": [], "start": [], "one_off": []}
	var topical := []
	for t in deck:
		if str(t["category"]) == skip_cat:
			continue
		var subj := eligible_subject(t, ctx, story, w, rng, skip_pid)
		if subj.is_empty():
			continue
		if bool(t.get("topical", false)):
			topical.append([t, subj])
		else:
			tiers[tier(t)].append([t, subj])
	# A card about the run the club is on right now (a losing streak) is this
	# week's story: it comes before the running stories and in a quiet week too.
	# Behind them it was never drawn, there is always an older story waiting.
	if not topical.is_empty():
		var c: Array = topical[rng.randi_range(0, topical.size() - 1)]
		return build(deck, c[0], c[1], ctx.get("club", {}), rng, w)
	# A priority card (the Grand Final week's, a week off's) comes before the older ones.
	for name in TIERS:
		var first: Array = (tiers[name] as Array).filter(func(c): return bool(c[0].get("priority", false)))
		if not first.is_empty():
			tiers[name] = first
	for name in TIERS:
		if name != "beat" and quiet:
			break
		var pool: Array = tiers[name]
		if pool.is_empty():
			continue
		var total := 0
		for c in pool:
			total += maxi(1, int(c[0].get("weight", 1)))
		var roll := rng.randi_range(1, total)
		for c in pool:
			roll -= maxi(1, int(c[0].get("weight", 1)))
			if roll <= 0:
				return build(deck, c[0], c[1], ctx.get("club", {}), rng, w)
	return {}


static func tier(t: Dictionary) -> String:
	if not (t.get("needs", {}) as Dictionary).is_empty():
		return "beat"
	if str(t.get("arc", "")) != "":
		return "start"
	return "one_off"


## Who the card would be about this week, or {} when it cannot come up:
## {"kind": "club"} or the chosen player's facts.
static func eligible_subject(t: Dictionary, ctx: Dictionary, story: Dictionary, w: int,
		rng: RandomNumberGenerator, skip_pid := "") -> Dictionary:
	var id := str(t["id"])
	if bool(t.get("scripted", false)):
		return {}   # dealt by the game itself (the result of a role trial), never drawn
	# A club deck's card comes up only for its club; a controversy only with the switch on.
	var deck := str(t.get("club", ""))
	if deck != "" and deck != str((ctx.get("club", {}) as Dictionary).get("club_deck", "")):
		return {}
	if bool(t.get("controversy", false)) and int((ctx.get("club", {}) as Dictionary).get("controversies", 1)) == 0:
		return {}
	if not (t.get("phase", ["regular"]) as Array).has(str(ctx.get("phase", "regular"))):
		return {}
	# A week off in the finals: only the cards written for it.
	if bool((ctx.get("club", {}) as Dictionary).get("finals_bye", false)) and not bool(t.get("bye", false)):
		return {}
	if played_between(int(story["last"].get(id, NEVER)), w) < int(t.get("cooldown", 0)):
		return {}
	var per := int(t.get("per_season", 0))
	if per > 0 and int(story["season"].get(id, 0)) >= per:
		return {}
	# A priority card (September's) is not held back by the mix of the last five weeks.
	if category_count(story, str(t["category"]), w) >= DIVERSITY_MAX and not bool(t.get("priority", false)) and not bool(t.get("always", false)):
		return {}
	var club: Dictionary = ctx.get("club", {})
	if not meets(club, t.get("when", {}), story["flags"].get("club", {})):
		return {}
	var subject: Dictionary = t.get("subject", {})
	if str(subject.get("kind", "club")) != "player":
		if not _arc_open_ok(t, story, "club", w):
			return {}
		return {"kind": "club"}
	var fits := []
	for p in ctx.get("players", []):
		var pid := str(p["id"])
		if pid == skip_pid:
			continue
		if bool(t.get("always", false)) and story["season"].has(_always_key(id, pid)):
			continue
		# No wait means no wait: Round 1's cards are drawn when the season is made, so
		# their stamp is later than a pre-season week and the gap reads negative.
		var wait := int(t.get("subject_cooldown", 0))
		if wait > 0:
			var since := played_between(int(story["subj"].get(pid, NEVER)), w)
			var series := str(t.get("series", ""))
			if series == "":
				if since < wait:
					continue
			elif since < mini(wait, SERIES_GAP) or played_between(int(story["subj"].get(_series_key(series, pid), NEVER)), w) < wait:
				continue
		if not meets(p, subject.get("where", {}), story["flags"].get(pid, {})):
			continue
		if not _arc_open_ok(t, story, pid, w):
			continue
		fits.append(p)
	return choose(fits, str(subject.get("pick", "random")), rng)


## Arc rules for one subject: a follow-up needs his flag inside its window and
## his arc still open; a start needs no earlier run of that arc for him.
static func _arc_open_ok(t: Dictionary, story: Dictionary, who: String, w: int) -> bool:
	var arc := str(t.get("arc", ""))
	var needs: Dictionary = t.get("needs", {})
	if not needs.is_empty():
		var set_at := int((story["flags"].get(who, {}) as Dictionary).get(str(needs.get("flag", "")), NEVER))
		if set_at == NEVER:
			return false
		var since := w - set_at
		if since < int(needs.get("after", 1)) or since > int(needs.get("within", 30)):
			return false
		if arc != "":
			return str((story["arcs"].get(arc + "|" + who, {}) as Dictionary).get("state", "")) == "open"
		return true
	if arc != "":
		return not story["arcs"].has(arc + "|" + who)
	return true


## Do these facts meet the conditions? `x_min`, `x_max`, `x_every` (a positive
## multiple), plain equality, and flag / no_flag against the holder's flags.
static func meets(facts: Dictionary, cond: Dictionary, flags: Dictionary) -> bool:
	for k in cond:
		var key := str(k)
		var v = cond[k]
		if key == "flag":
			if not flags.has(str(v)):
				return false
		elif key == "no_flag":
			if flags.has(str(v)):
				return false
		elif key.ends_with("_min"):
			if float(facts.get(key.trim_suffix("_min"), -INF)) < float(v):
				return false
		elif key.ends_with("_max"):
			if float(facts.get(key.trim_suffix("_max"), INF)) > float(v):
				return false
		elif key.ends_with("_every"):
			var n := int(facts.get(key.trim_suffix("_every"), 0))
			if n <= 0 or n % maxi(1, int(v)) != 0:
				return false
		else:
			# A number in a card (JSON reads 5 as 5.0) equals the same number in a fact.
			var have = facts.get(key, "")
			if (v is float or v is int) and (have is float or have is int):
				if float(have) != float(v):
					return false
			elif str(have) != str(v):
				return false
	return true


## The card's player among those who fit: "random", "highest:<fact>",
## "lowest:<fact>" or "random_top:<n>:<fact>" (one of the top n). {} for none.
static func choose(fits: Array, pick: String, rng: RandomNumberGenerator) -> Dictionary:
	if fits.is_empty():
		return {}
	var parts := pick.split(":")
	if parts[0] == "random":
		return fits[rng.randi_range(0, fits.size() - 1)]
	var fact := parts[parts.size() - 1]
	var sorted := fits.duplicate()
	sorted.sort_custom(func(a, b): return float(a.get(fact, 0)) > float(b.get(fact, 0)) \
			or (float(a.get(fact, 0)) == float(b.get(fact, 0)) and str(a["id"]) < str(b["id"])))
	if parts[0] == "lowest":
		return sorted[sorted.size() - 1]
	if parts[0] == "random_top":
		var n := mini(int(parts[1]), sorted.size())
		return sorted[rng.randi_range(0, n - 1)]
	return sorted[0]


## Where the story keeps the week a card of this series was last about him.
static func _series_key(series: String, pid: String) -> String:
	return "%s|%s" % [series, pid]


static func category_count(story: Dictionary, cat: String, w: int) -> int:
	var n := 0
	for row in story["cats"]:
		if str(row[1]) == cat and w - int(row[0]) < DIVERSITY_WEEKS:
			n += 1
	return n


static func _record_pick(story: Dictionary, card: Dictionary, w: int) -> void:
	var id := str(card["tid"])
	story["last"][id] = w
	story["seen"][id] = int(story["seen"].get(id, 0)) + 1
	story["season"][id] = int(story["season"].get(id, 0)) + 1
	var pid := str(card.get("player_id", ""))
	if pid != "":
		story["subj"][pid] = w
		if str(card.get("series", "")) != "":
			story["subj"][_series_key(str(card["series"]), pid)] = w
	(story["cats"] as Array).append([w, str(card["category"])])
	while (story["cats"] as Array).size() > 10:
		(story["cats"] as Array).pop_front()


## The card as the hub shows it, with what each choice does already worded
## (so the hint is generated from the very effects that will apply).
static func build(deck: Array, t: Dictionary, subj: Dictionary, club: Dictionary, rng: RandomNumberGenerator, w: int) -> Dictionary:
	var player := str(subj.get("kind", "")) != "club"
	var facts: Dictionary = club.duplicate()
	if player:
		facts.merge(subj, true)
	var titles: Array = t["title"]
	var texts: Array = t["text"]
	var options := []
	for c in t["choices"]:
		if not meets(facts, c.get("when", {}), {}):
			continue
		var detail := " ".join(PackedStringArray([describe(c, facts), fill(str(c.get("note", "")), facts)])).strip_edges()
		options.append({"key": str(c["key"]), "label": fill(str(c["label"]), facts), "detail": detail,
				"rule": fill(str(c.get("rule", "")), facts),
				"effects": (c.get("effects", []) as Array).duplicate(true), "result": fill(str(c.get("result", "")), facts)})
	var card := {"key": str(t["id"]), "tid": str(t["id"]), "story": true, "category": str(t["category"]),
			"default": int(t.get("default", -1)), "week": w, "facts": facts,
			"title": variant(titles, facts, rng),
			"text": variant(texts, facts, rng),
			"options": options}
	if str(t.get("stakes", "")) != "":
		card["stakes"] = fill(str(t["stakes"]), facts)
	if bool(t.get("choice_notes", false)):
		card["choice_notes"] = true
	if player:
		card["player_id"] = str(subj["id"])
		if str(t.get("series", "")) != "":
			card["series"] = str(t["series"])
	if str(t.get("arc", "")) != "":
		card["arc"] = str(t["arc"])
		card["beat"] = str(t.get("beat", ""))
		card["window"] = arc_window(deck, str(t["arc"]), t)
	var un: Dictionary = t.get("unanswered", {})
	var cost := int(un.get("board", 0))
	if cost != 0:
		card["unanswered"] = {"board": cost, "text": fill(str(un.get("text", "")), facts),
				"hint": "Say nothing: %s" % _board_words(cost).to_lower()}
	# Saying nothing can cost the player's trust instead (a card about what he asked for).
	var trust_cost := int(un.get("trust", 0))
	if trust_cost != 0 and player:
		card["unanswered"] = {"trust": trust_cost, "why": fill(str(un.get("why", "")), facts),
				"text": fill(str(un.get("text", "")), facts),
				"hint": "Say nothing: %s" % _lower_first(_trust_words(trust_cost, int(facts.get("trust", 0))))}
	return card


## One of a card's title or text variants. A variant may be a case,
## {"when": {facts}, "text": "..."}: the first case whose facts hold is the one
## (the card says what is true this week); else one plain line, chosen by the
## story stream as it always was.
static func variant(list: Array, facts: Dictionary, rng: RandomNumberGenerator) -> String:
	var pick := rng.randi_range(0, list.size() - 1)
	for v in list:
		if v is Dictionary and meets(facts, (v as Dictionary).get("when", {}), {}):
			return fill(str((v as Dictionary).get("text", "")), facts)
	var plain := list.filter(func(v): return not (v is Dictionary))
	if plain.is_empty():
		return ""
	return fill(str(list[pick] if not (list[pick] is Dictionary) else plain[0]), facts)


## A small chance that was written on a card, rolled once from the save's
## seed, the year, the week and the card, so the same save gives the same
## answer however often it is reloaded.
static func risk_hit(seed: int, year: int, week: int, key: String, chance: int) -> bool:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("risk|%d|%d|%d|%s" % [seed, year, week, key])
	return rng.randi_range(1, 100) <= chance


## How long an arc waits for its next beat: the longest window of its
## follow-ups (a card may carry "_window" to say so itself, as tests do).
static func arc_window(deck: Array, arc: String, t: Dictionary = {}) -> int:
	if t.has("_window"):
		return int(t["_window"])
	var most := 0
	for c in deck:
		if str(c.get("arc", "")) == arc:
			most = maxi(most, int((c.get("needs", {}) as Dictionary).get("within", 0)))
	return maxi(most, 1)


## After a card is answered (or settles by default): flags its choice sets,
## and the arc it belongs to opens, moves on or ends.
static func record_choice(story: Dictionary, card: Dictionary, choice: int, w: int) -> void:
	ensure(story)
	var opts: Array = card.get("options", [])
	var pid := str(card.get("player_id", ""))
	var set_any := false
	if choice >= 0 and choice < opts.size():
		for e in (opts[choice] as Dictionary).get("effects", []):
			if str(e.get("op", "")) != "flag":
				continue
			var who := "club" if str(e.get("on", "subject")) == "club" or pid == "" else pid
			if not story["flags"].has(who):
				story["flags"][who] = {}
			story["flags"][who][str(e.get("name", ""))] = w
			set_any = true
	var arc := str(card.get("arc", ""))
	if arc == "":
		return
	var key := arc + "|" + (pid if pid != "" else "club")
	var beat := str(card.get("beat", ""))
	if beat == "end":
		if story["arcs"].has(key):
			story["arcs"][key]["state"] = "done"
			story["arcs"][key]["ended"] = w
		return
	if beat == "start" and not set_any:
		return   # a start whose choice sets nothing never began
	var rec: Dictionary = story["arcs"].get(key, {"start": w, "state": "open"})
	rec["until"] = w + int(card.get("window", 1))
	story["arcs"][key] = rec


## Arcs nobody came back to inside their window close as lapsed.
static func lapse_arcs(story: Dictionary, w: int) -> void:
	for key in story["arcs"]:
		var rec: Dictionary = story["arcs"][key]
		if str(rec.get("state", "")) == "open" and w > int(rec.get("until", w)):
			rec["state"] = "lapsed"
			rec["ended"] = w


## A lever's size after trust: an effect marked "scale": "trust" lands harder
## with a player who trusts you (Trust.scaled). Used for the hint and the apply.
static func effect_d(e: Dictionary, facts: Dictionary) -> int:
	var d := int(e.get("d", 0))
	if str(e.get("scale", "")) == "trust":
		return Trust.scaled(d, int(facts.get("trust", 0)))
	return d


static func fill(s: String, facts: Dictionary) -> String:
	return s.format(facts) if s.contains("{") else s


## Names from a ranked list of players, in a card's result line: {best3} is
## the three at the top, {worst2} the two at the bottom (never the same player
## as one of the best). `rows` are {"name": String} already best first, so the
## caller decides what "best" means (a time trial ranks running fitness).
## Without enough names a token says "nobody" rather than leave braces.
static func fill_ranked(s: String, rows: Array) -> String:
	if not s.contains("{"):
		return s
	var re := RegEx.create_from_string(RANKED_TOKEN)
	var best_n := 0
	for m in re.search_all(s):
		if m.get_string(1) == "best":
			best_n = maxi(best_n, int(m.get_string(2)))
	var out := s
	for m in re.search_all(s):
		var n := int(m.get_string(2))
		var picked: Array
		if m.get_string(1) == "best":
			picked = rows.slice(0, n)
		else:
			picked = rows.slice(maxi(best_n, rows.size() - n), rows.size())
			picked.reverse()
		var names: Array = picked.map(func(r): return str(r["name"]))
		out = out.replace(m.get_string(), name_list(names))
	return out


## "A", "A and B", "A, B and C".
static func name_list(names: Array) -> String:
	if names.is_empty():
		return "nobody"
	if names.size() == 1:
		return str(names[0])
	return "%s and %s" % [", ".join(PackedStringArray(names.slice(0, names.size() - 1))), str(names[names.size() - 1])]


## What a choice does, in a coach's words, from its effects.
static func describe(c: Dictionary, facts: Dictionary) -> String:
	var out: PackedStringArray = []
	for e in c.get("effects", []):
		var s := _trial_words(e) if str(e.get("op", "")) == "role_trial" else _effect_words(e, facts)
		if s != "":
			out.append(fill(s, facts))
	return " ".join(out)


## What a choice does, as the coach weighs it: what he gains, then what it
## costs, each its own short line behind a plain marker, from the very effects
## that will apply, so the line cannot drift from the mechanic and a new card
## gets it for free. Every line carries its size, in percentages a coach reads
## the way he reads a ladder (director, 2026-10-18: "his morale up 15%",
## "about 20% of the time"): morale and board confidence run 0 to 100 and trust
## and togetherness -100 to 100, so one step is 1%. A dice roll says its chance.
## A cost that only happens if the coach later breaks a promise or the dice
## fall wrong says so. The game never says which choice is better. Effects that
## change nothing the coach feels (a flag, a note) show nothing; no lines at all
## when a choice does nothing mechanical.
const GAIN_MARK := "Gain: "
const COST_MARK := "Cost: "
## What the lines quote, from the rules they describe (tests/test_story.gd pins
## each against the rule's own constant, so a retune cannot leave a line behind).
## A full senior game's development (GameState.XP_SENIOR_GAME).
const SENIOR_GAME_XP := 37
## His legs at the first bounce after a heavy week (MatchSim._start_energy).
const HEAVY_LEGS_START := 88
## An early extension's premium over today's price (ClubLife.early_price) and
## the lift signing gives him (ClubStories._extend).
const EARLY_PREMIUM_PCT := 15
const EXTEND_MORALE := 8
## What a promise to the board moves on top of the result (GameState._board_after_round).
const PROMISE_WIN_UP := 8
const PROMISE_WIN_DOWN := 10
## What a broken promise costs the group's togetherness (GameState._board_after_round).
const BROKEN_TOGETHER := 2
## Trust lost when a promise made on a card is broken after the match: a game, a run.
const BROKEN_PROMISE_TRUST := -8
const BROKEN_RUN_TRUST := -10


static func stakes_lines(effects: Array, facts: Dictionary) -> PackedStringArray:
	var gains: PackedStringArray = []
	var costs: PackedStringArray = []
	var notes: PackedStringArray = []
	# Morale moves for the same group the same way are one move: two of them (a
	# card's own lift and a promise's thrill) print once, with their total.
	var morale_at := {}   # "gain|subject" -> [line index, total]
	for e in effects:
		for part in _effect_parts(e, facts):
			var s := fill(str(part[1]), facts)
			var into: PackedStringArray = notes if str(part[0]) == "note" else (gains if str(part[0]) == "gain" else costs)
			if part.size() > 3:
				var mk := "%s|%s" % [str(part[0]), str(part[2])]
				if morale_at.has(mk):
					var slot: Array = morale_at[mk]
					slot[1] = int(slot[1]) + int(part[3])
					into[int(slot[0])] = _morale_words(int(slot[1]), str(part[2]))
					continue
				morale_at[mk] = [into.size(), int(part[3])]
				into.append(s)
				continue
			if not into.has(s):
				into.append(s)
	var out: PackedStringArray = []
	if not notes.is_empty():
		out.append(" ".join(notes))
	if not gains.is_empty():
		out.append(GAIN_MARK + " ".join(_named(gains, facts)))
	if not costs.is_empty():
		out.append(COST_MARK + " ".join(_named(costs, facts)))
	return out


## A block of lines says who it is about before it says "he" (director,
## 2026-11-11: "arbitrarily calling players He ... is a bug"): the first line
## that opens with "He" or "His" opens with his first name instead. A block
## that already names him is left alone.
static func _named(lines: PackedStringArray, facts: Dictionary) -> PackedStringArray:
	var first := str(facts.get("first", ""))
	if first == "":
		return lines
	var out := PackedStringArray(lines)
	for i in range(out.size()):
		var s := out[i]
		if s.contains(first):
			return out
		if s.begins_with("He "):
			out[i] = first + s.substr(2)
			return out
		if s.begins_with("His "):
			out[i] = first + "'s" + s.substr(3)
			return out
	return out


## What happens if the coach leaves the card when the week is played, in one
## line under the text, from the card's own data: the choice it settles as (its
## gain and cost sit under that choice's button, so they are not said twice) or
## the price of saying nothing. "" when leaving it changes nothing.
static func silence_line(card: Dictionary) -> String:
	var un: Dictionary = card.get("unanswered", {})
	if str(un.get("hint", "")) != "":
		return str(un["hint"])
	var d := int(card.get("default", -1))
	var opts: Array = card.get("options", [])
	if d < 0 or d >= opts.size():
		return ""
	return "If you leave this, it goes as \"%s\"." % str((opts[d] as Dictionary).get("label", ""))


## The lines under one choice on a card (the hub shows these). Every choice
## carries a gain and a cost (bible §4): a choice whose own effects gain nothing
## states, as its gain, the other choices' costs it does not carry, from their
## effects (no slow-start chance, no promise to keep, the board untouched).
static func card_lines(card: Dictionary, i: int) -> PackedStringArray:
	var opts: Array = card.get("options", [])
	var facts: Dictionary = card.get("facts", {})
	var mine: Array = (opts[i] as Dictionary).get("effects", [])
	var lines := stakes_lines(mine, facts)
	for l in lines:
		if l.begins_with(GAIN_MARK):
			return lines
	var own := {}
	for e in mine:
		own[str(e.get("op", ""))] = true
	var spared: PackedStringArray = []
	for j in range(opts.size()):
		if j == i:
			continue
		for e in (opts[j] as Dictionary).get("effects", []):
			if own.has(str(e.get("op", ""))):
				continue
			var s := fill(_spared_words(e, facts), facts)
			if s != "" and not spared.has(s):
				spared.append(s)
	if spared.is_empty():
		return lines
	var out: PackedStringArray = []
	var placed := false
	for l in lines:
		if not placed and l.begins_with(COST_MARK):
			out.append(GAIN_MARK + " ".join(spared))
			placed = true
		out.append(l)
	if not placed:
		out.append(GAIN_MARK + " ".join(spared))
	return out


## Who makes way when he goes into the side for a run (ClubStories back_out):
## ", and he goes straight into the side, in place of Name".
## Nothing for a player already in this week's side.
static func _backing_out_words(facts: Dictionary) -> String:
	if bool(facts.get("selected", false)):
		return ""
	var out := str(facts.get("back_out", ""))
	return ", and he goes straight into the side" + (", in place of %s" % out if out != "" else "")


## What a choice spares him that another choice on the card would cost, in the
## same sizes; "" for a cost that is not spared by not choosing it (a mood).
static func _spared_words(e: Dictionary, facts: Dictionary) -> String:
	match str(e.get("op", "")):
		"slow_start":
			return "No %s chance of a slow start." % _pct(int(e.get("chance", 0)))
		"expects_game", "start_backing":
			return "No promise to keep: he is not owed a game."
		"back_kid":
			return "No promise to keep: {kid_name} is not owed a game."
		"promise_win":
			return "No promise to the board: a loss or draw costs %s less than a broken promise would." % _pct(PROMISE_WIN_DOWN)
		"board":
			var d := effect_d(e, facts)
			return "Board confidence stays where it is (the other choice costs it %s)." % _pct(absi(d)) if d < 0 else ""
		"role_trial":
			return "He stays in his usual spot as a {trial_home}."
		"heavy_legs":
			return "No heavy legs on game day."
		"rest":
			return "He is free to play this week."
	return ""


## A new club's approach for your out-of-contract player (ExpansionBuild).
const NEW_CLUB_KEEP_GAIN := "He stays for {keep_seasons}."
const NEW_CLUB_KEEP_COST := "{keep_price} a season against your cap."
const NEW_CLUB_GO_COST := "He joins {new_club} when this season ends."


## The one effect-phrase function: [kind, words] for each thing an effect does
## ("gain", "cost" or "note"); an effect that moves nothing the coach feels gives none.
static func _effect_parts(e: Dictionary, facts: Dictionary) -> Array:
	var op := str(e.get("op", ""))
	var d := effect_d(e, facts)
	var who := str(e.get("who", "subject"))
	# A lever that is not a gain or a cost on this card (a development week's
	# rest: he was not in the side, so missing the game costs nothing) says nothing.
	if bool(e.get("quiet", false)):
		return []
	if str(e.get("line", "")) != "":
		# A card may word an effect itself; it is still a gain or a cost by its sign.
		var k := "gain" if d > 0 or op in ["xp", "fresh"] else "cost"
		return [[k, str(e["line"])]]
	match op:
		"odds":
			# A roll: each outcome under its own gain or cost, with its odds.
			var rolled: Array = []
			var hit := int(e.get("chance", 0))
			for side in [["hit", "%s chance: " % _pct(hit)], ["miss", "%s chance: " % _pct(100 - hit)]]:
				for ne in e.get(side[0], []):
					for np in _effect_parts(ne, facts):
						rolled.append([np[0], side[1] + str(np[1])])
			return rolled
		"delegate":
			# Left to the captain: where the group stands now, then what each
			# outcome does, each under its own gain or cost.
			var parts: Array = [["note", _standing_words(facts)]]
			for pair in [["held", "If the group listens, "], ["failed", "If it doesn't, "]]:
				for ne in e.get(pair[0], []):
					for np in _effect_parts(ne, facts):
						parts.append([np[0], pair[1] + _lower_first(str(np[1]))])
			return parts
		"morale":
			if d == 0:
				return []
			var s := _morale_words(d, who)
			if str(e.get("scale", "")) == "trust" and d > 0:
				var b := str(facts.get("trust_band", "neutral"))
				var o := Trust.opinion(int(facts.get("trust", 0)))
				if b == "close" or b == "trusts":
					s += " It counts for more: his opinion of you is %d/100." % o
				elif b == "wary" or b == "lost":
					s += " It counts for less: his opinion of you is %d/100." % o
			if s != _morale_words(d, who):
				return [["gain" if d > 0 else "cost", s]]
			# A plain move carries who and how much, so stakes_lines can add two together.
			return [["gain" if d > 0 else "cost", s, who, d]]
		"board":
			return [] if d == 0 else [["gain" if d > 0 else "cost", _board_words(d)]]
		"trust":
			if d == 0:
				return []
			var tw := _trust_words(d, int(facts.get("trust", 0)))
			# Knocked back, he remembers it at contract time (director 2026-11-10):
			# under Contracts.REFUSE_BELOW he may refuse to re-sign with you.
			if d < 0 and bool(e.get("contract", false)):
				tw += " " + _refuse_words(d, int(facts.get("trust", 0)))
			return [["gain" if d > 0 else "cost", tw]]
		"xp":
			var whom: String = "He gets" if who == "subject" else ("Each player in the side gets" if who == "side" else ("Each of the others gets" if who == "others" else "Every player gets"))
			return [["gain", "%s %d development points (a senior game gives %d)." % [whom, d, SENIOR_GAME_XP]]]
		"fresh":
			return [["gain", "Fresh legs: %d%% less likely to be injured this week." % roundi((1.0 - ClubLife.FRESH_RISK) * 100.0)]]
		"rest":
			# He cannot be hurt in a game he does not play: the chance he is spared
			# (playing sore, on the cards that say so).
			var risk := "{sore_pct}" if str(e.get("spares", "")) == "sore" else "{injury_pct}"
			var spare := ("He can't get hurt this week: playing, he would carry %s chance of an injury." % risk) 					if facts.has("injury_pct") else "He can't get hurt in this week's game."
			return [["gain", spare], ["cost", "He misses this week's game."]]
		"sore":
			return [["cost", "He plays sore: %s chance he is injured (%s), and he starts %s short of fresh legs." % [
					_sore_chance(facts), _injury_length_words(), _pct(100 - roundi(ClubLife.SORE_LEGS))]]]
		"heavy_legs":
			var rise := roundi((ClubLife.HEAVY_RISK - 1.0) * 100.0)
			var short := 100 - HEAVY_LEGS_START
			if who == "subject":
				return [["cost", "Heavy legs on game day: he starts %d%% short of fresh and is %d%% more likely to be injured." % [short, rise]]]
			return [["cost", "Heavy legs across the %s on game day: each player starts %d%% short of fresh and is %d%% more likely to be injured." % [
					"side" if who == "side" else "whole list", short, rise]]]
		"expects_game":
			return [["cost", "He expects a game this week and goes straight into the side. Leave him out fit and the promise breaks: %s" % _broken_words(int(e.get("sting", 12)), BROKEN_PROMISE_TRUST, facts)]]
		"start_backing":
			return [["gain", _morale_words(Backing.THRILL, "subject"), "subject", Backing.THRILL],
					["cost", "He expects to be picked for the next {run_games} games%s. Leave him out fit and the promise breaks: %s" % [
							_backing_out_words(facts), _broken_words(Backing.STING, BROKEN_RUN_TRUST, facts)]]]
		"back_kid":
			return [["gain", "{kid_name}'s morale up %s." % _pct(Backing.THRILL)],
					["cost", "{kid_name} is promised the next {run_games} games, and he goes straight into the side. Leave him out fit and the promise breaks: %s" % _broken_words(Backing.STING, BROKEN_RUN_TRUST, {})]]
		"extend_early":
			var extend := [["gain", "He signs on for {more_seasons}, and his morale goes up %s." % _pct(EXTEND_MORALE)],
					["cost", "Locked in at {early_price} a season, %s over what he is worth today, whatever he does next." % _pct(EARLY_PREMIUM_PCT)]]
			# Under 50 he may refuse (director 2026-11-08): the odds before you ask.
			if str(facts.get("refuse_line", "")) != "":
				extend.append(["cost", "{refuse_line} If he refuses, he goes to free agency when the season ends."])
			return extend
		"new_club_keep":
			var keep := [["gain", NEW_CLUB_KEEP_GAIN], ["cost", NEW_CLUB_KEEP_COST
					+ ("" if bool(facts.get("keep_room", true)) else " {keep_note}")]]
			# Under 50 he may refuse (director 2026-11-08): the odds before you ask.
			if str(facts.get("refuse_line", "")) != "":
				keep.append(["cost", "{refuse_line} If he refuses, he joins {new_club} when the season ends."])
			return keep
		"new_club_go":
			if int(facts.get("comp_after", 0)) > 0:
				return [["gain", "{comp_line}"], ["cost", NEW_CLUB_GO_COST]]
			return [["cost", NEW_CLUB_GO_COST + " {comp_line}"]]
		"promise_win":
			return [["gain", "Win and board confidence goes up %s more than a win alone." % _pct(PROMISE_WIN_UP)],
					["cost", "Lose or draw and board confidence falls %s more than a loss alone." % _pct(PROMISE_WIN_DOWN)]]
		"captaincy_swap":
			return [["gain", "{vice_name} takes the armband; {name} stays in the leadership group."],
					["cost", "Taking it off {name} mid-season: his morale falls %s and his opinion of you falls %d. It uses your one change this season." % [
						_pct(absi(Captaincy.STRIPPED_MORALE)), -Trust.opinion_move(int(facts.get("trust", 0)), Captaincy.STRIPPED_TRUST)]]]
		"rush_back":
			if int(facts.get("pre_week", 0)) > 0:
				return _rush_preseason(facts)
			return [["gain", "He is cleared to play, and you name him."],
					["cost", "He plays sore: %s chance he is hurt again (any injury, not only this one; %s), and he starts %s short of fresh legs." % [
						_sore_chance(facts), _injury_length_words(), _pct(100 - roundi(ClubLife.SORE_LEGS))]]]
		"slow_start":
			return [["cost", _slow_words(e)]]
		"loss_sting":
			return [["cost", "If you lose that final, about a %s chance the side's morale also falls %s." % [
					_pct(int(e.get("chance", 0))), _pct(absi(int(e.get("d", 0))))]]]
		"role_trial":
			return [["gain", _trial_words(e)], ["cost", _trial_cost_words(e, facts)]]
		# The development talk (T5.r93, GameState.dev_talk): games there if it takes.
		"dev_promise":
			return [["cost", "If it takes ({take_odds}), he expects his next three games as a {proj_word}, and he is picked there. Leave him out of them fit and the promise breaks: %s Three games away from his usual spot." % _broken_words(
					GameState.DEV_PROMISE_STING, BROKEN_PROMISE_TRUST, facts)]]
		"no_promise":
			return [["gain", "No promise to keep."]]
		"on_record":
			return [["cost", _record_words(facts)]]
		# The pre-season cards' club levers: a culture strand (-100 to 100, so one
		# step is 1%), weeks of running toward the fitness base, weeks of drilling.
		"culture":
			return [] if d == 0 else [["gain" if d > 0 else "cost", _culture_words(e, d)]]
		"running":
			return [] if d == 0 else [["gain" if d > 0 else "cost", _running_words(d, facts)]]
		"drill":
			return [] if d <= 0 else [["gain", _drill_words(d, facts)]]
		# Contract talk put off: the early deal's premium is not paid now.
		"open_price":
			return [["gain", "No %s early premium: his price waits on his form, lower if it drops, higher if he improves." % _pct(EARLY_PREMIUM_PCT)]]
		# A choice that holds a player back from development the other choice gives.
		"forgo_xp":
			var without: String = {"side": "each player in the side goes", "all": "every player goes",
					"others": "each of the others goes"}.get(who, "he goes")
			return [] if d <= 0 else [["cost", "Slower growth: %s without %d development points (a senior game gives %d)." % [without, d, SENIOR_GAME_XP]]]
		# The physio's plan in the pre-season: he stays out as long as the injury runs.
		"keep_out":
			var out := []
			if int(facts.get("pre_miss_xp", 0)) > 0:
				out.append(["cost", "Slower growth: he goes without about %d pre-season development points while he recovers (a senior game gives %d)." % [
						int(facts["pre_miss_xp"]), SENIOR_GAME_XP]])
			if int(facts.get("pre_miss_rounds", 0)) > 0:
				out.append(["cost", "He is still out at Round 1, with %s to run." % _weeks_of(int(facts["pre_miss_rounds"]))])
			return out
	return []


## Clearing a player the physio still has in the pre-season (pre_knee_return): the
## training and the Round 1 he would miss on the physio's plan (ClubStories.preseason_miss),
## against carrying soreness to Round 1 and the Heavy weeks he would have sat out.
static func _rush_preseason(facts: Dictionary) -> Array:
	var out := []
	var xp := int(facts.get("pre_miss_xp", 0))
	var rounds := int(facts.get("pre_miss_rounds", 0))
	var heavy := int(facts.get("pre_miss_heavy", 0))
	if xp > 0:
		out.append(["gain", "He trains with the group from now: about %d pre-season development points he would otherwise miss (a senior game gives %d)." % [
				xp, SENIOR_GAME_XP]])
	if rounds > 0:
		out.append(["gain", "He is right for Round 1, where on the physio's plan he would still be out with %s to run." % _weeks_of(rounds)])
	if xp <= 0 and rounds <= 0:
		# Nearly right anyway (director 2026-11-08: the card comes every time).
		out.append(["gain", "He trains with the group from now. On the physio's plan he is back for next week's training anyway, so clearing him gains no development and no Round 1 game."])
	# The card comes after the week's time trial or pre-season match (GameState.preseason_advance).
	# The pre-season match carries a share of a normal match's risk (GameState._practice_squad).
	var games := "Round 1"
	var starts := "it"
	if int(facts.get("pre_week", 0)) < int(PreSeason.tune("practice_week")):
		var share := float(PreSeason.tune("practice_injury_rate"))
		starts = "each match"
		games += " and %s in the pre-season match" % ("half that" if is_equal_approx(share, 0.5) else "%s of that" % _pct(roundi(share * 100.0)))
	out.append(["cost", "He is sore until Round 1: %s chance he is hurt in %s (any injury, not only this one; %s), and he starts %s %s short of fresh legs." % [
			_sore_chance(facts), games, _injury_length_words(), starts, _pct(100 - roundi(ClubLife.SORE_LEGS))]])
	if heavy > 0:
		out.append(["cost", "He trains through %s he would have sat out, with a Heavy week's injury risk." % (
				"a Heavy week" if heavy == 1 else "%s Heavy weeks" % _count(heavy))])
	return out


static func _weeks_of(n: int) -> String:
	return "%s week%s" % [_count(n), "" if n == 1 else "s"]


## A finish put on the record (the papers, pre-season): when the papers can come
## back for it and what answering them then costs, read from the card that does
## it (media_papers_reckoning), so the line cannot drift from it.
const RECKONING_CARD := "media_papers_reckoning"


static func _record_words(facts: Dictionary) -> String:
	var t := StoryDeck.by_id(StoryDeck.all(), RECKONING_CARD)
	var head := "You have put that finish on the record."
	if t.is_empty():
		return head + " The board's target stays where it is."
	var costs := []
	for c in t.get("choices", []):
		for ce in c.get("effects", []):
			if str(ce.get("op", "")) == "board" and int(ce.get("d", 0)) < 0:
				costs.append(absi(int(ce["d"])))
	costs.sort()
	var needs: Dictionary = t.get("needs", {})
	# The window counts from the week the finish goes on the record (this card's week).
	var at := maxi(0, int(facts.get("round", 0)))
	var quiet := absi(int((t.get("unanswered", {}) as Dictionary).get("board", 0)))
	var price := ""
	if not costs.is_empty():
		price = _pct(int(costs[0])) if int(costs[0]) == int(costs[costs.size() - 1]) else "%s to %s" % [_pct(int(costs[0])), _pct(int(costs[costs.size() - 1]))]
		price = ", and answering them then costs board confidence %s%s" % [price, (" (%s if you say nothing)" % _pct(quiet)) if quiet > 0 else ""]
	return "%s If the club is below it between rounds %d and %d, the papers can come back for it once%s. The board's target stays where it is." % [
			head, at + int(needs.get("after", 0)), at + int(needs.get("within", 0)), price]


## The words for one effect, gains and costs together (a choice's detail and a
## captain's outcome read this).
static func _effect_words(e: Dictionary, facts: Dictionary) -> String:
	if str(e.get("op", "")) == "explain":
		return "{kpi_or_need}"
	var out: PackedStringArray = []
	for part in _effect_parts(e, facts):
		if str(part[0]) != "note":
			out.append(str(part[1]))
	if str(e.get("op", "")) == "delegate":
		return _delegate_words(e, facts)
	return " ".join(out)


## "8%".
static func _pct(n: int) -> String:
	return "%d%%" % n


## His chance of an injury playing sore, as a percentage ("about 20%"); an
## older card that only carried the "1 in N" odds keeps them.
static func _sore_chance(facts: Dictionary) -> String:
	return "{sore_pct}" if facts.has("sore_pct") else "{sore_odds}"


## How long an injury keeps him out, from the injury table: "66% of injuries
## are two weeks or less".
static func _injury_length_words() -> String:
	var short := 0.0
	for row in Injuries.SEVERITY:
		if int(row[1]) <= 2:
			short += float(row[2])
	return "%s of injuries are two weeks or less" % _pct(roundi(short * 100.0))


## A broken promise's price, in the order it lands. `trust` is the move
## (negative); the opinion it costs is from his trust in `facts` today.
static func _broken_words(sting: int, trust: int, facts: Dictionary) -> String:
	return "his morale falls up to %s, his opinion of you falls %d and the group's togetherness drops %s." % [
			_pct(sting), -Trust.opinion_move(int(facts.get("trust", 0)), trust), _pct(BROKEN_TOGETHER)]


## A slow start: the chance, the match it is for and what it costs at the first bounce.
static func _slow_words(e: Dictionary) -> String:
	var who := str(e.get("who", "subject"))
	# "on": "week" is this week's game (a card in the season), "grand_final" is
	# Saturday; a finals card's chance is for the next final.
	var when := "his next final" if who == "subject" else "its next final"
	if str(e.get("on", "")) == "grand_final":
		when = "Saturday"
	elif str(e.get("on", "")) == "week":
		when = "this week's game"
	var legs := _pct(100 - roundi(ClubLife.SLOW_LEGS))
	var chance := _pct(int(e.get("chance", 0)))
	if who == "subject":
		return "About a %s chance he starts %s slowly, %s short of fresh legs at the first bounce." % [chance, when, legs]
	return "About a %s chance %s starts %s slowly, every one of them %s short of fresh legs at the first bounce." % [
			chance, "the side" if who == "side" else "the whole list", when, legs]


## A culture strand's step: "Standards rises 1%."
static func _culture_words(e: Dictionary, d: int) -> String:
	var label := "Standards"
	for st in Culture.STRANDS:
		if str(st[0]) == str(e.get("strand", "")):
			label = str(st[1])
	return "Club culture: %s %s %s." % [label, "up" if d > 0 else "down", _pct(absi(d))]


## Weeks of running, in plain football maths (director, 2026-10-19: "plain
## football language with simple to understand maths"): the weeks the plan
## adds up to before and after, and what that does to the fitness base. In
## the pre-season the facts carry the forecast (pre_run); elsewhere the line
## says only the weeks.
static func _running_words(d: int, facts := {}) -> String:
	var n := absi(d)
	var head := ("%s more week%s of running" % [_count(n).capitalize(), "" if n == 1 else "s"]) if d > 0 			else ("%s week%s less running" % [_count(n).capitalize(), "" if n == 1 else "s"])
	if str(facts.get("result", "")) != "" and d < 0:
		# The week the season ends (B8): the cost lands on next pre-season's base.
		return "The list starts next pre-season %s week%s of running behind: a strong fitness base takes %s weeks of running by Round 1." % [
				_count(n), "" if n == 1 else "s", PreSeason.run_weeks_text(float(PreSeason.tune("base_strong_from")))]
	if not facts.has("pre_run"):
		return "%s: a strong fitness base takes %s weeks of running by Round 1." % [head, PreSeason.run_weeks_text(float(PreSeason.tune("base_strong_from")))]
	var was := float(facts["pre_run"])
	var now := maxf(0.0, was + float(d))
	var b0 := PreSeason.base_band(was)
	var b1 := PreSeason.base_band(now)
	var sums := "%s: %s weeks becomes %s" % [head, PreSeason.run_weeks_text(was), PreSeason.run_weeks_text(now)]
	if b0 != b1:
		return "%s, so the fitness base %s from %s to %s." % [sums, "goes" if d > 0 else "drops", b0, b1]
	var hint := ""
	if d > 0 and b1 != "strong":
		var need := float(PreSeason.tune("base_strong_from")) if b1 == "sound" else float(PreSeason.tune("base_thin_below"))
		hint = " (%s makes it %s)" % [PreSeason.run_weeks_text(need), "strong" if b1 == "sound" else "sound"]
	elif d < 0 and b1 != "thin":
		var floor_w := float(PreSeason.tune("base_thin_below")) if b1 == "sound" else float(PreSeason.tune("base_strong_from"))
		hint = " (under %s it turns %s)" % [PreSeason.run_weeks_text(floor_w), "thin" if b1 == "sound" else "sound"]
	return "%s, and the fitness base stays %s%s." % [sums, b1, hint]


## Weeks of drilling the plan the side plays, in plain words: where its
## fluency goes and what that is worth (PreSeason familiar_mult), from the
## pre-season facts (drill_plan, drill_level, drill_credit).
static func _drill_words(d: int, facts := {}) -> String:
	var head := "%s more week%s on the game plan" % [_count(d).capitalize(), "" if d == 1 else "s"]
	if not facts.has("drill_plan"):
		return "%s: every %d weeks of drilling raises the side's fluency in a plan one step (low, medium, high)." % [head, int(PreSeason.tune("drill_step_weeks"))]
	var plan := str(facts["drill_plan"])
	var base := float(facts.get("drill_level", PreSeason.WELL))
	var credit := float(facts.get("drill_credit", 0.0))
	var l0 := PreSeason.drilled_fluency(base, credit)
	var l1 := PreSeason.drilled_fluency(base, credit + float(d))
	if l1 != l0:
		return "%s: the side's fluency in %s goes from %s to %s, so the plan works at %d%% of its strength instead of %d%%." % [
				head, plan, PreSeason.fluency_long(l0), PreSeason.fluency_long(l1),
				roundi(PreSeason.familiar_mult(l1) * 100.0), roundi(PreSeason.familiar_mult(l0) * 100.0)]
	return "%s: the side already knows %s as well as it can (high fluency), so it gains nothing more." % [head, plan]


## A role trial: where he plays and for how long.
static func _trial_words(e: Dictionary) -> String:
	var n := int(e.get("weeks", 3))
	return "He plays as a {trial_word} for the next %s %s, then goes back to being a {trial_home}." % [_count(n), "game" if n == 1 else "games"]


## What a role trial costs the side: those games away from his usual spot, and
## how he rates there against where he plays now.
static func _trial_cost_words(e: Dictionary, facts: Dictionary) -> String:
	var n := int(e.get("weeks", 3))
	var head := "%s %s away from his usual spot" % [_count(n).capitalize(), "game" if n == 1 else "games"]
	if not facts.has("trial_ovr"):
		return head + "."
	return "%s: he rates {trial_ovr} as a {trial_word}, against {overall} as a {trial_home}." % head


static func _count(n: int) -> String:
	return (["one", "two", "three", "four", "five", "six"][clampi(n, 1, 6) - 1]) as String


## Left to the captain: what happens if the group listens and what if it doesn't,
## worded from the choice's own held / failed effects, and which way it stands now.
static func _standing_words(facts: Dictionary) -> String:
	if bool(facts.get("delegate_holds", false)):
		return "As it stands the group would listen to {name}."
	return "As it stands the group wouldn't listen to {name}."


static func _delegate_words(e: Dictionary, facts: Dictionary) -> String:
	var held := _lower_first(_outcome_words(e.get("held", []), facts))
	var failed := _lower_first(_outcome_words(e.get("failed", []), facts))
	if bool(facts.get("delegate_holds", false)):
		return "As it stands the group would listen to {name}: %s If they didn't, %s" % [held, failed]
	return "As it stands the group wouldn't listen to {name}: %s If they did, %s" % [failed, held]


static func _outcome_words(effects: Array, facts: Dictionary) -> String:
	var out: PackedStringArray = []
	for ne in effects:
		var w := _effect_words(ne, facts)
		if w != "":
			out.append(w)
	return " ".join(out) if not out.is_empty() else "nothing changes."


static func _lower_first(s: String) -> String:
	return s.substr(0, 1).to_lower() + s.substr(1)


## Every phrase names the thing that moves (morale, trust, board confidence),
## its direction and its size, in the names the game shows the player.
static func _morale_words(d: int, who: String) -> String:
	var move := "%s %s" % ["up" if d > 0 else "down", _pct(absi(d))]
	if who == "subject":
		return "His morale %s." % move
	if who == "vice":
		return "{vice_name}'s morale %s." % move
	var group: String = {"side": "across the side", "all": "across the whole list", "others": "in the rest of the group"}.get(who, "in the group")
	return "Morale %s %s." % [move, group]


static func _board_words(d: int) -> String:
	return "Board confidence %s %s." % ["up" if d > 0 else "down", _pct(absi(d))]


## A trust move as the opinion the game shows, from his trust `t` today:
## "His opinion of you down 2, to 48/100."
static func _trust_words(d: int, t: int) -> String:
	var o := Trust.opinion_move(t, d)
	if o == 0:
		return "His opinion of you stays %d/100." % Trust.opinion(t)
	return "His opinion of you %s %d, to %d/100." % ["up" if o > 0 else "down", absi(o), Trust.opinion(t) + o]


## What a fall in his opinion of you does to his next contract talks, from the
## refusal rule (Contracts.refuse_chance): the odds he won't re-sign, or how
## close the fall takes him to them.
static func _refuse_words(d: int, t: int) -> String:
	var after := Trust.opinion(t) + Trust.opinion_move(t, d)
	var chance := Contracts.refuse_chance(after)
	if chance > 0:
		return "At contract time that is %s %d%% chance he won't re-sign with you." % [LeagueStories.an(chance), chance]
	return "Under %d/100 he may refuse to re-sign with you, %d%% for each point under." % [
			Contracts.REFUSE_BELOW, Contracts.REFUSE_PER_POINT]


## What changed, for the card's result line: only the levers a player feels.
static func aftermath(applied: Dictionary) -> String:
	var out: PackedStringArray = []
	var o: Array = applied.get("opinion", [])
	if o.size() == 2 and int(o[0]) != int(o[1]):
		out.append("His opinion of you: %d → %d/100." % [int(o[0]), int(o[1])])
	var b := int(applied.get("board", 0))
	if b != 0:
		out.append("Board confidence went up." if b > 0 else "Board confidence went down.")
	return " ".join(out)
