class_name Attributes
extends RefCounted
## The one list of a player's rated attributes: their keys, the order each
## screen shows them in, their labels and their groups. Every other list
## (Skills.KEYS, the player sheet, training, the stat guide, the formation
## callouts, "plays like", the profile lines) points here, so the rating
## rebuild (Director Bible 4.2.30a, docs/RATING_REBUILD.md) changes one file.
## Phase 1 holds today's 16 skills exactly as the screens showed them; the 17
## attributes arrive with Phase 4.
## Kept free of every autoload, like Skills (tools/lint/autoload_reach.py).

## Storage order: how saves, data files and the players list keep them.
const KEYS := ["kicking", "handballing", "contested_marking", "uncontested_marking",
		"contested", "pressure", "intercept", "speed", "carry", "goalkicking", "accuracy",
		"creating", "ruck", "discipline", "durability", "star"]

## [key, label] in the order a card lists them (player sheet, training, the
## stat guide's names, the pre-season and training reports).
const CARD_ROWS := [
	["kicking", "Kicking"], ["handballing", "Handballing"], ["contested", "Contested ball"],
	["contested_marking", "Contested marking"], ["uncontested_marking", "Uncontested marking"],
	["pressure", "Pressure"], ["intercept", "Intercept"], ["speed", "Speed"], ["carry", "Carry"],
	["goalkicking", "Goalkicking"], ["accuracy", "Accuracy"],
	["creating", "Creating"], ["ruck", "Ruck"], ["discipline", "Discipline"],
	["durability", "Durability"], ["star", "Star power"],
]

## The word a sentence uses (the profile's strengths and weaknesses), in card
## order. Two differ from the card label: "Intercepting" and "Ruck work".
const PROSE_LABELS := {
	"kicking": "Kicking", "handballing": "Handballing", "contested": "Contested ball",
	"contested_marking": "Contested marking", "uncontested_marking": "Uncontested marking",
	"pressure": "Pressure", "intercept": "Intercepting", "speed": "Speed", "carry": "Carry",
	"goalkicking": "Goalkicking", "accuracy": "Accuracy", "creating": "Creating",
	"ruck": "Ruck work", "discipline": "Discipline", "durability": "Durability",
	"star": "Star power",
}

## The three a formation callout shows for each line, [key, short label].
const CALLOUTS := {
	"DEF": [["intercept", "Intercept"], ["pressure", "Pressure"], ["kicking", "Kicking"]],
	"MID": [["contested", "Contested"], ["handballing", "Handballing"], ["carry", "Carry"]],
	"FWD": [["goalkicking", "Goalkicking"], ["contested_marking", "Contested marking"], ["accuracy", "Accuracy"]],
	"RUCK": [["ruck", "Ruck"], ["contested", "Contested"], ["contested_marking", "Contested marking"]],
}

## [heading, [keys]] as the stat guide groups them, in the order they read.
const GROUPS := [
	["Ball winning", ["contested", "contested_marking", "uncontested_marking", "ruck"]],
	["Ball use", ["kicking", "handballing", "carry", "creating"]],
	["Scoring", ["goalkicking", "accuracy"]],
	["Defence", ["pressure", "intercept", "speed"]],
	["Body and class", ["discipline", "durability", "star"]],
]

## How he plays, as "plays like" compares players: every key but discipline
## and durability, which say nothing about his style.
const PLAY_STYLE_KEYS := ["kicking", "handballing", "contested", "contested_marking",
		"uncontested_marking", "pressure", "intercept", "speed", "carry", "goalkicking",
		"accuracy", "creating", "ruck", "star"]


## His card label, or the key itself when it is not an attribute.
static func label(key: String) -> String:
	for row in CARD_ROWS:
		if str(row[0]) == key:
			return str(row[1])
	return key
