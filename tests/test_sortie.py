import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.app import App,Enemy,V
from lasttrain.model import Session
from lasttrain import fieldwork
from tools.action_driver import Driver


class SortieTests(unittest.TestCase):
    def test_short_replies_keep_the_three_existing_personal_choices(self):
        from lasttrain.combat import cold_open
        from lasttrain.content import DIALOGUES
        for choice,expected in enumerate(('admit','order','hand')):
            s=cold_open();s.dialogue=None;s.flags.update(('door_open','carry','rescued'));s.enter('platform')
            s.interact('lida')
            while s.line<len(DIALOGUES[s.dialogue]['lines']):s.advance()
            s.choose(choice)
            while s.dialogue:s.advance()
            self.assertEqual(s.choices['lida'],expected);self.assertEqual(s.scene,'carriage')
            self.assertEqual(Session.restore(s.snapshot()).choices,s.choices)

    def test_physical_sortie_works_with_helper_or_found_stopper(self):
        for tool in (False,True):
            with self.subTest(tool=tool),tempfile.TemporaryDirectory() as folder:
                app=App(Path(folder)/'save.json');app.new()
                state=Driver(app).sortie(tool=tool,choice=0 if tool else 2)
                self.assertEqual(state.scene,'carriage');self.assertIn('rescued',state.flags)
                self.assertIn('lida_boarded',state.flags);self.assertFalse(state.carrying)
                self.assertEqual(state.health,100)
                self.assertIn('relay_fixed' if tool else 'relay_nina',state.flags)
                self.assertTrue({'combat_down_waiting_0','combat_down_waiting_1'}<=state.flags)
                self.assertEqual(Session.load(app.save_path).snapshot(),state.snapshot())
                pg.quit()

    def test_release_pause_and_damage_interrupt_field_operation(self):
        with tempfile.TemporaryDirectory() as folder:
            app=App(Path(folder)/'save.json');app.new();app.state.dialogue=None
            app.state.pos=[1280,360];app.enemies=[]
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_e));self.assertIsNotNone(app.field_task)
            driver=Driver(app);held=defaultdict(int,{pg.K_e:1});driver.tick(.4,held)
            self.assertNotIn('door_open',app.state.flags)
            progress=app.field_task.progress;app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE));driver.tick(.4,held)
            self.assertEqual(app.field_task.progress,progress)
            app.action('resume');driver.tick(.1)
            self.assertIsNone(app.field_task);self.assertNotIn('door_open',app.state.flags)
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_e));enemy=Enemy((1270,400))
            enemy.attack_state='windup';enemy.attack_timer=.03;enemy.strike=V(app.state.pos)
            app.enemies=[enemy];app.hurt=0;driver.tick(.1,held)
            self.assertIsNone(app.field_task);self.assertEqual(app.state.health,76)
            pg.quit()

    def test_cable_warning_damage_pause_and_escort_detour(self):
        self.assertEqual(fieldwork.cable_phase(.5),'warning')
        self.assertEqual(fieldwork.cable_phase(1.3),'live')
        self.assertEqual(fieldwork.cable_phase(3),'safe')
        with tempfile.TemporaryDirectory() as folder:
            app=App(Path(folder)/'save.json');app.new();app.state.dialogue=None;app.enemies=[]
            app.state.flags.update(('door_open','carry','action_return_live'));app.state.pos=[750,730]
            app.state.elapsed=.4;app.hurt=0
            driver=Driver(app);driver.tick(.2);self.assertEqual(app.state.health,100)
            driver.tick(.6);self.assertEqual(app.state.health,82)
            app.state.health=100;app.state.elapsed=1.2;app.hurt=0
            app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE));driver.tick(.3)
            self.assertEqual(app.state.health,100)
            app.action('resume');app.state.pos=[750,830];driver.tick(.3)
            self.assertEqual(app.state.health,100)
            app.state.carrying=True;app.state.pos=[900,730];app.seed_carry_trail()
            center,rear,_=app.carry_positions()
            self.assertTrue(fieldwork.cable_touches((center,rear)))
            pg.quit()
