import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pygame as pg
from lasttrain.app import App,V
from lasttrain.render import Renderer
from lasttrain.model import Session


class NpcViewTests(unittest.TestCase):
    def test_renderer_uses_authored_rear_for_upward_npc_directions(self):
        pg.init();pg.display.set_mode((1,1),pg.HIDDEN)
        try:
            renderer=Renderer()
            for kind in ('nina','lida','pavel'):
                for direction in ((0,-1),(1,-1),(-1,-1),(1,0),(-1,0),(0,1)):
                    actual=pg.Surface((320,320),pg.SRCALPHA)
                    renderer.actor((160,230),kind,phase=1,moving=True,facing=direction,target=actual)
                    expected=pg.Surface((320,320),pg.SRCALPHA)
                    rig=renderer.npc_back_rigs[kind] if direction[1]<0 else renderer.npc_rigs[kind]
                    rig.draw(expected,(160,230),1,True,direction)
                    self.assertEqual(pg.image.tobytes(actual,'RGBA'),pg.image.tobytes(expected,'RGBA'),(kind,direction))
        finally:pg.quit()

    def test_world_turns_nina_toward_player_and_lida_toward_carry_direction(self):
        with tempfile.TemporaryDirectory() as temp:
            app=App(Path(temp)/'save.json')
            try:
                app.state=Session();app.state.enter('ward',(620,510));app.mode='play';app.scene_changed()
                rear=app.renderer.npc_back_rigs['nina']
                with patch.object(rear,'draw',wraps=rear.draw) as draw:
                    app.draw();self.assertEqual(draw.call_count,1)
                    app.state.pos=[620,630];app.draw();self.assertEqual(draw.call_count,1)
                app.state.pos=[900,600];app.state.apply('carry')
                from lasttrain.carrying import CARRIER_SPACING
                from lasttrain.content import SCENES
                app.state.carry_rear=[900,600+CARRIER_SPACING*SCENES['ward'].actor_scale]
                rear=app.renderer.npc_back_rigs['lida']
                with patch.object(rear,'draw',wraps=rear.draw) as draw:
                    app.draw();self.assertEqual(draw.call_count,1)
                    self.assertIsNotNone(draw.call_args.args[-2])
            finally:pg.quit()
