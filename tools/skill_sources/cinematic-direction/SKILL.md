---
name: cinematic-direction
description: "Stage game cutscenes, dialogue gestures and camera beats with sound and gameplay handoff. Use for storyboard, shot blocking and runtime cinematic direction; not for changing a gameplay camera without reason."
---

# Cinematic Direction

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
