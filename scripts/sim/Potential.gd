class_name Potential
extends RefCounted
## Potential (POT): a player's projected natural peak - where his rating is
## expected to settle, not a cap. It is set once, when he enters the game,
## and never moves to match what he later reaches. Development is pulled
## toward it and gets steadily harder near and past it, under the same rules
## for every club; an occasional breakout carries a player beyond it.
##
## The dataset is one season of stats, so a star who missed most of 2026 is
## rated on two or three games and shrunk toward the league average. POT is
## what the development loop pulls toward, so those players - and high draft
## picks - climb quickly, while a player already at his ceiling stays put.
##
##   draftees    from draft rank: the top pick projects near 90
##   AFL players the highest of:
##                 current rating plus age headroom (younger = more room)
##                 recent peak: best 2023-25 rating (8+ games, rated with the
##                   same model), eased for players past 29
##                 draft pedigree: a high national-draft pick pulls a young
##                   player's ceiling up (pick 1 ~90), fading by 25
##   injured     under 12 games in 2026 but 12+ below his recent peak: the
##               2026 rating is a small-sample artefact, so he gets a rehab
##               year (Rozee, Moore, Sam Darcy in the shipped data)
##   overrides   data/potential_overrides.csv, matched on club + real name
##
## History and pedigree come from data/player_history_2026.csv, built by
## tools/build_history.py from AFL Tables and Wikipedia.
##
## Every roll is seeded by player id, so a player's POT is the same on every
## launch and every career.

const MAX_POT := 97
## Generated ceilings stop a few points above each position's best 2026
## rating (MID 92; DEF, FWD and RUCK 87-88 after the key position stretch
## in Ratings.position_stretch), so nobody outgrows his position. History,
## draft pedigree and hand-set overrides are not capped.
const ROLE_CAP := {"MID": 95, "RUCK": 92, "FWD": 92, "DEF": 92}
## An override this far above the current rating marks a rehab case.
const REHAB_GAP := 15
## Automatic rehab: a short 2026 and a recent peak this far above it.
const REHAB_GAMES := 12
const REHAB_PEAK_GAP := 12
## Seasons that count as "recent" for the peak: the data season's last three
## (2023 for today's start). GameDB sets it with the dataset.
static var peak_from_year := 2023
## Informed potential (director 2026-11-11, "Informed", TODO row 142): a real
## player's real peak sets his ceiling in a past start, give or take this luck.
const REAL_PEAK_LUCK := 3.0
## A 30-year-old's peak is not all coming back: ease it per year past 29.
const PEAK_AGE_EASE := 1.5

## Growth room above the current rating, by age.
## Oldest age that still gets a draft-rank ceiling (_draftee_potential).
const MAX_PROSPECT_AGE := 21.0
const AGE_HEADROOM := [[20.0, 16.0], [22.0, 12.0], [24.0, 8.0], [26.0, 4.0], [28.0, 2.0]]

## The rehab year: a star back from an injury season closes most of the gap
## at the next rollover, whatever his age.
const REHAB_PULL := 0.9
## Past 30 a player comes back from an injury season less of the way: the
## rehab pull eases this much per year, never below REHAB_PULL_FLOOR of it.
const REHAB_AGE_EASE := 0.12
const REHAB_PULL_FLOOR := 0.4


## The age a player's development step is read at: Fine Wine runs his decline
## Traits.FINE_WINE_YEARS behind his age once he is past the growing years
## (the 0-to-2 band ends at 27), so his growth is untouched.
const DECLINE_FROM := 27.0


static func ageing_age(age: float, fine_wine: bool) -> float:
	if not fine_wine or age <= DECLINE_FROM:
		return age
	return maxf(DECLINE_FROM, age - Traits.FINE_WINE_YEARS)


## The age the retirement rules read for him (Prospects.should_retire): Fine
## Wine retires Traits.FINE_WINE_YEARS later.
static func retire_age(p: Dictionary) -> float:
	var age := float(p.get("age", 26.0))
	return age - Traits.FINE_WINE_YEARS if Traits.fine_wine(p) else age


static func rehab_pull(age: float) -> float:
	return REHAB_PULL * clampf(1.0 - REHAB_AGE_EASE * maxf(0.0, age - 30.0), REHAB_PULL_FLOOR, 1.0)


## Set p["potential"] unless an earlier call or a save already did.
static func assign(p: Dictionary) -> void:
	if p.has("potential"):
		return
	var ov := int(Rating.ovr(p, 50))
	var rng := _rng(p)
	# A past start knows each real player's real peak (p["real_peak"], his best
	# real season from the data season on): that sets his ceiling, give or take
	# luck, not capped by position, the stars of each class tending to become
	# the sim's stars.
	var real_peak := float(p.get("real_peak", 0))
	if real_peak > 0.0:
		var luck := rng.randf_range(-REAL_PEAK_LUCK, REAL_PEAK_LUCK)
		p["potential"] = clampi(int(round(real_peak + luck)), ov, MAX_POT)
		var games := float(p.get("gm", 0.0))
		if games > 0.0 and games < REHAB_GAMES and real_peak - float(ov) >= REHAB_PEAK_GAP:
			p["rehab"] = true
		return
	var pot: float
	if bool(p.get("projected", false)):
		pot = _draftee_potential(p, rng)
	else:
		pot = float(ov) + _headroom(float(p.get("age", 26.0))) + rng.randf_range(-2.0, 3.0)
	var cap := mini(MAX_POT, int(ROLE_CAP.get(str(p.get("role", "MID")), MAX_POT)))
	pot = clampf(pot, float(ov), float(maxi(ov, cap)))
	# Real history and pedigree are not capped by position.
	var peak := recent_peak(p)
	if peak > 0.0:
		pot = maxf(pot, peak)
		var gm := float(p.get("gm", 0.0))
		if gm > 0.0 and gm < REHAB_GAMES and peak - float(ov) >= REHAB_PEAK_GAP:
			p["rehab"] = true
	pot = maxf(pot, pedigree_potential(p, pot))
	p["potential"] = clampi(int(round(pot)), ov, MAX_POT)
	# POT is what he can still reach (director, 2026-10-07), not a ceiling
	# from an old season: from 26, when growth is nearly done, it is the
	# best his development can still take him to (a rehab year included).
	# Younger players keep the projection their development pulls toward.
	if float(p.get("age", 26.0)) >= REACHABLE_FROM_AGE:
		p["potential"] = clampi(int(round(reachable_peak(p))), ov, MAX_POT)


## From this age POT is the reachable peak (assign).
const REACHABLE_FROM_AGE := 26.0


## The best rating his development is expected to take him to from now
## (outlook, ten seasons, breakouts aside).
static func reachable_peak(p: Dictionary) -> float:
	var best := float(Rating.ovr(p, 0))
	for season in outlook(p, 10):
		best = maxf(best, float(season[0]))
	return best


## Best recent season (8+ games), eased for age. 0 when there is none.
static func recent_peak(p: Dictionary) -> float:
	var best := 0.0
	for season in p.get("history", []):
		if int(season[0]) >= peak_from_year:
			best = maxf(best, float(season[1]))
	if best <= 0.0:
		return 0.0
	var age := float(p.get("age", 26.0))
	return best - PEAK_AGE_EASE * maxf(0.0, age - 29.0)


## A young player's national-draft pick pulls his ceiling toward what that
## pick is expected to become: pick 1 ~90, pick 30 ~81, pick 60 ~72. The
## pull is full at 19 and gone by 25; rookie listings and undrafted players
## get none.
static func pedigree_potential(p: Dictionary, pot: float) -> float:
	if str(p.get("drafted_type", "")) != "national":
		return pot
	var age := float(p.get("age", 26.0))
	var pull := clampf((25.0 - age) / 6.0, 0.0, 1.0) * 0.5
	if pull <= 0.0:
		return pot
	var ceiling := 90.0 - 0.3 * float(maxi(1, int(p.get("drafted_pick", 60))) - 1)
	return pot + (ceiling - pot) * pull if ceiling > pot else pot


## A hand-set POT (data/potential_overrides.csv). Also flags the rehab year
## when the rating sits well below it after a short (injury) season, so the
## jump happens next rollover. A full season's player grows at the ordinary
## pace toward it (director 2026-11-17, silent corrections).
static func set_override(p: Dictionary, pot: int) -> void:
	p["potential"] = clampi(pot, int(Rating.ovr(p, 1)), MAX_POT)
	var games := float(p.get("gm", 0.0))
	if int(p["potential"]) - int(Rating.ovr(p, 0)) >= REHAB_GAP 			and games > 0.0 and games < REHAB_GAMES:
		p["rehab"] = true


## What a player is expected to be worth, season by season, from now, by the
## game's own development today (director 2026-11-28, plan step 4: "Replace
## stale Potential.outlook with a projection that matches the actual XP +
## age-curve growth system"), taken at expected values instead of rolled:
## - XP: OUTLOOK_GAMES ordinary senior games a season at his POT's pace
##   (Growth.points_per_game), never past POT (GameState._buy);
## - ageing: each weighted attribute's age-curve change for the season
##   (Growth.age_change), at its share of his OVR and the stretch's slope, a
##   rise only while he is below POT, Fine Wine's decline later and gentler
##   (Growth.age_step);
## - the rehab year: rehab_pull(age) of the gap closed the summer he is back
##   (Growth.summer);
## - and retirement (Prospects.should_retire's ages).
## [[rating, chance he is still playing], ...] for `years` seasons, the first
## the one about to be played. Breakouts are left out: nobody can plan on one.
## Example: a 22-year-old 60 with POT 75 gains 15 x 0.12 = 1.8 a season from
## XP plus his age curves' share, and stops at 75.
const OUTLOOK_GAMES := 15.0
static func outlook(p: Dictionary, years: int) -> Array:
	var r := float(Rating.ovr(p, 50))
	var pot := maxf(r, float(p.get("potential", r)))
	var age := float(p.get("age", 26.0))
	var rehab := bool(p.get("rehab", false))
	var fine := Traits.fine_wine(p)
	var shift := Traits.FINE_WINE_YEARS if fine else 0.0
	var w: Dictionary = Rating.WEIGHTS.get(Rating.apos_of(p), Rating.WEIGHTS["Midfielder"])
	var alive := 1.0
	var out := []
	for t in range(years):
		out.append([r, alive])
		var raw := 0.0
		for k in w:
			raw += float(w[k]) * Growth.season_change(str(k), age, fine) / 100.0
		var d := raw * Rating.slope(Rating.unstretch(r))
		if d > 0.0 and r >= pot:
			d = 0.0
		var g := 0.0
		if r < pot:
			g = minf(pot - r, OUTLOOK_GAMES * Growth.points_per_game(int(round(pot))))
			if rehab:
				g = maxf(g, (pot - r) * rehab_pull(age))
		rehab = false
		var next := clampf(r + g + d, 25.0, float(MAX_POT))
		if g + d > 0.0:
			next = minf(next, maxf(r, pot))
		r = next
		age += 1.0
		var go := 0.0
		var ra := age - shift
		if r <= 32.0 or ra >= 37.0:
			go = 1.0
		elif ra >= 35.0:
			go = 0.70
		elif ra >= 33.0 and r < 42.0:
			go = 0.30
		alive *= 1.0 - go
	return out


## A breakout: an off-season in which a player jumps well beyond his normal
## development - past his projection if he was near it. Rolled fresh each
## year for every player alike, likelier when young, rare at any age, and
## open-ended: BREAKOUT_MIN plus an exponential tail averaging BREAKOUT_MEAN.
const BREAKOUT_CHANCE := [[22.0, 0.03], [25.0, 0.02], [28.0, 0.01]]
const BREAKOUT_MIN := 2.0
const BREAKOUT_MEAN := 2.5


static func breakout_jump(rng: RandomNumberGenerator) -> float:
	return BREAKOUT_MIN - BREAKOUT_MEAN * log(maxf(1e-6, 1.0 - rng.randf()))


static func breakout_chance(age: float) -> float:
	for band in BREAKOUT_CHANCE:
		if age <= float(band[0]):
			return float(band[1])
	return 0.0


static func _headroom(age: float) -> float:
	for band in AGE_HEADROOM:
		if age <= float(band[0]):
			return float(band[1])
	return 0.0


## A draftee's POT by his pick (director 2026-11-26, question box): "Set Pick
## 1 POT to ~84-90, Picks 2-5 to ~80-86, First Round (6-18) to ~74-82, and
## Rounds 2-3 to ~64-76 (with rare late-pick gems)". [last pick, lowest,
## highest], drawn evenly in his pick's range; a prospect with no rank (0) is
## a late pick.
const DRAFT_POT := [[1, 84.0, 90.0], [5, 80.0, 86.0], [18, 74.0, 82.0], [9999, 64.0, 76.0]]
## A late pick's gem: 1 in 30 of picks past the first round draws from picks
## 2-5's range instead (about one a class).
const GEM_CHANCE := 1.0 / 30.0
const GEM_FROM := 19


static func _draftee_potential(p: Dictionary, rng: RandomNumberGenerator) -> float:
	# A seasoned player on an expansion list is projected like a draftee but
	# is not an 18-year-old pick: past 21 his ceiling is the one any player
	# his age has. Draft classes are 18-19, so they never reach this.
	var age := float(p.get("age", 18.0))
	if age > MAX_PROSPECT_AGE:
		return float(int(Rating.ovr(p, 50))) + _headroom(age) + rng.randf_range(-2.0, 3.0)
	var rank := int(p.get("draft_rank", 0))
	if rank <= 0:
		rank = 9999
	var band: Array = DRAFT_POT[DRAFT_POT.size() - 1]
	for b in DRAFT_POT:
		if rank <= int(b[0]):
			band = b
			break
	var pot := rng.randf_range(float(band[1]), float(band[2]))
	if rank >= GEM_FROM and rng.randf() < GEM_CHANCE:
		pot = rng.randf_range(float(DRAFT_POT[1][1]), float(DRAFT_POT[1][2]))
	# A strong or weak generated class moves its best prospects' ceilings
	# (Prospects.CLASS_TIERS); an international's raw code adds room.
	return pot + float(p.get("class_ceiling", 0.0))


static func _rng(p: Dictionary) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("pot|%s|%s" % [str(p.get("id", "")), str(p.get("draft_year", ""))])
	return rng
