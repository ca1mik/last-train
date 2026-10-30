import copy
import unittest
from lasttrain.content import SCENES,walkable
from lasttrain.model import Session
from lasttrain.app import path_to
from test_chapter3 import start_third
from test_story import finish


class InteriorLayoutTests(unittest.TestCase):
    def test_old_apartment_preserves_letter_custody_and_input(self):
        s=start_third();s.interact('flat');s.interact('pavel');finish(s)
        for index in (2,0,1):s.interact('letters');finish(s,index)
        s.interact('pavel');finish(s,1)
        data=s.snapshot();data.update(schema=10,pos=[470,430])
        original=copy.deepcopy(data)
        restored=Session.restore(data)
        self.assertEqual(restored.pos,list(SCENES['flat'].start))
        self.assertEqual(restored.flags,s.flags)
        self.assertEqual(restored.choices,s.choices)
        self.assertEqual(restored.choices['pavel_statement'],'leave')
        self.assertEqual(data,original)

    def test_old_pharmacy_keeps_active_rescue(self):
        s=Session();s.enter('ward');s.start_dialogue('patient');finish(s)
        self.assertTrue(s.carrying)
        data=s.snapshot();data.update(schema=10,pos=[740,380])
        restored=Session.restore(data)
        self.assertTrue(restored.carrying)
        self.assertEqual(restored.flags,s.flags)
        self.assertEqual(restored.pos,list(SCENES['ward'].start))
        self.assertTrue(walkable(SCENES['ward'],restored.pos,24))

    def test_current_saves_cannot_walk_into_painted_furniture(self):
        for key in ('ward','flat'):
            s=Session() if key=='ward' else start_third()
            s.enter(key);data=s.snapshot();data['pos']=[700,250]
            with self.subTest(scene=key),self.assertRaises(ValueError):Session.restore(data)

    def test_stretcher_has_continuous_clearance_to_pharmacy_exit(self):
        scene=SCENES['ward'];objects={o.id:o for o in scene.objects}
        path=path_to('ward',objects['patient'].pos,objects['exit'].pos,24)
        self.assertTrue(path)
        self.assertLess(path[-1].distance_to(objects['exit'].pos),40)
        for point in path:self.assertTrue(walkable(scene,point,24))
