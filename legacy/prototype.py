import os, sys, math, random, json
from pathlib import Path
import pygame as pg

TITLE = 'Последний рейс'
W, H = 1280, 720
WORLD = pg.Rect(0, 0, 2600, 2200)
SAVE = Path(os.getenv('LOCALAPPDATA', str(Path.home()))) / 'LastTrain' / 'save.json'
V = pg.Vector2

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((W,H), pg.RESIZABLE)
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont('segoeui', 19)
        self.big = pg.font.SysFont('segoeui', 54, bold=True)
        self.small = pg.font.SysFont('segoeui', 15)
        self.running = True
        self.mode = 'menu'
        self.reset()

    def reset(self):
        self.rng = random.Random(47)
        self.pos = V(1300,1150)
        self.hp = 100.0
        self.scrap = self.parts = self.kills = self.level = 0
        self.elapsed = self.fire = self.hurt = self.spawn = 0.0
        self.bullets, self.enemies, self.particles = [], [], []
        self.train = pg.Rect(1190, 930, 220, 100)
        self.buildings = []
        for x in range(220,2500,420):
            for y in range(180,2100,390):
                r = pg.Rect(x,y, self.rng.randint(160,240),self.rng.randint(140,220))
                if not r.colliderect(pg.Rect(1030,800,570,550)):
                    self.buildings.append(r)
        self.crates=[]
        while len(self.crates)<32:
            p=V(self.rng.randint(90,2510),self.rng.randint(90,2110))
            if not any(r.inflate(80,80).collidepoint(p) for r in self.buildings) and p.distance_to(self.pos)>180:
                self.crates.append(p)
        self.message='Найдите 8 деталей в ящиках и вернитесь к поезду.'
        self.msg_time=8

    def save(self):
        SAVE.parent.mkdir(parents=True,exist_ok=True)
        data={k:getattr(self,k) for k in ['hp','scrap','parts','kills','level','elapsed']}
        data['pos']=list(self.pos)
        data['crates']=[list(p) for p in self.crates]
        tmp=SAVE.with_suffix('.tmp')
        tmp.write_text(json.dumps(data),encoding='utf-8')
        tmp.replace(SAVE)

    def load(self):
        try:
            d=json.loads(SAVE.read_text(encoding='utf-8'))
            self.reset()
            for k in ['hp','scrap','parts','kills','level','elapsed']: setattr(self,k,d[k])
            self.pos=V(d['pos']); self.crates=[V(p) for p in d['crates']]
            self.mode='play'
        except (OSError,ValueError,KeyError,TypeError):
            self.message='Сохранение не найдено. Начните новую игру.';self.msg_time=4

    def text(self,s,x,y,color=(220,228,225),font=None):
        self.screen.blit((font or self.font).render(s,True,color),(x,y))

    def move(self,p,delta,radius):
        for axis in [0,1]:
            p[axis]+=delta[axis]
            box=pg.Rect(p.x-radius,p.y-radius,radius*2,radius*2)
            if any(box.colliderect(r) for r in self.buildings): p[axis]-=delta[axis]
        p.x=max(radius,min(WORLD.w-radius,p.x));p.y=max(radius,min(WORLD.h-radius,p.y))

    def interact(self):
        for p in self.crates[:]:
            if p.distance_to(self.pos)<68:
                self.crates.remove(p);self.parts+=1;self.scrap+=7;self.hp=min(100,self.hp+9)
                self.message='Деталь найдена. +7 металлолома';self.msg_time=3;self.save();return
        if V(self.train.center).distance_to(self.pos)<190:
            if self.parts>=8: self.mode='win'
            else: self.message=f'Для ремонта нужно ещё {8-self.parts} деталей.';self.msg_time=3

    def update(self,dt):
        self.elapsed+=dt;self.fire-=dt;self.hurt-=dt;self.msg_time-=dt
        keys=pg.key.get_pressed()
        d=V(int(keys[pg.K_d] or keys[pg.K_RIGHT])-int(keys[pg.K_a] or keys[pg.K_LEFT]),int(keys[pg.K_s] or keys[pg.K_DOWN])-int(keys[pg.K_w] or keys[pg.K_UP]))
        if d.length_squared(): self.move(self.pos,d.normalize()*(290 if keys[pg.K_LSHIFT] else 190)*dt,16)
        cam=self.pos-V(self.screen.get_size())/2
        aim=V(pg.mouse.get_pos())+cam-self.pos
        if pg.mouse.get_pressed()[0] and self.fire<=0 and aim.length_squared():
            v=aim.normalize();self.bullets.append([self.pos+v*23,v*780,1.2]);self.fire=max(.10,.28-self.level*.035)
        night=int(self.elapsed//65)%2==1
        self.spawn-=dt
        if self.spawn<=0 and len(self.enemies)<45:
            angle=self.rng.random()*math.tau
            p=self.pos+V(math.cos(angle),math.sin(angle))*650
            p.x=max(25,min(2575,p.x));p.y=max(25,min(2175,p.y))
            if not any(r.inflate(40,40).collidepoint(p) for r in self.buildings):
                self.enemies.append([p, 55+int(self.elapsed/120)*15])
            self.spawn=.65 if night else 1.8
        for b in self.bullets[:]:
            b[0]+=b[1]*dt;b[2]-=dt
            hit=next((e for e in self.enemies if e[0].distance_to(b[0])<23),None)
            if hit:
                hit[1]-=30+self.level*9
                if hit[1]<=0:
                    self.enemies.remove(hit);self.kills+=1;self.scrap+=2
                    for _ in range(7): self.particles.append([V(hit[0]),V(self.rng.uniform(-90,90),self.rng.uniform(-90,90)),.4])
            if hit or b[2]<=0 or any(r.collidepoint(b[0]) for r in self.buildings): self.bullets.remove(b)
        for e in self.enemies:
            d=self.pos-e[0]
            if d.length_squared():self.move(e[0],d.normalize()*(105 if night else 73)*dt,17)
            if d.length()<34 and self.hurt<=0: self.hp-=12;self.hurt=.7
        for p in self.particles[:]:
            p[0]+=p[1]*dt;p[2]-=dt
            if p[2]<=0:self.particles.remove(p)
        if self.hp<=0:self.mode='dead'

    def draw_world(self):
        sw,sh=self.screen.get_size();cam=self.pos-V(sw,sh)/2
        def pt(p):return (round(p[0]-cam.x),round(p[1]-cam.y))
        def rect(r):return pg.Rect(r.x-cam.x,r.y-cam.y,r.w,r.h)
        self.screen.fill((20,30,33))
        for x in range(0,2600,80):pg.draw.line(self.screen,(26,37,39),pt((x,0)),pt((x,2200)))
        for y in range(0,2200,80):pg.draw.line(self.screen,(26,37,39),pt((0,y)),pt((2600,y)))
        for x in [1245,1355]:pg.draw.line(self.screen,(77,82,77),pt((x,0)),pt((x,2200)),5)
        for y in range(0,2200,35):pg.draw.line(self.screen,(55,58,52),pt((1228,y)),pt((1372,y)),5)
        for r in self.buildings:
            pg.draw.rect(self.screen,(10,18,22),rect(r.move(9,12)),border_radius=5)
            pg.draw.rect(self.screen,(48,62,65),rect(r),border_radius=5)
            pg.draw.rect(self.screen,(72,85,84),rect(r),2,border_radius=5)
            for x in range(r.x+20,r.right-15,38):pg.draw.rect(self.screen,(104,114,92),rect(pg.Rect(x,r.y+18,13,8)))
        pg.draw.rect(self.screen,(43,99,95),rect(self.train),border_radius=17)
        for x in range(1220,1390,48):pg.draw.rect(self.screen,(158,191,168),rect(pg.Rect(x,950,28,28)),border_radius=4)
        self.text('ПОСЛЕДНИЙ РЕЙС',*pt((1192,900)),(117,204,180),self.small)
        for p in self.crates:
            pg.draw.circle(self.screen,(51,65,44),pt(p),25)
            r=pg.Rect(0,0,25,25);r.center=pt(p)
            pg.draw.rect(self.screen,(192,155,80),r,border_radius=3);pg.draw.line(self.screen,(70,58,38),r.topleft,r.bottomright,3)
            if p.distance_to(self.pos)<68:self.text('E — обыскать',*pt(p+V(-48,-45)),(245,213,130),self.small)
        for e in self.enemies:
            pg.draw.circle(self.screen,(21,20,26),pt(e[0]+V(3,5)),20)
            pg.draw.circle(self.screen,(153,67,72),pt(e[0]),17)
            pg.draw.circle(self.screen,(255,179,112),pt(e[0]+V(-5,-4)),3)
        for b in self.bullets:pg.draw.circle(self.screen,(255,224,142),pt(b[0]),4)
        for p in self.particles:pg.draw.circle(self.screen,(185,97,78),pt(p[0]),3)
        center=pt(self.pos)
        pg.draw.circle(self.screen,(111,211,183) if self.hurt<=0 else (248,139,119),center,16)
        aim=V(pg.mouse.get_pos())-V(center)
        if aim.length_squared():pg.draw.line(self.screen,(216,220,191),center,V(center)+aim.normalize()*28,7)
        if int(self.elapsed//65)%2:
            shade=pg.Surface((sw,sh),pg.SRCALPHA);shade.fill((4,8,24,100));pg.draw.circle(shade,(0,0,0,0),center,175);self.screen.blit(shade,(0,0))
        pg.draw.rect(self.screen,(12,20,25),(0,0,sw,88))
        self.text('ПОСЛЕДНИЙ РЕЙС',24,13,(116,213,186))
        self.text(f'ДЕТАЛИ  {self.parts}/8      МЕТАЛЛ  {self.scrap}      ОРУЖИЕ  {self.level+1}',300,16)
        self.text(('НОЧЬ — существа быстрее' if int(self.elapsed//65)%2 else 'ДЕНЬ — ищите припасы'),sw-340,17,(218,173,113))
        pg.draw.rect(self.screen,(65,43,48),(24,49,230,12),border_radius=5)
        pg.draw.rect(self.screen,(107,200,160),(24,49,max(0,self.hp)*2.3,12),border_radius=5)
        self.text('WASD — движение  •  Мышь — прицел / огонь  •  Shift — бег  •  E — действие  •  U — улучшение (15)  •  Esc — пауза',24,sh-32,(164,182,185),self.small)
        if self.msg_time>0:self.text(self.message,300,51,(240,209,147),self.small)
        # Compass points toward the next objective.
        target=V(self.train.center) if self.parts>=8 else min(self.crates,key=lambda p:p.distance_to(self.pos),default=V(self.train.center))
        delta=target-self.pos
        if delta.length()>90:
            p=V(sw/2,sh/2)+delta.normalize()*110
            pg.draw.circle(self.screen,(227,189,103),p,5)
            self.text(f'{int(delta.length()/10)} м',p.x+10,p.y-10,(227,189,103),self.small)
        if V(self.train.center).distance_to(self.pos)<190:self.text('E — починить поезд и уехать',sw/2-145,sh/2+65,(239,210,139))

    def draw(self):
        self.draw_world()
        if self.mode!='play':
            sw,sh=self.screen.get_size();s=pg.Surface((sw,sh),pg.SRCALPHA);s.fill((5,12,18,220));self.screen.blit(s,(0,0))
            x=sw//2-300;y=sh//2-165
            title={'menu':TITLE,'pause':'Пауза','dead':'Город забрал ещё одного','win':'Поезд отправляется'}[self.mode]
            self.text(title,x,y,(126,220,189),self.big)
            lines={'menu':['Город опустел. Но ночью он оживает.','Соберите 8 деталей, восстановите поезд и выберитесь.','','Enter — новая игра','C — продолжить сохранение','Esc — выйти'], 'pause':['Enter — продолжить','F5 — сохранить','Esc — сохранить и выйти в меню'], 'dead':[f'Деталей: {self.parts}/8   •   Уничтожено существ: {self.kills}','','Enter — попробовать снова','Esc — в меню'], 'win':[f'Вы выбрались за {int(self.elapsed//60)} мин {int(self.elapsed%60)} сек.','Первый район пройден. Это конец прототипа.','','Enter — новая экспедиция','Esc — в меню']}[self.mode]
            for i,line in enumerate(lines):self.text(line,x,y+95+i*34)
        pg.display.flip()

    def run(self,frames=None):
        n=0
        while self.running:
            dt=min(self.clock.tick(60)/1000,.05)
            for event in pg.event.get():
                if event.type==pg.QUIT:
                    if self.mode in ['play','pause']:self.save()
                    self.running=False
                if event.type==pg.KEYDOWN:
                    k=event.key
                    if k==pg.K_RETURN and self.mode!='play':
                        if self.mode!='pause':self.reset()
                        self.mode='play'
                    elif k==pg.K_c and self.mode=='menu':self.load()
                    elif k==pg.K_ESCAPE:
                        if self.mode=='play':self.mode='pause'
                        elif self.mode=='pause':self.save();self.mode='menu'
                        elif self.mode=='menu':self.running=False
                        else:self.mode='menu'
                    elif self.mode=='play':
                        if k==pg.K_e:self.interact()
                        if k==pg.K_u and self.scrap>=15 and self.level<5:
                            self.scrap-=15;self.level+=1;self.message='Оружие улучшено: выше урон и скорострельность.';self.msg_time=3
                    if k==pg.K_F5 and self.mode in ['play','pause']:self.save();self.message='Игра сохранена';self.msg_time=3
            if self.mode=='play':self.update(dt)
            self.draw();n+=1
            if frames and n>=frames:break
        pg.quit()

if __name__=='__main__':
    game=Game()
    if '--smoke-test' in sys.argv:
        game.mode='play';game.run(120)
    else:game.run()
