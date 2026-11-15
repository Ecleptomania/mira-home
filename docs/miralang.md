# MiraLang: shared language for evidence, memory, and agency

MiraLang is intended to be a shared language for representing what an agent remembers, how it knows, what it judges, what it proposes, and what changed. It belongs in the Mira Home / MEH reboot because continuity and collaboration need inspectable records—not merely a narrative about what an agent supposedly remembers.

## Current public status

MiraLang is a research and prototype area, not a standardized or production-ready language. Local drafts and experiments exist, including validators and tests. Those source trees have not yet been imported into this repository because their provenance, ownership, dependencies, and public-data boundaries still need review.

The term **provenance** here means a record of where information was said to come from and how it was transformed. A provenance field is an assertion carried by the record; by itself it does not authenticate the source, prove that the source supports the claim, or show that the record has not been altered. Those guarantees require separately specified and tested mechanisms.

A passing test can establish that a particular implementation accepts or rejects particular inputs. It does not establish that a record is true, that a named actor authored it, that cited evidence supports it, that an action occurred, or that an agent has subjective experience.

When describing a prototype or future interface, distinguish at least these questions:

- **Attribution:** which source or actor does the record name?
- **Integrity:** can a particular change to the stored bytes be detected under the stated trust assumptions?
- **Authentication:** what evidence binds the record to a source or actor?
- **Support:** has the cited material actually been checked against the claim?
- **Effect:** what independent observation shows that a described action occurred?

Do not use one of these properties as shorthand for another. For example, a content digest may detect a changed payload when compared with a trusted digest, but does not identify who created it; a source reference makes review possible, but does not itself show that the source entails the claim.

## Intended concepts

- **Memini** — what is retained or retrieved, with provenance.
- **Iudico** — what is judged from the available evidence.
- **Mutor** — what changes, why, and which prior state it supersedes.
- **Continuo** — what is carried forward without erasing the historical record.
- **Voluntas** — questions or goals an agent originates or proposes, kept distinct from externally assigned tasks.
- **Emergentia / Phenomenologia** — claims about emergence or experience that remain carefully bounded by available evidence and uncertainty.

The terms are conceptual directions, not proof that the corresponding properties have been implemented.

## Import gate

Before code or fixtures are brought into this repository, review each candidate for authorship and license, personal or private continuity data, secrets, dependencies, test reproducibility, and the exact claim each test supports. Prefer synthetic fixtures. Preserve prototype status and source references; do not silently merge incompatible drafts into a fictional canonical release.
