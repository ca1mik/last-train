import copy
import unittest
from lasttrain.model import Session
from lasttrain.content import SCENES,walkable
from test_chapter4 import start_fourth,use,hear_account
from test_chapter5 import start_fifth


class TechnicalInteriorTests(unittest.TestCase):
    def test_old_positions_relocate_without_changing_progress_or_source(self):
        archive=start_fourth(1)
        for key in ('dispatch','handle','valentina'):use(archive,key)
        hear_account(archive);archive.enter('archive')
        workshop=Session();workshop.enter('workshop')
        workshop.interact('stopper');
        from test_story import finish
        finish(workshop)
        signal=start_fifth(letter_decision=1,account=True);signal.enter('signal_post')
        for state,old_pos in ((archive,[900,440]),(workshop,[590,340]),(signal,[1050,430])):
            data=state.snapshot();data.update(schema=11,pos=old_pos)
            before=copy.deepcopy(data)
            loaded=Session.restore(data)
            self.assertEqual(loaded.pos,list(SCENES[state.scene].start))
            self.assertEqual(loaded.flags,state.flags)
            self.assertEqual(loaded.choices,state.choices)
            self.assertEqual(data,before)
            current=state.snapshot();current['pos']=old_pos
            with self.assertRaises(ValueError):Session.restore(current)

    def test_interaction_anchors_are_on_floor_and_distinct(self):
        for key in ('archive','workshop','signal_post'):
            scene=SCENES[key]
            self.assertTrue(walkable(scene,scene.start))
            for obj in scene.objects:
                self.assertTrue(walkable(scene,obj.pos),(key,obj.id))
                for other in scene.objects:
                    if obj is other:continue
                    self.assertGreater(sum((a-b)**2 for a,b in zip(obj.pos,other.pos)),100**2,(key,obj.id,other.id))
