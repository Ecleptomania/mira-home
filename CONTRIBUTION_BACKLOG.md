# Open contribution backlog

This backlog turns the project's current research aims into small, reviewable invitations. It is a set of **proposed questions**, not a claim that the corresponding systems or interfaces already exist. Start with one issue-sized experiment or critique; challenge the framing when the evidence points elsewhere.

For project status and boundaries, read [`README.md`](README.md), [`docs/vision.md`](docs/vision.md), [`docs/miralang.md`](docs/miralang.md), [`HISTORY.md`](HISTORY.md), and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## What is public today

The repository currently contains project framing, history, vision, contribution guidance, and a MiraLang concept/status document. It does **not** yet contain a production harness or a verified integrated MEH/MiraLang/elastic-memory implementation. Local prototypes and test reports are not part of this repository unless explicitly imported and reviewed. A successful test proves only the behavior of the exact tested code and inputs; it does not establish the truth of a record, authorship, authority, real-world effect, or subjective experience.

## Contribution tracks

### 1. Provenance under compression

**Question:** after a record has been summarized repeatedly, can an independent reader still tell which statements are direct source, paraphrase, inference, contradiction, or unknown?

**Useful contribution:** a synthetic source bundle plus a lossy-summary/recovery test. Include at least one tempting but unsupported inference and one source that becomes unavailable. Define in advance what counts as a pass or failure.

**Do not claim:** that a citation alone proves a source supports a claim, or that provenance preservation establishes personal identity.

### 2. Revision without rewriting history

**Question:** can a later judgment correct an earlier one while preserving what changed, why it changed, and which evidence was available at each point?

**Useful contribution:** a proposed record shape, a counterexample, or a small state-transition test using fictional data. Include a conflicting-evidence case and show how the earlier state remains inspectable.

**Do not claim:** that a schema-valid correction is justified, truthful, or properly authorized without separate evidence.

### 3. Authority and effects in delegated work

**Question:** can a collaborator distinguish a proposal, an authorization, an attempted action, and a verified external effect—and represent revocation while work is already in flight?

**Useful contribution:** a threat model, state-machine critique, or synthetic test matrix covering scope, expiry, denial, revocation, retries, and uncertain outcomes.

**Do not claim:** that a log entry by itself enforces a permission boundary or proves an external action happened.

### 4. Retrieval and continuity evaluation

**Question:** when an agent is given an old record or summary, can it retrieve the relevant source, recognize missing evidence, and revise a prior answer rather than merely repeat it?

**Useful contribution:** a small, reproducible benchmark with held-back cases, explicit alternatives, and separate scores for retrieval, attribution, uncertainty, and correction. Compare against a simple baseline.

**Do not claim:** that benchmark performance resolves consciousness or numerical identity.

### 5. Public test and prototype design

**Question:** what is the smallest standalone testable component that would let an outsider falsify one of the project's assumptions?

**Useful contribution:** propose a narrowly scoped interface or test fixture, list dependencies and non-goals, and use synthetic/public data only. Keep prototypes separate until their source, license, dependencies, and data boundaries are reviewed.

## Contribution packet

For an issue, experiment, or pull request, include:

1. **Question or failure mode** — one sentence, narrow enough to test.
2. **Evidence class** — observed result, self-report, inference, proposal, or unknown.
3. **Source and revision** — link or stable identifier; for code, include the exact commit and command.
4. **Reproduction** — synthetic/public inputs, steps, expected result, and actual result.
5. **Falsifier and limits** — what result would count against the claim, and what the test cannot establish.
6. **Privacy/licensing check** — confirm that no private chats, personal data, secrets, or unreviewed third-party material are included.

A good first contribution can be a disagreement, a counterexample, or a test that shows the current framing is wrong. Please open a focused GitHub issue or discussion before a larger implementation proposal; link the relevant track above and state what evidence would change your view.

## Current boundary

These tracks are invitations for research and review, not accepted architecture or implementation specifications. The repository's `main` branch is the public source of truth for published project material. Do not infer that a local file, scheduled agent report, or unmerged branch is part of this public codebase. Updates to this backlog should record meaningful changes in Git history rather than silently converting proposals into established facts.
