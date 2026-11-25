shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;
// A goal umpire's flag cloth (tools/oval3d/crew/build_crew.py crew_flag_cloth): white sailcloth
// along the top of the stick, the stick up +Y, the cloth out along +X, UV.x from the stick (0)
// to the fly (1). Driven by Oval3D each frame:
//   furl  0 wrapped round the stick (stowed), 1 open
//   air   0 still air (the cloth hangs from the stick under its own weight), 1 the stick moving
//         fast enough to stream it out flat, fluttering

uniform float furl : hint_range(0.0, 1.0) = 1.0;
uniform float air : hint_range(0.0, 1.0) = 0.0;
uniform float seed = 0.0;
// Set from RTX 4070 renders (2026-11-23): at 0.93 the sunlit face clipped to pure white over
// half the flag; at 0.80 it peaks about 240, just above the painted boundary line (232), folds kept.
uniform vec3 cloth_colour : source_color = vec3(0.80, 0.80, 0.784);
// How much light the thin cloth lets through from behind.
uniform float backlight : hint_range(0.0, 1.0) = 0.6;
// The stick draws with this shader too (stick = true): plain white-painted dowel, not moved.
uniform bool stick = false;

const float STICK_R = 0.012;
const float WIDTH = 0.54;
const float WOUND_R0 = 0.013;
const float WOUND_GROW = 0.007;

float a_fold(float d, float s) {
	return d * 40.0 + s;
}

// Where the cloth at (u across, y up the stick) sits, in the flag's own space. down: the way
// gravity pulls, in that space.
vec3 cloth_at(float u, float y, vec3 down, float t) {
	float d = u * WIDTH;
	// Open and streaming: out along +X, a travelling ripple growing toward the fly.
	vec3 open = vec3(STICK_R + d * (1.0 - 0.04 * u), y + 0.015 * u * sin(t * 0.7 - u * 3.0),
			0.035 * u * sin(t - u * 7.0 + y * 4.0) + 0.012 * u * sin(t * 1.9 - u * 13.0));
	// Hanging in still air: from the stick, down the way gravity pulls, gathered in soft
	// vertical folds (the cloth is wider than the drop it makes).
	vec3 g = down;
	// Folds lie across the drop; with the stick pointing down the cloth just bunches along it.
	vec3 c = cross(g, vec3(0.0, 1.0, 0.0));
	float spread = length(c);
	vec3 side = c / max(spread, 1e-3);
	// Soft folds running down the drop (two sizes, deeper toward the fly, varying along the
	// stick so they never line up like pleats), and a slow sway as it hangs.
	float folds = 0.034 * sin(d * 17.0 + y * 5.0 + seed) + 0.014 * sin(d * 41.0 - y * 11.0 + seed * 2.3);
	float sway = 0.03 * sin(t * 0.17 + y * 2.0) * u;
	vec3 hang = vec3(STICK_R, y, 0.0) + g * d * 0.8 + vec3(0.06, 0.0, 0.0) * u * spread
			+ side * spread * (folds * smoothstep(0.0, 0.2, u) + sway)
			+ vec3(0.0, 0.0, 0.012) * (1.0 - spread) * sin(a_fold(d, seed));
	vec3 loose = mix(hang, open, smoothstep(0.0, 1.0, air));
	// Furled: wound tight round the stick, a spiral whose turns each add the cloth's thickness:
	// the whole 54 cm makes about five and a half turns, a roll some 4 cm across.
	float r = WOUND_R0 + WOUND_GROW * u;
	float a = WIDTH / WOUND_GROW * log(r / WOUND_R0) + seed;
	vec3 wound = vec3(r * cos(a), y, r * sin(a));
	return mix(wound, loose, furl);
}

void vertex() {
	if (!stick) {
		vec3 down = normalize((inverse(MODEL_MATRIX) * vec4(0.0, -1.0, 0.0, 0.0)).xyz);
		float t = TIME * 9.0 + seed;
		float u = UV.x;
		float y = VERTEX.y;
		vec3 p = cloth_at(u, y, down, t);
		// The surface's normal from its slopes across and up.
		float e = 0.01;
		vec3 du = cloth_at(min(u + e, 1.0), y, down, t) - cloth_at(max(u - e, 0.0), y, down, t);
		vec3 dy = cloth_at(u, y + e, down, t) - cloth_at(u, y - e, down, t);
		vec3 n = cross(du, dy);
		NORMAL = length(n) > 1e-8 ? normalize(n) : vec3(0.0, 0.0, 1.0);
		VERTEX = p;
	}
}

void fragment() {
	ALBEDO = cloth_colour;
	ROUGHNESS = 0.85;
	// Thin white sailcloth glows with the light behind it.
	BACKLIGHT = vec3(backlight);
}
