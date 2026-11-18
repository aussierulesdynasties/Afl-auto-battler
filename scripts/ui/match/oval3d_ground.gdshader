// The 3D oval's turf and paint, worked out from world metres (Oval3D.gd; the look set by
// Oval3DTurf.gd from the day's weather and time of day).
// AFL markings: boundary, centre square (50 m), centre circles (r 5 and 1.5) with the line
// across them, 50 m arcs from the centre of each goal, goal squares (9 m by 6.4 m), goal lines.
// Grass blades are 2-3 cm: a pixel or two from the broadcast cameras, so the turf is shading,
// not geometry. What reads on TV and is drawn here:
//   mown stripes  bands 12 m wide, mowed across the ground in alternate directions; a band is
//                 light when you look the way its blades lean and dark looking into them, so the
//                 stripes swap as the camera moves round and fade looking along them;
//   variation     broad patches (metres) and fine speckle (centimetres, faded out before it
//                 can shimmer) so the green is never flat;
//   wear          a map over the ground (Oval3DTurf): thin pale grass where play has been, mud
//                 in the wet;
//   weather       wet: darker, a wet sheen the lights show in; hot: straw, bleached patches,
//                 matte; windy: gusts rolling across the sheen.
shader_type spatial;
render_mode cull_disabled;

uniform vec2 half_size = vec2(86.3, 67.4);
uniform float goal_x = 85.0;
uniform float line_w = 0.12;
// The two mown colours (sRGB), as VignetteWeather.grass gives them for the day.
uniform vec3 grass_a : source_color = vec3(0.16, 0.39, 0.17);
uniform vec3 grass_b : source_color = vec3(0.18, 0.43, 0.19);
uniform vec3 apron_col : source_color = vec3(0.13, 0.32, 0.14);
uniform vec3 worn_col : source_color = vec3(0.38, 0.36, 0.22);
uniform vec3 mud_col : source_color = vec3(0.31, 0.25, 0.17);
uniform float wet = 0.0;        // 0 dry .. 1 soaked
uniform float hot = 0.0;        // 0 .. 1 dried out
uniform float wind = 0.0;       // 0 calm .. 1 strong breeze
uniform vec2 wind_dir = vec2(1.0, 0.0);
uniform float stripe_amount = 0.16;
uniform float saturation = 0.72;
// Wear over the ground: R thin grass, G churned; UV 0..1 across the whole plane.
uniform sampler2D wear_map : filter_linear, repeat_disable;
uniform vec2 wear_half = vec2(93.3, 74.4);

// The ground's own metres (the oval turns half a turn when the sides change ends; the
// stripes and the wear turn with it) and the camera in the same frame.
// The turf's textures (tools/oval3d/make_turf_textures.py): blades seen from above (0.6 m a
// tile; variation about the turf colour, 0.5 = the colour itself), their normals, and
// smooth patch noise (R broad, G clumps, B mottle).
uniform sampler2D blades_tex : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D blades_n : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D patches_tex : filter_linear_mipmap, repeat_enable;
uniform float blade_tile = 1.1;
uniform float blade_contrast = 1.5;
varying vec3 wpos;
varying vec3 cam_local;

void vertex() {
	wpos = VERTEX;
	cam_local = (inverse(MODEL_MATRIX) * vec4(CAMERA_POSITION_WORLD, 1.0)).xyz;
}

float paint(float d, float w) {
	float aa = fwidth(d) * 1.2;
	return 1.0 - smoothstep(w - aa, w + aa, abs(d));
}

vec3 lin(vec3 c) { return pow(c, vec3(2.2)); }

// The blade tile's own frame: u across the ground (x), v along the mower's run (z).
vec2 blade_uv(vec2 p, float lean, float tile) {
	return vec2(p.x, p.y * lean) / tile;
}

void fragment() {
	vec2 p = wpos.xz;
	float e = length(p / half_size);
	// Which way you look across the ground, flat.
	vec3 view_w = normalize(wpos - cam_local);
	vec2 look = normalize(view_w.xz + vec2(1e-4));

	// Mown stripes: bands along the ground, each mowed across it (+z or -z); the blades in a
	// band lean the way its mower ran (the tile is flipped band to band).
	float band = floor(p.x / 12.0);
	float lean = mod(band, 2.0) < 1.0 ? 1.0 : -1.0;
	// Looking with the lean shows the blades' lit backs (light), into it their shaded tips.
	float facing = lean * look.y;
	float stripe = 0.5 + 0.5 * facing;
	float edge = smoothstep(0.0, 0.6, min(fract(p.x / 12.0), 1.0 - fract(p.x / 12.0)) * 12.0);
	stripe = mix(0.5, stripe, edge);
	vec3 grass = mix(grass_a, grass_b, stripe);
	// The flat views' turf colours are strong; lit in 3D they go neon. Turf on a broadcast
	// is a muted green (red about 0.6 of green): take a quarter of the colour toward grey.
	grass = mix(vec3(dot(grass, vec3(0.3, 0.59, 0.11))), grass, saturation);
	grass *= 1.0 + stripe_amount * (stripe - 0.5) * (1.0 - 0.5 * wet);

	// The blades: the tile at its own size, and again larger and offset so it never repeats
	// visibly; mipmaps average them to the right grain at any distance.
	vec2 buv = blade_uv(p, lean, blade_tile);
	vec3 bl = texture(blades_tex, buv).rgb * 2.0;
	vec3 bl2 = texture(blades_tex, blade_uv(p + vec2(3.7, 1.3), lean, blade_tile * 3.1)).rgb * 2.0;
	vec3 blade = 1.0 + (mix(bl, bl2, 0.3) - 1.0) * blade_contrast;
	vec3 nb = texture(blades_n, buv).rgb;
	nb.y = lean > 0.0 ? nb.y : 1.0 - nb.y;

	// Variation: broad patches, then clumps, then mottle.
	vec3 pa = texture(patches_tex, p / 90.0).rgb;
	vec3 pb = texture(patches_tex, p / 23.0 + 0.37).rgb;
	float broad = pa.r * 0.6 + pb.g * 0.4;
	float clump = texture(patches_tex, p / 6.0 + 0.71).b;
	float speck = dot(bl, vec3(0.33));
	grass *= 0.86 + 0.28 * broad;
	grass *= 0.93 + 0.14 * clump;
	grass *= blade;

	// Hot: bleached patches where the broad noise is high.
	float bleach = hot * smoothstep(0.52, 0.68, broad + 0.2 * (clump - 0.5));
	grass = mix(grass, grass * vec3(1.3, 1.2, 0.75), bleach);

	// Wind: gusts rolling over the turf, the blades bending flatter (lighter) as one passes.
	float gust = texture(patches_tex, (p - wind_dir * TIME * 6.0) / 40.0).g;
	grass *= 1.0 + wind * 0.12 * (gust - 0.5) * 2.0;

	vec3 col = e > 1.0 ? apron_col * (0.86 + 0.28 * broad) * blade : grass;

	// Wear: thin pale grass where play has been; churned to mud in the wet.
	vec2 wuv = p / (2.0 * wear_half) + 0.5;
	vec4 w = texture(wear_map, wuv);
	float thin = w.r * (0.75 + 0.5 * clump);
	float churn = w.g * (0.6 + 0.8 * clump);
	col = mix(col, worn_col * mix(vec3(1.0), blade, 0.6), clamp(thin, 0.0, 1.0) * (1.0 - 0.6 * wet));
	col = mix(col, mud_col * (0.8 + 0.2 * speck), clamp(churn * wet, 0.0, 0.8));

	float ink = 0.0;
	// Boundary: the ellipse's distance, approximately, in metres.
	vec2 g = 2.0 * p / (half_size * half_size);
	float db = (dot(p / half_size, p / half_size) - 1.0) / max(length(g), 1e-4);
	// Behind each goal the boundary is the goal line: straight through all four posts, out
	// to where the oval meets it, as on a real ground (one line, not two).
	float yc = half_size.y * sqrt(max(1.0 - (goal_x / half_size.x) * (goal_x / half_size.x), 0.0));
	if (abs(p.y) < yc && abs(p.x) > goal_x - 6.0) db = abs(p.x) - goal_x;
	ink = max(ink, paint(db, line_w * 1.4));
	if (e < 1.0) {
		float sq = max(abs(p.x), abs(p.y)) - 25.0;
		ink = max(ink, paint(sq, line_w));
		float r = length(p);
		ink = max(ink, paint(r - 5.0, line_w));
		ink = max(ink, paint(r - 1.5, line_w));
		if (abs(p.y) < 5.0) ink = max(ink, paint(p.x, line_w));
		ink = max(ink, paint(length(p - vec2(goal_x, 0.0)) - 50.0, line_w));
		ink = max(ink, paint(length(p - vec2(-goal_x, 0.0)) - 50.0, line_w));
		for (int s = -1; s <= 1; s += 2) {
			float gx = float(s) * goal_x;
			if (abs(p.y) < 9.6) ink = max(ink, paint(p.x - gx, line_w));
			float inside = float(s) * (gx - p.x);
			if (inside > 0.0 && inside < 9.0) {
				ink = max(ink, paint(abs(p.y) - 3.2, line_w));
			}
			if (abs(p.y) < 3.2) ink = max(ink, paint(p.x - (gx - float(s) * 9.0), line_w));
		}
	}
	// Paint on worn or muddy turf is broken up, not a clean line.
	ink *= 1.0 - 0.55 * clamp(churn * wet + thin * 0.5, 0.0, 1.0) * step(1.0, speck);
	col = mix(col, vec3(0.96, 0.96, 0.93), ink * 0.92);
	ALBEDO = lin(col);
	// Dry turf is matte; wet blades hold a film of water that catches the lights. Paint and
	// mud lie flat; the blades' normals give the grain its light and shade.
	// Water sits in patches (the low spots): the sheen there, the rest just dark and damp.
	float sheen = wet * smoothstep(0.45, 0.62, broad) * (1.0 - 0.5 * churn);
	// A tight highlight: glints off the wet blades, not a grey wash over the ground.
	ROUGHNESS = mix(mix(0.85, 0.97, hot), 0.5, sheen);
	// Measured: with the tower lights facing the camera and the wet exposure, even 0.06 at a
	// grazing angle lays a grey film over the whole ground. Soaked turf keeps it to the puddles.
	SPECULAR = mix(mix(0.06, 0.012, wet), 0.05, sheen);
	NORMAL_MAP = mix(nb, vec3(0.5, 0.5, 1.0), clamp(ink + churn * wet, 0.0, 1.0));
	NORMAL_MAP_DEPTH = 1.0;
}
