shader_type spatial;
uniform vec4 base_color: source_color=vec4(.3,.33,.31,1);
uniform float tile_size=1.0;
varying vec3 world_position;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p);vec2 f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
void vertex(){world_position=(MODEL_MATRIX*vec4(VERTEX,1)).xyz;}
void fragment(){
    vec2 p=world_position.xz;
    float weather=noise(p*.8)*.7+noise(p*9.)*.3;
    vec3 color=base_color.rgb*mix(.84,1.08,weather);
    if(tile_size>.01){
        vec2 grid=p/tile_size;vec2 edge=min(fract(grid),1.-fract(grid))*tile_size;
        float aa=max(fwidth(p.x),fwidth(p.y));
        float seam=1.-smoothstep(.007,.007+aa,min(edge.x,edge.y));
        color*=mix(.94,1.06,hash(floor(grid)));color=mix(color,color*.48,seam*.65);
    }
    ALBEDO=color;ROUGHNESS=.79;SPECULAR=.3;
}
