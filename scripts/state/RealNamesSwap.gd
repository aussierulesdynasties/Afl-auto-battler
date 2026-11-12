extends RefCounted
## Real names only (director, 2026-11-12): a career saved while generated names
## were shown wrote those names into its news, match stories, almanac, records
## and milestones as plain text. This rewrites them once, when such a save is
## loaded, so a real player is never left under an invented name.
##
## Only a full generated name ("Josh Hart") is swapped, and only when it can
## mean one real person: a name two people carry, or one a generated player
## also has, is left alone. A player's own record keeps its "name" and
## "generic_name" (they are never shown for him, and saves expect them).


## Keys that hold the name of an invented person who is not a player or coach
## (ClubArcs: the chairman and the journalist, drawn from the same name lists
## as a real coach's hidden label, so the two can meet).
const PEOPLE_KEYS := ["chairman", "old_chairman", "journalist"]


## Every string in `state` (a decoded save) has each real person's generated
## name replaced by his real one. `pool` adds people the save no longer holds
## (the dataset's players). Returns how many strings changed.
static func apply(state: Dictionary, pool: Array = []) -> int:
	var names := names_in(state, pool)
	if names.is_empty():
		return 0
	return _walk(state, _by_first(names), _finder())


## generated name -> real name, for every real person found in `v` and `pool`.
static func names_in(v, pool: Array = []) -> Dictionary:
	var found := {}    # generated name -> real name ("" once two people claim it)
	var taken := {}    # names that belong to someone as they stand
	var seen := {}     # ids the save already names
	_collect(v, found, taken, seen)
	for p in pool:
		if p is Dictionary and not seen.has(str(p.get("id", ""))):
			_note(p, found, taken, seen)
	for key in MediaConference.JOURNALISTS:
		taken[str(MediaConference.JOURNALISTS[key].get("name", ""))] = true
	var out := {}
	for alias in found:
		if str(found[alias]) != "" and not taken.has(alias):
			out[alias] = found[alias]
	return out


static func _collect(v, found: Dictionary, taken: Dictionary, seen: Dictionary) -> void:
	if v is Dictionary:
		if v.has("generic_name"):
			_note(v, found, taken, seen)
		for k in v:
			# An invented chairman or journalist owns his name too.
			if v[k] is String and PEOPLE_KEYS.has(str(k)):
				taken[str(v[k]).strip_edges()] = true
			elif v[k] is Dictionary and str(k) == "people":
				for who in v[k]:
					if v[k][who] is String:
						taken[str(v[k][who]).strip_edges()] = true
			if v[k] is Dictionary or v[k] is Array:
				_collect(v[k], found, taken, seen)
	elif v is Array:
		for x in v:
			if x is Dictionary or x is Array:
				_collect(x, found, taken, seen)


static func _note(p: Dictionary, found: Dictionary, taken: Dictionary, seen: Dictionary) -> void:
	var alias := str(p.get("generic_name", "")).strip_edges()
	var real := str(p.get("real_name", "")).strip_edges()
	if p.has("id"):
		seen[str(p["id"])] = true
	if real == "":
		# A generated son or brother of a real player is shown with the family's
		# real surname; anyone else generated owns the name he was given.
		var fam := str(p.get("family_real_last", "")).strip_edges()
		if fam == "" or alias == "":
			if alias != "":
				taken[alias] = true
			return
		real = "%s %s" % [alias.get_slice(" ", 0), fam]
	taken[real] = true
	if alias == "" or alias == real or not alias.contains(" "):
		return
	found[alias] = real if str(found.get(alias, real)) == real else ""


static func _by_first(names: Dictionary) -> Dictionary:
	var by := {}
	for alias in names:
		var first := str(alias).get_slice(" ", 0)
		if not by.has(first):
			by[first] = []
		by[first].append([str(alias), str(names[alias])])
	return by


static func _finder() -> RegEx:
	var re := RegEx.new()
	re.compile("\\p{Lu}[\\p{L}'’-]*")
	return re


static func _walk(v, by: Dictionary, re: RegEx) -> int:
	var n := 0
	if v is Dictionary:
		var own: bool = v.has("generic_name")
		for k in v:
			if own and (str(k) == "generic_name" or str(k) == "name"):
				continue
			var x = v[k]
			if x is String:
				var s := swap(x, by, re)
				if s != x:
					v[k] = s
					n += 1
			elif x is Dictionary or x is Array:
				n += _walk(x, by, re)
			elif x is PackedStringArray:
				var w := _swap_all(x, by, re)
				if w != x:
					v[k] = w
					n += 1
	elif v is Array:
		for i in range(v.size()):
			var x = v[i]
			if x is String:
				var s := swap(x, by, re)
				if s != x:
					v[i] = s
					n += 1
			elif x is Dictionary or x is Array:
				n += _walk(x, by, re)
			elif x is PackedStringArray:
				var w := _swap_all(x, by, re)
				if w != x:
					v[i] = w
					n += 1
	return n


static func _swap_all(a: PackedStringArray, by: Dictionary, re: RegEx) -> PackedStringArray:
	var out := PackedStringArray()
	for s in a:
		out.append(swap(s, by, re))
	return out


## One string with every whole generated name in it replaced.
static func swap(s: String, by: Dictionary, re: RegEx) -> String:
	if s.length() < 3 or not s.contains(" "):
		return s
	var out := ""
	var at := 0
	for m in re.search_all(s):
		var start := m.get_start()
		if start < at or not by.has(m.get_string()):
			continue
		for pair in by[m.get_string()]:
			var alias: String = pair[0]
			var end := start + alias.length()
			if s.substr(start, alias.length()) != alias:
				continue
			# "Josh Hartley" is not "Josh Hart".
			if end < s.length() and _is_letter(s.unicode_at(end)):
				continue
			out += s.substr(at, start - at) + str(pair[1])
			at = end
			break
	if at == 0:
		return s
	return out + s.substr(at)


static func _is_letter(c: int) -> bool:
	return (c >= 65 and c <= 90) or (c >= 97 and c <= 122) or c >= 192
