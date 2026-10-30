import argparse
import heapq
import json
import math
from pathlib import Path
import pygame as pg
from .audio import Audio
from .content import SCENES, DIALOGUES, walkable, clear_sight
from .model import Session, DEFAULT_SAVE
from .render import Renderer, SIZE
from .mechanics import PowerBoard,RadioTune
from .chapters import chapter2,chapter3
from . import chapters
from . import combat
from . import fieldwork
from . import hospital_action
from .carrying import CARRIER_SPACING,rigid_rear,follow_rear,team_walkable
from .staging import CrossingSequence
from .brakes import BrakeTest,operate as operate_brakes
from .inspection import POINTS as INSPECTION_POINTS,VIEW as INSPECTION_VIEW,operate as operate_inspection

V=pg.Vector2
SETTINGS=DEFAULT_SAVE.with_name('settings.json')

def blocked(scene,pos,radius=14):
    return not walkable(SCENES[scene],pos,radius)

def path_to(scene,start,end,radius=17):
    cell=40;a=(round(start[0]/cell),round(start[1]/cell));b=(round(end[0]/cell),round(end[1]/cell))
    queue=[(0,a)];cost={a:0};came={};best=a
    while queue and len(cost)<4000:
        _,node=heapq.heappop(queue)
        if abs(node[0]-b[0])+abs(node[1]-b[1])<abs(best[0]-b[0])+abs(best[1]-b[1]):best=node
        if node==b:best=node;break
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            n=(node[0]+dx,node[1]+dy)
            if blocked(scene,(n[0]*cell,n[1]*cell),radius):continue
            c=cost[node]+1
            if c<cost.get(n,1e9):
                cost[n]=c;came[n]=node;heapq.heappush(queue,(c+abs(n[0]-b[0])+abs(n[1]-b[1]),n))
    out=[]
    while best in came:out.append(V(best[0]*cell,best[1]*cell));best=came[best]
    out.reverse();return out

class Enemy:
    def __init__(self,pos,kind='walker'):
        self.pos=V(pos);self.home=V(pos);self.target=None;self.interest=0;self.stun=0;self.repath=0;self.path=[]
        self.attack_state='idle';self.attack_timer=0;self.strike=V(pos)
        self.kind=kind;self.spec=combat.SPECS[kind];self.health=self.spec['health'];self.flag='';self.hit_flash=0
        self.attack_direction=V(0,1);self.attack_origin=V(pos);self.charge_hit=False
        self.walk_phase=0.0;self.moving=False;self.facing=V(0,1)

class App:
    def __init__(self,save_path=DEFAULT_SAVE):
        pg.mixer.pre_init(48000,-16,2,1024);pg.init()
        desktop=pg.display.get_desktop_sizes()[0]
        self.window_size=tuple(min(a,b) for a,b in zip((1600,900),(round(desktop[0]*.9),round(desktop[1]*.9))))
        if pg.display.get_driver()=='dummy':self.window_size=SIZE
        self.display=pg.display.set_mode(self.window_size,pg.RESIZABLE);pg.display.set_caption('Последний рейс')
        self.renderer=Renderer();self.audio=Audio();self.state=Session()
        self.mode='menu';self.previous_mode='menu';self.paused_mode='play';self.settings_parent='menu';self.selection=self.choice=0;self.running=True;self.clock=pg.time.Clock()
        self.time=self.walk_phase=self.hurt=self.step_timer=self.flare_time=0.0
        self.drive_distance=self.speed=0.0;self.moving=False;self.facing=V(0,1)
        self.drive_arrival='loop';self.travel_active=False;self.puzzle_selected=7;self.crossing_sequence=None;self.inspection_selected=0
        self.drive_min_stop=500;self.drive_limit_at=760;self.drive_max_speed=55
        self.radio_selected=0
        self.move_blend=0.0
        self.dash_time=self.dash_cooldown=0.0;self.dash_direction=V(0,1)
        self.dialogue_timer=0.0;self.dialogue_identity=None
        self.attack_time=0.0;self.attack_direction=V(0,1);self.attack_resolved=False;self.hit_sparks=[]
        self.hit_pause=0.0;self.dash_guard=False
        self.field_task=None;self.cable_state=None;self.winch_stroke=0
        self.rear_walk_phase=0.0;self.rear_moving=False;self.rear_direction=V(0,1)
        self.journal_page=0
        self.enemies=[];self.rings=[];self.loaded_scene=None;self.menu_notice=''
        self.carry_trail=[]
        self.carry_rear=None;self.carry_anchor=None
        self.save_path=Path(save_path);self.fullscreen=False;self.reduced_flash=True;self.autosave_timer=0;self.checkpoint=None
        self.load_settings()

    def load_settings(self):
        try:
            data=json.loads(SETTINGS.read_text(encoding='utf-8'));volume=data.get('volume',.55)
            if type(volume) in (float,int) and math.isfinite(volume):self.audio.volume=max(0,min(1,volume))
            self.reduced_flash=data.get('reduced_flash',True) is not False
        except (OSError,ValueError,TypeError,AttributeError):pass

    def save_settings(self):
        try:
            SETTINGS.parent.mkdir(parents=True,exist_ok=True);temp=SETTINGS.with_suffix('.tmp')
            temp.write_text(json.dumps({'volume':self.audio.volume,'reduced_flash':self.reduced_flash}),encoding='utf-8');temp.replace(SETTINGS)
        except OSError:self.menu_notice='Не удалось записать настройки.'

    def save(self,completed_work=False):
        try:
            if self.travel_active or self.mode=='drive' or self.crossing_sequence is not None:return False
            if not completed_work and (self.state.dialogue or self.field_task is not None):return False
            self.state.save(self.save_path);self.checkpoint=self.state.snapshot();return True
        except (OSError,ValueError) as exc:self.state.say('Не удалось сохранить игру. '+str(exc));return False

    def scene_changed(self,persist=True):
        if self.loaded_scene==self.state.scene:return
        self.loaded_scene=self.state.scene
        self.field_task=None;self.cable_state=None
        self.carry_rear=None;self.carry_anchor=None
        self.rear_moving=False
        self.enemies=[Enemy((1110,580))] if self.loaded_scene=='waiting' and 'rescued' not in self.state.flags else []
        if self.loaded_scene=='yard' and 'c2_boarded' not in self.state.flags:
            self.enemies=[Enemy((1300,750)),Enemy((700,520))]
        if self.loaded_scene=='switchyard' and 'c3_boarded' not in self.state.flags:
            self.enemies=[Enemy((1000,780)),Enemy((840,480))]
        if 'action_mode' in self.state.flags and self.loaded_scene in combat.ENCOUNTERS:
            stop={'waiting':'rescued','yard':'c2_boarded','switchyard':'c3_boarded'}[self.loaded_scene]
            self.enemies=[]
            if stop not in self.state.flags:
                for i,pos in enumerate(combat.ENCOUNTERS[self.loaded_scene]):
                    flag=f'combat_down_{self.loaded_scene}_{i}'
                    if flag not in self.state.flags:
                        enemy=Enemy(pos,combat.ENCOUNTER_TYPES[self.loaded_scene][i]);enemy.flag=flag;self.enemies.append(enemy)
        self.dash_time=self.dash_cooldown=self.attack_time=self.hit_pause=0;self.hit_sparks=[];self.dash_guard=False
        self.rings=[];self.hurt=1
        self.state.notice='';self.state.notice_time=0
        if self.state.carrying:self.seed_carry_trail()
        if persist:self.save()

    def new(self,action=True):
        self.crossing_sequence=None
        self.state=combat.cold_open() if action else Session();self.loaded_scene=None;self.enemies=[];self.travel_active=False;self.mode='play'
        self.state.dialogue=None;self.scene_changed();self.state.start_dialogue('c_action_start' if action else 'opening')

    def attack(self,direction=None):
        if self.mode!='play' or (self.state.dialogue and not combat.moving_dialogue(self.state)) or self.state.carrying or self.attack_time>0 or self.dash_time>0:return
        self.attack_direction=V(direction or self.facing)
        self.field_task=None
        if not self.attack_direction.length_squared():self.attack_direction=V(0,1)
        self.attack_direction.normalize_ip();self.facing=V(self.attack_direction)
        self.attack_time=.4;self.attack_resolved=False;self.audio.play('dash')

    def dash(self):
        if self.mode!='play' or (self.state.dialogue and not combat.moving_dialogue(self.state)) or self.state.carrying or self.dash_cooldown>0:return
        self.dash_direction=V(self.facing);self.dash_time=.16;self.dash_cooldown=.7
        self.field_task=None
        self.attack_time=0;self.audio.play('dash');self.noise(self.state.pos,280)

    def nearby(self,point=None):
        visible=[]
        for obj in SCENES[self.state.scene].objects:
            if obj.kind=='nina' and hospital_action.deployed(self.state,self.field_task):
                from dataclasses import replace
                obj=replace(obj,pos=hospital_action.positions(self.state)[1])
            if self.state.carrying and obj.kind=='lida':continue
            if obj.requires and obj.requires not in self.state.flags:continue
            if self.state.scene=='carriage' and self.state.chapter==2 and 'c2_arrived' in self.state.flags and 'c2_boarded' not in self.state.flags and obj.kind=='lida':continue
            if self.state.scene=='refuge' and obj.kind=='raisa' and 'c2_boarded' in self.state.flags:continue
            if obj.id=='stopper' and 'stopper' in self.state.flags:continue
            if obj.kind=='patient' and self.state.scene=='ward' and self.state.carrying:continue
            if obj.kind=='nina' and self.state.scene=='ward' and 'relay_nina' in self.state.flags:continue
            distance=V(obj.pos).distance_to(self.state.pos if point is None else point)
            if distance<90:visible.append((distance,obj))
        return min(visible,key=lambda q:q[0])[1] if visible else None

    def move(self,delta):
        if self.state.carrying and (self.carry_rear is None or self.carry_anchor is None or self.carry_anchor.distance_to(self.state.pos)>.01):self.seed_carry_trail()
        origin=V(self.state.pos);pos=V(origin);steps=max(1,math.ceil(delta.length()/8))
        for _ in range(steps):
            for axis in (0,1):
                p=V(pos);p[axis]+=delta[axis]/steps
                if blocked(self.state.scene,p,22 if self.state.carrying else 14):continue
                if self.state.carrying:
                    rear=follow_rear(p,self.carry_rear,CARRIER_SPACING*SCENES[self.state.scene].actor_scale)
                    if not team_walkable(SCENES[self.state.scene],p,rear):continue
                    self.carry_rear=rear;self.carry_anchor=V(p)
                pos=p
        self.state.pos=list(pos)
        if self.state.carrying and delta.length_squared()>.01 and pos.distance_to(origin)<.01 and self.state.notice_time<=0:
            self.state.say('Носилкам нужен широкий поворот. Отведите всю группу от края.')
        self.state.carry_rear=list(self.carry_rear) if self.state.carrying and self.carry_rear is not None else None
        if self.state.carrying:
            if not self.carry_trail:self.seed_carry_trail()
            if V(self.carry_trail[0]).distance_to(pos)>3:self.carry_trail.insert(0,V(pos))
            length=0
            for i in range(1,len(self.carry_trail)):
                length+=self.carry_trail[i-1].distance_to(self.carry_trail[i])
                if length>600:
                    self.carry_trail=self.carry_trail[:i+1];break
        else:self.carry_trail=[];self.carry_rear=None;self.carry_anchor=None

    def seed_carry_trail(self):
        origin=V(self.state.pos);needed=CARRIER_SPACING*SCENES[self.state.scene].actor_scale
        if self.state.carry_rear is not None:
            rear=V(self.state.carry_rear)
            if abs(origin.distance_to(rear)-needed)<1 and team_walkable(SCENES[self.state.scene],origin,rear):
                self.carry_rear=rear;self.carry_anchor=V(origin);self.carry_trail=[origin,rear];return
        self.carry_trail=[origin]
        # A pickup or room transition may face a nearby wall. Prefer that
        # direction, then choose an unobstructed placement of the full team.
        for direction in (self.facing,V(1,0),V(-1,0),V(0,1),V(0,-1),V(1,1).normalize(),V(-1,1).normalize(),V(1,-1).normalize(),V(-1,-1).normalize()):
            trail=[origin]
            for i in range(1,82):
                point=origin-direction*i*6
                if blocked(self.state.scene,point,22):break
                trail.append(point)
            if len(trail)>len(self.carry_trail):self.carry_trail=trail
            if trail[-1].distance_to(origin)>=needed:
                self.carry_trail=trail;break
        self.carry_rear=rigid_rear(origin,self.carry_trail,needed);self.carry_anchor=V(origin)
        self.state.carry_rear=list(self.carry_rear)

    def carry_positions(self):
        if self.carry_rear is None or self.carry_anchor is None or self.carry_anchor.distance_to(self.state.pos)>.01:self.seed_carry_trail()
        rear=V(self.carry_rear)
        center=(V(self.state.pos)+rear)*.5
        d=V(self.state.pos)-rear
        angle=-math.degrees(math.atan2(d.y,d.x)) if d.length_squared() else 0
        return center,rear,angle

    def noise(self,where,loudness=900):
        self.rings.append([V(where),20,1.5])
        for enemy in self.enemies:
            if enemy.pos.distance_to(where)<loudness:enemy.target=V(where);enemy.interest=10;enemy.repath=0

    def move_enemy(self,enemy,delta,slide=True):
        before=V(enemy.pos);steps=max(1,math.ceil(delta.length()/8))
        for _ in range(steps):
            step=delta/steps
            if not slide:
                point=enemy.pos+step
                if blocked(self.state.scene,point,17):break
                enemy.pos=point
            else:
                for axis in (0,1):
                    point=V(enemy.pos);point[axis]+=step[axis]
                    if not blocked(self.state.scene,point,17):enemy.pos=point
        motion=enemy.pos-before;distance=motion.length();enemy.moving=distance>.01
        if enemy.moving:
            enemy.facing=motion.normalize();enemy.walk_phase+=distance/(40*SCENES[self.state.scene].actor_scale)*math.pi
        return distance

    def hurt_player(self,damage,message):
        if self.hurt>0 or self.dash_guard:return False
        self.field_task=None;self.state.health-=damage;self.hurt=1.3
        self.audio.play('hurt');self.state.say(message);return True

    def interact(self):
        obj=self.nearby()
        if not obj:self.state.say('Подойдите ближе к двери, человеку или предмету.');return
        before=self.state.scene;event=self.state.interact(obj.id)
        if isinstance(event,str) and event.startswith('field_'):
            self.field_task=fieldwork.create(event[6:]);self.audio.play('metal')
            target=hospital_action.positions(self.state)[0] if self.field_task.kind in ('c2_attach','c2_rhythm','c2_lock') else self.field_task.target
            look=V(target)-V(self.state.pos)
            if look.length_squared():self.facing=look.normalize()
        elif event=='bell':self.audio.play('bell');self.noise(obj.pos)
        elif event in ('power','winch','radio','gate','brake','inspection'):
            self.mode=event;self.puzzle_selected=7;self.radio_selected=0
        else:self.audio.play('click')
        if before!=self.state.scene:self.scene_changed()
        elif not self.state.dialogue:self.save()

    def advance_dialogue(self):
        result=self.state.advance();self.choice=0;self.audio.play('click')
        if result=='c5_crossing_start':
            self.crossing_sequence=CrossingSequence();self.mode='crossing'
        if result=='c1_brake_started':self.mode='brake'
        if result in chapters.TRAVEL:
            self.mode='drive';self.drive_distance=0;self.speed=0;self.travel_active=True
            self.drive_arrival=chapters.TRAVEL[result]
            self.drive_min_stop=50 if result=='c1_align' else 500
            self.drive_limit_at=90 if result=='c1_align' else 760
            self.drive_max_speed=12 if result=='c1_align' else 55
        elif result in {info['complete'] for info in chapters.INFO.values()}:self.mode='chapter_end';self.selection=0
        if result:self.save()
        if result=='carry':self.seed_carry_trail()
        self.scene_changed()

    def choose_dialogue(self,index):
        data=DIALOGUES.get(self.state.dialogue,{})
        if (self.state.dialogue=='c5_departure' and self.state.line>=len(data.get('lines',[]))
                and 0<=index<len(data.get('choices',[]))):
            try:self.state.save(self.save_path.with_name(self.save_path.stem+'-route.json'))
            except OSError:self.state.say('Не удалось сохранить отдельную точку выбора маршрута.')
        self.state.choose(index);self.choice=0

    def action(self,action):
        if action is None:return
        required_mode={'test_power':'power','reset_power':'power','winch_crank':'winch','winch_pawl':'winch',
                       'listen_radio':'radio','beacon2':'radio','beacon3':'radio','next_chapter':'chapter_end',
                       'gate_support':'gate','gate_pin':'gate','gate_swing':'gate','gate_confirm':'gate',
                       **{'brake_'+a:'brake' for a in ('compressor','charge','apply','release','hold','observe')}}
        required_mode.update({'inspect_'+a:'inspection' for a in ('step','gap','landing','rails','platform')})
        if isinstance(action,str) and action in required_mode and self.mode!=required_mode[action]:return
        if isinstance(action,tuple) and action[0] in ('tile','radio') and self.mode!=('power' if action[0]=='tile' else 'radio'):return
        self.audio.play('click');self.menu_notice=''
        if isinstance(action,tuple):
            if action[0]=='choice':self.choose_dialogue(action[1])
            elif action[0]=='tile':
                self.puzzle_selected=action[1];PowerBoard.rotate(self.state.power,self.puzzle_selected)
            elif action[0]=='radio':
                self.radio_selected=action[1];RadioTune.adjust(self.state.radio,self.radio_selected)
            elif action[0]=='setting':
                i=action[1]
                if i==0:self.audio.volume=round((self.audio.volume+.1)%1.1,2)
                elif i==1:self.toggle_fullscreen()
                elif i==2:self.reduced_flash=not self.reduced_flash
                else:self.mode=self.settings_parent;self.selection=0
                self.save_settings()
            return
        if action=='new':
            if self.save_path.exists():self.mode='confirm_new';self.selection=1
            else:self.new()
        elif action=='confirm_new':self.new()
        elif action=='next_chapter':
            next_dialogue=chapters.INFO[self.state.chapter]['next']
            if next_dialogue:
                self.mode='play';self.state.start_dialogue(next_dialogue)
        elif isinstance(action,str) and action.startswith('inspect_'):
            for i,point in enumerate(INSPECTION_POINTS):
                if action[8:]==point[0]:self.inspection_selected=i
            if operate_inspection(self.state,action[8:]):self.mode='play'
            else:self.save()
        elif isinstance(action,str) and action.startswith('brake_'):
            if operate_brakes(self.state,action[6:]):
                self.mode='play'
                # The equipment operation is complete; its following confirmation
                # dialogue can be replayed from the controls after loading.
                try:self.state.save(self.save_path);self.checkpoint=self.state.snapshot()
                except (OSError,ValueError):self.state.say('Не удалось сохранить завершённую проверку.')
            else:self.save()
        elif isinstance(action,str) and action.startswith('gate_'):
            if chapters.chapter5.operate_gate(self.state,action[5:]):self.mode='play'
            else:self.save()
        elif action=='test_power':
            if chapter2.test_power(self.state):self.mode='play';self.save()
        elif action=='reset_power':self.state.power=list(PowerBoard.initial)
        elif action in ('winch_crank','winch_pawl'):
            if chapter2.operate_winch(self.state,'crank' if action=='winch_crank' else 'pawl'):self.mode='play'
            else:self.save()
        elif action=='listen_radio':
            if chapter3.listen(self.state):self.mode='play';self.audio.play('radio_signal')
            else:self.audio.play('radio_noise')
        elif action in ('beacon2','beacon3'):
            if chapter3.beacon(self.state,int(action[-1])):self.audio.play(action)
        elif action=='close_puzzle':self.state.puzzle=None;self.mode='play';self.save()
        elif action=='replay_route':
            if self.mode!='chapter_end' or self.state.chapter!=5:return
            try:
                restored=Session.load(self.save_path.with_name(self.save_path.stem+'-route.json'))
                if restored.chapter!=4 or 'c4_complete' not in restored.flags:raise ValueError('Invalid route checkpoint')
                self.state=restored;self.travel_active=False;self.loaded_scene=None;self.scene_changed()
                self.mode='play';self.state.start_dialogue('c5_departure');self.choice=0
            except (OSError,ValueError,KeyError,TypeError):self.menu_notice='Отдельная точка маршрута не найдена. Она создаётся при выборе последнего маршрута.'
        elif action=='load':
            try:
                self.state=Session.load(self.save_path);self.crossing_sequence=None;self.mode='play';self.travel_active=False;self.loaded_scene=None;self.scene_changed();self.state.say('Контрольная точка загружена.')
                if 'opening' not in self.state.flags:self.state.start_dialogue('opening')
                elif chapters.INFO[self.state.chapter]['complete'] in self.state.flags:self.mode='chapter_end'
            except (OSError,ValueError,KeyError,TypeError):self.menu_notice='Сохранение не найдено или повреждено. Можно начать новую историю.'
        elif action=='resume':self.mode=self.paused_mode if self.mode=='pause' else 'play'
        elif action=='save':
            if self.state.dialogue:self.menu_notice='Разговор ещё не закончен. Последняя завершённая сцена уже сохранена.'
            elif self.save():self.menu_notice='Контрольная точка сохранена.';self.state.say(self.menu_notice)
        elif action=='settings':self.settings_parent=self.mode;self.mode='settings';self.selection=0
        elif action=='menu':
            if self.mode not in ('menu','dead','confirm_new'):self.save()
            self.mode='menu';self.selection=0
        elif action=='quit':self.running=False
        elif action=='retry':
            try:self.state=Session.restore(self.checkpoint) if self.checkpoint else Session.load(self.save_path)
            except (ValueError,OSError,TypeError):self.state=Session()
            self.state.health=100;self.state.flares=max(1,self.state.flares);self.mode='play';self.travel_active=False;self.loaded_scene=None;self.scene_changed()

    def toggle_fullscreen(self):
        if not self.fullscreen:self.window_size=self.display.get_size()
        self.fullscreen=not self.fullscreen
        self.display=pg.display.set_mode((0,0) if self.fullscreen else self.window_size,pg.FULLSCREEN if self.fullscreen else pg.RESIZABLE)

    def mouse_pos(self,pos):
        w,h=self.display.get_size();scale=min(w/1280,h/720)
        return V((pos[0]-(w-1280*scale)/2)/scale,(pos[1]-(h-720*scale)/2)/scale)

    def event(self,event):
        if event.type==pg.QUIT:
            if self.mode not in ('menu','dead'):self.save()
            self.running=False;return
        if event.type==pg.WINDOWFOCUSLOST and self.mode in ('play','drive','crossing','journal','power','winch','radio','gate','brake','inspection'):self.paused_mode=self.mode;self.mode='pause';self.selection=0
        if event.type==pg.MOUSEBUTTONDOWN and self.mode=='play' and (not self.state.dialogue or combat.moving_dialogue(self.state)):
            if event.button==1:
                self.renderer.camera_for(self.state.scene,self.state.pos)
                self.attack(self.mouse_pos(event.pos)+self.renderer.camera-V(self.state.pos));return
            if event.button==3:self.dash();return
        if event.type in (pg.MOUSEMOTION,pg.MOUSEBUTTONDOWN) and self.mode=='inspection':
            p=self.mouse_pos(event.pos);view=pg.Rect(INSPECTION_VIEW)
            if view.collidepoint(p):
                targets=[V(view.x+point[2][0]*view.w/1536,view.y+point[2][1]*view.h/1024) for point in INSPECTION_POINTS]
                index=min(range(3),key=lambda i:targets[i].distance_to(p))
                if targets[index].distance_to(p)<55:
                    self.inspection_selected=index
                    if event.type==pg.MOUSEBUTTONDOWN and event.button==1:self.action('inspect_'+INSPECTION_POINTS[index][0])
                if event.type==pg.MOUSEBUTTONDOWN:return
        if event.type==pg.MOUSEBUTTONDOWN and event.button==1:
            if self.renderer.button_mode!=self.mode:return
            p=self.mouse_pos(event.pos)
            for rect,action in self.renderer.buttons:
                if rect.collidepoint(p):self.action(action);return
        if event.type==pg.MOUSEWHEEL and self.mode=='journal':
            pages=max(1,(len(self.state.journal())+3)//4)
            self.journal_page=max(0,min(pages-1,self.journal_page-event.y));return
        if event.type!=pg.KEYDOWN:return
        key=event.key
        if key==pg.K_F11:self.toggle_fullscreen();return
        if key==pg.K_ESCAPE:
            if self.mode in ('play','drive','crossing'):self.paused_mode=self.mode;self.mode='pause';self.selection=0
            elif self.mode=='pause':self.mode=self.paused_mode
            elif self.mode=='journal':self.mode='play'
            elif self.mode=='settings':self.mode=self.settings_parent;self.selection=0
            elif self.mode=='confirm_new':self.mode='menu';self.selection=0
            elif self.mode in ('power','winch','radio','gate','brake','inspection'):self.action('close_puzzle')
            return
        if self.mode=='power':
            col,row=self.puzzle_selected%5,self.puzzle_selected//5
            if key==pg.K_LEFT:self.puzzle_selected=row*5+(col-1)%5
            elif key==pg.K_RIGHT:self.puzzle_selected=row*5+(col+1)%5
            elif key==pg.K_UP:self.puzzle_selected=((row-1)%4)*5+col
            elif key==pg.K_DOWN:self.puzzle_selected=((row+1)%4)*5+col
            elif key in (pg.K_e,pg.K_SPACE):PowerBoard.rotate(self.state.power,self.puzzle_selected)
            elif key==pg.K_RETURN:self.action('test_power')
            elif key==pg.K_r:self.action('reset_power')
            return
        if self.mode=='inspection':
            if key in (pg.K_1,pg.K_2,pg.K_3):
                self.inspection_selected=key-pg.K_1;self.action('inspect_'+INSPECTION_POINTS[self.inspection_selected][0])
            elif key in (pg.K_LEFT,pg.K_UP):self.inspection_selected=(self.inspection_selected-1)%3
            elif key in (pg.K_RIGHT,pg.K_DOWN):self.inspection_selected=(self.inspection_selected+1)%3
            elif key in (pg.K_e,pg.K_SPACE):self.action('inspect_'+INSPECTION_POINTS[self.inspection_selected][0])
            elif key==pg.K_RETURN:self.action('inspect_platform')
            return
        if self.mode=='brake':
            controls={pg.K_1:'compressor',pg.K_2:'charge',pg.K_3:'apply',pg.K_4:'release',pg.K_SPACE:'hold',pg.K_RETURN:'observe'}
            if key in controls:self.action('brake_'+controls[key])
            return
        if self.mode=='gate':
            gate_keys={pg.K_1:'support',pg.K_2:'pin',pg.K_3:'swing',pg.K_RETURN:'confirm'}
            if key in gate_keys:self.action('gate_'+gate_keys[key])
            return
        if self.mode=='winch':
            if key in (pg.K_e,pg.K_RETURN):self.action('winch_crank')
            elif key==pg.K_SPACE:self.action('winch_pawl')
            return
        if self.mode=='radio':
            if key in (pg.K_LEFT,pg.K_UP):self.radio_selected=(self.radio_selected-1)%3
            elif key in (pg.K_RIGHT,pg.K_DOWN):self.radio_selected=(self.radio_selected+1)%3
            elif key in (pg.K_e,pg.K_SPACE):RadioTune.adjust(self.state.radio,self.radio_selected)
            elif key==pg.K_q:RadioTune.adjust(self.state.radio,self.radio_selected,-1)
            elif key in (pg.K_2,pg.K_3):self.action('beacon'+str(key-pg.K_0))
            elif key==pg.K_RETURN:self.action('listen_radio')
            return
        if self.mode=='play':
            if key==pg.K_e and self.field_task is not None and self.field_task.kind=='c2_rhythm':
                if getattr(event,'repeat',False):return
                task=self.field_task
                if V(task.target).distance_to(self.state.pos)>=110:self.field_task=None;return
                if V(hospital_action.work_position(self.state)).distance_to(self.state.pos)>8:return
                success=hospital_action.pulse(self.state,task);self.audio.play('metal' if success else 'click')
                if success:self.winch_stroke=.4
                if self.state.winch['stage']=='lock':self.field_task=None
                if success:self.save(completed_work=True)
                return
            if key==pg.K_SPACE and (not self.state.dialogue or combat.moving_dialogue(self.state)):
                self.dash();return
            if key==pg.K_f and (not self.state.dialogue or combat.moving_dialogue(self.state)):
                self.attack();return
            if self.state.dialogue and (not combat.moving_dialogue(self.state) or key in (pg.K_RETURN,pg.K_e)):
                data=DIALOGUES[self.state.dialogue];choices=data.get('choices',[])
                if self.state.line>=len(data['lines']):
                    if key in (pg.K_1,pg.K_2,pg.K_3):self.choose_dialogue(key-pg.K_1)
                    elif key in (pg.K_UP,pg.K_w):self.choice=(self.choice-1)%len(choices)
                    elif key in (pg.K_DOWN,pg.K_s):self.choice=(self.choice+1)%len(choices)
                    elif key in (pg.K_RETURN,pg.K_e,pg.K_SPACE):self.choose_dialogue(self.choice)
                elif key in (pg.K_RETURN,pg.K_e,pg.K_SPACE):self.advance_dialogue()
            elif key==pg.K_e:self.interact()
            elif key==pg.K_j:self.mode='journal';self.journal_page=0
            elif key==pg.K_q:
                if self.state.flares>0:
                    self.state.flares-=1;self.flare_time=3;self.audio.play('flare');self.noise(self.state.pos)
                    for enemy in self.enemies:
                        if enemy.pos.distance_to(self.state.pos)<320:
                            enemy.stun=4;enemy.attack_state='idle';enemy.attack_timer=0
                    self.state.say('Путевой отступает от света. У вас несколько секунд.')
                else:self.state.say('Ракет нет. Используйте звонок или пройдите тихо.')
            elif key==pg.K_F5:self.action('save')
        elif self.mode=='journal':
            if key==pg.K_j:self.mode='play'
            elif key in (pg.K_RIGHT,pg.K_DOWN,pg.K_d,pg.K_s):
                self.journal_page=min(max(0,(len(self.state.journal())-1)//4),self.journal_page+1)
            elif key in (pg.K_LEFT,pg.K_UP,pg.K_a,pg.K_w):self.journal_page=max(0,self.journal_page-1)
        elif self.mode!='drive':
            buttons=self.renderer.buttons
            if not buttons:return
            if key in (pg.K_UP,pg.K_w):self.selection=(self.selection-1)%len(buttons)
            elif key in (pg.K_DOWN,pg.K_s):self.selection=(self.selection+1)%len(buttons)
            elif self.mode=='settings' and self.selection==0 and key in (pg.K_LEFT,pg.K_RIGHT):
                self.audio.volume=max(0,min(1,self.audio.volume+(.05 if key==pg.K_RIGHT else -.05)));self.save_settings()
            elif key in (pg.K_RETURN,pg.K_SPACE):self.action(buttons[self.selection%len(buttons)][1])

    def update(self,dt,keys=None,active_dt=None):
        self.time+=dt;self.audio.update(self.state.scene,self.mode!='play')
        # Active play includes reading, equipment, travel and staged movement.
        # Menus, settings, death, completed-chapter screens and pauses are excluded.
        if self.mode in ('play','drive','crossing','journal','power','winch','radio','gate','brake','inspection'):
            active_elapsed=max(0,dt if active_dt is None else active_dt)
            self.state.elapsed+=active_elapsed
            self.state.notice_time=max(0,self.state.notice_time-active_elapsed)
        if self.mode=='brake':BrakeTest.step(self.state.brake,dt)
        if self.mode=='crossing':
            if self.crossing_sequence is not None and self.crossing_sequence.advance(dt):
                self.crossing_sequence=None;self.mode='play';self.state.start_dialogue('c5_crossed')
            return
        mobile_dialogue=combat.moving_dialogue(self.state)
        if self.mode=='play' and mobile_dialogue:
            identity=(self.state.dialogue,self.state.line)
            if identity!=self.dialogue_identity:self.dialogue_identity=identity;self.dialogue_timer=0
            self.dialogue_timer+=dt
            line=DIALOGUES[self.state.dialogue]['lines'][self.state.line][1]
            if self.dialogue_timer>max(1.5,min(4.5,len(line)/28)):
                self.advance_dialogue();self.dialogue_timer=0
        if self.mode!='play' or (self.state.dialogue and not mobile_dialogue):
            self.moving=False;self.move_blend*=math.exp(-12*dt)
        if self.mode=='drive':
            keys=keys if keys is not None else pg.key.get_pressed();throttle=keys[pg.K_w] or keys[pg.K_UP];brake=keys[pg.K_s] or keys[pg.K_DOWN]
            self.speed=max(0,min(self.drive_max_speed,self.speed+(8 if throttle else -1)*dt-(24*dt if brake else 0)));self.drive_distance+=self.speed*dt*.65
            if self.drive_distance>self.drive_limit_at:self.speed=max(0,self.speed-22*dt)
            if self.drive_distance>self.drive_min_stop and self.speed<.5:
                self.mode='play';self.travel_active=False;self.state.start_dialogue(self.drive_arrival)
            return
        if self.mode!='play' or (self.state.dialogue and not combat.moving_dialogue(self.state)):return
        if self.hit_pause>0:
            self.hit_pause=max(0,self.hit_pause-dt);return
        self.scene_changed();self.hurt=max(0,self.hurt-dt);self.flare_time=max(0,self.flare_time-dt)
        self.winch_stroke=max(0,getattr(self,'winch_stroke',0)-dt)
        keys=keys if keys is not None else pg.key.get_pressed()
        direction=V(int(keys[pg.K_d] or keys[pg.K_RIGHT])-int(keys[pg.K_a] or keys[pg.K_LEFT]),int(keys[pg.K_s] or keys[pg.K_DOWN])-int(keys[pg.K_w] or keys[pg.K_UP]))
        aligning=False;align_distance=0
        if self.field_task is not None and self.field_task.kind in hospital_action.WORK_KINDS:
            if direction.length_squared():self.field_task=None
            else:
                approach=V(hospital_action.work_position(self.state))-V(self.state.pos)
                if approach.length()>4:direction=approach;aligning=True;align_distance=approach.length()
                else:
                    look=V(hospital_action.positions(self.state)[0])-V(self.state.pos)
                    if look.length_squared():self.facing=look.normalize()
        before_rear=self.carry_positions()[1] if self.state.carrying else None
        self.rear_moving=False
        self.dash_cooldown=max(0,self.dash_cooldown-dt)
        self.dash_guard=self.dash_time>0
        if self.dash_time>0:direction=V(self.dash_direction)
        self.moving=False;sprint=keys[pg.K_LSHIFT] and not self.state.carrying;speed=110 if self.state.carrying else 360 if sprint else 235
        if self.dash_time>0:speed=790
        if self.attack_time>0:speed*=.55
        if aligning:speed=min(speed,align_distance/max(dt,.001))
        if direction.length_squared()>0:
            direction=direction.normalize();self.facing=direction;before=V(self.state.pos)
            self.move(direction*speed*dt);distance=before.distance_to(self.state.pos)
            self.moving=distance>.01
            if self.moving:
                previous=self.walk_phase
                self.walk_phase+=distance/(40*SCENES[self.state.scene].actor_scale)*math.pi
                if int(previous/math.pi)!=int(self.walk_phase/math.pi):
                    self.audio.play('step')
                    if sprint:self.noise(self.state.pos,420)
        self.move_blend+=((1 if self.moving else 0)-self.move_blend)*(1-math.exp(-12*dt))
        if aligning and not self.moving:
            self.field_task=None;self.state.say('Подойдите к лебёдке со стороны свободного прохода.')
        if before_rear is not None:
            motion=self.carry_positions()[1]-before_rear;distance=motion.length()
            if distance>.01:
                self.rear_moving=True;self.rear_direction=motion.normalize()
                self.rear_walk_phase+=distance/(40*SCENES[self.state.scene].actor_scale)*math.pi
        if self.field_task is not None:
            task=self.field_task
            valid=task.scene==self.state.scene and V(task.target).distance_to(self.state.pos)<110
            if not valid:self.field_task=None
            elif aligning:pass
            elif task.kind=='c2_rhythm':
                if self.moving or self.dash_time>0 or self.attack_time>0:self.field_task=None
                else:task.progress+=dt
            elif keys[pg.K_e] and not self.moving and self.dash_time<=0 and self.attack_time<=0:
                task.progress+=dt
                if task.progress>=task.duration:
                    followup=fieldwork.complete(self.state,task.kind)
                    self.field_task=fieldwork.create(followup) if followup else None
                    if self.state.carrying:
                        if task.kind=='lift':
                            exit_obj=next(o for o in SCENES[self.state.scene].objects if o.id=='exit')
                            self.facing=(V(exit_obj.pos)-V(self.state.pos)).normalize()
                        self.seed_carry_trail()
                    self.audio.play('metal');self.save(completed_work=task.kind.startswith('c2_'))
            else:self.field_task=None
        self.dash_time=max(0,self.dash_time-dt)
        if self.attack_time>0:
            self.attack_time=max(0,self.attack_time-dt)
            if self.attack_time<=.27 and not self.attack_resolved:
                self.attack_resolved=True
                for enemy in self.enemies[:]:
                    if combat.strike_hits(self.state.scene,self.state.pos,self.attack_direction,enemy.pos):
                        armored=enemy.kind=='brute' and enemy.attack_state=='windup'
                        enemy.health-=55;enemy.hit_flash=.15;self.hit_pause=.035
                        if not armored:enemy.stun=.27;enemy.attack_state='idle'
                        self.hit_sparks.append([V(enemy.pos),.18]);self.audio.play('metal')
                        push=enemy.pos-V(self.state.pos)
                        if push.length_squared():
                            for _ in range(2 if armored else 8):
                                point=enemy.pos+push.normalize()*4
                                if not blocked(self.state.scene,point,17):enemy.pos=point
                        if enemy.health<=0:
                            if enemy.flag:self.state.flags.add(enemy.flag)
                            self.enemies.remove(enemy)
        self.hit_sparks=[[p,life-dt] for p,life in self.hit_sparks if life>dt]
        for ring in self.rings[:]:
            ring[1]+=dt*180;ring[2]-=dt
            if ring[2]<=0:self.rings.remove(ring)
        for enemy in self.enemies:
            enemy.moving=False
            enemy.hit_flash=max(0,enemy.hit_flash-dt)
            enemy.stun=max(0,enemy.stun-dt)
            if enemy.stun>0:continue
            distance=enemy.pos.distance_to(self.state.pos);enemy.interest-=dt;enemy.repath-=dt
            visible=distance<(340 if 'action_mode' in self.state.flags else 155) and clear_sight(SCENES[self.state.scene],enemy.pos,self.state.pos)
            if enemy.attack_state!='idle':
                enemy.attack_timer-=dt
                if enemy.attack_state=='charge':
                    before=V(enemy.pos);expected=combat.CHARGE_SPEED*min(dt,max(0,enemy.attack_timer+dt))
                    distance_moved=self.move_enemy(enemy,enemy.attack_direction*expected,slide=False)
                    if not enemy.charge_hit and combat.segment_hits(before,enemy.pos,self.state.pos) and clear_sight(SCENES[self.state.scene],before,self.state.pos):
                        enemy.charge_hit=True;self.hurt_player(enemy.spec['damage'],'Бегун идёт по прямой. Уходите в сторону от полосы рывка.')
                    if enemy.attack_timer<=0 or distance_moved<expected-.5:
                        enemy.attack_state='recover';enemy.attack_timer=enemy.spec['recovery']
                    continue
                if enemy.attack_timer<=0:
                    if enemy.attack_state=='windup':
                        if enemy.kind=='runner':
                            enemy.attack_state='charge';enemy.attack_timer=combat.CHARGE_DISTANCE/combat.CHARGE_SPEED
                            self.audio.play('dash');continue
                        hit=(combat.sweep_hits(enemy.pos,enemy.attack_direction,self.state.pos) if enemy.kind=='brute' else V(self.state.pos).distance_to(enemy.strike)<42 and distance<78)
                        if hit and visible:self.hurt_player(enemy.spec['damage'],'Сцепщик бьёт широкой дугой. После замаха у него долгая пауза.' if enemy.kind=='brute' else 'Уходите от замаха. Q — сигнальная ракета.')
                        enemy.attack_state='recover';enemy.attack_timer=enemy.spec['recovery']
                        self.audio.play('metal' if enemy.kind=='brute' else 'dash')
                    else:enemy.attack_state='idle'
                continue
            if distance<enemy.spec['reach'] and visible:
                combat.begin_attack(enemy,self.state.pos)
                continue
            if visible:enemy.target=V(self.state.pos);enemy.interest=3
            if enemy.interest<=0:enemy.target=V(enemy.home)
            if enemy.target is not None:
                if enemy.repath<=0:enemy.path=path_to(self.state.scene,enemy.pos,enemy.target);enemy.repath=.7
                if enemy.path:
                    d=enemy.path[0]-enemy.pos
                    if d.length()<6:enemy.path.pop(0)
                    elif d.length_squared():
                        step=d.normalize()*min(d.length(),(enemy.spec['speed'] if visible and 'action_mode' in self.state.flags else 105 if visible else 70)*dt)
                        self.move_enemy(enemy,step)
        cable_phase=fieldwork.cable_phase(self.state.elapsed) if fieldwork.cable_present(self.state) else None
        if cable_phase!=self.cable_state:
            self.cable_state=cable_phase
            if cable_phase=='live':self.audio.play('electric')
        if cable_phase=='live' and self.hurt<=0:
            points=[V(self.state.pos)]
            if self.state.carrying:
                center,rear,_=self.carry_positions();points.extend((center,rear))
            if fieldwork.cable_touches(points):
                self.state.health-=18;self.hurt=1.3;self.audio.play('hurt')
                self.state.say('Разряд! Обойдите кабель по нижнему проходу — вместе с носилками.')
        if self.state.health<=0:self.mode='dead';self.selection=0
        self.autosave_timer+=dt
        if self.autosave_timer>30 and self.hurt<=0 and self.state.health>0:self.autosave_timer=0;self.save()

    def draw(self):
        width,height=self.display.get_size();ratio=min(width/1280,height/720);size=(max(1,int(1280*ratio)),max(1,int(720*ratio)))
        image=self.renderer.render_at(self,size)
        self.display.fill((0,0,0));self.display.blit(image,((width-size[0])//2,(height-size[1])//2));pg.display.flip()

    def run(self,frames=None):
        n=0
        while self.running:
            active_dt=self.clock.tick(60)/1000
            dt=min(.05,active_dt)
            for event in pg.event.get():self.event(event)
            self.update(dt,active_dt=active_dt);self.draw();n+=1
            if frames and n>=frames:break
        self.save_settings();pg.quit()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke-test',action='store_true');parser.add_argument('--screenshot')
    parser.add_argument('--screenshot-scene',choices=SCENES,default='platform')
    parser.add_argument('--screenshot-mode',choices=('play','power','winch','radio','gate','crossing','brake','inspection'),default='play')
    parser.add_argument('--screenshot-facing',choices=('front','back'),default='front')
    parser.add_argument('--screenshot-pos',type=float,nargs=2,metavar=('X','Y'))
    parser.add_argument('--render-size',type=int,nargs=2,default=SIZE,metavar=('WIDTH','HEIGHT'))
    parser.add_argument('--screenshot-action',action='store_true')
    parser.add_argument('--screenshot-field',choices=('relay','cable'))
    parser.add_argument('--screenshot-enemy',choices=('runner','brute'))
    parser.add_argument('--screenshot-hospital',choices=('winch','receive','pack'))
    args=parser.parse_args()
    if any(n<320 or n>7680 for n in args.render_size) or args.render_size[0]*9!=args.render_size[1]*16:parser.error('--render-size requires a 16:9 output between 320 and 7680 pixels')
    if args.screenshot_action and not args.screenshot:parser.error('--screenshot-action requires --screenshot')
    if args.screenshot_field and not args.screenshot:parser.error('--screenshot-field requires --screenshot')
    if args.screenshot_enemy and not args.screenshot:parser.error('--screenshot-enemy requires --screenshot')
    if args.screenshot_hospital and not args.screenshot:parser.error('--screenshot-hospital requires --screenshot')
    if args.screenshot_pos is not None:
        if not args.screenshot:parser.error('--screenshot-pos requires --screenshot')
        if not walkable(SCENES[args.screenshot_scene],args.screenshot_pos):parser.error('Screenshot position is outside the walkable floor')
    app=App()
    if args.screenshot:
        app.state.flags.update(('opening','nina_boarded','arrive','met_lida'))
        if args.screenshot_scene=='carriage':app.state.flags.update(('rescued','lida_boarded'))
        if args.screenshot_scene=='ward':app.state.flags.add('door_open')
        if args.screenshot_scene in ('hospital','refuge','power','yard','shed'):
            app.state.chapter=2
            app.state.flags.update(('rescued','lida_boarded','nina_after','chapter_complete','c2_arrived'))
            if args.screenshot_scene!='hospital':app.state.flags.update(('c2_intro','c2_refuge'))
        if args.screenshot_scene in ('settlement','relay_house','flat','switchyard','gantry'):
            app.state.chapter=3
            app.state.flags.update(('rescued','lida_boarded','nina_after','chapter_complete','c2_arrived','c2_gate_open','c2_boarded','c2_truth','c2_complete','c3_arrived'))
            if args.screenshot_mode=='radio':app.state.flags.update(('c3_repair','c3_notes'))
        if args.screenshot_scene in ('spillway','gallery','archive','dispatch','last_platform','signal_post','crossing','upper_platform'):
            app.state.chapter=4 if args.screenshot_scene in ('spillway','gallery','archive','dispatch') else 5
            app.state.flags.update(('c4_arrived',) if app.state.chapter==4 else ('c5_arrived',))
            if args.screenshot_scene=='upper_platform':app.state.flags.update(chapters.chapter5.REQUIRED)
            if args.screenshot_mode=='gate':app.state.flags.update(('c5_brake','c5_pavel_ready','c5_coupler'))
        position=args.screenshot_pos if args.screenshot_pos is not None else (840,625) if args.screenshot_scene=='platform' else None
        app.state.enter(args.screenshot_scene,position)
        app.mode=args.screenshot_mode
        if app.mode=='brake':
            app.state.flags.difference_update(('arrive','met_lida'))
            app.state.flags.add('c1_brake_started');app.state.puzzle='brake'
        if app.mode=='inspection':
            app.state.flags.difference_update(('arrive','met_lida'))
            app.state.flags.update(('c1_stop','c1_parked'));app.state.puzzle='inspection'
        if app.mode=='crossing':app.crossing_sequence=CrossingSequence(elapsed=8)
        app.facing=V(0,-1 if args.screenshot_facing=='back' else 1)
        if args.screenshot_action:
            app.state=combat.cold_open();app.loaded_scene=None;app.scene_changed(persist=False)
        if args.screenshot_field:
            app.state=combat.cold_open();app.state.dialogue=None
            app.state.flags.update(('combat_down_waiting_0','combat_down_waiting_1'))
            app.state.enter('waiting',(1280,360) if args.screenshot_field=='relay' else (1000,820))
            app.mode='play';app.loaded_scene=None;app.facing=V(1,-1) if args.screenshot_field=='relay' else V(-1,0)
            if args.screenshot_field=='cable':
                app.state.flags.update(('door_open','relay_nina','carry','action_return_live'))
                app.state.carrying=True;app.state.elapsed=1.3
            app.scene_changed(persist=False)
            if args.screenshot_field=='relay':
                app.field_task=fieldwork.create('relay');app.field_task.progress=.6
        if args.screenshot_enemy:
            app.state=combat.cold_open();app.state.dialogue=None;app.state.pos=[600,720]
            app.mode='play';app.loaded_scene=None;app.scene_changed(persist=False)
            enemy=Enemy((760,720),args.screenshot_enemy);app.enemies=[enemy]
            combat.begin_attack(enemy,app.state.pos);enemy.attack_timer=.25;enemy.facing=V(-1,0)
            app.facing=V(1,0)
        if args.screenshot_hospital:
            app.state=combat.cold_open();app.state.dialogue=None;app.state.chapter=2
            app.state.flags.update(('rescued','lida_boarded','nina_after','chapter_complete','c2_arrived','c2_intro','c2_refuge','c2_winch'))
            scene,pos,kind={'winch':('hospital',(810,360),'c2_rhythm'),'receive':('carriage',(520,580),'c2_receive'),'pack':('refuge',(380,530),'c2_pack')}[args.screenshot_hospital]
            app.state.enter(scene,pos);app.mode='play';app.loaded_scene=None;app.scene_changed(persist=False)
            if args.screenshot_hospital=='winch':app.state.winch={'stage':'turn','turns':2}
            app.field_task=fieldwork.create(kind);app.field_task.progress=.6;app.facing=V(0,-1)
        pg.image.save(app.renderer.render_at(app,tuple(args.render_size)),args.screenshot);pg.quit()
    else:app.run(90 if args.smoke_test else None)
