---
name: character-design
description: "Design game character anatomy, proportions, silhouettes and reference sheets for 2D, 2.5D or stylized 3D. Use for creating or revising appearance specifications; use animation skills for motion implementation."
---

# Character Design

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
