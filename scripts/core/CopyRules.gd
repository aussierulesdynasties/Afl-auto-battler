class_name CopyRules
extends RefCounted
## The game's one banned-terms list (copy voice, director 2026-11-10: option B, the senior
## coach's briefing; docs/VISUAL_STYLE_GUIDE.md §5.1). Every UI test and the screen lint read
## it; a surface adds its own extras on top, never a second copy of these.
##
## OVR and POT stay allowed (director, 2026-11-10: "Keep the numbers"). The match feed keeps a
## broadcaster's voice (director, 2026-11-10: "Keep broadcaster"), so "!" is allowed there.
## "Sim the week" keeps the word "sim" (director, 2026-11-10) as the button's name; "simming"
## stays banned ("Ask before Sim the week", not "Ask before simming").

## Whole words or phrases, any case. Advice ("should", "need to"), engine and software words
## ("modifier", "simulation", "roster"), and verdicts ("best choice").
const WORDS := [
	"should", "recommend", "recommended", "recommends", "need to", "needs to", "consider",
	"probability", "chance of success", "modifier", "modifiers", "simulation", "simming",
	"auto-pick", "projection", "roster", "starter", "starters", "payroll", "best choice",
	"best option", "best pick",
]
## Characters that never reach visible text: a raw meter ("/100": write "%d out of 100"),
## a code separator or name ("|", "_"), and "!" outside the broadcaster's feed.
const MARKS := ["/100", "|", "_"]
const SHOUT := "!"

static var _re: RegEx


static func _words_re() -> RegEx:
	if _re == null:
		var alts: Array = []
		for w in WORDS:
			alts.append(String(w).replace("-", "\\-").replace(" ", "\\s+"))
		_re = RegEx.create_from_string("(?i)(?<![A-Za-z])(" + "|".join(PackedStringArray(alts)) + ")(?![A-Za-z])")
	return _re


## The banned words in `text`, lower case, in the order they appear.
static func words_in(text: String) -> Array:
	var out: Array = []
	for m in _words_re().search_all(text):
		out.append(" ".join(m.get_string(1).to_lower().split(" ", false)))
	return out


## Every banned term in a line of visible text: words, marks, and "!" unless the line is
## the broadcaster's feed (`feed`).
static func check(text: String, feed := false) -> Array:
	var out := words_in(text)
	for m in MARKS:
		if text.contains(m):
			out.append(m)
	if not feed and text.contains(SHOUT):
		out.append(SHOUT)
	return out
