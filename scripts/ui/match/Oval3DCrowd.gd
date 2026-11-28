class_name Oval3DCrowd
extends Node3D
## The 3D view's crowd (row 202 step 2c; director 2026-11-17, Bible 2.92): a stepped concrete
## stand all the way round with a bench on every row and a supporter on most seats, each in his
## own club's colours. The mix: within MIX_D of the camera each supporter is a 3D person
## (Oval3DCrowdSet's baked bodies, seated idle and goal cheer); beyond it he is a card cut from
## the same bodies, turned to face the camera. When a side kicks a goal its supporters rise.
## Looks only: it reads nothing from the match but the time and who kicked the goal.
## Brought up to standard (2026-11-21, the MCG crowd): each club's cheer squad in the front rows
## behind a goal, the away supporters gathered toward their end in bays of their own, the members'
## reserve in collared shirts and jackets; a winter crowd dressed each his own way
## (Oval3DCrowdDress, oval3d_crowd_dress.gdshaderinc), each sitting and moving at his own pace;
## and it reacts to more than goals: a near miss, a big mark or tackle, the final siren (react).

const CROWD_SET := "res://assets/oval3d/crowd_set.res"
const ROWS := 42
const SEAT := 0.55           # m between neighbours along a row
const AISLE_EVERY := 28      # seats between aisles (an aisle is two seats wide)
const EMPTY := 0.08          # share of seats left empty when no crowd figure is given
## How a ground fills (_taken): each seat's draw, from its height up the stand (FILL_HIGH from
## the front row to the back), the wing over the ends (FILL_WING), the home end over the away
## (FILL_HOME), its bay's own draw (FILL_BAY, FILL_BAY_TOP in the upper tier, so whole bays up
## there close), the members' reserve (FILL_MEMBERS) and each seat's own chance (FILL_SEAT).
const FILL_HIGH := 1.0
const FILL_WING := 0.35
const FILL_HOME := 0.08
const FILL_BAY := 0.25
const FILL_BAY_TOP := 0.8
const FILL_MEMBERS := 0.6
const FILL_SEAT := 0.45
const NEUTRAL := 0.08        # share of supporters in neither club's colours (general stands)
const SECTORS := 96          # chunks round the ground (each also split front rows / back rows)
const SEAT_TIERS := 3        # a real ground's chunks: each sector also split low / middle / high
const MIX_D := 55.0          # m from the camera: 3D people nearer, cards beyond
const BASE_Y := 1.2          # m: the front row's step, level with the fence top
## The bench: SEAT_H high, from SEAT_F to SEAT_B m back from the row's front edge; the
## supporter's origin PERSON_D m back; a card stands CARD_FWD m forward of it (a seated body's
## knees reach forward of its origin). Chosen on the 2c board (2026-11-17).
const SEAT_H := 0.42
const SEAT_F := 0.40
const SEAT_B := 0.80
const PERSON_D := 0.65
const CARD_FWD := 0.5

## The reactions (react): the cheer up out of the seat, both hands to the head, a fist pump.
enum { CHEER, HEAD, PUMP }
## The guernsey designs the crowd draws (the shaders' numbers), from GameDB.club_guernsey's design;
## any other is drawn plain.
const DESIGNS := {"plain": 0, "stripes": 1, "hoops": 2, "twohoops": 2, "lowhoops": 5, "sash": 3,
		"yoke": 4, "shoulders": 4, "chevron": 4, "chevrons": 4, "wings": 4, "band": 5, "tiers": 2,
		"sides": 6, "panels": 6, "giants": 4}
## Where the crowd sits, in the ground's own frame (x along the ground, toward the home end):
## the cheer squads take the front rows behind each goal, SQUAD_W either side of its line and
## the lowest SQUAD_LOW of the seats; the away supporters lean toward their end (AWAY_BASE of a
## bay, up to AWAY_BASE + AWAY_END behind their goal, falling off over AWAY_SPREAD rad), with a few
## bays (AWAY_BAYS) of their own elsewhere.
const SQUAD_W := 0.17
const SQUAD_LOW := 0.07
const AWAY_BASE := 0.14
const AWAY_END := 0.5
const AWAY_SPREAD := 0.55
const AWAY_BAYS := 0.07
## A ground's members' reserve, as degrees round its own frame (0 the home end, 90 the far wing
## from the main camera... the field's +z), where most wear their own clothes. The MCC Members'
## Reserve is on the MCG's north-west, from the City end round to the wing.
const MEMBERS := {"mcg": [-168.0, -110.0]}
## Zones in the shaders' side number (side + 4 x zone).
const ZONE_STAND := 0
const ZONE_SQUAD := 1
const ZONE_MEMBERS := 2

var supporters := 0
## How many of each kind sit where (for the tests and the QA sheet): home, away, nobody's, and
## in the cheer squads and the members' reserve.
var census := {"home": 0, "away": 0, "neutral": 0, "squad": 0, "members": 0, "seats": 0, "taken": 0}
## The share of the seats taken, set before build (MatchAttendance.fill: the match's crowd over
## the ground's capacity).
var fill := 1.0 - EMPTY
var _react: Array = []        # the last four reactions: Vector4(when, side, kind, share)
## m from the camera within which a supporter is a 3D person (Oval3DQuality's people_d; MIX_D,
## the ruled mix, at High). 0: every supporter a card, and no 3D people are built at all.
var mix_d := MIX_D
var _people_mats: Array = []
var _card_mat: ShaderMaterial
var _meshes: Array = []      # each body dressed (Oval3DCrowdDress): its parts in UV.y
var _chunks: Array = []      # [{people: [MultiMeshInstance3D per body], cards: MultiMeshInstance3D}]


## The stand round an ellipse a x b m (the fence line), STAND_DEPTH deep, rising to rise_to m,
## and its supporters. home and away are each club's two colours (GameDB.club_colours); home_g
## and away_g each club's guernsey (GameDB.club_guernsey), {} for plain in its first colour.
func build(a: float, b: float, depth: float, rise_to: float, home: Array, away: Array,
		home_g := {}, away_g := {}) -> void:
	var cs := crowd_set()
	var pitch := depth / ROWS
	var rise := (rise_to - BASE_Y) / ROWS
	_terrace(a, b, pitch, rise)
	if cs == null:
		return
	_materials(cs, home, away, home_g, away_g)
	_seat(cs, a, b, pitch, rise)


## A real ground's crowd (row 202 2b/2c): a supporter on most of the model's own seats, the same
## mix as the stand (3D people within MIX_D, cards beyond), and the same colours and cheer.
## seats are the ground's seat transforms (each seat's origin and turn, in this node's space);
## tmpl the seat's triangles (seat_tmpl.bin), from which sitting_spot finds where he sits.
## to_field takes this node's space to the ground's (x along it, toward the home end), where the
## cheer squads, the away end and slug's members' reserve (MEMBERS) are placed.
func build_on_seats(seats: Array, tmpl: PackedVector3Array, home: Array, away: Array,
		home_g := {}, away_g := {}, to_field := Transform3D.IDENTITY, slug := "") -> void:
	var cs := crowd_set()
	if cs == null:
		return
	_materials(cs, home, away, home_g, away_g)
	var spot := sitting_spot(tmpl)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	var lay := _layout(rng, seats.map(func(t: Transform3D) -> Vector3: return to_field * (t * spot).origin), slug)
	# Tiers by height: the lowest third of the seats, the middle and the top each draw apart, so
	# a near chunk is never a strip from the fence to the roof.
	var ys := PackedFloat32Array()
	for t: Transform3D in seats:
		ys.append(t.origin.y)
	ys.sort()
	var cuts := [ys[ys.size() / 3], ys[ys.size() * 2 / 3]] if ys.size() > 2 else [INF, INF]
	var per := []
	for i in range(SECTORS * SEAT_TIERS):
		per.append([])
	var taken := _taken(rng, seats.map(func(t: Transform3D) -> Vector3: return to_field * (t * spot).origin), lay)
	for si in range(seats.size()):
		if not taken[si]:
			continue
		var t: Transform3D = seats[si]
		var at := t * spot
		var th := fposmod(atan2(at.origin.z, at.origin.x), TAU)
		var sector := int(th / TAU * SECTORS) % SECTORS
		var tier := 0 if at.origin.y < cuts[0] else (1 if at.origin.y < cuts[1] else 2)
		per[sector * SEAT_TIERS + tier].append(_supporter(cs, rng, at, _side_at(lay, rng, to_field * at.origin)))
	_chunked(cs, per)


## Where each kind of supporter sits on this ground (_side_at reads it): pos are the seats in the
## ground's frame. The cheer squads' rows are the lowest SQUAD_LOW of the seats; each bay's own
## lean (a few bays of away supporters away from their end, the rest a little either way).
func _layout(rng: RandomNumberGenerator, pos: Array, slug: String) -> Dictionary:
	var ys := PackedFloat32Array()
	for p: Vector3 in pos:
		ys.append(p.y)
	ys.sort()
	var low := ys[int(ys.size() * SQUAD_LOW)] if ys.size() > 0 else 0.0
	var bays := []
	for i in range(SECTORS * SEAT_TIERS):
		bays.append(AWAY_END * 0.7 if rng.randf() < AWAY_BAYS else rng.randf_range(-0.08, 0.08))
	var members: Array = MEMBERS.get(slug, [])
	return {"low": low, "bays": bays, "members": [deg_to_rad(members[0]), deg_to_rad(members[1])] if members.size() == 2 else [],
			"y0": ys[0] if ys.size() > 0 else 0.0, "y1": ys[ys.size() - 1] if ys.size() > 0 else 1.0}


## Which seats are taken (pos: each seat in the ground's frame), so that fill of them are: the
## crowd fills a ground the way a real one does. The cheer squads' rows are always full and the
## members' reserve fills first; then the lower rows before the upper ones, the wings before the
## pockets and ends, and the home end a touch before the away end. The upper tier empties in whole
## bays (a closed section), the rest in scattered seats. Every seat scores its draw on all of that
## and the best-scored fill of them are taken, so the share is exact.
func _taken(rng: RandomNumberGenerator, pos: Array, lay: Dictionary) -> Array:
	var bays := PackedFloat32Array()
	for i in range(SECTORS * SEAT_TIERS):
		bays.append(rng.randf_range(-1.0, 1.0))
	var y0: float = lay["y0"]
	var span := maxf(0.01, float(lay["y1"]) - y0)
	var m: Array = lay["members"]
	var scores := PackedFloat32Array()
	scores.resize(pos.size())
	for i in range(pos.size()):
		var p: Vector3 = pos[i]
		var th := atan2(p.z, p.x)
		var h := clampf((p.y - y0) / span, 0.0, 1.0)
		var tier := clampi(int(h * SEAT_TIERS), 0, SEAT_TIERS - 1)
		var sector := int(fposmod(th, TAU) / TAU * SECTORS) % SECTORS
		var sc := -FILL_HIGH * h + FILL_WING * absf(sin(th)) + FILL_HOME * cos(th) \
				+ bays[sector * SEAT_TIERS + tier] * (FILL_BAY_TOP if tier == SEAT_TIERS - 1 else FILL_BAY) \
				+ rng.randf() * FILL_SEAT
		if p.y <= float(lay["low"]) and (absf(th) < SQUAD_W or absf(wrapf(th - PI, -PI, PI)) < SQUAD_W):
			sc += 100.0
		elif m.size() == 2 and th >= float(m[0]) and th <= float(m[1]):
			sc += FILL_MEMBERS
		scores[i] = sc
	var sorted := scores.duplicate()
	sorted.sort()
	var want := clampi(int(round(clampf(fill, 0.0, 1.0) * pos.size())), 0, pos.size())
	var cut := sorted[pos.size() - want] if want > 0 and want < pos.size() else (-INF if want >= pos.size() else INF)
	var out := []
	out.resize(pos.size())
	for i in range(pos.size()):
		out[i] = scores[i] >= cut
	census["seats"] = pos.size()
	census["taken"] = out.count(true)
	return out


## A supporter's side and zone at p (the ground's frame) as the shaders read it (side + 4 x zone):
## the home cheer squad behind the home goal (+x), the away squad behind the other; in the members'
## reserve half wear nobody's colours; elsewhere the away supporters lean toward their end and
## gather in bays, friends sitting together (a 2 m patch leans one way).
func _side_at(lay: Dictionary, rng: RandomNumberGenerator, p: Vector3) -> float:
	var th := atan2(p.z, p.x)
	var to_away := absf(wrapf(th - PI, -PI, PI))
	var to_home := absf(th)
	if p.y <= float(lay["low"]):
		if to_home < SQUAD_W:
			census["squad"] += 1
			census["home"] += 1
			return 0.0 + 4.0 * ZONE_SQUAD
		if to_away < SQUAD_W:
			census["squad"] += 1
			census["away"] += 1
			return 1.0 + 4.0 * ZONE_SQUAD
	var zone := ZONE_STAND
	var neutral := NEUTRAL
	var m: Array = lay["members"]
	if m.size() == 2 and th >= float(m[0]) and th <= float(m[1]):
		zone = ZONE_MEMBERS
		neutral = 0.5
		census["members"] += 1
	if rng.randf() < neutral:
		census["neutral"] += 1
		return 0.5 + 4.0 * zone
	var sector := int(fposmod(th, TAU) / TAU * SECTORS) % SECTORS
	var y0: float = lay["y0"]
	var tier := clampi(int((p.y - y0) / maxf(0.01, float(lay["y1"]) - y0) * SEAT_TIERS), 0, SEAT_TIERS - 1)
	var away := AWAY_BASE + AWAY_END * exp(-to_away * to_away / (2.0 * AWAY_SPREAD * AWAY_SPREAD)) \
			+ float(lay["bays"][sector * SEAT_TIERS + tier])
	away += (_patch(Vector2(p.x, p.z) / 2.0 + Vector2(p.y, 0.0)) - 0.5) * 0.5
	if rng.randf() < clampf(away, 0.02, 0.95):
		census["away"] += 1
		return 1.0 + 4.0 * zone
	census["home"] += 1
	return 0.0 + 4.0 * zone


## A steady number 0-1 for each 2 m patch of seats (friends who came together).
static func _patch(c: Vector2) -> float:
	var k := Vector2(floorf(c.x), floorf(c.y))
	return fposmod(sin(k.x * 12.9898 + k.y * 78.233) * 43758.5453, 1.0)


## The baked bodies, or null, with one error that names the fix, when the file is not in place. It
## lives in the private assets repo since 2026-11-28 (#2321, docs/EPIC_ASSETS.md), so a checkout
## that pulled main without running tools/epic_assets.sh fetch has lost it; before this, every
## supporter then failed on a script error ("bodies" on a null instance, line 291) and the
## stand was left half built.
static func crowd_set() -> Oval3DCrowdSet:
	var cs: Oval3DCrowdSet = load(CROWD_SET) if ResourceLoader.exists(CROWD_SET) else null
	if cs == null:
		push_error("No crowd is drawn: %s is not in place. Run tools/epic_assets.sh fetch (docs/EPIC_ASSETS.md)." % CROWD_SET)
	return cs


## Where a supporter sits on a seat, in the seat's own space, from its triangles: his origin on
## the floor under the seat (its lowest point), PERSON_D - SEAT_F - (SEAT_B - SEAT_F) / 2 behind
## the pan's middle as on the stand, facing out over the pan, away from the backrest.
static func sitting_spot(tmpl: PackedVector3Array) -> Transform3D:
	var lo := INF
	var hi := -INF
	for v in tmpl:
		lo = minf(lo, v.y)
		hi = maxf(hi, v.y)
	# The pan: the points halfway between the floor and the backrest's top; the backrest: the
	# points at its top. Out over the pan, away from the backrest, is the way he faces.
	var pan := Vector3.ZERO
	var n_pan := 0
	var back := Vector3.ZERO
	var n_back := 0
	var pan_y := lo + (hi - lo) * 0.5
	for v in tmpl:
		if absf(v.y - pan_y) < (hi - lo) * 0.06:
			pan += v
			n_pan += 1
		elif v.y > hi - (hi - lo) * 0.06:
			back += v
			n_back += 1
	pan /= maxf(1.0, float(n_pan))
	back /= maxf(1.0, float(n_back))
	var front := Vector3(pan.x - back.x, 0.0, pan.z - back.z)
	front = front.normalized() if front.length() > 0.001 else Vector3.BACK
	# Front to back, the pan's middle is halfway between its front edge and its back edge.
	var near := INF
	var far := -INF
	for v in tmpl:
		if absf(v.y - pan_y) < (hi - lo) * 0.06:
			near = minf(near, v.dot(front))
			far = maxf(far, v.dot(front))
	if near < far:
		pan += front * ((near + far) * 0.5 - pan.dot(front))
	var behind := PERSON_D - (SEAT_F + SEAT_B) * 0.5
	var origin := Vector3(pan.x, lo, pan.z) - front * behind
	# The bodies face +Z (the stand turns them with looking_at the way out, -Z).
	return Transform3D(Basis.looking_at(-front, Vector3.UP), origin)


func _materials(cs: Oval3DCrowdSet, home: Array, away: Array, home_g := {}, away_g := {}) -> void:
	_meshes.clear()
	var necks := PackedFloat32Array()
	var legs := PackedFloat32Array()
	var waists := PackedFloat32Array()
	var kids := float(cs.bodies.size())
	for bi in range(cs.bodies.size()):
		var body: Dictionary = cs.bodies[bi]
		var dressed := Oval3DCrowdDress.dress(body)
		var child := str(body.get("name", "")) in ["boy", "girl"]
		if child:
			kids = minf(kids, float(bi))
		_meshes.append(dressed["mesh"])
		necks.append(float(dressed["neck"]))
		legs.append(float(dressed["legs"]))
		waists.append((dressed["torso"] as Vector2).x)
		var pm := ShaderMaterial.new()
		pm.shader = preload("res://scripts/ui/match/oval3d_crowd_people.gdshader")
		pm.set_shader_parameter("pos_tex", body["pos_tex"])
		pm.set_shader_parameter("nrm_tex", body["nrm_tex"])
		pm.set_shader_parameter("fps", float(body["fps"]))
		pm.set_shader_parameter("idle0", body["idle"])
		pm.set_shader_parameter("n_idle", 1)
		pm.set_shader_parameter("cheer", body["cheer"])
		pm.set_shader_parameter("head_clip", dressed["head"])
		pm.set_shader_parameter("pump_clip", dressed["pump"])
		pm.set_shader_parameter("react_len", Vector3(cs.cheer_s + 1.1, 2.6,
				float((dressed["pump"] as Vector2i).y) / float(body["fps"])))
		pm.set_shader_parameter("torso", dressed["torso"])
		pm.set_shader_parameter("child", child)
		_colours(pm, home, away, home_g, away_g)
		_people_mats.append(pm)
	_card_mat = ShaderMaterial.new()
	_card_mat.shader = preload("res://scripts/ui/match/oval3d_crowd_card.gdshader")
	_card_mat.set_shader_parameter("atlas", cs.atlas)
	_card_mat.set_shader_parameter("bodies", float(cs.bodies.size()))
	_card_mat.set_shader_parameter("card_w", cs.card_w)
	_card_mat.set_shader_parameter("card_h", cs.card_h)
	_card_mat.set_shader_parameter("card_x0", cs.card_x0)
	_card_mat.set_shader_parameter("card_y0", cs.card_y0)
	_card_mat.set_shader_parameter("card_fwd", CARD_FWD)
	# The atlas's own light averages about three-quarters on the lit front; the stand lights it again.
	_card_mat.set_shader_parameter("shade_lift", 1.0 / 0.75)
	_card_mat.set_shader_parameter("cheer_dur", cs.cheer_s)
	_card_mat.set_shader_parameter("cheer_len", cs.cheer_s + 1.0)
	_card_mat.set_shader_parameter("react_cheer", cs.cheer_s + 1.1)
	_card_mat.set_shader_parameter("neck_y", necks)
	_card_mat.set_shader_parameter("legs_y", legs)
	_card_mat.set_shader_parameter("torso_lo", waists)
	_card_mat.set_shader_parameter("kids_from", kids)
	_colours(_card_mat, home, away, home_g, away_g)
	_react.clear()
	_push_react()


## The match clock (s), which every supporter's idle and cheer run on.
func set_now(t: float) -> void:
	for m: ShaderMaterial in _people_mats + ([_card_mat] if _card_mat else []):
		m.set_shader_parameter("now", t)


## A goal at time t (s): side 0 (home) or 1 (away)'s supporters rise, most of them, each a
## beat apart; a few on the other side put their hands to their heads.
func cheer(side: int, t: float) -> void:
	react(CHEER, side, t, 0.9)
	react(HEAD, 1 - side, t, 0.2)


## The crowd reacts at time t (s): share (0-1) of side's supporters (0 home, 1 away) do kind
## (CHEER, HEAD or PUMP), each a beat apart. The last four reactions are kept, so one that
## follows another before it has finished plays for the other side too.
func react(kind: int, side: int, t: float, share: float) -> void:
	_react.append(Vector4(t, float(side), float(kind), share))
	while _react.size() > 4:
		_react.pop_front()
	_push_react()


## Every moment of the match the crowd reacts to (Oval3D passes each event as the director shows
## it): a goal (the scorers' supporters rise, a few of the others hold their heads); a behind (the
## kickers' supporters hold their heads at the near miss); a contested mark or an intercept, and a
## tackle (a few fist pumps); the final siren (the winners rise, some of the losers hold their heads).
func on_event(ev: Dictionary, t: float) -> void:
	var side := int(ev.get("side", -1))
	match str(ev.get("kind", "")):
		"goal":
			cheer(side, t)
		"behind":
			react(HEAD, side, t, 0.45)
		"mark":
			var text := str(ev.get("text", ""))
			if "contested" in text or "intercepts" in text:
				react(PUMP, side, t, 0.18)
		"tackle":
			react(PUMP, side, t, 0.15)
		"final":
			var sc: Array = ev.get("score", [0, 0])
			if sc.size() == 2 and int(sc[0]) != int(sc[1]):
				var won := 0 if int(sc[0]) > int(sc[1]) else 1
				react(CHEER, won, t, 0.95)
				react(HEAD, 1 - won, t, 0.3)


func _push_react() -> void:
	var v: Array = []
	for r: Vector4 in _react:
		v.append(r)
	while v.size() < 4:
		v.append(Vector4(-100.0, 0.0, 0.0, 0.0))
	for m: ShaderMaterial in _people_mats + ([_card_mat] if _card_mat else []):
		m.set_shader_parameter("react", PackedVector4Array(v))


func _colours(m: ShaderMaterial, home: Array, away: Array, home_g := {}, away_g := {}) -> void:
	m.set_shader_parameter("home_a", home[0])
	m.set_shader_parameter("home_b", home[1])
	m.set_shader_parameter("away_a", away[0])
	m.set_shader_parameter("away_b", away[1])
	for side in [["home", home, home_g], ["away", away, away_g]]:
		var g: Dictionary = side[2]
		var cols: Array = side[1]
		m.set_shader_parameter(side[0] + "_gb", g.get("base", cols[0]))
		m.set_shader_parameter(side[0] + "_gp", g.get("pattern", cols[1]))
		m.set_shader_parameter(side[0] + "_design", int(DESIGNS.get(str(g.get("design", "plain")), 0)))


## A supporter on each seat, row by row, evenly spaced round each row's ellipse, aisles and a few
## empty seats left. Each sector leans to one club (40-80% home); a few wear neither.
func _seat(cs: Oval3DCrowdSet, a0: float, b0: float, pitch: float, rise: float) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	# The rows' heights stand in for the seats' (the cheer squads in the lowest rows).
	var heights := []
	for r in range(ROWS):
		heights.append(Vector3(0.0, BASE_Y + float(r + 1) * rise, 0.0))
	var lay := _layout(rng, heights, "")
	lay["low"] = BASE_Y + 3.0 * rise
	var per := []
	for i in range(SECTORS * 2):
		per.append([])
	for r in range(ROWS):
		var dd := float(r) * pitch + PERSON_D
		var y := BASE_Y + float(r + 1) * rise
		var a := a0 + dd
		var b := b0 + dd
		# Arc length round this row's ellipse, so seats sit evenly spaced.
		var N := 4096
		var acc := PackedFloat32Array()
		acc.resize(N + 1)
		var prev := Vector2(a, 0.0)
		for i in range(1, N + 1):
			var th := TAU * float(i) / N
			var p := Vector2(a * cos(th), b * sin(th))
			acc[i] = acc[i - 1] + p.distance_to(prev)
			prev = p
		var L := acc[N]
		var n := int(L / SEAT)
		var j := 0
		for k in range(n):
			if k % AISLE_EVERY < 2 or rng.randf() > fill:
				continue
			var at := (float(k) + (0.5 if r % 2 == 1 else 0.0)) * L / n
			while j < N and acc[j + 1] < at:
				j += 1
			var th := TAU * (float(j) + (at - acc[j]) / maxf(0.0001, acc[j + 1] - acc[j])) / N
			var pos := Vector3(a * cos(th), y, b * sin(th))
			var outward := Vector3(cos(th) / a, 0.0, sin(th) / b).normalized()
			var sector := int(th / TAU * SECTORS) % SECTORS
			per[sector * 2 + (0 if r < ROWS / 2 else 1)].append(_supporter(cs, rng,
					Transform3D(Basis.looking_at(outward, Vector3.UP), pos), _side_at(lay, rng, pos)))
	_chunked(cs, per)


## One supporter at a seat's spot: turned a touch, leaning forward or back a little and sized a
## little either way, on a body picked by share. side is his side and zone (_side_at).
func _supporter(cs: Oval3DCrowdSet, rng: RandomNumberGenerator, at: Transform3D, side: float) -> Array:
	var basis := Basis(Vector3.UP, rng.randf_range(-0.3, 0.3)) * at.basis \
			* Basis(Vector3.RIGHT, rng.randf_range(-0.04, 0.12))
	basis = basis.scaled(Vector3.ONE * rng.randf_range(0.92, 1.06))
	var wsum := 0.0
	for body: Dictionary in cs.bodies:
		wsum += float(body["share"])
	var pick := rng.randf() * wsum
	var bi := 0
	while bi < cs.bodies.size() - 1 and pick >= float(cs.bodies[bi]["share"]):
		pick -= float(cs.bodies[bi]["share"])
		bi += 1
	supporters += 1
	return [Transform3D(basis, at.origin), Color(rng.randf(), side, rng.randf(), rng.randf()), bi]


## Each chunk of seats as its draws: 3D people (one batch per body, each body has its own
## table) shown within mix_d, and cards (every body in one batch, the body's atlas row in the
## seat's fourth number) beyond.
func _chunked(cs: Oval3DCrowdSet, per: Array) -> void:
	var card := _card_mesh()
	for list: Array in per:
		if list.is_empty():
			continue
		var chunk := {"people": []}
		if mix_d > 0.0:
			for bi in range(cs.bodies.size()):
				var mine: Array = list.filter(func(e): return e[2] == bi)
				var p := _batch(_meshes[bi], _people_mats[bi], mine, -1)
				p.visibility_range_end = mix_d
				chunk["people"].append(p)
		var c := _batch(card, _card_mat, list, cs.bodies.size())
		c.visibility_range_begin = mix_d
		chunk["cards"] = c
		_chunks.append(chunk)


## One draw: these seats as a batch of mesh. n_bodies >= 0 puts each seat's body in its fourth number.
func _batch(mesh: Mesh, mat: Material, seats: Array, n_bodies: int) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = mesh
	mm.instance_count = seats.size()
	for i in range(seats.size()):
		mm.set_instance_transform(i, seats[i][0])
		var c: Color = seats[i][1]
		if n_bodies >= 0:
			c.a = (float(seats[i][2]) + 0.5) / float(n_bodies)
		mm.set_instance_custom_data(i, c)
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.material_override = mat
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mmi)
	return mmi


## A card: a 1 x 1 quad standing on its bottom edge (the shader sizes and turns it).
func _card_mesh() -> ArrayMesh:
	var card := ArrayMesh.new()
	var ca := []
	ca.resize(Mesh.ARRAY_MAX)
	ca[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-0.5, 0, 0), Vector3(-0.5, 1, 0), Vector3(0.5, 1, 0), Vector3(0.5, 0, 0)])
	ca[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.BACK, Vector3.BACK, Vector3.BACK, Vector3.BACK])
	ca[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 1), Vector2(0, 0), Vector2(1, 0), Vector2(1, 1)])
	ca[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	card.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, ca)
	card.custom_aabb = AABB(Vector3(-1.5, -0.5, -1.5), Vector3(3, 3, 3))
	return card


## Concrete steps: each row a riser and a tread, and a bench along it.
func _terrace(semi_a: float, semi_b: float, pitch: float, rise: float) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var seg := 240
	var riser := Color(0.42, 0.42, 0.43)
	var tread := Color(0.2, 0.21, 0.24)
	var seat := Color(0.28, 0.3, 0.36)
	var P := func(t: float, d: float, y: float) -> Vector3:
		return Vector3(cos(t) * (semi_a + d), y, sin(t) * (semi_b + d))
	for i in range(seg):
		var t0 := TAU * float(i) / seg
		var t1 := TAU * float(i + 1) / seg
		var inward := -Vector3(cos(t0) / semi_a, 0.0, sin(t0) / semi_b).normalized()
		for r in range(ROWS):
			var d0 := float(r) * pitch
			var d1 := d0 + pitch
			var y0 := BASE_Y + float(r) * rise
			var y1 := y0 + rise
			_quad(st, [P.call(t0, d0, y0), P.call(t0, d0, y1), P.call(t1, d0, y1), P.call(t1, d0, y0)], inward, riser)
			_quad(st, [P.call(t0, d0, y1), P.call(t0, d1, y1), P.call(t1, d1, y1), P.call(t1, d0, y1)], Vector3.UP, tread)
			var sf := d0 + SEAT_F
			var sb := d0 + SEAT_B
			var ys := y1 + SEAT_H
			_quad(st, [P.call(t0, sf, y1), P.call(t0, sf, ys), P.call(t1, sf, ys), P.call(t1, sf, y1)], inward, seat)
			_quad(st, [P.call(t0, sf, ys), P.call(t0, sb, ys), P.call(t1, sb, ys), P.call(t1, sf, ys)], Vector3.UP, seat)
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.roughness = 1.0
	var mi := MeshInstance3D.new()
	mi.name = "Terrace"
	mi.mesh = st.commit()
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)


func _quad(st: SurfaceTool, q: Array, n: Vector3, c: Color) -> void:
	for k in [0, 1, 2, 0, 2, 3]:
		st.set_normal(n)
		st.set_color(c)
		st.add_vertex(q[k])
