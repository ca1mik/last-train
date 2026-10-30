import unittest
from lasttrain.model import Session
from lasttrain.inspection import operate
from test_brakes import start_check
from test_story import brake_check,finish

def stopped():
    s=start_check();brake_check(s);s.start_dialogue('loop');finish(s)
    return s

class ExitInspectionTests(unittest.TestCase):
    def test_parking_observations_and_safe_reposition_are_required(self):
        s=stopped();self.assertEqual(s.scene,'cabin')
        s.interact('cabin_door');self.assertIsNone(s.puzzle)
        self.assertFalse(operate(s,'platform'))
        s.interact('controls');finish(s);s.interact('cabin_door')
        self.assertEqual(s.puzzle,'inspection')
        self.assertFalse(operate(s,'platform'))
        for clue in ('step','gap','landing'):operate(s,clue)
        checkpoint=Session.restore(s.snapshot());checkpoint.interact('cabin_door')
        self.assertFalse(operate(checkpoint,'rails'));self.assertEqual(checkpoint.scene,'cabin')
        self.assertTrue(operate(checkpoint,'platform'));finish(checkpoint)
        self.assertIn('c1_align',checkpoint.flags)
        self.assertNotIn('arrive',checkpoint.flags)
        checkpoint.start_dialogue('c1_aligned');finish(checkpoint)
        self.assertEqual(checkpoint.scene,'platform')
        Session.restore(checkpoint.snapshot())

    def test_unparked_scan_cannot_be_restored(self):
        data=stopped().snapshot();data['flags'].append('c1_inspected_step')
        with self.assertRaises(ValueError):Session.restore(data)
