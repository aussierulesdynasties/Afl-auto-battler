shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;
// The run-through banner's crepe paper (Oval3DBanner): one piece of the printed face per
// instance. INSTANCE_CUSTOM.xy: its corner of the face; .z: 1 while it is still held up, when
// the breeze ripples it; .w: which of its edges are torn (1 left, 2 right, 4 bottom, 8 top) and
// 16 once it lies crumpled on the grass. A torn edge is ragged, never the piece's straight cut;
// crepe shows its fine crinkle, the joins between its strips, and lets light through from behind.

uniform sampler2D face : source_color, filter_linear_mipmap, repeat_disable;
uniform vec2 cells = vec2(40.0, 16.0);
uniform float paper_w = 18.0;
uniform float now = 0.0;
varying vec2 face_uv;
varying vec2 quad_uv;
varying flat float torn;

void vertex() {
	quad_uv = UV;
	face_uv = INSTANCE_CUSTOM.xy + UV / cells;
	torn = INSTANCE_CUSTOM.w;
	float held = INSTANCE_CUSTOM.z;
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	// A held sheet ripples in the breeze, more toward the bottom (the rope holds the top).
	float slack = 1.0 - face_uv.y * 0.6;
	VERTEX.z += held * slack * (0.07 * sin(now * 2.1 + wp.x * 0.7 + wp.y * 0.4) + 0.03 * sin(now * 3.7 - wp.x * 1.9));
}

float hash(float x) {
	return fract(sin(x * 127.1) * 43758.5453);
}

// Smooth noise along an edge, 0..1.
float noise1(float x) {
	float i = floor(x);
	float f = fract(x);
	return mix(hash(i), hash(i + 1.0), f * f * (3.0 - 2.0 * f));
}

// How far in from a torn edge the paper is gone here (a share of the piece).
float bite(float along, float seed) {
	return 0.03 + 0.20 * noise1(along * 9.0 + seed) + 0.08 * noise1(along * 31.0 + seed * 1.7);
}

void fragment() {
	int m = int(round(torn));
	if (m > 0) {
		// Global coordinates along each edge, so the two sides of one tear match up.
		float gx = face_uv.x * cells.x;
		float gy = face_uv.y * cells.y;
		if ((m & 1) != 0 && quad_uv.x < bite(gy, floor(gx + 0.5) * 3.1)) { discard; }
		if ((m & 2) != 0 && 1.0 - quad_uv.x < bite(gy, floor(gx + 0.5) * 3.1)) { discard; }
		if ((m & 4) != 0 && 1.0 - quad_uv.y < bite(gx, floor(gy + 0.5) * 5.3 + 11.0) * 1.3) { discard; }
		if ((m & 8) != 0 && quad_uv.y < bite(gx, floor(gy + 0.5) * 5.3 + 11.0) * 1.3) { discard; }
	}
	vec3 col = texture(face, face_uv).rgb;
	// The crinkle: fine ridges across each strip, faded out where they'd shimmer.
	float v = face_uv.y * cells.y * 24.0;
	float fw = fwidth(v);
	float ridge = sin(v * 6.2832) * clamp(1.0 - fw * 1.5, 0.0, 1.0);
	// The joins: the paper is taped from strips about 0.45 m wide.
	float u = face_uv.x * cells.x;
	float join = smoothstep(0.0, 0.05, abs(fract(u) - 0.5) * 2.0 - 0.9) ;
	col *= 1.0 - 0.10 * join;
	col *= 0.96 + 0.04 * ridge;
	if ((m & 16) != 0) {
		// Crumpled on the grass: the paper's colour, its print lost in the folds.
		vec3 wash = textureLod(face, face_uv, 6.0).rgb;
		float fold = noise1(quad_uv.x * 5.0 + face_uv.y * 40.0) * noise1(quad_uv.y * 4.0 + face_uv.x * 30.0);
		col = wash * (0.7 + 0.35 * fold);
	} else if (!FRONT_FACING) {
		// The back: the print shows through faintly, the paper's colour over it.
		vec3 wash = textureLod(face, face_uv, 6.0).rgb;
		col = mix(wash, col, 0.22) * 0.75;
	}
	ALBEDO = col;
	NORMAL_MAP = normalize(vec3(0.5, 0.5 + 0.18 * ridge, 1.0));
	ROUGHNESS = 0.92;
	SPECULAR = 0.2;
	BACKLIGHT = col * 0.35;
}
