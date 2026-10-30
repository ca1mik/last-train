---
name: character-consistency
description: "Preserve the identity of an existing game character across poses, views, sprite frames and asset revisions. Use for reference matching, drift reviews and multi-view consistency; not for inventing a new art direction."
---

# Character Consistency

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
