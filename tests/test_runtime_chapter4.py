import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App
from test_chapter4 import start_fourth
import test_runtime_chapter2 as runtime2

class FourthChapterRuntimeTests(unittest.TestCase):
    use=runtime2.SecondChapterRuntimeTests.use
    finish_dialogue=runtime2.SecondChapterRuntimeTests.finish_dialogue

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.app=App(Path(self.temp.name)/'save.json')

    def tearDown(self):pg.quit();self.temp.cleanup()

    def test_physical_inspection_and_handover(self):
        app=self.app;app.state=start_fourth(0);app.mode='play';app.loaded_scene=None;app.scene_changed()
        for key in ('dispatch','handle','valentina','exit','gallery','archive','chart','orders','inspection','exit','gauge','exit','dispatch','main','service','exit','gallery','confirm','exit','dispatch','recorder','recorder','statement','handover','exit','train','map'):
            self.use(key)
        self.assertEqual(app.mode,'chapter_end')
        self.assertIn('c4_complete',app.state.flags)
        app.action('load')
        self.assertEqual(app.state.chapter,4)
        self.assertIn('c4_complete',app.state.flags)

    def test_optional_account_uses_real_dispatch_interaction_and_checkpoint(self):
        app=self.app;app.state=start_fourth(1);app.mode='play';app.loaded_scene=None;app.scene_changed()
        for key in ('dispatch','handle','valentina'):self.use(key)
        self.use('valentina');self.assertIn('c4_account_known',app.state.flags)
        for index in (2,1):
            app.interact();self.assertEqual(app.state.dialogue,'c4_questions')
            self.finish_dialogue(index)
        app.action('load');self.assertNotIn('c4_addendum',app.state.flags)
        self.use('valentina');self.assertIn('c4_addendum',app.state.flags)
        app.action('load');self.assertIn('c4_addendum',app.state.flags)
