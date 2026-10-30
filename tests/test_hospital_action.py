import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App,V
from lasttrain.model import Session
from lasttrain.content import SCENES
from lasttrain import combat,hospital_action
from tools.action_driver import Driver
from test_chapter2 import start_second


class HospitalActionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.app=App(Path(self.temp.name)/'save.json')
        self.app.state=start_second();self.app.state.flags.add('action_mode');self.app.mode='play'
        self.app.loaded_scene=None;self.app.scene_changed();self.driver=Driver(self.app)

    def tearDown(self):pg.quit();self.temp.cleanup()

    def press(self,key):self.app.event(pg.event.Event(pg.KEYDOWN,key=key))

    def manual_fixture(self):
        app=self.app;app.state.flags.update(('c2_intro','c2_refuge','c2_winch'))
        app.state.pos=[810,360];app.state.dialogue=None;app.hurt=0;app.save()
        self.press(pg.K_e);self.driver.tick(1.05,defaultdict(int,{pg.K_e:1}))
        self.assertEqual(app.field_task.kind,'c2_rhythm');self.assertEqual(app.mode,'play')

    def test_both_complete_sorties_through_controls_and_saved_personal_answers(self):
        for route,answer in (('manual',0),('electric',1)):
            with self.subTest(route=route):
                if route=='electric':
                    self.app.state=start_second();self.app.state.flags.add('action_mode')
                    self.app.mode='play';self.app.loaded_scene=None;self.app.scene_changed();self.driver=Driver(self.app)
                s=self.driver.hospital_sortie(route,answer)
                self.assertEqual(s.scene,'carriage');self.assertEqual(s.health,100)
                self.assertTrue({'c2_complete','c2_boarded','c2_receiving_ready','c2_pack_ready','c2_gate_open'}<=s.flags)
                self.assertEqual(s.choices['power_route'],route)
                self.assertEqual(s.choices['hospital_truth'],('admit','defend')[answer])
                self.assertEqual(Session.load(self.app.save_path).snapshot(),s.snapshot())

    def test_winch_miss_has_no_turn_and_success_survives_reload_before_finishing(self):
        self.manual_fixture();app=self.app
        self.press(pg.K_e);self.assertEqual(app.state.winch['turns'],0)
        self.driver.tick(.55);self.press(pg.K_e)
        self.assertEqual(app.state.winch['turns'],1)
        loaded=Session.load(app.save_path);self.assertEqual(loaded.winch,{'stage':'turn','turns':1})
        self.assertNotIn('c2_gate_open',loaded.flags)
        app.action('load');self.assertIsNone(app.field_task)
        self.driver.use('switch');self.assertEqual(app.state.winch,{'stage':'lock','turns':4})
        self.assertIn('c2_gate_open',app.state.flags)
        self.assertEqual(Session.load(app.save_path).choices['power_route'],'manual')

    def test_winch_pause_freezes_beat_and_movement_or_damage_stops_work(self):
        self.manual_fixture();app=self.app;self.driver.tick(.3)
        phase=app.field_task.progress;self.press(pg.K_ESCAPE);self.driver.tick(.6)
        self.assertEqual(app.field_task.progress,phase)
        app.action('resume');self.driver.tick(.05,defaultdict(int,{pg.K_s:1}))
        self.assertIsNone(app.field_task);self.assertEqual(app.state.winch['turns'],0)
        self.press(pg.K_e);self.assertEqual(app.field_task.kind,'c2_rhythm')
        app.hurt_player(24,'test');self.assertIsNone(app.field_task)
        self.assertEqual(Session.load(app.save_path).winch['turns'],0)

    def test_receiving_is_atomic_and_saved_before_its_mobile_confirmation(self):
        app=self.app;app.state.flags.add('c2_refuge');app.state.enter('carriage',(520,580));app.loaded_scene=None;app.scene_changed()
        self.press(pg.K_e);self.driver.tick(.5,defaultdict(int,{pg.K_e:1}))
        self.assertNotIn('c2_receiving_ready',Session.load(app.save_path).flags)
        self.driver.tick();self.assertIsNone(app.field_task)
        self.press(pg.K_e);self.driver.tick(1.15,defaultdict(int,{pg.K_e:1}))
        self.assertEqual(app.state.dialogue,'c2_a_receiving');self.assertTrue(combat.moving_dialogue(app.state))
        self.assertIn('c2_receiving_ready',Session.load(app.save_path).flags)

    def test_working_refuge_reply_keeps_movement_and_its_original_effect(self):
        app=self.app;app.state.enter('refuge',(650,700));app.loaded_scene=None;app.scene_changed()
        app.state.start_dialogue('c2_refuge');before=V(app.state.pos)
        self.driver.tick(.1,defaultdict(int,{pg.K_d:1}))
        self.assertGreater(V(app.state.pos).distance_to(before),10)
        while app.state.dialogue:self.press(pg.K_RETURN)
        self.assertIn('c2_refuge',app.state.flags)
        app.state.start_dialogue('c2_truth');self.assertFalse(combat.moving_dialogue(app.state))
