import copy
import tempfile
from pathlib import Path
import unittest
from lasttrain.model import Session
from lasttrain.content import DIALOGUES, SCENES
from lasttrain.brakes import BrakeTest,operate as operate_brakes
from lasttrain.inspection import operate as inspect_exit

def disembark(s):
    s.interact('controls');finish(s)
    s.interact('cabin_door')
    for action in ('step','gap','landing','platform'):inspect_exit(s,action)
    finish(s)
    s.start_dialogue('c1_aligned');finish(s)

def brake_check(s):
    for action,wait in (('compressor',0),('charge',5),('observe',0),('apply',4),('observe',0),('release',3),('observe',0)):
        operate_brakes(s,action)
        for _ in range(round(wait/.05)):BrakeTest.step(s.brake,.05)
    finish(s)

def finish(s,choice=0):
    for _ in range(50):
        if not s.dialogue:return
        data=DIALOGUES[s.dialogue]
        if s.line>=len(data['lines']):s.choose(choice)
        else:s.advance()
    raise AssertionError('Dialogue did not finish')

def rescue(route='nina',choice=0):
    s=Session();s.start_dialogue('opening');finish(s)
    s.interact('cabin_door');finish(s)
    s.interact('controls');finish(s)
    brake_check(s)
    s.start_dialogue('loop');finish(s)
    disembark(s)
    s.interact('station_door');assert s.scene=='platform'
    s.interact('lida');finish(s)
    s.interact('station_door');assert s.scene=='waiting'
    s.interact('ward_door');assert s.scene=='waiting'
    if route=='tool':
        s.interact('relay');finish(s,1)
        s.interact('workshop_door');s.interact('stopper');finish(s)
        s.interact('note');finish(s);s.interact('exit');s.interact('relay');finish(s)
    else:s.interact('relay');finish(s,0)
    assert 'door_open' in s.flags
    s.interact('ward_door');s.interact('patient');finish(s)
    assert s.carrying
    s.interact('exit');s.interact('exit');s.interact('train')
    assert not s.carrying and 'rescued' in s.flags
    s.interact('lida');finish(s,choice)
    return s

class StoryTests(unittest.TestCase):
    def test_both_rescue_routes_and_all_answers_reach_ending(self):
        for route in ('nina','tool'):
            for choice in range(3):
                with self.subTest(route=route,choice=choice):
                    s=rescue(route,choice)
                    self.assertEqual(s.scene,'carriage')
                    s.interact('map');self.assertIsNone(s.dialogue)
                    s.interact('nina');finish(s)
                    s.interact('lida');finish(s)
                    s.interact('map');finish(s)
                    self.assertIn('chapter_complete',s.flags)
                    self.assertEqual(s.choices['lida'],('admit','order','hand')[choice])

    def test_roundtrip_at_every_story_beat(self):
        s=Session()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'checkpoint.json'
            for key in ('opening','meet_nina','departure','loop','lida_intro','relay_nina','patient'):
                if key=='relay_nina':s.enter('waiting')
                if key=='patient':s.enter('ward')
                s.start_dialogue(key);finish(s)
                if key=='departure':brake_check(s)
                if key=='loop':disembark(s)
                s.save(path);loaded=Session.load(path)
                self.assertEqual(s.snapshot(),loaded.snapshot())

    def test_corrupt_saves_rejected(self):
        base=Session().snapshot()
        for field,value in [('schema',0),('scene','missing'),('pos',[float('nan'),3]),
                            ('pos',[0,0]),('pos',[300,250]),('health',-1),('elapsed',float('inf')),
                            ('flags',['bogus']),('choices',{'lida':'wrong'}),('carrying',True)]:
            bad=copy.deepcopy(base);bad[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):Session.restore(bad)

    def test_dialogue_references_resolve(self):
        for data in DIALOGUES.values():
            self.assertTrue(data['lines'])
            for _,key in data.get('choices',[]):self.assertIn(key,DIALOGUES)
        for scene in SCENES.values():
            ids=[obj.id for obj in scene.objects]
            self.assertEqual(len(ids),len(set(ids)))

if __name__=='__main__':unittest.main()
