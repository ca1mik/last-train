---
name: character-rigging-animation
description: "Build, inspect or retarget character skeletons, skinning, IK constraints and animation blends for games. Use for rig deformation, bind-pose mismatch, root motion or skeletal transitions; use character-animation for overall clip production."
---

# Character Rigging and Animation

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
