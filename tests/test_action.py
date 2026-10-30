import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App,Enemy,V,blocked
from lasttrain.model import Session
from lasttrain import combat


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.app=App(Path(self.temp.name)/'save.json')
        self.app.new()

    def tearDown(self):pg.quit();self.temp.cleanup()

    def tick(self,seconds,keys=None):
        for _ in range(round(seconds/.01)):self.app.update(.01,keys or defaultdict(int))

    def test_new_campaign_moves_during_intro_and_pause_stops_it(self):
        app=self.app
        self.assertEqual(app.state.scene,'waiting')
        self.assertEqual(Session.load(app.save_path).scene,'waiting')
        before=V(app.state.pos);keys=defaultdict(int,{pg.K_d:1})
        self.tick(.5,keys)
        self.assertGreater(V(app.state.pos).distance_to(before),100)
        self.assertIsNotNone(app.state.dialogue)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_q))
        self.assertEqual(app.state.flares,2)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE))
        before=(list(app.state.pos),app.dialogue_timer,app.state.elapsed)
        self.tick(.5,keys)
        self.assertEqual((app.state.pos,app.dialogue_timer,app.state.elapsed),before)

    def test_real_attack_input_staggers_then_defeat_survives_reload(self):
        app=self.app;app.state.dialogue=None;app.state.pos=[580,720];app.facing=V(1,0)
        enemy=Enemy((650,720));enemy.flag='combat_down_waiting_0';app.enemies=[enemy]
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_f));self.tick(.14)
        self.assertEqual(enemy.health,45);self.assertGreater(enemy.stun,0)
        self.tick(.31)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_f));self.tick(.14)
        self.assertFalse(app.enemies)
        self.assertIn(enemy.flag,app.state.flags)
        app.save();app.action('load')
        self.assertNotIn(enemy.flag,[e.flag for e in app.enemies])
        self.assertEqual(len(app.enemies),1)

    def test_dash_has_recovery_cannot_cross_wall_or_carry_patient(self):
        app=self.app;app.state.dialogue=None;app.state.enter('cabin',(400,700));app.scene_changed();app.facing=V(-1,0)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_SPACE));self.tick(.2)
        self.assertFalse(blocked('cabin',app.state.pos))
        self.assertGreater(app.dash_cooldown,0)
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_SPACE));self.assertEqual(app.dash_time,0)
        app.dash_cooldown=0;app.state.carrying=True;app.dash();self.assertEqual(app.dash_time,0)

    def test_strikes_respect_facing_range_and_concrete_cover(self):
        self.assertTrue(combat.strike_hits('yard',(400,700),(1,0),(490,700)))
        self.assertFalse(combat.strike_hits('yard',(400,700),(1,0),(310,700)))
        self.assertFalse(combat.strike_hits('yard',(400,700),(1,0),(600,700)))
        self.assertFalse(combat.strike_hits('yard',(750,640),(1,0),(850,640)))

    def test_native_output_and_recorded_audio_are_present(self):
        app=self.app;app.renderer.render_at(app,(1920,1080))
        self.assertTrue(app.renderer.hd_fonts)
        self.assertTrue(app.renderer.native_backgrounds)
        self.assertTrue(app.audio.enabled)
        self.assertNotIn('rain',app.audio.sounds)
        self.assertEqual(len(app.audio.steps['concrete']),5)
        app.audio.update('waiting');self.assertEqual(app.audio.motor.get_volume(),0)
        app.audio.update('cabin');self.assertGreater(app.audio.motor.get_volume(),0)
