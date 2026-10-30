"""Contact sheet of the actual renderer, including view and phase selection."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import sys
import tempfile
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root))
import pygame as pg
from lasttrain.app import App

with tempfile.TemporaryDirectory() as temp:
    app=App(Path(temp)/'save.json');sheet=pg.Surface((1600,1200));sheet.fill((24,34,39))
    for row,(kind,direction) in enumerate((('brute',(0,1)),('brute',(0,-1)),('brute',(1,0)),('runner',(1,0)))):
        phases=(('windup',.7),('windup',.2),('recover',1.1),('recover',.6)) if kind=='brute' else (('windup',.5),('windup',.2),('charge',.1),('recover',.6))
        for column,(state,timer) in enumerate(phases):
            x=column*400+200;y=row*300+285
            app.renderer.actor((x,y),'enemy_'+kind,target=sheet,scale=1.4,facing=direction,enemy_state=state,enemy_timer=timer)
            sheet.blit(app.renderer.small.render(f'{kind} / {direction} / {state} {timer}',True,(220,225,212)),(column*400+15,row*300+6))
    pg.image.save(sheet,str(root/'release'/'previews'/'enemy-poses-v31.png'));pg.quit()
