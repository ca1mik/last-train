import math
import unittest
import pygame as pg
from pathlib import Path
from lasttrain.animation import foot_motion,SpriteRig,view_for_direction

class GaitTests(unittest.TestCase):
    def test_upward_directions_use_back_and_horizontal_keeps_front(self):
        for direction in ((0,-1),(-1,-1),(1,-1)):
            self.assertEqual(view_for_direction(direction),'back')
        for direction in ((0,0),(-1,0),(1,0),(0,1),(-1,1),(1,1)):
            self.assertEqual(view_for_direction(direction),'front')
    def test_stance_foot_remains_in_world_place_while_root_moves(self):
        for direction in ((1,0),(0,1),(1,1),(-1,-1)):
            d=pg.Vector2(direction).normalize()
            a,_=foot_motion(math.pi*.2,d)
            b,_=foot_motion(math.pi*.4,d)
            self.assertLess((a-(d*8+b)).length(),1e-6)

    def test_opposite_feet_alternate_swing_and_ground_contact(self):
        _,left=foot_motion(math.pi*1.5,(0,1))
        _,right=foot_motion(math.pi*2.5,(0,1))
        self.assertAlmostEqual(left,7)
        self.assertEqual(right,0)
        _,left=foot_motion(math.pi*.5,(0,1))
        _,right=foot_motion(math.pi*1.5,(0,1))
        self.assertEqual(left,0)
        self.assertAlmostEqual(right,7)

    def test_selected_rig_has_distinct_phases_without_head_jumps(self):
        pg.init();pg.display.set_mode((1,1),pg.HIDDEN)
        for filename,direction in (('artem-rig-v01.png',(0,1)),('artem-back-rig-v01.png',(0,-1)),('nina-rig-v01.png',(1,0)),('lida-rig-v01.png',(1,0)),('pavel-rig-v01.png',(1,0)),('nina-back-rig-v01.png',(0,-1)),('lida-back-rig-v01.png',(0,-1)),('pavel-back-rig-v01.png',(0,-1))):
            with self.subTest(filename=filename):
                rig=SpriteRig(Path(__file__).resolve().parent.parent/'assets'/'characters'/filename)
                frames=[];tops=[]
                for i in range(16):
                    surface=pg.Surface((400,400),pg.SRCALPHA)
                    rig.draw(surface,(200,280),i/16*math.tau,True,direction,2,i/16,1)
                    tops.append(surface.get_bounding_rect(min_alpha=128).top)
                    frames.append(pg.image.tobytes(surface,'RGBA'))
                self.assertGreater(len(set(frames)),12)
                self.assertLessEqual(max(tops)-min(tops),4)
        pg.quit()

    def test_npc_idle_does_not_walk_in_place(self):
        from lasttrain.render import Renderer
        pg.init();pg.display.set_mode((1,1),pg.HIDDEN);renderer=Renderer()
        for kind in ('nina','lida','pavel'):
            with self.subTest(kind=kind):
                self.assertIn(kind,renderer.npc_rigs)
                frames=[]
                for phase in (0,1,2):
                    surface=pg.Surface((300,300),pg.SRCALPHA)
                    renderer.actor((150,220),kind,phase=phase,moving=False,target=surface,time=0)
                    frames.append(pg.image.tobytes(surface,'RGBA'))
                self.assertEqual(len(set(frames)),1)
                moving=pg.Surface((300,300),pg.SRCALPHA)
                renderer.actor((150,220),kind,phase=1,moving=True,target=moving)
                self.assertNotEqual(frames[0],pg.image.tobytes(moving,'RGBA'))
        pg.quit()

    def test_renderer_selects_rear_atlas_for_upward_movement(self):
        from lasttrain.render import Renderer
        pg.init();pg.display.set_mode((1,1),pg.HIDDEN);renderer=Renderer()
        self.assertIsNotNone(renderer.hero_back_rig)
        surface=pg.Surface((300,300),pg.SRCALPHA)
        renderer.actor((150,220),facing=(0,-1),moving=True,phase=1,target=surface)
        actual=pg.image.tobytes(surface,'RGBA')
        expected=pg.Surface((300,300),pg.SRCALPHA)
        renderer.hero_clips['back'].draw(expected,(150,220),1)
        self.assertEqual(actual,pg.image.tobytes(expected,'RGBA'))
        other=pg.Surface((300,300),pg.SRCALPHA)
        renderer.actor((150,220),facing=(0,1),moving=True,phase=1,target=other)
        self.assertNotEqual(actual,pg.image.tobytes(other,'RGBA'))
        pg.quit()

if __name__=='__main__':unittest.main()
