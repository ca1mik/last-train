"""Record the game renderer's walk cycle; never alters the raster source atlas."""
import argparse
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
import pygame as pg
from lasttrain.animation import SpriteRig

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--atlas',default='assets/characters/artem-rig-v01.png')
    parser.add_argument('--view',choices=('front','back'),default='front')
    parser.add_argument('--prefix',default='hero-walk-v04')
    args=parser.parse_args()
    pg.init();pg.display.set_mode((1,1),pg.HIDDEN);rig=SpriteRig(root/args.atlas)
    out=root/'release'/'previews';out.mkdir(parents=True,exist_ok=True)
    sheet=pg.Surface((1280,720));sheet.fill((35,53,57))
    for i in range(8):
        x=150+i%4*310;y=310+i//4*340
        rig.draw(sheet,(x,y),i/8*math.tau,True,(0,-1 if args.view=='back' else 1),2.3,i/8,1)
        pg.draw.line(sheet,(100,135,125),(x-100,y),(x+100,y),1)
    contact=out/(args.prefix+'-contact.png')
    video=out/(args.prefix+'.mp4')
    pg.image.save(sheet,str(contact))
    executable=shutil.which('ffmpeg')
    if executable:
        command=[executable,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','640x480',
                 '-r','24','-i','pipe:0','-an','-c:v','libx264','-pix_fmt','yuv420p',str(video)]
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        surface=pg.Surface((640,480));direction=pg.Vector2(1,-1 if args.view=='back' else 1).normalize();distance=0
        try:
            for frame in range(96):
                t=frame/24;blend=min(1,t/.3,(4-t)/.3)
                distance+=100*blend/24
                surface.fill((31,46,49));camera=direction*distance
                for x in range(-64,704,64):
                    pg.draw.line(surface,(49,67,67),(x-camera.x%64,0),(x-camera.x%64,480),1)
                for y in range(-64,544,64):
                    pg.draw.line(surface,(49,67,67),(0,y-camera.y%64),(640,y-camera.y%64),1)
                rig.draw(surface,(320,350),distance/(40*2.4)*math.pi,True,direction,2.4,t,blend)
                process.stdin.write(pg.image.tobytes(surface,'RGB'))
        finally:process.stdin.close()
        error=process.stderr.read().decode('utf-8',errors='replace')
        if process.wait(timeout=60):raise RuntimeError(error)
        print('Recorded',video)
    print('Rendered',contact)
    pg.quit()

if __name__=='__main__':main()
