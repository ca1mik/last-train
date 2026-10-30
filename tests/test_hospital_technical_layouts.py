import copy
import unittest
from lasttrain.content import SCENES,walkable,clear_sight
from lasttrain.model import Session
import test_hospital_receiving as route


class HospitalTechnicalLayoutTests(unittest.TestCase):
    def test_legacy_positions_keep_tools_and_partial_puzzles(self):
        s=route.initial()
        for key in ('yard','shed','cable','winch'):s=route.use(s,key)
        s.power[0]=(s.power[0]+1)%4
        for scene,pos in (('power',[540,350]),('shed',[500,380]),('yard',[830,220])):
            s.enter(scene)
            data=s.snapshot();data.update(schema=13,pos=pos)
            original=copy.deepcopy(data)
            loaded=Session.restore(data)
            self.assertEqual(loaded.pos,list(SCENES[scene].start))
            self.assertEqual(loaded.flags,s.flags)
            self.assertEqual(loaded.choices,s.choices)
            self.assertEqual(loaded.power,s.power)
            self.assertEqual(loaded.winch,s.winch)
            self.assertEqual(data,original)
            data['schema']=14
            with self.assertRaises(ValueError):Session.restore(data)

    def test_anchors_and_returns_are_on_floor(self):
        for key in ('power','shed','yard'):
            scene=SCENES[key]
            self.assertTrue(walkable(scene,scene.start),key)
            for obj in scene.objects:self.assertTrue(walkable(scene,obj.pos),(key,obj.id))
        s=route.initial()
        for key in ('yard','shed','exit'):s=route.use(s,key)
        self.assertEqual(s.scene,'yard')
        self.assertTrue(walkable(SCENES['yard'],s.pos))
        for pos in ((1300,750),(700,520)):
            self.assertTrue(walkable(SCENES['yard'],pos))
        self.assertFalse(clear_sight(SCENES['yard'],(650,650),(1200,650)))

    def test_taken_tools_do_not_restart_collection_dialogue(self):
        s=route.initial()
        for key in ('yard','shed','cable','winch'):s=route.use(s,key)
        before=s.snapshot()
        for key in ('cable','winch'):
            s.interact(key)
            self.assertIsNone(s.dialogue)
            self.assertEqual(s.flags,set(before['flags']))
