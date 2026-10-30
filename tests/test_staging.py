import unittest
from lasttrain.staging import CrossingSequence
from lasttrain.content import SCENES,walkable

class CrossingTests(unittest.TestCase):
    def test_assisted_group_keeps_spacing_and_pavel_leaves_last(self):
        sequence=CrossingSequence()
        for t in (0,1,3,8,14,18):
            sequence.elapsed=t
            cast={kind:(pos,moving) for kind,pos,_,moving in sequence.actors()}
            center=cast['carry_patient'][0]
            self.assertEqual(cast['lida'][0][0]-center[0],70)
            self.assertEqual(center[0]-cast['artem'][0][0],70)
            for kind,(pos,_) in cast.items():self.assertTrue(walkable(SCENES['crossing'],pos),(t,kind))
            if t<4:self.assertFalse(cast['pavel'][1])
        self.assertTrue(all(pos[0]>=1200 for pos,_ in cast.values()))
        self.assertTrue(sequence.advance(.1))
        self.assertEqual(sequence.elapsed,18)
