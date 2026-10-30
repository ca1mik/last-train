"""Environment, character rig animation and readable letterboxed UI."""
import math
import random
import json
from pathlib import Path
import pygame as pg
from .content import SCENES, DIALOGUES, SCENE_ART
from .carrying import ELEVATION,STRETCHER_WIDTH,stretcher_transform,carrier_grips
from .mechanics import PowerBoard, DELTAS, Winch,RadioTune
from . import chapters,__version__
from .animation import SpriteRig,view_for_direction,FrameClip,clip_view
from . import combat
from . import fieldwork
from . import hospital_action
from .inspection import POINTS as INSPECTION_POINTS,VIEW as INSPECTION_VIEW

SIZE=(1280,720)
INK=(19,30,35)
PALE=(217,224,207)
AMBER=(232,186,117)
MINT=(139,186,167)

class Renderer:
    def __init__(self):
        self.surface=pg.Surface(SIZE,pg.SRCALPHA)
        self.output_scale=1.0;self.native_world=None;self.native_backgrounds={};self.text_calls=[];self.hd_fonts={}
        self.font=pg.font.SysFont('segoeui',22)
        self.small=pg.font.SysFont('segoeui',17)
        self.large=pg.font.SysFont('georgia',55)
        self.title=pg.font.SysFont('georgia',84)
        self.cache={}
        self.inspection_art=None
        inspection_path=Path(__file__).resolve().parent.parent/'assets'/'environments'/'exit-inspection-v01.png'
        if inspection_path.exists():self.inspection_art=pg.image.load(str(inspection_path)).convert()
        self.camera=pg.Vector2()
        self.buttons=[]
        self.button_mode=None
        self.portraits={}
        self.scaled_sprites={}
        self.sprite_sources={}
        self.signal_lever={}
        winch_path=Path(__file__).resolve().parent.parent/'assets'/'props'/'winch-cycle-v32.png'
        self.winch_clip=FrameClip(winch_path,components=True,height=55,reference_height=343) if winch_path.exists() else None
        pair_path=winch_path.parent.parent/'characters'/'artem-winch-pair-v32.png'
        self.winch_work_clip=FrameClip(pair_path,2,4,components=True,height=68,anchor_x=.66) if pair_path.exists() else None
        brace_path=pair_path.with_name('nina-brace-v32.png')
        self.nina_brace=FrameClip(brace_path,1,1,components=True,height=96) if brace_path.exists() else None
        lever_path=Path(__file__).resolve().parent.parent/'assets'/'props'/'signal-lever-v01.png'
        if lever_path.exists():
            sheet=pg.image.load(str(lever_path)).convert_alpha()
            meta=json.loads(lever_path.with_suffix('.json').read_text(encoding='utf-8'))
            factor=meta['scale']
            for name in ('shaft','base'):
                rect=meta[name];part=sheet.subsurface(rect)
                image=pg.transform.smoothscale(part,(round(rect[2]*factor),round(rect[3]*factor)))
                pivot=(pg.Vector2(meta['pivot'])-pg.Vector2(rect[:2]))*factor
                self.signal_lever[name]=(image,pivot)
        self.menu_art=None
        image_path=Path(__file__).resolve().parent.parent/'assets'/'concepts'/'station-v01.png'
        if image_path.exists():
            self.menu_art=pg.transform.smoothscale(pg.image.load(str(image_path)).convert(),SIZE)
        self.hero_idle=None
        self.hero_clips={}
        idle_path=Path(__file__).resolve().parent.parent/'assets'/'characters'/'artem-idle-directions-v28.png'
        self.hero_stances=FrameClip(idle_path,3,1) if idle_path.exists() else None
        enemy_path=idle_path.with_name('trackwalker-move-v28.png')
        self.enemy_clip=FrameClip(enemy_path) if enemy_path.exists() else None
        self.enemy_variants={};self.enemy_actions={};self.brute_actions={}
        for kind,height in (('runner',108),('brute',124)):
            path=idle_path.with_name(kind+('-walk-v31.png' if kind=='brute' else '-move-v31.png'))
            if path.exists():self.enemy_variants[kind]=FrameClip(path,components=kind=='brute',height=height)
            if kind=='runner':
                path=idle_path.with_name('runner-action-v31.png')
                if path.exists():self.enemy_actions[kind]=FrameClip(path,2,2,components=True,height=height,reference_height=503)
        for view in ('front','back','side'):
            path=idle_path.with_name('brute-attack-'+view+'-v31.png')
            if path.exists():
                clip=FrameClip(path,2 if view=='side' else 4,2 if view=='side' else 1,components=True,height=124)
                # Guard pose is the body reference; the raised hook adds height.
                clip.factor=124/clip.frames[0][1].h;self.brute_actions[view]=clip
        attack_path=idle_path.with_name('artem-attack-v28.png')
        self.hero_attack=FrameClip(attack_path,4,3,components=True) if attack_path.exists() else None
        for view in ('front','back','side'):
            path=Path(__file__).resolve().parent.parent/'assets'/'characters'/f'artem-jog-{view}-v28.png'
            if path.exists():self.hero_clips[view]=FrameClip(path)
        self.hero_rig=None
        rig_path=Path(__file__).resolve().parent.parent/'assets'/'characters'/'artem-rig-v01.png'
        if rig_path.exists():self.hero_rig=SpriteRig(rig_path)
        self.hero_back_rig=None
        back_path=rig_path.with_name('artem-back-rig-v01.png')
        if back_path.exists():self.hero_back_rig=SpriteRig(back_path)
        self.hero_walk=[]
        self.npc_sprites={}
        self.npc_rigs={}
        self.npc_back_rigs={}
        for name in ('nina','lida','pavel'):
            npc_rig_path=rig_path.with_name(name+'-rig-v01.png')
            if npc_rig_path.exists():self.npc_rigs[name]=SpriteRig(npc_rig_path)
            npc_back_path=rig_path.with_name(name+'-back-rig-v01.png')
            if npc_back_path.exists():self.npc_back_rigs[name]=SpriteRig(npc_back_path)
        self.patient_sprite=None
        patient_path=Path(__file__).resolve().parent.parent/'assets'/'characters'/'mikhail-stretcher-v01.png'
        if patient_path.exists():
            sheet=pg.image.load(str(patient_path)).convert_alpha()
            frame=sheet.subsurface(sheet.get_bounding_rect(min_alpha=128))
            self.patient_sprite=pg.transform.smoothscale(frame,(STRETCHER_WIDTH,round(frame.get_height()*STRETCHER_WIDTH/frame.get_width())))
            self.sprite_sources[id(self.patient_sprite)]=frame.copy()
        hero_path=Path(__file__).resolve().parent.parent/'assets'/'characters'/'artem-source-v01.png'
        if hero_path.exists():
            sheet=pg.image.load(str(hero_path)).convert_alpha()
            first=sheet.subsurface((0,0,round(sheet.get_width()/8),sheet.get_height()))
            bounds=first.get_bounding_rect(min_alpha=80)
            frame=first.subsurface(bounds)
            self.hero_idle=pg.transform.smoothscale(frame,(round(frame.get_width()*96/frame.get_height()),96))
            self.sprite_sources[id(self.hero_idle)]=frame.copy()
            self.portraits['Артём']=self.portrait(frame)
        walk_path=Path(__file__).resolve().parent.parent/'assets'/'characters'/'artem-walk-v02.png'
        if walk_path.exists():
            sheet=pg.image.load(str(walk_path)).convert_alpha()
            for i in range(4):
                left=round(i*sheet.get_width()/4);right=round((i+1)*sheet.get_width()/4)
                frame=sheet.subsurface((left,0,right-left,sheet.get_height()))
                self.hero_walk.append(pg.transform.smoothscale(frame,(78,104)))
                self.sprite_sources[id(self.hero_walk[-1])]=frame.copy()
        for kind,filename in [('nina','nina-idle-v01.png'),('lida','lida-idle-v01.png'),('enemy','trackwalker-idle-v01.png'),('pavel','pavel-idle-v01.png'),('valentina','valentina-idle-v01.png'),('raisa','raisa-idle-v01.png')]:
            path=Path(__file__).resolve().parent.parent/'assets'/'characters'/filename
            if path.exists():
                sheet=pg.image.load(str(path)).convert_alpha()
                bounds=sheet.get_bounding_rect(min_alpha=128)
                frame=sheet.subsurface(bounds)
                height=108 if kind=='enemy' else 96
                self.npc_sprites[kind]=pg.transform.smoothscale(frame,(round(frame.get_width()*height/frame.get_height()),height))
                self.sprite_sources[id(self.npc_sprites[kind])]=frame.copy()
                if kind in ('nina','lida','pavel','valentina','raisa'):
                    self.portraits[{'nina':'Нина','lida':'Лида','pavel':'Павел','valentina':'Валентина','raisa':'Раиса'}[kind]]=self.portrait(frame)
                    if kind=='raisa':self.portraits['Женщина у кровати']=self.portraits['Раиса']

    def portrait(self,frame):
        crop=frame.subsurface((0,0,frame.get_width(),int(frame.get_height()*.52)))
        ratio=min(155/crop.get_width(),180/crop.get_height())
        return pg.transform.smoothscale(crop,(int(crop.get_width()*ratio),int(crop.get_height()*ratio)))

    def text(self,text,pos,color=PALE,font=None,target=None):
        font=font or self.font
        if self.output_scale>1 and target is None:
            self.text_calls.append((text,tuple(pos),color,font))
        else:(target or self.surface).blit(font.render(text,True,color),pos)

    def render_at(self,app,size):
        """Rasterize world sprites and font glyphs at the actual output size."""
        factor=size[0]/SIZE[0]
        if factor<=1:return pg.transform.smoothscale(self.draw(app),size) if size!=SIZE else self.draw(app)
        self.output_scale=factor;self.text_calls=[]
        self.native_world=pg.Surface(size) if app.mode in ('play','power','winch','radio','gate','brake','inspection') else None
        try:
            canvas=self.draw(app)
            result=self.native_world if self.native_world is not None else pg.Surface(size)
            if self.native_world is None:result.fill((0,0,0))
            result.blit(pg.transform.smoothscale(canvas,size),(0,0))
            fonts={id(self.font):('segoeui',22),id(self.small):('segoeui',17),id(self.large):('georgia',55),id(self.title):('georgia',84)}
            for text,pos,color,font in self.text_calls:
                key=(id(font),factor)
                if key not in self.hd_fonts:
                    family,height=fonts[id(font)];self.hd_fonts[key]=pg.font.SysFont(family,round(height*factor))
                result.blit(self.hd_fonts[key].render(text,True,color),(round(pos[0]*factor),round(pos[1]*factor)))
            return result
        finally:self.output_scale=1;self.native_world=None;self.text_calls=[]

    def wrap(self,text,width,font=None):
        font=font or self.font
        lines=['']
        for word in text.split():
            attempt=(lines[-1]+' '+word).strip()
            if font.size(attempt)[0]>width and lines[-1]:
                lines.append(word)
            else:
                lines[-1]=attempt
        return lines

    def paragraph(self,text,x,y,width,color=PALE,font=None,spacing=32):
        for line in self.wrap(text,width,font):
            self.text(line,(x,y),color,font)
            y+=spacing
        return y

    def button(self,label,x,y,w=340,selected=False,action=None):
        r=pg.Rect(x,y,w,48)
        pg.draw.rect(self.surface,(45,65,65) if selected else (26,43,48),r,border_radius=3)
        pg.draw.line(self.surface,AMBER if selected else (67,91,90),(x,y+47),(x+w,y+47),1)
        self.text(label,(x+18,y+9),AMBER if selected else PALE)
        self.buttons.append((r,action))

    def background(self,key):
        if key in self.cache:
            return self.cache[key]
        scene=SCENES[key]
        s=pg.Surface(scene.size)
        exterior=key=='platform'
        if key in SCENE_ART:
            original=Path(__file__).resolve().parent.parent/'assets'/SCENE_ART[key]
            artwork=pg.image.load(str(original)).convert()
            if scene.art_crop:artwork=artwork.subsurface(scene.art_crop)
            s.blit(pg.transform.smoothscale(artwork,scene.size),(0,0))
            self.cache[key]=s
            return s
        s.fill((34,49,52) if exterior else (36,46,45))
        rng=random.Random(key)
        step=64 if exterior else 48
        for y in range(0,scene.size[1],step):
            for x in range(0,scene.size[0],step):
                c=rng.randrange(-5,6)
                color=(37+c,51+c,52+c) if exterior else (43+c,52+c,48+c)
                pg.draw.rect(s,color,(x+1,y+1,step-2,step-2))
                if rng.random()<.25:
                    pg.draw.line(s,(29,40,41),(x+5,y+10),(x+step-10,y+15),1)
        if exterior:
            for x in (155,325):
                pg.draw.line(s,(110,123,116),(x,0),(x,1120),5)
            for y in range(0,1120,35):
                pg.draw.line(s,(67,66,56),(130,y),(350,y),9)
            # Rain reflections, chipped platform edge and painted safety stripes.
            for _ in range(150):
                x=rng.randrange(470,1850);y=rng.randrange(200,1000)
                pg.draw.line(s,(51,68,69),(x,y),(x+rng.randrange(12,60),y),1)
            pg.draw.line(s,(161,151,111),(470,100),(470,890),5)
            for y in range(120,900,40):
                pg.draw.line(s,(108,112,93),(480,y),(495,y-10),2)
            # Painted train body, roof vents and chassis.
            pg.draw.rect(s,(11,20,25),(85,135,360,720),border_radius=30)
            pg.draw.rect(s,(41,78,73),(65,100,360,700),border_radius=35)
            pg.draw.rect(s,(76,111,96),(80,115,325,650),3,border_radius=30)
            for y in (170,270,370,470,570):
                pg.draw.rect(s,(15,31,36),(100,y,270,60),border_radius=5)
                for x in range(110,365,12):pg.draw.line(s,(62,85,79),(x,y+8),(x,y+50),2)
            for x in (105,265):
                pg.draw.rect(s,(226,179,105),(x,665,100,65),border_radius=6)
                pg.draw.line(s,(88,103,87),(x+50,665),(x+50,730),5)
            for x in (128,330):pg.draw.circle(s,(222,193,132),(x,770),10)
        else:
            for x in range(160,scene.size[0]-100,140):
                pg.draw.rect(s,(27,39,42),(x,120,90,50),border_radius=3)
                pg.draw.rect(s,(65,87,85),(x+5,125,80,40),1)
        for wall in scene.walls:
            r=pg.Rect(wall)
            if exterior and r.x==50 and r.y==100:
                continue
            pg.draw.rect(s,(14,24,28),r.move(10,15),border_radius=3)
            pg.draw.rect(s,(63,77,74),r,border_radius=3)
            pg.draw.line(s,(102,115,105),r.topleft,r.topright,3)
            for _ in range(max(2,r.w*r.h//4500)):
                x=rng.randrange(r.left,max(r.left+1,r.right-3));y=rng.randrange(r.top,max(r.top+1,r.bottom-3))
                pg.draw.line(s,(54,68,66),(x,y),(min(x+13,r.right),y),1)
        for obj in scene.objects:
            if key=='signal_post' and obj.id=='lever':continue
            self.prop(s,obj)
        self.cache[key]=s
        return s

    def prop(self,s,obj):
        x,y=obj.pos;k=obj.kind
        if k in ('lida','nina','patient','pavel','valentina','raisa','train'):
            return
        pg.draw.ellipse(s,(18,29,31),(x-26,y+8,60,17))
        if k in ('door','window'):
            pg.draw.rect(s,(19,32,36),(x-35,y-48,70,74),border_radius=3)
            pg.draw.rect(s,(103,118,105),(x-35,y-48,70,74),3,border_radius=3)
            pg.draw.rect(s,(72,101,98),(x-23,y-35,46,30))
            pg.draw.circle(s,AMBER,(x+21,y+8),3)
        elif k in ('console','relay','cabinet'):
            pg.draw.rect(s,(22,35,37),(x-45,y-35,90,65),border_radius=5)
            pg.draw.rect(s,(91,109,99),(x-45,y-35,90,65),2,border_radius=5)
            for dx in (-22,8):
                pg.draw.circle(s,(191,185,145),(x+dx,y-12),11)
                pg.draw.line(s,(27,40,43),(x+dx,y-12),(x+dx+4,y-20),2)
            pg.draw.rect(s,(155,69,52),(x+25,y+4,7,15))
        elif k=='bench':
            pg.draw.rect(s,(39,36,30),(x-65,y-22,130,50),border_radius=3)
            for dy in (-20,-7,6):pg.draw.rect(s,(123,111,77),(x-62,y+dy,124,9),border_radius=2)
        elif k in ('sign','map','paper'):
            pg.draw.rect(s,(45,59,57),(x-40,y-40,80,65),border_radius=3)
            pg.draw.rect(s,(185,183,147),(x-32,y-32,64,49))
            for dy in range(-22,15,9):pg.draw.line(s,(91,113,103),(x-23,y+dy),(x+22,y+dy),2)
        elif k=='bell':
            pg.draw.rect(s,(94,71,45),(x-5,y-26,10,30),border_radius=3)
            pg.draw.polygon(s,AMBER,[(x-18,y+13),(x-11,y-8),(x+11,y-8),(x+18,y+13)])
        elif k=='signal':
            pg.draw.line(s,(95,108,98),(x,y+30),(x,y-75),6)
            pg.draw.rect(s,(16,26,31),(x-15,y-80,30,58),border_radius=12)
            pg.draw.circle(s,(225,86,61),(x,y-65),8)
        elif k=='tool':
            pg.draw.line(s,(156,170,160),(x-19,y+5),(x+19,y-10),9)
            pg.draw.line(s,AMBER,(x+13,y-13),(x+23,y-7),9)
        elif k=='boot':
            pg.draw.ellipse(s,(78,110,101),(x-14,y+6,39,10))
            pg.draw.polygon(s,(142,94,62),[(x-8,y-20),(x+5,y-20),(x+4,y-2),(x+15,y+2),(x+15,y+10),(x-9,y+10)])
        elif k=='radio':
            pg.draw.rect(s,(26,38,39),(x-25,y-18,50,40),border_radius=4)
            for dx in range(-15,18,5):pg.draw.line(s,(104,119,102),(x+dx,y-9),(x+dx,y+7),1)
        elif k=='tea':
            for dx in (-16,16):
                pg.draw.ellipse(s,(178,178,148),(x+dx-8,y-9,16,24))
                pg.draw.ellipse(s,(87,59,37),(x+dx-6,y-9,12,7))

    def actor(self,pos,kind='artem',phase=0,moving=False,facing=(0,1),hurt=False,target=None,scale=1,rotation=0,time=0,blend=1,arm_blend=None,hand_targets=None,attack_phase=None,travel_direction=None,enemy_state=None,enemy_timer=0):
        if self.native_world is not None and target is None:
            factor=self.output_scale
            target=self.native_world;pos=pg.Vector2(pos)*factor;scale*=factor
            if hand_targets is not None:hand_targets=tuple(pg.Vector2(p)*factor for p in hand_targets)
        s=target or self.surface
        x,y=pos
        if kind=='work_artem' and self.winch_work_clip is not None:
            self.winch_work_clip.draw(s,pos,phase,scale);return
        if kind=='nina_brace' and self.nina_brace is not None:
            self.nina_brace.draw(s,pos,0,scale);return
        if kind.startswith('enemy_'):
            variant=kind[6:];clip=self.enemy_variants.get(variant,self.enemy_clip)
            action=self.brute_actions.get(clip_view(facing)) if variant=='brute' else self.enemy_actions.get(variant)
            if action is not None and enemy_state in ('windup','charge','recover'):
                if variant=='runner':index=(0 if enemy_timer>.38 else 1) if enemy_state=='windup' else 2 if enemy_state=='charge' else 3
                else:
                    view=clip_view(facing);column=0 if enemy_state=='windup' and enemy_timer>.4 else 1 if enemy_state=='windup' else 2 if enemy_timer>combat.SPECS['brute']['recovery']-.15 else 3
                    index=column
                action.draw(s,pos,0,scale,facing[0]<0,index);return
            if clip is not None:
                clip.draw(s,pos,phase if moving else 0,scale,facing[0]<0);return
            kind='enemy'
        if kind=='artem' and attack_phase is not None and hand_targets is None and self.hero_attack is not None:
            view=clip_view(facing);index=('front','back','side').index(view)*4+min(3,int(attack_phase*4))
            self.hero_attack.draw(s,pos,0,scale,view=='side' and facing[0]<0,index)
            return
        if kind=='enemy' and moving and self.enemy_clip is not None:
            self.enemy_clip.draw(s,pos,phase,scale,facing[0]<0)
            return
        if kind=='artem' and moving and hand_targets is None and self.hero_clips:
            view=clip_view(facing);self.hero_clips[view].draw(s,pos,phase,scale,view=='side' and facing[0]<0)
            return
        if kind=='artem' and hand_targets is None and self.hero_stances is not None:
            view=clip_view(facing)
            self.hero_stances.draw(s,pos,0,scale,view=='side' and facing[0]<0,('front','back','side').index(view))
            return
        if kind in self.npc_rigs:
            rig=self.npc_back_rigs.get(kind,self.npc_rigs[kind]) if view_for_direction(facing)=='back' else self.npc_rigs[kind]
            rig.draw(s,pos,phase,moving,facing,scale,time,blend if moving else 0,arm_blend,hand_targets,travel_direction)
            return
        if kind=='artem' and self.hero_rig is not None:
            rig=self.hero_back_rig if self.hero_back_rig is not None and view_for_direction(facing)=='back' else self.hero_rig
            rig.draw(s,pos,phase,moving,facing,scale,time,blend,arm_blend,hand_targets,travel_direction)
            return
        if kind in ('patient','carry_patient') and self.patient_sprite is not None:
            image=self.scale_sprite(self.patient_sprite,scale)
            flip,rotation=stretcher_transform(rotation)
            if flip:image=pg.transform.flip(image,True,False)
            if rotation:image=pg.transform.rotozoom(image,rotation,1)
            if kind=='carry_patient':y-=ELEVATION*scale
            s.blit(image,(x-image.get_width()/2,y-image.get_height()/2))
            return
        if kind in self.npc_sprites:
            image=self.npc_sprites[kind]
            image=self.scale_sprite(image,scale)
            pg.draw.ellipse(s,(12,22,25),(x-22,y-5,44,12))
            s.blit(image,(x-image.get_width()/2,y-image.get_height()))
            return
        if kind=='artem' and self.hero_idle is not None:
            walking=moving and bool(self.hero_walk)
            image=self.hero_walk[int((phase%(math.tau))/math.tau*len(self.hero_walk))] if walking else self.hero_idle
            image=self.scale_sprite(image,scale)
            if facing[0]<0:image=pg.transform.flip(image,True,False)
            pg.draw.ellipse(s,(12,22,25),(x-22,y-5,44,12))
            s.blit(image,(x-image.get_width()/2,y-(101*scale if walking else image.get_height())))
            return
        # This temporary articulated rig is replaced by authored raster clips as they pass QA.
        coat={'artem':(53,68,70),'nina':(168,130,65),'lida':(83,113,86),'enemy':(51,61,64),'pavel':(108,105,74),'valentina':(75,110,108),'raisa':(64,84,108)}[kind]
        skin=(178,152,122) if kind!='enemy' else (46,54,53)
        stride=math.sin(phase)*9 if moving else 0
        bob=abs(math.cos(phase))*2 if moving else math.sin(phase*.5)*.8
        def p(dx,dy):return (round(x+dx*scale),round(y+dy*scale))
        def line(c,a,b,w):pg.draw.line(s,c,p(*a),p(*b),max(1,int(w*scale)))
        pg.draw.ellipse(s,(10,20,24),(x-18*scale,y-5*scale,37*scale,15*scale))
        line((27,36,39),(-6,-12),(-7+stride*.4,-1+stride*.35),9)
        line((27,36,39),(6,-12),(7-stride*.4,-1-stride*.35),9)
        polygon=[p(-14,-40+bob),p(10,-42+bob),p(15,-12),p(-14,-10)]
        if kind=='enemy':polygon=[p(-11,-48+bob),p(8,-50+bob),p(19,-5),p(-16,-5)]
        pg.draw.polygon(s,(181,103,87) if hurt else coat,polygon)
        line(tuple(min(255,c+20) for c in coat),(-11,-39+bob),(-13,-15-stride*.3),6)
        line(tuple(max(0,c-12) for c in coat),(11,-38+bob),(16,-16+stride*.3),6)
        pg.draw.circle(s,skin,p(0,-50+bob),max(2,int(10*scale)))
        pg.draw.ellipse(s,(76,79,70) if kind=='artem' else (189,183,155) if kind=='lida' else (62,49,38),
                        (x-10*scale,y+(-61+bob)*scale,20*scale,9*scale))
        if kind=='artem':
            line((146,67,60),(-8,-41+bob),(8,-42+bob),5)
            line((131,59,53),(5,-40+bob),(10,-25+bob),5)
            line((120,104,75),(-11,-38+bob),(11,-13),2)
            pg.draw.rect(s,(106,88,58),(*p(6,-22),13*scale,15*scale),border_radius=2)
        elif kind=='enemy':
            line((164,180,157),(-13,-29+bob),(13,-29+bob),4)
        elif kind=='lida':
            pg.draw.rect(s,(118,93,59),(*p(11,-17),18*scale,14*scale),border_radius=3)
        if kind=='nina':
            line((196,189,150),(14,-28),(18,-10),7)

    def scale_sprite(self,image,scale):
        if scale==1:return image
        key=(id(image),scale)
        if key not in self.scaled_sprites:
            self.scaled_sprites[key]=pg.transform.smoothscale(self.sprite_sources.get(id(image),image),(round(image.get_width()*scale),round(image.get_height()*scale)))
        return self.scaled_sprites[key]

    def camera_for(self,scene,pos):
        width,height=SCENES[scene].size
        self.camera.x=max(0,min(width-1280,pos[0]-640)) if width>=1280 else (width-1280)/2
        # Keep the back-wall controls visible on entering this control room.
        vertical_anchor=620 if scene=='signal_post' else 580 if scene in ('carriage','flat','ward','workshop','archive','power','shed') else 500 if scene in ('dispatch','upper_platform','refuge') else 340
        self.camera.y=max(-50,min(height-720,pos[1]-vertical_anchor)) if height>=720 else (height-720)/2

    def world(self,app):
        st=app.state;scene=SCENES[st.scene];self.camera_for(st.scene,st.pos)
        cam=self.camera;s=self.surface
        if self.native_world is None:s.fill((11,21,26));s.blit(self.background(st.scene),-cam)
        else:
            s.fill((0,0,0,0));factor=self.output_scale;key=(st.scene,factor)
            if key not in self.native_backgrounds:
                self.native_backgrounds.clear()
                if st.scene in SCENE_ART:
                    path=Path(__file__).resolve().parent.parent/'assets'/SCENE_ART[st.scene]
                    source=pg.image.load(str(path)).convert()
                    if scene.art_crop:source=source.subsurface(scene.art_crop)
                else:source=self.background(st.scene)
                self.native_backgrounds[key]=pg.transform.smoothscale(source,(round(scene.size[0]*factor),round(scene.size[1]*factor)))
            self.native_world.fill((11,21,26));self.native_world.blit(self.native_backgrounds[key],-cam*factor)
        if st.scene=='signal_post':self.signal_equipment(app)
        self.return_hazard(app)
        self.enemy_telegraphs(app)
        winch_deployed=hospital_action.deployed(st,app.field_task)
        work_stroke=getattr(app,'winch_stroke',0)
        pair_work=(winch_deployed and self.winch_work_clip is not None and not app.moving and app.attack_time<=0
                   and pg.Vector2(hospital_action.work_position(st)).distance_to(st.pos)<8
                   and (work_stroke>0 or app.field_task is not None and app.field_task.kind in hospital_action.WORK_KINDS))
        if winch_deployed:
            machine=pg.Vector2(hospital_action.positions(st)[0])
            target=self.native_world if self.native_world is not None else s
            anchor=next(o.pos for o in scene.objects if o.id=='switch')
            pg.draw.line(target,(29,34,34),(machine+pg.Vector2(-8,-35)-cam)*self.output_scale,(pg.Vector2(anchor)+pg.Vector2(0,30)-cam)*self.output_scale,max(2,round(4*self.output_scale)))
            pg.draw.line(target,(143,146,133),(machine+pg.Vector2(-8,-35)-cam)*self.output_scale,(pg.Vector2(anchor)+pg.Vector2(0,30)-cam)*self.output_scale,max(1,round(2*self.output_scale)))
            support=pg.Vector2(hospital_action.positions(st)[1])
            pg.draw.line(target,(143,146,133),(support+pg.Vector2(34,-54)-cam)*self.output_scale,(machine+pg.Vector2(-8,-35)-cam)*self.output_scale,max(1,round(2*self.output_scale)))
            if self.winch_clip is not None and not pair_work:
                stroke=getattr(app,'winch_stroke',0);phase=(1-stroke/.4)*math.tau if stroke>0 else 0
                target=self.native_world if self.native_world is not None else s
                self.winch_clip.draw(target,(machine-cam)*self.output_scale,phase,scene.actor_scale*self.output_scale,index=6 if stroke<=0 else None)
        entities=[]
        for o in scene.objects:
            if o.requires and o.requires not in st.flags:continue
            if o.kind in ('lida','nina','patient','pavel','valentina','raisa'):
                if winch_deployed and o.kind=='nina':continue
                if st.carrying and o.kind=='lida':continue
                if st.scene=='carriage' and st.chapter==2 and 'c2_arrived' in st.flags and 'c2_boarded' not in st.flags and o.kind=='lida':continue
                if st.scene=='refuge' and o.kind=='raisa' and 'c2_boarded' in st.flags:continue
                if st.scene=='platform' and o.kind=='lida' and 'lida_boarded' in st.flags:continue
                if st.scene=='ward' and o.kind=='patient' and (st.carrying or 'rescued' in st.flags):continue
                if st.scene=='ward' and o.kind=='nina' and 'relay_nina' in st.flags:continue
                entities.append((o.pos[1],o.pos,o.kind,0))
        entities.append((st.pos[1],st.pos,'player',0))
        if winch_deployed:
            support=pg.Vector2(hospital_action.positions(st)[1])
            entities.append((support.y,support,'nina',0))
        for e in app.enemies:entities.append((e.pos.y,e.pos,'enemy',0))
        carry_hands={};carry_direction=app.facing
        if st.carrying:
            center,rear,angle=app.carry_positions()
            entities.append((rear.y,rear,'lida',0))
            carry_direction=pg.Vector2(st.pos)-rear
            if not carry_direction.length_squared():carry_direction=app.facing
            scale=scene.actor_scale
            self.actor(center-cam,'carry_patient',scale=scale,rotation=angle)
            if self.patient_sprite is not None:
                image=self.scale_sprite(self.patient_sprite,scale)
                front_hands,rear_hands=carrier_grips(center,image.get_size(),scale,angle,st.pos,rear)
                carry_hands={'player':tuple(p-cam for p in front_hands),'lida':tuple(p-cam for p in rear_hands)}
        for _,pos,kind,angle in sorted(entities,key=lambda q:q[0]):
            if kind=='player':
                working=app.field_task is not None and app.field_task.kind=='relay'
                phase=(1-work_stroke/.4)*math.tau if work_stroke>0 else 0
                self.actor(pg.Vector2(pos)-cam,'work_artem' if pair_work else 'artem',phase=phase if pair_work else app.walk_phase,moving=app.moving,facing=carry_direction if st.carrying else app.attack_direction if app.attack_time>0 else app.facing,hurt=app.hurt>0,scale=scene.actor_scale,time=app.time,blend=app.move_blend,arm_blend=0 if st.carrying else None,hand_targets=carry_hands.get('player'),attack_phase=1-app.attack_time/.4 if app.attack_time>0 else .4 if working else None,travel_direction=app.facing if st.carrying else None)
            else:
                assisting=st.carrying and kind=='lida'
                enemy=next((e for e in app.enemies if e.pos is pos),None) if kind=='enemy' else None
                facing=carry_direction if assisting else pg.Vector2(st.pos)-pg.Vector2(pos) if pg.Vector2(pos).distance_to(st.pos)<180 else (0,1)
                if enemy is not None:facing=enemy.facing
                if winch_deployed and kind=='nina':facing=(1,0)
                actor_kind='enemy_'+enemy.kind if enemy is not None and enemy.kind!='walker' else kind
                if winch_deployed and kind=='nina' and self.nina_brace is not None:actor_kind='nina_brace'
                self.actor(pg.Vector2(pos)-cam,actor_kind,phase=app.rear_walk_phase if assisting else enemy.walk_phase if enemy is not None else app.time*3,
                           moving=app.rear_moving if assisting else enemy.moving if enemy is not None else False,scale=scene.actor_scale,
                           rotation=angle,time=app.time,arm_blend=0 if assisting else None,
                           facing=facing,hand_targets=carry_hands.get(kind),travel_direction=app.rear_direction if assisting else None,
                           enemy_state=enemy.attack_state if enemy is not None else None,enemy_timer=enemy.attack_timer if enemy is not None else 0)
        shade=pg.Surface(SIZE,pg.SRCALPHA);shade.fill((4,12,23,20 if st.scene in SCENE_ART else 100))
        lights=list(scene.lights)+[(st.pos[0],st.pos[1]-20,140,(182,191,158))]
        for x,y,r,color in ([] if st.scene in SCENE_ART else lights):
            center=pg.Vector2(x,y)-cam
            for radius,alpha in [(r,70),(r*.75,40),(r*.45,8)]:
                pg.draw.circle(shade,(5,14,20,alpha),center,int(radius))
        if app.flare_time>0:
            radius=230 if app.reduced_flash else 250+int(math.sin(app.time*15)*20)
            pg.draw.circle(shade,(90,38,22,30 if app.reduced_flash else 15),pg.Vector2(st.pos)-cam,radius)
        s.blit(shade,(0,0))
        if st.scene=='platform':
            rng=random.Random(71)
            for _ in range(120):
                x=(rng.randrange(1280)+app.time*75)%1280;y=(rng.randrange(720)+app.time*490)%720
                pg.draw.line(s,(87,111,116),(x,y),(x-5,y+15),1)
        for ring in app.rings:
            radius=ring[1]
            pg.draw.circle(s,(139,163,151),pg.Vector2(ring[0])-cam,int(radius),1)
        for enemy in app.enemies:
            if 'action_mode' in st.flags:
                p=enemy.pos-cam
                color=(139,190,183) if enemy.kind=='runner' else (223,177,103) if enemy.kind=='brute' else (204,116,89)
                pg.draw.rect(s,(35,26,28),(p.x-24,p.y+15,48,5))
                pg.draw.rect(s,color,(p.x-24,p.y+15,48*enemy.health/enemy.spec['health'],5))
                self.text(enemy.spec['name'],(p.x-30,p.y+24),color,self.small)
                if enemy.hit_flash>0:pg.draw.circle(s,(245,218,170),p-pg.Vector2(0,45),18,3)
        if app.attack_time>0:
            p=pg.Vector2(st.pos)-cam-pg.Vector2(0,38*scene.actor_scale)
            angle=math.atan2(-app.attack_direction.y,app.attack_direction.x)
            progress=max(0,min(1,(.4-app.attack_time)/.23))
            radius=60*scene.actor_scale
            pg.draw.arc(s,(240,204,143),(p.x-radius,p.y-radius*.45,radius*2,radius*.9),angle-.8,angle-.8+progress*1.6,4)
        for point,life in app.hit_sparks:
            p=point-cam-pg.Vector2(0,38*scene.actor_scale)
            for angle in range(0,360,60):
                delta=pg.Vector2(1,0).rotate(angle)
                pg.draw.line(s,(248,212,158),p+delta*8,p+delta*(8+(1-life/.18)*27),2)
        target=app.nearby()
        if target and not st.dialogue and not (app.field_task is not None and app.field_task.kind=='c2_rhythm'):
            x,y=pg.Vector2(target.pos)-cam
            label=target.label
            if target.kind=='raisa' and {'c2_address','c2_beds','c2_card_written'}&st.flags:label='Раиса'
            text='E  '+label
            kind=fieldwork.task_kind(st,target.id)
            if kind is not None:text=('E  ' if kind=='c2_rhythm' else 'Удерживать E  ')+fieldwork.TASKS[kind][3]
            w=self.small.size(text)[0]+24
            pg.draw.rect(s,(17,30,35),(x-w/2,y+20,w,31),border_radius=3)
            self.text(text,(x-w/2+12,y+25),AMBER,self.small)
        if app.field_task is not None:
            task=app.field_task;point=pg.Vector2(task.target)-cam
            if task.kind=='c2_rhythm':
                bar=pg.Rect(point.x-160,point.y+170,320,14)
                pg.draw.rect(s,INK,bar.inflate(20,68),border_radius=5)
                pg.draw.rect(s,(55,69,69),bar,border_radius=3)
                lo,hi=hospital_action.BEAT_WINDOW
                pg.draw.rect(s,MINT,(bar.x+bar.w*lo,bar.y,bar.w*(hi-lo),bar.h),border_radius=2)
                cursor=bar.x+bar.w*hospital_action.beat_phase(task)
                pg.draw.line(s,PALE,(cursor,bar.y-5),(cursor,bar.bottom+5),3)
                self.text(f'E на светлой метке   {st.winch["turns"]}/4',(bar.x,bar.y-28),AMBER,self.small)
            else:
                progress=max(0,min(1,task.progress/task.duration))
                pg.draw.rect(s,(12,26,30),(point.x-75,point.y+59,150,9),border_radius=3)
                pg.draw.rect(s,AMBER,(point.x-75,point.y+59,150*progress,9),border_radius=3)
        # Letterbox and quiet quest HUD.
        pg.draw.rect(s,(13,24,29),(0,0,1280,76))
        self.text('ПОСЛЕДНИЙ РЕЙС',(28,15),MINT,self.small)
        self.text(scene.title,(28,40),PALE,self.small)
        self.paragraph(st.objective(),360,21,885,color=AMBER,font=self.font,spacing=25)
        pg.draw.rect(s,(13,24,29),(0,677,1280,43))
        self.text('WASD  ход   Shift  бег   ЛКМ / F  удар   Пробел / ПКМ  рывок   E  действие   Q  ракета',(26,690),(142,161,158),self.small)
        self.text(f'Здоровье {int(st.health)}   /   Ракеты {st.flares}',(1030,690),PALE,self.small)
        if not st.carrying:
            self.text('Рывок',(885,690),MINT,self.small)
            pg.draw.rect(s,(46,65,66),(948,700,64,5),border_radius=2)
            pg.draw.rect(s,AMBER if app.dash_cooldown<=0 else MINT,(948,700,64*(1-min(1,app.dash_cooldown/.7)),5),border_radius=2)
        if st.notice_time>0:
            lines=self.wrap(st.notice,1020,self.small)
            r=pg.Rect(110,600-len(lines)*24,1060,len(lines)*24+22)
            pg.draw.rect(s,(20,35,39),r,border_radius=4)
            for i,line in enumerate(lines):self.text(line,(130,r.y+10+i*24),AMBER,self.small)

    def enemy_telegraphs(self,app):
        factor=self.output_scale;target=self.native_world if self.native_world is not None else self.surface
        layer=pg.Surface(target.get_size(),pg.SRCALPHA)
        def p(world):return (pg.Vector2(world)-self.camera)*factor
        for enemy in app.enemies:
            if enemy.attack_state not in ('windup','charge'):continue
            color=(139,211,202) if enemy.kind=='runner' else (235,171,93)
            if enemy.kind=='runner':
                origin=p(enemy.attack_origin);end=p(enemy.strike);normal=pg.Vector2(-enemy.attack_direction.y,enemy.attack_direction.x)*38*factor
                points=(origin-normal,end-normal,end+normal,origin+normal)
                pg.draw.polygon(layer,(*color,45 if enemy.attack_state=='windup' else 90),points)
                pg.draw.lines(layer,(*color,200),True,points,max(1,round(2*factor)))
                tip=end;back=end-enemy.attack_direction*20*factor
                pg.draw.lines(layer,(*color,240),False,(back-normal*.3,tip,back+normal*.3),max(1,round(2*factor)))
            elif enemy.kind=='brute':
                center=p(enemy.pos);angle=enemy.attack_direction.as_polar()[1]
                points=[center]+[center+pg.Vector2(combat.SWEEP_RADIUS,0).rotate(angle+a)*factor for a in range(-75,76,10)]+[center+pg.Vector2(combat.SWEEP_RADIUS,0).rotate(angle+75)*factor]
                pg.draw.polygon(layer,(*color,42),points);pg.draw.lines(layer,(*color,210),True,points,max(1,round(2*factor)))
            else:
                point=p(enemy.strike);pg.draw.circle(layer,(*color,220),point,round(42*factor),max(1,round(2*factor)))
        target.blit(layer,(0,0))

    def return_hazard(self,app):
        if not fieldwork.cable_present(app.state):return
        factor=self.output_scale;target=self.native_world if self.native_world is not None else self.surface
        phase=fieldwork.cable_phase(app.state.elapsed);zone=fieldwork.CABLE
        size=(round((zone.w+40)*factor),round((zone.h+40)*factor))
        fx=pg.Surface(size,pg.SRCALPHA)
        def p(x,y):return (round(x*factor),round(y*factor))
        color=(232,180,102) if phase=='warning' else (169,220,237) if phase=='live' else (110,129,124)
        if phase!='safe':
            pg.draw.rect(fx,(*color,45 if phase=='warning' else 80),(*p(20,20),round(zone.w*factor),round(zone.h*factor)),border_radius=round(12*factor))
            pg.draw.rect(fx,(*color,180),(*p(20,20),round(zone.w*factor),round(zone.h*factor)),max(1,round(2*factor)),border_radius=round(12*factor))
        points=[p(12,70),p(38,63),p(55,75),p(78,68),p(92,78),p(120,70),p(145,82)]
        pg.draw.lines(fx,(22,32,33,255),False,points,max(2,round(5*factor)))
        pg.draw.lines(fx,(*color,255),False,points,max(1,round(factor)))
        if phase=='live':
            for i in range(5):
                x=32+i*22;y=40+math.sin(app.time*24+i)*15
                pg.draw.lines(fx,(220,247,249,255),False,[p(x,70),p(x+8,y),p(x+14,64)],max(1,round(2*factor)))
        target.blit(fx,(pg.Vector2(zone.topleft)-self.camera-pg.Vector2(20,20))*factor)

    def dialogue(self,app):
        st=app.state;data=DIALOGUES[st.dialogue];s=self.surface
        if combat.moving_dialogue(st):
            speaker,text=data['lines'][st.line]
            panel=pg.Rect(740,90,510,132)
            pg.draw.rect(s,(13,26,32,238),panel,border_radius=5)
            self.text(speaker,(755,100),AMBER,self.small)
            self.paragraph(text,755,128,478,font=self.small,spacing=23)
            return
        panel=pg.Rect(70,425,1140,235)
        pg.draw.rect(s,(13,26,32),panel,border_radius=5)
        pg.draw.line(s,(106,139,127),(92,426),(1188,426),2)
        if st.line<len(data['lines']):
            speaker,text=data['lines'][st.line]
            portrait=self.portraits.get(speaker.split(' · ')[0])
            x=285 if portrait is not None else 105
            if portrait is not None:
                self.surface.blit(portrait,(100+(155-portrait.get_width())//2,455))
            self.text(speaker or '•',(x,447),AMBER,self.font)
            self.paragraph(text,x,488,1175-x,font=self.font)
            self.text('Enter / E / пробел — дальше',(920,623),(142,162,156),self.small)
        else:
            self.text('Что сделать?',(105,446),AMBER)
            for i,(label,_) in enumerate(data.get('choices',[])):
                if st.dialogue=='c3_letters' and ('c3_letter_early','c3_letter_middle','c3_letter_late')[i] in st.flags:
                    label+=' (прочитано)'
                if st.dialogue=='c4_questions' and ('c4_account_known','c4_account_search','c4_account_after')[i] in st.flags:
                    label+=' (обсудили)'
                self.button(f'{i+1}. {label}',100,484+i*51,1080,app.choice==i,('choice',i))

    def menu(self,app):
        s=self.surface
        self.world(app)
        if app.mode=='menu' and self.menu_art is not None:
            s.blit(self.menu_art,(0,0))
        veil=pg.Surface(SIZE,pg.SRCALPHA);veil.fill((7,17,24,220));s.blit(veil,(0,0))
        self.buttons=[]
        if app.mode=='menu':
            self.text('ПОСЛЕДНИЙ',(105,110),PALE,self.title)
            self.text('РЕЙС',(105,195),AMBER,self.title)
            self.paragraph('Выйти на станцию. Пробиться к людям. Вернуться к поезду.',110,305,510,color=MINT)
            self.button('Новый рейс',110,425,420,app.selection==0,'new')
            self.button('Продолжить',110,483,420,app.selection==1,'load')
            self.button('Настройки',110,541,420,app.selection==2,'settings')
            self.button('Выйти',110,599,420,app.selection==3,'quit')
            self.text(f'Главы 1–{max(chapters.INFO)} • рабочая версия '+'.'.join(__version__.split('.')[:2]),(850,650),(135,155,151),self.small)
        elif app.mode=='confirm_new':
            self.text('Начать заново?',(170,175),PALE,self.large)
            self.paragraph('Текущая контрольная точка будет заменена после начала новой истории.',175,265,850)
            self.button('Начать новую историю',175,380,470,app.selection==0,'confirm_new')
            self.button('Вернуться',175,440,470,app.selection==1,'menu')
        elif app.mode=='pause':
            self.text('Остановка',(160,155),PALE,self.large)
            minutes=int(app.state.elapsed)//60
            self.text(f'Активная игра: {minutes//60}:{minutes%60:02d}',(165,225),MINT,self.small)
            for i,(label,action) in enumerate([('Продолжить','resume'),('Сохранить','save'),('Настройки','settings'),('В главное меню','menu')]):
                self.button(label,165,280+i*60,450,app.selection==i,action)
        elif app.mode=='settings':
            self.text('Настройки',(160,130),PALE,self.large)
            labels=[f'Громкость: {int(app.audio.volume*100)}%',
                    'Полный экран: '+('да' if app.fullscreen else 'нет'),
                    'Мягкие вспышки: '+('да' if app.reduced_flash else 'нет'),
                    'Вернуться']
            for i,label in enumerate(labels):self.button(label,165,250+i*65,650,app.selection==i,('setting',i))
            self.text('Громкость: ← / → или нажатие. F11 переключает полный экран.',(165,550),MINT,self.small)
            self.text(f'Вывод мира и текста: {app.display.get_width()} × {app.display.get_height()} • по размеру окна',(165,590),MINT,self.small)
        elif app.mode=='journal':
            self.text('Записи в дороге',(110,100),PALE,self.large)
            y=200
            all_entries=list(reversed(app.state.journal()))
            pages=max(1,(len(all_entries)+3)//4)
            app.journal_page=max(0,min(pages-1,app.journal_page))
            entries=all_entries[app.journal_page*4:(app.journal_page+1)*4]
            if not entries:self.text('Пока здесь только чистая бумага.',(115,y),MINT)
            for title,body in entries:
                self.text(title,(115,y),AMBER);y+=32
                y=self.paragraph(body,115,y,1030,font=self.small,spacing=24)+22
            self.text(f'← / → / колесо мыши — страницы   •   {app.journal_page+1}/{pages}   •   J / Esc — закрыть',(115,650),MINT,self.small)
        elif app.mode=='dead':
            self.text('Темнота ближе',(160,180),PALE,self.large)
            self.paragraph('Путевой услышал вас. Попробуйте отвлечь его звонком или сигнальной ракетой. Бежать рядом с ним опасно.',165,280,900)
            self.button('С контрольной точки',165,420,510,app.selection==0,'retry')
            self.button('В меню',165,485,510,app.selection==1,'menu')
        elif app.mode=='chapter_end':
            info=chapters.INFO[app.state.chapter]
            self.text(info['title'],(120,140),PALE,self.large)
            self.paragraph(chapters.chapter5.result(app.state) if app.state.chapter==5 else info['result'],125,240,1000)
            self.paragraph('Дорога продолжается.' if info['next'] else 'Конец рейса. Спасибо за прохождение.',125,330,1000,color=MINT)
            if info['next']:
                self.button(info['next_label'],125,440,500,app.selection==0,'next_chapter')
                self.button('Вернуться в вагон',125,500,500,app.selection==1,'resume')
                self.button('В главное меню',125,560,500,app.selection==2,'menu')
            else:
                self.button('Выбрать последний маршрут заново',125,430,560,app.selection==0,'replay_route')
                self.button('Осмотреть место завершения',125,495,560,app.selection==1,'resume')
                self.button('В главное меню',125,560,560,app.selection==2,'menu')
        if app.menu_notice:
            self.paragraph(app.menu_notice,720,480,450,AMBER,self.small,26)

    def draw(self,app):
        self.buttons=[]
        if app.mode=='play':
            self.world(app)
            if app.state.dialogue:self.dialogue(app)
        elif app.mode=='crossing':
            self.crossing_scene(app)
        elif app.mode=='drive':
            self.drive(app)
        elif app.mode in ('power','winch','radio','gate','brake','inspection'):
            self.world(app)
            self.puzzle(app)
        else:self.menu(app)
        self.button_mode=app.mode
        return self.surface

    def crossing_scene(self,app):
        s=self.surface
        s.blit(pg.transform.smoothscale(self.background('crossing'),SIZE),(0,0))
        sequence=app.crossing_sequence
        if sequence is not None:
            cast=sequence.actors();positions={kind:pg.Vector2(pos[0]*1280/1536,pos[1]*720/1024) for kind,pos,_,_ in cast}
            center=positions['carry_patient'];scale=.9
            self.actor(center,'carry_patient',scale=scale)
            hands={}
            if self.patient_sprite is not None:
                image=self.scale_sprite(self.patient_sprite,scale)
                front,rear=carrier_grips(center,image.get_size(),scale,0,positions['lida'],positions['artem'])
                hands={'lida':front,'artem':rear}
            for kind,pos,distance,moving in cast:
                if kind=='carry_patient':continue
                p=(pos[0]*1280/1536,pos[1]*720/1024)
                self.actor(p,kind,phase=distance*(1280/1536)/(40*.9)*math.pi,moving=moving,
                           facing=(1,0),scale=.9,time=app.time,blend=1 if moving else 0,
                           arm_blend=0 if kind in ('lida','artem') else None,hand_targets=hands.get(kind))
        pg.draw.rect(s,INK,(0,0,1280,76));pg.draw.rect(s,INK,(0,677,1280,43))
        self.text('ПОСЛЕДНИЙ ПРОШЁЛ',(28,18),MINT,self.font)
        self.text('Нина проверяет путь • Лида и Артём несут Михаила • Павел замыкает',(28,47),PALE,self.small)
        self.text('Esc — пауза. При выходе переход начнётся с последней контрольной точки.',(28,691),MINT,self.small)

    def puzzle(self,app):
        s=self.surface;st=app.state
        veil=pg.Surface(SIZE,pg.SRCALPHA);veil.fill((4,14,22,180));s.blit(veil,(0,0))
        pg.draw.rect(s,(19,35,40),(65,90,1150,580),border_radius=6)
        if app.mode=='inspection':
            self.inspection_panel(app)
            return
        if app.mode=='brake':
            self.brake_panel(app)
            return
        if app.mode=='gate':
            self.gate_panel(app)
            return
        if app.mode=='radio':
            self.radio_panel(app)
            return
        if app.mode=='power':
            self.text('Два контура',(100,110),PALE,self.large)
            self.text('Проверка без нагрузки • генератор остаётся на резерве',(105,180),MINT,self.small)
            fed=PowerBoard.powered(st.power,'c2_cable' in st.flags)
            for i in range(20):
                x=125+(i%5)*104;y=245+(i//5)*76
                r=pg.Rect(x,y,91,65)
                selected=i==app.puzzle_selected
                pg.draw.rect(s,(39,59,61) if i in PowerBoard.sockets else (23,39,43),r,border_radius=4)
                pg.draw.rect(s,AMBER if selected else (76,99,93),r,2 if selected else 1,border_radius=4)
                center=pg.Vector2(r.center)
                color=MINT if i in fed else (91,115,111)
                for port in PowerBoard.ports(i,st.power):
                    dx,dy=DELTAS[port]
                    pg.draw.line(s,color,center,center+pg.Vector2(dx*43,dy*30),5)
                if i in PowerBoard.sockets:pg.draw.circle(s,color,center,7)
                if i not in PowerBoard.fixed and i in PowerBoard.sockets:
                    self.buttons.append((r,('tile',i)))
                if i==PowerBoard.source:self.text('ВВОД',(x,y-22),AMBER,self.small)
                if i==PowerBoard.hospital:self.text('УБЕЖИЩЕ',(x+105,y+18),MINT if i in fed else PALE,self.small)
                if i==PowerBoard.gate:self.text('СТРЕЛКА',(x+105,y+18),MINT if i in fed else PALE,self.small)
            if 'c2_cable' not in st.flags:
                x=125+2*104+45;y=245+3*76
                pg.draw.line(s,(188,96,77),(x-12,y-11),(x+12,y-4),3)
                self.text('Разрыв',(x-30,y-36),(223,138,107),self.small)
            self.paragraph('Соедините ввод с обоими выходами. Свет убежища должен сохраниться.',810,245,350,color=PALE)
            self.paragraph('Перемычка: '+('найдена и подключена' if 'c2_cable' in st.flags else 'нужна бухта со склада'),810,345,350,color=AMBER,font=self.small,spacing=26)
            self.paragraph('← ↑ ↓ → — выбрать узел\nE / пробел — повернуть'.replace('\n',' • '),810,410,350,color=MINT,font=self.small,spacing=26)
            self.button('Проверить  [Enter]',105,555,330,False,'test_power')
            self.button('Сбросить  [R]',455,555,275,False,'reset_power')
            self.button('Отойти  [Esc]',755,555,330,False,'close_puzzle')
        else:
            self.text('Ручной перевод',(100,110),PALE,self.large)
            self.paragraph('Нина держит страховочный трос. Сначала нагрузите рукоятку, затем освободите собачку.',105,185,1060,color=MINT)
            center=pg.Vector2(365,390);angle=st.winch['turns']*math.pi/2
            pg.draw.circle(s,(95,117,111),center,90,8)
            for a in range(4):
                d=pg.Vector2(math.cos(angle+a*math.pi/2),math.sin(angle+a*math.pi/2))*85
                pg.draw.line(s,(108,128,115),center,center+d,8)
            knob=center+pg.Vector2(math.cos(angle),math.sin(angle))*85
            pg.draw.circle(s,AMBER,knob,12)
            pg.draw.line(s,(161,153,117),(448,370),(700,370),5)
            pg.draw.rect(s,(90,109,102),(670,335,50,90),border_radius=4)
            stage=st.winch['stage']
            texts={'load':'1. Натяните трос рукояткой.', 'release':'2. Освободите собачку.',
                   'turn':f'3. Переведите стрелку: {st.winch["turns"]}/{Winch.required_turns}.',
                   'lock':'4. Зафиксируйте замок.'}
            self.paragraph(texts[stage],790,310,340,color=AMBER)
            self.paragraph('При неверном действии механизм остаётся на месте. Не нужно угадывать темп.',790,390,340,color=MINT,font=self.small,spacing=26)
            self.button('Рукоятка  [E]',105,555,330,False,'winch_crank')
            self.button('Собачка / замок  [пробел]',455,555,380,False,'winch_pawl')
            self.button('Отойти  [Esc]',855,555,270,False,'close_puzzle')
        if st.notice:
            self.paragraph(st.notice,105,615,1040,color=AMBER,font=self.small,spacing=23)

    def inspection_panel(self,app):
        s=self.surface;view=pg.Rect(INSPECTION_VIEW);f=app.state.flags
        self.text('Выход из состава',(100,110),PALE,self.large)
        self.text('Осмотрите три участка. Решите, можно ли выходить. Esc — отойти.',(105,180),MINT,self.small)
        if self.inspection_art is not None:s.blit(pg.transform.smoothscale(self.inspection_art,view.size),view)
        selected=INSPECTION_POINTS[app.inspection_selected]
        focus=pg.Vector2(selected[2][0]*view.w/1536,selected[2][1]*view.h/1024)
        shade=pg.Surface(view.size,pg.SRCALPHA);shade.fill((4,14,20,135))
        pg.draw.circle(shade,(4,14,20,0),focus,115);s.blit(shade,view)
        pg.draw.rect(s,(82,112,104),view,1)
        for i,(key,label,pos,_) in enumerate(INSPECTION_POINTS):
            point=pg.Vector2(view.x+pos[0]*view.w/1536,view.y+pos[1]*view.h/1024)
            color=MINT if 'c1_inspected_'+key in f else AMBER
            pg.draw.circle(s,INK,point,19);pg.draw.circle(s,color,point,20,2)
            self.text(str(i+1),point-pg.Vector2(6,12),color,self.font)
            self.button(('✓ ' if 'c1_inspected_'+key in f else '')+f'{i+1}. {label}',790,235+i*62,390,False,'inspect_'+key)
        self.paragraph(app.state.notice or 'Мышь или 1–3 — осмотреть. Стрелки — направить свет, E — проверить участок.',790,435,385,font=self.small,spacing=23)
        self.button('Спуститься к рельсам',790,555,390,False,'inspect_rails')
        self.button('Подать к платформе [Enter]',790,615,390,False,'inspect_platform')

    def brake_panel(self,app):
        s=self.surface;b=app.state.brake
        self.text('Проверка тормозов',(100,110),PALE,self.large)
        self.text('Нина проверяет хвостовой вагон. Артём сверяет показания.',(105,180),MINT,self.small)
        for x,key,label,limit in ((320,'line','Магистраль',6),(630,'cylinder','Цилиндр',4)):
            center=pg.Vector2(x,350)
            pg.draw.circle(s,(12,26,32),center,101)
            pg.draw.circle(s,(109,139,127),center,100,3)
            for i in range(limit+1):
                angle=math.radians(135+270*i/limit)
                unit=pg.Vector2(math.cos(angle),math.sin(angle))
                pg.draw.line(s,PALE,center+unit*79,center+unit*91,2)
                position=center+unit*64
                self.text(str(i),position-pg.Vector2(5,9),PALE,self.small)
            angle=math.radians(135+270*b[key]/limit)
            tip=center+pg.Vector2(math.cos(angle),math.sin(angle))*73
            pg.draw.line(s,AMBER,center,tip,4);pg.draw.circle(s,AMBER,center,7)
            self.text(label,(x-74,220),MINT,self.font)
            self.text(f'{b[key]:.1f} бар',(x-43,460),PALE,self.font)
        steps={'charge':('1 / Зарядка','Включите компрессор [1], зарядите магистраль [2]. При 5 бар подтвердите показания [Enter].'),
               'apply':('2 / Торможение','Переведите рукоятку на торможение [3]. Цилиндр должен подняться к 3 бар, магистраль — снизиться.'),
               'release':('3 / Отпуск','Отпустите тормоз [4]. Цилиндр — к нулю, магистраль — снова к 5 бар. Подтвердите [Enter].'),
               'done':('Проверено','Проверка закончена.')}
        title,text=steps[b['stage']]
        self.text(title,(850,245),AMBER,self.font)
        self.paragraph(text,850,288,315,color=PALE,font=self.small,spacing=25)
        self.text('Компрессор: '+('вкл.' if b['compressor'] else 'выкл.'),(850,415),MINT,self.small)
        self.text('Рукоятка: '+{'hold':'перекрыша','charge':'зарядка','apply':'торможение','release':'отпуск'}[b['valve']],(850,445),MINT,self.small)
        self.paragraph(app.state.notice or 'Каждый этап подтвердите только после изменения показаний.',105,505,1080,font=self.small)
        for label,x,action in [('Компрессор [1]',105,'compressor'),('Зарядить [2]',315,'charge'),('Тормозить [3]',525,'apply'),('Отпустить [4]',735,'release'),('Проверить [Enter]',945,'observe')]:
            self.button(label,x,560,200 if x<945 else 240,False,'brake_'+action)
        self.button('Перекрыть [пробел]',105,615,260,False,'brake_hold')
        self.text('Esc — отойти. Показания и выполненные этапы сохраняются.',(395,631),MINT,self.small)

    def signal_equipment(self,app):
        target=1.0 if 'c5_semaphore' in app.state.flags else 0.0
        if getattr(self,'signal_session',None)!=id(app.state):
            self.signal_session=id(app.state);self.signal_visual=target;self.signal_time=app.time
        dt=max(0,min(.1,app.time-self.signal_time));self.signal_time=app.time
        self.signal_visual+=(target-self.signal_visual)*(1-math.exp(-4*dt))
        lever=next(o for o in SCENES['signal_post'].objects if o.id=='lever')
        base=pg.Vector2(lever.pos)+pg.Vector2(0,-90)-self.camera
        angle=45-90*self.signal_visual
        if self.signal_lever:
            for name in ('shaft','base'):
                image,pivot=self.signal_lever[name]
                rotation=angle if name=='shaft' else 0
                rotated=pg.transform.rotozoom(image,rotation,1)
                center=base+(pg.Vector2(image.get_size())*.5-pivot).rotate(-rotation)
                self.surface.blit(rotated,rotated.get_rect(center=center))
        else:
            tip=base+pg.Vector2(0,-105).rotate(-angle)
            pg.draw.line(self.surface,(152,162,140),base,tip,8)
            pg.draw.circle(self.surface,AMBER,tip,9)
            pg.draw.circle(self.surface,(39,56,57),base,14)
        self.text('ОТКРЫТ' if target else 'ЗАКРЫТ',base+pg.Vector2(-43,28),MINT if target else AMBER,self.small)
        lamp=base+pg.Vector2(70,-170)
        pg.draw.rect(self.surface,(34,43,44),(lamp.x-19,lamp.y-29,38,58),border_radius=6)
        pg.draw.rect(self.surface,(93,105,100),(lamp.x-19,lamp.y-29,38,58),1,border_radius=6)
        for y in (-23,23):pg.draw.circle(self.surface,(125,128,113),lamp+pg.Vector2(0,y),2)
        pg.draw.circle(self.surface,(11,22,24),lamp,15)
        color=(137,196,153) if target else (205,113,85)
        for radius in range(12,0,-1):
            light=.45+.55*(1-radius/12)
            pg.draw.circle(self.surface,tuple(round(c*light) for c in color),lamp,radius)
        pg.draw.circle(self.surface,tuple(min(255,c+35) for c in color),lamp+pg.Vector2(-3,-4),3)

    def gate_panel(self,app):
        s=self.surface;f=app.state.flags
        self.text('Вес створки',(100,110),PALE,self.large)
        self.paragraph('Павел разгружает петлю. Артём освобождает штырь и проверяет упор.',105,184,1000,color=MINT,font=self.small)
        target=1.0 if 'c5_gate_swung' in f else 0.0
        pin_target=1.0 if 'c5_pin_out' in f else 0.0
        signature=id(app.state)
        if getattr(self,'gate_session',None)!=signature:
            self.gate_session=signature;self.gate_visual=target;self.pin_visual=pin_target;self.gate_time=app.time
        dt=max(0,min(.1,app.time-self.gate_time));self.gate_time=app.time
        self.gate_visual+=(target-self.gate_visual)*(1-math.exp(-5*dt))
        self.pin_visual+=(pin_target-self.pin_visual)*(1-math.exp(-9*dt))
        # An engineering close-up: the pin lifts clear before the leaf can swing.
        hinge=pg.Vector2(245,460);angle=self.gate_visual*1.25
        end=hinge+pg.Vector2(390*math.cos(angle),-100*math.sin(angle))
        pg.draw.line(s,(68,89,88),(150,486),(750,486),4)
        pg.draw.rect(s,(83,102,99),(226,250,36,237),border_radius=3)
        lift=7 if 'c5_gate_supported' in f else 0
        for offset in (0,-135):
            pg.draw.line(s,(143,158,145),hinge+pg.Vector2(0,offset-lift),end+pg.Vector2(0,offset-lift),10)
        for i in range(1,9):
            p=hinge.lerp(end,i/9)-pg.Vector2(0,lift)
            pg.draw.line(s,(104,125,118),p,p-pg.Vector2(0,135),5)
        pg.draw.circle(s,AMBER,hinge-pg.Vector2(0,60),12,3)
        pin=pg.Vector2(632,390-95*self.pin_visual-lift)
        pg.draw.line(s,AMBER,pin,pin+pg.Vector2(0,60),8)
        pg.draw.circle(s,AMBER,pin,10,3)
        pg.draw.rect(s,MINT if 'c5_gate_swung' in f else (64,87,84),(345,476,52,10),border_radius=3)
        labels=[('c5_gate_supported','Вес снят'),('c5_pin_out','Штырь свободен'),('c5_gate_swung','Створка на упоре')]
        for i,(flag,label) in enumerate(labels):
            self.text(('● ' if flag in f else '○ ')+label,(800,280+i*58),MINT if flag in f else PALE,self.font)
        self.paragraph(app.state.notice or 'Осмотрите петлю и договоритесь с Павлом.',105,500,1050,font=self.small)
        for label,x,action in [('Павел: держать [1]',105,'support'),('Вынуть штырь [2]',380,'pin'),('Открыть [3]',655,'swing'),('Проверить [Enter]',930,'confirm')]:
            self.button(label,x,560,255,False,'gate_'+action)
        self.text('Esc — отойти; выполненные действия сохранятся.',(105,635),MINT,self.small)

    def radio_panel(self,app):
        s=self.surface;st=app.state
        self.text('Живой ответ',(100,110),PALE,self.large)
        connected='c3_repair' in st.flags and st.line_power
        self.text('Линия подключена' if connected else 'Линия без приёма — проверьте ввод и разъединитель',(105,180),MINT,self.small)
        q=RadioTune.quality(st.radio) if connected else 0
        pg.draw.rect(s,(12,27,33),(105,225,665,140),border_radius=4)
        for y in range(245,360,25):pg.draw.line(s,(32,53,55),(115,y),(760,y),1)
        points=[]
        for x in range(115,760,3):
            t=x*.045
            noise=math.sin(t*5.7+app.time*14)*math.sin(t*2.3-app.time*9)
            wave=math.sin(t+app.time*2)
            points.append((x,295+wave*q*32+noise*(1-q)*47))
        pg.draw.lines(s,MINT if q>.94 else (112,146,137),False,points,2)
        self.text('Полезный сигнал',(805,235),PALE)
        pg.draw.rect(s,(42,58,58),(810,278,340,14),border_radius=4)
        pg.draw.rect(s,MINT,(810,278,round(q*340),14),border_radius=4)
        quality_text='Голос различим' if q>.94 else 'Слова тонут в помехах' if q>.68 else 'Гул и треск'
        self.text(quality_text,(810,303),MINT,self.small)
        labels=('Диапазон','Подстройка','Фильтр')
        for i,label in enumerate(labels):
            cx=200+i*220;cy=465
            self.text(label,(cx-self.font.size(label)[0]/2,389),PALE)
            color=AMBER if app.radio_selected==i else (111,137,127)
            pg.draw.circle(s,color,(cx,cy),43,2)
            angle=st.radio[i]/RadioTune.ranges[i]*math.tau-math.pi/2
            end=(cx+math.cos(angle)*32,cy+math.sin(angle)*32)
            pg.draw.line(s,color,(cx,cy),end,4)
            value=str(st.radio[i])
            self.text(value,(cx-self.font.size(value)[0]/2,510),color)
            self.buttons.append((pg.Rect(cx-55,cy-55,110,110),('radio',i)))
        if 'c3_notes' in st.flags:
            self.paragraph('Отметки журнала: сектор 8, тонкая подстройка 4, речевой фильтр 2.',810,345,340,MINT,self.small,25)
        else:
            self.paragraph('Ищите максимум сигнала. Сначала диапазон, затем подстройка и фильтр. Журнал на посту поможет.',810,345,340,MINT,self.small,25)
        self.paragraph('← → — выбрать • E — вперёд • Q — назад',810,440,340,PALE,self.small,25)
        for i in range(st.signal_pattern):
            on=app.reduced_flash or (int(app.time/.4)%5==i)
            pg.draw.circle(s,AMBER if on else (64,78,71),(830+i*30,515),7)
        self.button('Два импульса  [2]',105,555,245,False,'beacon2')
        self.button('Три импульса  [3]',370,555,245,False,'beacon3')
        self.button('Слушать  [Enter]',635,555,245,False,'listen_radio')
        self.button('Отойти  [Esc]',900,555,245,False,'close_puzzle')
        if st.notice:self.paragraph(st.notice,105,615,1040,AMBER,self.small,23)

    def drive(self,app):
        s=self.surface;s.fill((13,27,34))
        horizon=170
        pg.draw.rect(s,(28,43,47),(0,horizon,1280,550))
        for i in range(13):
            depth=((i/13+app.drive_distance*.001)%1)
            y=horizon+depth*depth*480
            half=40+depth*400
            pg.draw.line(s,(78,88,79),(640-half,y),(640+half,y),int(1+depth*7))
        for side in (-1,1):
            pg.draw.line(s,(146,153,129),(640+side*22,horizon),(640+side*480,720),5)
        for i in range(7):
            z=((i/7+app.drive_distance*.0008)%1)
            x=640+(1 if i%2 else -1)*(100+z*z*650)
            y=horizon+z*z*430
            pg.draw.line(s,(49,66,67),(x,y),(x,y-50-z*240),max(2,int(z*9)))
            if i==3:pg.draw.line(s,(167,70,58),(x,y-50-z*230),(x+20+z*30,y-40-z*230),int(2+z*9))
        pg.draw.rect(s,(23,38,42),(0,570,1280,150))
        pg.draw.rect(s,(89,105,92),(0,570,1280,8))
        self.text(('ПОДАЧА К ПЛАТФОРМЕ • ' if app.drive_max_speed==12 else 'ПЕРЕГОН • ')+{1:'СЛУЖЕБНАЯ',2:'БОЛЬНИЧНАЯ',3:'РАБОЧИЙ ПОСЁЛОК',4:'ВОДОСБРОС',5:'СТАРАЯ ПЛАТФОРМА'}[app.state.chapter],(55,36),MINT)
        self.text(f'{int(app.speed)} км/ч',(80,605),AMBER,self.large)
        self.text('W / ↑ — тяга     S / ↓ — тормоз',(420,610),PALE)
        self.text('Малый ход, не выше 12 км/ч. У отметки остановитесь.' if app.drive_max_speed==12 else 'Держите 25–45 км/ч. У красного сигнала остановитесь.',(420,647),MINT,self.small)
        if app.drive_distance>app.drive_min_stop:
            pg.draw.circle(s,(219,79,55),(1040,240),19)
            self.text('КРАСНЫЙ • ТОРМОЗИТЕ',(850,295),AMBER)
        if app.drive_distance>app.drive_limit_at:
            self.text('Сигнал ограничивает скорость',(820,345),MINT,self.small)
