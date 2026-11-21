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
##   shadow_atlas  the sun's shadow map, pixels a side (the four towers at night share it)
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
##   scale         share of the screen's pixels the 3D picture is drawn at (stretched to fit)
##   blades        the standing grass blades round the ball
const PRESETS := {
	HIGH: {"shadow_atlas": 4096, "shadow_filter": RenderingServer.SHADOW_QUALITY_SOFT_HIGH, "splits": 4,
			"seat_shadows": true, "stand_shade": true, "people_d": 55.0, "lod": 1.0, "scale": 1.0,
			"blades": true},
	MEDIUM: {"shadow_atlas": 2048, "shadow_filter": RenderingServer.SHADOW_QUALITY_SOFT_LOW, "splits": 4,
			"seat_shadows": false, "stand_shade": true, "people_d": 30.0, "lod": 2.0, "scale": 1.0,
			"blades": true},
	LOW: {"shadow_atlas": 2048, "shadow_filter": RenderingServer.SHADOW_QUALITY_SOFT_LOW, "splits": 2,
			"seat_shadows": false, "stand_shade": false, "people_d": 0.0, "lod": 4.0, "scale": 0.75,
			"blades": false},
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


## The 3D picture's viewport: its mesh detail and how many of its pixels are drawn.
static func apply_viewport(level: String, vp: Viewport) -> void:
	var p := preset(level)
	vp.mesh_lod_threshold = float(p["lod"])
	var s := float(p["scale"])
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = s


## A ground's seats cast shadows or not, by the level: the seat batches (GroundModels) and a
## model's own seat meshes. The rest of the model always casts (its roofs shade the stands).
static func apply_model(level: String, root: Node) -> void:
	if bool(preset(level)["seat_shadows"]):
		return
	for g: GeometryInstance3D in root.find_children("*", "GeometryInstance3D", true, false):
		if g.has_meta("seats") or str(g.name).to_lower().contains("seat"):
			g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


## The sun's shadow bands (each draws its casters again).
static func apply_sun(level: String, sun: DirectionalLight3D) -> void:
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS \
			if int(preset(level)["splits"]) == 4 else DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
