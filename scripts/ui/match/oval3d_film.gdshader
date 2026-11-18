// The broadcast film look over the 3D oval (director's pick "A Broadcast film", 2026-11-19).
// A full-screen quad in front of the match camera reads the drawn picture (linear, before
// tone mapping) and redraws it: a slight lens softening, highlights bloom gently, warm highs
// and cool lows, lifted blacks, a faint vignette and fine grain that changes every frame.
shader_type spatial;
render_mode unshaded, fog_disabled, depth_test_disabled, depth_draw_never, cull_disabled;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;

void vertex() {
	POSITION = vec4(VERTEX.xy, 1.0, 1.0);
}

vec3 to_p(vec3 c) { return pow(max(c, vec3(0.0)), vec3(1.0 / 2.2)); }
vec3 to_l(vec3 c) { return pow(max(c, vec3(0.0)), vec3(2.2)); }
float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }

// The tone (rule 2.81) applied here rather than by the environment, so the club rings drawn after
// the film keep their exact colour (Oval3DTurf._tone_to_film hands it over). Godot 4.7's own AgX
// and colour adjustments (tonemap_mobile.glsl, MIT licence), unchanged.
uniform bool tone = false;
uniform float exposure = 1.0;
uniform vec4 awp = vec4(1.0); // the AgX curve: contrast, toe, slope, shoulder
uniform vec3 grade = vec3(1.0); // brightness, contrast, saturation

vec3 allenwp_curve(vec3 x) {
	const float xo = 0.18;
	const float shoulder_max = 1.0 - xo;
	vec3 s = x - xo;
	vec3 slope_s = awp.z * s;
	s = slope_s * (1.0 + s / awp.w) / (1.0 + (slope_s / shoulder_max));
	s += xo;
	vec3 t = pow(x, vec3(awp.x));
	t = t / (t + awp.y);
	return mix(s, t, lessThan(x, vec3(xo)));
}

vec3 linear_to_srgb(vec3 c) {
	c = max(c, vec3(0.0));
	const vec3 a = vec3(0.055);
	return mix((vec3(1.0) + a) * pow(c, vec3(1.0 / 2.4)) - a, 12.92 * c, lessThan(c, vec3(0.0031308)));
}

vec3 srgb_to_linear(vec3 c) {
	c = max(c, vec3(0.0));
	const vec3 a = vec3(0.055);
	return mix(pow((c + a) * (1.0 / (vec3(1.0) + a)), vec3(2.4)), c * (1.0 / 12.92), lessThan(c, vec3(0.04045)));
}

vec3 tone_map(vec3 c) {
	c = max(c * exposure, vec3(0.0));
	const mat3 inset = mat3(
			vec3(0.544814746488245, 0.140416948464053, 0.0888104196149096),
			vec3(0.373787398372697, 0.754137554567394, 0.178871756420858),
			vec3(0.0813978551390581, 0.105445496968552, 0.732317823964232));
	const mat3 outset = mat3(
			vec3(1.96488741169489, -0.299313364904742, -0.164352742528393),
			vec3(-0.855988495690215, 1.32639796461980, -0.238183969428088),
			vec3(-0.108898916004672, -0.0270845997150571, 1.40253671195648));
	c = outset * min(vec3(1.0), allenwp_curve(inset * c));
	c = linear_to_srgb(c * grade.x);
	c = mix(vec3(0.5), c, grade.y);
	c = mix(vec3(dot(vec3(1.0), c) * (1.0 / 3.0)), c, grade.z);
	return srgb_to_linear(c);
}

void fragment() {
	vec2 uv = SCREEN_UV;
	// Picture width / 1080, so the softening and grain keep the same size on every screen.
	float scale = VIEWPORT_SIZE.x / 1080.0;
	float frame = floor(TIME * 30.0);
	vec3 c = texture(screen_tex, uv).rgb;
	// Blur sizes as a share of the picture: a picture half as wide blurs one mip level less.
	float lod = log2(max(scale, 0.01));
	vec3 soft = textureLod(screen_tex, uv, max(1.2 + lod, 0.0)).rgb;
	vec3 bloom = textureLod(screen_tex, uv, max(4.5 + lod, 0.0)).rgb;
	vec3 p = to_p(mix(c, soft, 0.55));
	p += max(to_p(bloom) - 0.62, vec3(0.0)) * 0.55;
	float l = luma(p);
	p += mix(vec3(-0.012, 0.0, 0.02), vec3(0.025, 0.012, -0.02), smoothstep(0.2, 0.8, l));
	p = 0.035 + p * 0.955;
	vec2 v = uv - 0.5;
	p *= 1.0 - 0.22 * dot(v, v) * 1.6;
	// Grain grains are one pixel of a 1080-wide picture: on a smaller picture each pixel holds
	// several, which average out, so the grain is fainter in the same proportion.
	p += (hash(floor(uv * VIEWPORT_SIZE / max(scale, 1.0)) + vec2(frame * 17.13, frame * 3.71)) - 0.5) * 0.035 * min(scale, 1.0);
	vec3 o = to_l(p);
	if (tone) {
		o = tone_map(o);
	}
	ALBEDO = o;
}
