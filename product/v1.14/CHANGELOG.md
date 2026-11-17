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
- **Status:** Candidate UI code in isolated working copy; not integrated/deployed/live-verified. Interactive filtering behavior remains unconfirmed because the synthetic browser input path did not change the input value.

## 2026-11-16 — Continue owner-search verification (BLOCKED)

- **Scope:** Continued the same owner-search UI slice; no second feature selected. Read the canonical project root and latest product receipt. The current feature worktree is `/home/flesh/MiraHome-Reboot`, branch `feature/mira-home-agent-inspector-v1.14-2026-11-16`; the product code and prior log entries were already present and clean at this run's start.
- **Observed in preview:** Started the disposable fixture with `MIRA_PREVIEW_PORT=17341 python3 product/v1.14/preview_server.py` (run `bg_875eaac1-36d0-412f-ac9d-02758ccf9d21`). Opened `http://127.0.0.1:17341/`, switched to Workers, and observed the `Hitta owner` input plus synthetic `demo-owner` card. The fixture is not live Mira state.
- **BLOCKED — interactive verification:** `browser.test_input` click/key actions and `browser.type` did not change `#workerSearch`; read-back through `browser.test_state` continued to show `value:""`, so filtering and the no-match state could not be proven in the preview. The alternate direct-DOM route returned this exact error: `browser.eval is refused: this run is using the signed-in station profile, and arbitrary page script there could read the cookies and storage of accounts you are signed into. Use browser.inspect (by ref from browser.snapshot) for computed styles/attributes/shadow DOM, or browser.get_text for content. On your own localhost server, browser.test_snapshot and browser.test_state read the page.`
- **Checks:** `node --check product/v1.14/mira_home/ui/static/app.js`, `python3 -m py_compile product/v1.14/preview_server.py`, and `git diff --check` passed. These are syntax/hygiene checks only, not proof of live interactive behavior. One HTTP fixture assertion failed because the static HTML is only a shell and the GUI content is rendered by JavaScript; the server itself returned HTTP 200 and `/api/state` contained `demo-owner`.
- **Start command:** from the repository root, `python3 product/v1.14/preview_server.py` (or set `MIRA_PREVIEW_PORT` to a free localhost port).
- **Status:** BLOCKED / not delivered for the requested end-to-end UI verification. No live integration, deployment, or public PR was made. Do not call owner search verified until input events can be delivered/read back in the disposable preview.

## 2026-11-17 — Keep owner search through live view refreshes

- **Scope:** Continued the same Workers / Department Owners search slice from the prior receipt; did not select a second backlog item. Read the shared coordination root and the latest product receipt before continuing.
- **Before:** Every state refresh rebuilt the Workers view and reset the query input to blank, so a search was lost during polling and hidden cards reappeared.
- **After:** The typed owner query now survives Workers rerenders and immediately reapplies to the refreshed owner list. Matching remains case-insensitive and local to the owner cards; task execution state and other views are unchanged.
- **Changed file:** `product/v1.14/mira_home/ui/static/app.js`.
- **Focused regression:** `node --check product/v1.14/mira_home/ui/static/app.js`, `python3 -m py_compile product/v1.14/preview_server.py`, and `git diff --check` — PASS. A deterministic Node regression checked case-insensitive name/domain/status matching, trimmed query, empty query, no-match behavior, and presence of query persistence/reapply hooks — PASS.
- **UI verification boundary:** Preview HTML, Workers navigation, search control, and synthetic `demo-owner` card were observed. Actual typed interaction and post-refresh DOM behavior could not be verified: `browser.test_navigate` refused local-server ownership on three attempts and `browser.test_state` is read-only. The direct-DOM `browser.eval` route was refused because this run uses the signed-in station profile. This receipt does not claim interactive UI behavior verified.
- **Disposable preview:** `http://127.0.0.1:17352/` (`MIRA_PREVIEW_PORT=17352 python3 product/v1.14/preview_server.py`; run `bg_073befeb-c726-4163-86ea-7b4df39aec9a`). Preview data is synthetic only.
- **Start command:** from repository root: `python3 product/v1.14/preview_server.py` (or set `MIRA_PREVIEW_PORT` to a free localhost port).
- **Status:** Candidate UI code in isolated feature worktree; not integrated/deployed/live-verified.
