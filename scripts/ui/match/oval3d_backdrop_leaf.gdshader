// A ground's surroundings (GroundModels.backdrop): the leaf cards of its trees, cut out of their
// texture (alpha below 0.5 is a gap between sprays) and tinted by their vertex colour. A
// StandardMaterial3D with an alpha scissor drew these cards black under the match's light (Mobile
// renderer, Godot 4.7: lit as if in full shade, with or without the sun's shadows; the same cards
// opaque, or through this shader, take the sun). Matte, as the rest of the surroundings' ground.
// One-sided: the background scenes lay each card twice, front and back, with the crown's normal.
shader_type spatial;
render_mode cull_back, shadows_disabled;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic;

void fragment() {
	vec4 t = texture(tex, UV);
	ALBEDO = t.rgb * COLOR.rgb;
	// Mipmaps average a leaf's alpha with the gaps round it, so past a few metres more and more of each
	// spray falls under the cut and the crowns thin to sticks (Traeger QA, 2026-11-22: crowns at 100 m read
	// a third as full as Google Earth's). Raising alpha by the mip level keeps each spray's coverage the
	// same at every distance (Ben Golus, "Anti-aliased Alpha Test", 2017).
	float lod = textureQueryLod(tex, UV).x;
	ALPHA = t.a * (1.0 + max(lod, 0.0) * 0.25);
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}
