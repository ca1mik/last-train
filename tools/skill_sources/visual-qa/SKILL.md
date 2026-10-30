---
name: visual-qa
description: "Verify actual game renders, character poses, animations, scene readability and visual regressions with captured evidence. Use after graphics or motion changes and before visual completion claims; headless logic tests alone do not qualify."
---

# Visual QA

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
