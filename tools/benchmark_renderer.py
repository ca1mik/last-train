"""Local renderer timing only: does not claim end-user FPS or whole-game QA."""
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
from time import perf_counter
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
import pygame as pg
from lasttrain import __version__
from lasttrain.app import App,Enemy

def main():
    results=[]
    with tempfile.TemporaryDirectory() as temp:
        app=App(Path(temp)/'save.json');app.mode='play';app.state.chapter=3
        app.state.flags.update(('c3_arrived','c3_met'))
        for scene in ('settlement','relay_house','switchyard'):
            app.state.enter(scene);app.enemies=[Enemy((1000,780)),Enemy((840,480))] if scene=='switchyard' else []
            app.moving=True;app.move_blend=1
            for _ in range(5):app.renderer.draw(app)
            samples=[]
            for i in range(120):
                app.time=i/60;app.walk_phase=i*.18
                before=perf_counter();app.renderer.draw(app);samples.append((perf_counter()-before)*1000)
            samples.sort()
            results.append({'scene':scene,'frames':len(samples),'median_ms':round(statistics.median(samples),3),
                            'p95_ms':round(samples[int(len(samples)*.95)-1],3),'max_ms':round(max(samples),3)})
        pg.quit()
    report={'version':__version__,'scope':'renderer only, 1280x720, SDL dummy, warmed scene cache; excludes gameplay update, display and vsync',
            'scenes':results,'release_readiness_proven':False}
    out=root/'release'/('renderer-perf-'+'.'.join(__version__.split('.')[:2])+'.json')
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
