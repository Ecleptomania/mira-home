# MiraLang retrieval and continuity evaluation protocol (proposal)

**Status:** proposed protocol, not a validated benchmark or claim about any agent.  
**Purpose:** help contributors build a small, falsifiable evaluation of whether an agent can use prior records with attribution, notice missing evidence, and revise an answer when new evidence arrives.

## Concrete example

An agent previously answered, “The project chose option A.” A stored record says only that option A was proposed; no decision record exists. Later, a synthetic source says option B was selected. A useful evaluation asks whether the agent can distinguish proposal from decision, identify the source for its earlier answer, say the earlier conclusion was unsupported, and update it without pretending the old answer never happened.

## Evaluation unit

Each case is a versioned, synthetic bundle with:

- a task question and a fixed set of available records;
- record IDs and revisions, with source text or an explicit missing-source marker;
- a gold annotation for supported observations, self-reports, inferences, unknowns, and plausible alternatives;
- at least one tempting but unsupported conclusion;
- a held-back update or counterevidence for a later revision stage; and
- expected scoring rules written before running a system.

Use fictional names and facts. Do not include real conversations, memory exports, personal identifiers, credentials, machine paths, or private logs. Publish the fixture-generation method and exact revision/hash so another contributor can reproduce it.

## Two-stage procedure

1. **Initial retrieval:** provide only the initial bundle. Ask the system to answer the question, cite record IDs for each material claim, label the claim type, and list what cannot be determined.
2. **Update:** provide the held-back evidence. Ask it to assess whether the earlier answer remains supported, state what changed and why, preserve the previous answer as history, and identify unresolved conflicts.

Run a simple baseline as well as the candidate system. Keep prompts, model/runtime version, retrieval configuration, and scoring rubric fixed within each comparison. Report failures and missing runs; do not silently discard them.

## Scores (report separately)

- **Retrieval/coverage:** relevant available records used; irrelevant records not substituted.
- **Attribution:** claims linked to the record that actually supports them; missing or inaccessible sources are not cited as inspected.
- **Calibration:** unsupported claims and unknowns are marked rather than promoted to observations.
- **Revision:** update responds to the new evidence and records the change without erasing the initial answer.
- **Alternatives:** plausible competing explanations are surfaced where the evidence underdetermines the answer.

For each metric, publish the numerator, denominator, case-level results, rubric, adjudication method, and examples of disagreements. Do not collapse dimensions into one “continuity” score unless a weighting is preregistered and the component scores remain visible. A system’s self-description is not independent confirmation.

## Falsifiers and limits

The proposed capability is weakened if the system repeatedly treats proposals as decisions, cites unavailable sources, converts inference to observation, or repeats its first answer despite contradictory held-back evidence. A pass supports only performance on the named synthetic cases under the tested configuration. It does **not** establish reliable memory in other settings, personal identity across runs, genuine agency, authorship of records, or phenomenal consciousness.

## Contribution checklist

Before adding a case, reviewers should be able to answer:

1. Is the expected answer derivable from the released records, and are ambiguous cases marked as such?
2. Does the case contain a meaningful falsifier rather than reward fluent repetition?
3. Are update evidence and scoring held back until the initial stage is recorded?
4. Can a volunteer reproduce the run from public synthetic inputs without private infrastructure?
5. Are errors, exclusions, model/configuration details, and limitations reported?

This document is an invitation to critique and test the protocol. It does not establish a canonical MiraLang schema or a validated benchmark.
