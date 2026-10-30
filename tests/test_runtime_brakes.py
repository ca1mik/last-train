import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App
from lasttrain.model import Session
import test_runtime_chapter2 as runtime2

class BrakeRuntimeTests(unittest.TestCase):
    use=runtime2.SecondChapterRuntimeTests.use
    finish_dialogue=runtime2.SecondChapterRuntimeTests.finish_dialogue

    def test_walk_to_controls_and_complete_test_with_real_input_and_reload(self):
        with tempfile.TemporaryDirectory() as folder:
            self.app=App(Path(folder)/'save.json');app=self.app
            app.new(action=False);self.finish_dialogue()
            self.use('cabin_door');self.use('controls')
            self.assertEqual(app.mode,'brake');app.draw()
            for key in (pg.K_1,pg.K_2):app.event(pg.event.Event(pg.KEYDOWN,key=key))
            for _ in range(110):app.update(.05)
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN))
            self.assertEqual(app.state.brake['stage'],'apply')
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE));app.action('load')
            self.assertEqual(app.state.brake['stage'],'apply')
            self.use('controls');self.assertEqual(app.mode,'brake')
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_3))
            before=dict(app.state.brake)
            app.event(pg.event.Event(pg.WINDOWFOCUSLOST));app.update(1)
            self.assertEqual(app.state.brake,before)
            app.action('resume')
            for _ in range(80):app.update(.05)
            app.draw();app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN))
            self.assertEqual(app.state.brake['stage'],'release')
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_4))
            for _ in range(60):app.update(.05)
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN))
            self.assertEqual(app.mode,'play')
            self.assertEqual(Session.load(app.save_path).brake['stage'],'done')
            self.finish_dialogue()
            self.assertEqual(app.mode,'drive');self.assertTrue(app.travel_active)
            before=dict(app.state.brake);app.action('brake_apply')
            self.assertEqual(app.state.brake,before)
            pg.quit()
