import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App
from lasttrain.content import DIALOGUES
from test_chapter5 import start_fifth,FINAL_ROUTE,finish_fourth
import test_runtime_chapter2 as runtime2

class FifthChapterRuntimeTests(unittest.TestCase):
    use=runtime2.SecondChapterRuntimeTests.use
    finish_dialogue=runtime2.SecondChapterRuntimeTests.finish_dialogue

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.app=App(Path(self.temp.name)/'save.json')

    def tearDown(self):pg.quit();self.temp.cleanup()

    def test_physical_final_stop_and_saved_ending(self):
        app=self.app;app.state=start_fifth();app.mode='play';app.loaded_scene=None;app.scene_changed()
        for key in FINAL_ROUTE:
            self.use(key)
            if key=='walkway':
                self.assertEqual(app.mode,'crossing');app.draw()
                self.assertNotIn('c5_crossed',app.state.flags)
                app.update(2);time=app.crossing_sequence.elapsed
                app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE));app.update(1)
                self.assertEqual(app.crossing_sequence.elapsed,time)
                self.assertFalse(app.save())
                app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE))
                for _ in range(340):app.update(.05)
                self.assertIsNone(app.crossing_sequence);self.finish_dialogue()
                self.assertIn('c5_crossed',app.state.flags)
            if key=='gate':
                self.assertEqual(app.mode,'gate');app.draw()
                for control in (pg.K_1,pg.K_2,pg.K_3):
                    app.event(pg.event.Event(pg.KEYDOWN,key=control));app.update(.05);app.draw()
                for _ in range(30):app.update(.05);app.draw()
                self.assertGreater(app.renderer.gate_visual,.99)
                self.assertGreater(app.renderer.pin_visual,.99)
                app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE))
                self.assertEqual(app.mode,'play')
                self.use('gate');self.assertEqual(app.mode,'gate')
                app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN));self.finish_dialogue()
                self.assertIn('c5_gate',app.state.flags)
                before=set(app.state.flags);app.action('gate_swing');self.assertEqual(app.state.flags,before)
        self.assertEqual(app.mode,'chapter_end')
        self.assertEqual(app.state.choices['ending'],'testimony')
        app.draw();app.action('load');app.draw()
        self.assertEqual(app.mode,'chapter_end')
        self.assertEqual(app.state.scene,'upper_platform')

    def test_return_dialogue_leads_to_final_screen(self):
        app=self.app;app.state=finish_fourth();app.mode='play';app.loaded_scene=None;app.scene_changed()
        app.state.start_dialogue('c5_departure')
        while app.state.line<len(DIALOGUES[app.state.dialogue]['lines']):
            app.advance_dialogue()
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_2));self.finish_dialogue()
        self.assertEqual(app.mode,'chapter_end');self.assertEqual(app.state.choices['ending'],'return')
        app.draw()

        app.action('load')
        self.assertEqual(app.state.choices['ending'],'return')
        app.action('replay_route')
        self.assertEqual(app.state.chapter,4)
        self.assertEqual(app.state.dialogue,'c5_departure')
        self.assertNotIn('ending',app.state.choices)
        self.assertIn('c4_complete',app.state.flags)
        self.finish_dialogue()
        self.assertEqual(app.mode,'drive')
        self.assertEqual(app.state.chapter,5)

    def test_signal_lever_moves_after_confirmed_operation(self):
        app=self.app;app.state=start_fifth();app.state.enter('signal_post');app.mode='play'
        app.draw();self.assertEqual(app.renderer.signal_visual,0)
        self.assertEqual(set(app.renderer.signal_lever),{'shaft','base'})
        from lasttrain.content import SCENES
        lever=next(o for o in SCENES['signal_post'].objects if o.id=='lever')
        anchor=pg.Vector2(lever.pos)+pg.Vector2(0,-90)-app.renderer.camera
        region=pg.Rect(anchor.x-100,anchor.y-110,200,140)
        initial=pg.image.tobytes(app.renderer.surface.subsurface(region),'RGB')
        app.state.flags.add('c5_semaphore')
        app.update(.05);app.draw()
        intermediate=pg.image.tobytes(app.renderer.surface.subsurface(region),'RGB')
        self.assertNotEqual(initial,intermediate)
        self.assertGreater(app.renderer.signal_visual,0)
        self.assertLess(app.renderer.signal_visual,1)
        for _ in range(35):app.update(.05);app.draw()
        self.assertGreater(app.renderer.signal_visual,.99)
        final=pg.image.tobytes(app.renderer.surface.subsurface(region),'RGB')
        self.assertNotEqual(intermediate,final)

    def test_missing_route_checkpoint_does_not_replace_ending(self):
        app=self.app;app.state=finish_fourth();app.state.start_dialogue('c5_return')
        app.mode='play';self.finish_dialogue()
        before=app.state.snapshot();app.action('replay_route')
        self.assertEqual(app.state.snapshot(),before)
        self.assertEqual(app.mode,'chapter_end')
        self.assertIn('не найдена',app.menu_notice)
