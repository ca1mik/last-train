"""Record actual movement, combat inputs and emitted foley in the game renderer."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from collections import defaultdict
from pathlib import Path
import json
import math
import shutil
import subprocess
import sys
import tempfile
import wave
import numpy as np
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root))
import pygame as pg
from lasttrain.app import App,V,path_to


def main():
    out=root/'release'/'previews';out.mkdir(exist_ok=True)
    fps=30;seconds=14;size=(1920,1080);rate=48000;events=[];frame=0
    with tempfile.TemporaryDirectory() as temp:
        app=App(Path(temp)/'save.json');app.new();original=app.audio.play
        def record(name):
            material='wood' if app.state.scene in ('cabin','carriage','flat','shed','refuge') else 'concrete'
            if name=='step':sound=app.audio.steps[material][app.audio.step_index%5];gain=app.audio.volume*.58
            else:sound=app.audio.sounds.get(name);gain=app.audio.volume*(.3 if name=='metal' else .65)
            if sound is not None:events.append((frame/fps,sound.get_raw(),gain))
            original(name)
        app.audio.play=record
        ffmpeg=shutil.which('ffmpeg')
        process=subprocess.Popen([ffmpeg,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p',str(out/'action-v28-silent.mp4')],stdin=subprocess.PIPE)
        try:
            for frame in range(fps*seconds):
                keys=defaultdict(int)
                if app.enemies:
                    enemy=min(app.enemies,key=lambda e:e.pos.distance_to(app.state.pos));delta=enemy.pos-V(app.state.pos)
                    if enemy.attack_state=='windup' and app.dash_cooldown<=0:
                        app.facing=-delta.normalize();app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_SPACE))
                    elif delta.length()<115:
                        app.attack(delta)
                    else:
                        path=path_to(app.state.scene,app.state.pos,enemy.pos)
                        direction=path[0]-V(app.state.pos) if path else delta
                        if abs(direction.x)>3:keys[pg.K_d if direction.x>0 else pg.K_a]=1
                        if abs(direction.y)>3:keys[pg.K_s if direction.y>0 else pg.K_w]=1
                else:
                    keys[pg.K_d]=1
                    if frame%90==0:app.event(pg.event.Event(pg.KEYDOWN,key=pg.K_SPACE))
                app.update(1/fps,keys)
                image=app.renderer.render_at(app,size)
                if frame in (0,85,150,260):pg.image.save(image,str(out/f'action-v28-frame-{frame:03}.png'))
                process.stdin.write(pg.image.tobytes(image,'RGB'))
        finally:process.stdin.close()
        if process.wait(timeout=60):raise RuntimeError('Video encode failed')
        mix=np.zeros((seconds*rate,2),np.float64)
        for when,raw,gain in events:
            sound=np.frombuffer(raw,dtype=np.int16).reshape(-1,2)/32768
            start=round(when*rate);length=min(len(sound),len(mix)-start)
            if length>0:mix[start:start+length]+=sound[:length]*gain
        peak=float(np.abs(mix).max());pcm=(np.clip(mix,-1,1)*32767).astype(np.int16)
        with wave.open(str(out/'action-v28-audio.wav'),'wb') as wav:
            wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(pcm.tobytes())
        subprocess.run([ffmpeg,'-y','-loglevel','error','-i',str(out/'action-v28-silent.mp4'),'-i',str(out/'action-v28-audio.wav'),'-c:v','copy','-c:a','aac','-b:a','192k','-shortest',str(out/'action-v28.mp4')],check=True)
        report={'duration':seconds,'resolution':size,'fps':fps,'audio_peak':peak,'sound_events':len(events),
                'health':app.state.health,'enemies_remaining':len(app.enemies),'defeated':sorted(f for f in app.state.flags if f.startswith('combat_down_')),
                'automated_runtime_recording':True,'human_playtest':False}
        (out/'action-v28.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
        pg.quit()


if __name__=='__main__':main()
