import copy
import unittest
from lasttrain.brakes import BrakeTest,operate
from lasttrain.model import Session
from test_story import finish,brake_check

def start_check():
    s=Session();s.start_dialogue('opening');finish(s)
    s.interact('cabin_door');finish(s);s.interact('controls');finish(s)
    return s

class BrakeTests(unittest.TestCase):
    def test_confirmation_requires_pressure_response_in_correct_order(self):
        s=start_check();self.assertEqual(s.puzzle,'brake')
        operate(s,'observe');self.assertEqual(s.brake['stage'],'charge')
        operate(s,'charge');BrakeTest.step(s.brake,6)
        self.assertEqual(s.brake['line'],0)
        operate(s,'compressor');BrakeTest.step(s.brake,5);operate(s,'observe')
        self.assertEqual(s.brake['stage'],'apply')
        operate(s,'observe');self.assertEqual(s.brake['stage'],'apply')
        operate(s,'apply');BrakeTest.step(s.brake,4);operate(s,'observe')
        self.assertEqual(s.brake['stage'],'release')
        operate(s,'observe');self.assertEqual(s.brake['stage'],'release')
        operate(s,'release');BrakeTest.step(s.brake,3)
        self.assertTrue(operate(s,'observe'));finish(s)
        self.assertIn('drive',s.flags)
        Session.restore(s.snapshot())

    def test_partial_pressure_survives_load_and_legacy_progress_is_preserved(self):
        s=start_check();operate(s,'compressor');operate(s,'charge');BrakeTest.step(s.brake,1.5)
        loaded=Session.restore(s.snapshot());self.assertEqual(loaded.brake,s.brake)
        loaded.interact('controls');self.assertEqual(loaded.puzzle,'brake')
        BrakeTest.step(loaded.brake,4);operate(loaded,'observe')
        self.assertEqual(loaded.brake['stage'],'apply')
        completed=start_check();brake_check(completed)
        old=completed.snapshot();old['schema']=7;old.pop('brake')
        old['flags'].remove('c1_brake_ready')
        restored=Session.restore(old)
        self.assertEqual(restored.brake['stage'],'done');self.assertIn('drive',restored.flags)

    def test_invalid_pressure_and_departure_cannot_be_restored(self):
        s=Session()
        with self.assertRaises(ValueError):s.apply('drive')
        for value in (-1,6,float('nan'),True):
            data=s.snapshot();data['brake']['line']=value
            with self.assertRaises(ValueError):Session.restore(data)
        data=s.snapshot();data['flags'].append('c1_brake_ready')
        with self.assertRaises(ValueError):Session.restore(data)
