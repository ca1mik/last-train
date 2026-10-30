"""Record actual combat controls; chapter two uses an explicit canonical QA fixture."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root));sys.path.insert(0,str(root/'tests'))
import pygame as pg
from lasttrain.app import App
from tools.action_driver import Driver
from test_chapter2 import start_second


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prefix',default='combat-v31');args=parser.parse_args()
    out=root/'release'/'previews';shots=set();seen=set();results=[]
    process=subprocess.Popen([shutil.which('ffmpeg'),'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p',str(out/(args.prefix+'.mp4'))],stdin=subprocess.PIPE)
    try:
        with tempfile.TemporaryDirectory() as temp:
            app=App(Path(temp)/'save.json')
            for encounter in ('waiting','yard'):
                app.new();app.state.dialogue=None
                if encounter=='yard':
                    app.state=start_second();app.state.flags.add('action_mode');app.loaded_scene=None;app.scene_changed()
                start_health=app.state.health;driver=Driver(app)
                def frame(d):
                    if d.frames%2:return
                    image=app.renderer.render_at(app,(1920,1080))
                    for enemy in app.enemies:
                        seen.add(enemy.kind)
                        key=enemy.kind+'-'+enemy.attack_state
                        if enemy.kind!='walker' and enemy.attack_state in ('windup','charge','recover') and key not in shots:
                            pg.image.save(image,str(out/(args.prefix+'-'+key+'.png')));shots.add(key)
                    process.stdin.write(pg.image.tobytes(image,'RGB'))
                driver.on_frame=frame
                if encounter=='yard':driver.use('nina');driver.use('yard')
                driver.fight();driver.tick(.3)
                results.append({'encounter':encounter,'seconds':driver.frames/60,'start_health':start_health,'end_health':app.state.health,'defeated':not app.enemies})
    finally:process.stdin.close();pg.quit()
    if process.wait(timeout=60):raise RuntimeError('Encode failed')
    report={'encounters':results,'seen_types':sorted(seen),'shots':sorted(shots),'resolution':[1920,1080],'fps':30,'automated_runtime_recording':True,'human_playtest':False,'chapter2_start':'canonical model fixture, not full campaign runtime traversal','audio':False}
    (out/(args.prefix+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)


if __name__=='__main__':main()
