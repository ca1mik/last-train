import unittest
from lasttrain.model import Session
from lasttrain.content import SCENES,walkable
from test_chapter3 import start_third,finish_third
from test_story import finish

def start_fourth(policy=0,letter_decision=None):
    s=finish_third(start_third(),policy,letter_decision=letter_decision)
    s.interact('map');finish(s)
    assert s.chapter==4
    s.start_dialogue('c4_arrival');finish(s)
    return s

def use(s,key,choice=0):
    s.interact(key);finish(s,choice)
    Session.restore(s.snapshot())


def hear_account(s,order=(0,1,2)):
    for index in order:use(s,'valentina',index)
    use(s,'valentina')
    return s

class FourthChapterTests(unittest.TestCase):
    def test_routes_recording_and_statement_matrix(self):
        for policy in (0,1):
            for audience in (0,1):
                for statement in (0,1):
                    with self.subTest(policy=policy,audience=audience,statement=statement):
                        s=start_fourth(policy)
                        for key in ('dispatch','handle','valentina','exit','gallery','archive','chart','orders','inspection','application','exit','gauge','exit','dispatch','main','service','exit','gallery','confirm','exit','dispatch','recorder'):
                            use(s,key)
                        self.assertIn('c4_contact_verified',s.flags)
                        # The branch was executed, not merely selected by a test flag.
                        self.assertIn('c4_tape_heard',s.flags)
                        use(s,'recorder',audience);use(s,'statement',statement);use(s,'handover')
                        use(s,'main')
                        self.assertIn('c4_contact_verified',s.flags)
                        for key in ('exit','train','map'):use(s,key)
                        self.assertIn('c4_complete',s.flags)
                        self.assertEqual(s.choices['tape_audience'],'all' if policy==0 else ('all','archive')[audience])
                        self.assertEqual(s.choices['statement'],('signed','deferred')[statement])

    def test_incomplete_route_does_not_confirm(self):
        s=start_fourth()
        for key in ('gallery','confirm','gauge'):use(s,key)
        self.assertNotIn('c4_contact_verified',s.flags)
        self.assertNotIn('c4_level_checked',s.flags)
        for key in ('exit','dispatch','main','handover'):use(s,key)
        self.assertNotIn('c4_handover',s.flags)
        data=s.snapshot();data['flags'].append('c4_contact_verified')
        with self.assertRaises(ValueError):Session.restore(data)

    def test_all_room_starts_and_objects_are_walkable(self):
        for key in ('spillway','gallery','archive','dispatch'):
            scene=SCENES[key]
            self.assertTrue(walkable(scene,scene.start),key)
            for obj in scene.objects:self.assertTrue(walkable(scene,obj.pos),(key,obj.id))

    def test_previous_dispatch_layout_migrates_without_losing_progress(self):
        s=start_fourth();use(s,'dispatch');use(s,'handle');use(s,'valentina')
        old=s.snapshot();old['schema']=4;old['pos']=[250,200]
        migrated=Session.restore(old)
        self.assertEqual(migrated.pos,list(SCENES['dispatch'].start))
        self.assertIn('c4_met',migrated.flags)
        self.assertEqual(migrated.choices,s.choices)
        current=s.snapshot();current['pos']=[250,200]
        with self.assertRaises(ValueError):Session.restore(current)
