import copy
import itertools
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pygame as pg
from lasttrain.app import App
from lasttrain.content import SCENES
from lasttrain.model import Session
from lasttrain.mechanics import PowerBoard
from lasttrain.chapters import chapter2
from lasttrain.chapters.chapter2_evacuation import PREPARATION
from test_chapter2 import start_second
from test_chapter3 import finish_second
from test_story import finish


def use(s,key):
    s.interact(key);finish(s)
    return Session.restore(s.snapshot())


def initial():
    s=start_second()
    for key in ('nina','refuge','lida','exit'):s=use(s,key)
    return s


def receiving(s):
    for key in ('train','nina','cabin'):s=use(s,key)
    return s


def packing(s):
    for key in ('refuge','supplies','exit'):s=use(s,key)
    return s


def gate(s,route):
    for key in ('yard','shed','cable' if route=='electric' else 'winch','exit','exit'):s=use(s,key)
    if route=='electric':
        s=use(s,'power');s.power=list(PowerBoard.solution)
        self_checked=chapter2.test_power(s)
        assert self_checked
        s=use(s,'exit');s=use(s,'switch')
    else:
        s.interact('switch')
        for action in ('crank','pawl','crank','crank','crank','crank','pawl'):chapter2.operate_winch(s,action)
        finish(s);s=Session.restore(s.snapshot())
    return s


class HospitalReceivingTests(unittest.TestCase):
    def test_all_preparation_orders_work_with_both_power_routes(self):
        for route in ('electric','manual'):
            for order in itertools.permutations(('receive','pack','gate')):
                s=initial()
                for step in order:
                    s=receiving(s) if step=='receive' else packing(s) if step=='pack' else gate(s,route)
                    self.assertNotIn('c2_boarded',s.flags)
                    self.assertNotIn('hospital_truth',s.choices)
                self.assertTrue(PREPARATION<=s.flags)
                s=use(s,'refuge');s=use(s,'lida')
                self.assertIn('c2_boarded',s.flags)
                self.assertEqual(s.scene,'carriage')
                self.assertEqual(s.choices['power_route'],route)

    def test_lida_requires_the_two_preparations_and_route(self):
        s=gate(initial(),'manual');s=use(s,'refuge')
        s.interact('lida');self.assertEqual(s.dialogue,'c2_need_receiving');finish(s)
        s=use(s,'exit');s=receiving(s);s=use(s,'refuge')
        s.interact('lida');self.assertEqual(s.dialogue,'c2_need_pack');finish(s)
        self.assertNotIn('c2_boarded',s.flags)
        no_route=packing(receiving(initial()));no_route=use(no_route,'refuge')
        no_route=use(no_route,'lida');self.assertNotIn('c2_boarded',no_route.flags)

    def test_legacy_boarding_migrates_but_current_forgery_is_rejected(self):
        s=finish_second();data=s.snapshot();data['schema']=12
        data['flags']=[flag for flag in data['flags'] if flag not in PREPARATION]
        original=copy.deepcopy(data);loaded=Session.restore(data)
        self.assertEqual(loaded.flags,s.flags);self.assertEqual(loaded.choices,s.choices)
        self.assertEqual(data,original)
        current=s.snapshot()
        for missing in PREPARATION:
            bad=copy.deepcopy(current);bad['flags'].remove(missing)
            with self.assertRaises(ValueError):Session.restore(bad)
        before=initial().snapshot();before['schema']=12
        self.assertFalse(PREPARATION&Session.restore(before).flags)

    def test_lida_is_not_present_in_two_rooms_before_boarding(self):
        with tempfile.TemporaryDirectory() as temp:
            app=App(Path(temp)/'save.json')
            try:
                s=initial();s=use(s,'train');app.state=s;app.mode='play';app.scene_changed()
                lida=next(o for o in SCENES['carriage'].objects if o.id=='lida')
                app.state.pos=list(lida.pos)
                self.assertTrue(app.nearby() is None or app.nearby().id!='lida')
                with patch.object(app.renderer,'actor',wraps=app.renderer.actor) as draw:
                    app.draw();self.assertFalse(any(len(c.args)>1 and c.args[1]=='lida' for c in draw.call_args_list))
                app.state=finish_second();app.state.pos=list(lida.pos);app.scene_changed()
                self.assertEqual(app.nearby().id,'lida')
            finally:pg.quit()
