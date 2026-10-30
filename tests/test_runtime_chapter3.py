import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App
from lasttrain.mechanics import RadioTune
from lasttrain.content import SCENES
from test_chapter3 import start_third,finish_second,finish_third
import test_runtime_chapter2 as runtime2

class ThirdChapterRuntimeTests(unittest.TestCase):
    def test_letters_are_read_through_real_apartment_interactions(self):
        app=self.app;app.state=start_third();app.mode='play';app.loaded_scene=None;app.scene_changed()
        for key in ('flat','pavel','letters'):self.use(key)
        for index in (1,2):app.interact();self.finish_dialogue(index)
        self.use('pavel')
        self.assertEqual(app.state.choices['pavel_statement'],'take')
        app.action('load');self.assertIn('c3_letters_discussed',app.state.flags)
    # Reuse the physical walk/input driver, without inheriting its tests.
    use=runtime2.SecondChapterRuntimeTests.use
    finish_dialogue=runtime2.SecondChapterRuntimeTests.finish_dialogue

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.app=App(Path(self.temp.name)/'save.json')

    def tearDown(self):pg.quit();self.temp.cleanup()

    def test_physical_repair_radio_input_recording_and_load(self):
        app=self.app;app.state=start_third(1);app.mode='play';app.loaded_scene=None;app.scene_changed()
        for key in ('flat','pavel','pavel','cassette','exit','relay','spare','maintenance','exit','yard','gantry','fault'):
            self.use(key)
        self.assertNotIn('c3_repair',app.state.flags)
        for key in ('exit','breaker','gantry','fault','exit','breaker','exit','relay','receiver'):self.use(key)
        self.assertEqual(app.mode,'radio');self.assertIn('c3_repair',app.state.flags)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN));self.assertEqual(app.mode,'radio')
        for control,target in enumerate(RadioTune.target):
            self.assertEqual(app.radio_selected,control)
            for _ in range(target):app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_e))
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RIGHT))
        self.assertEqual(app.state.radio,list(RadioTune.target))
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN));self.assertEqual(app.mode,'radio')
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_3));app.draw()
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN));self.assertEqual(app.mode,'play')
        self.assertEqual(app.state.dialogue,'c3_contact_3')
        before=list(app.state.radio)
        app.action(('radio',0))
        app.event(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=(200,465)))
        self.assertEqual(app.state.radio,before)
        self.finish_dialogue()
        for key in ('exit','flat','pavel','pavel','nina','nina','lida','map'):self.use(key)
        self.assertEqual(app.mode,'chapter_end');self.assertIn('c3_complete',app.state.flags)
        self.assertEqual(app.state.choices['recording_policy'],'share')
        app.action('menu');app.action('load')
        self.assertEqual(app.mode,'chapter_end');self.assertEqual(app.state.signal_pattern,3)
        self.assertIn('c3_contact',app.state.flags)

    def test_transition_from_second_chapter_preserves_checkpoint(self):
        app=self.app;app.state=finish_second(1);app.mode='chapter_end';app.save()
        app.action('next_chapter');self.finish_dialogue()
        self.assertEqual(app.mode,'drive');self.assertEqual(app.drive_arrival,'c3_arrival')
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE));app.action('save')
        self.assertEqual(app.state.load(app.save_path).chapter,2)
        app.action('resume');app.drive_distance=600;app.speed=0;app.update(.02,defaultdict(int));self.finish_dialogue()
        self.assertEqual((app.state.chapter,app.state.scene),(3,'settlement'))
        self.assertFalse(app.travel_active)

    def test_journal_pages_and_pavel_visibility(self):
        position=list(next(o.pos for o in SCENES['carriage'].objects if o.id=='pavel'))
        app=self.app;app.state=finish_second();app.mode='play';app.state.pos=position.copy()
        self.assertIsNone(app.nearby())
        app.state=finish_third(start_third());app.state.pos=position.copy()
        self.assertEqual(app.nearby().id,'pavel')
        self.assertGreater(len(app.state.journal()),4)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_j));app.draw()
        self.assertEqual(app.journal_page,0)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RIGHT));app.draw()
        self.assertEqual(app.journal_page,1)
        app.event(pg.event.Event(pg.MOUSEWHEEL,y=1));self.assertEqual(app.journal_page,0)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_j));self.assertEqual(app.mode,'play')

if __name__=='__main__':unittest.main()
