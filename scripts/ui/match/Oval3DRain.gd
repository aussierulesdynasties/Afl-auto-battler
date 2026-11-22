class_name Oval3DRain
extends GPUParticles3D
## Rain falling on screen on a wet day (rule 2.83: "yes it should, if its raining?"), as the
## approved prototype draws it (tools/visual/capture_look3d.gd, looks "haze" and "rain"): thin
## streaks in a box of air in front of whichever camera is drawing, and the air greying with
## distance so the far stands fade while the near play stays clear.
## Looks only (rule 1.29): it reads the camera and never touches the match.
##
## The box follows the camera each frame; the drops already falling stay where they are in the
## world (local_coords off), so a camera cut fills the new view within a second.

## A drop falling 12 m/s blurs about half a metre in a 24th of a second.
const STREAK := Vector2(0.025, 0.4)
## A streak's grey as it shows on screen, and how strong at its middle.
const RAIN_GREY := 0.7
const RAIN_ALPHA := 0.22
## How far out along the camera's aim the box's middle sits (its near face about 15 m out: a drop
## nearer than that fills a phone screen as a long white needle), and its middle's height.
const AHEAD := 45.0
const MID_Y := 10.0

var oval: Node3D


func _init(p_oval: Node3D, drops: int) -> void:
	oval = p_oval
	name = "Oval3DRain"
	amount = maxi(1, drops)
	lifetime = 2.5
	preprocess = 2.5
	local_coords = false
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	visibility_aabb = AABB(Vector3(-80, -80, -80), Vector3(160, 160, 160))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(34.0, 18.0, 30.0)
	pm.direction = Vector3(0.25, -1.0, 0.08)
	pm.spread = 2.0
	pm.initial_velocity_min = 11.0
	pm.initial_velocity_max = 13.0
	pm.gravity = Vector3(0.0, -2.0, 0.0)
	process_material = pm
	var q := QuadMesh.new()
	q.size = STREAK
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	m.billboard_keep_scale = true
	# The haze greys the far stands, not the drops in front of them (fogged, a drop 40 m out
	# takes the haze's own grey and vanishes against it).
	m.disable_fog = true
	# Drawn over the match film (Oval3D._film), which redraws the picture as the camera saw it
	# before anything see-through: under it, the film would wipe the drops off. So the drop's
	# colour is set as it shows on screen: the prototype's streak (0.45 grey) after the wet day's
	# exposure and the TV tone, about 0.7.
	m.render_priority = Material.RENDER_PRIORITY_MAX
	m.albedo_color = Color(RAIN_GREY, RAIN_GREY * 1.03, RAIN_GREY * 1.08, RAIN_ALPHA)
	# Soft across its width and fading at both ends, as a camera sees a falling drop: drawn over
	# the film, a hard-edged streak would be a crisp white line the film never softened.
	m.albedo_texture = _streak()
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	q.material = m
	draw_pass_1 = q


## The streak's shape: brightest down its middle, fading to nothing at its sides and ends.
static func _streak() -> ImageTexture:
	var img := Image.create(8, 32, false, Image.FORMAT_LA8)
	for y in 32:
		var along := sin(PI * (y + 0.5) / 32.0)
		for x in 8:
			var across := 1.0 - absf((x + 0.5) / 8.0 - 0.5) * 2.0
			img.set_pixel(x, y, Color(1, 1, 1, across * across * along))
	return ImageTexture.create_from_image(img)


func _ready() -> void:
	place()
	restart()


func _process(_delta: float) -> void:
	place()


## The box of air in front of the camera, level, whatever the camera's tilt.
func place() -> void:
	var cam: Camera3D = oval.get("camera")
	if cam == null or not cam.is_inside_tree():
		return
	var fwd := -cam.global_basis.z
	var f := Vector3(fwd.x, 0.0, fwd.z)
	if f.length() < 0.01:
		f = Vector3.FORWARD
	f = f.normalized()
	var c := cam.global_position + fwd * AHEAD
	global_transform = Transform3D(Basis.looking_at(f, Vector3.UP), Vector3(c.x, MID_Y, c.z))


## Rain haze: depth fog that starts 40 m from the camera and thickens to the far stands, so the
## men stay clear and only the distance greys (cheap on a phone). The prototype's values.
static func haze(env: Environment, on: bool) -> void:
	env.fog_enabled = on
	if not on:
		return
	env.fog_mode = Environment.FOG_MODE_DEPTH
	env.fog_density = 0.55
	env.fog_depth_begin = 40.0
	env.fog_depth_end = 280.0
	env.fog_depth_curve = 1.0
	env.fog_light_color = Color(0.15, 0.15 * 1.02, 0.15 * 1.06)
	env.fog_light_energy = 1.0
	env.fog_sun_scatter = 0.0
	env.fog_aerial_perspective = 0.0
	env.fog_sky_affect = 0.0
	env.fog_height_density = 0.0
