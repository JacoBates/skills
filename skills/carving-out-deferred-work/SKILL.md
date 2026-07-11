---
name: carving-out-deferred-work
description: Use when follow-up or cleanup work surfaces mid-task that you won't do now - a dedup, a broader migration, a nice-to-have uncovered while shipping something else - or when you say "defer this" / "file a follow-up" / "split this out for later" / "make a ticket for the rest" / "out of scope for now, but".
---

# Carving out deferred work

## Overview

Mid-task, work often surfaces that is real but shouldn't be done now: it would
bloat the current change, needs separate review or verification, or is simply a
different concern. The instinct is a one-line "TODO: do X later" or a stub
ticket titled "refactor the thing". Both rot - the next person (or agent) has no
memory of the session, so they can't tell what X actually is, why it was left,
where the seam is, or how to prove they did it right.

This skill produces a **deferred unit of work that a stranger can pick up cold**:
a titled artifact (normally a tracker ticket) whose body carries enough context,
a sharp boundary, the risk, and the verification that the decision to defer is
auditable and the work is landable on its own.

**Core principle:** the value is not the template - it is the *judgement* that
the thing is a clean, independently-landable seam. If you can't state what's in,
what's out, and why deferring is safe, the unit isn't ready to be carved out
yet. Sharpen it first, or don't defer it.

## When to use

- You're about to leave a `TODO`/`FIXME` comment or a stub ticket titled
  "refactor the thing" for work you won't do in this change.
- A dedup or cleanup you spotted spans files the current change never touched.
- A reviewer or you flagged "out of scope for now" and you want that decision
  recorded, not lost.
- You're handing off mid-stream and want the not-yet-done parts captured as
  discrete, grabbable units rather than prose in a handoff doc.

Do NOT use this to dump every idea into the tracker. A deferral is worth filing
only when it is a concrete, bounded change - not "improve performance someday".

## The boundary gate (do this first)

Before writing anything, test whether the work is actually deferrable as a clean
unit. Answer these; if you can't, the seam is muddy - surface that to the user
and sharpen it before producing the artifact. Do not file a vague ticket.

1. **In / out.** Can you name exactly what this unit changes and, explicitly,
   what it does NOT touch? If "out" is fuzzy, the seam is fuzzy.
2. **Deferred lands without current.** Can the deferred unit ship on its own
   later, not depending on unfinished pieces of the current work? If it can only
   land inside this PR, it isn't deferrable - it's just this work.
3. **Current lands without deferred.** Is the current change correct and complete
   with the deferred bit left out? If not, you can't defer it.

If any answer is "no" or "not sure", first close the gap yourself with the tools
you have - grep/search to enumerate the sites, read the current change to check
coupling. Only interview the user for what you genuinely cannot determine
(intent, why-defer, one-seam-or-two). Don't offload a lookup you could do. A
well-carved seam is the whole point.

## The body: five parts, each a discipline

A carved-out unit's body has five parts. Each is also the bar it must clear - if
any part is missing or vague, the unit isn't ready.

- **Context** (*self-contained*) - what exists now that this work builds on or
  cleans up, written so someone with zero session memory can orient. Name the
  exact file paths - no "a few places", no "maybe elsewhere"; if you can't
  enumerate the sites you haven't scoped it, go find them. Show a short snippet of
  any existing abstraction this work should adopt. Cross-reference sibling tickets
  by id.
- **Task** (*self-contained*) - the precise change. Name the specific
  methods/classes/files to touch and what to do to each. Mechanical enough to hand
  to an agent cold.
- **Out of scope** (*clean seam*) - explicit exclusions, each with a reason and,
  where relevant, a cross-ref to the ticket that DOES own it. This is where the
  seam is drawn.
- **Risk & verification** (*named up front*) - the landmine (what could silently
  break) stated first, then the exact check that proves it didn't: commands, the
  environment they run in, and which check is the *real gate*. If a tool
  regenerates artifacts (contract tests, schemas, snapshots), state the required
  "no diff" check explicitly.
- **Deferral justification** (*why now*) - one or two lines on why it's deferred
  now (scope, review cost, separate verification, different concern) so the
  decision is auditable and not re-litigated.

## Producing the artifact

1. Run the boundary gate. If muddy, self-serve the lookups; interview only for
   genuine judgement gaps; don't proceed until the seam is sharp.
2. Draft the title + body from the conversation - deferrals emerge from work in
   flight, so mine what the session already established rather than re-asking it.
3. **Surface the title and full body to the user for explicit approval before
   creating anything** - this is public-space text. Do not create on assumed
   consent.
4. On approval, create the artifact in the tracker. Where it lives
   (list/status/assignee/parent) and how it relates to the originating work
   (subtask, link, dependency) are per-situation decisions - surface and confirm,
   don't assume a fixed destination. Check the project's own instructions
   (AGENTS.md / CLAUDE.md) for tracker conventions.
5. Report the created id/URL back.

## Red flags

| Thought | Reality |
| --- | --- |
| "I'll just leave a TODO comment" | A comment has no context and no owner. Carve a real unit. |
| "Refactor the thing later" as a title | If the title is vague, the seam is vague. Name the specific change. |
| "The next person will figure out the boundary" | They have zero session memory. Draw the seam now, in Out of scope. |
| "It's obvious why we're deferring" | Obvious now, gone in a week. Record the justification. |
| "It works, no need to say how to verify" | Name the landmine and the gate, or the picker-upper can't prove correctness. |
| "I'll create the ticket, then show you" | Public-space text needs approval BEFORE it lands. Draft, approve, then create. |
| "Everything I noticed should be a ticket" | Only concrete, bounded changes. Vague wishes rot the tracker. |
| "Chuck it in the backlog and move on" | Fire-and-forget is how deferrals rot. Run the gate, name the sites, state the check - then file. |
| "a few places / maybe elsewhere" | Hedged scope = unscoped. Enumerate the exact sites now, or the picker-upper inherits your uncertainty. |
| "Not urgent, just don't want to lose track" | That's a reminder, not a carved unit. Give it a boundary, context, and verification or it's unactionable later. |
