# Mira Home product work log

## 2026-11-16 — Filter department owners in the Workers view

- **Source/version:** User direction in `/home/flesh/MiraHome/StarNet/START_HERE.md`, `project/SHARED_WORK.md`, and `project/MEH_CANONICAL_ROADMAP_2026-11-13.md`; interface source copied from `/home/flesh/MiraHome/mira-home-v1.14-meh/mira_home/ui/static` into `product/v1.14/` in the existing feature worktree. Latest shared-root receipt read: `private/LAST_CONSOLIDATION_RECEIPT.json` (2026-11-15T23:53Z). It was a root-consolidation receipt, not an earlier UI feature delivery; no preceding GUI feature receipt was found in the shared product root.
- **Selected backlog improvement:** Make the existing Workers / Department Owners GUI searchable by owner name, domain, or status.
- **Before:** Workers view rendered all owners as one undifferentiated list, with no local way to find a specific owner.
- **After:** Added an accessible text search input that filters the existing owner cards by name/domain/status, with a live result count and a clear empty state if no owners exist. The filter only affects owners; task execution state and other views are unchanged.
- **Changed files:** `mira_home/ui/static/app.js`, `mira_home/ui/static/style.css`.
- **Focused regression:** `node --check product/v1.14/mira_home/ui/static/app.js` — PASS; `python3 -m py_compile product/v1.14/preview_server.py` — PASS; `git diff --check` — PASS. A separate Node fixture confirmed whitespace-trimmed, case-insensitive name/status matching, empty query, and no-match behavior.
- **Disposable preview:** `python3 product/v1.14/preview_server.py` (with `MIRA_PREVIEW_PORT=17332`; run `bg_22175bc0-3426-45ad-ac63-2485a217fabc`) served synthetic data at `http://127.0.0.1:17332/`. In the local browser test, switched to Workers and confirmed the `demo-owner` card plus visible `Hitta owner` input (`#workerSearch`, type=search, placeholder `Namn, roll eller status`). Keystroke-driven filtering was not verified in-browser; the preview was terminated after the visual/control check. This is a synthetic fixture, not live Mira Home state.
- **Start command:** from repository root: `python3 product/v1.14/preview_server.py` (or set `MIRA_PREVIEW_PORT` to a free localhost port first).
- **Status:** Candidate UI code in isolated working copy; not integrated/deployed/live-verified.

## 2026-11-16 — Give owner search an explicit no-match state

- **Source/version:** Same existing feature worktree and v1.14 UI source; continued the preceding `feat(ui): add department owner search` slice rather than selecting a new feature. Canonical direction remains `/home/flesh/MiraHome/StarNet/START_HERE.md`, `project/SHARED_WORK.md`, and `project/MEH_CANONICAL_ROADMAP_2026-11-13.md`. The prior receipt is this file's preceding entry; its synthetic preview did not verify keystroke filtering.
- **Before:** Filtering hid non-matching owner cards and reported a count, but an empty match set left a blank owner region with no explicit explanation.
- **After:** A filtered search with zero matches now displays “Inga owners matchar sökningen.” The message is hidden when the query is cleared or any owner matches; owner records and task data are unchanged.
- **Changed file:** `product/v1.14/mira_home/ui/static/app.js`.
- **Focused regression:** `node --check product/v1.14/mira_home/ui/static/app.js`, `python3 -m py_compile product/v1.14/preview_server.py`, and `git diff --check` — PASS. Browser preview loaded the Workers screen and located the search control and synthetic `demo-owner`. Headless synthetic key entry did not change the input value, so dynamic filtering and the new empty state were NOT verified in-browser; the preview remains synthetic, not live Mira state.
- **Disposable preview:** `http://127.0.0.1:17334/`, process `bg_4b7fa194-3621-4a00-b30e-0063baef8d78` (`MIRA_PREVIEW_PORT=17334 python3 product/v1.14/preview_server.py`).
- **Start command:** from repository root: `python3 product/v1.14/preview_server.py` (or set `MIRA_PREVIEW_PORT` to a free localhost port first).
- **Status:** Candidate UI code in isolated feature worktree; not integrated/deployed/live-verified. Interactive filtering behavior remains unconfirmed because the synthetic browser input path did not change the input value.
