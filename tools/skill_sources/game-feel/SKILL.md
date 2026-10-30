---
name: game-feel
description: "Polish control response, movement, impact feedback, camera and sound in a playable game. Use for jerky movement, weak hits, excessive shake or noisy effects; not for adding arbitrary particles to hide missing animation."
---

# Game Feel

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
Use engine frame timing/capture, animation playback, actual input and audio
recording/metering. A waveform does not establish pleasant sound; listen when
audio playback tools are actually available and disclose when not.

## Procedure
1. Reproduce a specific visible/audible complaint. Separate source animation,
   controller velocity, camera interpolation, collision, frame pacing and sound.
2. Measure input-to-action rules, acceleration/braking, turn speed, attack
   contact/recovery, dodge distance/cooldown and damage timing before tuning.
3. Change one causal group at a time. Match feet to travel and impacts to contact.
   Preserve player agency with intentional buffering/cancel windows.
4. Add brief, readable local hit feedback. Hit stop/shake/squash are optional,
   not mandatory: do not freeze the whole world on every hit or distort a fixed
   anatomical style. Include reduced-motion options if strong effects are used.
5. Check sound levels, clipping, loops, distance attenuation and active listener.
   Do not reintroduce continuous hiss to simulate atmosphere. Test real mixes
   with simultaneous footsteps, combat, environment and dialogue.
6. Compare normal-speed fixed/following-camera footage, repeated inputs,
   diagonal turns, crowded combat and pause/resume. Recheck at relevant rates.

## Acceptance
Observed response matches timing, visual contact and feedback. No camera judder,
repeated knockback accumulation, global hit freeze or masking effects. Record
actual remaining motion/audio defects; subjective feel needs direct play review.
