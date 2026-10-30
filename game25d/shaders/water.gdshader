shader_type spatial;
render_mode cull_disabled;
varying vec3 world_position;
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
    float ripples=sin(length(fract(world_position.xz*1.8)-0.5)*42.0-TIME*5.0);
    ALBEDO=vec3(0.24,0.30,0.32);
    EMISSION=vec3(0.018,0.025,0.030);
    METALLIC=0.0;
    SPECULAR=0.7;
    ROUGHNESS=0.26+0.025*ripples;
    NORMAL=normalize(NORMAL+vec3(sin(world_position.x*31.0+TIME*2.0)*0.025,0.0,cos(world_position.z*29.0+TIME)*0.025));
}
