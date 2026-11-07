class_name CareerRecord
extends RefCounted
## The facts on record from a player's career, for the Career section of his
## sheet (T5.r110, P-37; director "Yes", 2026-10-18). Reads what is already
## kept and writes nothing; a line is only ever a fact the save recorded:
##   Career        his debut season and club (only a career on record in full),
##                 the clubs he was at for a premiership
##   Firsts        his debut match, when it was for your club
##   Milestones    his milestone games and goals (your matches only)
##   honour_roll   league awards by year: Brownlow, Coleman, Coaches Award,
##                 Rising Star, Norm Smith, Golden Fist; your club's best and
##                 fairest and All-Australians in seasons you coached
##   p["honours"]  counts the roll cannot date: best and fairests at other
##                 clubs, All-Australian jumpers, seasons as captain
##
## `skip` holds what his "With us" lines already say (Remembered.sheet_keys:
## "debut", "flag:2030", "bf:2029"), so a fact is said once on the sheet. His
## games, goals and clubs are the totals line's, never repeated here.
##
## Each line is {"text", "bold"}: honours bold, the rest plain. Oldest first:
## debut, milestones, flags, then awards.

const AWARDS := [["brownlow", "Brownlow Medal"], ["coleman", "Coleman Medal"],
		["coaches_award", "Coaches Award"], ["rising_star", "Rising Star"],
		["norm_smith", "Norm Smith Medal"], ["golden_fist", Awards.GOLDEN_FIST]]


static func lines(p: Dictionary, honour_roll: Array, milestone_log: Dictionary, my_club: String,
		club_name: Callable, skip: Dictionary = {}) -> Array:
	var out := []
	var id := str(p.get("id", ""))
	if id == "":
		return out
	var stints: Array = Career.of(p).get("stints", [])

	# His debut: the match when it was for you, else the season and club when
	# his whole career is on record.
	if not skip.has("debut"):
		var d := Firsts.get_one(p, "debut")
		if not d.is_empty():
			var at := str(stints[0][0]) if not stints.is_empty() else my_club
			out.append(_l("Debuted %s, for %s." % [Firsts.when_text(d), club_name.call(at)]))
		elif Career.complete(p) and not stints.is_empty():
			out.append(_l("Debuted in %d, for %s." % [int(stints[0][1]), club_name.call(str(stints[0][0]))]))

	# Milestone games and goals, as the match recorded them.
	for e in milestone_log.get("log", []):
		if not (e is Dictionary) or str(e.get("who", "")) != "player" or str(e.get("id", "")) != id:
			continue
		var when := Firsts.when_text({"year": int(e.get("year", 0)), "label": str(e.get("label", ""))})
		match str(e.get("kind", "")):
			"games":
				out.append(_l("%s game %s." % [_ordinal(int(e.get("value", 0))), when]))
			"goals":
				out.append(_l("%s career goal %s." % [_ordinal(int(e.get("value", 0))), when]))

	# Premierships: the club he was at that season, grouped by club.
	var flags := {}
	var flag_clubs := []
	for e in honour_roll:
		if not (e is Dictionary):
			continue
		var y := int(e.get("year", 0))
		var premier := str(e.get("premier", ""))
		if premier == "" or (premier == my_club and skip.has("flag:%d" % y)):
			continue
		for st in stints:
			if str(st[0]) == premier and y >= int(st[1]) and y <= int(st[2]):
				if not flags.has(premier):
					flags[premier] = []
					flag_clubs.append(premier)
				(flags[premier] as Array).append(y)
				break
	for c in flag_clubs:
		var ys: Array = flags[c]
		out.append(_l("At %s for the %s premiership%s." % [club_name.call(c), _and_years(ys),
				"" if ys.size() == 1 else "s"], true))

	# League awards, by year.
	for pair in AWARDS:
		var ys := []
		for e in honour_roll:
			if not (e is Dictionary):
				continue
			var rows = e.get(pair[0], [])
			if rows is Array and not (rows as Array).is_empty() and rows[0] is Dictionary \
					and str((rows[0] as Dictionary).get("id", "")) == id:
				ys.append(int(e.get("year", 0)))
		if not ys.is_empty():
			out.append(_l("%s %s." % [pair[1], _years(ys)], true))

	# Best and fairests: dated where the roll has them (your club, the seasons
	# you coached it), else the count kept on him.
	var h: Dictionary = p.get("honours", {}) if p.get("honours") is Dictionary else {}
	var bf_dated := {}
	var bf_order := []
	for e in honour_roll:
		if not (e is Dictionary):
			continue
		var rows = e.get("my_bf", [])
		var c := str(e.get("my_club", ""))
		var y := int(e.get("year", 0))
		if rows is Array and not (rows as Array).is_empty() and rows[0] is Dictionary \
				and str((rows[0] as Dictionary).get("id", "")) == id and c != "":
			if not bf_dated.has(c):
				bf_dated[c] = []
				bf_order.append(c)
			(bf_dated[c] as Array).append(y)
	for c in bf_order:
		var ys: Array = (bf_dated[c] as Array).filter(func(y): return not (c == my_club and skip.has("bf:%d" % y)))
		if not ys.is_empty():
			out.append(_l(_bf_line("%s %s" % [BestAndFairest.heading(c, str(club_name.call(c))), _years(ys)], c, my_club, club_name), true))
	var bf_counts = h.get("bf", {})
	if bf_counts is Dictionary:
		for c in bf_counts:
			var n := int(bf_counts[c])
			if n > 0 and not bf_dated.has(str(c)):
				out.append(_l(_bf_line(BestAndFairest.count_line(str(c), str(club_name.call(str(c))), n), str(c), my_club, club_name), true))

	# All-Australian: dated in the seasons you coached his club, counted otherwise.
	var aa := []
	for e in honour_roll:
		if e is Dictionary and (e.get("my_aa", []) as Array).has(id):
			aa.append(int(e.get("year", 0)))
	var aa_n := maxi(aa.size(), int(h.get("aa", 0)))
	if aa_n > 0:
		out.append(_l("All-Australian %s." % _years(aa) if aa.size() == aa_n
				else "All-Australian in %d seasons." % aa_n if aa_n > 1 else "All-Australian once.", true))

	# Seasons as captain.
	var capt = h.get("captain", {})
	if capt is Dictionary:
		for c in capt:
			var n := int(capt[c])
			if n > 0:
				out.append(_l("Captain of %s, %d season%s." % [club_name.call(str(c)), n, "" if n == 1 else "s"]))
	return out


## A club medal names its club when it is not yours ("Keith "Bluey" Truscott
## Medal at Melbourne."), so a medal from his old club reads as theirs.
static func _bf_line(text: String, club: String, my_club: String, club_name: Callable) -> String:
	if club != my_club and BestAndFairest.is_named(club):
		return "%s at %s." % [text, club_name.call(club)]
	return text + "."


static func _l(text: String, bold := false) -> Dictionary:
	return {"text": text, "bold": bold}


## "2029, 2031"
static func _years(ys: Array) -> String:
	return ", ".join(PackedStringArray(ys.map(func(y): return str(y))))


## "2030", "2030 and 2032", "2028, 2030 and 2032"
static func _and_years(ys: Array) -> String:
	if ys.size() == 1:
		return str(ys[0])
	return "%s and %d" % [_years(ys.slice(0, ys.size() - 1)), int(ys[-1])]


static func _ordinal(n: int) -> String:
	var suffix := "th"
	if n % 100 < 11 or n % 100 > 13:
		suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
	return "%d%s" % [n, suffix]
