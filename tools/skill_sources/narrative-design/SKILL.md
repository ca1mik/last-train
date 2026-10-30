---
name: narrative-design
description: "Develop game story, character arcs, dialogue and branching events tied to player actions. Use for scenario writing and narrative integration; preserve existing canon and use narrative-qa to validate state reachability."
---

# Narrative Design

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
Read actual scenario/data files and quest code. Use existing data formats and
engine event systems; a new narrative framework is not required by default.

## Procedure
1. Build a fact ledger from NARRATIVE_BIBLE and source: dates/ages, relationships,
   living status, motivations, locations and knowledge per character. Cite files.
   Resolve conflicts by evidence; label interpretation and proposals separately.
2. Define conflict, playable objective and consequence per beat. Attach each beat
   to an actual mechanic or planned state transition; avoid making an action game
   into long mandatory dialogue panels to explain every event.
3. Track what each character knows, wants and refuses. Write distinct voices
   with subtext and concrete actions, preserving chronology and motivations.
4. Specify event ID, prerequisites, actor presence, start/end state, repeat policy,
   interruption behaviour and save persistence. Choices need visible consequences;
   do not introduce hidden punishment or canon twists without authorization.
5. Provide branch/act structure, critical path, optional content and reconvergence.
   Separate implemented scenes from scripts that have not reached the new engine.
6. Prototype one beat in-game, review pacing alongside movement/combat, then
   hand off event coverage and unresolved questions to narrative-qa.

## Acceptance
Every required beat has a playable trigger or is explicitly future work. No
unapproved retcon, impossible simultaneous presence, knowledge leak or unearned
resolution. Proposed script text alone is not implemented narrative content.
