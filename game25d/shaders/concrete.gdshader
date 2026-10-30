shader_type spatial;
uniform vec4 base_color: source_color=vec4(0.3,0.33,0.31,1.0);
varying vec3 world_position;
float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p) {
    vec2 i=floor(p);vec2 f=fract(p);f=f*f*(3.0-2.0*f);
    return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
}
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1)).xyz; }
void fragment() {
    vec2 p=world_position.xz;
    float weather=noise(p*0.75)*0.6+noise(p*3.0)*0.25+noise(p*27.0)*0.15;
    float damp=smoothstep(0.48,0.78,noise(p*0.43+vec2(21,9)));
    ALBEDO=base_color.rgb*mix(0.68,1.16,weather)*(1.0-damp*0.24);
    ROUGHNESS=mix(0.9,0.42,damp);
    SPECULAR=0.35;
}
