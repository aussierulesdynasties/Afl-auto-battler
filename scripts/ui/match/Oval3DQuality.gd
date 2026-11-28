class_name Oval3DQuality
extends RefCounted
## Graphics quality for the 3D match view: Low, Medium or High (Settings > Graphics). Looks only:
## the match, its result and every call are the same at every level.
##
## High is the look as built and ruled (shadows of rule 2.80, the crowd mix of rule 2.92: 3D
## people within 55 m of the camera, cards beyond). Medium and Low trade detail the broadcast
## camera barely shows for a steadier frame on a weaker phone. What each level costs, ground by
## ground, is measured by tools/perf/grounds_budget.gd (docs/PHONE_3D_BUDGET.md).

const LOW := "low"
const MEDIUM := "medium"
const HIGH := "high"
const LEVELS := [LOW, MEDIUM, HIGH]

## Each level:
##   shadow_atlas  the sun's shadow map, pixels a side
##   shadow_filter how soft its edge is drawn (RenderingServer.SHADOW_QUALITY_*). Not the hard
##                 edge: on the Mobile renderer it loses the roof's shade on a stand (Marvel lit
##                 bright under its roof), so Low keeps the soft filter's cheapest setting
##   splits        the sun's shadow map is cut into this many bands by distance, finer near the
##                 camera; each band draws every shadow caster in it again: 4 or 2
##   seat_shadows  each seat casts its own shadow (under a supporter it is barely seen)
##   stand_shade   a late game's plain stand throws its shade across the wing (rule 2.80 C)
##   people_d      m from the camera within which a supporter is a 3D person, cards beyond; 0
##                 every supporter a card (no 3D people built)
##   lod           mesh detail threshold (Viewport.mesh_lod_threshold): higher drops detail sooner
##   scale         share of the screen's pixels the 3D picture is drawn at (stretched to fit, by FSR)
##   blades        the standing grass blades round the ball
##   tower_shadows how many of a ground's light towers throw the men's shadows at night (each
##                 draws the men again into its own part of the sun's shadow map); the rest
##                 light without one
##   rain          drops in the air on a wet day (rule 2.83: when it rains, rain falls on screen, so
##                 every level keeps some; High is the approved prototype's count)
##   msaa          edge smoothing (Viewport.msaa_3d): each pixel's edge sampled 4 or 2 times, so a
##                 player's outline, a line or a post is not a staircase. Multisampling, not FXAA:
##                 FXAA blurs the whole picture, guernsey numbers and the boards' names with it.
##                 On a phone's tiled GPU the extra samples stay on the chip, so it is cheap, and
##                 it is what the hair's alpha-to-coverage cards need to draw soft strand ends.
##                 Low has none: its picture is drawn at three-quarter size and stretched,
##                 which softens the edges anyway.
const PRESETS := {
	HIGH: {"shadow_atlas": 4096, "shadow_filter": RenderingServer.SHADOW_QUALITY_SOFT_HIGH, "splits": 4,
			"seat_shadows": true, "stand_shade": true, "people_d": 55.0, "lod": 1.0, "scale": 1.0,
			"blades": true, "tower_shadows": 4, "rain": 40000, "msaa": Viewport.MSAA_4X},
	MEDIUM: {"shadow_atlas": 2048, "shadow_filter": RenderingServer.SHADOW_QUALITY_SOFT_LOW, "splits": 4,
			"seat_shadows": false, "stand_shade": true, "people_d": 30.0, "lod": 2.0, "scale": 1.0,
			"blades": true, "tower_shadows": 2, "rain": 20000, "msaa": Viewport.MSAA_2X},
	LOW: {"shadow_atlas": 2048, "shadow_filter": RenderingServer.SHADOW_QUALITY_SOFT_LOW, "splits": 2,
			"seat_shadows": false, "stand_shade": false, "people_d": 0.0, "lod": 4.0, "scale": 0.75,
			"blades": false, "tower_shadows": 1, "rain": 10000, "msaa": Viewport.MSAA_DISABLED},
}


## The level's settings; an unknown level reads as High.
static func preset(level: String) -> Dictionary:
	return PRESETS.get(level, PRESETS[HIGH])


static func valid(level: String) -> String:
	return level if level in LEVELS else HIGH


## The shadow map's size and edge, for the whole renderer (one sun at a time draws).
static func apply_shadows(level: String) -> void:
	var p := preset(level)
	RenderingServer.directional_shadow_atlas_set_size(int(p["shadow_atlas"]), true)
	RenderingServer.directional_soft_shadow_filter_set_quality(int(p["shadow_filter"]))


## The 3D picture's viewport: its mesh detail, how many of its pixels are drawn and how its
## edges are smoothed.
static func apply_viewport(level: String, vp: Viewport) -> void:
	var p := preset(level)
	vp.mesh_lod_threshold = float(p["lod"])
	var s := float(p["scale"])
	# A smaller picture is stretched back up with FSR 1, which sharpens edges as it stretches;
	# plain bilinear stretching left Low's players and lines soft (about 1% more GPU time).
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if s < 1.0 else Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = s
	vp.msaa_3d = int(p["msaa"]) as Viewport.MSAA
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED


## A ground's seats cast shadows or not, by the level: the seat batches (GroundModels) and a
## model's own seat meshes. The rest of the model always casts (its roofs shade the stands).
static func apply_model(level: String, root: Node) -> void:
	# Low draws the buildings near the ground plain (GroundModels._facade): no floors, recesses or hipped roofs.
	for g: Node3D in root.find_children("BuildingsNear*", "Node3D", true, false):
		if g.has_meta("facade_detail"):
			g.visible = level != LOW
		elif g.has_meta("facade_plain"):
			g.visible = level == LOW
	# The far horizon's low blocks and its trees past 1.5 km (tools/grounds/backdrop/horizon: city_far_low,
	# trees_far): Low leaves them to the land's own photo. 138k of Marvel's 260k horizon triangles, a pixel
	# high in Low's three-quarter picture.
	for pattern in ["city_far_low*", "trees_far*"]:
		for g: Node3D in root.find_children(pattern, "Node3D", true, false):
			g.visible = level != LOW
	# A roof's lattice trusses (the Gabba's rafters, a model object named "lattice"): thousands of thin members drawn
	# again into every shadow band for a shade the roof sheet already casts; High keeps their shadows.
	if level != HIGH:
		for g: GeometryInstance3D in root.find_children("*", "GeometryInstance3D", true, false):
			if str(g.name).to_lower().begins_with("lattice"):
				g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if bool(preset(level)["seat_shadows"]):
		return
	for g: GeometryInstance3D in root.find_children("*", "GeometryInstance3D", true, false):
		if g.has_meta("seats") or str(g.name).to_lower().contains("seat"):
			g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


## The sun's shadow bands (each draws its casters again).
static func apply_sun(level: String, sun: DirectionalLight3D) -> void:
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS \
			if int(preset(level)["splits"]) == 4 else DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
