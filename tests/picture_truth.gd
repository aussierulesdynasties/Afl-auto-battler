extends RefCounted
## The measures of tests/run_picture_truth_tests.gd (T8.85, P-76), kept apart
## from the match they are run on so each can be shown a made-up fault. Every
## one returns "" when the picture is true and says what is wrong otherwise.

const MODES := ["held", "flight", "carry", "loose", "dead"]
## A held ball rides this far in front of its holder (MatchDirector._update_ball).
const HELD_REACH := 0.6
## A ball above this height that neither moves nor drops is hanging in the air.
const HOVER_HEIGHT := 0.3
## The longest a ball lies still out of hands, in match seconds, before somebody
## has it (MatchDirector.COLLECT_LIMIT; the seeded match's longest is 3.5).
const LYING_LIMIT := 6.0
## The ball may leave the oval by this (the seeded match never has it outside).
const OVER_FENCE := 6.0
## The hardest kick leaves the boot at about this, in metres a match second.
const KICK_SPEED := 62.0
## A player may step this far over the boundary line.
const OVER_LINE := 4.0


## The longest step any point took between two frames.
static func fastest(prev: PackedVector2Array, now: PackedVector2Array) -> float:
	var most := 0.0
	for i in range(mini(prev.size(), now.size())):
		most = maxf(most, prev[i].distance_to(now[i]))
	return most


## No point moved more than `limit` metres between two frames (`scale` is the
## points' units per metre: 1 on the ground, pixels per metre on the screen).
static func speed_fault(prev: PackedVector2Array, now: PackedVector2Array, scale: float, limit: float) -> String:
	if prev.size() != now.size():
		return "%d discs became %d" % [prev.size(), now.size()]
	for i in range(now.size()):
		if not now[i].is_finite():
			return "disc %d has no place" % i
		var step := prev[i].distance_to(now[i]) / scale
		if step > limit * 1.001:
			return "disc %d moved %.2f m in a tick, the most a footballer covers is %.2f m" % [i, step, limit]
	return ""


## The ball is out of hands and has not moved since the last frame.
static func lying(ball: Dictionary, prev: Dictionary) -> bool:
	if str(ball.get("mode", "")) == "held" or str(prev.get("mode", "")) == "held":
		return false
	return (ball.get("pos", Vector2.ZERO) as Vector2).distance_to(prev.get("pos", Vector2.INF)) < 0.01


## The ball is in a player's hands, or on its way somewhere, or on the ground
## for no longer than it takes a player to get to it (`still`, match seconds).
static func ball_fault(ball: Dictionary, prev: Dictionary, tokens: Array, _h: float, still: float) -> String:
	var mode := str(ball.get("mode", ""))
	if not MODES.has(mode):
		return "the ball is '%s'" % mode
	var pos: Vector2 = ball.get("pos", Vector2.INF)
	var height := float(ball.get("h", 0.0))
	if not pos.is_finite() or is_nan(height) or is_inf(height):
		return "the ball has no place (%s, height %s)" % [str(pos), str(height)]
	var over := pos.distance_to(MatchMotion.clamp_to_oval(pos, 0.0))
	if over > OVER_FENCE:
		return "the ball is %.1f m outside the oval" % over
	if height < -0.01:
		return "the ball is %.2f m under the ground" % -height
	if mode == "held":
		var holder := int(ball.get("holder", -1))
		if holder < 0 or holder >= tokens.size():
			return "the ball is held by nobody (holder %d)" % holder
		var gap := pos.distance_to(tokens[holder]["pos"])
		if gap > HELD_REACH + 0.05:
			return "the held ball is %.2f m from its holder" % gap
		return ""
	if not prev.is_empty() and lying(ball, prev) and height > HOVER_HEIGHT \
			and absf(height - float(prev.get("h", 0.0))) < 0.001:
		return "the ball hangs %.2f m up without moving (%s)" % [height, mode]
	if still > LYING_LIMIT:
		return "the ball has lain still for %.1f match seconds with nobody on it (%s)" % [still, mode]
	return ""


## Thirty-six discs, 18 a side, each drawn once, on the screen, on the ground,
## and no two men of a side in the same number.
static func disc_fault(tokens: Array, discs: PackedVector2Array, order: Array, view: Rect2, radius: float) -> String:
	if tokens.size() != 36 or discs.size() != 36:
		return "%d players and %d discs, not 36" % [tokens.size(), discs.size()]
	var sides := [0, 0]
	var nums := [{}, {}]
	for i in range(36):
		var t: Dictionary = tokens[i]
		var side := int(t.get("side", -1))
		if side < 0 or side > 1:
			return "disc %d plays for nobody" % i
		sides[side] += 1
		var num := int(t.get("num", 0))
		if nums[side].has(num):
			return "two of side %d wear number %d" % [side, num]
		nums[side][num] = true
		var pos: Vector2 = t.get("pos", Vector2.INF)
		if not pos.is_finite() or not discs[i].is_finite():
			return "disc %d has no place" % i
		var over := pos.distance_to(MatchMotion.clamp_to_oval(pos, 0.0))
		if over > OVER_LINE:
			return "player %d is %.1f m outside the oval" % [i, over]
		if not view.grow(radius).has_point(discs[i]):
			return "disc %d is drawn off the screen at %s" % [i, str(discs[i])]
	if sides[0] != 18 or sides[1] != 18:
		return "%d against %d, not 18 a side" % [sides[0], sides[1]]
	var seen := {}
	for id in order:
		seen[int(id)] = true
	if order.size() != 36 or seen.size() != 36:
		return "%d discs are drawn in %d places" % [seen.size(), order.size()]
	return ""


static func scoreline(goals: int, behinds: int) -> String:
	return "%d.%d (%d)" % [goals, behinds, goals * 6 + behinds]


## The score counted from the feed's events (`goals`, `behinds`), the match's
## own running score (`engine_*`) and the two scoreboard texts all agree.
static func score_fault(goals: Array, behinds: Array, engine_goals: Array, engine_behinds: Array,
		home_text: String, away_text: String) -> String:
	for side in range(2):
		if int(engine_goals[side]) != int(goals[side]) or int(engine_behinds[side]) != int(behinds[side]):
			return "the match has side %d on %d.%d, the events played add up to %d.%d" % [side,
					int(engine_goals[side]), int(engine_behinds[side]), int(goals[side]), int(behinds[side])]
	if home_text != scoreline(goals[0], behinds[0]):
		return "the scoreboard shows the home side '%s', the events add up to %s" % [home_text, scoreline(goals[0], behinds[0])]
	if away_text != scoreline(goals[1], behinds[1]):
		return "the scoreboard shows the away side '%s', the events add up to %s" % [away_text, scoreline(goals[1], behinds[1])]
	return ""


## A goal's line in the feed carries both scores, the home side's first.
static func goal_row_fault(text: String, goals: Array, behinds: Array) -> String:
	var home := scoreline(goals[0], behinds[0])
	var away := scoreline(goals[1], behinds[1])
	var at := text.find(home)
	if at < 0 or text.find(away, at + home.length()) < 0:
		return "'%s' should read %s then %s" % [text, home, away]
	return ""


## Every word a row of the feed shows.
static func text_of(node: Node) -> String:
	var out := ""
	if node is RichTextLabel:
		out = (node as RichTextLabel).get_parsed_text()
	elif node is Label:
		out = (node as Label).text
	for c in node.get_children():
		out += " " + text_of(c)
	return out


## The body whose strip this is, or "" when no body in the sheet has that move.
static func _body_with(anim: String, facing: String, info: Dictionary) -> String:
	for body in VignetteFigures.BODIES:
		if VignetteFigures.has(body, anim, facing) and VignetteFigures.strip(body, anim, facing) == info:
			return str(body)
	return ""


static func _in_sheet(info: Dictionary, frame: int) -> bool:
	var sheet := Rect2(Vector2.ZERO, Vector2(VignetteFigures.SHEET_SIZE))
	var src := VignetteFigures.source(info, frame)
	return src.size.x > 0.0 and src.size.y > 0.0 and sheet.encloses(src)


## One figure a scene drew (StoppageVignette.frame_log): the move it asked for
## is in the sheet, the strip it drew is that move's, and the frame is one of
## the move's own (a frame past the end holds on the last without a word).
static func frame_fault(e: Dictionary) -> String:
	var anim := str(e.get("anim", ""))
	var facing := str(e.get("facing", ""))
	var name := "%s %s" % [anim, facing]
	if not e.has("info"):
		return "%s: the strip drawn is not recorded" % name
	var info: Dictionary = e["info"]
	if _body_with(anim, facing, info) == "":
		return "%s is drawn from a strip that is not that move's" % name
	var wanted := int(e.get("wanted", -1))
	if wanted < 0 or wanted >= int(info["frames"]):
		return "%s asks for frame %d of %d" % [name, wanted, int(info["frames"])]
	if not _in_sheet(info, wanted):
		return "%s frame %d lies outside the sheet" % [name, wanted]
	return ""


## One figure on the ground view (PitchView._figure_slots).
static func slot_fault(s: Dictionary) -> String:
	var anim := str(s.get("anim", ""))
	var facing := str(s.get("facing", ""))
	var name := "%s %s" % [anim, facing]
	if bool(s.get("fallback", true)):
		return "%s stands in for a move the sheet lacks" % name
	var info: Dictionary = s.get("info", {})
	if info.is_empty() or not VignetteFigures.has("average", anim, facing) \
			or VignetteFigures.strip("average", anim, facing) != info:
		return "%s is drawn from a strip that is not that move's" % name
	var frame := int(s.get("frame", -1))
	if frame < 0 or frame >= int(info["frames"]) or not _in_sheet(info, frame):
		return "%s shows frame %d of %d" % [name, frame, int(info["frames"])]
	return ""


## A side's guernsey is the design its club declares, and the sheet holds it.
static func kit_fault(code: String, kit: Dictionary, declared: String, designs: Array) -> String:
	if not designs.has(declared):
		return "%s declares '%s', which the design sheet does not hold" % [code, declared]
	if str(kit.get("design", "")) != declared:
		return "%s wears '%s', the club's guernsey is '%s'" % [code, str(kit.get("design", "")), declared]
	return ""
