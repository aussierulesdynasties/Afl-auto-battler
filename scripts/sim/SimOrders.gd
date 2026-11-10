class_name SimOrders
extends RefCounted
## "When I sim the week" (row T3.R43, P-66; director bible 43: "the assistant
## follows set lines and stops only for what no line covers"). The standing
## orders the assistant follows each week the coach sims, set once and kept
## with the career (GameState.sim_orders). The game plan is not a line here:
## it is the club's plan, set in Coaching, and every match starts on it.
##   youth      selection: best side, or promised runs for young players
##   questions  how the week's cards are answered, or "ask": Sim the week stops
##              and shows each card for the coach to answer
##   press      who fronts the press after a simmed match
## Each option says what it does for him and what it costs, never which is
## better (bible principle 4). The words for selection and cards are the
## season skip's own (SkipOrders), so the two read the same.

const KEYS := ["youth", "questions", "press"]
const SHORT := {"youth": "Selection", "questions": "The week's questions", "press": "Press conferences"}


static func defaults() -> Dictionary:
	return {"youth": "form", "questions": "usual", "press": "me"}


## The lines in order: {"key", "title", "lead", "options": [{"key", "label",
## "gain", "cost"}]}.
static func questions() -> Array:
	var skip := {}
	for q in SkipOrders.questions("season"):
		skip[str(q["key"])] = q
	var youth: Dictionary = (skip["youth"] as Dictionary).duplicate(true)
	youth["lead"] = "Selection, every week you sim."
	var cards: Dictionary = (skip["questions"] as Dictionary).duplicate(true)
	cards["title"] = "The week's questions"
	cards["lead"] = "The cards waiting when you sim the week."
	(cards["options"] as Array).append({"key": "ask", "label": "Ask me",
			"gain": "Every card is yours to answer: Sim the week stops and shows you the first one waiting.",
			"cost": "A stop before the week is played whenever a card is waiting."})
	var press := {"key": "press", "title": "Press conferences",
		"lead": "The press after a match you simmed.", "options": [
			{"key": "me", "label": "I front the press",
				"gain": "Your answers can lift a player's morale, the board's confidence or a journalist's opinion of you.",
				"cost": "Every answer is a risk: it can cost them as well."},
			{"key": "assistant", "label": "The assistant fronts it",
				"gain": "No answer is given in your name, so nothing is put at risk.",
				"cost": "Nothing is gained either: the question goes by."},
		]}
	return [youth, cards, press]


## The label of answer `key` to line `q`.
static func label(q: String, key: String) -> String:
	return SkipOrders.label(questions(), q, key)


## The cards Sim the week stops for under `orders`: every card still waiting
## when the coach asked to be asked, otherwise none (each other answer covers
## every card). Indices into `cards`.
static func stops(cards: Array, orders: Dictionary) -> Array:
	var out: Array = []
	if str(orders.get("questions", "usual")) != "ask":
		return out
	for i in range(cards.size()):
		if not bool((cards[i] as Dictionary).get("resolved", false)):
			out.append(i)
	return out
