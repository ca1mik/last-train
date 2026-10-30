"""Distance-driven cutout animation using separately authored raster parts."""
import math
import json
import pygame as pg
V=pg.Vector2
PARTS=('body','arm_l','arm_r','leg_l','leg_r','scarf')


class FrameClip:
    """Whole authored poses. One scale for the cycle; no limb warping."""
    def __init__(self,path,columns=4,rows=2,components=False,height=108,reference_height=None,anchor_x=.5):
        sheet=pg.image.load(str(path)).convert_alpha();self.frames=[];self.cache={};self.anchors=[]
        if components:
            pieces=[]
            for component in pg.mask.from_surface(sheet,80).connected_components(3000):
                bounds=component.get_bounding_rects()[0]
                if bounds.h>150 and bounds.w>50:pieces.append((bounds,component))
            if len(pieces)!=columns*rows:raise ValueError('Wrong number of complete character poses')
            pieces.sort(key=lambda v:(v[0].centery//round(sheet.get_height()/rows),v[0].centerx))
            for i,(bounds,component) in enumerate(pieces):
                image=sheet.subsurface(bounds).copy()
                matte=component.to_surface(setcolor=(255,255,255,255),unsetcolor=(0,0,0,0))
                image.blit(matte,(0,0),area=bounds,special_flags=pg.BLEND_RGBA_MULT)
                self.frames.append((image,image.get_rect()))
                self.anchors.append((i%columns+anchor_x)*sheet.get_width()/columns-bounds.left)
        for i in range(columns*rows):
            if components:break
            x0=round(i%columns*sheet.get_width()/columns);x1=round((i%columns+1)*sheet.get_width()/columns)
            y0=round(i//columns*sheet.get_height()/rows);y1=round((i//columns+1)*sheet.get_height()/rows)
            cell=sheet.subsurface((x0,y0,x1-x0,y1-y0));bounds=cell.get_bounding_rect(min_alpha=100)
            if not bounds.w or not bounds.h:raise ValueError('Empty animation frame')
            self.frames.append((cell.copy(),bounds))
            self.anchors.append(cell.get_width()*anchor_x)
        heights=sorted(bounds.h for _,bounds in self.frames);self.factor=height/(reference_height or heights[len(heights)//2])

    def draw(self,target,pos,phase,scale=1,mirror=False,index=None):
        index=int((phase%math.tau)/math.tau*len(self.frames)) if index is None else index
        key=(index,scale,mirror)
        if key not in self.cache:
            source,bounds=self.frames[index];factor=self.factor*scale
            image=pg.transform.smoothscale(source,(round(source.get_width()*factor),round(source.get_height()*factor)))
            if mirror:image=pg.transform.flip(image,True,False)
            anchor=self.anchors[index]*factor
            self.cache[key]=(image,round(bounds.bottom*factor),image.get_width()-anchor if mirror else anchor)
        image,baseline,anchor=self.cache[key]
        target.blit(image,(round(pos[0]-anchor),round(pos[1]-baseline)))


def clip_view(direction):
    d=V(direction)
    if abs(d.x)>abs(d.y)*.85:return 'side'
    return 'back' if d.y<0 else 'front'

def view_for_direction(direction):
    """The game has eight movement directions and two authored body views."""
    d=V(direction)
    return 'back' if d.length_squared() and d.normalize().y<-.35 else 'front'

def foot_motion(phase,direction,stride=40):
    direction=V(direction)
    direction=direction.normalize() if direction.length_squared() else V(0,1)
    u=(phase%math.tau)/math.tau
    if u<.5:
        travel=(.5-2*u)*stride;lift=0.0
    else:
        swing=(u-.5)*2
        travel=(-.5+swing*swing*(3-2*swing))*stride
        lift=math.sin(math.pi*swing)*7
    return direction*travel-V(0,lift),lift

class SpriteRig:
    """Three-by-two atlas. Joint pivots stay fixed while individual limbs move."""
    def __init__(self,path):
        from pathlib import Path
        path=Path(path)
        meta_path=path.with_suffix('.json')
        self.meta=json.loads(meta_path.read_text(encoding='utf-8-sig')) if meta_path.exists() else {}
        sheet=pg.image.load(str(path)).convert_alpha();self.parts={}
        for i,name in enumerate(self.meta.get('parts',PARTS)):
            if name in self.meta.get('regions',{}):rect=self.meta['regions'][name]
            else:
                left=round((i%3)*sheet.get_width()/3);right=round((i%3+1)*sheet.get_width()/3)
                top=round((i//3)*sheet.get_height()/2);bottom=round((i//3+1)*sheet.get_height()/2)
                rect=(left,top,right-left,bottom-top)
            cell=sheet.subsurface(rect)
            if name in self.meta.get('isolate_parts',[]):
                # Atlas gutters may contain the edge of a neighboring limb.
                # Isolate the authored part at load time; leave the source intact.
                component=pg.mask.from_surface(cell,0).connected_component()
                matte=pg.Surface(cell.get_size(),pg.SRCALPHA)
                component.to_surface(matte,setcolor=(255,255,255,255),unsetcolor=(0,0,0,0))
                cell=cell.copy();cell.blit(matte,(0,0),special_flags=pg.BLEND_RGBA_MULT)
            bounds=cell.get_bounding_rect(min_alpha=128)
            if bounds.w<10 or bounds.h<10:raise ValueError('Missing animation part: '+name)
            self.parts[name]=cell.subsurface(bounds).copy()
        self.body_cache={}

    def paint_segment(self,target,source,pivot,tip,start,end,width_factor=None):
        if width_factor is not None:
            natural=(end-start).length()/max(1,(tip-pivot).length())
            squeeze=width_factor/max(.001,natural)
            width=max(1,round(source.get_width()*squeeze))
            actual=width/source.get_width()
            source=pg.transform.smoothscale(source,(width,source.get_height()))
            pivot=V(pivot.x*actual,pivot.y);tip=V(tip.x*actual,tip.y)
        delta=end-start
        axis=tip-pivot;factor=max(.001,delta.length()/max(1,axis.length()))
        angle=-axis.angle_to(delta)
        rotated=pg.transform.rotozoom(source,angle,factor)
        offset=(V(source.get_size())*.5-pivot)*factor
        center=start+offset.rotate(-angle)
        target.blit(rotated,rotated.get_rect(center=(round(center.x),round(center.y))))

    def segment(self,target,name,start,end,scale):
        source=self.parts[name]
        a,b=self.meta.get('anchors',{}).get(name,((.5,0),(.5,1)))
        pivot=V(a[0]*source.get_width(),a[1]*source.get_height())
        tip=V(b[0]*source.get_width(),b[1]*source.get_height())
        ext=self.meta.get('extremities',{}).get(name)
        if ext:
            y0=round(source.get_height()*ext['start'])
            piece=source.subsurface((0,y0,source.get_width(),source.get_height()-y0))
            factor=ext['height']*scale/piece.get_height()
            joint=V(ext['joint'][0]*source.get_width(),ext['joint'][1]*source.get_height())
            joint_target=end+(joint-tip)*factor
            cloth=source.subsurface((0,0,source.get_width(),min(source.get_height(),round(joint.y+source.get_height()*.07))))
            self.paint_segment(target,cloth,pivot,joint,start,joint_target)
            texture=pg.transform.smoothscale(piece,(max(1,round(piece.get_width()*factor)),max(1,round(piece.get_height()*factor))))
            center=end+(V(piece.get_size())*.5+V(0,y0)-tip)*factor
            target.blit(texture,texture.get_rect(center=(round(center.x),round(center.y))))
        else:self.paint_segment(target,source,pivot,tip,start,end)

    def bent_arm(self,target,name,shoulder,hand,scale):
        source=self.parts[name]
        a,b=self.meta.get('anchors',{}).get(name,((.5,0),(.5,1)))
        pivot=V(a[0]*source.get_width(),a[1]*source.get_height())
        tip=V(b[0]*source.get_width(),b[1]*source.get_height())
        source_elbow=pivot.lerp(tip,.5)
        delta=hand-shoulder;distance=delta.length()
        along=delta.normalize() if distance else V(0,1)
        length=max(20.5*scale,distance*.501)
        width_factor=41*scale/max(1,(tip-pivot).length())
        normal=V(-along.y,along.x)
        if normal.y<0:normal=-normal
        elbow=(shoulder+hand)*.5+normal*math.sqrt(max(0,length*length-distance*distance*.25))
        upper_bottom=min(source.get_height(),round(source_elbow.y+source.get_height()*.06))
        self.paint_segment(target,source.subsurface((0,0,source.get_width(),upper_bottom)),pivot,source_elbow,shoulder,elbow,width_factor)
        lower_top=max(0,round(source_elbow.y-source.get_height()*.06))
        ext=self.meta.get('extremities',{}).get(name)
        if ext:
            y0=round(source.get_height()*ext['start'])
            joint=V(ext['joint'][0]*source.get_width(),ext['joint'][1]*source.get_height())
            factor=ext['height']*scale/(source.get_height()-y0)
            joint_target=hand+(joint-tip)*factor
            lower_bottom=min(source.get_height(),round(joint.y+source.get_height()*.07))
            cloth=source.subsurface((0,lower_top,source.get_width(),lower_bottom-lower_top))
            self.paint_segment(target,cloth,source_elbow-V(0,lower_top),joint-V(0,lower_top),elbow,joint_target,width_factor)
            piece=source.subsurface((0,y0,source.get_width(),source.get_height()-y0))
            texture=pg.transform.smoothscale(piece,(max(1,round(piece.get_width()*factor)),max(1,round(piece.get_height()*factor))))
            center=hand+(V(piece.get_size())*.5+V(0,y0)-tip)*factor
            target.blit(texture,texture.get_rect(center=(round(center.x),round(center.y))))
        else:
            lower=source.subsurface((0,lower_top,source.get_width(),source.get_height()-lower_top))
            self.paint_segment(target,lower,source_elbow-V(0,lower_top),tip-V(0,lower_top),elbow,hand,width_factor)

    def draw(self,target,pos,phase,moving,direction,scale=1,time=0,blend=1,arm_blend=None,hand_targets=None,travel_direction=None):
        blend=max(0,min(1,blend));direction=V(direction)
        direction=direction.normalize() if direction.length_squared() else V(0,1)
        mirror=direction.x<0
        if mirror:direction.x*=-1
        gait_direction=V(travel_direction) if travel_direction is not None else V(direction)
        if gait_direction.length_squared():gait_direction.normalize_ip()
        if travel_direction is not None and mirror:gait_direction.x*=-1
        canvas=pg.Surface((round(160*scale),round(160*scale)),pg.SRCALPHA)
        anchor=V(80,118)*scale
        def p(x,y):return anchor+V(x,y)*scale
        bob=abs(math.sin(phase))*1.1*blend+math.sin(time*1.6)*.3*(1-blend)
        feet=[]
        for i,(name,offset) in enumerate((('leg_l',-6),('leg_r',6))):
            motion,lift=foot_motion(phase+i*math.pi,gait_direction);motion*=blend;lift*=blend
            foot=p(offset+motion.x,motion.y);ground=foot+V(0,lift*scale)
            pg.draw.ellipse(canvas,(5,14,19,round(70-lift*4)),(ground.x-8*scale,ground.y-2*scale,16*scale,5*scale))
            feet.append((name,p(offset,-self.meta.get('hip_height',50)-bob),foot))
        for name,hip,foot in sorted(feet,key=lambda v:v[2].y):self.segment(canvas,name,hip,foot,scale)
        for i,(name,shoulder_pos) in enumerate(zip(('arm_l','arm_r'),self.meta.get('shoulders',((-14,-78),(14,-78))))):
            if hand_targets is not None:continue
            x,y=shoulder_pos
            swing=math.sin(phase+i*math.pi)*9*(blend if arm_blend is None else max(0,min(1,arm_blend)))
            self.segment(canvas,name,p(x,y-bob),p(x+(-4 if x<0 else 4)-direction.x*swing,y+41-bob-direction.y*swing),scale)
        hands=[]
        if hand_targets is not None:
            for point in hand_targets:
                local=V(point)-V(pos)
                if mirror:local.x=-local.x
                hands.append(anchor+local)
            x,y=self.meta.get('shoulders',((-14,-78),(14,-78)))[0]
            self.bent_arm(canvas,'arm_l',p(x,y-bob),hands[0],scale)
        if scale not in self.body_cache:
            source=self.parts['body'];height=round(self.meta.get('body_height',68)*scale)
            self.body_cache[scale]=pg.transform.smoothscale(source,(round(source.get_width()*height/source.get_height()),height))
        body=self.body_cache[scale]
        canvas.blit(body,(anchor.x-body.get_width()/2,anchor.y-(self.meta.get('body_top',96)+bob)*scale))
        if hand_targets is not None:
            # Far arm behind the torso, near arm above it. Fixed wrists, moving shoulders.
            x,y=self.meta.get('shoulders',((-14,-78),(14,-78)))[1]
            self.bent_arm(canvas,'arm_r',p(x,y-bob),hands[1],scale)
        if mirror:canvas=pg.transform.flip(canvas,True,False)
        target.blit(canvas,(pos[0]-anchor.x,pos[1]-anchor.y))
