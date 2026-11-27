extends RefCounted
## A test's way to read and set OVR now that it is read from the attributes and
## never stored (Director Bible 4.2.30a, docs/RATING_REBUILD.md §3). Snapshot
## rows (a match roster, a draft read, a medical row) still carry the number
## they were given; a player carries attributes.


## His OVR: read from his attributes when he has them (Rating.ovr), else the
## number a snapshot row carries, else `fallback`.
static func of(d: Dictionary, fallback: Variant = null) -> Variant:
	if not (d.get("attr", {}) as Dictionary).is_empty():
		return Rating.ovr(d, fallback)
	return d.get("overall", fallback)


## Gives a test player an OVR of `n` by moving every attribute his position
## weighs by the same amount (a snapshot row with no attributes takes the
## number itself). Returns him.
static func to(d: Dictionary, n: float) -> Dictionary:
	var want := clampi(int(round(n)), 1, 99)
	if (d.get("attr", {}) as Dictionary).is_empty():
		if d.has("overall"):
			d["overall"] = want
			return d
		# Only the attributes his position weighs are set; the rest keep the
		# game's own defaults (Attributes.value).
		d["attr"] = {}
	var a: Dictionary = d["attr"]
	var apos := Rating.apos_of(d)
	var weights: Dictionary = Rating.WEIGHTS[apos]
	for _i in 8:
		var gap := int(round(Rating.unstretch(want) - Rating.raw_of(a, apos)))
		if gap == 0:
			break
		for k in weights:
			a[k] = clampi(int(round(float(a.get(k, 50)))) + gap, 1, 99)
	# The stretch moves OVR more than a point for an even point: the last steps
	# go one attribute at a time, lightest first.
	var keys: Array = weights.keys()
	keys.sort_custom(func(x, y): return int(weights[x]) < int(weights[y]))
	for _i in 400:
		var now := Rating.of_attrs(a, apos)
		if now == want:
			break
		var k: String = keys[_i % keys.size()]
		a[k] = clampi(int(round(float(a.get(k, 50)))) + (1 if now < want else -1), 1, 99)
	return d
