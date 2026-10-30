"""Check the assets actually consumed by the game, not discarded source variants."""
from pathlib import Path
import sys
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame as pg

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
CHARACTERS=['artem-source-v01.png','artem-walk-v02.png','nina-idle-v01.png',
            'lida-idle-v01.png','trackwalker-idle-v01.png','mikhail-stretcher-v01.png','pavel-idle-v01.png','artem-rig-v01.png','valentina-idle-v01.png','artem-back-rig-v01.png','nina-rig-v01.png','lida-rig-v01.png','pavel-rig-v01.png','raisa-idle-v01.png']

def main():
    pg.init()
    selected_characters=CHARACTERS+[name+'-back-rig-v01.png' for name in ('nina','lida','pavel')]+['artem-jog-'+view+'-v28.png' for view in ('front','back','side')]+['artem-idle-directions-v28.png','artem-attack-v28.png','trackwalker-move-v28.png']
    selected_characters+=['runner-move-v31.png','runner-action-v31.png','brute-walk-v31.png','artem-winch-pair-v32.png','nina-brace-v32.png']+['brute-attack-'+view+'-v31.png' for view in ('front','back','side')]
    for name in ['characters/'+name for name in selected_characters]+['props/signal-lever-v01.png','props/winch-cycle-v32.png']:
        path=ROOT/'assets'/name
        image=pg.image.load(str(path))
        assert image.get_flags() & pg.SRCALPHA, f'No alpha: {name}'
        corners=((0,0),(image.get_width()-1,0),(0,image.get_height()-1),(image.get_width()-1,image.get_height()-1))
        # Generated RGBA atlases can contain one alpha quantization step in an
        # otherwise empty corner. Parts are alpha-cropped before game rendering.
        # Reject visible backgrounds; preserve the original raster unchanged.
        corner_alpha=max(image.get_at(p).a for p in corners)
        assert corner_alpha<=1, f'Opaque corner: {name} (alpha {corner_alpha})'
        bounds=image.get_bounding_rect(min_alpha=128)
        assert bounds.w>100 and bounds.h>100, f'Empty character: {name}'
        print(f'{name}: {image.get_width()}x{image.get_height()}, corner alpha {corner_alpha}/255 OK')
    station=pg.image.load(str(ROOT/'assets'/'concepts'/'station-v01.png'))
    assert station.get_width()>=1280
    print('Station background: OK')
    from lasttrain.content import SCENE_ART
    selected=set(SCENE_ART.values())|{'environments/exit-inspection-v01.png'}
    for name in sorted(selected):
        scene=pg.image.load(str(ROOT/'assets'/name))
        assert scene.get_width()>=1280
        print(name+': OK')
    from lasttrain.animation import SpriteRig
    pg.display.set_mode((1,1),pg.HIDDEN)
    rig=SpriteRig(ROOT/'assets'/'characters'/'artem-rig-v01.png')
    assert set(rig.parts)=={'body','arm_l','arm_r','leg_l','leg_r','scarf'}
    rear=SpriteRig(ROOT/'assets'/'characters'/'artem-back-rig-v01.png')
    assert set(rear.parts)==set(rig.parts)
    nina=SpriteRig(ROOT/'assets'/'characters'/'nina-rig-v01.png')
    assert set(nina.parts)=={'body','arm_l','arm_r','leg_l','leg_r'}
    for name in ('lida','pavel'):
        npc=SpriteRig(ROOT/'assets'/'characters'/(name+'-rig-v01.png'))
        assert set(npc.parts)==set(nina.parts)
    for name in ('nina','lida','pavel'):
        npc=SpriteRig(ROOT/'assets'/'characters'/(name+'-back-rig-v01.png'))
        assert set(npc.parts)==set(nina.parts)
    print('Hero rig regions and joint metadata: OK')
    from lasttrain.animation import FrameClip
    clip=FrameClip(ROOT/'assets'/'props'/'winch-cycle-v32.png',components=True,height=55,reference_height=343)
    assert len(clip.frames)==8
    print('Winch: 8 complete prop phases OK')
    clip=FrameClip(ROOT/'assets'/'characters'/'artem-winch-pair-v32.png',2,4,components=True,height=68,anchor_x=.66)
    assert len(clip.frames)==8
    print('Artem with winch: 8 complete paired poses OK')
    clip=FrameClip(ROOT/'assets'/'characters'/'nina-brace-v32.png',1,1,components=True,height=96)
    assert len(clip.frames)==1
    print('Nina bracing the cable: complete whole-body pose OK')
    for name,columns,rows,components in [('runner-move-v31.png',4,2,False),('runner-action-v31.png',2,2,True),('brute-walk-v31.png',4,2,True)]+[('brute-attack-'+view+'-v31.png',2 if view=='side' else 4,2 if view=='side' else 1,True) for view in ('front','back','side')]:
        clip=FrameClip(ROOT/'assets'/'characters'/name,columns,rows,components=components)
        assert len(clip.frames)==columns*rows
        print(f'{name}: {len(clip.frames)} complete poses OK')
    pg.quit()

if __name__=='__main__':main()
