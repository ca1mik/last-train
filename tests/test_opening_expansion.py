import unittest
from lasttrain.model import Session
from lasttrain.content import DIALOGUES
from test_story import finish,rescue,brake_check

def choose_first(s,index):
    for _ in range(len(DIALOGUES[s.dialogue]['lines'])):s.advance()
    s.choose(index);finish(s)

class ExpandedOpeningTests(unittest.TestCase):
    def test_work_and_family_conversations_preserve_departure(self):
        for topic in range(3):
            with self.subTest(topic=topic):
                s=Session();s.start_dialogue('opening');finish(s)
                s.interact('cabin_door');finish(s)
                s.interact('tea');choose_first(s,topic)
                self.assertIn(('c1_job','c1_morning','tea')[topic],s.flags)
                Session.restore(s.snapshot())
                s.interact('controls');finish(s)
                brake_check(s)
                self.assertIn('drive',s.flags)

    def test_all_post_rescue_answers_leave_map_available(self):
        for topic in range(3):
            s=rescue();s.interact('nina');choose_first(s,topic)
            self.assertIn('nina_after',s.flags)
            s.interact('map');finish(s)
            self.assertIn('chapter_complete',s.flags)
            Session.restore(s.snapshot())
            self.assertTrue(any('Мастерская' in title for title,_ in s.journal()))
