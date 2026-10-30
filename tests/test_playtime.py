import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App
from lasttrain.model import Session

class PlaytimeTests(unittest.TestCase):
    def test_old_location_notices_clear_and_expire_during_reading(self):
        with tempfile.TemporaryDirectory() as folder:
            app=App(Path(folder)/'save.json');app.state.say('Старая инструкция');app.scene_changed()
            self.assertEqual(app.state.notice,'');self.assertEqual(app.state.notice_time,0)
            app.mode='play';app.state.start_dialogue('opening');app.state.say('Новая инструкция')
            app.update(.05,active_dt=6)
            self.assertEqual(app.state.notice_time,0)
            pg.quit()
    def test_active_modes_count_reading_and_equipment_but_pause_does_not(self):
        with tempfile.TemporaryDirectory() as folder:
            app=App(Path(folder)/'save.json');app.loaded_scene=app.state.scene
            for mode in ('play','drive','crossing','journal','power','winch','radio','gate','brake','inspection'):
                with self.subTest(mode=mode):
                    app.mode=mode;app.state.start_dialogue('opening');before=app.state.elapsed
                    app.update(.5)
                    self.assertAlmostEqual(app.state.elapsed-before,.5)
            for mode in ('menu','settings','pause','dead','chapter_end','confirm_new'):
                app.mode=mode;before=app.state.elapsed;app.update(.5)
                self.assertEqual(app.state.elapsed,before,mode)
            app.mode='play';before=app.state.elapsed
            app.update(.05,active_dt=.4)
            self.assertAlmostEqual(app.state.elapsed-before,.4)
            app.state.dialogue=None;app.mode='play';app.save()
            self.assertEqual(Session.load(app.save_path).elapsed,app.state.elapsed)
            pg.quit()

    def test_focus_loss_pauses_equipment_time_and_resume_restores_panel(self):
        with tempfile.TemporaryDirectory() as folder:
            app=App(Path(folder)/'save.json');app.mode='radio'
            app.event(pg.event.Event(pg.WINDOWFOCUSLOST))
            before=app.state.elapsed;app.update(1)
            self.assertEqual(app.mode,'pause');self.assertEqual(app.state.elapsed,before)
            app.action('resume');self.assertEqual(app.mode,'radio')
            app.update(1);self.assertEqual(app.state.elapsed,before+1)
            pg.quit()
