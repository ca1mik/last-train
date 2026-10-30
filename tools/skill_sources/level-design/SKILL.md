---
name: level-design
description: "Design, block out and validate playable game levels with routes, encounters, exploration and pacing. Use for location layout, meaningful duration, alternate paths, collision and navigation; not environment decoration alone."
---

# Level Design

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
