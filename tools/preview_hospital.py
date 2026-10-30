"""Capture the second sortie via controls from a canonical chapter-two QA fixture."""
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
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root));sys.path.insert(0,str(root/'tests'))
import pygame as pg
from lasttrain.app import App
from tools.action_driver import Driver
from test_chapter2 import start_second


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--route',choices=('manual','electric'),default='manual');parser.add_argument('--prefix',default='hospital-v32');args=parser.parse_args()
    prefix=args.prefix+'-'+args.route;out=root/'release'/'previews';events=[];shots=set();fps=30;rate=48000
    with tempfile.TemporaryDirectory() as temp:
        app=App(Path(temp)/'save.json');app.state=start_second();app.state.flags.add('action_mode')
        app.mode='play';app.loaded_scene=None;app.scene_changed();driver=Driver(app)
        process=subprocess.Popen([shutil.which('ffmpeg'),'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p',str(out/(prefix+'-silent.mp4'))],stdin=subprocess.PIPE)
        original=app.audio.play
        def sound_event(name):
            material='wood' if app.state.scene in ('cabin','carriage','refuge','shed') else 'concrete'
            if name=='step':sound=app.audio.steps[material][app.audio.step_index%5];gain=app.audio.volume*.58
            else:sound=app.audio.sounds.get(name);gain=app.audio.volume*(.3 if name=='metal' else .65)
            if sound is not None:events.append((driver.frames/60,sound.get_raw(),gain))
            original(name)
        app.audio.play=sound_event
        def frame(d):
            if d.frames%2:return
            image=app.renderer.render_at(app,(1920,1080))
            task=app.field_task
            label=('winch' if task is not None and task.kind=='c2_rhythm' and app.state.winch['turns']==1 else
                   'lock' if task is not None and task.kind=='c2_lock' and task.progress>.3 else
                   'board' if app.mode=='power' else
                   'receiving' if task is not None and task.kind=='c2_receive' and task.progress>.5 else
                   'packing' if task is not None and task.kind=='c2_pack' and task.progress>.4 else
                   'boarded' if 'c2_boarded' in app.state.flags else None)
            if label is not None and label not in shots:
                pg.image.save(image,str(out/f'{prefix}-{label}.png'));shots.add(label)
            process.stdin.write(pg.image.tobytes(image,'RGB'))
        driver.on_frame=frame
        try:state=driver.hospital_sortie(args.route);driver.tick(.4)
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
        report={'duration_seconds':duration,'health':state.health,'scene':state.scene,'chapter_complete':'c2_complete' in state.flags,
                'boarded':'c2_boarded' in state.flags,'power_route':state.choices.get('power_route'),'hospital_truth':state.choices.get('hospital_truth'),
                'shots':sorted(shots),'audio_peak':float(np.abs(mix).max()),'resolution':[1920,1080],'fps':fps,
                'start':'canonical model fixture after chapter-one completion; chapter one not recorded here',
                'automated_runtime_recording':True,'human_playtest':False}
        (out/(prefix+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8');print(report);pg.quit()


if __name__=='__main__':main()
