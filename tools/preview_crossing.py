"""Record the actual crossing renderer for visual review."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import sys
from pathlib import Path
from types import SimpleNamespace
import shutil
import subprocess
import argparse
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
import pygame as pg
from lasttrain.render import Renderer
from lasttrain.staging import CrossingSequence

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prefix',default='crossing-v11');args=parser.parse_args()
    pg.init();pg.display.set_mode((1,1),pg.HIDDEN)
    renderer=Renderer();sequence=CrossingSequence()
    app=SimpleNamespace(crossing_sequence=sequence,time=0)
    out=root/'release'/'previews';out.mkdir(exist_ok=True,parents=True)
    executable=shutil.which('ffmpeg')
    process=None
    if executable:
        process=subprocess.Popen([executable,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
            '-s','1280x720','-r','24','-i','pipe:0','-an','-c:v','libx264','-pix_fmt','yuv420p',
            str(out/(args.prefix+'.mp4'))],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for frame in range(433):
            app.time=sequence.elapsed=frame/24
            renderer.crossing_scene(app)
            if frame==192:pg.image.save(renderer.surface,str(out/(args.prefix+'.png')))
            if process:process.stdin.write(pg.image.tobytes(renderer.surface,'RGB'))
    finally:
        if process:process.stdin.close()
    if process:
        error=process.stderr.read().decode(errors='replace')
        if process.wait(timeout=60):raise RuntimeError(error)
    pg.quit();print(out/(args.prefix+'.png'))

if __name__=='__main__':main()
