"""Record the complete first rescue through real controls and active game time."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
import numpy as np
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root))
import pygame as pg
from lasttrain.app import App
from tools.action_driver import Driver


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prefix',default='sortie-v30');args=parser.parse_args();prefix=args.prefix
    out=root/'release'/'previews';events=[];shots=set();fps=30;rate=48000
    with tempfile.TemporaryDirectory() as temp:
        app=App(Path(temp)/'save.json');app.new();driver=Driver(app)
        process=subprocess.Popen([shutil.which('ffmpeg'),'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p',str(out/(prefix+'-silent.mp4'))],stdin=subprocess.PIPE)
        original=app.audio.play
        def sound_event(name):
            material='wood' if app.state.scene in ('cabin','carriage','flat','shed','refuge') else 'carpet' if app.state.scene=='ward' else 'concrete'
            if name=='step':sound=app.audio.steps[material][app.audio.step_index%5];gain=app.audio.volume*.58
            else:sound=app.audio.sounds.get(name);gain=app.audio.volume*(.3 if name=='metal' else .65)
            if sound is not None:events.append((driver.frames/60,sound.get_raw(),gain))
            original(name)
        app.audio.play=sound_event
        def frame(d):
            if d.frames%2:return
            image=app.renderer.render_at(app,(1920,1080))
            label=('relay' if app.field_task is not None and app.field_task.kind=='relay' and app.field_task.progress>.5 else
                   'return' if app.state.carrying and app.state.scene=='waiting' and app.state.pos[0]<1000 else
                   'loading' if app.field_task is not None and app.field_task.kind=='load' and app.field_task.progress>.5 else
                   'safe' if app.state.scene=='carriage' else None)
            if label is not None and label not in shots:
                pg.image.save(image,str(out/f'{prefix}-{label}.png'));shots.add(label)
            process.stdin.write(pg.image.tobytes(image,'RGB'))
        driver.on_frame=frame
        try:
            state=driver.sortie();driver.tick(1)
        finally:process.stdin.close()
        if process.wait(timeout=60):raise RuntimeError('Encode failed')
        duration=driver.frames/60;mix=np.zeros((round(duration*rate),2),np.float64)
        for when,raw,gain in events:
            sound=np.frombuffer(raw,dtype=np.int16).reshape(-1,2)/32768;start=round(when*rate)
            count=min(len(sound),len(mix)-start)
            if count>0:mix[start:start+count]+=sound[:count]*gain
        with wave.open(str(out/(prefix+'-audio.wav')),'wb') as wav:
            wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(rate)
            wav.writeframes((np.clip(mix,-1,1)*32767).astype(np.int16).tobytes())
        subprocess.run([shutil.which('ffmpeg'),'-y','-loglevel','error','-i',str(out/(prefix+'-silent.mp4')),'-i',str(out/(prefix+'-audio.wav')),'-c:v','copy','-c:a','aac','-b:a','192k','-shortest',str(out/(prefix+'.mp4'))],check=True)
        report={'duration_seconds':duration,'health':state.health,'scene':state.scene,'rescued':'rescued' in state.flags,
                'lida_boarded':'lida_boarded' in state.flags,'shots':sorted(shots),'audio_peak':float(np.abs(mix).max()),
                'resolution':[1920,1080],'fps':fps,'automated_runtime_recording':True,'human_playtest':False}
        (out/(prefix+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(report);pg.quit()


if __name__=='__main__':main()
