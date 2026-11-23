// A ground model's surfaces in a match (Oval3DTurf.light_stands): the model's own colour, roughness
// and metal, lit as before by the sun, the sky and its reflections, with one change (director,
// 2026-11-21: roof undersides "grey, a faint green tint"). The sky's light map has sunlit grass
// below the horizon, as the centre square sees it; a stand's face turned down sees seats and
// concrete. amb_* is the difference between the sky's light with that grass greyed and with it as
// it is, for a face turned straight down, half down, level, half up and straight up: added to the
// sky's own light it greys what a face took from the grass. A face turned up changes by nothing.
// A model's occlusion map (Optus's bronze) dims the sky's light, the correction included.
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D albedo_tex : source_color, hint_default_white, filter_linear_mipmap, repeat_enable;
uniform bool use_vcol = false;   // the model paints with its vertex colours (Adelaide)
uniform vec4 albedo_col : source_color = vec4(1.0);
uniform float roughness_v = 0.85;
// The model's occlusion map, when it has one (glTF occlusion, red): it dims the sky's light and not the sun's.
uniform bool use_ao = false;
uniform sampler2D ao_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float metallic_v = 0.0;
uniform vec3 uv_scale = vec3(1.0);
uniform vec3 uv_offset = vec3(0.0);
uniform vec3 amb_down = vec3(0.0);
uniform vec3 amb_low = vec3(0.0);
uniform vec3 amb_level = vec3(0.0);
uniform vec3 amb_high = vec3(0.0);
uniform vec3 amb_up = vec3(0.0);
// The sky's reflections are not scaled by the ambient energy as its light is: amb_* x this.
uniform float ref_scale = 1.0;
// A translucent roof membrane's underside (the Gabba's PTFE, a material named "membrane_lit*"): the sun
// shining through it, as its own light, with no grey correction (Oval3DTurf._light_stands sets it from the sun).
uniform vec3 through = vec3(0.0);

vec3 sky_fix(float y) {
	if (y < -0.5) {
		return mix(amb_low, amb_down, (-y - 0.5) * 2.0);
	} else if (y < 0.0) {
		return mix(amb_level, amb_low, -y * 2.0);
	} else if (y < 0.5) {
		return mix(amb_level, amb_high, y * 2.0);
	}
	return mix(amb_high, amb_up, (y - 0.5) * 2.0);
}

void fragment() {
	vec4 a = texture(albedo_tex, UV * uv_scale.xy + uv_offset.xy) * albedo_col;
	if (use_vcol) {
		a.rgb *= COLOR.rgb;
	}
	ALBEDO = a.rgb;
	ROUGHNESS = roughness_v;
	float ao = use_ao ? texture(ao_tex, UV * uv_scale.xy + uv_offset.xy).r : 1.0;
	if (use_ao) {
		AO = ao;
	}
	METALLIC = metallic_v;
	vec3 v = normalize(-VERTEX);
	float n_y = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).y;
	float r_y = (INV_VIEW_MATRIX * vec4(reflect(-v, NORMAL), 0.0)).y;
	// The scattered light, for the face's direction (metal does not scatter).
	vec3 fix = a.rgb * sky_fix(n_y) * (1.0 - metallic_v);
	// The mirrored light, for the direction it mirrors: a face seen at a low angle, or metal,
	// mirrors the grass below as much as it scatters it (Schlick's share, dulled by roughness).
	vec3 f0 = mix(vec3(0.04), a.rgb, metallic_v);
	float nv = clamp(dot(NORMAL, v), 0.0, 1.0);
	// Schlick with roughness, as the renderer's own sky reflection is weighted: a rough face at a grazing angle mirrors
	// far less than a smooth one. The plain Schlick share took out more green than the sky had put in, and a white
	// face seen edge-on (Optus's roof fascia from above) turned purple.
	vec3 f = f0 + (max(vec3(1.0 - roughness_v), f0) - f0) * pow(1.0 - nv, 5.0);
	fix += f * sky_fix(r_y) * ref_scale * (1.0 - roughness_v * 0.6);
	EMISSION = fix * ao + a.rgb * through * step(n_y, 0.0);
}
