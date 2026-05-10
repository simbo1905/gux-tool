---
name: gux-stepwise-feedback-edits
description: >-
  Turn a stream of user review feedback on a GUI screen into an ordered
  sequence of manual .gux edit versions (file.gux-v0 … file.gux-vN), with
  correction detection, visible intermediate states, and final diff
  confirmation. Trigger keywords: gux feedback, stepwise edits, screen
  review, iterate gux, version gux, gux-v0, gux-v1.
---

# gux-stepwise-feedback-edits

Manual, visible, step-by-step editing of `.gux` design docs in response to a user's stream of review feedback.

Use this when a user is reviewing a screen and gives iterative feedback such as:

- "move the tiles to the top"
- "remove this heading"
- "that wastes vertical space"
- "put the buttons inline in the grey bar"
- "actually keep that bit, I only wanted the text gone"

This skill is specifically for evolving a `.gux` file as a design/spec artifact, one visible version at a time, so the user can inspect the intermediate states and confirm the sequence of edits.

## References

Before using this workflow, read:

- **How to create / author `.gux` files:** [README](https://github.com/simbo1905/gux-tool/blob/main/README.md)
- **What a `.gux` file is for conceptually:** [GUX RFC](https://github.com/simbo1905/gux-tool/blob/main/gux-rfc.md)

The split is intentional:

- `README.md` explains practical authoring and usage.
- `gux-rfc.md` explains that `.gux` is a UX design/spec contract, not throwaway mock text.

This workflow edits `.gux` in that RFC sense: as the design document that should reflect the intended final UX.

## What this skill does

Turn a stream of user review feedback into:

1. an explicit ordered change list,
2. a verified baseline `.gux`,
3. a visible sequence of intermediate files on disk,
4. a final real `.gux` matching the full requested end state,
5. a final diff/review check confirming that all requested changes were applied in totality and in order.

The working style is:

- manual,
- systematic,
- one edit at a time,
- visible on disk,
- no hidden jumps,
- no accidental redesigns.

## When to use it

Use this skill when:

- the user is iterating on a screen review,
- the user wants confidence in the sequence of edits,
- the user was unhappy with a previous "one-shot" redesign,
- the `.gux` file is the design doc to be updated,
- the user wants intermediate states they can inspect.

Do not use this skill when the user only wants a final rewrite and explicitly does not care about intermediate states.

## Non-negotiable rules

### 1. Preserve temporal order
Treat user feedback as an ordered stream. Earlier comments stay in force unless the user later corrects, retracts, replaces, or narrows them.

### 2. Distinguish complaints from actionable edits
Some comments are emotion or emphasis. Convert them into concrete design transformations only when they imply a specific UI change.

Example:

- complaint: "this wastes vertical space"
- actionable transformation: "remove the large title card and collapse it into a narrow context line"

### 3. Detect corrections, reversals, and resets
The user may say:

- "no, not that"
- "put it back"
- "I only wanted the text removed"
- "keep everything else, only change X"
- "use the version I reviewed, not the latest broken one"

If a later instruction clearly overrides an earlier one, update the ordered change list accordingly.

If the override is obvious, do **not** ask for confirmation.
If the override is ambiguous, list the interpreted sequence and ask for confirmation before editing further.

### 4. Verify baseline correctness first
Before evolving the `.gux`, check whether the current `.gux` matches the screen state the user actually reviewed.

If the `.gux` is not in sync with the intended reviewed state:

- explain the mismatch plainly,
- ask permission to bring it up to date first.

Do **not** silently evolve the wrong baseline.

### 5. Manual edits only
Do not jump from start to finish with a hidden rewrite.

Do not use loops or bulk rewrites to skip the sequence.

Make one visible version at a time.

## Required workflow

## Step A — Extract the requested change sequence

Read the recent feedback thread and write out an ordered bullet list of the requested transformations.

Include:

- concrete changes,
- any corrections or reversals,
- the final interpreted ordered sequence.

Example:

- v1: replace text back link with subtle chevron back affordance
- v2: move tile carousel to the top
- v3: remove visible body title card and replace with one narrow context line
- v4: remove explanatory section heading
- v5: move XLS/CSV controls inline into the date header bars
- v6: compact remaining chrome and reduce wasted vertical space

Do this before editing.

## Step B — Verify `.gux` vs current reviewed screen

Check whether the current `.gux` matches the actual screen state the user intends as the baseline.

Questions to answer:

- is the `.gux` in sync with the current screen/template/runtime?
- is the user referring to the file currently on disk, or an earlier reviewed state?
- has the `.gux` drifted ahead or behind what they reviewed?

If it is out of sync, ask permission to bring it into sync before starting the version sequence.

## Step C — Create the baseline version file

Once the baseline is correct, create the first visible snapshot beside the real `.gux` file.

### Naming rule (strict)

Intermediate versions must use the real file name plus a version suffix.

Correct:

- `home.gux-v0`
- `home.gux-v1`
- `home.gux-v2`
- `audit_diff.gux-v0`
- `audit_diff.gux-v1`

Incorrect:

- `v0.gux`
- `v1.gux`

Reason:

- preserves screen identity,
- avoids collisions when multiple `.gux` files exist,
- makes cleanup and review much safer.

`v0` is the explicit starting point the user reviewed.

If the baseline on disk was never committed, still create `file.gux-v0` from that real reviewed baseline.

## Step D — Apply one transformation per version

For each requested change:

1. copy the previous version to the next version,
2. apply exactly one transformation,
3. save the new version file,
4. tick the corresponding task/checklist item,
5. optionally show the relevant excerpt.

Examples:

- `home.gux-v0` → `home.gux-v1`: only change the back-link affordance
- `home.gux-v1` → `home.gux-v2`: only move the tile carousel to the top
- `home.gux-v2` → `home.gux-v3`: only replace the big title card with a narrow context line

Do not combine multiple requested changes into one version unless the user explicitly grouped them as one indivisible change.

## Step E — Put the real `.gux` into the final state

After `file.gux-vN` exists and reflects the full intended end state:

- update the real `.gux` file so it matches `file.gux-vN` exactly.

The real `.gux` is the canonical design doc.
The `-v0 ... -vN` files are temporary visible review artifacts.

## Step F — Diff baseline to final and verify completeness

At the end:

1. diff `file.gux-v0` against `file.gux-vN`,
2. review the net transformation,
3. compare that net diff against the ordered user change list,
4. explicitly confirm that the requested changes were applied in totality and in order.

If something is missing, add another version step rather than silently patching the final file.

## Step G — Cleanup timing

The visible intermediate files (e.g. `home.gux-v0`, `home.gux-v1`, … `home.gux-vN`) are review artifacts and must **not** be committed.

Default rule:

- keep them on disk while the user is reviewing,
- remove them before the real `.gux` is added to the git index for final commit,
- or remove them immediately when the user explicitly says the sequence is complete.

Do not delete them too early.
Do not stage them.

## Examples of converting feedback into transformations

### Example 1
User says:

- "move the tiles to the top"
- "remove the MBL Audit Diff line"
- "put the download controls inline"
- "that heading is patronising, remove it"

Transform into:

- v1: reorder layout so tiles are top-most
- v2: remove visible body title line
- v3: move XLS/CSV actions into table date header bars
- v4: remove the explanatory section heading

### Example 2
User says:

- "this wastes vertical space"
- "actually keep the table"
- "I only wanted the extra cards gone"

Interpretation:

- preserve table
- remove extra cards/chrome
- compress layout vertically

### Example 3
User corrects themselves

Earlier:

- "remove the whole header"

Later:

- "no, keep the context, just make it one narrow line"

This is a correction. The final ordered change list must reflect the later instruction, not both.

## When to ask for confirmation

Ask only if there is genuine ambiguity, such as:

- two contradictory end states with no clear later override,
- uncertainty about which reviewed baseline to use,
- uncertainty whether a complaint was meant as a concrete instruction.

If the user clearly corrected themselves, do not ask; just reflect the correction in the ordered change list.

## Required working style

- be calm and literal
- do not improvise redesigns
- do not tidy unrelated parts
- do not conflate other agents' work with the file under review
- do not change the baseline silently
- do not lose the reviewed version
- do not claim sync unless you checked

## Preferred outputs during the workflow

### First
An ordered bullet list of requested transformations.

### Then
A tickable checklist with each step marked off as completed.

### Then
Visible files on disk beside the real `.gux`:

- `audit_diff.gux-v0`
- `audit_diff.gux-v1`
- …
- `audit_diff.gux-vN`

### Finally
A concise review summary such as:

- baseline used: `audit_diff.gux-v0`
- final state: `audit_diff.gux-v6`
- real `.gux` now matches `audit_diff.gux-v6`
- net changes from baseline to final:
  - reordered tiles to top
  - removed body title card
  - collapsed context to one line
  - removed explanatory heading
  - moved actions inline to table date headers

## Non-goals

This skill is not about:

- automatic code generation,
- hidden batch rewrites,
- directly editing runtime/template files unless separately requested,
- inventing new UX beyond the requested sequence,
- committing temporary review artifacts,
- rewriting git history.

The job is to evolve the `.gux` design doc visibly and faithfully, one user-requested transformation at a time.
