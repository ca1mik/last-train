---
name: environment-design
description: "Build coherent game environments, props, materials and lighting while preserving playable routes. Use for scene art, world scale, depth, atmosphere and optimization; use level-design for initial route planning."
---

# Environment Design

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
