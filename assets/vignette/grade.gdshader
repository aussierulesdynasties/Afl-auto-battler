shader_type canvas_item;
// The broadcast grade (Features "vignette_grade"): one full-screen pass over a match
// vignette's world - ground, crowd, figures, air - under the names and bars, which draw
// after it. Light only: a contrast curve, a little saturation, a split tone (warm
// highlights, cool shadows) set per weather, a soft edge vignette, a gentle bloom off
// the backbuffer's own mips (one extra tap) and very fine grain.

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform float contrast = 1.12;      // S-curve strength around mid grey
uniform float saturation = 1.08;
uniform vec3 hi_tint = vec3(1.05, 1.0, 0.92);   // multiplies the highlights
uniform vec3 lo_tint = vec3(0.94, 0.98, 1.06);  // multiplies the shadows
uniform float lift = 0.0;           // raises the blacks (flat, overcast look)
uniform float vignette = 0.28;      // edge darkening at the corners
uniform float bloom = 0.18;
uniform float bloom_from = 0.62;    // luma where bloom starts
uniform float grain = 0.025;
uniform float grain_speed = 1.0;    // 0 under Settings > Reduced motion: still grain

float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

float hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

void fragment() {
	vec3 c = textureLod(screen_tex, SCREEN_UV, 0.0).rgb;
	// Bloom: a blurred mip, only what is brighter than bloom_from, added back.
	vec3 b = textureLod(screen_tex, SCREEN_UV, 3.0).rgb;
	vec3 glow = max(b - vec3(bloom_from), vec3(0.0)) / (1.0 - bloom_from);
	c += glow * bloom;
	// Contrast: a smooth S-curve pivoting at 0.5, mixed in by strength.
	vec3 s = c * c * (3.0 - 2.0 * c);
	c = mix(c, clamp(s, 0.0, 1.0), clamp(contrast - 1.0, 0.0, 1.0) * 2.0);
	c = lift + c * (1.0 - lift);
	// Saturation.
	float l = luma(c);
	c = mix(vec3(l), c, saturation);
	// Split tone by luma.
	float w = smoothstep(0.15, 0.85, l);
	c *= mix(lo_tint, hi_tint, w);
	// Edge vignette: an ellipse, soft, the corners darkest.
	vec2 q = SCREEN_UV - 0.5;
	float v = smoothstep(0.35, 0.85, length(q * vec2(1.0, 0.8)) * 1.4);
	c *= 1.0 - vignette * v;
	// Grain: fine, centred, weakest in the highlights.
	float n = hash(FRAGCOORD.xy + floor(TIME * 24.0 * grain_speed) * 17.0) - 0.5;
	c += n * grain * (1.0 - 0.6 * l);
	COLOR = vec4(clamp(c, 0.0, 1.0), 1.0);
}
