---
name: narrative-qa
description: "Audit game canon, dialogue, event order, branch reachability and quest completion against actual source and runtime states. Use for contradictions, duplicate characters, broken triggers and incomplete scenario migrations."
---

# Narrative QA

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
Use existing scenario data/code, state traces, saves and engine runtime tests.
Do not invent a narrative parser or claim every branch was tested from a grep.

## Procedure
1. Extract facts and proposed facts separately. Build chronology (dates, ages,
   travel time), relationships, knowledge and character-presence tables with
   source locations. Preserve explicit user canon and approved amendments.
2. Inventory real event/quest IDs, guards, effects, one-shot flags and persistence.
   Detect missing targets, impossible prerequisites and effects that never run.
3. Map branches and reconvergence. For each critical outcome list an initial save,
   ordinary-input route, expected event order and observable final world state.
4. Test interruption, repeat, reload, optional-content omission and reverse order.
   Check resource exhaustion/actor death cannot strand mandatory rescue goals.
5. Check simultaneous presence, item ownership and dialogue knowledge against
   world state. A radio line is not proof its speaker is physically spawned.
6. Compare described campaign with the active engine. Mark legacy-only chapters,
   proposed quests, implemented but untested branches and tested outcomes.

## Acceptance
Return an evidence ledger with pass/fail/unknown per branch/fact and reproducible
defects. Search/static checks find candidates; runtime traces establish behaviour.
Never label a found-patient objective as completed evacuation without boarding
evidence. Leave unreachable/unimplemented narrative content clearly open.
