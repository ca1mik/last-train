---
name: 2-5d-character-pipeline
description: "Integrate characters into a real 2.5D game scene with camera projection, world scale, depth, lighting, occlusion and contact. Use for orthographic 3D or explicitly chosen sprite-in-3D pipelines; not CSS depth effects."
---

# 2.5D Character Pipeline

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
