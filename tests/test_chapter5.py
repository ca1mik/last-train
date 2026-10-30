import unittest
from lasttrain.model import Session
from lasttrain.content import SCENES,walkable
from lasttrain.chapters import chapter5
from test_chapter4 import start_fourth,use,hear_account
from test_story import finish

def finish_fourth(policy=0,audience=0,statement=0,letter_decision=None,account=False):
    s=start_fourth(policy,letter_decision)
    for key in ('dispatch','handle','valentina'):use(s,key)
    if account:hear_account(s)
    for key in ('exit','gallery','archive','chart','orders','inspection','exit','gauge','exit','dispatch','main','service','exit','gallery','confirm','exit','dispatch','recorder'):
        use(s,key)
    use(s,'recorder',audience);use(s,'statement',statement)
    for key in ('handover','exit','train','map'):use(s,key)
    return s

def start_fifth(policy=0,audience=0,statement=0,letter_decision=None,account=False):
    s=finish_fourth(policy,audience,statement,letter_decision,account)
    s.interact('map');finish(s,0)
    assert s.chapter==5
    s.start_dialogue('c5_arrival');finish(s)
    return s

FINAL_ROUTE=('brake','nina','pavel','train','lida','cabin','coupler','gate','semaphore','plate','lever','crossing','walkway','lida','pavel','documents')

class FifthChapterTests(unittest.TestCase):
    def test_art_layouts_and_previous_save_migration(self):
        for key in ('last_platform','upper_platform'):
            scene=SCENES[key]
            self.assertTrue(walkable(scene,scene.start))
            for obj in scene.objects:self.assertTrue(walkable(scene,obj.pos),(key,obj.id))
        s=start_fifth();data=s.snapshot();data['schema']=5;data['pos']=[220,200]
        loaded=Session.restore(data)
        self.assertEqual(loaded.pos,list(SCENES['last_platform'].start))
        self.assertEqual(loaded.flags,s.flags)

    def test_final_routes_and_results_survive_each_checkpoint(self):
        for policy,audience,statement,ending in ((0,0,0,'testimony'),(0,0,1,'unfinished'),(1,1,0,'unfinished'),(1,0,0,'testimony')):
            with self.subTest(policy=policy,audience=audience,statement=statement):
                s=start_fifth(policy,audience,statement)
                for key in FINAL_ROUTE:
                    use(s,key)
                    if s.puzzle=='gate':
                        for action in ('support','pin','swing','confirm'):chapter5.operate_gate(s,action)
                        finish(s)
                    if 'c5_crossing_start' in s.flags and 'c5_crossed' not in s.flags:
                        s.start_dialogue('c5_crossed');finish(s)
                self.assertEqual(s.choices['ending'],ending)
                self.assertIn('c5_complete',s.flags)
                self.assertEqual(s.scene,'upper_platform')
                self.assertEqual(s.health,100)
                before=dict(s.choices);s.interact('raisa')
                self.assertEqual(s.dialogue,'c5_raisa_upper');finish(s)
                self.assertEqual(s.choices,before)
                Session.restore(s.snapshot())

    def test_safe_return_is_distinct_and_retains_evidence(self):
        s=finish_fourth(1,1,1)
        s.interact('map');finish(s,1)
        self.assertEqual(s.choices['ending'],'return')
        self.assertIn('c3_original',s.flags)
        self.assertNotIn('c5_arrived',s.flags)
        Session.restore(s.snapshot())

    def test_cannot_cross_or_open_signal_before_team_is_ready(self):
        s=start_fifth()
        for key in ('coupler','gate','semaphore','lever','crossing'):use(s,key)
        self.assertNotIn('c5_gate',s.flags)
        self.assertNotIn('c5_semaphore',s.flags)
        self.assertEqual(s.scene,'signal_post')
        data=s.snapshot();data['flags'].append('c5_crossed')
        with self.assertRaises(ValueError):Session.restore(data)

    def test_gate_order_and_partial_checkpoint(self):
        s=start_fifth()
        for key in ('brake','pavel','coupler','gate'):use(s,key)
        self.assertEqual(s.puzzle,'gate')
        for action in ('pin','swing','confirm'):self.assertFalse(chapter5.operate_gate(s,action))
        self.assertNotIn('c5_pin_out',s.flags)
        chapter5.operate_gate(s,'support');chapter5.operate_gate(s,'pin')
        restored=Session.restore(s.snapshot());restored.interact('gate')
        self.assertIn('c5_pin_out',restored.flags)
        chapter5.operate_gate(restored,'swing')
        self.assertTrue(chapter5.operate_gate(restored,'confirm'));finish(restored)
        self.assertIn('c5_gate',restored.flags)
