// The 3D view's far crowd (row 202 step 2c, Bible 2.92; Oval3DCrowd, beyond 55 m): one supporter
// per instance as a flat card that turns to face the camera (upright, turning only round the
// vertical), cut from an atlas of the 3D supporter drawn from the front (oval3d_crowd_people, mode 1). Columns 0-7 are his idle,
// 8-15 his cheer. The atlas holds which part each pixel is (top red, pants green, skin blue,
// hair and shoes black) times the light, so each card wears its own clothes from one picture.
// INSTANCE_CUSTOM as for the 3D people: x time offset, y side, z clothes seed; w which body.
shader_type spatial;
render_mode skip_vertex_transform, cull_disabled;

uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform float columns = 16.0;
// Atlas rows: one body each; a card's body is its fourth instance number (w).
uniform float bodies = 1.0;
uniform float card_fps = 4.0;
uniform float cheer_dur = 2.0;   // s: the cheer clip's length, over its 8 columns
uniform float now = 0.0;
uniform float cheer_from = -100.0;
uniform float cheer_len = 4.0;
uniform float cheer_side = 0.0;
// The card's size and foot in the body's own metres (the atlas camera's frame).
uniform float card_w = 1.0;
uniform float card_h = 2.0;
uniform float card_y0 = 0.0;
uniform float card_x0 = 0.0;
// The picture stands this far in front of the body's origin (m), toward the camera: a seated
// supporter's knees reach forward over the bench, so a card at his hips hides his legs behind it.
uniform float card_fwd = 0.0;
// The atlas already holds its own light; the stand lights the card again, so lift it back.
uniform float shade_lift = 1.0;
uniform vec4 home_a : source_color;
uniform vec4 home_b : source_color;
uniform vec4 away_a : source_color;
uniform vec4 away_b : source_color;

varying vec3 c_top;
varying vec3 c_bottom;
varying vec3 c_skin;
varying vec3 c_hair;

vec3 lin(vec3 c) { return pow(c, vec3(2.2)); }
float hash(float n) { return fract(sin(n * 12.9898) * 43758.5453); }

void vertex() {
	vec3 o = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float sc = length(MODEL_MATRIX[1].xyz);
	vec3 r = INV_VIEW_MATRIX[0].xyz;
	r = normalize(vec3(r.x, 0.0, r.z));
	vec3 fwd = CAMERA_POSITION_WORLD - o;
	o += normalize(vec3(fwd.x, 0.0, fwd.z)) * card_fwd * sc;
	vec3 w = o + r * (card_x0 + VERTEX.x * card_w) * sc + vec3(0.0, 1.0, 0.0) * (card_y0 + VERTEX.y * card_h) * sc;
	VERTEX = (VIEW_MATRIX * vec4(w, 1.0)).xyz;
	vec3 to_cam = CAMERA_POSITION_WORLD - o;
	to_cam = normalize(vec3(to_cam.x, 0.0, to_cam.z));
	NORMAL = normalize((VIEW_MATRIX * vec4(normalize(to_cam + vec3(0.0, 0.15, 0.0)), 0.0)).xyz);
	vec4 ic = INSTANCE_CUSTOM;
	float fr = mod(floor((now + ic.x * 30.0) * card_fps), 8.0);
	float since = now - cheer_from;
	if (abs(ic.y - cheer_side) < 0.01 && since > 0.0 && since < cheer_len) {
		fr = 8.0 + min(7.0, floor(clamp(since + ic.x * 0.3, 0.0, cheer_dur) / cheer_dur * 8.0));
	}
	float body = min(bodies - 1.0, floor(ic.w * bodies));
	UV = vec2((fr + UV.x) / columns, (body + UV.y) / bodies);
	float s = ic.z * 97.0;
	vec3 plain = lin(mix(vec3(0.12, 0.12, 0.14), vec3(0.62, 0.6, 0.56), hash(s + 1.0)));
	vec3 club_a = ic.y < 0.25 ? home_a.rgb : away_a.rgb;
	vec3 club_b = ic.y < 0.25 ? home_b.rgb : away_b.rgb;
	float h = hash(s);
	bool neutral = abs(ic.y - 0.5) < 0.01;
	c_top = neutral || h > 0.75 ? plain : (h < 0.55 ? club_a : club_b);
	c_bottom = lin(mix(vec3(0.08, 0.08, 0.1), vec3(0.3, 0.32, 0.38), hash(s + 2.0)));
	float sk = hash(s + 3.0);
	c_skin = lin(sk < 0.55 ? vec3(0.85, 0.68, 0.55) : sk < 0.8 ? vec3(0.72, 0.53, 0.4) : sk < 0.92 ? vec3(0.55, 0.38, 0.27) : vec3(0.36, 0.24, 0.17));
	// Hair: dark brown, brown, black, blonde or grey, as the people shader.
	float hh = hash(s + 4.0);
	vec3 hc = hh < 0.3 ? vec3(0.16, 0.1, 0.06) : hh < 0.55 ? vec3(0.32, 0.21, 0.12)
			: hh < 0.75 ? vec3(0.04, 0.035, 0.03) : hh < 0.9 ? vec3(0.62, 0.5, 0.3) : vec3(0.55, 0.53, 0.5);
	c_hair = lin(hc * mix(0.8, 1.15, hash(s + 5.0)));
}

void fragment() {
	vec4 c = texture(atlas, UV);
	// The atlas's empty pixels are black: at a distance its smaller copies mix that black into
	// each edge, so take the colour back out of the coverage.
	c.rgb /= max(c.a, 0.05);
	float s = max(max(c.r, c.g), c.b);
	vec3 base = c_hair * 0.7;
	if (s > 0.03) {
		base = (c.r >= c.g && c.r >= c.b) ? c_top : (c.g >= c.b ? c_bottom : c_skin);
	}
	ALBEDO = base * clamp((s > 0.03 ? s : 0.6) * shade_lift, 0.0, 1.0);
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 0.9;
	SPECULAR = 0.1;
}
