// The 3D view's near crowd (row 202 step 2c, Bible 2.92; Oval3DCrowd): one supporter per instance,
// posed from a baked vertex animation table (tools/oval3d/bake_crowd_vat.py, packed into
// assets/oval3d/crowd_set.res by tools/oval3d/build_crowd_set.gd): every frame's vertex positions are a row
// of pos_tex, so thousands of people move with no skeletons. The mesh's UV.x holds each vertex's
// column; its vertex colour says what the vertex is (R top, G pants, B skin, A hair).
// INSTANCE_CUSTOM: x = this person's own time offset (0-1), y = side (0 home, 1 away, 0.5 nobody's),
// z = a seed for clothes and skin, w = which idle clip (0-1).
// mode 0 = in the stand; 1 = drawn into the cards' atlas (row atlas_row of the table).
shader_type spatial;
render_mode cull_back;

uniform sampler2D pos_tex : filter_nearest;
uniform sampler2D nrm_tex : filter_nearest;
uniform float fps = 15.0;
uniform float now = 0.0;
// Idle clips (row, frames) and the cheer (row, frames); n_idle of the four are used.
uniform ivec2 idle0; uniform ivec2 idle1; uniform ivec2 idle2; uniform ivec2 idle3;
uniform int n_idle = 1;
uniform ivec2 cheer;
// A goal: the scoring side's supporters cheer from cheer_from for cheer_len seconds.
uniform float cheer_from = -100.0;
uniform float cheer_len = 4.0;
uniform float cheer_side = 0.0;
uniform vec4 home_a : source_color;
uniform vec4 home_b : source_color;
uniform vec4 away_a : source_color;
uniform vec4 away_b : source_color;
uniform int mode = 0;
uniform int atlas_row = 0;

varying vec4 role;
varying vec3 c_top;
varying vec3 c_bottom;
varying vec3 c_skin;
varying vec3 c_hair;

vec3 lin(vec3 c) { return pow(c, vec3(2.2)); }
float hash(float n) { return fract(sin(n * 12.9898) * 43758.5453); }

vec3 pose(ivec2 clip, float t, bool loop, out vec3 nrm, int vid) {
	float f = t * fps;
	float fr = float(clip.y);
	f = loop ? mod(f, fr) : clamp(f, 0.0, fr - 1.0);
	int a = int(floor(f));
	int b = loop ? (a + 1) % clip.y : min(a + 1, clip.y - 1);
	float k = fract(f);
	vec3 pa = texelFetch(pos_tex, ivec2(vid, clip.x + a), 0).xyz;
	vec3 pb = texelFetch(pos_tex, ivec2(vid, clip.x + b), 0).xyz;
	nrm = normalize(mix(texelFetch(nrm_tex, ivec2(vid, clip.x + a), 0).xyz,
			texelFetch(nrm_tex, ivec2(vid, clip.x + b), 0).xyz, k));
	return mix(pa, pb, k);
}

void vertex() {
	int vid = int(UV.x);
	role = COLOR;
	vec3 n1;
	vec3 p;
	if (mode != 0) {
		p = texelFetch(pos_tex, ivec2(vid, atlas_row), 0).xyz;
		n1 = texelFetch(nrm_tex, ivec2(vid, atlas_row), 0).xyz;
	} else {
		vec4 ic = INSTANCE_CUSTOM;
		int pick = int(floor(ic.w * float(n_idle) * 0.999));
		ivec2 clip = pick == 0 ? idle0 : pick == 1 ? idle1 : pick == 2 ? idle2 : idle3;
		float t = now + ic.x * 30.0;
		p = pose(clip, t, true, n1, vid);
		float since = now - cheer_from;
		if (abs(ic.y - cheer_side) < 0.01 && since > 0.0 && since < cheer_len && cheer.y > 0) {
			// Up out of the idle over a fifth of a second, back down over half a second.
			float w = clamp(since / 0.2, 0.0, 1.0) * clamp((cheer_len - since) / 0.5, 0.0, 1.0);
			vec3 n2;
			vec3 q = pose(cheer, since + ic.x * 0.3, false, n2, vid);
			p = mix(p, q, w);
			n1 = normalize(mix(n1, n2, w));
		}
	}
	VERTEX = p;
	NORMAL = n1;
	// Clothes: a supporter wears his club's colours or everyday clothes; nobody's side wears plain.
	float s = INSTANCE_CUSTOM.z * 97.0;
	vec3 plain = lin(mix(vec3(0.12, 0.12, 0.14), vec3(0.62, 0.6, 0.56), hash(s + 1.0)));
	vec3 club_a = INSTANCE_CUSTOM.y < 0.25 ? home_a.rgb : away_a.rgb;
	vec3 club_b = INSTANCE_CUSTOM.y < 0.25 ? home_b.rgb : away_b.rgb;
	float h = hash(s);
	bool neutral = abs(INSTANCE_CUSTOM.y - 0.5) < 0.01;
	c_top = neutral || h > 0.75 ? plain : (h < 0.55 ? club_a : club_b);
	c_bottom = lin(mix(vec3(0.08, 0.08, 0.1), vec3(0.3, 0.32, 0.38), hash(s + 2.0)));
	float sk = hash(s + 3.0);
	c_skin = lin(sk < 0.55 ? vec3(0.85, 0.68, 0.55) : sk < 0.8 ? vec3(0.72, 0.53, 0.4) : sk < 0.92 ? vec3(0.55, 0.38, 0.27) : vec3(0.36, 0.24, 0.17));
	// Hair: dark brown, brown, black, blonde or grey, each with a little spread of its own.
	float hh = hash(s + 4.0);
	vec3 hc = hh < 0.3 ? vec3(0.16, 0.1, 0.06) : hh < 0.55 ? vec3(0.32, 0.21, 0.12)
			: hh < 0.75 ? vec3(0.04, 0.035, 0.03) : hh < 0.9 ? vec3(0.62, 0.5, 0.3) : vec3(0.55, 0.53, 0.5);
	c_hair = lin(hc * mix(0.8, 1.15, hash(s + 5.0)));
}

void fragment() {
	if (mode == 1) {
		// The card atlas: the part (top red, pants green, skin blue; hair and shoes black) times a
		// simple light from high in front, so one picture carries both (crowd3d_card.gdshader).
		ALBEDO = vec3(0.0);
		SPECULAR = 0.0;
		ROUGHNESS = 1.0;
		vec3 n = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
		float d = clamp(dot(n, normalize(vec3(0.3, 0.8, 0.5))), 0.0, 1.0);
		EMISSION = role.rgb * (0.35 + 0.65 * d);
	} else {
		float none = clamp(1.0 - role.r - role.g - role.b - role.a, 0.0, 1.0);
		ALBEDO = role.r * c_top + role.g * c_bottom + role.b * c_skin + role.a * c_hair
				+ none * lin(vec3(0.1, 0.1, 0.11));
		ROUGHNESS = 0.9;
		SPECULAR = 0.1;
	}
}
