// Soft skin lighting (director 2026-11-19, "yes, get the lighting solved"): the phone renderer has no skin
// scattering, so where skin turns away from the sun the light stops dead and the jaw's underside reads as a hard
// line against the throat. Here the light wraps a little way past the edge on skin: (N.L + w) / (1 + w), so with
// w = 0.3 a spot side-on to the sun gets 23% light instead of 0%. Everything else is Godot's own default lighting
// (Burley diffuse, Schlick-GGX specular; LIGHT_COLOR already carries the PI) copied as it is, so with w = 0 (kit, boots) nothing changes.
// The including shader sets skin_wrap (0 = not skin, 1 = skin) and spec_amt (the material's SPECULAR) in fragment().
uniform float wrap = 0.3;
varying float skin_wrap;
varying float spec_amt;

float _schlick(float u) {
	float m = clamp(1.0 - u, 0.0, 1.0);
	float m2 = m * m;
	return m2 * m2 * m;
}

void light() {
	float w = wrap * skin_wrap;
	float ndl = dot(NORMAL, LIGHT);
	float c_ndl = clamp(ndl, 0.0, 1.0);
	float wrap_ndl = clamp((ndl + w) / (1.0 + w), 0.0, 1.0);
	float c_ndv = clamp(dot(NORMAL, VIEW), 1e-4, 1.0);
	vec3 h = normalize(VIEW + LIGHT);
	float c_ndh = clamp(dot(NORMAL, h), 0.0, 1.0);
	float c_ldh = clamp(dot(LIGHT, h), 0.0, 1.0);
	// Burley diffuse (Godot's default), its N.L term wrapped on skin.
	float fd90m1 = 2.0 * c_ldh * c_ldh * ROUGHNESS - 0.5;
	float fdv = 1.0 + fd90m1 * _schlick(c_ndv);
	float fdl = 1.0 + fd90m1 * _schlick(max(wrap_ndl, c_ndl));
	DIFFUSE_LIGHT += LIGHT_COLOR * ATTENUATION * (1.0 / PI) * fdv * fdl * wrap_ndl;
	// Schlick-GGX specular (Godot's default), on the real N.L only.
	if (c_ndl > 0.0) {
		float a = ROUGHNESS * ROUGHNESS;
		float a2 = a * a;
		float dd = 1.0 + (a2 - 1.0) * c_ndh * c_ndh;
		float d = a2 / (PI * dd * dd);
		float g = 0.5 / mix(2.0 * c_ndl * c_ndv, c_ndl + c_ndv, a);
		float f0 = 0.16 * spec_amt * spec_amt;
		float f90 = clamp(f0 * 50.0, METALLIC, 1.0);
		float f = f0 + (f90 - f0) * _schlick(c_ldh);
		SPECULAR_LIGHT += LIGHT_COLOR * ATTENUATION * SPECULAR_AMOUNT * c_ndl * d * f * g;
	}
}
