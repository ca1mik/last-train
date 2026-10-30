"""Record the real semaphore renderer after the campaign model prepares the crew."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
root=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(root),str(root/'tests')]
import pygame as pg
from lasttrain.app import App
from lasttrain.chapters import chapter5
from test_chapter5 import start_fifth
from test_story import finish


def main():
    state=start_fifth()
    for key in ('brake','nina','pavel','train','lida','cabin','coupler','gate','semaphore','plate'):
        state.interact(key);finish(state)
        if state.puzzle=='gate':
            for action in ('support','pin','swing','confirm'):chapter5.operate_gate(state,action)
            finish(state)
    out=root/'release/previews';out.mkdir(exist_ok=True)
    encoder=shutil.which('ffmpeg');process=None
    with tempfile.TemporaryDirectory() as temp:
        app=App(Path(temp)/'save.json');app.state=state;app.mode='play';app.scene_changed()
        if encoder:
            process=subprocess.Popen([encoder,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
                '-s','1280x720','-r','24','-i','pipe:0','-an','-c:v','libx264','-pix_fmt','yuv420p',
                str(out/'signal-operation-v24.mp4')],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            for frame in range(96):
                if frame==12:state.interact('lever');finish(state)
                app.update(1/24);app.draw()
                if frame in (0,18,72):
                    label={0:'closed',18:'moving',72:'open'}[frame]
                    pg.image.save(app.renderer.surface,str(out/('signal-'+label+'-v24.png')))
                if process:process.stdin.write(pg.image.tobytes(app.renderer.surface,'RGB'))
        finally:
            if process:process.stdin.close()
            pg.quit()
        if process:
            error=process.stderr.read().decode(errors='replace')
            if process.wait(timeout=60):raise RuntimeError(error)
    print(out/'signal-operation-v24.mp4')


if __name__=='__main__':main()
