class_name Promises
extends RefCounted
## Every promise you make a player, in one place (relationship overhaul,
## phase 1, director 2026-11-26), and what keeping your word does to how the
## playing group sees you, the senior coach.
##
## Each kind of promise keeps its working state where it always has (so
## selection and auto-pick need no change):
##   "run"        a run of senior games (Backing, p["backed"]; card ops
##                start_backing and back_kid)
##   "game"       a game this week (card op expects_game, p["expects_game"])
##   "dev_games"  his games in a new position once he learns it (card op
##                dev_promise, p["dev_talk"], GameState._dev_owed)
##   "win"        a win promised to the board (card op promise_win,
##                gs.board["promise"]): no player, so no opinion marks
## (no_promise, the honest "it's for depth" answer, is not a promise.)
## This class is the one door they all go through when a promise is made, kept,
## broken or lapses. It keeps:
##   gs.coach_word      the coach's record: {"made", "kept", "broken",
##                      "lapsed", "log": [{"y", "w", "k", "out", "who"}]}
##   gs.coach_standing  {"respect", "authority", "base": [r, a], "log":
##                      [{"y", "w", "r", "a", "why"}], "side": [ids]}: two
##                      scores out of 100 that move with what you actually do.
##                      Backing players and keeping your word builds Respect;
##                      ruthless drops build Authority; a broken promise only
##                      costs Respect. The senior coach's archetype only sets where
##                      they start (and where they settle back to between
##                      seasons), never where they must stay.
##   gs.club_standing   {code: the same shape} for every other club's senior
##                      coach, moved by the same drop rule after every round
##                      (every club gets it, director 2026-11-09). Rival clubs
##                      make no promises, so only drops move theirs for now.
## Saves from before 2026-11-26 start these empty (director: old saves need no
## care). Neither score touches the match: standing is read on the profile, the
## selection preview and (later phases) the Council and factions.
##
## A kept promise leaves a lasting mark on his opinion of you, a broken one a
## permanent one (Trust.change, as it always has, at the call site), and the
## players in his line who watched it get a smaller mark of their own. Marks
## go through Opinion.add, and the player's temperament sizes them and how
## long he holds them (Temperament.scale; a broken promise's permanent cost too,
## broken_trust).

const KINDS := ["run", "game", "dev_games", "win"]

## Both scores are out of 100, and start at 50 before the archetype's lean.
const LOWEST := 0
const HIGHEST := 100
const START := 50
## The senior coach's Philosophical archetype (Archetypes.PHILOSOPHICAL) sets
## the lean: [Respect, Authority]. Each lean sums to zero, so no archetype
## starts better off, only differently.
const ARCH_LEAN := {
	"FATH": [10, -10],
	"HARD": [-10, 10],
	"ANA": [-5, 5],
	"GAMB": [5, -5],
}

## What each moment moves: [Respect, Authority].
const MADE := [1, 0]
const KEPT := {"run": [4, 0], "game": [2, 0], "dev_games": [4, 0], "win": [0, 2]}
## Breaking your word costs Respect, and builds no Authority: hard selection
## and discipline calls build that, a broken promise only costs (director,
## 2026-11-26).
const BROKEN := {"run": [-6, 0], "game": [-4, 0], "dev_games": [-6, 0], "win": [0, -2]}
## Dropping a fit player who played last week: the hard call.
const DROP := [0, 1]
## The most drops that count towards Authority in one round.
const DROP_ROUND_MAX := 2
## Between seasons each score settles this share of the way back to its base.
const SETTLE := 0.25

## The trust a broken promise costs him (the call sites' own constants).
const BROKEN_TRUST := {"run": StoryEngine.BROKEN_RUN_TRUST, "game": StoryEngine.BROKEN_PROMISE_TRUST,
		"dev_games": StoryEngine.BROKEN_PROMISE_TRUST}
## Line-mates who see a promise broken (Opinion "saw_promise_broken").
const WITNESS_MAX := 6
const LOG_KEEP := 12

## What a kept or broken promise is called on the profile.
const KIND_WORDS := {"run": "a run of games", "game": "a game", "dev_games": "games in a new position",
		"win": "a win"}


# ---------------------------------------------------------------------------
# The coach's standing (every club's senior coach, by the same rules)
# ---------------------------------------------------------------------------

## The base [Respect, Authority] for a Philosophical archetype key ("" is level).
static func base_for(arch_p: String) -> Array:
	var lean: Array = ARCH_LEAN.get(arch_p, [0, 0])
	return [START + int(lean[0]), START + int(lean[1])]


## Where a club's standing is kept: yours in gs.coach_standing, every other
## club's in gs.club_standing[code]. "" is yours.
static func _store(gs, club: String) -> Dictionary:
	if club == "" or club == str(gs.my_club):
		if not (gs.coach_standing is Dictionary):
			gs.coach_standing = {}
		return gs.coach_standing
	if not (gs.club_standing is Dictionary):
		gs.club_standing = {}
	if not (gs.club_standing.get(club) is Dictionary):
		gs.club_standing[club] = {}
	return gs.club_standing[club]


## A senior coach's standing, filled in on first use: it starts at his
## archetype's base. Before the archetype is known (no club yet) a level
## reading is shown and nothing is kept, unless `keep` (a move). `club` ""
## is yours.
static func standing(gs, keep := false, club := "") -> Dictionary:
	var code := str(gs.my_club) if club == "" else club
	var s := _store(gs, club)
	if not s.has("respect") or not s.has("authority"):
		var arch := _arch_p(code)
		if arch == "" and not keep:
			return {"respect": START, "authority": START, "base": [START, START], "log": []}
		var base := base_for(arch)
		s["base"] = base
		s["respect"] = int(base[0])
		s["authority"] = int(base[1])
	if not (s.get("log") is Array):
		s["log"] = []
	if not (s.get("base") is Array):
		s["base"] = [START, START]
	return s


static func respect(gs, club := "") -> int:
	return int(standing(gs, false, club)["respect"])


static func authority(gs, club := "") -> int:
	return int(standing(gs, false, club)["authority"])


## Move a standing and keep the reason. Returns [dr, da] actually moved.
static func move(gs, dr: int, da: int, why: String, club := "") -> Array:
	var s := standing(gs, true, club)
	var r0 := int(s["respect"])
	var a0 := int(s["authority"])
	s["respect"] = clampi(r0 + dr, LOWEST, HIGHEST)
	s["authority"] = clampi(a0 + da, LOWEST, HIGHEST)
	var moved := [int(s["respect"]) - r0, int(s["authority"]) - a0]
	if moved[0] == 0 and moved[1] == 0:
		return moved
	var log: Array = s["log"]
	log.append({"y": int(gs.season_year), "w": str(gs.last_label), "r": moved[0], "a": moved[1], "why": why})
	while log.size() > LOG_KEEP:
		log.pop_front()
	return moved


## A standing's reasons, newest first.
static func standing_reasons(gs, club := "") -> Array:
	var log: Array = (standing(gs, false, club)["log"] as Array).duplicate()
	log.reverse()
	return log


## "Respect 58 out of 100. Authority 46 out of 100."
static func standing_words(gs, club := "") -> String:
	return "Respect %d out of 100. Authority %d out of 100." % [respect(gs, club), authority(gs, club)]


## One reason as a profile lists it: "Round 5, 2026. You kept your word to
## Calder on a run of games. Respect +4."
static func reason_text(r: Dictionary) -> String:
	var why := str(r.get("why", "")).strip_edges()
	if why != "" and not why.ends_with("."):
		why += "."
	var bits := []
	if int(r.get("r", 0)) != 0:
		bits.append("Respect %+d." % int(r["r"]))
	if int(r.get("a", 0)) != 0:
		bits.append("Authority %+d." % int(r["a"]))
	return ("%s, %d. %s %s" % [str(r.get("w", "")), int(r.get("y", 0)), why, " ".join(bits)]).strip_edges()


## Between seasons: every club's scores settle SETTLE of the way back to
## their base.
static func season_end(gs) -> void:
	var clubs := [""]
	if gs.club_standing is Dictionary:
		clubs.append_array((gs.club_standing as Dictionary).keys())
	for club in clubs:
		var s := standing(gs, true, str(club))
		var base: Array = s["base"]
		for i in 2:
			var k := "respect" if i == 0 else "authority"
			var gap := int(base[i]) - int(s[k])
			s[k] = int(s[k]) + int(round(gap * SETTLE))
		s.erase("side")


## A new senior coach's archetype is set (or changed): the base follows it,
## and the scores move by the change in lean.
static func rebase(gs, arch_p: String, club := "") -> void:
	var s := standing(gs, true, club)
	var old: Array = s["base"]
	var new := base_for(arch_p)
	s["respect"] = clampi(int(s["respect"]) + int(new[0]) - int(old[0]), LOWEST, HIGHEST)
	s["authority"] = clampi(int(s["authority"]) + int(new[1]) - int(old[1]), LOWEST, HIGHEST)
	s["base"] = new


# ---------------------------------------------------------------------------
# The coach's word
# ---------------------------------------------------------------------------

static func word(gs) -> Dictionary:
	var w = gs.coach_word
	if not (w is Dictionary):
		w = {}
		gs.coach_word = w
	for k in ["made", "kept", "broken", "lapsed"]:
		if not w.has(k):
			w[k] = 0
	if not (w.get("log") is Array):
		w["log"] = []
	return w


## "You have kept 5 of the 7 promises you've seen through." ("" before the first).
static func word_line(gs) -> String:
	var w := word(gs)
	var done := int(w["kept"]) + int(w["broken"])
	if done == 0:
		return ""
	return "You have kept %d of the %d promises you've seen through." % [int(w["kept"]), done]


static func _log_word(gs, p: Dictionary, kind: String, out: String) -> void:
	var w := word(gs)
	w[out] = int(w.get(out, 0)) + 1
	var log: Array = w["log"]
	log.append({"y": int(gs.season_year), "w": str(gs.last_label), "k": kind, "out": out, "who": str(p.get("id", ""))})
	while log.size() > LOG_KEEP:
		log.pop_front()


## A promise is made (a run, a game this week, games in a new position, a win
## for the board: `p` {}). Backing a player builds Respect.
static func made(gs, p: Dictionary, kind: String) -> void:
	_log_word(gs, p, kind, "made")
	if not p.is_empty():
		move(gs, int(MADE[0]), int(MADE[1]), "You backed %s with %s" % [GameDB.player_display_name(p), KIND_WORDS.get(kind, "a promise")])


## A promise is settled: `out` "kept", "broken" or "lapsed". The broken
## promise's sting and permanent trust cost are the call site's (they always
## were); this adds the coach's record, his standing, the kept promise's mark
## on the player and the mark on the players who watched it broken.
static func settle(gs, p: Dictionary, kind: String, out: String) -> void:
	if not (out in ["kept", "broken", "lapsed"]):
		return
	_log_word(gs, p, kind, out)
	var who := GameDB.player_display_name(p) if not p.is_empty() else "the board"
	var what: String = KIND_WORDS.get(kind, "a promise")
	match out:
		"kept":
			var m: Array = KEPT.get(kind, [0, 0])
			move(gs, int(m[0]), int(m[1]), "You kept your word to %s on %s" % [who, what])
			if not p.is_empty():
				_mark_kept(gs, p)
		"broken":
			var m: Array = BROKEN.get(kind, [0, 0])
			move(gs, int(m[0]), int(m[1]), "You broke your word to %s on %s" % [who, what])
			for q in ([] if p.is_empty() else witnesses(gs, p)):
				_opinion_add(gs, q, "saw_promise_broken", "promise_broken")


## The players who saw it: his line-mates on your list, up to WITNESS_MAX.
static func witnesses(gs, p: Dictionary) -> Array:
	var out := []
	var role := str(p.get("role", ""))
	for q in gs.my_list:
		if out.size() >= WITNESS_MAX:
			break
		if str(q.get("id", "")) != str(p.get("id", "")) and str(q.get("role", "")) == role:
			out.append(q)
	return out


static func _mark_kept(gs, p: Dictionary) -> void:
	_opinion_add(gs, p, "promise_kept", "promise_kept")


## What breaking a `kind` promise costs his trust, permanently, sized by his
## temperament ("promise_broken"): what the call sites charge and every
## preview and card shows.
static func broken_trust(p: Dictionary, kind: String) -> int:
	var t := int(BROKEN_TRUST.get(kind, 0))
	if t == 0:
		return 0
	return clampi(roundi(float(t) * Temperament.scale(p, "promise_broken")), -Trust.STEP_MAX, Trust.STEP_MAX)


# ---------------------------------------------------------------------------
# What a player is owed now, and what dropping him would do
# ---------------------------------------------------------------------------

## His promises under way: [{"kind", "text", "weeks_left"}], a run first.
static func of(gs, player_id: String) -> Array:
	var p: Dictionary = gs.list_player(player_id)
	if p.is_empty():
		return []
	var out := []
	var run := Backing.current(p)
	if not run.is_empty():
		var games := int(run.get("games", Backing.RUN_GAMES))
		var played := int(run.get("played", 0))
		out.append({"kind": "run", "weeks_left": maxi(0, games - played),
				"text": "Promised a run of %s games: game %s next." % [MatchNotes.count_word(games), MatchNotes.count_word(played + 1)]})
	var dev: Dictionary = gs._dev_owed(p)
	if not dev.is_empty():
		var left := GameState.DEV_PROMISE_GAMES
		if str(dev.get("state", "")) == "on" and str(gs.role_trial.get("id", "")) == player_id:
			left = int(gs.role_trial.get("left", left))
		out.append({"kind": "dev_games", "weeks_left": left,
				"text": "Promised %s games in his new position." % MatchNotes.count_word(GameState.DEV_PROMISE_GAMES)})
	# A run or the new-position games set this week's expectation themselves:
	# only a card's game stands on its own.
	if p.has("expects_game") and run.is_empty() and dev.is_empty():
		out.append({"kind": "game", "weeks_left": 1, "text": "Promised a game this week."})
	return out


## What leaving him out of this week's side would do, read only:
## {"respect", "authority", "broken": [texts], "opinion": his shown opinion's
## move}. A player who is not in the side, or cannot play, breaks nothing.
static func preview_drop(gs, player_id: String) -> Dictionary:
	var out := {"respect": 0, "authority": 0, "broken": [], "opinion": 0}
	var p: Dictionary = gs.list_player(player_id)
	if p.is_empty() or not Ratings.available(p):
		return out
	var s := standing(gs)
	var r := int(s["respect"])
	var a := int(s["authority"])
	var t := Trust.value(gs.relations, Trust.player_key(player_id))
	var t0 := t
	for pr in of(gs, player_id):
		var k := str(pr["kind"])
		var m: Array = BROKEN.get(k, [0, 0])
		r = clampi(r + int(m[0]), LOWEST, HIGHEST)
		a = clampi(a + int(m[1]), LOWEST, HIGHEST)
		(out["broken"] as Array).append(str(pr["text"]))
		t = clampi(t + broken_trust(p, k), Trust.LOWEST, Trust.HIGHEST)
	if (s.get("side", []) as Array).has(player_id):
		a = clampi(a + int(DROP[1]), LOWEST, HIGHEST)
	out["respect"] = r - int(s["respect"])
	out["authority"] = a - int(s["authority"])
	out["opinion"] = Trust.opinion(t) - Trust.opinion(t0)
	return out


## After a match, for any club (yours when `club` is ""): a fit player who
## played its last match and not this one was dropped (yours only in a side
## you named). Each counts towards its
## senior coach's Authority, up to DROP_ROUND_MAX a round, the same rule at
## every club. `played` is {id: true} for who took the field; `unavailable`
## the players who could not have. Then this side is remembered for next week.
static func after_match(gs, played: Dictionary, unavailable := {}, club := "") -> void:
	var s := standing(gs, true, club)
	var list: Array = gs.my_list
	if club != "" and club != str(gs.my_club) and gs.season != null:
		list = gs.season.lists.get(club, [])
	var by_id := {}
	for q in list:
		by_id[str(q.get("id", ""))] = q
	var last: Array = s.get("side", [])
	# Your side on Auto-pick is the match-day staff's pick, not your call: it
	# drops nobody on your say-so (every rival coach names his own side).
	var mine := club == "" or club == str(gs.my_club)
	if mine and gs.my_selection().is_empty():
		last = []
	var drops := 0
	for id in last:
		if played.has(str(id)) or unavailable.has(str(id)) or not by_id.has(str(id)):
			continue
		var q: Dictionary = by_id[str(id)]
		if int(q.get("injury_weeks", 0)) > 0 or not Backing.fit(q):
			continue
		drops += 1
	drops = mini(drops, DROP_ROUND_MAX)
	if drops > 0:
		move(gs, int(DROP[0]) * drops, int(DROP[1]) * drops,
				"Dropped %s from the side" % ("a player" if drops == 1 else "%s players" % MatchNotes.count_word(drops)), club)
	s["side"] = played.keys().map(func(x): return str(x))


# ---------------------------------------------------------------------------
# Marks on his opinion
# ---------------------------------------------------------------------------

static func _arch_p(code: String) -> String:
	if code == "":
		return ""
	return str(CoachEffects.arch_of(code)[1])


## A mark on his opinion (Opinion.add, data/relations/modifiers.json), sized by
## his temperament's `lever` and fading at his pace ("decay").
static func _opinion_add(gs, p: Dictionary, mark: String, lever: String) -> void:
	Opinion.add(gs.relations, Opinion.player_key(str(p.get("id", ""))), mark, int(gs.season_year),
			str(gs.last_label), str(gs.my_club), Temperament.scale(p, lever), "promise", Temperament.scale(p, "decay"))
