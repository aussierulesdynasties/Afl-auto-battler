// PROTOTYPE: the 3D oval's crowd - one seat per cell, coloured from both clubs and plain
// clothes, a few empty seats. UV.x runs round the ground (160 per lap), UV.y up the stand.
shader_type spatial;
render_mode cull_disabled;

uniform vec4 home_a : source_color;
uniform vec4 home_b : source_color;
uniform vec4 away_a : source_color;
uniform vec4 away_b : source_color;

vec3 lin(vec3 c) { return pow(c, vec3(2.2)); }

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec2 cell = floor(UV * vec2(18.0, 40.0));
	vec2 f = fract(UV * vec2(18.0, 40.0));
	float h = hash(cell);
	float h2 = hash(cell + 17.3);
	vec3 seat = lin(vec3(0.16, 0.17, 0.2));
	vec3 c;
	if (h < 0.22) c = home_a.rgb;
	else if (h < 0.32) c = home_b.rgb;
	else if (h < 0.50) c = away_a.rgb;
	else if (h < 0.58) c = away_b.rgb;
	else if (h < 0.92) c = lin(mix(vec3(0.15, 0.15, 0.17), vec3(0.75, 0.72, 0.68), h2));
	else c = seat;
	// A person is a blob in the middle of the seat; the rest is the seat row.
	float body = step(abs(f.x - 0.5), 0.36) * step(abs(f.y - 0.5), 0.4);
	ALBEDO = mix(seat, c, body);
	ROUGHNESS = 1.0;
}
