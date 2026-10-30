"""Install project-authored game skills using the official skill-creator initializer.

Sources live in tools/skill_sources. Never overwrite an unrelated installed skill.
"""
import json
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = Path.home() / '.codex' / 'skills'
CREATOR = SKILLS / '.system' / 'skill-creator' / 'scripts'

COMMON = '''## Shared project contract

Find the project root and read its AGENTS.md. Read the relevant sections of
GAME_DESIGN_DOCUMENT.md, NARRATIVE_BIBLE.md, ART_STYLE_GUIDE.md,
CHARACTER_BIBLE.md, LEVEL_DESIGN_GUIDE.md, ANIMATION_GUIDE.md and ASSET_REGISTRY.md.
These names are a project convention, not guaranteed files: discover existing
equivalents first; document missing inputs rather than inventing their contents.
Distinguish implemented facts, user decisions, proposals, and verified results.
Retain reference provenance and approval status. A draft or a purchased pack is
not an approved design. Preserve working mechanics and archive superseded assets.
For canon or appearance changes that require approval, prepare a concrete proposal
and continue independent work; never infer approval from elapsed time.
Use actual available APIs after checking installed versions. A skill is workflow
instructions, not an installed model, engine, MCP server or quality guarantee.
Report what ran, which artifacts were inspected, defects, and untested scope.

'''

SPECS = {
'character-design': (
 'Design game character anatomy, proportions, silhouettes and reference sheets for 2D, 2.5D or stylized 3D. Use for creating or revising appearance specifications; use animation skills for motion implementation.',
 'Character Design', 'Character proportions and reference specifications',
 '''## Tools
Use the existing engine, imagegen for raster concepts, and Blender bpy for native
models when available. Open local references before describing or editing them.

## Procedure
1. Inventory actual character assets, story facts, camera projection, runtime
   scale and approved references. Separate concept art from game-ready geometry.
2. Write a versioned character specification: ID, age/role, body landmarks,
   silhouette, head/body ratio, shoulder/hip widths, garment construction,
   palette/materials, footwear, handedness, accessories and asymmetry. Do not
   impose one anatomical ratio on every style; measure the selected reference.
3. Record identity invariants and approval evidence. Mark unresolved details as
   draft. Match the established style; propose a replacement only for a stated
   defect. Get explicit approval before changing established appearance/canon.
4. Produce front/back/side/three-quarter references at one scale and camera.
   For raster work use imagegen with explicit reference roles and invariants;
   inspect every output. Generated sheets are candidates, not exact animation.
5. Check in the actual game camera at native size and enlarged crops. Compare
   actor with doors, benches, tools, NPCs and floor contacts. Check light/dark
   backgrounds, silhouette recognition and deformation in extreme poses.

## Acceptance
No cropped extremities, accidental body-length changes or unapproved identity
changes. Character is recognizable at gameplay size. Specification includes
source paths and approval state; mesh/sprite is not called final before render
inspection. Hand off invariants to character-consistency and motion requirements
to character-animation / character-rigging-animation.
'''),
'character-consistency': (
 'Preserve the identity of an existing game character across poses, views, sprite frames and asset revisions. Use for reference matching, drift reviews and multi-view consistency; not for inventing a new art direction.',
 'Character Consistency', 'Preserve identity across views and animation frames',
 '''## Tools
Use imagegen for referenced raster edits, the engine for rendered poses, and
Blender for geometry measurements. Inspect local images before editing.

## Procedure
1. Select the approved master version from CHARACTER_BIBLE and ASSET_REGISTRY;
   record its hash, approval evidence and material/accessory identities.
2. Build a comparison matrix: face/hair, body landmarks, garment seams/length,
   palette, tool hand, bag side, scale and camera. Record each as fixed or allowed
   to vary. Lighting variation is not a new clothing colour.
3. Prefer one rig/model for multi-view 3D; for generated raster variants feed
   the master as a reference and request only the intended change. Do not mirror
   asymmetric characters without correcting tool, strap and bag sides.
4. Compare front/back/side/diagonals and contact/extreme frames at equal scale.
   Check occluded accessories as well as visible ones; rotation cannot move a
   bag to the other hip. Use neutral-light renders plus game-light renders.
5. Fix the smallest divergent feature, repeat the same comparisons, and register
   the new version without overwriting the master before acceptance.

## Acceptance
Attach reviewed comparison images and a per-invariant pass/fail/unknown record.
Pixel differences alone cannot prove identity because poses and lights change.
If there is no approved master, say so and use a labelled provisional baseline.
'''),
'2d-sprite-pipeline': (
 'Prepare game-ready 2D sprites, frame sequences, atlases, pivots and engine imports. Use for raster character animation production or sprite export, including sprites rendered from 3D; not for native 3D character rigging.',
 '2D Sprite Pipeline', 'Sprites, pivots, atlases and frame sequence checks',
 '''## Tools
Use imagegen for raster creation/edits, a verified existing atlas tool or engine
importer for packing, and Blender for renders from a rig. Do not install an
unverified packer or substitute code-drawn primitives for finished characters.

## Procedure
1. Read the character master and determine target on-screen pixel height,
   resolution, filtering, colour space, alpha convention and camera direction.
2. Define a manifest before export: character/version, directions, clip names,
   frame order, per-frame duration, loop flag, foot/root pivot in a common
   untrimmed canvas, trim offsets, hurtboxes and event times.
3. Use a coherent rig or authored key poses for loops. Do not assume independently
   generated figures form an animation. Inspect contact, passing, extremes,
   loop seam and changes in garment/accessory volume before atlas packing.
4. Export non-overlapping frames with transparent padding and appropriate
   extrusion for filtering. Keep original canvases and pivots; trimming must
   preserve offsets. Never stretch an entire character to fill a cell.
5. Import using the real engine. Check alpha fringes on light/dark backgrounds,
   atlas bleeding at zoom levels, intended filter, uniform scale and pivot.
6. Play all directions at intended speed, including idle/walk/run/attack
   transitions. Capture a temporal strip and gameplay footage, not just an atlas.

## Acceptance
Validate frame count/order/dimensions and decoded alpha; no overlap, crop, pivot
jitter, visible loop pop or asymmetric mirroring error. A 2D sheet is not a 3D
asset. State unsupported directions/clips and the actual import/render evidence.
'''),
'2-5d-character-pipeline': (
 'Integrate characters into a real 2.5D game scene with camera projection, world scale, depth, lighting, occlusion and contact. Use for orthographic 3D or explicitly chosen sprite-in-3D pipelines; not CSS depth effects.',
 '2.5D Character Pipeline', 'Camera, depth, scale and character scene integration',
 '''## Tools
Use the project's actual 3D engine and Blender bpy for model work. For Godot,
inspect Camera3D, Node3D, Skeleton3D and AnimationTree in the installed version.
Use Three.js / React Three Fiber only for an existing compatible web stack.

## Procedure
1. Establish whether assets are native meshes, prerendered sprites, or billboard
   sprites. Preserve the chosen method; document projection, camera basis,
   orthographic size/FOV, axes, units, floor height and depth ordering.
2. Measure imported bounds and transforms. Normalize metres exactly once at
   a documented boundary. Compare human, door, stairs, bench and collision shape.
   Keep visual root/feet aligned; do not mask errors by per-room rescaling.
3. Match world lights, material response, shadows and floor contacts. For sprite
   billboards specify normal/shadow limitations rather than claiming mesh-like
   lighting. Check near/far depths, front/back and all diagonals in-scene.
4. Test occlusion using the actual projection. Orthographic rays are parallel;
   a ray from the camera origin is not equivalent. Render-only lintels and signs
   can obstruct a character even without colliders. Preserve collision when
   fading occluders. Test ceilings, pillars, translucent edges and combat crowds.
5. Put physics and pose clocks on a deliberate timing model; use interpolated
   transforms for a following render camera. Test fixed and following cameras,
   direction changes, slope/step contacts, hit reactions and pause/resume.

## Acceptance
Inspect real GPU frames at actual viewport dimensions and gameplay-size crops.
No hidden actor, scale drift, floor penetration, detached shadows, perspective
mismatch or camera-induced jitter. Record hardware/runtime and any renderer
warnings; a headless logic test is not visual evidence.
'''),
'character-rigging-animation': (
 'Build, inspect or retarget character skeletons, skinning, IK constraints and animation blends for games. Use for rig deformation, bind-pose mismatch, root motion or skeletal transitions; use character-animation for overall clip production.',
 'Character Rigging and Animation', 'Skeletons, skinning, retargeting and contact controls',
 '''## Tools
Use Blender's installed bpy in its own executable and the target engine's
skeleton/animation APIs. Check versioned documentation before calls; do not
assume APIs from older Blender/Godot versions or invent a Blender MCP.

## Procedure
1. Inspect skeleton hierarchy, rest matrices, armature/world scale, axes, units,
   skin groups, inverse bind matrices, material paths and available actions.
   Equal bone names do not establish equal bind poses or retarget compatibility.
2. Store an explicit source-to-target bone map and rest-pose correction. Test
   T/rest pose, shoulder elevation, elbow/knee extremes, wrists and ankles before
   batch retargeting. Preserve bone lengths; avoid compensating with scale keys.
3. Choose in-place or root motion per clip. Document which component moves the
   body; never apply both clip translation and controller travel unintentionally.
4. Define IK contacts in the correct space and blend their influence. Keep
   reach within limb length, pole direction stable and knee bends intentional.
   Check hands on tools/trolleys and feet on changing terrain. Export/bake only
   supported results; Blender constraints are not automatically runtime IK.
5. Align walk/run contact phases, tune cadence from world speed and measured
   stride. Use appropriate upper-body masks, action restart/exit rules and a
   single deliberate clock. Inspect turns, interrupts, death and pause/resume.
6. Export non-destructively; reimport into the engine and sample the actual
   runtime skeleton. Check missing tracks, bind offsets and accessory weights.

## Acceptance
Report contact slip, mesh penetration and discontinuities with sample timing and
world scale. Render extreme poses and transition footage. No static-pose-only
signoff, no claim that available clip names prove good motion. Scan Blender logs
for Python tracebacks even when its process exit code is zero.
'''),
'character-animation': (
 'Author and polish game character idle, locomotion, jump, attack and interaction animation in skeletal or frame-based pipelines. Use for clip timing, transitions, clothing motion and movement readability; use rigging skill for skeleton repair.',
 'Character Animation', 'Readable motion, transitions and secondary animation',
 '''## Tools
Use the existing engine's playback/capture, Blender for skeletal authoring, and
the 2d-sprite-pipeline for frame export. Use imagegen for art candidates only;
generated pose sheets do not establish temporal coherence.

## Procedure
1. Inventory actual clips and gameplay states. Make a coverage table for idle,
   walk, run, jump if used, attack, dodge, hurt, death, interact and recovery.
   Record missing clips explicitly; an accelerated run is not a roll animation.
2. Define contact/key poses, anticipation, active/recovery timings, event markers
   and cancellation rules. Place gameplay hit events at observed weapon contact.
   Preserve responsiveness; do not add long anticipation to every player action.
3. Establish phase, stride and loop seams before blending. Match cadence to
   measured travel. Keep gait support believable and prevent excessive vertical
   bounce, locked arms, sliding feet or snapped facing changes.
4. Add restrained follow-through to clothes/hair/straps with stable attachments.
   Test accessory collisions and avoid simulation noise at gameplay distance.
5. Test start/stop, 180-degree turn, diagonal, repeated attacks, movement attack,
   dodge cancel, hurt, death, pause/resume and low/render-frame-rate variants.
6. Review fixed-camera and following-camera videos at normal speed, then slow
   motion and consecutive frames. Still-frame contact sheets supplement motion.

## Acceptance
No visible pops, body-volume changes, phase jumps or planted-foot skating beyond
the project's declared tolerance. Check death through the final pose, not its
first half. Separate source-animation defects from controller/camera defects.
Record observed remaining defects and do not call motion polished by test count.
'''),
'level-design': (
 'Design, block out and validate playable game levels with routes, encounters, exploration and pacing. Use for location layout, meaningful duration, alternate paths, collision and navigation; not environment decoration alone.',
 'Level Design', 'Playable routes, encounter pacing and traversal checks',
 '''## Tools
Use the actual engine's collision/navigation tools, map inspection and input-driven
playthrough capture. Graybox primitives are valid for layout, not final characters.

## Procedure
1. Read the implemented mission states and existing geometry. Define the player's
   objective, meaningful actions, entry/exit conditions and expected route.
2. Draw a route graph with optional branches and visible landmarks. For each
   sector specify encounter purpose, alternatives, resources, safe space,
   interaction, checkpoint and changed return route. Avoid repeated empty rooms.
3. Block out at the engine's real metre/pixel scale first. Test player/enemy
   clearance, dodge travel, door widths, camera occlusion and navigation before
   adding dressing. Test both forward and escort/evacuation return directions.
4. Tie locks and shortcuts to observable causes. Check no softlock after resource
   depletion, enemy death, return traversal, save/load or abandoning an interaction.
5. Measure movement, combat, exploration and dialogue time separately. A bot
   shortest-path run is not first-play duration; a target is not a measurement.
   Use a human first-play when claiming player duration. Do not extend time by
   slow walking, long holds, health inflation or filler waves.
6. Add environment dressing only after route validation, then repeat collisions,
   readability, timing and altered-state traversal. Hand off to visual-qa.

## Acceptance
Show the route graph, actual playable states, completion trace and known gaps.
Prove entry-to-exit reachability with ordinary controls. Goals, durations and
future sectors remain proposals until implemented and tested.
'''),
'environment-design': (
 'Build coherent game environments, props, materials and lighting while preserving playable routes. Use for scene art, world scale, depth, atmosphere and optimization; use level-design for initial route planning.',
 'Environment Design', 'Cohesive spaces, materials, lighting and readable depth',
 '''## Tools
Use the project engine, Blender for native meshes, imagegen for texture/concept
work, and engine profiling. Preserve provenance for imported packs and textures.

## Procedure
1. Read the validated level blockout and ART_STYLE_GUIDE. Identify landmarks,
   foreground/midground/background, navigable surfaces and visual focal points.
2. Set a metric kit: doors, steps, rails, furniture, props and texture density.
   Use repeatable modules but break obvious repetition with meaningful wear and
   composition. Do not replace required finished character art with primitives.
3. Separate materials by response, not only colour. Check metal roughness,
   fabric matte response, concrete grain and water reflection at gameplay angle.
   Inspect imported texture URIs, UV scale, normals and material colour space.
4. Light player/enemy silhouettes and usable exits. Compare neutral-light asset
   review with actual warm/cool scene lighting. Avoid hiding poor shapes in fog.
5. Add restrained atmosphere with real scene depth and correct layering. No CSS
   depth substitutes. Particles, water, sway and flicker must not obscure combat
   or create irritating noise/flash loops. Distinguish art from gameplay effects.
6. Re-test all routes/collisions and camera occlusion after dressing. Profile
   representative dense combat, shadows, transparency and asset memory.

## Acceptance
Actual renders demonstrate coherent scale, contact shadows, readable paths and
materials. No z-fighting, floating props or decorative collision traps. Record
hardware/viewport/performance conditions; avoid unsupported universal FPS claims.
'''),
'narrative-design': (
 'Develop game story, character arcs, dialogue and branching events tied to player actions. Use for scenario writing and narrative integration; preserve existing canon and use narrative-qa to validate state reachability.',
 'Narrative Design', 'Character arcs and story delivered through player actions',
 '''## Tools
Read actual scenario/data files and quest code. Use existing data formats and
engine event systems; a new narrative framework is not required by default.

## Procedure
1. Build a fact ledger from NARRATIVE_BIBLE and source: dates/ages, relationships,
   living status, motivations, locations and knowledge per character. Cite files.
   Resolve conflicts by evidence; label interpretation and proposals separately.
2. Define conflict, playable objective and consequence per beat. Attach each beat
   to an actual mechanic or planned state transition; avoid making an action game
   into long mandatory dialogue panels to explain every event.
3. Track what each character knows, wants and refuses. Write distinct voices
   with subtext and concrete actions, preserving chronology and motivations.
4. Specify event ID, prerequisites, actor presence, start/end state, repeat policy,
   interruption behaviour and save persistence. Choices need visible consequences;
   do not introduce hidden punishment or canon twists without authorization.
5. Provide branch/act structure, critical path, optional content and reconvergence.
   Separate implemented scenes from scripts that have not reached the new engine.
6. Prototype one beat in-game, review pacing alongside movement/combat, then
   hand off event coverage and unresolved questions to narrative-qa.

## Acceptance
Every required beat has a playable trigger or is explicitly future work. No
unapproved retcon, impossible simultaneous presence, knowledge leak or unearned
resolution. Proposed script text alone is not implemented narrative content.
'''),
'cinematic-direction': (
 'Stage game cutscenes, dialogue gestures and camera beats with sound and gameplay handoff. Use for storyboard, shot blocking and runtime cinematic direction; not for changing a gameplay camera without reason.',
 'Cinematic Direction', 'Shots, gestures, sound cues and gameplay handoffs',
 '''## Tools
Use the current engine's camera/timeline/animation/audio systems and capture.
Blender can author poses; imagegen can explore storyboard frames, not replace
runtime staging. Inspect actual available actor clips before promising gestures.

## Procedure
1. Read the narrative beat and camera/art constraints. State the emotional and
   gameplay purpose, duration target, player control and skip policy.
2. Make a shot/beat list with camera transform/projection, subjects, eye lines,
   blocking, gesture, sound cue and event trigger. Preserve spatial orientation.
3. Block in-scene using actual character models. Check hand contacts, gaze,
   facial/gesture readability at final scale and actor/world collisions.
4. Synchronize cues with observed animation events. Use real audio durations;
   do not claim lip-sync or voice acting if no such asset exists.
5. Restore camera/control/AI/audio deterministically after end, skip, interruption,
   pause, death and reload. World/quest effects must occur exactly once.
6. Capture complete playback and a skipped path; inspect transition frames,
   camera cuts, occlusion, clipping, subtitles and player reacquisition of control.

## Acceptance
No unsupported shot/voice promises, snap to wrong player position, duplicated
quest effects or input lock. Keep action-game scenes concise and justified.
If nothing is implemented, deliver a labelled storyboard and an integration plan.
'''),
'gameplay-design': (
 'Design and integrate game loops, combat, interactions, NPC states, quests and progression. Use for mechanics and state-machine work connected to player goals; use game-feel for response polish.',
 'Gameplay Design', 'Mechanics, world states, combat and quest integration',
 '''## Tools
Use actual engine scripts, input/collision APIs, deterministic fixtures and an
input-driven runtime pass. Inspect the project before adding dependencies.

## Procedure
1. State the desired player decision and current implemented behaviour. Diagram
   the core loop, resources and success/failure/recovery conditions.
2. Define state transitions with guards, entry/exit effects, ownership, event
   order, persistence and cancellation. Distinguish visual pose from gameplay
   state; ensure timers and animation events share a deliberate timing model.
3. Prototype the smallest complete interaction using existing architecture.
   Preserve inputs, saves and related mechanics. Implement feedback and failure
   recovery, not only a happy-path flag change.
4. Test collision cones, range, invulnerability, repeated inputs, exhaustion,
   NPC navigation and interrupts. Enemy attacks need readable local telegraphs;
   debug lines are not default combat art.
5. Exercise a complete goal with normal controls. Stage fixtures explicitly;
   internal state mutation is not an input-driven playthrough. Re-test linked
   mechanics after changes, including checkpoint/restart and paused states.
6. Compare player choices and pacing against the design intention; remove
   redundant mandatory actions before adding complexity or difficulty.

## Acceptance
Playable evidence shows the complete implemented loop with consequences and
recovery. Tests verify meaningful behaviour rather than mirroring code. Do not
claim a campaign or evacuation exists because its future state names do.
'''),
'game-feel': (
 'Polish control response, movement, impact feedback, camera and sound in a playable game. Use for jerky movement, weak hits, excessive shake or noisy effects; not for adding arbitrary particles to hide missing animation.',
 'Game Feel', 'Responsive controls, stable motion and readable feedback',
 '''## Tools
Use engine frame timing/capture, animation playback, actual input and audio
recording/metering. A waveform does not establish pleasant sound; listen when
audio playback tools are actually available and disclose when not.

## Procedure
1. Reproduce a specific visible/audible complaint. Separate source animation,
   controller velocity, camera interpolation, collision, frame pacing and sound.
2. Measure input-to-action rules, acceleration/braking, turn speed, attack
   contact/recovery, dodge distance/cooldown and damage timing before tuning.
3. Change one causal group at a time. Match feet to travel and impacts to contact.
   Preserve player agency with intentional buffering/cancel windows.
4. Add brief, readable local hit feedback. Hit stop/shake/squash are optional,
   not mandatory: do not freeze the whole world on every hit or distort a fixed
   anatomical style. Include reduced-motion options if strong effects are used.
5. Check sound levels, clipping, loops, distance attenuation and active listener.
   Do not reintroduce continuous hiss to simulate atmosphere. Test real mixes
   with simultaneous footsteps, combat, environment and dialogue.
6. Compare normal-speed fixed/following-camera footage, repeated inputs,
   diagonal turns, crowded combat and pause/resume. Recheck at relevant rates.

## Acceptance
Observed response matches timing, visual contact and feedback. No camera judder,
repeated knockback accumulation, global hit freeze or masking effects. Record
actual remaining motion/audio defects; subjective feel needs direct play review.
'''),
'visual-qa': (
 'Verify actual game renders, character poses, animations, scene readability and visual regressions with captured evidence. Use after graphics or motion changes and before visual completion claims; headless logic tests alone do not qualify.',
 'Visual QA', 'Real render evidence, animation review and visual regressions',
 '''## Tools
Use native engine GPU capture for native games; Playwright for browser/Electron
surfaces and review reports. Playwright cannot directly control native Godot.
Use Blender render for asset inspection and ffprobe/FFmpeg for temporal evidence.
The bundled scripts/audit_evidence.py checks PNG/video metadata and hashes without
altering assets; run --help first. Image metadata cannot prove aesthetic quality.

## Procedure
1. Write a claim-to-check matrix before capture: user complaints, changed
   features, relevant controls/states and expected completion claims. Choose
   actual model/scene versions, cameras, lighting, resolutions and timestamps.
2. Run resource/code checks, then render on the actual GPU/runtime. Record
   renderer, executable version, viewport dimensions, FPS and asset hashes.
   Requested window size can differ from captured size; verify image dimensions.
3. Capture front/back/sides/diagonals, neutral light and scene light; include
   close-up AND gameplay size. Reset actor state between diagnostic poses.
   Stop locomotion for standing attacks and sample death through its final pose.
4. For motion capture idle/start/walk/run/stop, 180-turn, diagonals, repeated and
   moving attacks, dodge, hurt, death and pause/resume. Review normal-speed motion
   plus consecutive transition frames; 0.5-second sampling misses jerks.
5. Inspect identity, scale, skin deformation, foot contacts, tool/accessory
   attachments, alpha edges, clipping, z-fighting, shadows, occlusion, UI fit and
   camera stability. Check small window, dense combat and obstructed corners.
6. Separate fixture-staged screenshots from ordinary-input playthroughs. Verify
   interactions/collisions and linked regression checks, including failure paths.
7. Record defects with severity, artifact/timestamp, expected/observed result,
   owner and fix. Fix defects within the authorized change; rerun the same case
   and linked regressions. Keep unresolved art decisions visible, not auto-passed.

## Acceptance
Maintain separate statuses for technical capture, visual inspection, motion,
interaction, human playtest and release readiness. Numeric checks/diffs support
inspection; they never certify appeal, identity or fun. Do not use an old
screenshot to certify changed assets. No completion claim for an unrendered
visual change. An infrastructure task may finish with explicitly failed game
quality findings; that does not mean the game or art was accepted.
'''),
'narrative-qa': (
 'Audit game canon, dialogue, event order, branch reachability and quest completion against actual source and runtime states. Use for contradictions, duplicate characters, broken triggers and incomplete scenario migrations.',
 'Narrative QA', 'Canon, event prerequisites and quest branch verification',
 '''## Tools
Use existing scenario data/code, state traces, saves and engine runtime tests.
Do not invent a narrative parser or claim every branch was tested from a grep.

## Procedure
1. Extract facts and proposed facts separately. Build chronology (dates, ages,
   travel time), relationships, knowledge and character-presence tables with
   source locations. Preserve explicit user canon and approved amendments.
2. Inventory real event/quest IDs, guards, effects, one-shot flags and persistence.
   Detect missing targets, impossible prerequisites and effects that never run.
3. Map branches and reconvergence. For each critical outcome list an initial save,
   ordinary-input route, expected event order and observable final world state.
4. Test interruption, repeat, reload, optional-content omission and reverse order.
   Check resource exhaustion/actor death cannot strand mandatory rescue goals.
5. Check simultaneous presence, item ownership and dialogue knowledge against
   world state. A radio line is not proof its speaker is physically spawned.
6. Compare described campaign with the active engine. Mark legacy-only chapters,
   proposed quests, implemented but untested branches and tested outcomes.

## Acceptance
Return an evidence ledger with pass/fail/unknown per branch/fact and reproducible
defects. Search/static checks find candidates; runtime traces establish behaviour.
Never label a found-patient objective as completed evacuation without boarding
evidence. Leave unreachable/unimplemented narrative content clearly open.
'''),
'art-direction': (
 'Establish and maintain a game style bible, references, palette, proportions, material language and visual acceptance. Use for coherent art direction and cross-asset review; do not silently replace an established style.',
 'Art Direction', 'Shared style bible and cross-asset visual coherence',
 '''## Tools
Use inspected project references, native engine renders, Blender and imagegen
as appropriate. Promotional references are comparison material, not reusable
game assets. Check actual licenses before incorporating external content.

## Procedure
1. Inventory the selected direction, user feedback, existing asset families and
   previous rejected approaches. Distinguish approved intent from unapproved
   visual execution and available-but-unselected downloaded packs.
2. Write ART_STYLE_GUIDE with reference roles, camera/projection, silhouette,
   proportions, value hierarchy, palette, material roughness, texture treatment,
   lighting and effects. Use measurements and annotated real images over slogans.
3. Define acceptance for characters, animation and locations at game size. Set
   explicit exceptions and version/approval state. Do not introduce stylistic
   changes merely because a tool can generate a different attractive picture.
4. Review a representative character, prop and scene together under neutral
   and actual lighting. Identify mismatched shape language, density or contrast.
5. Resolve the largest perceptual defect first, request a concrete approval for
   canon/appearance changes, then propagate approved decisions to character and
   asset bibles. Keep original masters and provenance.
6. Hand off an actionable defect list to relevant production skills and visual-qa.

## Acceptance
The guide points to actual reference paths and tested renders, not imagined
assets. State what is approved, provisional, rejected and still missing. A style
bible is a control document; final visual acceptance requires the rendered work.
''')
}

def main():
    manifest = []
    for name, (description, display, short, body) in SPECS.items():
        source = ROOT / 'tools' / 'skill_sources' / name
        installed = SKILLS / name
        source.mkdir(parents=True, exist_ok=True)
        content = f'---\nname: {name}\ndescription: {json.dumps(description)}\n---\n\n# {display}\n\n' + COMMON + body
        (source / 'SKILL.md').write_text(content, encoding='utf-8')
        if not installed.exists():
            subprocess.run([sys.executable, str(CREATOR / 'init_skill.py'), name,
                            '--path', str(SKILLS), '--interface', f'display_name={display}',
                            '--interface', f'short_description={short}', '--interface',
                            f'default_prompt=Use ${name} to review and improve the existing game project with actual evidence.'],
                           check=True, capture_output=True, text=True)
        else:
            previous = (installed / 'SKILL.md').read_text(encoding='utf-8')
            if 'Shared project contract' not in previous:
                raise RuntimeError(f'Refusing to replace unrelated skill: {installed}')
        (installed / 'SKILL.md').write_text(content, encoding='utf-8')
        for helper in source.glob('*.py'):
            (installed / 'scripts').mkdir(exist_ok=True)
            shutil.copy2(helper, installed / 'scripts' / helper.name)
        result = subprocess.run([sys.executable, str(CREATOR / 'quick_validate.py'), str(installed)],
                                capture_output=True, text=True)
        manifest.append({'name': name, 'path': str(installed), 'source': str(source),
                         'validation_exit': result.returncode, 'validation': result.stdout.strip()})
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
    report = ROOT / 'release' / 'capability-audit'
    report.mkdir(parents=True, exist_ok=True)
    (report / 'skills-validation.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'created': len(manifest), 'validated': len(manifest), 'report': str(report)}, indent=2))

if __name__ == '__main__':
    main()
