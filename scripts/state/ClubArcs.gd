class_name ClubArcs
extends RefCounted
## GameState's side of the coach's career arcs (CoachArcs): triggers read
## from real game state, the coach's own record, the week's arc beat as a Hub
## event card, and what an answer moves on. Without a club every entry point
## returns at once and writes nothing.
## `gs` is GameState; its state lives in gs.coach_arcs.

const NEWS_KIND := "coach_arc"


static func on(gs) -> bool:
	return str(gs.my_club) != ""


static func _st(gs) -> Dictionary:
	if not (gs.coach_arcs is Dictionary):
		gs.coach_arcs = {}
	return CoachArcs.ensure(gs.coach_arcs)


# ---------------------------------------------------------------------------
# The season's start: the coach's record, endings, season triggers
# ---------------------------------------------------------------------------
static func season_start(gs) -> void:
	if not on(gs) or gs.season == null:
		return
	var st := _st(gs)
	var year := int(gs.season_year)
	_count_last_season(gs, st)
	_people(gs, st)
	st["counts"] = {"year": year, "refusals": 0, "statements": 0}
	var defs := CoachArcs.all()
	for id in (st["active"] as Dictionary).keys():
		var def := CoachArcs.by_id(defs, str(id))
		if def.is_empty():
			st["active"].erase(id)
			continue
		var rec: Dictionary = st["active"][id]
		var ending := CoachArcs.closing(def, rec, close_facts(gs, rec), year)
		if ending != "":
			_end(gs, st, def, rec, ending, "Season start")
		elif str(def.get("season_line", "")) != "" and int(rec.get("start", year)) < year:
			# An arc that runs on (runs_on) says where it stands each season.
			var line := StoryEngine.fill(str(def["season_line"]), _facts(gs, st, rec, {"club": GameDB.club_name(gs.my_club), "opp": ""}))
			CoachArcs.log_line(st, year, "Season start", str(id), line)
			gs.add_news(NEWS_KIND, line)
	var ctx := ClubStories.context(gs)
	_try_starts(gs, st, defs, ctx, true)


## The last season, counted once into the coach's own record (catalogue need 4).
static func _count_last_season(gs, st: Dictionary) -> void:
	var c: Dictionary = st["coach"]
	var year := int(gs.season_year)
	if int(c["start"]) == 0:
		c["start"] = year
		c["seen"] = year - 1
	if str(c["club"]) == "":
		c["club"] = str(gs.my_club)
		(c["clubs"] as Array).append({"code": str(gs.my_club), "name": GameDB.club_name(gs.my_club), "from": year, "to": 0, "why": "first job"})
	for h in gs.honour_roll:
		var y := int(h.get("year", 0))
		# Every season he coached counts, at whichever club he coached it.
		if y <= int(c["seen"]) or y >= year or str(h.get("my_club", "")) == "":
			continue
		c["seasons"] = int(c["seasons"]) + 1
		var wld := str(h.get("my_record", "0-0-0")).split("-")
		for n in wld:
			c["games"] = int(c["games"]) + int(n)
		# The flag counts for the club he coached that season, not the one he
		# has just moved to (a move at the rollover lands before this count).
		if str(h.get("premier", "")) == str(h.get("my_club", "")):
			c["flags"] = int(c["flags"]) + 1
			c["last_flag"] = y
		c["seen"] = y
	for p in gs.my_list:
		c["coached"][str(p["id"])] = true


## Named people who are not players (catalogue need 3): the chairman, and the
## journalist (the papers' writer when the club has one).
static func _people(gs, st: Dictionary) -> void:
	var people: Dictionary = st["people"]
	if not people.has("chairman"):
		people["chairman"] = _gen_name(int(gs.career_seed), "chairman|" + str(gs.my_club))
	if not people.has("journalist"):
		var writer := str(ClubStories.papers_facts(gs).get("writer", ""))
		people["journalist"] = writer if writer != "" else _gen_name(int(gs.career_seed), "journalist")


static func _gen_name(seed: int, what: String) -> String:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("arcname|%d|%s" % [seed, what])
	return "%s %s" % [Coaches.COACH_FIRST_NAMES[rng.randi_range(0, Coaches.COACH_FIRST_NAMES.size() - 1)],
			GameDB.FICTIONAL_LAST_NAMES[rng.randi_range(0, GameDB.FICTIONAL_LAST_NAMES.size() - 1)]]


# ---------------------------------------------------------------------------
# The week: endings for players who left, weekly triggers, one due beat
# ---------------------------------------------------------------------------
static func week(gs) -> void:
	if not on(gs) or gs.season == null:
		return
	var st := _st(gs)
	# The rollover builds the new season before its pre-season opens: that
	# first pick is not Round 1, so no arc starts or plays in it.
	if _rollover_pick(gs, st):
		return
	_people(gs, st)
	if int(st["counts"].get("year", 0)) != int(gs.season_year):
		st["counts"] = {"year": int(gs.season_year), "refusals": 0, "statements": 0}
	var defs := CoachArcs.all()
	var ctx := ClubStories.context(gs)
	# A player arc whose player has gone ends now, by its own rule for it.
	for id in (st["active"] as Dictionary).keys():
		var def := CoachArcs.by_id(defs, str(id))
		var rec: Dictionary = st["active"][id]
		if str(def.get("kind", "")) == "player" and gs.list_player(str(rec.get("who", ""))).is_empty():
			var ending := CoachArcs.closing(def, rec, close_facts(gs, rec), int(gs.season_year))
			_end(gs, st, def, rec, ending if ending != "" else "faded", _label(gs))
	ClubMoves.record_reunion(gs, st)
	# A move decided at the season's close (ClubMoves.season_close) has just
	# ended every arc at the club he is leaving: none starts there after it.
	if (st.get("move", {}) as Dictionary).is_empty():
		_try_starts(gs, st, defs, ctx, false)
	var card := _due_card(gs, st, defs, ctx)
	if card.is_empty():
		return
	# One arc beat beside one deck card (catalogue need 8).
	while gs.week_events.size() > 1:
		gs.week_events.pop_back()
	gs.week_events.append(card)


static func _due_card(gs, st: Dictionary, defs: Array, ctx: Dictionary) -> Dictionary:
	var w: int = gs.story_week()
	var year := int(gs.season_year)
	var order: Array = (st["active"] as Dictionary).keys()
	order.sort_custom(func(a, b): return int(st["active"][a]["last_w"]) < int(st["active"][b]["last_w"]))
	for id in order:
		var def := CoachArcs.by_id(defs, str(id))
		var rec: Dictionary = st["active"][id]
		var subj := _subject_facts(ctx, rec) if str(def.get("kind", "")) == "player" else {}
		if str(def.get("kind", "")) == "player" and subj.is_empty():
			continue
		var facts := _facts(gs, st, rec, ctx["club"])
		facts.merge(subj, true)
		var b := CoachArcs.due_beat(def, rec, w, year, str(ctx["phase"]), facts)
		if b.has("_skipped"):
			CoachArcs.log_line(st, year, _label(gs), str(id), "(%s passed: its moment never came)" % str(b["_skipped"]))
			continue
		if b.is_empty():
			continue
		var card := _build(gs, st, def, rec, b, ctx, w)
		if not card.is_empty():
			return card
	return {}


static func _build(gs, st: Dictionary, def: Dictionary, rec: Dictionary, b: Dictionary, ctx: Dictionary, w: int) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("arc|%d|%d|%d|%s" % [int(ctx["seed"]), int(ctx["year"]), int(ctx["week"]), str(b["id"])])
	var t: Dictionary = StoryDeck.normalise(b)
	var club := _facts(gs, st, rec, ctx["club"])
	var subj := {"kind": "club"}
	if str(def.get("kind", "")) == "player":
		subj = _subject_facts(ctx, rec)
		t["subject"] = {"kind": "player"}
	elif b.has("subject"):
		var want: Dictionary = b["subject"]
		var fits := (ctx["players"] as Array).filter(func(p): return StoryEngine.meets(p, want.get("where", {}), {}))
		subj = StoryEngine.choose(fits, str(want.get("pick", "random")), rng)
		if subj.is_empty():
			return {}
		t["subject"] = {"kind": "player"}
	var card := StoryEngine.build([], t, subj, club, rng, w)
	card["coach_arc"] = str(def["id"])
	card["arc_name"] = str(def.get("name", ""))
	return card


static func _subject_facts(ctx: Dictionary, rec: Dictionary) -> Dictionary:
	for p in ctx["players"]:
		if str(p["id"]) == str(rec.get("who", "")):
			return p
	return {}


## The arc's own facts beside the week's club facts (CoachArcs.ARC_FACTS).
static func _facts(gs, st: Dictionary, rec: Dictionary, club: Dictionary) -> Dictionary:
	var c: Dictionary = st["coach"]
	var f: Dictionary = club.duplicate()
	f.merge(st["people"], true)
	f.merge(rec.get("mem", {}), false)
	f["seasons_coached"] = int(c["seasons"]) + 1
	f["coach_games"] = int(c["games"])
	f["coach_flags"] = int(c["flags"])
	f["drought"] = _dry(st)
	f["arc_times"] = int((st["done"].get(str(rec.get("id", "")), {}) as Dictionary).get("times", 0))
	f["arc_year"] = int(rec.get("start", gs.season_year))
	f["arc_seasons"] = int(gs.season_year) - int(rec.get("start", gs.season_year))
	f["opp_is_rival"] = str(rec.get("mem", {}).get("rival_club", "")) != "" and str(club.get("opp", "")) == str(rec["mem"]["rival_club"])
	var old := str(rec.get("mem", {}).get("old_club", ""))
	f["opp_is_old"] = old != "" and str(club.get("opp", "")) == old
	var hf := hero_facts(gs)
	var who := str(rec.get("who", ""))
	f["hero_streak"] = int(hf["hero_streak"])
	f["hero_count"] = int((hf["hero_counts"] as Dictionary).get(who, 0)) if who != "" else 0
	f["last_hero_mine"] = bool(hf["last_hero_mine"])
	f["hero_is_arc_player"] = who != "" and str(hf["last_hero_id"]) == who
	f["close_losses"] = int(hf["close_losses"])
	f["turned_against"] = int(hf["turned_against"])
	for k in ["rival_club", "father", "old_club", "old_chairman", "former", "suitor", "suitor_president", "assistant", "assistant_to"]:
		if not f.has(k):
			f[k] = ""
	for k in ["flag_year", "flag_years_on"]:
		if not f.has(k):
			f[k] = 0
	if not f.has("flag_reunion"):
		f["flag_reunion"] = false
	return f


## This season's facts from the match stories (MatchStory.arc_facts).
static func hero_facts(gs) -> Dictionary:
	return MatchStory.arc_facts(gs.match_stories, int(gs.season_year))


## Seasons this coach has gone without a flag at his current club: since his
## last flag there, or since he arrived (a move starts the count again).
static func _dry(st: Dictionary) -> int:
	var c: Dictionary = st["coach"]
	var since := ClubMoves._club_since(st, str(c.get("club", "")))
	if since == 0:
		since = int(c.get("start", 0))
	if since == 0:
		return int(c["seasons"]) if int(c["last_flag"]) == 0 else int(c["seen"]) - int(c["last_flag"])
	if int(c["last_flag"]) >= since:
		return int(c["seen"]) - int(c["last_flag"])
	return maxi(0, int(c["seen"]) - since + 1)


## True for the week pick made while the rollover builds a season whose
## pre-season has not opened yet (GameState.start_season, then open_preseason).
static func _rollover_pick(gs, st: Dictionary) -> bool:
	return int(st["coach"].get("seen", 0)) > 0 and gs.season.round_index == 0 \
			and not gs.season.is_regular_done() and int(gs.preseason.get("year", 0)) != int(gs.season_year)


# ---------------------------------------------------------------------------
# Triggers, from real game state
# ---------------------------------------------------------------------------
static func _try_starts(gs, st: Dictionary, defs: Array, ctx: Dictionary, season_start: bool) -> void:
	var year := int(gs.season_year)
	for def in defs:
		if not CoachArcs.can_start(def, st, year):
			continue
		var hit := trigger(gs, st, def, ctx, season_start)
		if hit.is_empty():
			continue
		var rec := CoachArcs.start(st, def, year, gs.story_week(), str(hit.get("who", "")), hit.get("mem", {}))
		var line := _start_line(def, _facts(gs, st, rec, ctx["club"]))
		CoachArcs.log_line(st, year, "Season start" if season_start else _label(gs), str(def["id"]), "BEGINS: " + line)
		gs.add_news(NEWS_KIND, line)
		# One new arc a week at most.
		if not season_start:
			return


## An arc's start line: one string, or variants as a card's text has them
## ({"when": {facts}, "text"} cases first, else the first plain line).
static func _start_line(def: Dictionary, facts: Dictionary) -> String:
	var sl: Variant = def.get("start_line", "")
	if sl is Array:
		var rng := RandomNumberGenerator.new()
		rng.seed = 0
		var plain: Array = (sl as Array).filter(func(v): return not (v is Dictionary))
		return StoryEngine.variant((sl as Array).filter(func(v): return v is Dictionary) + plain.slice(0, 1), facts, rng)
	return StoryEngine.fill(str(sl), facts)


## {} when the arc's trigger does not hold now, else {"who": player id or "",
## "mem": names to remember}.
static func trigger(gs, st: Dictionary, def: Dictionary, ctx: Dictionary, season_start: bool) -> Dictionary:
	var tr: Dictionary = def.get("trigger", {})
	var club: Dictionary = ctx["club"]
	var players: Array = ctx["players"]
	var c: Dictionary = st["coach"]
	match str(tr.get("kind", "")):
		"hot_seat":
			if season_start and bool(gs.board.get("warned", false)):
				return {"mem": {}}
			if not season_start and str(ctx["phase"]) == "regular" and int(club.get("round", 0)) >= int(tr.get("round_min", 8)) \
					and gs.board_confidence() < int(tr.get("board_below", 40)):
				return {"mem": {}}
		"board_feud":
			if season_start or str(ctx["phase"]) != "regular":
				return {}
			if int(st["counts"].get("refusals", 0)) >= int(tr.get("refusals", 2)) \
					or absi(gs.board_confidence() - side_trust(gs)) >= int(tr.get("gap", 30)):
				return {"mem": {}}
		"protege":
			for p in players:
				var backed := bool(p.get("backed", false)) or (gs.story.get("arcs", {}) as Dictionary).has("backed_kid|" + str(p["id"]))
				if backed and float(p.get("age", 99)) <= float(tr.get("age_max", 20)) and int(p.get("potential", 0)) >= int(tr.get("potential_min", 80)):
					return _player_hit(p)
			# Or a kid the match stories keep naming the hero (plan step 1b).
			if tr.has("hero_count_min"):
				var counts: Dictionary = hero_facts(gs)["hero_counts"]
				for p in players:
					if float(p.get("age", 99)) <= float(tr.get("age_max", 20)) 							and int(counts.get(str(p["id"]), 0)) >= int(tr["hero_count_min"]):
						return _player_hit(p)
		"one_year_too_long":
			for p in players:
				if bool(p.get("last_season", false)) and float(p.get("age", 0)) >= float(tr.get("age_min", 31)) \
						and int(p.get("games", 0)) >= int(tr.get("games_min", 150)):
					return _player_hit(p)
		"drought":
			if season_start and _dry(st) >= int(tr.get("seasons_min", 5)):
				return {"mem": {}}
		"star_wants_out":
			for p in players:
				var unhappy := int(p.get("overall_rank", 99)) <= int(tr.get("top", 3)) and int(p.get("contract_years", 9)) == 1 \
						and ClubLife.morale(p) < int(tr.get("morale_below", 50))
				if unhappy or (gs.trade_requests as Dictionary).has(str(p["id"])):
					return _player_hit(p)
		"media":
			if statements(gs, st) >= int(tr.get("statements", 3)):
				return {"mem": {}}
			# Or a player of yours the hero again and again: the papers come asking.
			if tr.has("hero_count_min"):
				var counts: Dictionary = hero_facts(gs)["hero_counts"]
				for id in counts:
					if int(counts[id]) >= int(tr["hero_count_min"]):
						return {"mem": {}}
		"rivalry":
			for code in gs.season.ladder:
				if str(code) == str(gs.my_club) or not Rivalries.established(gs.my_club, str(code)).is_empty():
					continue
				if Rivalries.state(gs.rivalry_history, gs.my_club, str(code)) == "rivals":
					return {"mem": {"rival_club": GameDB.club_name(str(code)), "rival_code": str(code)}}
		"family_club":
			for p in gs.my_list:
				for tie in p.get("family", []):
					if str(tie.get("relation", "")) == "son of" and (c["coached"] as Dictionary).has(str(tie.get("id", ""))):
						var hit := _player_hit(p)
						hit["mem"]["father"] = _person_name(gs, str(tie["id"]))
						hit["mem"]["father_id"] = str(tie["id"])
						return hit
		"sacked":
			var mv: Dictionary = c.get("moved", {})
			if season_start and str(mv.get("why", "")) == "sacked" and int(mv.get("year", 0)) == int(gs.season_year) - 1:
				return {"mem": _old_club_mem(gs, st, str(mv.get("from", "")))}
		"poached":
			return ClubMoves.poach_trigger(gs, st, tr, season_start)
		"reunion":
			return ClubMoves.reunion_trigger(gs, st, club, ctx, season_start)
		"assistant":
			return ClubMoves.assistant_trigger(gs, st, tr, ctx, season_start)
		"legacy":
			if season_start and (int(c["seasons"]) + 1 >= int(tr.get("seasons_min", 10)) or int(c["games"]) >= int(tr.get("games_min", 250)) \
					or int(c["flags"]) >= int(tr.get("flags_min", 2))):
				return {"mem": {}}
	return {}


## What an arc about a club he left remembers: its name, its chairman in his
## time, and the best player there he coached.
static func _old_club_mem(gs, st: Dictionary, code: String) -> Dictionary:
	var chairman := ""
	for h in st["coach"]["clubs"]:
		if str(h.get("code", "")) == code:
			chairman = str(h.get("chairman", ""))
	return {"old_club": GameDB.club_name(code), "old_code": code, "old_chairman": chairman if chairman != "" else "their chairman",
			"former": ClubMoves.former_player(gs, st, code)}


static func _player_hit(p: Dictionary) -> Dictionary:
	return {"who": str(p["id"]), "mem": {"name": GameDB.player_display_name(p), "first": str(p.get("first", "")),
			"games": int(p.get("games", 0))}}


static func _person_name(gs, id: String) -> String:
	var p: Dictionary = gs._find_player(id)
	if not p.is_empty():
		return GameDB.player_display_name(p)
	var gone: Dictionary = gs.departed_names.get(id, {})
	return GameDB.player_display_name(gone) if not gone.is_empty() else "his father"


## The list's trust in you on the board's 0-100 scale (Trust runs -100..100).
static func side_trust(gs) -> int:
	if gs.my_list.is_empty():
		return 50
	var sum := 0
	for p in gs.my_list:
		sum += Trust.value(gs.relations, Trust.player_key(str(p["id"])))
	return int(round((float(sum) / gs.my_list.size() + 100.0) / 2.0))


## Public statements this season: media cards answered, and press answers on record.
static func statements(gs, st: Dictionary) -> int:
	var n := int(st["counts"].get("statements", 0))
	for k in gs.media_memory:
		var v = gs.media_memory[k]
		if str(k).begins_with("said|") and v is Dictionary and int(v.get("year", 0)) == int(gs.season_year):
			n += 1
	return n


## What a closing rule reads at a season's start (CoachArcs.CLOSE_FACTS).
static func close_facts(gs, rec: Dictionary) -> Dictionary:
	var last: Dictionary = gs.honour_roll[-1] if not gs.honour_roll.is_empty() else {}
	var hist: Array = gs.board.get("history", [])
	var f := {"sacked": bool(gs.board.get("sacked", false)), "warned": bool(gs.board.get("warned", false)),
			"premiers": str(last.get("premier", "")) == str(gs.my_club) and str(last.get("premier", "")) != "",
			"met": bool(hist[-1].get("met", false)) if not hist.is_empty() else false,
			"board": gs.board_confidence(), "ladder_last": int(last.get("my_position", 0))}
	var who := str(rec.get("who", ""))
	if who != "":
		var p: Dictionary = gs.list_player(who)
		f["here"] = not p.is_empty()
		f["morale"] = ClubLife.morale(p) if not p.is_empty() else 0
	return f


# ---------------------------------------------------------------------------
# Answers and endings
# ---------------------------------------------------------------------------
## A card was answered (or settled with no answer, choice -1). An arc card
## moves its arc on; a deck card may count toward a trigger (a board ask
## refused, a public statement).
static func answered(gs, card: Dictionary, choice: int) -> void:
	if not on(gs):
		return
	var st := _st(gs)
	var opts: Array = card.get("options", [])
	var id := str(card.get("coach_arc", ""))
	if id == "":
		_count(st, card, choice)
		return
	if not (st["active"] as Dictionary).has(id):
		return
	var def := CoachArcs.by_id(CoachArcs.all(), id)
	var rec: Dictionary = st["active"][id]
	var key := str(opts[choice].get("key", "")) if choice >= 0 and choice < opts.size() else ""
	var label := str(opts[choice].get("label", "")) if key != "" else "(no answer)"
	var year := int(gs.season_year)
	var ending := CoachArcs.answer(def, rec, str(card.get("tid", "")), key, gs.story_week(), year)
	CoachArcs.log_line(st, year, _label(gs), id, "%s: %s. %s" % [str(card.get("title", "")), label, str(card.get("outcome", ""))])
	if ending != "":
		_end(gs, st, def, rec, ending, _label(gs))


static func _count(st: Dictionary, card: Dictionary, choice: int) -> void:
	var opts: Array = card.get("options", [])
	var cat := str(card.get("category", ""))
	if cat == "board":
		var refused := choice < 0 and not (card.get("unanswered", {}) as Dictionary).is_empty()
		if choice >= 0 and choice < opts.size():
			for e in opts[choice].get("effects", []):
				if str(e.get("op", "")) == "board" and int(e.get("d", 0)) < 0:
					refused = true
		if refused:
			st["counts"]["refusals"] = int(st["counts"].get("refusals", 0)) + 1
	elif cat == "media" and choice >= 0:
		st["counts"]["statements"] = int(st["counts"].get("statements", 0)) + 1


static func _end(gs, st: Dictionary, def: Dictionary, rec: Dictionary, ending: String, label: String) -> void:
	var e: Dictionary = (def.get("endings", {}) as Dictionary).get(ending, {})
	var facts := _facts(gs, st, rec, {"club": GameDB.club_name(gs.my_club), "opp": ""})
	var line := StoryEngine.fill(str(e.get("line", "%s ends." % str(def.get("name", "")))), facts)
	if not gs.board.is_empty():
		if e.has("board_to"):
			gs.board["confidence"] = clampi(int(e["board_to"]), 0, 100)
		elif int(e.get("board", 0)) != 0:
			gs.board["confidence"] = clampi(gs.board_confidence() + int(e["board"]), 0, 100)
	CoachArcs.log_line(st, int(gs.season_year), label, str(def["id"]), "ENDS (%s): %s" % [ending, line])
	gs.add_news(NEWS_KIND, line)
	# The old club's last reunion, for its cooldown (and its premiership year).
	var old := str(rec.get("mem", {}).get("old_code", ""))
	if str(def["id"]) == "reunion" and old != "":
		for h in st["coach"]["clubs"]:
			if str(h.get("code", "")) == old:
				h["reunion"] = int(gs.season_year)
				if bool(rec.get("mem", {}).get("flag_reunion", false)):
					h["anniv"] = int(rec.get("start", gs.season_year))
	CoachArcs.finish(st, str(def["id"]), ending, int(gs.season_year))


static func _label(gs) -> String:
	var ph := ClubStories.phase(gs)
	var wk := ClubStories.week_in_season(gs)
	if ph == "finals":
		return "Finals"
	if ph == "preseason":
		return "Pre-season"
	return "R%d" % wk


## The weekly checklist's big call (WeekChecklist.big_call): the arc beat due
## this week, still to answer. {} or {"text", "route", "card"}.
static func big_call(gs) -> Dictionary:
	if not on(gs):
		return {}
	for c in gs.week_events:
		if str((c as Dictionary).get("coach_arc", "")) != "" and not bool(c.get("resolved", false)):
			return {"text": str(c.get("title", "")), "route": "", "card": c}
	return {}
