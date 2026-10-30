import copy
import itertools
import unittest
from lasttrain.model import Session
from lasttrain.content import DIALOGUES
from lasttrain.chapters import chapter3,chapter5
from test_story import finish
from test_chapter3 import start_third,repair_line
from lasttrain.mechanics import RadioTune
from test_chapter5 import start_fifth,finish_fourth,FINAL_ROUTE
from test_chapter4 import use

def read_letters(s,order=(0,1,2),decision=0):
    for index in order:s.interact('letters');finish(s,index)
    s.interact('pavel');finish(s,decision)

class PavelLetterTests(unittest.TestCase):
    def test_both_custodians_reach_personal_handoff_without_changing_ending_rules(self):
        for decision in (0,1):
            for audience,statement,ending in ((0,0,'testimony'),(1,1,'unfinished')):
                with self.subTest(decision=decision,ending=ending):
                    s=start_fifth(1,audience,statement,decision)
                    for key in FINAL_ROUTE[:-1]:
                        use(s,key)
                        if s.puzzle=='gate':
                            for action in ('support','pin','swing','confirm'):chapter5.operate_gate(s,action)
                            finish(s)
                        if 'c5_crossing_start' in s.flags and 'c5_crossed' not in s.flags:
                            s.start_dialogue('c5_crossed');finish(s)
                    s.interact('documents')
                    self.assertEqual(s.dialogue,'c5_'+ending+'_pavel');finish(s)
                    self.assertEqual(s.choices['ending'],ending)
                    self.assertIn('лично передал',chapter5.result(s))
                    Session.restore(s.snapshot())

    def test_safe_return_preserves_the_letter_for_later_personal_submission(self):
        for decision in (0,1):
            s=finish_fourth(letter_decision=decision)
            s.interact('map');finish(s,1)
            self.assertEqual(s.choices['ending'],'return')
            self.assertIn('сохранено для личной передачи',chapter5.result(s))
            Session.restore(s.snapshot())

    def test_all_reading_orders_and_both_custody_choices_survive_load(self):
        for order in itertools.permutations(range(3)):
            for decision in (0,1):
                with self.subTest(order=order,decision=decision):
                    s=start_third();s.interact('flat');s.interact('pavel');finish(s)
                    read_letters(s,order,decision)
                    self.assertEqual(s.choices['pavel_statement'],('take','leave')[decision])
                    self.assertIn('c3_letters_discussed',s.flags)
                    self.assertEqual(Session.restore(s.snapshot()).snapshot(),s.snapshot())
                    s.interact('pavel');self.assertEqual(s.dialogue,'c3_pavel_work')

    def test_accusation_changes_cooperation_tone_but_keeps_repair_available(self):
        s=start_third();s.interact('flat');s.interact('pavel');finish(s,1)
        s.interact('pavel');self.assertEqual(s.dialogue,'c3_pavel_work_wary');finish(s)
        self.assertIn('c3_work',s.flags)
        s.interact('letters');finish(s,0)
        s.interact('pavel');self.assertEqual(s.dialogue,'c3_pavel_work_wary')
        self.assertNotIn('pavel_statement',s.choices)

    def test_letter_decision_does_not_replace_live_contact_or_original_tape(self):
        s=start_third();s.interact('flat');s.interact('pavel');finish(s)
        read_letters(s);s.interact('pavel');finish(s)
        self.assertEqual(s.scene,'flat');self.assertNotIn('c3_boarded',s.flags)
        s.interact('exit');repair_line(s)
        s.radio=list(RadioTune.target);chapter3.beacon(s,2);chapter3.listen(s);finish(s)
        for key in ('exit','flat','cassette'):s.interact(key);finish(s)
        s.interact('pavel');self.assertEqual(s.dialogue,'c3_pavel_boarding_statement');finish(s)
        self.assertEqual(s.scene,'carriage')

    def test_forged_statement_and_missing_drafts_are_rejected(self):
        s=start_third();data=s.snapshot();data['choices']['pavel_statement']='take'
        with self.assertRaises(ValueError):Session.restore(data)
        s.interact('flat');s.interact('pavel');finish(s);read_letters(s)
        data=s.snapshot();data['flags'].remove('c3_letter_middle')
        with self.assertRaises(ValueError):Session.restore(data)
