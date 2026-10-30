import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App
from lasttrain.inspection import POINTS,VIEW
from test_exit_inspection import stopped
import test_runtime_chapter2 as runtime2

class ExitRuntimeTests(unittest.TestCase):
    use=runtime2.SecondChapterRuntimeTests.use
    finish_dialogue=runtime2.SecondChapterRuntimeTests.finish_dialogue

    def test_physical_observation_mouse_keyboard_and_short_drive(self):
        with tempfile.TemporaryDirectory() as folder:
            self.app=App(Path(folder)/'save.json');app=self.app;app.state=stopped()
            app.mode='play';app.loaded_scene=None;app.scene_changed()
            self.use('controls');self.use('cabin_door')
            self.assertEqual(app.mode,'inspection');app.draw()
            x,y=POINTS[0][2];view=pg.Rect(VIEW)
            # The test display is 1280x720, so panel coordinates are display coordinates.
            point=(round(view.x+x*view.w/1536),round(view.y+y*view.h/1024))
            app.event(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=point))
            self.assertIn('c1_inspected_step',app.state.flags)
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE));app.action('load')
            self.use('cabin_door')
            for key in (pg.K_2,pg.K_3):app.event(pg.event.Event(pg.KEYDOWN,key=key))
            app.draw();app.action('inspect_rails');self.assertEqual(app.mode,'inspection')
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN));self.finish_dialogue()
            self.assertEqual(app.mode,'drive');self.assertEqual(app.drive_max_speed,12)
            self.assertNotIn('arrive',app.state.flags)
            for _ in range(200):app.update(.05,defaultdict(int,{pg.K_w:1}))
            self.assertLessEqual(app.speed,12)
            self.assertGreater(app.drive_distance,app.drive_min_stop)
            for _ in range(30):app.update(.05,defaultdict(int,{pg.K_s:1}))
            self.finish_dialogue()
            self.assertEqual(app.state.scene,'platform');self.assertIn('arrive',app.state.flags)
            pg.quit()
