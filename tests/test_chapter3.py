import copy
from pathlib import Path
import tempfile
import unittest
from lasttrain.model import Session
from lasttrain.mechanics import RadioTune
from lasttrain.chapters import chapter2,chapter3
from lasttrain.content import DIALOGUES
from test_chapter2 import start_second,prepare_receiving
from test_story import finish

def finish_second(truth=0,card=False):
    s=start_second()
    if card:
        for key in ('refuge','raisa','roster','exit'):s.interact(key);finish(s)
    for key in ('nina','refuge','lida','exit','yard','shed','winch','exit','exit','switch'):
        s.interact(key);finish(s)
    for action in ('crank','pawl','crank','crank','crank','crank','pawl'):chapter2.operate_winch(s,action)
    finish(s)
    prepare_receiving(s);s.interact('lida');finish(s)
    s.interact('nina');finish(s,truth)
    s.interact('map');finish(s)
    return s

def start_third(truth=0):
    s=finish_second(truth);s.interact('map');finish(s)
    assert s.chapter==3
    s.start_dialogue('c3_arrival');finish(s)
    return s

def repair_line(s,pavel=0):
    s.interact('flat');s.interact('pavel');finish(s,pavel)
    s.interact('pavel');finish(s);s.interact('exit')
    s.interact('relay');s.interact('spare');finish(s);s.interact('exit')
    s.interact('yard');s.interact('gantry');s.interact('fault')
    assert 'c3_repair' not in s.flags
    s.interact('exit');s.interact('breaker');s.interact('gantry');s.interact('fault')
    assert 'c3_repair' in s.flags
    s.interact('exit');s.interact('breaker');s.interact('exit')
    s.interact('relay');s.interact('receiver')

def finish_third(s,policy=0,pattern=2,letter_decision=None):
    if letter_decision is not None:
        s.interact('flat');s.interact('pavel');finish(s)
        for index in (0,1,2):s.interact('letters');finish(s,index)
        s.interact('pavel');finish(s,letter_decision);s.interact('exit')
    repair_line(s)
    s.radio=list(RadioTune.target);chapter3.beacon(s,pattern);assert chapter3.listen(s);finish(s)
    s.interact('exit');s.interact('flat');s.interact('cassette');finish(s)
    s.interact('pavel');finish(s)
    s.interact('nina');finish(s,policy)
    s.interact('nina');finish(s)
    s.interact('map');finish(s)
    return s

class RadioTests(unittest.TestCase):
    def test_peak_is_unique_and_controls_wrap(self):
        self.assertTrue(RadioTune.locked(list(RadioTune.target)))
        self.assertEqual(RadioTune.quality(list(RadioTune.target)),1)
        peaks=[]
        for a in range(12):
            for b in range(10):
                for c in range(4):
                    v=[a,b,c]
                    if RadioTune.locked(v):peaks.append(v)
                    if v!=list(RadioTune.target):self.assertLess(RadioTune.quality(v),1)
        self.assertEqual(peaks,[list(RadioTune.target)])
        v=[0,0,0]
        for i,n in enumerate(RadioTune.ranges):
            RadioTune.adjust(v,i,-1);self.assertEqual(v[i],n-1)
            RadioTune.adjust(v,i);self.assertEqual(v[i],0)

    def test_live_answer_needs_repair_power_tuning_and_new_beacon(self):
        s=start_third()
        self.assertFalse(chapter3.beacon(s,2));self.assertEqual(s.signal_pattern,0)
        self.assertFalse(chapter3.listen(s))
        repair_line(s)
        self.assertFalse(chapter3.listen(s))
        s.radio=list(RadioTune.target);self.assertFalse(chapter3.listen(s))
        self.assertTrue(chapter3.beacon(s,3))
        s.enter('switchyard');s.interact('breaker')
        self.assertEqual(s.signal_pattern,0)
        self.assertFalse(chapter3.listen(s))
        s.interact('breaker');self.assertFalse(chapter3.listen(s))
        chapter3.beacon(s,2);self.assertTrue(chapter3.listen(s))
        self.assertEqual(s.dialogue,'c3_contact_2')
        finish(s);self.assertIn('c3_contact',s.flags)

class ThirdChapterTests(unittest.TestCase):
    def test_prior_honesty_changes_ninas_help(self):
        for truth,dialogue in ((0,'c3_nina_open'),(1,'c3_nina_guarded')):
            s=start_third(truth);s.interact('nina')
            self.assertEqual(s.dialogue,dialogue);finish(s)
            self.assertEqual('c3_notes' in s.flags,truth==0)

    def test_both_pavel_answers_recording_choices_and_signals_finish(self):
        for answer in (0,1):
            for policy in (0,1):
                for pattern in (2,3):
                    with self.subTest(answer=answer,policy=policy,pattern=pattern):
                        s=start_third(answer);repair_line(s,answer)
                        s.radio=list(RadioTune.target);chapter3.beacon(s,pattern)
                        self.assertTrue(chapter3.listen(s));self.assertEqual(s.dialogue,'c3_contact_'+str(pattern));finish(s)
                        s.interact('exit');s.interact('flat');s.interact('cassette');finish(s)
                        s.interact('pavel');finish(s);self.assertEqual(s.scene,'carriage')
                        s.interact('map');self.assertEqual(s.dialogue,'c3_tape_decision');finish(s,policy)
                        s.interact('nina');self.assertEqual(s.dialogue,'c3_nina_shared' if policy==0 else 'c3_nina_held');finish(s)
                        s.interact('lida');self.assertEqual(s.dialogue,'c3_lida_after' if policy==0 else 'c3_lida_wait');finish(s)
                        s.interact('pavel');finish(s);s.interact('map');finish(s)
                        self.assertIn('c3_complete',s.flags)
                        self.assertEqual(s.choices['pavel_response'],('listen','accuse')[answer])
                        self.assertEqual(s.choices['recording_policy'],('share','hold')[policy])
                        self.assertEqual(Session.restore(s.snapshot()).snapshot(),s.snapshot())

    def test_partial_radio_state_roundtrip_and_old_schema(self):
        s=start_third();s.radio=[7,3,1];s.line_power=False
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'save.json';s.save(p);loaded=Session.load(p)
        self.assertEqual(s.snapshot(),loaded.snapshot())
        old=finish_second().snapshot();old['schema']=3
        for key in ('radio','signal_pattern','line_power'):old.pop(key)
        migrated=Session.restore(old)
        self.assertEqual(migrated.chapter,2);self.assertIn('c2_complete',migrated.flags)
        self.assertEqual(migrated.radio,[0,0,0]);self.assertTrue(migrated.line_power)

    def test_invalid_contact_and_state_are_rejected(self):
        base=start_third().snapshot()
        for key,value in [('radio',[12,0,0]),('radio',[True,0,0]),('signal_pattern',1),('line_power',1)]:
            bad=copy.deepcopy(base);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):Session.restore(bad)
        bad=copy.deepcopy(base);bad['flags'].append('c3_contact')
        with self.assertRaises(ValueError):Session.restore(bad)

if __name__=='__main__':unittest.main()
