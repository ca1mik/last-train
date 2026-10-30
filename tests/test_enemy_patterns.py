import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App,Enemy,V
from lasttrain import combat
from lasttrain.content import SCENES,walkable


class EnemyPatternTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.app=App(Path(self.temp.name)/'save.json');self.app.new()
        self.app.state.dialogue=None;self.app.state.pos=[600,720];self.app.hurt=0

    def tearDown(self):pg.quit();self.temp.cleanup()

    def tick(self,seconds,keys=None):
        for _ in range(round(seconds/.01)):self.app.update(.01,keys or defaultdict(int))

    def test_runner_locks_lane_and_can_be_dodged_sideways(self):
        app=self.app;enemy=Enemy((780,720),'runner');app.enemies=[enemy]
        self.tick(.01);self.assertEqual(enemy.attack_state,'windup');locked=V(enemy.strike)
        self.tick(.3,defaultdict(int,{pg.K_w:1}));self.tick(.6)
        self.assertEqual(app.state.health,100);self.assertEqual(enemy.strike,locked)
        self.assertEqual(enemy.attack_state,'recover');self.assertAlmostEqual(enemy.pos.y,720)
        self.assertAlmostEqual(enemy.pos.x,585,delta=2)

    def test_runner_charge_hits_only_once_and_stops_at_wall(self):
        app=self.app;enemy=Enemy((780,720),'runner');app.enemies=[enemy]
        self.tick(.9);self.assertEqual(app.state.health,76);self.assertTrue(enemy.charge_hit)
        app.state.pos=[760,500];app.state.health=100;app.hurt=0
        enemy=Enemy((1080,500),'runner');app.enemies=[enemy];combat.begin_attack(enemy,app.state.pos)
        self.tick(.9)
        self.assertEqual(enemy.attack_state,'recover');self.assertGreater(enemy.pos.x,1000)
        self.assertTrue(walkable(SCENES['waiting'],enemy.pos,17));self.assertEqual(app.state.health,100)

    def test_brute_windup_is_not_cancelled_by_normal_punches(self):
        app=self.app;app.state.pos=[580,720];app.facing=V(1,0)
        enemy=Enemy((650,720),'brute');app.enemies=[enemy]
        self.tick(.01);app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_f));self.tick(.14)
        self.assertEqual(enemy.health,110);self.assertEqual(enemy.attack_state,'windup');self.assertEqual(enemy.stun,0)
        self.tick(.31);app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_f));self.tick(.14)
        self.assertEqual(enemy.health,55);self.tick(.5)
        self.assertEqual(app.state.health,68);self.assertEqual(enemy.attack_state,'recover')
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_f));self.tick(.14)
        self.assertFalse(app.enemies)

    def test_flare_interrupts_charge_and_pause_freezes_telegraph(self):
        app=self.app;enemy=Enemy((780,720),'runner');app.enemies=[enemy]
        self.tick(.1);before=(enemy.attack_timer,V(enemy.pos))
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE));self.tick(.6)
        self.assertEqual((enemy.attack_timer,enemy.pos),before)
        app.action('resume');self.tick(.45);self.assertEqual(enemy.attack_state,'charge')
        app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_q));self.tick(.2)
        self.assertEqual(enemy.attack_state,'idle');self.assertGreater(enemy.stun,3)
        self.assertEqual(app.state.health,100)

    def test_sweep_has_a_safe_back_and_respects_range(self):
        self.assertTrue(combat.sweep_hits((700,700),(1,0),(800,750)))
        self.assertFalse(combat.sweep_hits((700,700),(1,0),(650,700)))
        self.assertFalse(combat.sweep_hits((700,700),(1,0),(900,700)))
