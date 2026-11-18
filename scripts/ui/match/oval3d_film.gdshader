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

void fragment() {
	vec2 uv = SCREEN_UV;
	// Picture width / 1080, so the softening and grain keep the same size on every screen.
	float scale = VIEWPORT_SIZE.x / 1080.0;
	float frame = floor(TIME * 30.0);
	vec3 c = texture(screen_tex, uv).rgb;
	vec3 soft = textureLod(screen_tex, uv, 1.2 * scale).rgb;
	vec3 bloom = textureLod(screen_tex, uv, 4.5).rgb;
	vec3 p = to_p(mix(c, soft, 0.55));
	p += max(to_p(bloom) - 0.62, vec3(0.0)) * 0.55;
	float l = luma(p);
	p += mix(vec3(-0.012, 0.0, 0.02), vec3(0.025, 0.012, -0.02), smoothstep(0.2, 0.8, l));
	p = 0.035 + p * 0.955;
	vec2 v = uv - 0.5;
	p *= 1.0 - 0.22 * dot(v, v) * 1.6;
	p += (hash(floor(uv * VIEWPORT_SIZE / max(scale, 1.0)) + vec2(frame * 17.13, frame * 3.71)) - 0.5) * 0.035;
	ALBEDO = to_l(p);
}
