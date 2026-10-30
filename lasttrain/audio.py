"""Quiet tonal beds and CC0 foley; no continuously looping noise generator."""
from array import array
from pathlib import Path
import math
import pygame as pg

ROOT=Path(__file__).resolve().parent.parent/'assets'/'audio'/'kenney-impact'


def tone(name,rate,channels):
    durations={'engine':4,'bell':1.8,'flare':.4,'hurt':.22,'radio_signal':1.4,
               'radio_noise':.18,'beacon2':1,'beacon3':1.4,'dash':.16,'click':.055,'electric':.16}
    duration=durations[name];samples=array('h');count=round(duration*rate)
    for i in range(count):
        t=i/rate
        envelope=min(1,t/.005,(duration-t)/.015)
        if name=='engine':
            value=(math.sin(math.tau*40*t)*.04+math.sin(math.tau*80*t)*.014)*(1+.12*math.sin(math.tau*3*t))
            envelope=1
        elif name=='bell':
            value=sum(math.sin(math.tau*f*t)*a for f,a in ((780,.14),(1273,.05),(2041,.02)))*math.exp(-t*4)
        elif name.startswith('beacon'):
            pulse=t%.4
            value=math.sin(math.tau*660*t)*.09*math.sin(pulse/.13*math.pi)**2 if pulse<.13 and t<int(name[-1])*.4 else 0
        elif name=='radio_signal':
            value=math.sin(math.tau*(440 if t<.65 else 660)*t)*.055*math.sin(t*math.pi/duration)**2
        elif name=='electric':
            value=(math.sin(math.tau*(880*t+700*t*t))*.035+math.sin(math.tau*1660*t)*.02)*math.exp(-t*20)
        elif name in ('flare','dash','hurt'):
            f={'flare':160,'dash':240,'hurt':95}[name]
            value=math.sin(math.tau*(f*t-50*t*t))*.09*math.exp(-t*14)
        else:value=math.sin(math.tau*350*t)*.025*math.exp(-t*40)
        samples.extend([round(value*max(0,envelope)*32767)]*channels)
    return samples


class Audio:
    def __init__(self):
        self.enabled=False;self.volume=.55;self.sounds={};self.steps={};self.step_index=0;self.scene='cabin'
        try:
            if not pg.mixer.get_init():pg.mixer.init(48000,-16,2,1024)
            rate,_,channels=pg.mixer.get_init();self.channels=channels
            pg.mixer.set_num_channels(16);pg.mixer.set_reserved(2)
            for name in ('engine','bell','flare','hurt','radio_signal','radio_noise','beacon2','beacon3','click','dash','electric'):
                self.sounds[name]=pg.mixer.Sound(buffer=tone(name,rate,channels))
            for material in ('concrete','wood','carpet'):
                self.steps[material]=[pg.mixer.Sound(str(ROOT/f'footstep_{material}_{i:03}.ogg')) for i in range(5)]
            self.sounds['metal']=pg.mixer.Sound(str(ROOT/'impactMetal_light_000.ogg'))
            self.motor=pg.mixer.Channel(0);self.foley=pg.mixer.Channel(1)
            self.motor.play(self.sounds['engine'],loops=-1);self.motor.set_volume(0)
            self.enabled=True
        except (pg.error,FileNotFoundError):pass

    def play(self,name):
        if not self.enabled:return
        if name=='step':
            material='wood' if self.scene in ('cabin','carriage','flat','shed','refuge') else 'carpet' if self.scene=='ward' else 'concrete'
            variants=self.steps[material];sound=variants[self.step_index%len(variants)];self.step_index+=1
            self.foley.set_volume(self.volume*.58);self.foley.play(sound)
        elif name in self.sounds:
            sound=self.sounds[name];sound.set_volume(self.volume*(.3 if name=='metal' else .65));sound.play()

    def update(self,scene,paused=False):
        if not self.enabled:return
        self.scene=scene
        # Engine belongs to the train. Menus and rooms have no blanket hiss.
        self.motor.set_volume(self.volume*(.33 if scene in ('cabin','carriage') and not paused else 0))
