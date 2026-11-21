// A real player's Tripo head on the body's neck socket (Oval3D.socket_head; row 202, 2d). His own
// texture, and over his neck's bottom 2 cm it blends to the body's skin, so the two meet in one colour:
// by the vertex colour's green where fit_head.py wrote it (skin over the band's bottom 70%), else its red.
// The skin it blends to is the body's own at the ring below (CUSTOM0, Oval3D._ring_skin): his skin colour
// times the MetaHuman map there, and the map's sheen, so the join shows no change of tone or shine.
shader_type spatial;
// Both sides drawn in the band: where his neck's jagged bottom edge (Gawn's beard) is pulled onto the
// socket, a few small triangles fold over and face inward; drawn, they show skin there instead of a slit.
render_mode cull_disabled;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic;
uniform float rough = 0.6;
uniform float sss = 0.0;
uniform vec3 beard_dark : source_color = vec3(0.06, 0.04, 0.03);
instance uniform vec4 skin : source_color = vec4(0.76, 0.57, 0.45, 1.0);
// The stock MetaHuman head's pores and sheen (director 2026-11-19: "Add the pore map"), read at the head's second
// coordinates (UV2: the MetaHuman face layout every head is built on, mh_head_src.py); his own colours stay.
// 0,0 there (the eyeballs) means no map. The normal map is DirectX (green down the image, +v).
uniform sampler2D skin_head_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D skin_head_srmf : filter_linear_mipmap, repeat_disable;

#include "res://scripts/ui/match/oval3d_skin_light.gdshaderinc"

varying float band;
varying float bend;
varying vec4 ring_skin;

void vertex() {
	// Colour by the green alone (the bottom 2 cm): the red is the 6 cm shape band, which at his nape is hair.
	band = COLOR.g;
	bend = max(COLOR.r, COLOR.g);
	ring_skin = CUSTOM0;
}

void fragment() {
	ALBEDO = mix(texture(tex, UV).rgb, skin.rgb * ring_skin.rgb, band);
	float has_maps = step(1e-4, UV2.x + UV2.y);
	float map_rough = mix(rough, texture(skin_head_srmf, UV2).g, has_maps);
	// Above the band a back is the inside of a beard card: its texture there is skin (a pale shard in his
	// beard), so it takes the beard's own dark instead; it still closes the scan's holes.
	ROUGHNESS = mix(map_rough, ring_skin.a, band);
	// The head carries no tangents (its normals are re-aimed in the band), so the map's frame comes from how
	// UV2 runs across the screen (a cotangent frame from the pixel's derivatives).
	if (FRONT_FACING && has_maps > 0.5) {
		vec3 n = normalize(NORMAL);
		vec3 dp1 = dFdx(VERTEX), dp2 = dFdy(VERTEX);
		vec2 du1 = dFdx(UV2), du2 = dFdy(UV2);
		vec3 p2 = cross(dp2, n), p1 = cross(n, dp1);
		vec3 t = p2 * du1.x + p1 * du2.x;
		vec3 b = p2 * du1.y + p1 * du2.y;
		float k = inversesqrt(max(1e-20, max(dot(t, t), dot(b, b))));
		// Godot imports a normal map as two channels (red, green); the third is rebuilt here.
		vec2 mxy = texture(skin_head_nrm, UV2).rg * 2.0 - 1.0;
		vec3 m = vec3(mxy, sqrt(max(0.0, 1.0 - dot(mxy, mxy))));
		NORMAL = normalize(t * k * m.x + b * k * m.y + n * m.z);
	}
	SSS_STRENGTH = sss;
	// His head is skin and hair in one texture: all of it takes the soft skin light; a beard card's back does not.
	skin_wrap = 1.0;
	spec_amt = 0.5;
	if (!FRONT_FACING && bend < 0.5) {
		ALBEDO = beard_dark;
		ROUGHNESS = 1.0;
		SPECULAR = 0.0;
		skin_wrap = 0.0;
		spec_amt = 0.0;
	}
	// A folded triangle seen from behind is lit as if facing out, so it shades like the skin around it.
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
}
