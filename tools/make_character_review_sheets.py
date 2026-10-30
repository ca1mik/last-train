"""QA-only crops/contact sheets from genuine rendered screenshots, not game assets."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release/capability-audit'
for case, name in [(0,'idle'),(3,'attack')]:
    sheet=Image.new('RGB',(1680,900),'#263239')
    draw=ImageDraw.Draw(sheet)
    for i in range(8):
        path=OUT/'grip-close'/f'case-{case:02d}-view-{i*45:03d}.png'
        with Image.open(path) as image:
            tile=image.crop((350,0,1250,900)).resize((420,420),Image.Resampling.LANCZOS)
        x=(i%4)*420;y=(i//4)*450
        sheet.paste(tile,(x,y+26));draw.text((x+12,y+6),f'{name} / {i*45} deg',fill='white')
    sheet.save(OUT/f'grip-{name}-8views.jpg',quality=94)
print('QA contact sheets: idle and attack, 8 actual rendered directions each')
