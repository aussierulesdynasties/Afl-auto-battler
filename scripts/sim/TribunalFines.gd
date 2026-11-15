class_name TribunalFines
extends RefCounted
## What a player has paid in MRO fines (director, 2026-11-14: "in the stats
## section we should also track how much fees players have accrued from
## tribunal fines"). Every club's players, by the same rule.
##
## A fine's size is the real AFL scale of 2025: $1,000 for a player's first
## fine of the season, $1,875 for his second, $3,125 from his third (the 2025
## MRO fines on record: zerohanger.com's 2025 MRO and Tribunal tracker).
##
## In a Legacy season before 2025 the scale is in that season's money: scaled
## by that season's salary cap against 2025's (bug bash 4, L11), to the
## nearest $25.
##
## Kept on the player as `tribunal_fines`: {"<year>": {"n": fines, "total": dollars}}.
## A save from before this has no key, and reads as no fines.

const SCALE := [1000, 1875, 3125]
const SCALE_YEAR := 2025
const KEY := "tribunal_fines"


## The fine for a player's next one in `year`: the scale by how many he has
## had, in that season's money.
static func next_amount(p: Dictionary, year: int) -> int:
	var base: int = SCALE[mini(count(p, year), SCALE.size() - 1)]
	var cap := Contracts.era_cap(year)
	var cap_then := Contracts.era_cap(SCALE_YEAR)
	if year >= SCALE_YEAR or cap <= 0 or cap_then <= 0:
		return base
	return maxi(25, int(round(float(base) * float(cap) / float(cap_then) / 25.0)) * 25)


## Who hands out a fine in `year`: the Match Review Panel from 2005 (EraRules
## match_review), the Tribunal before it.
static func body(year: int) -> String:
	return "the MRO" if EraRules.on("match_review", year) else "the Tribunal"


## "the MRO sanction" from 2005, "the sanction" before the panel existed.
static func sanction(year: int) -> String:
	return "the MRO sanction" if EraRules.on("match_review", year) else "the sanction"


## Charge him his next fine of `year`; returns the amount.
static func charge(p: Dictionary, year: int) -> int:
	var amount := next_amount(p, year)
	var book: Dictionary = p.get(KEY, {})
	var y: Dictionary = book.get(str(year), {})
	book[str(year)] = {"n": int(y.get("n", 0)) + 1, "total": int(y.get("total", 0)) + amount}
	p[KEY] = book
	return amount


## A fine cleared at the Tribunal is paid back in full.
static func refund(p: Dictionary, year: int, amount: int) -> void:
	var book: Dictionary = p.get(KEY, {})
	var y: Dictionary = book.get(str(year), {})
	if y.is_empty():
		return
	var n := maxi(0, int(y.get("n", 0)) - 1)
	var total := maxi(0, int(y.get("total", 0)) - amount)
	if n == 0 and total == 0:
		book.erase(str(year))
	else:
		book[str(year)] = {"n": n, "total": total}
	if book.is_empty():
		p.erase(KEY)
	else:
		p[KEY] = book


static func season_total(p: Dictionary, year: int) -> int:
	return int((p.get(KEY, {}) as Dictionary).get(str(year), {}).get("total", 0))


static func count(p: Dictionary, year: int) -> int:
	return int((p.get(KEY, {}) as Dictionary).get(str(year), {}).get("n", 0))


static func career_total(p: Dictionary) -> int:
	var t := 0
	for y in p.get(KEY, {}):
		t += int(p[KEY][y].get("total", 0))
	return t


static func career_count(p: Dictionary) -> int:
	var t := 0
	for y in p.get(KEY, {}):
		t += int(p[KEY][y].get("n", 0))
	return t


## "$1,875": dollars with thousands commas.
static func money(amount: int) -> String:
	var s := str(absi(amount))
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return "$" + s + out
