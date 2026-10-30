# Assets of the native 2.5D prototype

The original Man model and eleven base animations were downloaded from Quaternius's public CC0 listing at https://poly.pizza/m/HMnuH5geEG . Original binary: source_25d/quaternius/Man-CC0.glb, 493196 bytes. Download URL is recorded in LICENSES.txt.

tools/prepare_25d_model.py imports that binary in Blender 5.1.1, preserves its skeleton and skin weights, changes clothing materials, and adds skinned coat tails, scarf, satchel, strap and railway key. The worker and hooded enemy GLBs are adaptations of this original. The patient is the unadorned character with altered clothing colors. The beveled unit box is authored in Blender by the same script and is used to model the environment in metres. No other game's meshes, textures or screenshots are used in gameplay.

Animation processing at runtime: measured contact phases of the original walk and run loops are aligned, loops share a cycle clock, the right tool arm's swing is moderated, locomotion and upper-body actions blend in an AnimationTree. This is development animation and does not represent commissioned final performance capture.

Version 0.35 corrects the tool grip from wrist-origin placement to measured palm/finger landmarks. Source hand geometry and the corresponding bind chain are scaled together around the wrist (0.72), and a fixed grip is baked into the original action channels. The original 0.34 authored GLBs are preserved under source_25d/authored-v34. This retains the original CC0 rig/mesh topology; it is not a new final character model. Angular cuffs and other anatomy/clothing defects remain open.

Version 0.36 assigns the leg skin surfaces to the existing trouser material to match the established workwear specification. Version 0.35 binaries are preserved in source_25d/authored-v35. The patient stretcher, expanded level geometry, metric floor shader and analytic two-bone carry IK are authored in the project. No additional animation pack is claimed integrated. Static wrist-target checks are not final animation acceptance.

Sound files: selected files from Kenney Impact Sounds 1.0, CC0. The author's original License.txt is preserved as assets/audio/Kenney-CC0.txt. No continuous synthesized rain/noise bed is played.

Version 0.38 retargets selected animations from Quaternius Universal Animation
Library Standard (CC0), official page https://quaternius.com/packs/universalanimationlibrary.html
and distribution https://quaternius.itch.io/universal-animation-library . The
downloaded in-place UAL1_Standard.glb and original License.txt remain in
source_25d/ual-standard. The license is copied into
assets/characters/motion-v38/UAL-CC0.txt and the distribution's licenses folder.
tools/retarget_man_v038.py uses an explicit 63-to-31 bone map, world-space
rest corrections, analytic leg posing and a floor correction on visible skinned
geometry. Blender helper shapes are excluded. No base-character replacement,
new face, skin weights or limb scaling is introduced. Original worker.glb and
wraith.glb remain intact; runtime uses the motion-v38 copies.

UAL Idle, Walk, Sprint, Roll, Hit_Chest and Death01 feed the runtime. The Jog
candidate and Sword_Attack are retained for comparison but are not selected
for runtime locomotion or the melee strike. The original authored Man attack
remains until its timing and contact receive separate review. Animation, coat
deformation, tool contact and artistic acceptance still have open requirements.

Station layout, native prop geometry, lighting, procedural spatial shaders, UI and gameplay code are authored in this project. Rendering uses Godot 4.7.2. Godot MIT and third-party notices are supplied alongside the Windows executable.

References in design/references are official promotional screenshots of Death's Door and Hades, stored outside this project for visual comparison only. They are excluded from export. Kenney Survivors was downloaded for comparison but none of its character models or textures is included in this prototype.

Several original Google Drive downloads returned quota-error HTML instead of models. Those files were rejected and moved to source_25d/rejected-downloads with .html suffixes; they are neither assets nor license evidence.
# Дополнение 0.44, 18.10.2026

Окружение `scripts/environment_kit.gd`, сцены forest/wasteland/locations и
шейдеры foliage/path_ground написаны для проекта. Они используют базовые
Godot-меши и ранее существующий собственный beveled-box. Новых сторонних
паков, текстур, музыки или персонажных моделей в этом срезе нет. Авторские
материалы процедурные; движение листьев происходит в настоящей 3D-сцене.

0.45: пауза/журнал, аудиошины/предпочтения и исправления gameplay — собственный
Godot-код проекта. Новых сторонних изображений, моделей или голосовых записей
нет. Режим preview освобождает аудиоплееры и ждёт декодер перед завершением.

0.46-dev: вагон/приём и обстановка убежища в hospital_reception.gd — собственные
Godot-примитивы/материалы. Patient.glb используется прежний, как Михаил; положение
над матрасом исправлено после GPU-просмотра. Новых третьесторонних ассетов нет.

