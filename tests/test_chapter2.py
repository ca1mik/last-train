import copy
import tempfile
from pathlib import Path
import unittest
from lasttrain.model import Session
from lasttrain.mechanics import PowerBoard, Winch
from lasttrain.chapters import chapter2
from test_story import rescue,finish

def start_second():
    s=rescue('tool',0)
    s.interact('nina');finish(s)
    s.interact('map');finish(s)
    s.interact('map');finish(s)
    assert s.chapter==2
    s.start_dialogue('c2_arrival');finish(s)
    return s


def prepare_receiving(s):
    for key in ('train','nina','cabin','refuge','supplies'):
        s.interact(key);finish(s);Session.restore(s.snapshot())
    return s

class PowerTests(unittest.TestCase):
    def test_solution_needs_a_real_bridge(self):
        rotation=list(PowerBoard.solution)
        self.assertTrue(PowerBoard.validate(rotation))
        self.assertTrue(PowerBoard.result(rotation,True)[0])
        self.assertFalse(PowerBoard.result(rotation,False)[0])
        self.assertIn(PowerBoard.hospital,PowerBoard.powered(rotation,False))
        self.assertNotIn(PowerBoard.gate,PowerBoard.powered(rotation,False))

    def test_rotating_a_junction_changes_connectivity(self):
        rotation=list(PowerBoard.solution)
        for _ in range(4):
            before=rotation[7];PowerBoard.rotate(rotation,7)
            self.assertEqual(rotation[7],(before+1)%4)
        self.assertEqual(rotation,list(PowerBoard.solution))
        rotation[7]=0
        self.assertFalse(PowerBoard.result(rotation,True)[0])
        self.assertFalse(PowerBoard.result(list(PowerBoard.initial),True)[0])

    def test_fixed_source_and_sinks_cannot_rotate(self):
        rotation=list(PowerBoard.initial)
        for node in PowerBoard.fixed:PowerBoard.rotate(rotation,node)
        self.assertEqual(rotation,list(PowerBoard.initial))

    def test_winch_cannot_be_forced_out_of_order(self):
        state=Winch.initial()
        self.assertFalse(Winch.act(state,'pawl')[1])
        self.assertEqual(state,Winch.initial())
        Winch.act(state,'crank')
        self.assertEqual(state['stage'],'release')
        Winch.act(state,'crank');self.assertEqual(state['turns'],0)
        Winch.act(state,'pawl')
        for _ in range(4):self.assertFalse(Winch.act(state,'crank')[1])
        self.assertEqual(state,{'stage':'lock','turns':4})
        self.assertTrue(Winch.act(state,'pawl')[1])

class SecondChapterTests(unittest.TestCase):
    def test_both_routes_and_answers_finish_with_refuge_powered(self):
        for route in ('electric','manual'):
            for answer in (0,1):
                with self.subTest(route=route,answer=answer):
                    s=start_second()
                    s.interact('switch');self.assertNotIn('c2_gate_open',s.flags)
                    s.interact('nina');finish(s)
                    s.interact('refuge');s.interact('lida');finish(s);s.interact('exit')
                    s.interact('yard');s.interact('shed')
                    s.interact('cable' if route=='electric' else 'winch');finish(s)
                    s.interact('exit');s.interact('exit')
                    if route=='electric':
                        s.interact('power');s.interact('board')
                        self.assertFalse(chapter2.test_power(s))
                        s.power=list(PowerBoard.solution)
                        self.assertTrue(chapter2.test_power(s))
                        s.interact('board');self.assertIsNone(s.puzzle)
                        s.interact('exit');s.interact('switch');finish(s)
                    else:
                        s.interact('switch')
                        for action in ('crank','pawl','crank','crank','crank','crank','pawl'):
                            chapter2.operate_winch(s,action)
                        finish(s)
                    self.assertIn('c2_gate_open',s.flags)
                    self.assertEqual(s.choices['power_route'],route)
                    prepare_receiving(s);s.interact('lida');finish(s)
                    self.assertEqual(s.scene,'carriage')
                    s.interact('map');self.assertIsNone(s.dialogue)
                    s.interact('nina');finish(s,answer)
                    s.interact('map');finish(s)
                    self.assertIn('c2_complete',s.flags)
                    self.assertEqual(s.choices['hospital_truth'],('admit','defend')[answer])
                    Session.restore(s.snapshot())

    def test_partial_equipment_survives_save_and_migration(self):
        s=start_second();s.power[7]=3;Winch.act(s.winch,'crank')
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'save.json';s.save(path);loaded=Session.load(path)
        self.assertEqual(s.snapshot(),loaded.snapshot())
        old=Session().snapshot()
        for field in ('chapter','power','winch'):del old[field]
        old['schema']=2
        old['pos']=[470,450]
        migrated=Session.restore(old)
        self.assertEqual(migrated.chapter,1)
        self.assertEqual(migrated.power,list(PowerBoard.initial))
        self.assertEqual(migrated.pos,[850,700])

    def test_corrupt_puzzle_state_rejected(self):
        good=start_second().snapshot()
        for field,value in [('power',[0]),('power',[True]*20),('chapter',5),
                            ('winch',{'stage':'turn','turns':-1})]:
            bad=copy.deepcopy(good);bad[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):Session.restore(bad)
        bad=copy.deepcopy(good);bad['flags'].append('c2_power_ready')
        with self.assertRaises(ValueError):Session.restore(bad)

if __name__=='__main__':unittest.main()
