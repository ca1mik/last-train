"""Run evidence integrity checks, negative-input probes and persist audit scope."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release/capability-audit'
HELPER=ROOT/'tools/skill_sources/visual-qa/audit_evidence.py'
spec=importlib.util.spec_from_file_location('evidence_audit',HELPER)
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
files=list((OUT/'final/poses').glob('*.png'))+list((OUT/'blender').glob('*.png'))
files += [OUT/'final/scene/scene-25d.png',OUT/'motion.mp4']
files += list((ROOT/'game25d/assets/characters').glob('*.glb'))
files += [ROOT/'assets/characters/artem-jog-front-v28.png']
subprocess.run([sys.executable,str(HELPER),*[str(p) for p in files],
                '--output',str(OUT/'evidence-integrity.json')],check=True)
subprocess.run([sys.executable,str(HELPER),*[str(p) for p in (ROOT/'game25d/assets/characters').glob('*.glb')],
                '--output',str(OUT/'asset-inventory.json')],check=True)
negative=[]
with tempfile.TemporaryDirectory(prefix='game_evidence_probe_') as temporary:
    corrupt=bytearray((OUT/'final/poses/case-00-view-000.png').read_bytes())
    corrupt[29] ^= 1
    for name,data in [('corrupted.png',corrupt),('truncated.glb',(ROOT/'game25d/assets/characters/worker.glb').read_bytes()[:100])]:
        target=Path(temporary)/name;target.write_bytes(data)
        try:
            helper.inspect_file(target)
        except (ValueError, OSError) as error:
            negative.append({'case':name,'rejected':True,'reason':str(error)})
        else:
            raise AssertionError(f'Invalid file accepted: {name}')
(OUT/'negative-input-probes.json').write_text(json.dumps(negative,indent=2),encoding='utf-8')

manifest=json.loads((ROOT/'dist/LastTrain-0.35-25D/build-manifest.json').read_text(encoding='utf-8-sig'))
skill_validation=json.loads((OUT/'skills-validation.json').read_text(encoding='utf-8'))
for row in skill_validation:
    path=Path(row['path'])/'SKILL.md'
    row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
(OUT/'skills-validation.json').write_text(json.dumps(skill_validation,indent=2),encoding='utf-8')
locked=json.loads((ROOT/'tools/visual-qa/package-lock.json').read_text(encoding='utf-8'))
dependencies={name:{k:value.get(k) for k in ['version','resolved','integrity']}
              for name,value in locked['packages'].items() if name}
summary={'date':'2026-10-17','build':manifest,'specialized_skills':len(skill_validation),
         'official_skills_installed':['playwright','playwright-interactive'],
         'existing_system_skills':['imagegen','skill-creator'],
         'versions':{'Godot':'4.7.2','Blender':'5.1.1','Node':'24.14.0','Python':'3.12.10',
                     'Playwright':'1.64.1','Playwright CLI':'0.1.22','Chromium':'156.0.8078.4'},
         'native_pose_images':len(list((OUT/'final/poses').glob('*.png'))),
         'blender_views':len(list((OUT/'blender').glob('*.png'))),
         'gameplay':json.loads((OUT/'final/gameplay.json').read_text(encoding='utf-8')),
         'negative_input_probes':negative,'npm_dependencies':dependencies,
         'interactive_transport':'node_repl + node:module createRequire; direct ESM import failed',
         'mcp_search':'Plugin Management search Blender Playwright Godot returned zero plugins; no direct such MCP tools available',
         'imagegen':'Built-in tool and system skill available; no new generation executed in this audit',
         'three_r3f':'Not installed: native Godot is the current stack',
         'visual_quality':'not accepted; see design/visual-defects-2026-10-17.md',
         'release_ready':False,'human_playtest':False,
         'limits':['Pose fixture does not prove locomotion contacts','Full scenario and duration not implemented or tested',
                   'Angular wrist/cuff topology remains','7 Texture RID leak warning on scene shutdown',
                   'CLI has official transitive alpha Playwright dependency, pinned in lockfile; stable Chromium explicitly configured',
                   'No voice/lip-sync or fresh imagegen output claimed']}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({'skills':len(skill_validation),'native_poses':summary['native_pose_images'],
                  'negative_probes':len(negative),'release_ready':False}))
