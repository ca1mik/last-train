"""Eight directions through the actual game carrier and stretcher renderer."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import sys
import math
import argparse
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
import pygame as pg
from lasttrain.render import Renderer
from lasttrain.carrying import carrier_grips,CARRIER_SPACING


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prefix',default='carry-directions-v25')
    args=parser.parse_args()
    pg.init();pg.display.set_mode((1,1),pg.HIDDEN)
    renderer=Renderer();sheet=pg.Surface((1440,720));font=pg.font.Font(None,24)
    scale=1.15
    for i,angle in enumerate((0,45,90,135,180,-135,-90,-45)):
        tile=pg.Surface((360,360));tile.fill((35,53,57))
        center=pg.Vector2(180,240);direction=pg.Vector2(1,0).rotate(-angle)
        front=center+direction*CARRIER_SPACING/2*scale;rear=center-direction*CARRIER_SPACING/2*scale
        image=renderer.scale_sprite(renderer.patient_sprite,scale)
        hands=carrier_grips(center,image.get_size(),scale,angle,front,rear)
        renderer.actor(center,'carry_patient',scale=scale,rotation=angle,target=tile)
        cast=(('artem',front,hands[0]),('lida',rear,hands[1]))
        for kind,pos,grips in sorted(cast,key=lambda row:row[1].y):
            renderer.actor(pos,kind,facing=direction,phase=i*math.pi/4,moving=True,
                           scale=scale,target=tile,hand_targets=grips)
        tile.blit(font.render(str(angle)+' degrees',True,(198,216,202)),(12,10))
        sheet.blit(tile,((i%4)*360,(i//4)*360))
    path=root/'release/previews'/(args.prefix+'.png')
    pg.image.save(sheet,str(path));pg.quit();print(path)


if __name__=='__main__':main()
