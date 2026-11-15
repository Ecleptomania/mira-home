# MiraLang experimental prototype

**Status: non-canonical work in progress.** This standalone prototype is not an adopted MiraLang specification. It is not connected to StarNet, Mira Home/MEH runtime, or production, and it does not modify any active system.

## Contents

- `miralang_draft.py`: draft JSON parsing/canonicalization, bundle and request shape checks, inert Surface parsing/rendering, and result/request correlation.
- `miralang_persisted_experiment.py`: isolated filesystem-backed task/checkpoint experiment and read-only recovery evaluation.
- `miralang_agency_draft.py`: inert validators for proposal and decision-attribution record shapes.
- Matching `test_*.py` modules contain synthetic standard-library tests.

Run the tests from this directory with `python3 -m unittest -v`.

## Limits

These modules validate draft structure and local integrity properties only. They do not authenticate authorship, evidence, timestamps, provenance, or authority; grant permission; establish truth; commit canonical state; or demonstrate autonomous agency, identity, continuity, or subjective experience. Recovery evaluation is read-only and does not resume execution. The persisted experiment assumes a trusted local filesystem and does not support coordinated cross-process writes. SHA-256 checks content against a locally stored digest; it is not authentication.

This directory is a prototype contribution for review only. Publication does not imply canonical adoption, runtime integration, or production readiness.
