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
- **Focused regression:** `node --check product/v1.14/mira_home/ui/static/app.js`, `python3 -m py_compile product/v1.14/preview_server.py`, and `git diff --check` — PASS. Browser preview loaded the Workers screen and located the search control and synthetic `demo-owner`. Headless synthetic key entry did not change the input value, so dynamic filtering and the new empty state were NOT verified in-browser; the disposable preview was terminated after the static/control check. No live Mira state was used.
- **Disposable preview:** `http://127.0.0.1:17334/`, process `bg_4b7fa194-3621-4a00-b30e-0063baef8d78` (`MIRA_PREVIEW_PORT=17334 python3 product/v1.14/preview_server.py`).
- **Start command:** from repository root: `python3 product/v1.14/preview_server.py` (or set `MIRA_PREVIEW_PORT` to a free localhost port first).
- **Status:** Candidate UI code in isolated feature worktree; not integrated/deployed/live-verified. Interactive filtering and the no-match state remain unconfirmed in-browser.

## 2026-11-16 — Continue owner-search verification (BLOCKED)

- **Scope:** Continued the same owner-search UI slice; no second feature selected. Read the canonical project root and latest product receipt. The current feature worktree is `/home/flesh/MiraHome-Reboot`, branch `feature/mira-home-agent-inspector-v1.14-2026-11-16`; the product code and prior log entries were already present and clean at this run's start.
- **Observed in preview:** Started the disposable fixture with `MIRA_PREVIEW_PORT=17341 python3 product/v1.14/preview_server.py` (run `bg_875eaac1-36d0-412f-ac9d-02758ccf9d21`). Opened `http://127.0.0.1:17341/`, switched to Workers, and observed the `Hitta owner` input plus synthetic `demo-owner` card. The fixture is not live Mira state.
- **BLOCKED — interactive verification:** `browser.test_input` click/key actions and `browser.type` did not change `#workerSearch`; read-back through `browser.test_state` continued to show `value:""`, so filtering and the no-match state could not be proven in the preview. The alternate direct-DOM route returned this exact error: `browser.eval is refused: this run is using the signed-in station profile, and arbitrary page script there could read the cookies and storage of accounts you are signed into. Use browser.inspect (by ref from browser.snapshot) for computed styles/attributes/shadow DOM, or browser.get_text for content. On your own localhost server, browser.test_snapshot and browser.test_state read the page.`
- **Checks:** `node --check product/v1.14/mira_home/ui/static/app.js`, `python3 -m py_compile product/v1.14/preview_server.py`, and `git diff --check` passed. One HTTP fixture assertion failed because the static HTML is only a shell and the GUI content is rendered by JavaScript; the server itself returned HTTP 200 and `/api/state` contained `demo-owner`.
- **Start command:** from the repository root, `python3 product/v1.14/preview_server.py` (or set `MIRA_PREVIEW_PORT` to a free localhost port).
- **Status:** BLOCKED / not delivered for the requested end-to-end UI verification. No live integration, deployment, or public PR was made. Do not call owner search verified until input events can be delivered/read back in the preview.

## 2026-11-17 — Keep owner search through live view refreshes

- **Scope:** Continued the same Workers / Department Owners search slice from the prior receipt; did not select a new feature. Read the canonical root, current feature branch, and existing product log; no second feature selected.
- **Before:** Every state refresh rebuilt the Workers view and reset the query input to blank, so a search was lost during polling and hidden cards reappeared.
- **After:** The typed owner query now survives Workers rerenders and immediately reapplies to the refreshed owner list. Matching remains case-insensitive and local to owner cards; task execution state and other views are unchanged.
- **Changed files:** `product/v1.14/mira_home/ui/static/app.js`, `product/v1.14/preview_server.py` (two deterministic synthetic owners to exercise match and no-match paths).
- **Focused regression:** `node --check product/v1.14/mira_home/ui/static/app.js`, `python3 -m py_compile product/v1.14/preview_server.py`, `git diff --check`, and deterministic Node checks for case-insensitive name/domain/status matching, trimmed query, empty query, no-match, persistence/reapply hooks — PASS.
- **UI verification boundary:** The preceding receipt observed the preview view and controls, but actual typed interaction and post-refresh DOM behavior remained unverified. This receipt therefore does not claim live interactive behavior verified.
- **Disposable preview:** `http://127.0.0.1:17352/` (`MIRA_PREVIEW_PORT=17352 python3 product/v1.14/preview_server.py`; run `bg_073befeb-c726-4163-86ea-7b4df39aec9a`). Preview data synthetic only.
- **Status:** Candidate UI code in isolated feature worktree; not integrated/deployed/live-verified.

## 2026-11-17 — Verify owner search persistence in disposable UI

- **Scope:** Continued the same Workers / Department Owners search improvement. Source direction remains `START_HERE.md`, `project/SHARED_WORK.md`, and `project/MEH_CANONICAL_ROADMAP_2026-11-13.md`; worktree `/home/flesh/MiraHome-Reboot`, branch `feature/mira-home-agent-inspector-v1.14-2026-11-16`.
- **Before:** Previous receipts documented the unresolved concern: query retention/reapplication across Workers rerenders had code checks but no interactive browser observation.
- **After:** Existing implementation stores the query in `workerSearchTerm`, restores it to the rebuilt search box, and reapplies filtering when the Workers view is rebuilt.
- **Focused regression:** `node --check product/v1.14/mira_home/ui/static/app.js`; `python3 -m py_compile product/v1.14/preview_server.py`; `git diff --check`; deterministic Node checks for case-insensitive name/domain/status, trimmed/empty/no-match behavior, query hooks, and preview fixture `/api/state` with two synthetic owners — PASS.
- **Disposable preview:** `MIRA_PREVIEW_PORT=17354 python3 product/v1.14/preview_server.py` (process `bg_3ccc2912-aaca-4635-9cae-c9171beac133`), URL `http://127.0.0.1:17354/`. Browser opened Workers, typed `demo-archive`, and read back `#workerSearch.value="demo-archive"`; `#ownerCards` contained only `demo-archive / MEMORY FIXTURES · IDLE`. A fresh navigation and query `nomatch` showed `0 av 2 owners` and `Inga owners matchar sökningen.`. Fixture synthetic, not live Mira data. Rerender-persistence specifically was not freshly re-observed.
- **Status:** Interactive search and empty-result behavior verified in disposable preview; candidate only—not integrated/deployed/live-verified.

## 2026-11-17 — Keep focus while owner search survives refresh

- **Scope:** Continued the existing Workers / Department Owners search improvement. No second backlog item selected. Product source remains in the existing v1.14 feature worktree; canonical direction is the shared StarNet root.
- **Before:** Search query restored and filtered after refresh, but Workers rerender replaced the input every 1.8 seconds, dropping keyboard focus/caret.
- **After:** When Workers rerender starts with `#workerSearch` focused, the rebuilt input receives focus and its selection/caret range is restored. Saved query/results are reapplied.
- **Changed files:** `product/v1.14/mira_home/ui/static/app.js`, this changelog.
- **Focused checks:** `node --check product/v1.14/mira_home/ui/static/app.js`; `python3 -m py_compile product/v1.14/preview_server.py`; `git diff --check`; fixture API assertion for two owners — PASS.
- **Disposable UI:** `MIRA_PREVIEW_PORT=17412 python3 product/v1.14/preview_server.py`, background `bg_3b800a6a-0d0f-4f86-abe6-ae3705ccad85`, URL `http://127.0.0.1:17412/`. Browser verified Workers view, typed `demo-archive`, and read back input, one matching result, and only the matching card. Focus persistence across actual polling rerender was not directly verified. Fixture synthetic only.
- **Status:** Candidate GUI change; interactive filter verified in disposable preview; focus restoration syntax-checked but not directly verified across polling. Not live-integrated/deployed.

## 2026-11-18 — Continue focus retention verification (BLOCKED)

- **Scope:** Continued the existing Workers owner-search slice only; no second backlog improvement selected. Worktree `/home/flesh/MiraHome-Reboot`, branch `feature/mira-home-agent-inspector-v1.14-2026-11-16`; open PR #11 (`https://github.com/Ecleptomania/mira-home/pull/11`).
- **Before:** Query matching was verified interactively; focus/caret across a polling rerender remained unobserved.
- **After:** No code change. Existing UI captures whether the search input was focused and its selection range before rerender, then restores focus/caret, query, and filtering. Candidate code only.
- **Checks:** `node --check product/v1.14/mira_home/ui/static/app.js`, `python3 -m py_compile product/v1.14/preview_server.py`, `git diff --check`; synthetic fixture `/api/state` returned two owners — PASS. These do not prove focus continuity.
- **Disposable preview:** `MIRA_PREVIEW_PORT=17451 python3 product/v1.14/preview_server.py` (background `bg_7fb0e81f-dd1c-49d0-90e5-0e540161e270`, `http://127.0.0.1:17451/`). Browser loaded Workers and search control, but input/focus persistence could not be exercised by the available interaction path. Focus across the timer remains NOT VERIFIED.
- **Status:** Owner search/no-match remain supported by earlier preview evidence; focus/caret continuity remains unverified. Candidate only—not integrated, deployed or live-verified. Synthetic fixture only.

## 2026-11-19 — Verify owner-search clear action; continue existing PR

- **Scope:** Continued the existing Workers / Department Owners owner-search feature only. No second backlog item was selected. Existing public PR #11: https://github.com/Ecleptomania/mira-home/pull/11, branch `feature/mira-home-agent-inspector-v1.14-2026-11-16`.
- **Behavior verified in disposable synthetic UI:** At `http://127.0.0.1:17612/`, entered `demo-archive`; the query remained visible, the result count became `1 av 2 owners`, and only the matching synthetic owner card remained. Clicked `Rensa`; read back an empty input and both owner cards restored. `/api/state` contained exactly the two synthetic fixture owners.
- **Checks run:** `node --check product/v1.14/mira_home/ui/static/app.js`; `python3 -m py_compile product/v1.14/preview_server.py`; `git diff --check`; HTTP fixture assertion — PASS. Review: compared the exact two-file commit diff; it only changes owner-search clear interaction and receipt. Secret/privacy scan of those exact files found no credentials or private memory, and no host-private path in code.
- **Delivery state:** Local commit `7a382140a599cfd58763c315323d9f3efea6a0b7`; UI remains a synthetic-preview candidate, not integrated/deployed/live-verified. PR #11 is open; no merge performed.
- **Push status:** Local HTTPS push had failed because git could not read HTTPS username/credential. Retrying publication through the authorized GitHub connector now; receipt to follow. Backlog delta: existing owner-search slice advances from clear action unverified to verified in synthetic preview; no new backlog item.
