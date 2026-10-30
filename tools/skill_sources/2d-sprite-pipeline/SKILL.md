---
name: 2d-sprite-pipeline
description: "Prepare game-ready 2D sprites, frame sequences, atlases, pivots and engine imports. Use for raster character animation production or sprite export, including sprites rendered from 3D; not for native 3D character rigging."
---

# 2D Sprite Pipeline

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
