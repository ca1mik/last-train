import math
import copy
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import tempfile
import unittest
import pygame as pg
from lasttrain.carrying import rigid_rear,carrier_grips,grip_pairs,ELEVATION,CARRIER_SPACING,team_walkable
from lasttrain.animation import SpriteRig
from lasttrain.app import App,V,blocked
from lasttrain.content import SCENES


class CarryTests(unittest.TestCase):
    def test_checkpoint_preserves_rear_position_and_rejects_a_collapsed_team(self):
        from lasttrain.combat import cold_open
        from lasttrain.model import Session
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'save.json';app=App(path)
            try:
                app.state=cold_open();app.state.dialogue=None
                app.state.flags.update(('carry','door_open','relay_nina'))
                app.state.enter('ward',(900,750));app.state.carrying=True;app.facing=V(-1,0)
                app.loaded_scene=None;app.scene_changed();app.move(V(-35,-10));app.save()
                before=app.carry_positions()[1];data=app.state.snapshot();original=copy.deepcopy(data)
                loaded=Session.restore(data);self.assertEqual(data,original)
                self.assertEqual(loaded.carry_rear,list(before))
                app.action('load');self.assertLess(app.carry_positions()[1].distance_to(before),.001)
                bad=copy.deepcopy(data);bad['carry_rear']=list(data['pos'])
                with self.assertRaises(ValueError):Session.restore(bad)
                bad=copy.deepcopy(data);bad['carry_rear']=[20,20]
                with self.assertRaises(ValueError):Session.restore(bad)
            finally:pg.quit()

    def test_reversing_keeps_length_and_the_full_team_cannot_cut_a_corner(self):
        with tempfile.TemporaryDirectory() as temp:
            app=App(Path(temp)/'save.json')
            try:
                app.state.enter('ward',(900,750));app.state.carrying=True;app.facing=V(1,0);app.seed_carry_trail()
                previous=V(app.carry_positions()[1])
                for _ in range(80):
                    app.move(V(-4,0));_,rear,_=app.carry_positions()
                    self.assertAlmostEqual(rear.distance_to(app.state.pos),CARRIER_SPACING*SCENES['ward'].actor_scale)
                    self.assertTrue(team_walkable(SCENES['ward'],app.state.pos,rear))
                    self.assertLess(rear.distance_to(previous),8);previous=V(rear)
                app.state.enter('waiting',(1100,700));app.carry_trail=[];app.seed_carry_trail()
                app.move(V(0,-200));_,rear,_=app.carry_positions()
                self.assertGreater(app.state.pos[1],530)
                self.assertTrue(team_walkable(SCENES['waiting'],app.state.pos,rear))
            finally:pg.quit()

    def test_backward_steps_plant_the_foot_using_travel_not_facing(self):
        pg.init();pg.display.set_mode((1,1),pg.HIDDEN)
        try:
            rig=SpriteRig(Path('assets/characters/artem-rig-v01.png'));original=rig.segment;captured=[]
            root=V(400,350)
            def capture(surface,name,start,end,scale):
                if name=='leg_l':captured.append(V(end)+root-V(80,118))
                original(surface,name,start,end,scale)
            rig.segment=capture
            for x,phase in ((400,.2*math.pi),(392,.4*math.pi)):
                root=V(x,350);surface=pg.Surface((800,600),pg.SRCALPHA)
                rig.draw(surface,root,phase,True,(1,0),travel_direction=(-1,0))
            self.assertLess(captured[0].distance_to(captured[1]),.01)
        finally:pg.quit()

    def test_both_ends_of_stretcher_are_level_on_horizontal_floor(self):
        for angle in (0,180,-180):
            a,b=grip_pairs(V(400,500),(306,105),1.7,angle)
            self.assertLess(abs(((a[0]+a[1])*.5).y-((b[0]+b[1])*.5).y),1)

    def test_right_angle_turn_keeps_rigid_length_instead_of_arc_midpoint(self):
        trail=[V(500,500),V(500,600),V(300,600),V(100,600)]
        rear=rigid_rear(trail[0],trail,170)
        self.assertAlmostEqual(rear.distance_to(trail[0]),170)
        self.assertAlmostEqual(rear.y,600)
        self.assertLess(rear.x,400)
        self.assertAlmostEqual(rigid_rear((500,500),trail[:2],170).distance_to((500,500)),170)

    def test_handle_projection_follows_flipped_and_rotated_stretcher(self):
        center=V(300,400);size=(306,105);scale=1.7
        base=grip_pairs(center,size,scale,0)
        for angle in (-180,-135,-90,-45,0,45,90,135,180):
            direction=V(1,0).rotate(-angle)
            front=center+direction*144.5;rear=center-direction*144.5
            pairs=carrier_grips(center,size,scale,angle,front,rear)
            self.assertLess(sum(p.distance_to(front) for p in pairs[0]),sum(p.distance_to(front) for p in pairs[1]))
            # Rotation preserves the separation of handles on each end.
            distances=sorted(pair[0].distance_to(pair[1]) for pair in pairs)
            for actual,expected in zip(distances,sorted(pair[0].distance_to(pair[1]) for pair in base)):
                self.assertAlmostEqual(actual,expected)

    def test_wrists_stay_locked_through_walk_phases_and_mirroring(self):
        pg.init();pg.display.set_mode((1,1),pg.HIDDEN)
        try:
            for name in ('artem-rig-v01','artem-back-rig-v01','lida-rig-v01','lida-back-rig-v01'):
                rig=SpriteRig(Path('assets/characters')/(name+'.png'))
                original=rig.bent_arm;captured=[]
                def capture(surface,part,shoulder,hand,scale):
                    captured.append(V(hand));original(surface,part,shoulder,hand,scale)
                rig.bent_arm=capture
                for scale in (1,1.7,2.8):
                    for direction in ((1,0),(-1,0),(0,-1),(0,1)):
                        pos=V(350,400);targets=(pos+V(-10,-72)*scale,pos+V(10,-40)*scale)
                        for phase in (0,.7,1.6,3.8,5.4):
                            captured.clear();surface=pg.Surface((800,600),pg.SRCALPHA)
                            rig.draw(surface,pos,phase,True,direction,scale,hand_targets=targets)
                            self.assertEqual(len(captured),2)
                            for actual,expected in zip(captured,targets):
                                if direction[0]<0:actual.x=round(160*scale)-actual.x
                                actual+=pos-V(80,118)*scale
                                self.assertLess(actual.distance_to(expected),1.1)
        finally:pg.quit()

    def test_pickup_near_wall_places_full_team_on_available_floor(self):
        with tempfile.TemporaryDirectory() as temp:
            app=App(Path(temp)/'save.json')
            try:
                app.state.enter('ward',(1030,680));app.state.carrying=True
                app.facing=V(0,1);app.seed_carry_trail()
                center,rear,_=app.carry_positions()
                self.assertAlmostEqual(rear.distance_to(app.state.pos),CARRIER_SPACING*SCENES['ward'].actor_scale)
                self.assertEqual(center,(V(app.state.pos)+rear)*.5)
                self.assertFalse(blocked('ward',rear,22))
                for point in app.carry_trail:self.assertFalse(blocked('ward',point,22))
            finally:pg.quit()
