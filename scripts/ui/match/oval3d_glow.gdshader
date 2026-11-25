// A floodlight seen from the ground at night (Oval3DTowers): a bright core with a soft halo
// round it, added over the finished picture (after the broadcast film), always facing the camera. The stands and the roof
// still hide it where they stand in front (depth test kept).
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, fog_disabled, shadows_disabled;

uniform float strength = 1.0;     // 0 off .. 1 a night game
uniform float core = 0.12;        // the core's radius, a share of the quad's half width
uniform float brightness = 1.0;   // the core's brightness, added over the finished picture
uniform float halo_amount = 0.45; // the soft light round it, in the night air
uniform vec3 tint = vec3(0.96, 0.98, 1.0);

void vertex() {
	// Face the camera, keeping the quad's size.
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(
			vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0),
			vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0),
			vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0),
			vec4(0.0, 0.0, 0.0, 1.0));
}

void fragment() {
	float r = length(UV - 0.5) * 2.0;
	float c = 1.0 - smoothstep(core * 0.6, core, r);
	float halo = pow(max(0.0, 1.0 - r), 2.5) * halo_amount;
	ALBEDO = tint * (c * brightness + halo) * strength;
	ALPHA = 1.0;
}
