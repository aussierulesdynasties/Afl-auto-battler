// PROTOTYPE: the 3D oval's turf and paint, worked out from world metres (Oval3D.gd).
// AFL markings: boundary, centre square (50 m), centre circles (r 5 and 1.5) with the line
// across them, 50 m arcs from the centre of each goal, goal squares (9 m by 6.4 m), goal lines.
shader_type spatial;
render_mode cull_disabled;

uniform vec2 half_size = vec2(86.3, 67.4);
uniform float goal_x = 85.0;
uniform float line_w = 0.12;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float paint(float d, float w) {
	float aa = fwidth(d) * 1.2;
	return 1.0 - smoothstep(w - aa, w + aa, abs(d));
}

vec3 lin(vec3 c) { return pow(c, vec3(2.2)); }

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec2 p = wpos.xz;
	float e = length(p / half_size);
	// Mown stripes across the ground, 12 m apart; the apron outside the boundary darker.
	float stripe = step(0.5, fract(p.x / 12.0));
	vec3 grass = mix(vec3(0.17, 0.42, 0.17), vec3(0.20, 0.48, 0.20), stripe);
	float n = hash(floor(p * 3.0));
	grass *= 0.95 + 0.08 * n;
	vec3 apron = vec3(0.13, 0.33, 0.14);
	vec3 col = e > 1.0 ? apron : grass;

	float ink = 0.0;
	// Boundary: the ellipse's distance, approximately, in metres.
	vec2 g = 2.0 * p / (half_size * half_size);
	float db = (dot(p / half_size, p / half_size) - 1.0) / max(length(g), 1e-4);
	ink = max(ink, paint(db, line_w * 1.4));
	if (e < 1.0) {
		// Centre square.
		float sq = max(abs(p.x), abs(p.y)) - 25.0;
		ink = max(ink, paint(sq, line_w));
		// Centre circles and the line across them.
		float r = length(p);
		ink = max(ink, paint(r - 5.0, line_w));
		ink = max(ink, paint(r - 1.5, line_w));
		if (abs(p.y) < 5.0) ink = max(ink, paint(p.x, line_w));
		// 50 m arcs.
		ink = max(ink, paint(length(p - vec2(goal_x, 0.0)) - 50.0, line_w));
		ink = max(ink, paint(length(p - vec2(-goal_x, 0.0)) - 50.0, line_w));
		// Goal lines (between the behind posts) and goal squares.
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
	col = mix(col, vec3(0.96, 0.96, 0.93), ink);
	ALBEDO = lin(col);
	ROUGHNESS = 0.95;
}
