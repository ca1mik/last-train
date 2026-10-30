import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
from pathlib import Path
import unittest
import pygame as pg
from lasttrain.app import App, blocked, path_to, V
from lasttrain.content import SCENES

class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.app=App(Path(cls.temp.name)/'save.json')

    @classmethod
    def tearDownClass(cls):pg.quit();cls.temp.cleanup()

    def test_every_interactable_has_walkable_approach(self):
        for key,scene in SCENES.items():
            for obj in scene.objects:
                candidates=[V(obj.pos)+V(dx,dy) for dx,dy in ((0,60),(0,-60),(60,0),(-60,0),(0,0))]
                reachable=False
                for point in candidates:
                    if blocked(key,point):continue
                    path=path_to(key,scene.start,point)
                    if path and path[-1].distance_to(obj.pos)<90:
                        reachable=True;break
                with self.subTest(scene=key,obj=obj.id):self.assertTrue(reachable)

    def test_render_all_scenes_and_modes(self):
        app=self.app
        for key,scene in SCENES.items():
            app.state.enter(key);app.mode='play';app.scene_changed();app.draw()
        app.state.start_dialogue('lida_refusal');app.draw()
        app.state.line=3;app.draw()
        app.state.dialogue=None
        for mode in ('menu','pause','settings','journal','dead','chapter_end','confirm_new','drive','power','winch','radio'):
            app.mode=mode;app.draw()

    def test_collision_stops_high_speed_motion(self):
        app=self.app;app.state.enter('cabin',(400,700))
        app.move(V(-1000,0))
        self.assertGreater(app.state.pos[0],300)
        self.assertFalse(blocked('cabin',app.state.pos))

    def test_drive_resume_survives_settings(self):
        app=self.app;app.mode='drive'
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE))
        self.assertEqual(app.mode,'pause')
        app.action('settings');app.action(('setting',3))
        self.assertEqual(app.mode,'pause')
        app.action('resume');self.assertEqual(app.mode,'drive')

    def test_physical_rescue_route(self):
        from test_story import finish
        app=self.app;app.new(action=False);finish(app.state)
        def use(key,choice=0):
            scene=SCENES[app.state.scene]
            if app.state.carrying:
                points=((1360,820),(1120,820),(440,820)) if app.state.scene=='waiting' and key=='exit' else ((1370,560),(1040,560),(650,560)) if app.state.scene=='platform' and key=='train' else ()
                for target in points:
                    for waypoint in path_to(app.state.scene,app.state.pos,target,24):
                        for _ in range(150):
                            delta=waypoint-V(app.state.pos)
                            if delta.length()<2:break
                            app.move(delta.normalize()*min(4,delta.length()))
            obj=next(o for o in scene.objects if o.id==key)
            approaches=[]
            for dx,dy in ((0,60),(0,-60),(60,0),(-60,0),(0,0)):
                p=V(obj.pos)+V(dx,dy)
                if not blocked(app.state.scene,p):
                    path=path_to(app.state.scene,app.state.pos,p,24 if app.state.carrying else 17)
                    if path and path[-1].distance_to(obj.pos)<85:approaches.append(path)
            self.assertTrue(approaches,key)
            for point in min(approaches,key=len):
                for _ in range(100):
                    delta=point-V(app.state.pos)
                    if delta.length()<2:break
                    app.move(delta.normalize()*min(4,delta.length()))
            self.assertIsNotNone(app.nearby(),(app.state.scene,key,app.state.pos))
            self.assertEqual(app.nearby().id,key)
            app.interact();finish(app.state,choice);app.scene_changed()
        use('cabin_door');use('controls')
        from test_story import brake_check
        brake_check(app.state)
        app.state.start_dialogue('loop');finish(app.state)
        from test_story import disembark
        disembark(app.state);app.mode='play';app.scene_changed()
        for key in ('lida','station_door'):use(key)
        use('relay',1)
        for key in ('workshop_door','stopper','note','exit','relay','ward_door','patient','exit','exit','train','lida','nina','map'):use(key)
        self.assertIn('chapter_complete',app.state.flags)

    def test_gait_stops_when_collision_stops_the_player(self):
        from collections import defaultdict
        from lasttrain.model import Session
        app=self.app;app.state=Session();app.state.enter('cabin',(400,700));app.mode='play'
        app.loaded_scene='cabin';app.enemies=[]
        app.move(V(-1000,0));app.walk_phase=1.23
        app.update(.05,defaultdict(int,{pg.K_a:1}))
        self.assertFalse(app.moving)
        self.assertEqual(app.walk_phase,1.23)

    def test_attack_has_warning_dodge_and_flare_interrupt(self):
        from collections import defaultdict
        from lasttrain.model import Session
        from lasttrain.app import Enemy
        app=self.app;app.state=Session();app.state.enter('waiting',(1150,700));app.mode='play'
        app.loaded_scene='waiting';app.hurt=0;app.enemies=[Enemy((1150,745))]
        keys=defaultdict(int)
        app.update(.1,keys)
        self.assertEqual(app.state.health,100)
        self.assertEqual(app.enemies[0].attack_state,'windup')
        app.update(.2,keys);self.assertEqual(app.state.health,100)
        app.update(.2,keys);self.assertEqual(app.state.health,76)
        self.assertEqual(app.enemies[0].attack_state,'recover')
        app.state.health=100;app.hurt=0;app.enemies=[Enemy((1150,745))]
        app.update(.1,keys);app.state.pos=[1320,700];app.update(.5,keys)
        self.assertEqual(app.state.health,100)
        app.state.pos=[1150,700];app.enemies=[Enemy((1150,745))];app.update(.1,keys)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_q));app.update(.5,keys)
        self.assertEqual(app.state.health,100)
        self.assertEqual(app.enemies[0].attack_state,'idle')
        self.assertGreater(app.enemies[0].stun,0)

if __name__=='__main__':unittest.main()
