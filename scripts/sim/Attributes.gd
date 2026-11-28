class_name Attributes
extends RefCounted
## The one list of a player's 18 attributes (the rating rebuild, Director
## Bible 4.2.30a, docs/RATING_REBUILD.md §2): their keys, groups, labels and
## the order each screen shows them in. Every attribute is 1-99 on one
## league-wide scale: an 80 Kicking kicks the same for a key defender and a
## midfielder. They are the only truth about a player; his OVR is worked out
## from them (Rating.gd) and never stored.
## Kept free of every autoload (tools/lint/autoload_reach.py).

## Storage order: how saves, data files and the players list keep them.
const KEYS := ["speed", "endurance", "strength", "work_rate", "kicking", "handballing", "marking",
		"contested_marking", "one_on_one", "contested_ball", "goalkicking", "ruck", "vision",
		"reading_play", "pressure", "forward_craft", "discipline", "durability"]

## Strength's share of a ruck or one-on-one contest (RATING_REBUILD §2: Strength
## drives "breaking tackles, one-on-one and ruck contests"): 20%, the share Speed
## and Endurance each take of a tackle. The contest attribute keeps the rest.
const STRENGTH_SHARE := 0.20

## The four groups (§2).
const PHYSICAL := ["speed", "endurance", "strength", "work_rate"]
const TECHNICAL := ["kicking", "handballing", "marking", "contested_marking", "one_on_one",
		"contested_ball", "goalkicking", "ruck"]
const FOOTY_IQ := ["vision", "reading_play", "pressure", "forward_craft"]
const MENTAL := ["discipline", "durability"]

## What out of position cuts (Rating.cut, RATING_REBUILD §2): Technical and
## Footy IQ, and "disposal", read from Kicking and Handballing.
const CUT_BY_POSITION := {"kicking": true, "handballing": true, "marking": true,
		"contested_marking": true, "one_on_one": true, "contested_ball": true, "goalkicking": true,
		"ruck": true, "vision": true, "reading_play": true, "pressure": true, "forward_craft": true,
		"disposal": true}

## [key, label] in the order a card lists them (player sheet, training, the
## stat guide's names, the pre-season and training reports): group by group.
const CARD_ROWS := [
	["speed", "Speed"], ["endurance", "Endurance"], ["strength", "Strength"], ["work_rate", "Work Rate"],
	["kicking", "Kicking"], ["handballing", "Handballing"], ["marking", "Marking"],
	["contested_marking", "Contested marking"], ["one_on_one", "One-on-one defence"],
	["contested_ball", "Contested ball"], ["goalkicking", "Goalkicking"], ["ruck", "Ruck"],
	["vision", "Vision"], ["reading_play", "Reading the play"], ["pressure", "Pressure"],
	["forward_craft", "Forward craft"], ["discipline", "Discipline"], ["durability", "Durability"],
]

## The word a sentence uses (the profile's strengths and weaknesses), in card
## order. One differs from the card label: "Ruck work".
const PROSE_LABELS := {
	"speed": "Speed", "endurance": "Endurance", "strength": "Strength", "work_rate": "Work Rate",
	"kicking": "Kicking", "handballing": "Handballing", "marking": "Marking",
	"contested_marking": "Contested marking", "one_on_one": "One-on-one defence",
	"contested_ball": "Contested ball", "goalkicking": "Goalkicking", "ruck": "Ruck work",
	"vision": "Vision", "reading_play": "Reading the play", "pressure": "Pressure",
	"forward_craft": "Forward craft", "discipline": "Discipline", "durability": "Durability",
}

## The three a formation callout shows for each line, [key, short label]:
## the old three under their new names (intercept is Reading the play, carry
## Speed, goals a game Forward craft, accuracy Goalkicking). Phase 8 words.
const CALLOUTS := {
	"DEF": [["reading_play", "Reading the play"], ["pressure", "Pressure"], ["kicking", "Kicking"]],
	"MID": [["contested_ball", "Contested"], ["handballing", "Handballing"], ["speed", "Speed"]],
	"FWD": [["forward_craft", "Forward craft"], ["contested_marking", "Contested marking"],
			["goalkicking", "Goalkicking"]],
	"RUCK": [["ruck", "Ruck"], ["contested_ball", "Contested"], ["contested_marking", "Contested marking"]],
}

## [heading, [keys]] as the stat guide groups them, in the order they read.
const GROUPS := [
	["Physical", PHYSICAL],
	["Technical", TECHNICAL],
	["Footy IQ", FOOTY_IQ],
	["Mental and durability", MENTAL],
]

## How he plays, as "plays like" compares players: every key but discipline
## and durability, which say nothing about his style.
const PLAY_STYLE_KEYS := ["speed", "endurance", "strength", "work_rate", "kicking", "handballing",
		"marking", "contested_marking", "one_on_one", "contested_ball", "goalkicking", "ruck", "vision",
		"reading_play", "pressure", "forward_craft"]

## Handballs' share of AFL disposals: where the match asks for ball use
## without saying kick or handball, Kicking counts 56% and Handballing 44%
## (§2).
const HANDBALL_SHARE := 0.44


## His card label, or the key itself when it is not an attribute.
static func label(key: String) -> String:
	for row in CARD_ROWS:
		if str(row[0]) == key:
			return str(row[1])
	return key


## Ball use where the match does not say kick or handball.
static func disposal_of(a: Dictionary, fallback := 50.0) -> float:
	return (1.0 - HANDBALL_SHARE) * float(a.get("kicking", fallback)) \
			+ HANDBALL_SHARE * float(a.get("handballing", fallback))


## One attribute by key, where "disposal" is the derived ball use above
## (never stored).
static func value(a: Dictionary, key: String, fallback := 50.0) -> float:
	if key == "disposal":
		return disposal_of(a, fallback)
	return float(a.get(key, fallback))
