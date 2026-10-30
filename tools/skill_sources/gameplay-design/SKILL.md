---
name: gameplay-design
description: "Design and integrate game loops, combat, interactions, NPC states, quests and progression. Use for mechanics and state-machine work connected to player goals; use game-feel for response polish."
---

# Gameplay Design

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
Use actual engine scripts, input/collision APIs, deterministic fixtures and an
input-driven runtime pass. Inspect the project before adding dependencies.

## Procedure
1. State the desired player decision and current implemented behaviour. Diagram
   the core loop, resources and success/failure/recovery conditions.
2. Define state transitions with guards, entry/exit effects, ownership, event
   order, persistence and cancellation. Distinguish visual pose from gameplay
   state; ensure timers and animation events share a deliberate timing model.
3. Prototype the smallest complete interaction using existing architecture.
   Preserve inputs, saves and related mechanics. Implement feedback and failure
   recovery, not only a happy-path flag change.
4. Test collision cones, range, invulnerability, repeated inputs, exhaustion,
   NPC navigation and interrupts. Enemy attacks need readable local telegraphs;
   debug lines are not default combat art.
5. Exercise a complete goal with normal controls. Stage fixtures explicitly;
   internal state mutation is not an input-driven playthrough. Re-test linked
   mechanics after changes, including checkpoint/restart and paused states.
6. Compare player choices and pacing against the design intention; remove
   redundant mandatory actions before adding complexity or difficulty.

## Acceptance
Playable evidence shows the complete implemented loop with consequences and
recovery. Tests verify meaningful behaviour rather than mirroring code. Do not
claim a campaign or evacuation exists because its future state names do.
