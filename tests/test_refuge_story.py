import unittest
from lasttrain.model import Session
from lasttrain.content import DIALOGUES
from test_chapter2 import start_second
from test_story import finish
from test_chapter3 import finish_second
from test_chapter5 import finish_fourth
from lasttrain.content import SCENES,walkable

class RefugeStoryTests(unittest.TestCase):
    def test_raisa_card_branch_and_later_train_conversations(self):
        for card in (False,True):
            s=finish_second(card=card);choices=dict(s.choices)
            s.interact('raisa')
            self.assertEqual(s.dialogue,'c2_raisa_card' if card else 'c2_raisa_no_card')
            finish(s);self.assertEqual(s.choices,choices)
            s.start_dialogue('c3_departure');finish(s)
            s.interact('raisa');self.assertEqual(s.dialogue,'c3_raisa_train');finish(s)
            Session.restore(s.snapshot())
        s=finish_fourth();s.interact('raisa');self.assertEqual(s.dialogue,'c4_raisa_train');finish(s)
        s.interact('map');finish(s)
        s.interact('raisa');self.assertEqual(s.dialogue,'c5_raisa_train');finish(s)

    def test_previous_refuge_coordinates_migrate_to_new_floor(self):
        s=start_second();s.enter('refuge');data=s.snapshot();data['schema']=8;data['pos']=[220,740]
        restored=Session.restore(data)
        self.assertTrue(walkable(SCENES['refuge'],restored.pos))
        self.assertEqual(restored.pos,list(SCENES['refuge'].start))
        self.assertEqual(restored.flags,s.flags)
        current=s.snapshot();current['pos']=[220,740]
        with self.assertRaises(ValueError):Session.restore(current)

    def test_address_card_changes_boarding_without_blocking_other_routes(self):
        for offer in (0,1,2):
            with self.subTest(offer=offer):
                s=start_second();s.interact('refuge');s.interact('lida');finish(s);s.interact('beds')
                for _ in range(len(DIALOGUES[s.dialogue]['lines'])):s.advance()
                s.choose(offer);finish(s,0)
                # Asking about the coat leads to the offer to write the address.
                if offer<2:
                    self.assertIn('c2_address',s.flags)
                    s.interact('roster');finish(s)
                    self.assertIn('c2_card_written',s.flags)
                    Session.restore(s.snapshot())
                else:self.assertNotIn('c2_card_written',s.flags)
                s.flags.add('c2_gate_open');s.interact('exit')
                from test_chapter2 import prepare_receiving
                prepare_receiving(s);s.interact('lida')
                self.assertEqual(s.dialogue,'c2_boarding_named' if offer<2 else 'c2_boarding')
