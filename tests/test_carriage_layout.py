import unittest
from lasttrain.model import Session
from lasttrain.content import SCENES,walkable
from test_chapter3 import finish_second

class CarriageLayoutTests(unittest.TestCase):
    def test_people_and_map_have_walkable_positions_inside_the_playable_crop(self):
        scene=SCENES['carriage']
        self.assertEqual(scene.art_crop,(0,0,1536,720))
        self.assertTrue(walkable(scene,scene.start))
        for obj in scene.objects:self.assertTrue(walkable(scene,obj.pos),(obj.id,obj.pos))

    def test_old_carriage_positions_relocate_without_losing_choices(self):
        s=finish_second();data=s.snapshot();data['schema']=9;data['pos']=[470,390]
        restored=Session.restore(data)
        self.assertEqual(restored.pos,list(SCENES['carriage'].start))
        self.assertEqual(restored.flags,s.flags);self.assertEqual(restored.choices,s.choices)
        self.assertEqual(data['pos'],[470,390])
        current=s.snapshot();current['pos']=[470,390]
        with self.assertRaises(ValueError):Session.restore(current)
