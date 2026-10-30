"""Exercise a sortie through keyboard/mouse events and ordinary update ticks."""
from collections import defaultdict
import pygame as pg
from lasttrain.app import V,path_to,blocked
from lasttrain.content import SCENES,DIALOGUES
from lasttrain import combat
from lasttrain import hospital_action
from lasttrain.mechanics import PowerBoard


class Driver:
    def __init__(self,app,on_frame=None):self.app=app;self.on_frame=on_frame;self.frames=0

    def tick(self,seconds=1/60,keys=None):
        for _ in range(max(1,round(seconds*60))):
            self.app.update(1/60,keys or defaultdict(int));self.frames+=1
            if self.on_frame is not None:self.on_frame(self)
            if self.app.mode=='dead':raise AssertionError('Sortie controller died')

    @staticmethod
    def keys(direction):
        keys=defaultdict(int)
        if abs(direction.x)>3:keys[pg.K_d if direction.x>0 else pg.K_a]=1
        if abs(direction.y)>3:keys[pg.K_s if direction.y>0 else pg.K_w]=1
        return keys

    def walk(self,point):
        app=self.app;radius=24 if app.state.carrying else 17
        path=path_to(app.state.scene,app.state.pos,point,radius)
        if not path:raise AssertionError(('No route',app.state.scene,app.state.pos,point))
        for waypoint in path:
            for _ in range(240):
                direction=waypoint-V(app.state.pos)
                if direction.length()<6:break
                self.tick(keys=self.keys(direction))
            else:raise AssertionError(('Blocked route',app.state.scene,app.state.pos,waypoint))
        if V(app.state.pos).distance_to(point)>50:raise AssertionError(('Partial route',point,app.state.pos))

    def finish_dialogue(self,choice=0):
        for _ in range(80):
            app=self.app
            if not app.state.dialogue:return
            data=DIALOGUES[app.state.dialogue]
            if self.on_frame is not None:self.tick(1.5)
            if app.state.dialogue is None:return
            if app.state.line>=len(data['lines']):app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_1+choice))
            else:app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN))
        raise AssertionError('Dialogue did not finish')

    def use(self,key,choice=0):
        app=self.app
        if app.state.dialogue:self.finish_dialogue()
        scene=SCENES[app.state.scene];obj=next(o for o in scene.objects if o.id==key)
        approaches=[]
        for dx,dy in ((0,60),(0,-60),(60,0),(-60,0),(0,0),(55,55),(-55,55),(55,-55),(-55,-55)):
            point=V(obj.pos)+V(dx,dy)
            if blocked(app.state.scene,point,24 if app.state.carrying else 17):continue
            target=app.nearby(point)
            if target is None or target.id!=key:continue
            path=path_to(app.state.scene,app.state.pos,point,24 if app.state.carrying else 17)
            endpoint=app.nearby(path[-1]) if path else None
            stable=path and all((candidate:=app.nearby(path[-1]+V(offset))) is not None and candidate.id==key for offset in ((6,0),(-6,0),(0,6),(0,-6)))
            if path and path[-1].distance_to(obj.pos)<85 and endpoint is not None and endpoint.id==key and stable:approaches.append((len(path),point))
        if not approaches:raise AssertionError(('No approach',app.state.scene,key))
        self.walk(min(approaches,key=lambda p:p[0])[1])
        if app.nearby() is None or app.nearby().id!=key:raise AssertionError(('Wrong target',key,app.nearby()))
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_e))
        if app.field_task is not None:
            for _ in range(240):
                if app.field_task is None or app.field_task.kind=='c2_rhythm':break
                self.tick(keys=defaultdict(int,{pg.K_e:1}))
            else:raise AssertionError('Field work did not complete')
        if app.field_task is not None and app.field_task.kind=='c2_rhythm':
            for _ in range(4-app.state.winch['turns']):
                for _ in range(90):
                    if hospital_action.beat_ready(app.field_task):break
                    self.tick()
                else:raise AssertionError('Winch beat did not arrive')
                app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_e));self.tick(.45)
            self.use('switch');return
        self.finish_dialogue(choice)

    def solve_power(self):
        app=self.app
        if app.mode!='power':raise AssertionError('Not at power board')
        for index,target in enumerate(PowerBoard.solution):
            if index in PowerBoard.fixed or index not in PowerBoard.sockets:continue
            while app.puzzle_selected//5!=index//5:
                app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_DOWN));self.tick(.05)
            while app.puzzle_selected%5!=index%5:
                app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RIGHT));self.tick(.05)
            for _ in range((target-app.state.power[index])%4):
                app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_e));self.tick(.12)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN));self.tick(.2)
        if app.mode!='play' or 'c2_power_ready' not in app.state.flags:raise AssertionError('Power route did not pass')

    def hospital_sortie(self,route='manual',answer=0):
        for key in ('nina','refuge','lida','supplies','exit','train','nina','cabin','yard'):self.use(key)
        self.fight()
        for key in ('shed','cable' if route=='electric' else 'winch','exit','exit'):self.use(key)
        if route=='electric':
            self.use('power');self.use('board');self.solve_power();self.use('exit')
        self.use('switch')
        for key in ('refuge','lida'):self.use(key)
        self.use('nina',answer);self.use('map')
        return self.app.state

    def fight(self):
        app=self.app
        for _ in range(2400):
            if not app.enemies:return
            threats=[e for e in app.enemies if e.attack_state=='windup' and
                     ((e.kind=='runner' and combat.segment_hits(e.attack_origin,e.strike,app.state.pos,50)) or
                      (e.kind=='brute' and combat.sweep_hits(e.pos,e.attack_direction,app.state.pos)))]
            if threats:
                threat=min(threats,key=lambda e:e.pos.distance_to(app.state.pos))
                direction=V(-threat.attack_direction.y,threat.attack_direction.x) if threat.kind=='runner' else V(app.state.pos)-threat.pos
                if direction.length_squared():direction.normalize_ip()
                options=(direction,-direction,V(-direction.y,direction.x),V(direction.y,-direction.x))
                direction=next((d for d in options if all(not blocked(app.state.scene,V(app.state.pos)+d*i,14) for i in range(16,129,16))),direction)
                self.tick(keys=self.keys(direction*100))
                if app.dash_cooldown<=0:app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_SPACE))
                self.tick(keys=self.keys(direction*100));continue
            enemy=min(app.enemies,key=lambda e:e.pos.distance_to(app.state.pos));delta=enemy.pos-V(app.state.pos)
            if combat.strike_hits(app.state.scene,app.state.pos,delta.normalize() if delta.length_squared() else (1,0),enemy.pos):
                app.renderer.camera_for(app.state.scene,app.state.pos)
                point=enemy.pos-app.renderer.camera;w,h=app.display.get_size();ratio=min(w/1280,h/720)
                point=point*ratio+V((w-1280*ratio)/2,(h-720*ratio)/2)
                app.event(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=tuple(point)))
                self.tick()
            else:
                path=path_to(app.state.scene,app.state.pos,enemy.pos)
                self.tick(keys=self.keys(path[0]-V(app.state.pos) if path else delta))
        raise AssertionError('Combat did not resolve')

    def sortie(self,tool=False,choice=0):
        self.fight()
        if tool:
            for key in ('workshop_door','stopper','exit'):self.use(key)
        for key in ('relay','ward_door','patient','exit'):self.use(key)
        self.walk((1360,820));self.walk((1120,820));self.walk((440,820));self.use('exit')
        self.walk((1370,560));self.walk((1040,560));self.walk((650,560))
        self.use('train');self.use('lida',choice)
        return self.app.state
