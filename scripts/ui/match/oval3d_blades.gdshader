// Standing blades of grass around the play, for the close camera (Oval3DTurf): one thin
// triangle an instance, scattered over a square round the ball. Each blade keeps its place
// on the ground as the square follows the ball (it wraps to the far side, never slides).
// Coloured like the turf under it (the same day's colours), swaying in the wind, pushed
// flat round the players' boots and the ball.
shader_type spatial;
render_mode cull_disabled, shadows_disabled;

uniform vec2 centre = vec2(0.0);        // the square's centre, ground metres
uniform float span = 16.0;              // the square's side, metres
uniform vec3 grass_a : source_color = vec3(0.16, 0.39, 0.17);
uniform vec3 grass_b : source_color = vec3(0.18, 0.43, 0.19);
uniform float wet = 0.0;
uniform float hot = 0.0;
uniform float wind = 0.0;
uniform vec2 wind_dir = vec2(1.0, 0.0);
uniform vec2 half_size = vec2(86.3, 67.4);
// A traced ground's fence as a Fourier radius (as oval3d_ground.gdshader's fen); fen_n 0: the ellipse.
uniform float fen[33];
uniform int fen_n = 0;
// The boots and the ball: xy where on the ground, z how far they flatten the grass (m).
uniform vec3 pushers[48];
uniform int pusher_count = 0;

varying float tip;
varying vec3 tint;
varying float fade;

float hash1(float n) { return fract(sin(n * 12.9898) * 43758.5453); }

void vertex() {
	// The instance's own spot in the square (custom data x, y; its seed z; every instance's
	// transform is the identity), wrapped to stay within half a span of the centre.
	vec2 off = INSTANCE_CUSTOM.xy;
	vec2 at = off + floor((centre - off) / span + 0.5) * span;
	float seed = INSTANCE_CUSTOM.z;
	tip = clamp(VERTEX.y / 0.07, 0.0, 1.0);
	vec3 v = VERTEX;
	// Turned about its own upright, its own height and lean.
	float yaw = seed * 6.2832;
	v.xz = mat2(vec2(cos(yaw), sin(yaw)), vec2(-sin(yaw), cos(yaw))) * v.xz;
	v.y *= mix(0.7, 1.25, hash1(seed * 7.0)) * (1.0 - 0.25 * hot);
	vec2 bend = vec2(hash1(seed * 3.0) - 0.5, hash1(seed * 5.0) - 0.5) * 0.03;
	// The wind: a sway that runs across the ground in gusts.
	float g = sin(dot(at, wind_dir) * 0.35 - TIME * 3.0) * 0.5 + 0.5;
	bend += wind_dir * (0.008 + wind * 0.035 * g) * sin(TIME * (2.0 + seed) + seed * 9.0);
	// Pushed flat by boots and the ball.
	for (int i = 0; i < pusher_count; i++) {
		vec2 d = at - pushers[i].xy;
		float r = pushers[i].z;
		float k = 1.0 - smoothstep(r * 0.4, r, length(d));
		bend += normalize(d + vec2(1e-4)) * k * 0.06;
		v.y *= 1.0 - 0.55 * k;
	}
	v.xz += bend * tip * tip;
	// Off the ground (outside the boundary the apron's blades are the same; past the fence none).
	float e = length(at / (half_size + 6.0));
	if (fen_n > 0) {
		float l = max(length(at), 1e-4);
		vec2 u = at / l;
		float r = fen[0];
		vec2 cs = u;
		for (int k = 1; 2 * k < fen_n; k++) {
			r += fen[2 * k - 1] * cs.x + fen[2 * k] * cs.y;
			cs = vec2(cs.x * u.x - cs.y * u.y, cs.y * u.x + cs.x * u.y);
		}
		e = l / r;
	}
	float edge = length((at - centre) / (span * 0.5));
	fade = (1.0 - smoothstep(0.7, 1.0, edge)) * step(e, 1.0);
	v *= fade;
	VERTEX = vec3(at.x, 0.0, at.y) + v;
	float hue = hash1(seed * 11.0);
	tint = mix(grass_a, grass_b, hue);
	tint = mix(vec3(dot(tint, vec3(0.3, 0.59, 0.11))), tint, 0.72);
	tint *= hue < 0.08 ? vec3(1.5, 1.2, 0.7) : vec3(0.85 + 0.35 * hash1(seed * 13.0));
	tint = mix(tint, tint * vec3(1.3, 1.2, 0.75), hot * step(0.6, hash1(seed * 17.0)));
}

void fragment() {
	// Lit as the turf is lit (straight up), whichever face is toward the camera: a thin
	// blade's own face would flip dark from behind.
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	vec3 c = tint * mix(0.75, 1.3, tip);
	ALBEDO = pow(c, vec3(2.2));
	// Matte even in the wet: a glinting blade reads as a white fleck, like rain.
	ROUGHNESS = 0.8;
	SPECULAR = 0.05;
}
