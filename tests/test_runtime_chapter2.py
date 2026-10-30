import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App, V, blocked, path_to
from lasttrain.content import SCENES, DIALOGUES
from lasttrain.mechanics import PowerBoard
from test_chapter2 import start_second
from test_story import rescue,finish

class SecondChapterRuntimeTests(unittest.TestCase):
    def test_optional_address_card_is_reachable_through_real_interactions(self):
        from test_chapter2 import start_second
        app=self.app;app.state=start_second();app.mode='play';app.loaded_scene=None;app.scene_changed()
        for key in ('refuge','raisa','roster'):self.use(key)
        self.assertIn('Раиса',app.renderer.portraits)
        self.assertIn('c2_card_written',app.state.flags)
        app.action('load');self.assertIn('c2_card_written',app.state.flags)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.app=App(Path(self.temp.name)/'save.json')

    def tearDown(self):
        pg.quit();self.temp.cleanup()

    def finish_dialogue(self,choice=0):
        app=self.app
        for _ in range(60):
            if not app.state.dialogue:return
            data=DIALOGUES[app.state.dialogue]
            if app.state.line>=len(data['lines']):app.action(('choice',choice))
            else:app.advance_dialogue()
        self.fail('Conversation failed to terminate')

    def use(self,key):
        app=self.app;scene=SCENES[app.state.scene]
        obj=next(o for o in scene.objects if o.id==key)
        candidates=[]
        for dx,dy in ((0,60),(0,-60),(60,0),(-60,0),(0,0)):
            p=V(obj.pos)+V(dx,dy)
            if blocked(app.state.scene,p):continue
            path=path_to(app.state.scene,app.state.pos,p)
            if path and path[-1].distance_to(obj.pos)<85:candidates.append(path)
        self.assertTrue(candidates,key)
        for point in min(candidates,key=len):
            for _ in range(100):
                delta=point-V(app.state.pos)
                if delta.length()<2:break
                app.move(delta.normalize()*min(4,delta.length()))
        self.assertIsNotNone(app.nearby(),key)
        self.assertEqual(app.nearby().id,key)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_e))
        self.finish_dialogue()

    def test_travel_from_first_chapter_with_pause_and_load(self):
        app=self.app;s=rescue();s.interact('nina');finish(s);s.interact('map');finish(s)
        app.state=s;app.mode='chapter_end';app.save()
        app.action('next_chapter');self.finish_dialogue()
        self.assertEqual(app.mode,'drive');self.assertTrue(app.travel_active)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE))
        app.action('settings');app.action(('setting',3));app.action('save')
        self.assertEqual(app.mode,'pause')
        self.assertEqual(app.state.load(app.save_path).chapter,1)
        app.action('resume');self.assertEqual(app.mode,'drive')
        app.drive_distance=600;app.speed=0;app.update(.02,defaultdict(int));self.finish_dialogue()
        self.assertEqual((app.mode,app.state.scene,app.state.chapter),('play','hospital',2))
        app.action('menu');app.action('load')
        self.assertEqual(app.state.scene,'hospital')

    def test_physical_routes_and_real_puzzle_input(self):
        for route in ('electric','manual'):
            with self.subTest(route=route):
                app=self.app;app.state=start_second();app.mode='play';app.travel_active=False;app.loaded_scene=None;app.scene_changed()
                for key in ('nina','refuge','lida','exit','yard','shed'):
                    self.use(key)
                self.use('cable' if route=='electric' else 'winch')
                for key in ('exit','exit'):self.use(key)
                if route=='electric':
                    self.use('power');self.use('board')
                    self.assertEqual(app.mode,'power')
                    app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN))
                    self.assertEqual(app.mode,'power')
                    for i in PowerBoard.sockets:
                        if i in PowerBoard.fixed:continue
                        app.puzzle_selected=i
                        for _ in range((PowerBoard.solution[i]-app.state.power[i])%4):
                            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_e))
                    app.draw()
                    app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN))
                    self.assertEqual(app.mode,'play')
                    self.use('exit');self.use('switch')
                else:
                    self.use('switch');self.assertEqual(app.mode,'winch')
                    app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_SPACE))
                    self.assertEqual(app.state.winch['stage'],'load')
                    for key in (pg.K_e,pg.K_SPACE,pg.K_e,pg.K_e,pg.K_e,pg.K_e,pg.K_SPACE):
                        app.event(pg.event.Event(pg.KEYDOWN,key=key))
                    self.finish_dialogue();self.assertEqual(app.mode,'play')
                for key in ('train','nina','cabin','refuge','supplies','lida','nina','map'):self.use(key)
                self.assertIn('c2_complete',app.state.flags)
                self.assertEqual(app.mode,'chapter_end')
                self.assertEqual(app.state.load(app.save_path).choices['power_route'],route)

if __name__=='__main__':unittest.main()
