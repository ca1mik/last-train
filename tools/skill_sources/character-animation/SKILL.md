---
name: character-animation
description: "Author and polish game character idle, locomotion, jump, attack and interaction animation in skeletal or frame-based pipelines. Use for clip timing, transitions, clothing motion and movement readability; use rigging skill for skeleton repair."
---

# Character Animation

## Shared project contract

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

## Tools
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
