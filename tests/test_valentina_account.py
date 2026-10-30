import copy
import itertools
import unittest
from lasttrain.model import Session
from lasttrain.content import DIALOGUES
from lasttrain.chapters import chapter5
from lasttrain.chapters.chapter4_expansion import ACCOUNT_FLAGS
from test_chapter4 import start_fourth,use,hear_account
from test_chapter5 import start_fifth,finish_fourth,FINAL_ROUTE
from test_story import finish


class ValentinaAccountTests(unittest.TestCase):
    def test_all_question_orders_preserve_facts_without_replacing_route_or_tape(self):
        for order in itertools.permutations(range(3)):
            s=start_fourth(1)
            for key in ('dispatch','handle','valentina'):use(s,key)
            before=dict(s.choices)
            for index in order:
                s.interact('valentina');self.assertEqual(s.dialogue,'c4_questions')
                finish(s,index);s=Session.restore(s.snapshot())
                self.assertNotIn('c4_addendum',s.flags)
            use(s,'valentina');self.assertIn('c4_addendum',s.flags)
            self.assertEqual(s.choices,before)
            self.assertNotIn('c4_tape_heard',s.flags)
            self.assertNotIn('c4_contact_verified',s.flags)
            self.assertNotIn('c4_handover',s.flags)
            s.interact('valentina');self.assertEqual(s.dialogue,'c4_account_done')

    def test_repeated_topic_does_not_count_as_three_accounts(self):
        s=start_fourth()
        for key in ('dispatch','handle','valentina'):use(s,key)
        for _ in range(3):use(s,'valentina',0)
        self.assertEqual(set(ACCOUNT_FLAGS)&s.flags,{'c4_account_known'})
        s.interact('valentina');self.assertEqual(s.dialogue,'c4_questions')

    def test_forged_addendum_and_account_before_meeting_are_rejected(self):
        s=start_fourth();s.interact('dispatch');data=s.snapshot()
        for extras in (['c4_addendum'],['c4_account_known'],list(ACCOUNT_FLAGS)+['c4_addendum']):
            bad=copy.deepcopy(data);bad['flags']+=extras
            with self.assertRaises(ValueError):Session.restore(bad)
        for key in ('handle','valentina'):use(s,key)
        hear_account(s);valid=s.snapshot();original=copy.deepcopy(valid)
        for missing in ACCOUNT_FLAGS:
            bad=copy.deepcopy(valid);bad['flags'].remove(missing)
            with self.assertRaises(ValueError):Session.restore(bad)
        self.assertEqual(valid,original)

    def test_addendum_coexists_with_pavel_letter_and_does_not_choose_ending(self):
        for letter in (None,1):
            for policy,audience,statement,expected in ((1,0,0,'testimony'),(1,1,0,'unfinished'),(0,0,1,'unfinished')):
                s=start_fifth(policy,audience,statement,letter,account=True)
                selected=None
                for key in FINAL_ROUTE:
                    s.interact(key)
                    if key=='documents':
                        selected=s.dialogue
                        self.assertTrue(selected.endswith('_addendum'))
                        self.assertEqual('_pavel_' in selected,letter is not None)
                        text=' '.join(line[1] for line in DIALOGUES[selected]['lines'])
                        self.assertIn('примечание Валентины',text)
                    finish(s)
                    if s.puzzle=='gate':
                        for action in ('support','pin','swing','confirm'):chapter5.operate_gate(s,action)
                        finish(s)
                    if 'c5_crossing_start' in s.flags and 'c5_crossed' not in s.flags:
                        s.start_dialogue('c5_crossed');finish(s)
                    s=Session.restore(s.snapshot())
                self.assertIsNotNone(selected)
                self.assertEqual(s.choices['ending'],expected)
                self.assertIn('примечание Валентины',chapter5.result(s))

    def test_safe_return_keeps_signed_addendum(self):
        s=finish_fourth(1,1,1,account=True)
        s.interact('map');finish(s,1)
        restored=Session.restore(s.snapshot())
        self.assertEqual(restored.choices['ending'],'return')
        self.assertIn('c4_addendum',restored.flags)
        self.assertIn('примечание Валентины',chapter5.result(restored))
